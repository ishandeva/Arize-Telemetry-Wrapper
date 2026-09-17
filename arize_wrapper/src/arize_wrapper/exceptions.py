"""Stable exception hierarchy exposed by :mod:`arize_wrapper`."""


class ArizeWrapperError(Exception):
    """Base exception for this package."""


class ArizeWrapperConfigError(ArizeWrapperError):
    """Configuration is absent, invalid, or inconsistent."""


class ArizeWrapperInstrumentationError(ArizeWrapperError):
    """Arize setup or telemetry submission could not be completed."""


class MissingOptionalDependencyError(ArizeWrapperError):
    """A caller used an integration whose optional dependencies are absent."""
