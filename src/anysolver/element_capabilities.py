"""Fail-closed guards for formulation-specific production capabilities."""

from __future__ import annotations

from typing import Any, Iterable


class ElementCapabilityError(NotImplementedError):
    """Raised before a workflow evaluates an element with a declared gap."""


def require_model_element_capabilities(
    model: Any,
    capabilities: str | Iterable[str],
    *,
    context: str,
) -> None:
    """Reject declared element gaps before assembly, state, or geometry work."""

    requested = (
        frozenset((capabilities,))
        if isinstance(capabilities, str)
        else frozenset(str(value) for value in capabilities)
    )
    if not requested:
        raise ValueError("at least one element capability is required")
    blocked: list[tuple[int, tuple[str, ...]]] = []
    elements = getattr(getattr(model, "mesh", None), "elements", {})
    for element_id, element in elements.items():
        gaps = frozenset(str(value) for value in getattr(element, "capability_gaps", ()))
        overlap = tuple(sorted(requested & gaps))
        if overlap:
            blocked.append((int(element_id), overlap))
    if not blocked:
        return
    blocked.sort(key=lambda item: item[0])
    details = "; ".join(
        f"{element_id} ({', '.join(gaps)})" for element_id, gaps in blocked[:8]
    )
    if len(blocked) > 8:
        details += f"; and {len(blocked) - 8} more"
    raise ElementCapabilityError(
        f"{context} is unavailable because element capability PARITY_GAP remains: "
        f"{details}"
    )


__all__ = ["ElementCapabilityError", "require_model_element_capabilities"]
