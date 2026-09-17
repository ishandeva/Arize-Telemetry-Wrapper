import pytest

from arize_wrapper.config import ArizeConfig
from arize_wrapper.exceptions import ArizeWrapperInstrumentationError
from arize_wrapper.ml import logger


class _Frame:
    def __init__(self, values=None):
        self.values = dict(values or {})

    def copy(self):
        return _Frame(self.values)

    def __setitem__(self, key, value):
        self.values[key] = value


class _Schema:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class _V7Client:
    def __init__(self):
        self.calls = []

    def log(self, **kwargs):
        self.calls.append(kwargs)
        return "logged-v7"


class _MLNamespace:
    def __init__(self, calls):
        self.calls = calls

    def log(self, **kwargs):
        self.calls.append(kwargs)
        return "logged-v8"


class _V8Client:
    def __init__(self):
        self.calls = []
        self.ml = _MLNamespace(self.calls)


def _config(fail_silently=False):
    return ArizeConfig(
        space_id="space",
        api_key="key",
        project_name="fraud",
        service_name="fraud-model",
        deployment_environment="production",
        tenant="tenant-a",
        service_version="3.1.0",
        fail_silently=fail_silently,
    )


@pytest.mark.parametrize("client_type, name_key", [(_V7Client, "model_id"), (_V8Client, "model_name")])
def test_ml_logger_injects_identity_columns_and_handles_client_versions(
    monkeypatch, client_type, name_key
):
    monkeypatch.setattr(logger, "_load_arize_types", lambda: _Schema)
    original = _Frame({"prediction": [1, 0]})
    client = client_type()

    result = logger.log_predictions(
        client=client,
        config=_config(),
        dataframe=original,
        schema_kwargs={"prediction_label_column_name": "prediction"},
        model_type="binary",
        environment="production",
    )

    assert result.startswith("logged")
    sent = client.calls[0]
    assert sent[name_key] == "fraud-model"
    assert sent["model_version"] == "3.1.0"
    assert sent["dataframe"].values["arize_tenant"] == "tenant-a"
    assert sent["dataframe"].values["arize_service_name"] == "fraud-model"
    assert sent["dataframe"].values["arize_deployment_environment"] == "production"
    assert "arize_tenant" not in original.values
    assert set(logger.REQUIRED_TAG_COLUMNS).issubset(
        sent["schema"].kwargs["tag_column_names"]
    )


def test_ml_logger_wraps_send_failures(monkeypatch):
    monkeypatch.setattr(logger, "_load_arize_types", lambda: _Schema)

    class BrokenClient:
        def log(self, **kwargs):
            raise RuntimeError("network unavailable")

    with pytest.raises(ArizeWrapperInstrumentationError, match="fraud-model"):
        logger.log_predictions(
            client=BrokenClient(),
            config=_config(),
            dataframe=_Frame(),
            schema_kwargs={},
            model_type="binary",
            environment="production",
        )


def test_disabled_ml_telemetry_is_a_safe_noop():
    disabled = ArizeConfig(
        space_id="space",
        api_key="key",
        project_name="fraud",
        service_name="fraud-model",
        deployment_environment="production",
        tenant="tenant-a",
        enabled=False,
    )
    assert (
        logger.log_predictions(
            client=None,
            config=disabled,
            dataframe=_Frame(),
            schema_kwargs={},
            model_type="binary",
            environment="production",
        )
        is None
    )
