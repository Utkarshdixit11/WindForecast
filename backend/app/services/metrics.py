"""Accuracy metrics calculation module for wind generation forecasts."""

import math
from typing import List, Optional, Tuple
import pandas as pd

from backend.app.schemas.models import AccuracyMetrics


def calculate_accuracy_metrics(
    pairs: List[Tuple[float, float]]
) -> AccuracyMetrics:
    """Calculate statistical accuracy metrics from a list of (forecast_mw, actual_mw) pairs.

    Convention:
      error = forecast - actual
      absolute_error = abs(error)

    Metrics:
      - MAE (MW): Mean Absolute Error
      - RMSE (MW): Root Mean Squared Error
      - Bias (MW): Mean Signed Error (positive = overforecast, negative = underforecast)
      - WAPE (%): Weighted Absolute Percentage Error = sum(|F - A|) / sum(A) * 100
      - Total MWh: sum(MW) * 0.5h
    """
    n = len(pairs)
    if n == 0:
        return AccuracyMetrics(
            sample_count=0,
            mae_mw=0.0,
            rmse_mw=0.0,
            bias_mw=0.0,
            wape_pct=None,
            total_actual_mwh=0.0,
            total_forecast_mwh=0.0
        )

    df = pd.DataFrame(pairs, columns=["forecast", "actual"])
    df["error"] = df["forecast"] - df["actual"]
    df["abs_error"] = df["error"].abs()
    df["sq_error"] = df["error"] ** 2

    mae = float(df["abs_error"].mean())
    mse = float(df["sq_error"].mean())
    rmse = float(math.sqrt(mse))
    bias = float(df["error"].mean())

    total_actual_mw = float(df["actual"].sum())
    total_forecast_mw = float(df["forecast"].sum())

    # Energy delivered/predicted in MWh (each settlement period is 0.5 hours)
    total_actual_mwh = round(total_actual_mw * 0.5, 2)
    total_forecast_mwh = round(total_forecast_mw * 0.5, 2)

    # WAPE with robust zero-denominator check
    wape: Optional[float] = None
    if total_actual_mw > 0:
        wape = round(float((df["abs_error"].sum() / total_actual_mw) * 100.0), 4)

    return AccuracyMetrics(
        sample_count=n,
        mae_mw=round(mae, 2),
        rmse_mw=round(rmse, 2),
        bias_mw=round(bias, 2),
        wape_pct=wape,
        total_actual_mwh=total_actual_mwh,
        total_forecast_mwh=total_forecast_mwh
    )
