"""Tests for forecast eligibility, selection, matching, and cutoff logic."""

from datetime import datetime, timezone
import pytest

from backend.app.schemas.models import CutoffType, ForecastCutoffConfig, FuelHHRecord, PeriodStatus, WindforRecord
from backend.app.services.forecast_selector import (
    compute_decision_cutoff,
    get_uk_settlement_period,
    match_and_analyze_forecasts,
)


def test_cutoff_computation_gmt_winter():
    """Verify Day-Ahead 11:00 London cutoff calculation during winter (GMT, UTC+0)."""
    config = ForecastCutoffConfig(
        cutoff_type=CutoffType.DAY_AHEAD_FIXED,
        cutoff_time_uk="11:00"
    )
    # Delivery on Jan 2, 2026 at 14:00 UTC
    delivery_utc = datetime(2026, 1, 2, 14, 0, tzinfo=timezone.utc)
    cutoff = compute_decision_cutoff(delivery_utc, config)

    # Cutoff should be Jan 1, 2026 at 11:00 UTC
    assert cutoff == datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc)


def test_cutoff_computation_bst_summer_daylight_saving():
    """Verify Day-Ahead 11:00 London cutoff calculation during British Summer Time (BST, UTC+1)."""
    config = ForecastCutoffConfig(
        cutoff_type=CutoffType.DAY_AHEAD_FIXED,
        cutoff_time_uk="11:00"
    )
    # Delivery on July 15, 2026 at 14:00 UTC (BST is UTC+1)
    delivery_utc = datetime(2026, 7, 15, 14, 0, tzinfo=timezone.utc)
    cutoff = compute_decision_cutoff(delivery_utc, config)

    # On July 14, 11:00 BST corresponds to 10:00 UTC!
    assert cutoff == datetime(2026, 7, 14, 10, 0, tzinfo=timezone.utc)


def test_cutoff_computation_relative_hours():
    """Verify relative lead hours cutoff calculation."""
    config = ForecastCutoffConfig(
        cutoff_type=CutoffType.RELATIVE_HOURS,
        relative_hours_lead=24
    )
    delivery_utc = datetime(2026, 1, 2, 14, 0, tzinfo=timezone.utc)
    cutoff = compute_decision_cutoff(delivery_utc, config)

    assert cutoff == datetime(2026, 1, 1, 14, 0, tzinfo=timezone.utc)


def test_latest_eligible_forecast_selection_and_post_cutoff_rejection():
    """Verify that:
    1. The latest forecast published BEFORE or AT cutoff is selected.
    2. Forecasts published AFTER cutoff are strictly rejected (preventing look-ahead bias).
    """
    delivery_iso = "2026-01-02T12:00:00Z"
    cutoff_config = ForecastCutoffConfig(
        cutoff_type=CutoffType.DAY_AHEAD_FIXED,
        cutoff_time_uk="11:00"
    )

    # Actual generation
    fuelhh = [
        FuelHHRecord(
            dataset="FUELHH",
            startTime=datetime.fromisoformat(delivery_iso),
            fuelType="WIND",
            generation=12000.0
        )
    ]

    # Multiple forecasts published over time for that delivery period:
    # Cutoff for 2026-01-02 delivery is 2026-01-01 11:00:00 UTC
    windfor = [
        # Early forecast (eligible, but older)
        WindforRecord(
            dataset="WINDFOR",
            startTime=datetime.fromisoformat(delivery_iso),
            publishTime=datetime.fromisoformat("2026-01-01T06:00:00Z"),
            generation=11000.0
        ),
        # Latest eligible forecast (published 10:30 <= 11:00) -> MUST BE SELECTED
        WindforRecord(
            dataset="WINDFOR",
            startTime=datetime.fromisoformat(delivery_iso),
            publishTime=datetime.fromisoformat("2026-01-01T10:30:00Z"),
            generation=11800.0
        ),
        # Post-cutoff forecast (published 11:30 > 11:00) -> MUST BE EXCLUDED!
        WindforRecord(
            dataset="WINDFOR",
            startTime=datetime.fromisoformat(delivery_iso),
            publishTime=datetime.fromisoformat("2026-01-01T11:30:00Z"),
            generation=12500.0
        ),
        # Real-time forecast on delivery day -> MUST BE EXCLUDED!
        WindforRecord(
            dataset="WINDFOR",
            startTime=datetime.fromisoformat(delivery_iso),
            publishTime=datetime.fromisoformat("2026-01-02T08:00:00Z"),
            generation=12100.0
        ),
    ]

    time_series, summary, metrics, warnings = match_and_analyze_forecasts(
        fuelhh_records=fuelhh,
        windfor_records=windfor,
        start_date="2026-01-02",
        end_date="2026-01-02",
        cutoff_config=cutoff_config
    )

    # Find the target period row
    target_row = next(r for r in time_series if r.delivery_start_time == delivery_iso)

    assert target_row.status == PeriodStatus.VALID_PAIR
    # Must select 11800 (from 10:30Z), NOT 12500 (from 11:30Z) or 12100
    assert target_row.forecast_generation_mw == 11800.0
    assert target_row.forecast_publish_time == "2026-01-01T10:30:00Z"
    assert target_row.actual_generation_mw == 12000.0
    # error = forecast - actual = 11800 - 12000 = -200 MW (underforecasting)
    assert target_row.error_mw == -200.0
    assert target_row.absolute_error_mw == 200.0


def test_missing_forecast_when_all_forecasts_post_cutoff():
    """Verify that if all available forecasts were published after the cutoff, status is MISSING_FORECAST."""
    delivery_iso = "2026-01-02T12:00:00Z"
    cutoff_config = ForecastCutoffConfig(
        cutoff_type=CutoffType.DAY_AHEAD_FIXED,
        cutoff_time_uk="11:00"
    )

    fuelhh = [
        FuelHHRecord(
            dataset="FUELHH",
            startTime=datetime.fromisoformat(delivery_iso),
            fuelType="WIND",
            generation=9500.0
        )
    ]

    # Only post-cutoff forecasts
    windfor = [
        WindforRecord(
            dataset="WINDFOR",
            startTime=datetime.fromisoformat(delivery_iso),
            publishTime=datetime.fromisoformat("2026-01-01T11:45:00Z"),
            generation=9400.0
        )
    ]

    time_series, summary, metrics, warnings = match_and_analyze_forecasts(
        fuelhh_records=fuelhh,
        windfor_records=windfor,
        start_date="2026-01-02",
        end_date="2026-01-02",
        cutoff_config=cutoff_config
    )

    target_row = next(r for r in time_series if r.delivery_start_time == delivery_iso)
    assert target_row.status == PeriodStatus.MISSING_FORECAST
    assert target_row.forecast_generation_mw is None
    assert target_row.actual_generation_mw == 9500.0
    assert target_row.error_mw is None


def test_missing_actual_outturn():
    """Verify that if actual generation is missing, status is MISSING_ACTUAL."""
    delivery_iso = "2026-01-02T12:00:00Z"
    cutoff_config = ForecastCutoffConfig(
        cutoff_type=CutoffType.DAY_AHEAD_FIXED,
        cutoff_time_uk="11:00"
    )

    fuelhh = []  # No actuals provided
    windfor = [
        WindforRecord(
            dataset="WINDFOR",
            startTime=datetime.fromisoformat(delivery_iso),
            publishTime=datetime.fromisoformat("2026-01-01T10:00:00Z"),
            generation=8000.0
        )
    ]

    time_series, summary, metrics, warnings = match_and_analyze_forecasts(
        fuelhh_records=fuelhh,
        windfor_records=windfor,
        start_date="2026-01-02",
        end_date="2026-01-02",
        cutoff_config=cutoff_config
    )

    target_row = next(r for r in time_series if r.delivery_start_time == delivery_iso)
    assert target_row.status == PeriodStatus.MISSING_ACTUAL
    assert target_row.forecast_generation_mw == 8000.0
    assert target_row.actual_generation_mw is None
    assert target_row.error_mw is None


def test_duplicate_records_deduplication():
    """Verify that duplicate actual and forecast records are gracefully deduplicated."""
    delivery_iso = "2026-01-02T12:00:00Z"
    cutoff_config = ForecastCutoffConfig()

    fuelhh = [
        FuelHHRecord(
            dataset="FUELHH",
            startTime=datetime.fromisoformat(delivery_iso),
            fuelType="WIND",
            generation=10000.0
        ),
        FuelHHRecord(
            dataset="FUELHH",
            startTime=datetime.fromisoformat(delivery_iso),
            fuelType="WIND",
            generation=10000.0
        ),
    ]

    windfor = [
        WindforRecord(
            dataset="WINDFOR",
            startTime=datetime.fromisoformat(delivery_iso),
            publishTime=datetime.fromisoformat("2026-01-01T09:00:00Z"),
            generation=9800.0
        ),
        WindforRecord(
            dataset="WINDFOR",
            startTime=datetime.fromisoformat(delivery_iso),
            publishTime=datetime.fromisoformat("2026-01-01T09:00:00Z"),
            generation=9800.0
        ),
    ]

    time_series, summary, metrics, warnings = match_and_analyze_forecasts(
        fuelhh_records=fuelhh,
        windfor_records=windfor,
        start_date="2026-01-02",
        end_date="2026-01-02",
        cutoff_config=cutoff_config
    )

    target_row = next(r for r in time_series if r.delivery_start_time == delivery_iso)
    assert target_row.status == PeriodStatus.VALID_PAIR
    assert target_row.forecast_generation_mw == 9800.0
    assert target_row.actual_generation_mw == 10000.0
    assert any("Deduplicated" in w for w in warnings)


def test_settlement_period_numbering():
    """Verify settlement period numbers from 1 to 48."""
    # 00:00 -> Period 1
    d1 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    _, p1 = get_uk_settlement_period(d1)
    assert p1 == 1

    # 12:00 -> Period 25
    d25 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    _, p25 = get_uk_settlement_period(d25)
    assert p25 == 25

    # 23:30 -> Period 48
    d48 = datetime(2026, 1, 1, 23, 30, tzinfo=timezone.utc)
    _, p48 = get_uk_settlement_period(d48)
    assert p48 == 48


def test_resolution_matching_hourly_block_vs_exact():
    """Verify that hourly_block maps hourly forecasts to both 30-min periods, while exact_timestamp requires exact startTime."""
    t0 = "2026-01-02T12:00:00Z"
    t1 = "2026-01-02T12:30:00Z"

    fuelhh = [
        FuelHHRecord(dataset="FUELHH", startTime=datetime.fromisoformat(t0), fuelType="WIND", generation=10000.0),
        FuelHHRecord(dataset="FUELHH", startTime=datetime.fromisoformat(t1), fuelType="WIND", generation=10500.0),
    ]

    # Only one hourly forecast published for the hour starting at 12:00
    windfor = [
        WindforRecord(
            dataset="WINDFOR",
            startTime=datetime.fromisoformat(t0),
            publishTime=datetime.fromisoformat("2026-01-01T10:00:00Z"),
            generation=9800.0
        )
    ]

    # 1. Hourly block matching (default): both t0 and t1 should be paired
    config_block = ForecastCutoffConfig(resolution_matching="hourly_block")
    ts_block, summary_block, _, _ = match_and_analyze_forecasts(
        fuelhh, windfor, "2026-01-02", "2026-01-02", config_block
    )
    row_t1_block = next(r for r in ts_block if r.delivery_start_time == t1)
    assert row_t1_block.status == PeriodStatus.VALID_PAIR
    assert row_t1_block.forecast_generation_mw == 9800.0
    assert row_t1_block.actual_generation_mw == 10500.0

    # 2. Exact timestamp matching: t1 has no exact forecast -> MISSING_FORECAST
    config_exact = ForecastCutoffConfig(resolution_matching="exact_timestamp")
    ts_exact, summary_exact, _, _ = match_and_analyze_forecasts(
        fuelhh, windfor, "2026-01-02", "2026-01-02", config_exact
    )
    row_t1_exact = next(r for r in ts_exact if r.delivery_start_time == t1)
    assert row_t1_exact.status == PeriodStatus.MISSING_FORECAST
    assert row_t1_exact.forecast_generation_mw is None

