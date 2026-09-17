# Integration guide

## 1. Install and configure

Install the required extra and put the `.env.example` values in the runtime
environment or the organization's secret manager. `ArizeConfig.from_env()`
reports every missing required variable in one error, rather than failing one
at a time.

```python
from arize_wrapper import ArizeConfig

config = ArizeConfig.from_env()
```

Required configuration:

- `ARIZE_SPACE_ID`, `ARIZE_API_KEY`, `ARIZE_PROJECT_NAME`
- `ARIZE_SERVICE_NAME`, `ARIZE_DEPLOYMENT_ENVIRONMENT`, `ARIZE_TENANT`

Optional configuration:

- `ARIZE_SERVICE_VERSION` adds model/service version metadata.
- `ARIZE_ENDPOINT` supports a private endpoint only when the installed
  approved `arize-otel` version exposes an `endpoint` argument; otherwise the
  wrapper fails early with an actionable message.
- `ARIZE_ENABLED=false` turns the integration into a safe local no-op.
- `ARIZE_FAIL_SILENTLY=true` logs initialization/submission errors and
  continues without telemetry. Keep it `false` for staging and production
  unless an availability decision explicitly says otherwise.

## 2. LLM instrumentation methods

### Decorator (recommended for one function = one model invocation)

```python
from arize_wrapper.llm import initialize_llm

telemetry = initialize_llm(config)

@telemetry.llm(
    prompt_template="Classify sentiment: {text}",
    prompt_template_version="v2",
    temperature=0.0,
)
def classify(text: str) -> str:
    return model.generate(text, temperature=0.0)
```

### Context manager

```python
with telemetry.llm_call(
    prompt_template="Classify sentiment: {text}",
    prompt_template_version="v2",
    temperature=0.0,
    span_name="sentiment.classify",
):
    result = model.generate(text, temperature=0.0)
```

### Existing provider auto-instrumentation

Initialize this wrapper before registering the provider instrumentor. The
wrapper applies required fields to its own span and to spans created inside
the active decorator/context-manager scope. The provider instrumentor remains
responsible for its model-specific semantic attributes.

```python
telemetry = initialize_llm(config)
OpenAIInstrumentor().instrument(tracer_provider=telemetry.tracer_provider)
```

## 3. Classical ML logging

Use the `arize` SDK's normal model type, environment, and schema fields, but
do not add the three organization identity columns yourself. The wrapper
copies the dataframe and injects them.

```python
client = init_ml_client(config)
log_predictions(
    client=client,
    config=config,
    dataframe=predictions,
    schema_kwargs={
        "prediction_id_column_name": "prediction_id",
        "feature_column_names": ["amount"],
        "prediction_label_column_name": "prediction",
    },
    model_type=ModelTypes.BINARY_CLASSIFICATION,
    environment=Environments.PRODUCTION,
)
```

See `examples/llm_openai_example.py` and `examples/ml_example.py` for complete
application-shaped samples and the Arize AX UI for delivery verification.
