"""Opt-in contact definitions and coupled static contact profiles."""

from .core import (
    ContactDefinition,
    ContactInteraction,
    ContactResults,
    ContactSolverSettings,
    ContactSurface,
    ContactValidationReport,
    RigidContactBody,
    validate_general_contact,
)

__all__ = [
    "ContactDefinition",
    "ContactInteraction",
    "ContactResults",
    "ContactSolverSettings",
    "ContactSurface",
    "ContactValidationReport",
    "RigidContactBody",
    "validate_general_contact",
]
