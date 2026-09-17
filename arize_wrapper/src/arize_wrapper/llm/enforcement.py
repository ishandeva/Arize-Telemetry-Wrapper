"""OpenTelemetry processor that applies organization-required Arize fields."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from opentelemetry.context import Context
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor

from ..config import ArizeConfig
from ..constants import (
    LLM_PROMPT_TEMPLATE,
    LLM_PROMPT_TEMPLATE_VERSION,
    LLM_SPAN_KIND,
    LLM_TEMPERATURE,
    METADATA,
    OPENINFERENCE_SPAN_KIND,
    build_metadata,
)
from .context import current_llm_attributes

logger = logging.getLogger(__name__)

_LLM_REQUIRED_KEYS = (
    LLM_TEMPERATURE,
    LLM_PROMPT_TEMPLATE_VERSION,
    LLM_PROMPT_TEMPLATE,
)


class TraceMetadataError(RuntimeError):
    """Raised when strict validation finds a missing required LLM field."""


class EnforcedMetadataSpanProcessor(SpanProcessor):
    """Set static metadata on every span and dynamic fields in an LLM context.

    ``metadata`` is a JSON-valued OpenInference attribute.  The processor
    preserves application-defined metadata keys but treats the three required
    organization keys as authoritative configuration values.  This prevents a
    caller from accidentally emitting a trace for the wrong tenant or service.
    """

    def __init__(self, config: ArizeConfig, strict: bool = False) -> None:
        self._config = config
        self._strict = strict

    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        self._merge_required_metadata(span)
        dynamic_attributes = current_llm_attributes()
        if dynamic_attributes:
            for key, value in dynamic_attributes.items():
                span.set_attribute(key, value)

    def on_end(self, span: ReadableSpan) -> None:
        if self._get_attribute(span, OPENINFERENCE_SPAN_KIND) != LLM_SPAN_KIND:
            return
        missing = [
            key for key in _LLM_REQUIRED_KEYS if self._get_attribute(span, key) is None
        ]
        if not missing:
            return
        message = "LLM span {!r} is missing required attribute(s): {}".format(
            span.name, ", ".join(missing)
        )
        if self._strict:
            raise TraceMetadataError(message)
        logger.warning("arize_wrapper: %s", message)

    def shutdown(self) -> None:
        """The wrapper owns no exporter resources."""

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """No buffered work exists in this processor."""
        return True

    def _merge_required_metadata(self, span: Span) -> None:
        raw_metadata = self._get_attribute(span, METADATA)
        metadata = self._decode_metadata(raw_metadata)
        required = build_metadata(
            service_name=self._config.service_name,
            environment=self._config.deployment_environment,
            tenant=self._config.tenant,
        )
        service = metadata.get("service")
        metadata["service"] = service if isinstance(service, dict) else {}
        metadata["service"]["name"] = required["service"]["name"]
        if self._config.service_version:
            metadata["service"]["version"] = self._config.service_version
        deployment = metadata.get("deployment")
        metadata["deployment"] = deployment if isinstance(deployment, dict) else {}
        metadata["deployment"]["environment"] = required["deployment"]["environment"]
        metadata["tenant"] = required["tenant"]
        span.set_attribute(
            METADATA,
            json.dumps(metadata, sort_keys=True, separators=(",", ":")),
        )

    @staticmethod
    def _decode_metadata(raw_metadata: Any) -> dict:
        if not raw_metadata:
            return {}
        try:
            decoded = json.loads(raw_metadata)
        except (TypeError, ValueError):
            logger.warning("arize_wrapper: replacing invalid JSON metadata on span.")
            return {}
        if not isinstance(decoded, dict):
            logger.warning("arize_wrapper: replacing non-object metadata on span.")
            return {}
        return decoded

    @staticmethod
    def _get_attribute(span: Any, key: str) -> Any:
        attributes = getattr(span, "attributes", None) or {}
        return attributes.get(key)
