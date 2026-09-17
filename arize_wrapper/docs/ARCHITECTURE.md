# Architecture overview

The package has a small shared core plus separate integrations because Arize
uses different transport models for LLM tracing and classical ML monitoring.

```text
ArizeConfig
    | validates connection + service/environment/tenant identity
    +--> LLM: initialize_llm -> ArizeTelemetry -> OpenTelemetry spans -> Arize AX
    |                              |
    |                              +--> decorator / context manager / auto-instrumented children
    |
    +--> ML: init_ml_client + log_predictions -> Arize pandas client -> Arize ML
```

## Shared core

`ArizeConfig` reads environment-specific values once, checks that required
settings are non-empty, and makes the service name, deployment environment,
and tenant authoritative. It has no Arize SDK dependency, which lets services
validate configuration early and lets tests exercise the standards contract
without credentials.

## LLM path

`initialize_llm()` calls `arize.otel.register()` and attaches an
`EnforcedMetadataSpanProcessor`. On every span start, that processor writes
the OpenInference `metadata` JSON object. Within `llm_call()` or `@llm()`, it
also writes dynamic LLM fields to every child span. That means provider
auto-instrumentation can coexist with the wrapper: the wrapper owns standards
fields while the provider instrumentor records messages, model name, tokens,
and response data.

The explicit wrapper span is provider-neutral and is useful for custom model
clients. If a provider auto-instrumentor creates its own nested LLM span, both
spans are intentional: the wrapper span proves the organization contract; the
child span contains provider-level detail.

## ML path

Classical Arize prediction logging is schema/dataframe based rather than span
based. `log_predictions()` never modifies the caller's dataframe; it copies
it, writes three standard tag columns, and sends it using either legacy
`Client.log()` or current `Client.ml.log()` layouts. The ML path does not
invent LLM prompt/temperature attributes for prediction batches.

## Dependency boundary

The top-level package and configuration module use only the Python standard
library. Arize, pandas, and OpenTelemetry imports occur only in the respective
integration path. Missing extras result in a `MissingOptionalDependencyError`
with the exact installation extra to add.
