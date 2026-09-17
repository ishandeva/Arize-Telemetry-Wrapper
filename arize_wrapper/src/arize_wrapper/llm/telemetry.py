"""High-level helpers and decorators for manually tracing LLM calls."""

from __future__ import annotations

import functools
import inspect
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional, Union

from ..config import ArizeConfig
from ..constants import build_llm_attributes
from .context import llm_attribute_context

TemperatureValue = Union[float, Callable[..., float]]


def _resolve_temperature(value: TemperatureValue, args: tuple, kwargs: dict) -> float:
    resolved = value(*args, **kwargs) if callable(value) else value
    return float(resolved)


class ArizeTelemetry:
    """A configured LLM telemetry facade returned by :func:`initialize_llm`.

    A call wrapped with :meth:`llm` gets a provider-neutral manual LLM span.
    The same required attributes also flow to any child span created by an
    OpenInference auto-instrumentor, so applications may combine this wrapper
    with a provider-specific instrumentor without another standards layer.
    """

    def __init__(self, config: ArizeConfig, tracer_provider: Any) -> None:
        self.config = config
        self.tracer_provider = tracer_provider

    @property
    def enabled(self) -> bool:
        return self.tracer_provider is not None

    def get_tracer(self, name: str = "arize_wrapper") -> Any:
        if not self.enabled:
            return None
        return self.tracer_provider.get_tracer(name)

    @contextmanager
    def llm_call(
        self,
        *,
        prompt_template: str,
        prompt_template_version: str,
        temperature: float,
        span_name: str = "llm.call",
    ) -> Iterator[Any]:
        """Create a manual LLM span with every required organization field."""
        with llm_attribute_context(
            prompt_template=prompt_template,
            prompt_template_version=prompt_template_version,
            temperature=temperature,
        ) as attributes:
            if not self.enabled:
                yield None
                return
            from opentelemetry.trace import Status, StatusCode

            tracer = self.get_tracer()
            with tracer.start_as_current_span(span_name) as span:
                # Explicit assignment makes the helper work with any compliant
                # provider, not only with our processor.
                for key, value in attributes.items():
                    span.set_attribute(key, value)
                try:
                    yield span
                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    raise
                else:
                    span.set_status(Status(StatusCode.OK))

    def llm(
        self,
        *,
        prompt_template: str,
        prompt_template_version: str,
        temperature: TemperatureValue,
        span_name: Optional[str] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorate a sync or async function that performs one LLM invocation.

        ``temperature`` may be a number or a callable receiving the decorated
        function's ``*args`` and ``**kwargs``.  The latter supports request
        specific model settings without weakening required-field validation.
        """

        def decorator(function: Callable[..., Any]) -> Callable[..., Any]:
            name = span_name or function.__qualname__
            if inspect.iscoroutinefunction(function):

                @functools.wraps(function)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    resolved = _resolve_temperature(temperature, args, kwargs)
                    with self.llm_call(
                        prompt_template=prompt_template,
                        prompt_template_version=prompt_template_version,
                        temperature=resolved,
                        span_name=name,
                    ):
                        return await function(*args, **kwargs)

                return async_wrapper

            @functools.wraps(function)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                resolved = _resolve_temperature(temperature, args, kwargs)
                with self.llm_call(
                    prompt_template=prompt_template,
                    prompt_template_version=prompt_template_version,
                    temperature=resolved,
                    span_name=name,
                ):
                    return function(*args, **kwargs)

            return wrapper

        return decorator

    def required_llm_attributes(
        self, *, prompt_template: str, prompt_template_version: str, temperature: float
    ) -> dict:
        """Expose the exact dynamic attributes for custom integration code."""
        return build_llm_attributes(
            prompt_template=prompt_template,
            prompt_template_version=prompt_template_version,
            temperature=temperature,
        )
