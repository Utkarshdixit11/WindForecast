"""Pytest configuration and deterministic fixtures."""

import os
import sys
from pathlib import Path
import pytest

# Ensure repository root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.schemas.models import CutoffType, ForecastCutoffConfig, FuelHHRecord, WindforRecord
from backend.app.services.synthetic_generator import KNOWN_NUMERICAL_FIXTURE, generate_synthetic_dataset


@pytest.fixture
def known_numerical_data():
    """Known numerical fixture with hand-calculated ground truth metrics."""
    return KNOWN_NUMERICAL_FIXTURE


@pytest.fixture
def default_cutoff_config():
    """Default Day-Ahead 11:00 London time cutoff configuration."""
    return ForecastCutoffConfig(
        cutoff_type=CutoffType.DAY_AHEAD_FIXED,
        cutoff_time_uk="11:00"
    )


@pytest.fixture
def synthetic_data_3days():
    """3-day synthetic dataset with deliberate edge cases."""
    fuel_raw, wind_raw = generate_synthetic_dataset(start_date_str="2026-01-01", days=3)
    fuel_records = [FuelHHRecord(**r) for r in fuel_raw]
    wind_records = [WindforRecord(**r) for r in wind_raw]
    return fuel_records, wind_records
