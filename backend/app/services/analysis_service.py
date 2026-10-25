"""Analysis orchestrator service coordinating data retrieval, forecast selection, and metrics."""

from datetime import datetime
import logging
from typing import Optional
from backend.app.clients.bmrs_client import BMRSClient, BMRSClientError
from backend.app.schemas.models import (
    AnalysisPeriod,
    AnalysisResponse,
    CutoffType,
    DataMode,
    ForecastCutoffConfig,
    FuelHHRecord,
    WindforRecord,
)
from backend.app.services.forecast_selector import match_and_analyze_forecasts
from backend.app.services.synthetic_generator import generate_synthetic_dataset

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service to coordinate Elexon data retrieval, forecast selection logic, and accuracy evaluation."""

    def __init__(self, client: Optional[BMRSClient] = None):
        self.client = client or BMRSClient()

    async def run_analysis(
        self,
        start_date: str = "2026-01-01",
        end_date: str = "2026-01-31",
        cutoff_type: CutoffType = CutoffType.DAY_AHEAD_FIXED,
        cutoff_time_uk: str = "11:00",
        relative_hours_lead: int = 24,
        resolution_matching: str = "hourly_block",
        force_mode: Optional[str] = None
    ) -> AnalysisResponse:
        """Run the full analytics pipeline."""
        cutoff_config = ForecastCutoffConfig(
            cutoff_type=cutoff_type,
            cutoff_time_uk=cutoff_time_uk,
            relative_hours_lead=relative_hours_lead,
            resolution_matching=resolution_matching
        )

        # Validate date inputs
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            if start_dt > end_dt:
                raise ValueError("start_date cannot be after end_date")
            days_span = (end_dt - start_dt).days + 1
            if days_span > 62:
                raise ValueError("Date range exceeds maximum allowed query window (62 days)")
        except Exception as e:
            raise ValueError(f"Invalid date range parameter: {e}")

        analysis_period = AnalysisPeriod(
            start_date=start_date,
            end_date=end_date,
            total_days=days_span
        )

        warnings = []
        is_demo = False
        data_source = "Elexon BMRS Open Data API"
        active_mode = DataMode.LIVE

        # Handle explicit DEMO mode
        if force_mode == "demo":
            logger.info("Executing analysis in forced DEMO mode using synthetic fixtures.")
            is_demo = True
            active_mode = DataMode.DEMO
            data_source = "Synthetic Fixture (Demo Mode - Not Genuine Elexon Observations)"
            fuel_raw, wind_raw = generate_synthetic_dataset(start_date_str=start_date, days=days_span)
            fuel_records = [FuelHHRecord(**r) for r in fuel_raw]
            wind_records = [WindforRecord(**r) for r in wind_raw]
            warnings.append("DEMO MODE ACTIVE: Using synthetic test data. Values do not represent genuine Elexon observations.")

        else:
            # Attempt live retrieval with cache fallback
            try:
                fuel_records, fuel_mode = await self.client.fetch_fuelhh_actuals(start_date, end_date)
                wind_records, wind_mode = await self.client.fetch_windfor_forecasts(start_date, end_date)

                if fuel_mode == DataMode.CACHE and wind_mode == DataMode.CACHE:
                    active_mode = DataMode.CACHE
                    data_source = "Elexon BMRS Open Data API (Local Cache)"
                else:
                    active_mode = DataMode.LIVE
                    data_source = "Elexon BMRS Open Data API (Live Stream)"

            except Exception as e:
                logger.error(f"Failed to fetch Elexon live/cached data: {e}")
                if force_mode == "live":
                    raise BMRSClientError(f"Live Elexon API request failed: {e}")

                # Graceful fallback to synthetic demo fixture with explicit warning
                logger.warning("Falling back to synthetic fixture demo mode due to API unavailability.")
                is_demo = True
                active_mode = DataMode.DEMO
                data_source = "Synthetic Fixture (Fallback Demo Mode - Not Genuine Elexon Observations)"
                fuel_raw, wind_raw = generate_synthetic_dataset(start_date_str=start_date, days=days_span)
                fuel_records = [FuelHHRecord(**r) for r in fuel_raw]
                wind_records = [WindforRecord(**r) for r in wind_raw]
                warnings.append(
                    f"Elexon BMRS API was unavailable ({str(e)}). "
                    "Displaying synthetic demo fixture. These are simulated figures and not genuine Elexon observations."
                )

        # Execute forecast selection, matching, and error calculations
        time_series, missing_summary, metrics, selection_warnings = match_and_analyze_forecasts(
            fuelhh_records=fuel_records,
            windfor_records=wind_records,
            start_date=start_date,
            end_date=end_date,
            cutoff_config=cutoff_config
        )

        warnings.extend(selection_warnings)

        return AnalysisResponse(
            analysis_period=analysis_period,
            data_source=data_source,
            data_mode=active_mode,
            is_demo=is_demo,
            decision_cutoff_config=cutoff_config,
            metrics=metrics,
            missing_data_summary=missing_summary,
            time_series=time_series,
            warnings=warnings
        )
