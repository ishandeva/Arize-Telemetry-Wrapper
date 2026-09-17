"""A small, provider-neutral front door for organization-standard Arize telemetry.

The package intentionally does not import Arize or OpenTelemetry at import time.
Install ``arize-telemetry-wrapper[llm]`` for tracing and/or
``arize-telemetry-wrapper[ml]`` for classic ML prediction logging.
"""

from .config import ArizeConfig
from .exceptions import (
    ArizeWrapperConfigError,
    ArizeWrapperError,
    ArizeWrapperInstrumentationError,
    MissingOptionalDependencyError,
)
from .logging_utils import configure_default_logging

__version__ = "0.1.0"

__all__ = [
    "ArizeConfig",
    "ArizeWrapperError",
    "ArizeWrapperConfigError",
    "ArizeWrapperInstrumentationError",
    "MissingOptionalDependencyError",
    "configure_default_logging",
    "__version__",
]
