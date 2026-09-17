"""Classical ML prediction logging helpers."""

from .logger import log_predictions
from .setup import init_ml_client

__all__ = ["init_ml_client", "log_predictions"]
