"""Opt-in contact definitions and coupled static contact profiles."""

from importlib import import_module


_CORE_EXPORTS = frozenset({
    "ContactDefinition", "ContactInteraction", "ContactResults",
    "ContactSolverSettings", "ContactSurface", "ContactValidationReport",
    "RigidContactBody", "validate_general_contact",
})
_CAPABILITY_EXPORTS = frozenset({
    "ContactCapabilityReport", "report_general_contact_capability",
})
_STATIC_EXPORTS = frozenset({
    "ContactPathControl", "ContactPathNodalForce", "ContactPathProgram",
    "solve_static_contact_path",
})
_REQUEST_EXPORTS = frozenset({
    "ContactRequestIdentity", "ContactRequestIdentityError",
    "identify_general_contact_request", "verify_general_contact_request",
})
_SKIN_EXPORTS = frozenset({
    "ContactSkinGeometryError", "ContactShellSkinFace", "ContactShellSkinGeometry",
    "recover_general_contact_shell_skins",
})
_TRANSIENT_EXPORTS = frozenset({
    "ContactNodalLoadHistory", "ContactTransientSolverControls",
    "TransientContactResults", "TransientContactSettings",
    "solve_transient_contact",
})
_NATIVE_EXPORTS = frozenset({'NativeS3ContactPair', 'create_native_contact_analysis'})


def __getattr__(name: str):
    if name == "RigidCappedCylinder":
        module = "capped_cylinder"
    elif name in _CORE_EXPORTS:
        module = "core"
    elif name in _CAPABILITY_EXPORTS:
        module = "capability"
    elif name in _STATIC_EXPORTS:
        module = "static_path"
    elif name in _REQUEST_EXPORTS:
        module = "request_identity"
    elif name in _SKIN_EXPORTS:
        module = "skin_geometry"
    elif name in _TRANSIENT_EXPORTS:
        module = "transient"
    elif name in _NATIVE_EXPORTS:
        module = "native_multi_s3_static"
    elif name == 'NativeContactActivationSettings':
        module = 'native_activation_static'
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f".{module}", __name__), name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))

__all__ = [
    "NativeS3ContactPair", "create_native_contact_analysis",
    "NativeContactActivationSettings",
    "RigidCappedCylinder",
    "ContactCapabilityReport",
    "ContactDefinition",
    "ContactInteraction",
    "ContactResults",
    "ContactSolverSettings",
    "ContactSurface",
    "ContactValidationReport",
    "RigidContactBody",
    "validate_general_contact",
    "report_general_contact_capability",
    "ContactPathControl",
    "ContactPathNodalForce",
    "ContactPathProgram",
    "solve_static_contact_path",
    "ContactRequestIdentity",
    "ContactRequestIdentityError",
    "identify_general_contact_request",
    "verify_general_contact_request",
    "ContactSkinGeometryError",
    "ContactShellSkinFace",
    "ContactShellSkinGeometry",
    "recover_general_contact_shell_skins",
    "ContactNodalLoadHistory",
    "ContactTransientSolverControls",
    "TransientContactResults",
    "TransientContactSettings",
    "solve_transient_contact",
]
