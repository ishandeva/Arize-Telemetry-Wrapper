"""Optional legacy/classical-ML Arize client setup."""

from __future__ import annotations

import logging
from typing import Any

from ..config import ArizeConfig
from ..exceptions import (
    ArizeWrapperInstrumentationError,
    MissingOptionalDependencyError,
)

logger = logging.getLogger(__name__)


def init_ml_client(config: ArizeConfig) -> Any:
    """Create Arize's pandas logger client without exposing credentials to callers."""
    if not config.enabled:
        return None
    try:
        from arize.pandas.logger import Client
    except ImportError as exc:
        raise MissingOptionalDependencyError(
            "Classic ML logging requires optional dependencies. Install with "
            'pip install "arize-telemetry-wrapper[ml]".'
        ) from exc
    kwargs = {"space_id": config.space_id, "api_key": config.api_key}
    if config.endpoint:
        kwargs["uri"] = config.endpoint
    try:
        return Client(**kwargs)
    except Exception as exc:
        message = "arize_wrapper: failed to initialize the ML client: {}".format(exc)
        if config.fail_silently:
            logger.exception("%s ML telemetry will be disabled.", message)
            return None
        logger.error(message)
        raise ArizeWrapperInstrumentationError(message) from exc
