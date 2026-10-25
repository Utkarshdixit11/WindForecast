"""Tests for FastAPI endpoints."""

import asyncio
import httpx
from backend.app.main import app


def api_get(path: str, params=None):
    """Helper to execute synchronous GET request against FastAPI app via ASGITransport."""
    async def _call():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get(path, params=params)
    return asyncio.run(_call())


def test_root_endpoint():
    """Verify root endpoint returns system links."""
    response = api_get("/")
    assert response.status_code == 200
    data = response.json()
    assert "health" in data
    assert "metadata" in data
    assert "analysis" in data


def test_health_endpoint():
    """Verify health endpoint operational status."""
    response = api_get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp_utc" in data


def test_metadata_endpoint():
    """Verify metadata endpoint describes datasets, methodology, and metric formulas."""
    response = api_get("/api/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "datasets" in data
    assert "FUELHH" in data["datasets"]["actuals"]["dataset_name"]
    assert "WINDFOR" in data["datasets"]["forecasts"]["dataset_name"]
    assert "decision_cutoff_methodology" in data
    assert "metric_definitions" in data
    assert "MAPE_rationale" in data["metric_definitions"]


def test_analysis_endpoint_demo_mode():
    """Verify /api/analysis runs deterministically with synthetic fixtures under demo mode."""
    response = api_get(
        "/api/analysis",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-01-03",
            "cutoff_type": "day_ahead_fixed",
            "cutoff_time_uk": "11:00",
            "force_mode": "demo"
        }
    )
    assert response.status_code == 200
    data = response.json()

    assert data["is_demo"] is True
    assert "demo" in data["data_mode"]
    assert "Synthetic Fixture" in data["data_source"]

    # Verify metrics structure
    metrics = data["metrics"]
    assert metrics["sample_count"] > 0
    assert metrics["mae_mw"] > 0.0
    assert metrics["rmse_mw"] > 0.0
    assert isinstance(metrics["bias_mw"], (int, float))
    assert metrics["wape_pct"] is not None
    assert "MAPE" in metrics["mape_note"]

    # Verify summary
    summary = data["missing_data_summary"]
    assert summary["total_expected_periods"] == 3 * 48  # 144
    assert summary["valid_pair_count"] > 0

    # Verify time series
    time_series = data["time_series"]
    assert len(time_series) == 144
    first_record = time_series[0]
    assert "delivery_start_time" in first_record
    assert "delivery_start_time_uk" in first_record
    assert "decision_cutoff_time" in first_record
    assert "status" in first_record


def test_analysis_invalid_date_range():
    """Verify 400 Bad Request when start_date is after end_date."""
    response = api_get(
        "/api/analysis",
        params={
            "start_date": "2026-01-10",
            "end_date": "2026-01-05",
            "force_mode": "demo"
        }
    )
    assert response.status_code == 400
    assert "cannot be after" in response.json()["detail"]


def test_analysis_range_exceeds_limit():
    """Verify 400 Bad Request when date range exceeds 62 days limit."""
    response = api_get(
        "/api/analysis",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-04-01",
            "force_mode": "demo"
        }
    )
    assert response.status_code == 400
    assert "exceeds maximum allowed" in response.json()["detail"]
