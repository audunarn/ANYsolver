"""Opt-in contact definitions and coupled static contact profiles."""

from importlib import import_module


_CORE_EXPORTS = frozenset({
    "ContactDefinition", "ContactInteraction", "ContactResults",
    "ContactSolverSettings", "ContactSurface", "ContactValidationReport",
    "RigidContactBody", "validate_general_contact",
})
_STATIC_EXPORTS = frozenset({
    "ContactPathControl", "ContactPathNodalForce", "ContactPathProgram",
    "solve_static_contact_path",
})
_TRANSIENT_EXPORTS = frozenset({
    "ContactNodalLoadHistory", "ContactTransientSolverControls",
    "TransientContactResults", "TransientContactSettings",
    "solve_transient_contact",
})


def __getattr__(name: str):
    if name in _CORE_EXPORTS:
        module = "core"
    elif name in _STATIC_EXPORTS:
        module = "static_path"
    elif name in _TRANSIENT_EXPORTS:
        module = "transient"
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f".{module}", __name__), name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))

__all__ = [
    "ContactDefinition",
    "ContactInteraction",
    "ContactResults",
    "ContactSolverSettings",
    "ContactSurface",
    "ContactValidationReport",
    "RigidContactBody",
    "validate_general_contact",
    "ContactPathControl",
    "ContactPathNodalForce",
    "ContactPathProgram",
    "solve_static_contact_path",
    "ContactNodalLoadHistory",
    "ContactTransientSolverControls",
    "TransientContactResults",
    "TransientContactSettings",
    "solve_transient_contact",
]
