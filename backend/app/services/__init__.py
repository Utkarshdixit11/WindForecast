"""Services package."""
from backend.app.services.analysis_service import AnalysisService
from backend.app.services.forecast_selector import compute_decision_cutoff, match_and_analyze_forecasts
from backend.app.services.metrics import calculate_accuracy_metrics
from backend.app.services.synthetic_generator import KNOWN_NUMERICAL_FIXTURE, generate_synthetic_dataset

__all__ = [
    "AnalysisService",
    "compute_decision_cutoff",
    "match_and_analyze_forecasts",
    "calculate_accuracy_metrics",
    "generate_synthetic_dataset",
    "KNOWN_NUMERICAL_FIXTURE",
]
