# Required attributes

The following organization fields are the supported Confluence contract for
version `0.1.0` of this wrapper. Extend this table and the constants module in
a backward-compatible release when the organization changes its standard.

| Required Arize path | Source | LLM representation | Classical ML representation |
| --- | --- | --- | --- |
| `attributes.metadata.service.name` | `ARIZE_SERVICE_NAME` | `metadata = {"service":{"name": ...}}` | `arize_service_name` tag column |
| `attributes.metadata.deployment.environment` | `ARIZE_DEPLOYMENT_ENVIRONMENT` | `metadata = {"deployment":{"environment": ...}}` | `arize_deployment_environment` tag column |
| `attributes.metadata.tenant` | `ARIZE_TENANT` | `metadata = {"tenant": ...}` | `arize_tenant` tag column |
| `attributes.llm.temperature` | `@telemetry.llm(temperature=...)` or `llm_call()` | `llm.temperature` and `llm.invocation_parameters` | Not applicable to a prediction batch |
| `attributes.llm.prompt_template.version` | Required decorator/context-manager argument | `llm.prompt_template.version` | Not applicable to a prediction batch |
| `attributes.llm.prompt_template.template` | Required decorator/context-manager argument | `llm.prompt_template.template` | Not applicable to a prediction batch |

`metadata` is intentionally a single JSON-valued OpenInference attribute.
Arize flattens its contents to the `attributes.metadata.*` values listed
above. The package preserves application-defined metadata keys but always
overwrites the three required identity values with `ArizeConfig`, avoiding
cross-tenant or wrong-service telemetry.

`llm.invocation_parameters` is an additional standard OpenInference JSON
attribute. It is emitted alongside the explicitly required `llm.temperature`
so auto-instrumented Arize views retain their normal parameter behavior.

`ARIZE_SERVICE_VERSION` is optional and, when supplied, is added as
`metadata.service.version` on LLM spans and as `model_version` for ML logging.
