"""Synthetic data generator and fixtures for offline demo mode and deterministic testing.

Never presents synthetic data as genuine Elexon observations.
Explicitly labels all generated records with demo/synthetic indicators.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
import math


def generate_synthetic_dataset(
    start_date_str: str = "2026-01-01",
    days: int = 3,
    cutoff_hour: int = 11
) -> Tuple[List[Dict], List[Dict]]:
    """Generate synthetic FUELHH actuals and WINDFOR forecasts.

    Includes edge cases:
    - Multiple forecasts per period (published D-2, D-1 06:00, D-1 10:30, D-1 11:30 post-cutoff, D-1 16:00 post-cutoff)
    - Rejection of post-cutoff forecasts
    - Missing forecast for a specific delivery period
    - Missing actual for a specific delivery period
    - Zero generation period
    - Duplicate forecast records with identical timestamps
    """
    fuelhh_records: List[Dict] = []
    windfor_records: List[Dict] = []

    start_dt = datetime.fromisoformat(f"{start_date_str}T00:00:00").replace(tzinfo=timezone.utc)
    total_periods = days * 48

    for p in range(total_periods):
        period_dt = start_dt + timedelta(minutes=30 * p)
        period_iso = period_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        settlement_date = period_dt.strftime("%Y-%m-%d")
        settlement_period = (p % 48) + 1

        # Smooth synthetic wind actual curve (base 10,000 MW with diurnal and harmonic waves)
        hour = period_dt.hour + period_dt.minute / 60.0
        wave1 = 5000.0 * math.sin((hour / 24.0) * 2 * math.pi)
        wave2 = 2500.0 * math.cos((hour / 12.0) * 2 * math.pi)
        base_actual = max(200.0, 11000.0 + wave1 + wave2 + (p * 50 % 800))

        # Edge case: period 20 has near-zero actual generation
        if p == 20:
            actual_mw = 0.0
        else:
            actual_mw = round(base_actual, 1)

        # Edge case: period 35 has missing actual outturn
        if p != 35:
            fuelhh_records.append({
                "dataset": "FUELHH",
                "startTime": period_iso,
                "publishTime": (period_dt + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "settlementDate": settlement_date,
                "settlementPeriod": settlement_period,
                "fuelType": "WIND",
                "generation": actual_mw,
                "_synthetic": True
            })

        # Generate forecasts for this delivery period
        delivery_day = datetime(period_dt.year, period_dt.month, period_dt.day, tzinfo=timezone.utc)
        d_minus_1 = delivery_day - timedelta(days=1)

        # Edge case: period 45 has ONLY post-cutoff forecasts (should result in MISSING_FORECAST)
        if p == 45:
            # Only published at 11:30 and 14:00 on D-1
            windfor_records.append({
                "dataset": "WINDFOR",
                "startTime": period_iso,
                "publishTime": (d_minus_1.replace(hour=11, minute=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "generation": round(actual_mw * 1.05, 1),
                "_synthetic": True
            })
            windfor_records.append({
                "dataset": "WINDFOR",
                "startTime": period_iso,
                "publishTime": (d_minus_1.replace(hour=14, minute=0)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "generation": round(actual_mw * 1.04, 1),
                "_synthetic": True
            })
            continue

        # Normal forecasts progression:
        # 1. Early forecast: D-2 18:00
        early_pub = (d_minus_1 - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
        windfor_records.append({
            "dataset": "WINDFOR",
            "startTime": period_iso,
            "publishTime": early_pub,
            "generation": round(actual_mw * 1.15 + 400, 1),
            "_synthetic": True
        })

        # 2. Morning eligible forecast: D-1 06:30
        morning_pub = (d_minus_1.replace(hour=6, minute=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        windfor_records.append({
            "dataset": "WINDFOR",
            "startTime": period_iso,
            "publishTime": morning_pub,
            "generation": round(actual_mw * 1.08 + 200, 1),
            "_synthetic": True
        })

        # 3. Latest eligible forecast prior to 11:00 cutoff: D-1 10:30
        eligible_pub = (d_minus_1.replace(hour=10, minute=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        eligible_pred = round(actual_mw * 1.03 + (150 if p % 2 == 0 else -150), 1)
        windfor_records.append({
            "dataset": "WINDFOR",
            "startTime": period_iso,
            "publishTime": eligible_pub,
            "generation": eligible_pred,
            "_synthetic": True
        })

        # Duplicate test record for p == 10 to verify deduplication
        if p == 10:
            windfor_records.append({
                "dataset": "WINDFOR",
                "startTime": period_iso,
                "publishTime": eligible_pub,
                "generation": eligible_pred,
                "_synthetic": True
            })

        # 4. Post-cutoff forecast: D-1 11:30 (Must be excluded when cutoff is 11:00!)
        post_cutoff_pub = (d_minus_1.replace(hour=11, minute=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        windfor_records.append({
            "dataset": "WINDFOR",
            "startTime": period_iso,
            "publishTime": post_cutoff_pub,
            "generation": round(actual_mw * 0.99, 1),  # Closer to actual, would create look-ahead bias!
            "_synthetic": True
        })

        # 5. Late post-cutoff forecast: D-1 16:00
        late_pub = (d_minus_1.replace(hour=16, minute=0)).strftime("%Y-%m-%dT%H:%M:%SZ")
        windfor_records.append({
            "dataset": "WINDFOR",
            "startTime": period_iso,
            "publishTime": late_pub,
            "generation": round(actual_mw * 0.98, 1),
            "_synthetic": True
        })

    return fuelhh_records, windfor_records


# Known numerical benchmark fixture for exact mathematical verification
KNOWN_NUMERICAL_FIXTURE = [
    {"forecast": 1000.0, "actual": 800.0},    # err = +200, abs = 200, sq = 40000
    {"forecast": 1200.0, "actual": 1500.0},   # err = -300, abs = 300, sq = 90000
    {"forecast": 900.0,  "actual": 900.0},    # err = 0,    abs = 0,   sq = 0
    {"forecast": 1500.0, "actual": 1100.0},   # err = +400, abs = 400, sq = 160000
    {"forecast": 700.0,  "actual": 1000.0},   # err = -300, abs = 300, sq = 90000
]
# Expected exact metrics for KNOWN_NUMERICAL_FIXTURE:
# N = 5
# sum(actual) = 5300.0 MW
# sum(forecast) = 5300.0 MW
# sum(error) = 0.0 MW -> Bias = 0.0 MW
# sum(abs_error) = 1200.0 MW -> MAE = 240.0 MW
# sum(sq_error) = 380000.0 -> MSE = 76000.0 -> RMSE = sqrt(76000) = 275.6809750417978 MW
# WAPE = (1200.0 / 5300.0) * 100 = 22.641509433962263 %
# Total actual MWh = 5300.0 * 0.5 = 2650.0 MWh
# Total forecast MWh = 5300.0 * 0.5 = 2650.0 MWh
