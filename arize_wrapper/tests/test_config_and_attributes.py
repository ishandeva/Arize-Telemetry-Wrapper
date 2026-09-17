import json

import pytest

from arize_wrapper.config import ArizeConfig
from arize_wrapper.constants import (
    LLM_PROMPT_TEMPLATE,
    LLM_PROMPT_TEMPLATE_VERSION,
    LLM_TEMPERATURE,
    REQUIRED_ATTRIBUTE_PATHS,
    build_llm_attributes,
    build_metadata,
)
from arize_wrapper.exceptions import ArizeWrapperConfigError
from arize_wrapper.llm.setup import _register_provider, initialize_llm


def _environment():
    return {
        "ARIZE_SPACE_ID": "space",
        "ARIZE_API_KEY": "key",
        "ARIZE_PROJECT_NAME": "support",
        "ARIZE_SERVICE_NAME": "support-api",
        "ARIZE_DEPLOYMENT_ENVIRONMENT": "staging",
        "ARIZE_TENANT": "tenant-a",
    }


def test_from_env_reads_required_and_optional_values():
    environment = _environment()
    environment.update(
        {
            "ARIZE_SERVICE_VERSION": "1.2.3",
            "ARIZE_ENABLED": "yes",
            "ARIZE_FAIL_SILENTLY": "0",
        }
    )

    config = ArizeConfig.from_env(environment)

    assert config.service_name == "support-api"
    assert config.environment == "staging"
    assert config.service_version == "1.2.3"
    assert config.required_attributes() == {
        "attributes.metadata.service.name": "support-api",
        "attributes.metadata.deployment.environment": "staging",
        "attributes.metadata.tenant": "tenant-a",
    }


def test_from_env_reports_all_missing_values():
    with pytest.raises(ArizeWrapperConfigError) as error:
        ArizeConfig.from_env({"ARIZE_SPACE_ID": "space"})

    text = str(error.value)
    assert "ARIZE_API_KEY" in text
    assert "ARIZE_TENANT" in text


def test_invalid_boolean_is_actionable():
    environment = _environment()
    environment["ARIZE_ENABLED"] = "perhaps"
    with pytest.raises(ArizeWrapperConfigError, match="ARIZE_ENABLED"):
        ArizeConfig.from_env(environment)


def test_required_attribute_builders_use_exact_standard_names():
    metadata = build_metadata(
        service_name="support-api", environment="staging", tenant="tenant-a"
    )
    attributes = build_llm_attributes(
        prompt_template="Help {customer}",
        prompt_template_version="v3",
        temperature=0.25,
    )

    assert metadata == {
        "service": {"name": "support-api"},
        "deployment": {"environment": "staging"},
        "tenant": "tenant-a",
    }
    assert set(REQUIRED_ATTRIBUTE_PATHS) == {
        "attributes.metadata.service.name",
        "attributes.metadata.deployment.environment",
        "attributes.metadata.tenant",
        "attributes.llm.temperature",
        "attributes.llm.prompt_template.version",
        "attributes.llm.prompt_template.template",
    }
    assert attributes[LLM_TEMPERATURE] == 0.25
    assert attributes[LLM_PROMPT_TEMPLATE] == "Help {customer}"
    assert attributes[LLM_PROMPT_TEMPLATE_VERSION] == "v3"
    assert json.loads(attributes["llm.invocation_parameters"]) == {"temperature": 0.25}


def test_disabled_initialization_needs_no_vendor_dependency():
    config = ArizeConfig(
        space_id="space",
        api_key="key",
        project_name="support",
        service_name="support-api",
        deployment_environment="development",
        tenant="tenant-a",
        enabled=False,
    )
    telemetry = initialize_llm(config)
    assert telemetry.enabled is False
    assert telemetry.tracer_provider is None


def test_register_adapter_only_passes_supported_endpoint_arguments():
    calls = []

    def register(*, space_id, api_key, project_name, endpoint):
        calls.append(
            {
                "space_id": space_id,
                "api_key": api_key,
                "project_name": project_name,
                "endpoint": endpoint,
            }
        )
        return "provider"

    config = ArizeConfig(
        space_id="space",
        api_key="key",
        project_name="support",
        service_name="support-api",
        deployment_environment="development",
        tenant="tenant-a",
        endpoint="https://private.example",
    )
    assert _register_provider(config, register) == "provider"
    assert calls[0]["endpoint"] == "https://private.example"
