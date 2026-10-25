"""Forecast eligibility, selection, matching, and time series construction module."""

from datetime import date, datetime, time, timedelta, timezone
import logging
from typing import Dict, List, Optional, Tuple
import zoneinfo
import pandas as pd

from backend.app.schemas.models import (
    AccuracyMetrics,
    CutoffType,
    ForecastCutoffConfig,
    FuelHHRecord,
    MissingDataSummary,
    PeriodAnalysisRecord,
    PeriodStatus,
    WindforRecord,
)
from backend.app.services.metrics import calculate_accuracy_metrics

logger = logging.getLogger(__name__)
UK_TZ = zoneinfo.ZoneInfo("Europe/London")


def compute_decision_cutoff(
    delivery_start_utc: datetime,
    config: ForecastCutoffConfig
) -> datetime:
    """Compute the purchase decision cutoff timestamp for a specific delivery period.

    Separates delivery time, publication time, and cutoff timestamp.
    Handles UTC <-> Europe/London daylight-saving transitions transparently.

    Rules:
    - DAY_AHEAD_FIXED (default):
        1. Determine delivery date in UK local time (Europe/London).
        2. Decision date is local delivery date minus 1 calendar day (D-1).
        3. Combine decision date with config.cutoff_time_uk (e.g. 11:00) in Europe/London.
        4. Convert localized decision cutoff to UTC.
    - RELATIVE_HOURS:
        Cutoff is delivery_start_utc minus config.relative_hours_lead.
    """
    if config.cutoff_type == CutoffType.RELATIVE_HOURS:
        return delivery_start_utc - timedelta(hours=config.relative_hours_lead)

    # DAY_AHEAD_FIXED
    delivery_uk = delivery_start_utc.astimezone(UK_TZ)
    local_delivery_date = delivery_uk.date()
    local_decision_date = local_delivery_date - timedelta(days=1)

    cutoff_parts = config.cutoff_time_uk.strip().split(":")
    hour = int(cutoff_parts[0])
    minute = int(cutoff_parts[1]) if len(cutoff_parts) > 1 else 0

    cutoff_local = datetime(
        year=local_decision_date.year,
        month=local_decision_date.month,
        day=local_decision_date.day,
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
        tzinfo=UK_TZ
    )
    return cutoff_local.astimezone(timezone.utc)


def generate_period_grid(start_date: str, end_date: str) -> List[datetime]:
    """Generate all standard 30-minute delivery period start times between start_date and end_date (inclusive)."""
    start_dt = datetime.fromisoformat(f"{start_date}T00:00:00").replace(tzinfo=timezone.utc)
    end_dt = datetime.fromisoformat(f"{end_date}T23:30:00").replace(tzinfo=timezone.utc)

    periods = []
    curr = start_dt
    while curr <= end_dt:
        periods.append(curr)
        curr += timedelta(minutes=30)
    return periods


def get_uk_settlement_period(delivery_start_utc: datetime) -> Tuple[str, int]:
    """Calculate UK settlement date and settlement period (1 to 48, or 46/50 on clock transitions)."""
    delivery_uk = delivery_start_utc.astimezone(UK_TZ)
    settlement_date_str = delivery_uk.date().isoformat()

    # Calculate period from midnight local time
    # In standard 24h days, period = (hours * 2) + (minutes // 30) + 1
    period_num = (delivery_uk.hour * 2) + (delivery_uk.minute // 30) + 1
    return settlement_date_str, period_num


def match_and_analyze_forecasts(
    fuelhh_records: List[FuelHHRecord],
    windfor_records: List[WindforRecord],
    start_date: str,
    end_date: str,
    cutoff_config: ForecastCutoffConfig
) -> Tuple[List[PeriodAnalysisRecord], MissingDataSummary, AccuracyMetrics, List[str]]:
    """Process actuals and forecasts to produce the analytical time series and metrics.

    Ensures:
    - Look-ahead bias prevention: any forecast published > decision_cutoff is rejected.
    - Latest eligible selection: among forecasts published <= decision_cutoff, pick the one with max publishTime.
    - Deterministic deduplication of forecasts and actuals.
    - Transparent reporting of MISSING_FORECAST, MISSING_ACTUAL, and MISSING_BOTH periods.
    """
    warnings: List[str] = []

    # 1. Index actuals by delivery startTime (UTC)
    actuals_by_period: Dict[str, FuelHHRecord] = {}
    duplicate_actuals = 0
    for r in fuelhh_records:
        if r.fuelType.upper() != "WIND":
            continue
        key = r.startTime.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if key in actuals_by_period:
            duplicate_actuals += 1
            # Keep the latest published if duplicated
            if r.publishTime and actuals_by_period[key].publishTime:
                if r.publishTime > actuals_by_period[key].publishTime:
                    actuals_by_period[key] = r
        else:
            actuals_by_period[key] = r

    if duplicate_actuals > 0:
        warnings.append(f"Deduplicated {duplicate_actuals} FUELHH actual records.")

    # 2. Group forecasts by target delivery startTime (UTC)
    forecasts_by_period: Dict[str, List[WindforRecord]] = {}
    for f in windfor_records:
        key = f.startTime.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if key not in forecasts_by_period:
            forecasts_by_period[key] = []
        forecasts_by_period[key].append(f)

    # 3. Iterate over the expected delivery period grid
    grid = generate_period_grid(start_date, end_date)
    time_series: List[PeriodAnalysisRecord] = []
    valid_pairs: List[Tuple[float, float]] = []

    missing_forecast_count = 0
    missing_actual_count = 0
    missing_both_count = 0
    valid_pair_count = 0

    for period_dt in grid:
        period_iso = period_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        delivery_uk_dt = period_dt.astimezone(UK_TZ)
        delivery_uk_str = delivery_uk_dt.isoformat()
        settlement_date_str, settlement_period_num = get_uk_settlement_period(period_dt)

        # Compute decision cutoff
        cutoff_dt = compute_decision_cutoff(period_dt, cutoff_config)
        cutoff_iso = cutoff_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Retrieve eligible forecasts published on or before cutoff
        candidate_forecasts = list(forecasts_by_period.get(period_iso, []))

        # If hourly_block matching enabled and no direct forecast exists for HH:30, check the top of the hour (HH:00)
        if not candidate_forecasts and cutoff_config.resolution_matching == "hourly_block" and period_dt.minute == 30:
            top_of_hour_iso = period_dt.replace(minute=0).strftime("%Y-%m-%dT%H:%M:%SZ")
            candidate_forecasts = list(forecasts_by_period.get(top_of_hour_iso, []))

        eligible_forecasts = [
            f for f in candidate_forecasts
            if f.publishTime.astimezone(timezone.utc) <= cutoff_dt
        ]

        selected_forecast: Optional[WindforRecord] = None
        if eligible_forecasts:
            # Sort by publishTime ascending and take the latest eligible
            eligible_forecasts.sort(key=lambda x: x.publishTime)
            selected_forecast = eligible_forecasts[-1]

        # Retrieve actual wind generation
        actual_record = actuals_by_period.get(period_iso)
        actual_val = actual_record.generation if actual_record else None
        forecast_val = selected_forecast.generation if selected_forecast else None

        # Determine status and compute errors
        status: PeriodStatus
        error: Optional[float] = None
        abs_error: Optional[float] = None

        if selected_forecast is not None and actual_val is not None:
            status = PeriodStatus.VALID_PAIR
            valid_pair_count += 1
            error = round(forecast_val - actual_val, 2)
            abs_error = round(abs(error), 2)
            valid_pairs.append((forecast_val, actual_val))
        elif selected_forecast is None and actual_val is not None:
            status = PeriodStatus.MISSING_FORECAST
            missing_forecast_count += 1
        elif selected_forecast is not None and actual_val is None:
            status = PeriodStatus.MISSING_ACTUAL
            missing_actual_count += 1
        else:
            status = PeriodStatus.MISSING_BOTH
            missing_both_count += 1

        time_series.append(PeriodAnalysisRecord(
            delivery_start_time=period_iso,
            delivery_start_time_uk=delivery_uk_str,
            settlement_date=settlement_date_str,
            settlement_period=settlement_period_num,
            decision_cutoff_time=cutoff_iso,
            forecast_publish_time=selected_forecast.publishTime.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if selected_forecast else None,
            forecast_generation_mw=forecast_val,
            actual_generation_mw=actual_val,
            error_mw=error,
            absolute_error_mw=abs_error,
            status=status
        ))

    total_expected = len(grid)
    completeness_pct = round((valid_pair_count / total_expected * 100.0) if total_expected > 0 else 0.0, 2)

    missing_summary = MissingDataSummary(
        total_expected_periods=total_expected,
        valid_pair_count=valid_pair_count,
        missing_forecast_count=missing_forecast_count,
        missing_actual_count=missing_actual_count,
        missing_both_count=missing_both_count,
        data_completeness_pct=completeness_pct
    )

    metrics = calculate_accuracy_metrics(valid_pairs)

    if missing_forecast_count > 0:
        warnings.append(
            f"{missing_forecast_count} settlement periods did not have an eligible forecast published prior to the {cutoff_config.cutoff_time_uk} D-1 cutoff."
        )
    if missing_actual_count > 0:
        warnings.append(
            f"{missing_actual_count} settlement periods were missing FUELHH actual generation observations."
        )

    return time_series, missing_summary, metrics, warnings
