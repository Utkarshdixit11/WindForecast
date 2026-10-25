"""Tests for BMRS API client with mocked network calls and caching."""

import json
from pathlib import Path
import pytest
import httpx

from backend.app.clients.bmrs_client import BMRSClient, BMRSClientError
from backend.app.schemas.models import DataMode


@pytest.mark.asyncio
async def test_client_reads_from_cache(tmp_path: Path):
    """Verify that the client retrieves cached data without making network requests."""
    client = BMRSClient(cache_dir=tmp_path)

    # Pre-populate cache
    cache_file = tmp_path / "FUELHH_WIND_2026-01-01_2026-01-02.json"
    cached_data = [
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2026-01-01T00:30:00Z",
            "settlementDate": "2026-01-01",
            "settlementPeriod": 1,
            "fuelType": "WIND",
            "generation": 10500.0
        }
    ]
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cached_data, f)

    records, mode = await client.fetch_fuelhh_actuals("2026-01-01", "2026-01-02")
    assert mode == DataMode.CACHE
    assert len(records) == 1
    assert records[0].generation == 10500.0


@pytest.mark.asyncio
async def test_client_fetch_with_retries_and_error(tmp_path: Path, monkeypatch):
    """Verify that network failures trigger retries and ultimately raise BMRSClientError."""
    client = BMRSClient(cache_dir=tmp_path, max_retries=2, retry_backoff=0.01)

    async def mock_get(*args, **kwargs):
        raise httpx.ConnectError("Network unreachable")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with pytest.raises(BMRSClientError) as exc_info:
        await client._fetch_with_retries("https://example.com/api", {})

    assert "Failed to fetch from BMRS API after 2 attempts" in str(exc_info.value)


@pytest.mark.asyncio
async def test_client_non_retryable_400(tmp_path: Path, monkeypatch):
    """Verify that HTTP 400 client error raises immediately without useless retries."""
    client = BMRSClient(cache_dir=tmp_path, max_retries=3, retry_backoff=0.01)

    mock_response = httpx.Response(
        status_code=400,
        text="Invalid parameters",
        request=httpx.Request("GET", "https://example.com/api")
    )

    async def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with pytest.raises(BMRSClientError) as exc_info:
        await client._fetch_with_retries("https://example.com/api", {})

    assert "HTTP 400" in str(exc_info.value)
