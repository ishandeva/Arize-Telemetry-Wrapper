"""Arize AX/OpenTelemetry setup, isolated behind a small stable API."""

from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, Dict, Optional

from ..config import ArizeConfig
from ..exceptions import (
    ArizeWrapperInstrumentationError,
    MissingOptionalDependencyError,
)
from .telemetry import ArizeTelemetry

logger = logging.getLogger(__name__)


def _load_register() -> Callable[..., Any]:
    try:
        from arize.otel import register
    except ImportError as exc:
        raise MissingOptionalDependencyError(
            "LLM tracing requires optional dependencies. Install with "
            'pip install "arize-telemetry-wrapper[llm]".'
        ) from exc
    return register


def _register_provider(config: ArizeConfig, register: Callable[..., Any]) -> Any:
    kwargs: Dict[str, Any] = {
        "space_id": config.space_id,
        "api_key": config.api_key,
        "project_name": config.project_name,
    }
    if config.endpoint:
        # ``arize-otel`` has changed its endpoint argument over releases.
        # Only pass it if the installed version declares an explicit support.
        parameters = inspect.signature(register).parameters
        if "endpoint" not in parameters:
            raise ArizeWrapperInstrumentationError(
                "ARIZE_ENDPOINT was supplied, but the installed arize-otel "
                "version does not expose an endpoint argument. Upgrade the "
                "approved arize-otel dependency or remove ARIZE_ENDPOINT."
            )
        kwargs["endpoint"] = config.endpoint
    return register(**kwargs)


def initialize_llm(config: ArizeConfig, strict: bool = False) -> ArizeTelemetry:
    """Initialize the Arize tracer provider once and return a telemetry facade.

    ``strict`` is best used in tests or development: it reports any manually
    created LLM span that omits one of the three dynamic required fields.  In
    production the default warning leaves telemetry flowing while making the
    gap searchable in application logs.
    """
    if not config.enabled:
        logger.info("arize_wrapper: telemetry is disabled by ARIZE_ENABLED.")
        return ArizeTelemetry(config=config, tracer_provider=None)

    try:
        provider = _register_provider(config, _load_register())
        if not getattr(provider, "_arize_wrapper_processor_installed", False):
            # Import only after the user has explicitly initialized tracing so
            # importing the base package never requires an OTel installation.
            from .enforcement import EnforcedMetadataSpanProcessor

            provider.add_span_processor(
                EnforcedMetadataSpanProcessor(config=config, strict=strict)
            )
            setattr(provider, "_arize_wrapper_processor_installed", True)
        return ArizeTelemetry(config=config, tracer_provider=provider)
    except MissingOptionalDependencyError:
        raise
    except Exception as exc:
        message = "arize_wrapper: failed to initialize Arize LLM tracing: {}".format(exc)
        if config.fail_silently:
            logger.exception("%s Telemetry will be disabled.", message)
            return ArizeTelemetry(config=config, tracer_provider=None)
        logger.error(message)
        raise ArizeWrapperInstrumentationError(message) from exc


def init_llm_tracing(config: ArizeConfig, strict: bool = False) -> Any:
    """Compatibility helper returning the underlying tracer provider.

    New integrations should prefer :func:`initialize_llm`, which returns an
    object exposing decorators and context managers as well as the provider.
    """
    return initialize_llm(config=config, strict=strict).tracer_provider
