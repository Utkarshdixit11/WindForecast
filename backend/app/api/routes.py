"""FastAPI API router defining analytics, metadata, and health endpoints."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.models import (
    AnalysisResponse,
    CutoffType,
    MetadataResponse,
)
from backend.app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/api", tags=["Analytics"])
analysis_service = AnalysisService()


@router.get(
    "/health",
    summary="Health check",
    description="Check the operational status of the analytics API service."
)
async def get_health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "UK Wind Forecast Accuracy Analytics API",
        "version": "1.0.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }


@router.get(
    "/metadata",
    response_model=MetadataResponse,
    summary="Service metadata and analytical methodology",
    description="Detailed documentation of datasets, decision cutoff mechanics, and metrics."
)
async def get_metadata():
    """Return dataset details, methodology, and formula definitions."""
    return MetadataResponse(
        service_name="UK Wind Forecast Accuracy Analytics API",
        version="1.0.0",
        data_provider="Elexon BMRS Open Data API (Balancing Mechanism Reporting Service)",
        datasets={
            "actuals": {
                "dataset_name": "FUELHH",
                "endpoint": "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream",
                "fuel_type_filter": "WIND",
                "description": "Half-hourly generation outturn for Great Britain by fuel type (30-minute settlement periods in MW).",
                "primary_fields": ["startTime", "generation", "fuelType", "settlementDate", "settlementPeriod"]
            },
            "forecasts": {
                "dataset_name": "WINDFOR",
                "endpoint": "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream",
                "description": "Rolling National Grid ESO wind generation forecasts published at regular intervals throughout the day.",
                "primary_fields": ["startTime", "publishTime", "generation"]
            }
        },
        decision_cutoff_methodology={
            "default_cutoff_type": "day_ahead_fixed",
            "default_uk_time": "11:00 London time on Day D-1",
            "market_alignment": (
                "Corresponds to standard Day-Ahead wholesale power auction gate closure in the UK (e.g. EPEX SPOT / Nord Pool). "
                "Procurement traders submit order bids at 11:00 London time on the day prior to physical delivery."
            ),
            "selection_rule": (
                "For every 30-minute delivery period, we select the latest forecast where publishTime <= decision_cutoff. "
                "Any forecast published after the cutoff is strictly excluded to prevent look-ahead bias."
            ),
            "separation_of_concepts": (
                "Delivery time (startTime), forecast publication time (publishTime), and decision cutoff (cutoffTime) "
                "are explicitly separated."
            )
        },
        metric_definitions={
            "error": "forecast - actual (Positive = overforecasting; Negative = underforecasting)",
            "absolute_error": "abs(forecast - actual)",
            "MAE": "Mean Absolute Error: (1/N) * sum(|forecast - actual|) in MW",
            "RMSE": "Root Mean Squared Error: sqrt((1/N) * sum((forecast - actual)^2)) in MW",
            "Bias": "Mean Signed Error: (1/N) * sum(forecast - actual) in MW",
            "WAPE": "Weighted Absolute Percentage Error: (sum(|forecast - actual|) / sum(actual)) * 100 (%)",
            "MAPE_rationale": "MAPE is omitted due to extreme division-by-zero distortion when actual wind approaches 0 MW."
        },
        timezone_handling={
            "storage_and_comparison": "UTC ISO 8601 timestamps",
            "display_and_settlement": "Europe/London (UK Local Time), correctly mapping GMT (winter) and BST (summer) clock changes"
        }
    )


@router.get(
    "/analysis",
    response_model=AnalysisResponse,
    summary="Wind forecast accuracy analysis",
    description="Calculate forecast errors and summary metrics for January 2026 purchase decisions."
)
async def get_analysis(
    start_date: str = Query("2026-01-01", description="Start date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query("2026-01-31", description="End date (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    cutoff_type: CutoffType = Query(CutoffType.DAY_AHEAD_FIXED, description="Cutoff type"),
    cutoff_time_uk: str = Query("11:00", description="Cutoff time in UK local time (HH:MM)"),
    relative_hours_lead: int = Query(24, ge=1, le=168, description="Lead hours for relative cutoff"),
    resolution_matching: str = Query("hourly_block", description="Resolution strategy: 'hourly_block' (ESO hourly mapped to 30-min settlement periods) or 'exact_timestamp'"),
    force_mode: Optional[str] = Query(None, description="'live' (force live API), 'demo' (synthetic fixtures), or auto")
):
    """Retrieve wind generation actuals and forecasts, apply decision cutoff logic, and calculate metrics."""
    try:
        response = await analysis_service.run_analysis(
            start_date=start_date,
            end_date=end_date,
            cutoff_type=cutoff_type,
            cutoff_time_uk=cutoff_time_uk,
            relative_hours_lead=relative_hours_lead,
            resolution_matching=resolution_matching,
            force_mode=force_mode
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Analysis pipeline error: {str(e)}"
        )
