import asyncio
import json

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import StatusCode

from arize_wrapper.config import ArizeConfig
from arize_wrapper.constants import (
    LLM_PROMPT_TEMPLATE,
    LLM_PROMPT_TEMPLATE_VERSION,
    LLM_TEMPERATURE,
    METADATA,
)
from arize_wrapper.llm.enforcement import EnforcedMetadataSpanProcessor, TraceMetadataError
from arize_wrapper.llm.telemetry import ArizeTelemetry


def _config():
    return ArizeConfig(
        space_id="space",
        api_key="key",
        project_name="support",
        service_name="support-api",
        deployment_environment="staging",
        tenant="tenant-a",
        service_version="1.2.3",
    )


def _telemetry(strict=False):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(EnforcedMetadataSpanProcessor(_config(), strict=strict))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return ArizeTelemetry(_config(), provider), exporter


def test_decorator_populates_every_required_llm_attribute():
    telemetry, exporter = _telemetry()

    @telemetry.llm(
        prompt_template="Reply to {customer}",
        prompt_template_version="v4",
        temperature=0.2,
    )
    def answer(customer):
        return "Hello " + customer

    assert answer("Ada") == "Hello Ada"
    span = exporter.get_finished_spans()[0]
    metadata = json.loads(span.attributes[METADATA])
    assert metadata == {
        "deployment": {"environment": "staging"},
        "service": {"name": "support-api", "version": "1.2.3"},
        "tenant": "tenant-a",
    }
    assert span.attributes[LLM_TEMPERATURE] == 0.2
    assert span.attributes[LLM_PROMPT_TEMPLATE_VERSION] == "v4"
    assert span.attributes[LLM_PROMPT_TEMPLATE] == "Reply to {customer}"
    assert json.loads(span.attributes["llm.invocation_parameters"]) == {
        "temperature": 0.2
    }
    assert span.status.status_code is StatusCode.OK


def test_context_manager_applies_fields_to_nested_provider_span():
    telemetry, exporter = _telemetry()
    tracer = telemetry.get_tracer("provider-simulation")

    with telemetry.llm_call(
        prompt_template="Answer: {question}",
        prompt_template_version="v5",
        temperature=0.7,
    ):
        with tracer.start_as_current_span("provider.chat"):
            pass

    spans = {span.name: span for span in exporter.get_finished_spans()}
    child = spans["provider.chat"]
    assert child.attributes[LLM_TEMPERATURE] == 0.7
    assert child.attributes[LLM_PROMPT_TEMPLATE_VERSION] == "v5"
    assert json.loads(child.attributes[METADATA])["tenant"] == "tenant-a"


def test_async_decorator_preserves_context_and_result():
    telemetry, exporter = _telemetry()

    @telemetry.llm(
        prompt_template="Answer: {question}",
        prompt_template_version="v1",
        temperature=lambda _question, temperature: temperature,
    )
    async def answer(question, temperature):
        return question.upper()

    assert asyncio.run(answer("ready", 0.4)) == "READY"
    assert exporter.get_finished_spans()[0].attributes[LLM_TEMPERATURE] == 0.4


def test_wrapped_exception_marks_span_as_error():
    telemetry, exporter = _telemetry()

    @telemetry.llm(
        prompt_template="Do work: {value}", prompt_template_version="v1", temperature=0
    )
    def broken(value):
        raise RuntimeError(value)

    with pytest.raises(RuntimeError, match="boom"):
        broken("boom")
    span = exporter.get_finished_spans()[0]
    assert span.status.status_code is StatusCode.ERROR


class _ReadableSpan:
    name = "unmanaged"
    attributes = {"openinference.span.kind": "LLM"}


def test_strict_processor_rejects_an_unmanaged_llm_span():
    processor = EnforcedMetadataSpanProcessor(_config(), strict=True)
    with pytest.raises(TraceMetadataError, match="llm.temperature"):
        processor.on_end(_ReadableSpan())
