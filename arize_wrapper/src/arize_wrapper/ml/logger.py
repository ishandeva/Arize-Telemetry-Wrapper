"""Classical ML prediction logging with organization identity injected."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Optional

from ..config import ArizeConfig
from ..exceptions import ArizeWrapperInstrumentationError, MissingOptionalDependencyError

logger = logging.getLogger(__name__)

REQUIRED_TAG_COLUMNS = (
    "arize_tenant",
    "arize_service_name",
    "arize_deployment_environment",
)


def _load_arize_types() -> Any:
    try:
        from arize.pandas.logger import Schema
    except ImportError as exc:
        raise MissingOptionalDependencyError(
            "Classic ML logging requires optional dependencies. Install with "
            'pip install "arize-telemetry-wrapper[ml]".'
        ) from exc
    return Schema


def _call_log(client: Any, **kwargs: Any) -> Any:
    """Support both broadly deployed Arize pandas logging client layouts."""
    ml_namespace = getattr(client, "ml", None)
    if ml_namespace is not None and hasattr(ml_namespace, "log"):
        v8_kwargs = dict(kwargs)
        v8_kwargs["model_name"] = v8_kwargs.pop("model_id")
        return ml_namespace.log(**v8_kwargs)
    if hasattr(client, "log"):
        return client.log(**kwargs)
    raise TypeError("The provided ML client exposes neither log() nor ml.log().")


def log_predictions(
    *,
    client: Any,
    config: ArizeConfig,
    dataframe: Any,
    schema_kwargs: Dict[str, Any],
    model_type: Any,
    environment: Any,
    tag_column_names: Optional[Iterable[str]] = None,
    **log_kwargs: Any,
) -> Any:
    """Log predictions while injecting tenant, service, and deployment tags.

    The classic Arize ML API has a tabular schema rather than OpenInference
    spans.  Thus the three static required attributes are represented as
    guaranteed tag columns; the LLM-specific prompt and temperature fields do
    not apply to a batch-prediction payload.
    """
    if client is None or not config.enabled:
        logger.debug("arize_wrapper: ML telemetry disabled; prediction batch not sent.")
        return None
    Schema = _load_arize_types()
    frame = dataframe.copy()
    standards = {
        "arize_tenant": config.tenant,
        "arize_service_name": config.service_name,
        "arize_deployment_environment": config.deployment_environment,
    }
    for column, value in standards.items():
        # Authoritative values prevent inconsistent dashboards caused by an
        # application-provided column of the same name.
        frame[column] = value
    schema_arguments = dict(schema_kwargs)
    schema_tags = schema_arguments.pop("tag_column_names", ())
    tags = list(tag_column_names if tag_column_names is not None else schema_tags)
    for required in REQUIRED_TAG_COLUMNS:
        if required not in tags:
            tags.append(required)
    schema = Schema(tag_column_names=tags, **schema_arguments)
    try:
        payload = {
            "dataframe": frame,
            "schema": schema,
            "environment": environment,
            "model_id": config.service_name,
            "model_type": model_type,
            **log_kwargs,
        }
        if config.service_version:
            payload["model_version"] = config.service_version
        return _call_log(client, **payload)
    except Exception as exc:
        message = "arize_wrapper: failed to log predictions for {!r}: {}".format(
            config.service_name, exc
        )
        if config.fail_silently:
            logger.exception("%s", message)
            return None
        logger.error(message)
        raise ArizeWrapperInstrumentationError(message) from exc
