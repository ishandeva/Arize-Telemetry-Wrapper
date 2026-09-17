"""Context-local dynamic attributes for a single LLM invocation."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Iterator, Optional

from ..constants import build_llm_attributes
from ..exceptions import ArizeWrapperConfigError

_active_llm_attributes: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "arize_wrapper_active_llm_attributes", default=None
)


def current_llm_attributes() -> Optional[Dict[str, Any]]:
    """Return a copy of invocation attributes active in this execution context."""
    attributes = _active_llm_attributes.get()
    return None if attributes is None else dict(attributes)


def _validate_llm_values(
    prompt_template: str, prompt_template_version: str, temperature: float
) -> None:
    if not isinstance(prompt_template, str) or not prompt_template.strip():
        raise ArizeWrapperConfigError("prompt_template must be a non-empty string.")
    if not isinstance(prompt_template_version, str) or not prompt_template_version.strip():
        raise ArizeWrapperConfigError(
            "prompt_template_version must be a non-empty string."
        )
    if isinstance(temperature, bool):
        raise ArizeWrapperConfigError("temperature must be a finite numeric value.")
    try:
        numeric = float(temperature)
    except (TypeError, ValueError) as exc:
        raise ArizeWrapperConfigError(
            "temperature must be a finite numeric value."
        ) from exc
    if numeric != numeric or numeric in (float("inf"), float("-inf")):
        raise ArizeWrapperConfigError("temperature must be a finite numeric value.")


@contextmanager
def llm_attribute_context(
    *, prompt_template: str, prompt_template_version: str, temperature: float
) -> Iterator[Dict[str, Any]]:
    """Make required LLM values visible to spans created in this context.

    :class:`~arize_wrapper.llm.enforcement.EnforcedMetadataSpanProcessor`
    reads this context during ``on_start``.  Context variables propagate over
    ``asyncio`` tasks, which makes the helper safe for async LLM applications.
    """
    _validate_llm_values(prompt_template, prompt_template_version, temperature)
    attributes = build_llm_attributes(
        prompt_template=prompt_template,
        prompt_template_version=prompt_template_version,
        temperature=float(temperature),
    )
    token = _active_llm_attributes.set(attributes)
    try:
        yield dict(attributes)
    finally:
        _active_llm_attributes.reset(token)
