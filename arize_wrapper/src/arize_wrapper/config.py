"""Configuration loading and validation for Arize telemetry."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Optional

from .exceptions import ArizeWrapperConfigError

_REQUIRED_ENVIRONMENT_KEYS = (
    "ARIZE_SPACE_ID",
    "ARIZE_API_KEY",
    "ARIZE_PROJECT_NAME",
    "ARIZE_SERVICE_NAME",
    "ARIZE_DEPLOYMENT_ENVIRONMENT",
    "ARIZE_TENANT",
)


def _as_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ArizeWrapperConfigError(
        "ARIZE_ENABLED must be one of true/false, 1/0, yes/no, or on/off."
    )


@dataclass(frozen=True)
class ArizeConfig:
    """Connection and organization identity required to initialize telemetry.

    Secrets belong in a secret manager or environment variables, not source
    control.  ``service_version`` and ``endpoint`` are optional enhancements;
    the six fields in :meth:`required_attributes` are always enforced for LLM
    spans created through this package.
    """

    space_id: str
    api_key: str
    project_name: str
    service_name: str
    deployment_environment: str
    tenant: str
    service_version: Optional[str] = None
    endpoint: Optional[str] = None
    enabled: bool = True
    fail_silently: bool = False

    def __post_init__(self) -> None:
        required = {
            "space_id": self.space_id,
            "api_key": self.api_key,
            "project_name": self.project_name,
            "service_name": self.service_name,
            "deployment_environment": self.deployment_environment,
            "tenant": self.tenant,
        }
        blank = [name for name, value in required.items() if not str(value).strip()]
        if blank:
            raise ArizeWrapperConfigError(
                "arize_wrapper configuration values cannot be empty: "
                + ", ".join(blank)
            )

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> "ArizeConfig":
        """Read configuration from an environment mapping (``os.environ`` by default)."""
        values = os.environ if environ is None else environ
        missing = [key for key in _REQUIRED_ENVIRONMENT_KEYS if not values.get(key)]
        if missing:
            raise ArizeWrapperConfigError(
                "Missing required Arize configuration: "
                + ", ".join(missing)
                + ". Copy .env.example and configure your secret manager."
            )
        enabled_value = values.get("ARIZE_ENABLED", "true")
        return cls(
            space_id=values["ARIZE_SPACE_ID"],
            api_key=values["ARIZE_API_KEY"],
            project_name=values["ARIZE_PROJECT_NAME"],
            service_name=values["ARIZE_SERVICE_NAME"],
            deployment_environment=values["ARIZE_DEPLOYMENT_ENVIRONMENT"],
            tenant=values["ARIZE_TENANT"],
            service_version=values.get("ARIZE_SERVICE_VERSION") or None,
            endpoint=values.get("ARIZE_ENDPOINT") or None,
            enabled=_as_bool(enabled_value),
            fail_silently=_as_bool(values.get("ARIZE_FAIL_SILENTLY", "false")),
        )

    @property
    def environment(self) -> str:
        """Compatibility alias for code that calls the field ``environment``."""
        return self.deployment_environment

    def required_attributes(self) -> Mapping[str, str]:
        """Return the three static organization-required metadata values."""
        return {
            "attributes.metadata.service.name": self.service_name,
            "attributes.metadata.deployment.environment": self.deployment_environment,
            "attributes.metadata.tenant": self.tenant,
        }
