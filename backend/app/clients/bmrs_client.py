"""Elexon BMRS Open Data API client with caching, retry logic, and fallback support."""

import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import httpx

from backend.app.config import settings
from backend.app.schemas.models import DataMode, FuelHHRecord, WindforRecord

logger = logging.getLogger(__name__)


class BMRSClientError(Exception):
    """Base exception for BMRS client errors."""
    pass


class BMRSClient:
    """Client for Elexon BMRS Open Data API (/datasets/FUELHH/stream and /datasets/WINDFOR/stream)."""

    def __init__(
        self,
        base_url: str = settings.ELEXON_API_BASE_URL,
        timeout: float = settings.ELEXON_HTTP_TIMEOUT,
        cache_dir: Path = settings.CACHE_DIR,
        max_retries: int = settings.ELEXON_MAX_RETRIES,
        retry_backoff: float = settings.ELEXON_RETRY_BACKOFF,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

    def _get_cache_path(self, dataset: str, start_key: str, end_key: str) -> Path:
        """Construct deterministic cache file path."""
        safe_start = start_key.replace(":", "-")
        safe_end = end_key.replace(":", "-")
        return self.cache_dir / f"{dataset}_{safe_start}_{safe_end}.json"

    def _read_cache(self, path: Path) -> Optional[List[Dict[str, Any]]]:
        """Read data from local cache if file exists and is valid."""
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        logger.info(f"Loaded {len(data)} records from cache: {path.name}")
                        return data
            except Exception as e:
                logger.warning(f"Failed to read cache file {path}: {e}")
        return None

    def _write_cache(self, path: Path, data: List[Dict[str, Any]]) -> None:
        """Write fetched records to disk cache."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            logger.info(f"Cached {len(data)} records to {path.name}")
        except Exception as e:
            logger.warning(f"Failed to write cache file {path}: {e}")

    async def _fetch_with_retries(self, url: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """HTTP GET request with timeout and exponential backoff retry logic."""
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"BMRS API Request [attempt {attempt}/{self.max_retries}]: {url} params={params}")
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    if not isinstance(data, list):
                        raise BMRSClientError(f"Unexpected API response type: {type(data)}")
                    return data
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_exception = e
                logger.warning(f"BMRS API network/timeout on attempt {attempt}: {e}")
            except httpx.HTTPStatusError as e:
                last_exception = e
                # Do not retry on 4xx client errors other than 429 rate limit
                if e.response.status_code != 429 and 400 <= e.response.status_code < 500:
                    raise BMRSClientError(f"Elexon BMRS API HTTP {e.response.status_code}: {e.response.text}") from e
                logger.warning(f"BMRS API HTTP error on attempt {attempt}: {e}")
            except Exception as e:
                last_exception = e
                logger.warning(f"Unexpected error querying BMRS API on attempt {attempt}: {e}")

            if attempt < self.max_retries:
                sleep_sec = self.retry_backoff * (2 ** (attempt - 1))
                await asyncio.sleep(sleep_sec)

        raise BMRSClientError(f"Failed to fetch from BMRS API after {self.max_retries} attempts: {last_exception}")

    async def fetch_fuelhh_actuals(
        self,
        start_date: str,
        end_date: str,
        force_refresh: bool = False
    ) -> Tuple[List[FuelHHRecord], DataMode]:
        """Fetch FUELHH wind actuals stream for date range [start_date, end_date]."""
        cache_path = self._get_cache_path("FUELHH_WIND", start_date, end_date)

        if not force_refresh:
            cached = self._read_cache(cache_path)
            if cached is not None:
                records = [FuelHHRecord(**r) for r in cached]
                return records, DataMode.CACHE

        url = f"{self.base_url}/datasets/FUELHH/stream"
        params = {
            "settlementDateFrom": start_date,
            "settlementDateTo": end_date,
            "fuelType": "WIND"
        }

        try:
            raw_data = await self._fetch_with_retries(url, params)
            records = [FuelHHRecord(**r) for r in raw_data if r.get("fuelType") == "WIND"]
            self._write_cache(cache_path, [r.model_dump(mode="json") for r in records])
            return records, DataMode.LIVE
        except Exception as e:
            logger.error(f"Error fetching live FUELHH data: {e}")
            # Try cache even if expired/previous
            cached = self._read_cache(cache_path)
            if cached is not None:
                logger.info("Falling back to local cache for FUELHH.")
                return [FuelHHRecord(**r) for r in cached], DataMode.CACHE
            raise

    async def fetch_windfor_forecasts(
        self,
        start_date: str,
        end_date: str,
        force_refresh: bool = False
    ) -> Tuple[List[WindforRecord], DataMode]:
        """Fetch WINDFOR forecast stream published for the purchase decisions period.

        To cover day-ahead decisions for deliveries starting on start_date (e.g. 2026-01-01),
        forecasts published from D-2 (or 2 days prior to start_date) up through end_date 23:59:59 are fetched.
        """
        # Determine publishing window boundaries
        start_dt = datetime.fromisoformat(f"{start_date}T00:00:00").replace(tzinfo=timezone.utc)
        # Decision for start_date begins 2 days prior to account for early forecasts
        pub_from_dt = start_dt - timedelta(days=2)
        pub_to_dt = datetime.fromisoformat(f"{end_date}T23:59:59").replace(tzinfo=timezone.utc)

        pub_from_str = pub_from_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        pub_to_str = pub_to_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        cache_path = self._get_cache_path("WINDFOR", pub_from_str[:10], pub_to_str[:10])

        if not force_refresh:
            cached = self._read_cache(cache_path)
            if cached is not None:
                records = [WindforRecord(**r) for r in cached]
                return records, DataMode.CACHE

        url = f"{self.base_url}/datasets/WINDFOR/stream"
        params = {
            "publishDateTimeFrom": pub_from_str,
            "publishDateTimeTo": pub_to_str
        }

        try:
            raw_data = await self._fetch_with_retries(url, params)
            records = [WindforRecord(**r) for r in raw_data]
            self._write_cache(cache_path, [r.model_dump(mode="json") for r in records])
            return records, DataMode.LIVE
        except Exception as e:
            logger.error(f"Error fetching live WINDFOR data: {e}")
            cached = self._read_cache(cache_path)
            if cached is not None:
                logger.info("Falling back to local cache for WINDFOR.")
                return [WindforRecord(**r) for r in cached], DataMode.CACHE
            raise
