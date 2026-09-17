"""Arize/OpenInference attribute names and organization-required field names.

Arize AX represents custom metadata in one JSON-valued OpenInference
``metadata`` attribute.  In Arize this is queryable as
``attributes.metadata.<key>``; therefore the nested JSON below produces the
three required metadata fields without relying on non-standard flat keys.
"""

from __future__ import annotations

import json
from typing import Any, Dict

METADATA = "metadata"
OPENINFERENCE_SPAN_KIND = "openinference.span.kind"
LLM_SPAN_KIND = "LLM"
LLM_TEMPERATURE = "llm.temperature"
LLM_INVOCATION_PARAMETERS = "llm.invocation_parameters"
LLM_PROMPT_TEMPLATE = "llm.prompt_template.template"
LLM_PROMPT_TEMPLATE_VERSION = "llm.prompt_template.version"

REQUIRED_ATTRIBUTE_PATHS = (
    "attributes.metadata.service.name",
    "attributes.metadata.deployment.environment",
    "attributes.metadata.tenant",
    "attributes.llm.temperature",
    "attributes.llm.prompt_template.version",
    "attributes.llm.prompt_template.template",
)


def build_metadata(
    *, service_name: str, environment: str, tenant: str
) -> Dict[str, Any]:
    """Return the canonical metadata object for every telemetry span."""
    return {
        "service": {"name": service_name},
        "deployment": {"environment": environment},
        "tenant": tenant,
    }


def encode_metadata(*, service_name: str, environment: str, tenant: str) -> str:
    """Encode canonical metadata deterministically for OpenTelemetry."""
    return json.dumps(
        build_metadata(
            service_name=service_name, environment=environment, tenant=tenant
        ),
        sort_keys=True,
        separators=(",", ":"),
    )


def build_llm_attributes(
    *, prompt_template: str, prompt_template_version: str, temperature: float
) -> Dict[str, Any]:
    """Return all dynamic organization-required attributes for an LLM span.

    ``llm.temperature`` is emitted as the requested first-class attribute.
    ``llm.invocation_parameters`` is additionally emitted because it is the
    OpenInference field used by common auto-instrumentors and Arize views.
    """
    numeric_temperature = float(temperature)
    return {
        OPENINFERENCE_SPAN_KIND: LLM_SPAN_KIND,
        LLM_TEMPERATURE: numeric_temperature,
        LLM_INVOCATION_PARAMETERS: json.dumps(
            {"temperature": numeric_temperature},
            sort_keys=True,
            separators=(",", ":"),
        ),
        LLM_PROMPT_TEMPLATE: prompt_template,
        LLM_PROMPT_TEMPLATE_VERSION: prompt_template_version,
    }
