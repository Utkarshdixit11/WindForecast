"""Tests for accuracy metrics calculation module."""

import pytest
from backend.app.services.metrics import calculate_accuracy_metrics


def test_known_numerical_metrics(known_numerical_data):
    """Test MAE, RMSE, Bias, and WAPE against exact known numerical values.

    Fixture:
      Pair 1: F=1000, A=800  -> e=+200, |e|=200, e^2=40000
      Pair 2: F=1200, A=1500 -> e=-300, |e|=300, e^2=90000
      Pair 3: F=900,  A=900  -> e=0,    |e|=0,   e^2=0
      Pair 4: F=1500, A=1100 -> e=+400, |e|=400, e^2=160000
      Pair 5: F=700,  A=1000 -> e=-300, |e|=300, e^2=90000

    Expectations:
      N = 5
      sum(actual) = 5300 MW
      sum(forecast) = 5300 MW
      sum(error) = 0 MW -> Bias = 0.0 MW
      sum(abs_error) = 1200 MW -> MAE = 240.0 MW
      sum(sq_error) = 380000 -> MSE = 76000 -> RMSE = sqrt(76000) ~= 275.68 MW
      WAPE = (1200 / 5300) * 100 ~= 22.6415 %
      Total actual energy = 5300 * 0.5 = 2650.0 MWh
    """
    pairs = [(item["forecast"], item["actual"]) for item in known_numerical_data]
    metrics = calculate_accuracy_metrics(pairs)

    assert metrics.sample_count == 5
    assert metrics.mae_mw == 240.0
    assert pytest.approx(metrics.rmse_mw, 0.01) == 275.68
    assert metrics.bias_mw == 0.0
    assert pytest.approx(metrics.wape_pct, 0.001) == 22.6415
    assert metrics.total_actual_mwh == 2650.0
    assert metrics.total_forecast_mwh == 2650.0


def test_positive_bias_overforecasting():
    """Verify that positive bias correctly signals systematic overforecasting."""
    pairs = [(1200.0, 1000.0), (1300.0, 1000.0)]
    metrics = calculate_accuracy_metrics(pairs)

    # e1 = +200, e2 = +300 -> mean error = +250
    assert metrics.bias_mw == 250.0
    assert metrics.mae_mw == 250.0
    assert metrics.sample_count == 2


def test_negative_bias_underforecasting():
    """Verify that negative bias correctly signals systematic underforecasting."""
    pairs = [(800.0, 1000.0), (700.0, 1000.0)]
    metrics = calculate_accuracy_metrics(pairs)

    # e1 = -200, e2 = -300 -> mean error = -250
    assert metrics.bias_mw == -250.0
    assert metrics.mae_mw == 250.0
    assert metrics.sample_count == 2


def test_zero_denominator_wape_handling():
    """Verify that WAPE gracefully handles actual generation summing to zero without crashing."""
    pairs = [(100.0, 0.0), (50.0, 0.0)]
    metrics = calculate_accuracy_metrics(pairs)

    assert metrics.sample_count == 2
    assert metrics.mae_mw == 75.0
    assert metrics.bias_mw == 75.0
    assert metrics.wape_pct is None  # Zero denominator correctly handled


def test_empty_pairs_list():
    """Verify metrics calculation on empty dataset."""
    metrics = calculate_accuracy_metrics([])

    assert metrics.sample_count == 0
    assert metrics.mae_mw == 0.0
    assert metrics.rmse_mw == 0.0
    assert metrics.bias_mw == 0.0
    assert metrics.wape_pct is None
    assert metrics.total_actual_mwh == 0.0
    assert metrics.total_forecast_mwh == 0.0
