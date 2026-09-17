# Arize Telemetry Wrapper

`arize-telemetry-wrapper` is the organization-standard Python integration for
Arize AX. It centralizes client setup, configuration validation, required
attribute collection, error handling, and lightweight LLM instrumentation.
Application teams provide their model call and business logic; the wrapper
provides consistent telemetry.

## Install

Install only the capability the application uses:

```bash
pip install "arize-telemetry-wrapper[llm]"
pip install "arize-telemetry-wrapper[ml]"
```

An LLM application using a provider auto-instrumentor must additionally
install that provider's OpenInference instrumentor (for example,
`openinference-instrumentation-openai`). The wrapper deliberately does not
choose or install a provider-specific integration for an application.

## Configure

Copy `.env.example` values into the deployment's secret manager. At a minimum
set the Arize connection values plus `ARIZE_SERVICE_NAME`,
`ARIZE_DEPLOYMENT_ENVIRONMENT`, and `ARIZE_TENANT`. Never commit an API key.

```python
from arize_wrapper import ArizeConfig
from arize_wrapper.llm import initialize_llm

telemetry = initialize_llm(ArizeConfig.from_env())
```

## Instrument one LLM call

```python
from arize_wrapper import ArizeConfig
from arize_wrapper.llm import initialize_llm

telemetry = initialize_llm(ArizeConfig.from_env())

@telemetry.llm(
    prompt_template="Summarize this ticket: {ticket_text}",
    prompt_template_version="2026-09-01",
    temperature=0.2,
)
def summarize(ticket_text: str) -> str:
    return call_your_llm(ticket_text, temperature=0.2)
```

The decorator starts an LLM span and sets all six required fields. Use
`telemetry.llm_call(...)` when decorating a function is inconvenient. For an
async function, the same decorator works and its context follows `asyncio`
tasks.

For a dynamic temperature, pass a resolver:

```python
@telemetry.llm(
    prompt_template="Answer: {question}",
    prompt_template_version="v4",
    temperature=lambda _question, temperature=0.2: temperature,
)
def answer(question: str, temperature: float = 0.2) -> str:
    return call_your_llm(question, temperature=temperature)
```

## Classical ML prediction logging

```python
from arize_wrapper import ArizeConfig
from arize_wrapper.ml import init_ml_client, log_predictions

config = ArizeConfig.from_env()
client = init_ml_client(config)
response = log_predictions(
    client=client,
    config=config,
    dataframe=prediction_dataframe,
    schema_kwargs={"prediction_id_column_name": "prediction_id"},
    model_type=model_type,
    environment=environment,
)
```

The helper injects the organization identity as `arize_tenant`,
`arize_service_name`, and `arize_deployment_environment` tag columns. Prompt
template and temperature fields are LLM-only and do not apply to a batch ML
payload.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Required attributes](docs/ATTRIBUTES.md)
- [Integration guide](docs/INTEGRATION_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Versioning and release](docs/VERSIONING_AND_RELEASE.md)

Runnable examples are in `examples/`. The test suite does not send data to
Arize and does not require credentials.
