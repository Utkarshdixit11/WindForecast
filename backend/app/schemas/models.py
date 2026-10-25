"""Data models and schemas for Wind Forecast Accuracy Analytics."""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class CutoffType(str, Enum):
    """Cutoff determination logic type."""
    DAY_AHEAD_FIXED = "day_ahead_fixed"  # e.g., 11:00 London time on Day D-1
    RELATIVE_HOURS = "relative_hours"     # e.g., N hours before delivery period


class DataMode(str, Enum):
    """Execution data mode."""
    LIVE = "live"
    DEMO = "demo"
    CACHE = "cache"


class PeriodStatus(str, Enum):
    """Status of forecast and actual pairing for a delivery period."""
    VALID_PAIR = "VALID_PAIR"
    MISSING_FORECAST = "MISSING_FORECAST"
    MISSING_ACTUAL = "MISSING_ACTUAL"
    MISSING_BOTH = "MISSING_BOTH"


class FuelHHRecord(BaseModel):
    """Raw record from BMRS FUELHH dataset."""
    dataset: str = "FUELHH"
    startTime: datetime
    publishTime: Optional[datetime] = None
    settlementDate: Optional[str] = None
    settlementPeriod: Optional[int] = None
    fuelType: str
    generation: float

    @field_validator("generation", mode="before")
    @classmethod
    def parse_generation(cls, v: Any) -> float:
        if v is None:
            return 0.0
        return float(v)


class WindforRecord(BaseModel):
    """Raw record from BMRS WINDFOR dataset."""
    dataset: str = "WINDFOR"
    startTime: datetime  # Forecast target delivery period
    publishTime: datetime  # Forecast publication timestamp
    generation: float

    @field_validator("generation", mode="before")
    @classmethod
    def parse_generation(cls, v: Any) -> float:
        if v is None:
            return 0.0
        return float(v)


class ForecastCutoffConfig(BaseModel):
    """Configuration for Day-Ahead purchase decision cutoff."""
    cutoff_type: CutoffType = Field(
        default=CutoffType.DAY_AHEAD_FIXED,
        description="Type of cutoff: 'day_ahead_fixed' (e.g. 11:00 D-1) or 'relative_hours'"
    )
    cutoff_time_uk: str = Field(
        default="11:00",
        description="HH:MM in UK local time (Europe/London) on Day D-1 for day_ahead_fixed"
    )
    relative_hours_lead: int = Field(
        default=24,
        description="Lead hours prior to delivery start time if using relative_hours"
    )
    resolution_matching: str = Field(
        default="hourly_block",
        description=(
            "Resolution alignment strategy between WINDFOR (hourly forecasts from ESO) and FUELHH (30-min settlement periods). "
            "'hourly_block' maps the hourly forecast across both 30-min periods (HH:00 and HH:30). "
            "'exact_timestamp' only pairs HH:00 periods, marking HH:30 as MISSING_FORECAST."
        )
    )
    rationale: str = Field(
        default=(
            "Default cutoff represents 11:00 London local time on Day D-1, aligning with "
            "standard UK Day-Ahead power exchange order submission deadlines (EPEX SPOT / Nord Pool GB). "
            "Any forecast published after this cutoff is excluded to prevent look-ahead bias."
        ),
        description="Explanation of the cutoff assumption"
    )


class AccuracyMetrics(BaseModel):
    """Statistical accuracy metrics computed from valid forecast-actual pairs."""
    sample_count: int = Field(..., description="Number of valid forecast-actual pairs (N)")
    mae_mw: float = Field(..., description="Mean Absolute Error in MW: (1/N) * sum(|F - A|)")
    rmse_mw: float = Field(..., description="Root Mean Squared Error in MW: sqrt((1/N) * sum((F - A)^2))")
    bias_mw: float = Field(
        ...,
        description="Mean Signed Error in MW: (1/N) * sum(F - A). Positive = overforecasting, Negative = underforecasting"
    )
    wape_pct: Optional[float] = Field(
        None,
        description="Weighted Absolute Percentage Error (%): (sum(|F - A|) / sum(A)) * 100. None if sum(A) == 0."
    )
    total_actual_mwh: float = Field(
        ...,
        description="Total actual wind energy delivered (MW * 0.5h = MWh) over valid pairs"
    )
    total_forecast_mwh: float = Field(
        ...,
        description="Total forecasted wind energy (MW * 0.5h = MWh) over valid pairs"
    )
    mape_note: str = Field(
        default=(
            "MAPE (Mean Absolute Percentage Error) is intentionally omitted because actual wind generation "
            "frequently approaches zero MW during calm periods, which causes division-by-zero or mathematically "
            "distorted percentage spikes. WAPE is provided instead as an industry-standard volume-weighted metric."
        ),
        description="Methodological note regarding percentage errors"
    )


class MissingDataSummary(BaseModel):
    """Summary of data coverage across all expected settlement periods."""
    total_expected_periods: int = Field(..., description="Total half-hour delivery periods in analysis window")
    valid_pair_count: int = Field(..., description="Periods with both eligible forecast and actual generation")
    missing_forecast_count: int = Field(..., description="Periods missing an eligible forecast before cutoff")
    missing_actual_count: int = Field(..., description="Periods missing observed actual generation")
    missing_both_count: int = Field(..., description="Periods missing both forecast and actual generation")
    data_completeness_pct: float = Field(..., description="(valid_pair_count / total_expected_periods) * 100")


class PeriodAnalysisRecord(BaseModel):
    """Analytical row for a single 30-minute delivery period."""
    delivery_start_time: str = Field(..., description="Delivery start time in UTC ISO 8601")
    delivery_start_time_uk: str = Field(..., description="Delivery start time in Europe/London local time")
    settlement_date: str = Field(..., description="UK settlement date (YYYY-MM-DD)")
    settlement_period: int = Field(..., description="Settlement period number (1 to 48/50)")
    decision_cutoff_time: str = Field(..., description="Purchase decision cutoff in UTC ISO 8601")
    forecast_publish_time: Optional[str] = Field(None, description="Publication timestamp of chosen forecast in UTC")
    forecast_generation_mw: Optional[float] = Field(None, description="Selected forecast wind generation (MW)")
    actual_generation_mw: Optional[float] = Field(None, description="Actual observed wind generation (MW)")
    error_mw: Optional[float] = Field(
        None,
        description="Signed error (forecast - actual) in MW. Positive = overforecasting, Negative = underforecasting"
    )
    absolute_error_mw: Optional[float] = Field(None, description="Absolute error |forecast - actual| in MW")
    status: PeriodStatus = Field(..., description="Eligibility and matching status")


class AnalysisPeriod(BaseModel):
    """Analysis time boundary."""
    start_date: str
    end_date: str
    total_days: int


class AnalysisResponse(BaseModel):
    """Top-level analytical payload returned by /api/analysis."""
    analysis_period: AnalysisPeriod
    data_source: str = Field(..., description="Identifies data provider / origin (e.g. Elexon BMRS Live, Cache, Demo)")
    data_mode: DataMode = Field(..., description="'live', 'cache', or 'demo'")
    is_demo: bool = Field(..., description="Explicit flag: True if synthetic fixture demo data is used")
    decision_cutoff_config: ForecastCutoffConfig
    metrics: AccuracyMetrics
    missing_data_summary: MissingDataSummary
    time_series: List[PeriodAnalysisRecord]
    warnings: List[str] = Field(default_factory=list, description="Data quality or operational warnings")


class MetadataResponse(BaseModel):
    """System and methodology metadata returned by /api/metadata."""
    service_name: str = "UK Wind Forecast Accuracy Analytics"
    version: str = "1.0.0"
    data_provider: str = "Elexon BMRS Open Data API"
    datasets: Dict[str, Any]
    decision_cutoff_methodology: Dict[str, Any]
    metric_definitions: Dict[str, str]
    timezone_handling: Dict[str, str]
