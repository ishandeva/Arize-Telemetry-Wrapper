# Troubleshooting and logging

The package never installs logging handlers on import. Configure application
logging normally, or call `configure_default_logging()` during startup for a
simple development setup.

## Configuration error listing missing variables

`ArizeConfig.from_env()` includes all missing variables in one
`ArizeWrapperConfigError`. Copy `.env.example` to the deployment's secret
configuration and check the service name, tenant, and deployment environment
first; those values must be non-empty even when telemetry is disabled.

## `MissingOptionalDependencyError`

Install the integration extra named in the error:

```bash
pip install "arize-telemetry-wrapper[llm]"
pip install "arize-telemetry-wrapper[ml]"
```

Provider auto-instrumentation has a separate provider-specific dependency.
For example, an OpenAI application installs its OpenInference OpenAI
instrumentor in addition to the LLM extra.

## No LLM traces arrive

Check that the runtime has `ARIZE_ENABLED=true`, valid Arize credentials, and
the correct `ARIZE_PROJECT_NAME`. Initialize the wrapper before registering a
provider instrumentor and before making any provider call. Confirm the
application reaches normal shutdown so the tracer provider flushes spans.

For a custom or unsupported provider, use `telemetry.llm_call()` or the
decorator. A web-server or HTTP-client span alone is not an LLM span and does
not carry model-level semantics.

## Warning: required LLM attributes are missing

The warning identifies a manually created `openinference.span.kind=LLM` span
outside an `@telemetry.llm` or `telemetry.llm_call()` scope. Prefer one of
those helpers. In CI, call `initialize_llm(config, strict=True)` and test your
instrumented code path to surface the same gap immediately.

## Endpoint setting rejected

`ARIZE_ENDPOINT` is checked against the installed `arize-otel` function
signature to avoid silently ignoring a private endpoint. Install the
organization-approved version that supports an `endpoint` argument, or remove
the setting for the normal Arize cloud endpoint.

## Availability policy

With the default `ARIZE_FAIL_SILENTLY=false`, setup and ML submission problems
raise `ArizeWrapperInstrumentationError` with a context-rich message. Set it
to `true` only if the service owner has explicitly decided telemetry must not
affect request availability; the failure is then logged and the call becomes a
no-op. Configuration errors and missing dependencies remain explicit.
