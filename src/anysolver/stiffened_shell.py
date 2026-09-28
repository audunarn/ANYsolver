"""Explicit experimental entry for the developing stiffened-shell profiles.

Capabilities report the exact implemented subset. G0-G6 qualification and
release are separate decisions tied to final installed artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._b2_physical_linear_definition import (
    PROFILE_ID as B2_E4_PL_FAST_LINEAR_V1,
    PhysicalB2Member, CompiledPhysicalB2Member,
)
from ._stiffened_shell_b2_experimental import ExperimentalB2Analysis

from ._stiffened_shell_ge_experimental import (
    PROFILE as B3_GE_E4_PL_STIFFENED_SHELL_V1,
    ExperimentalGEAnalysis, FixedCoordinate, LinearDefinition, LinearResult,
    NodalAction, PointConnection, ShellPanel,
)


@dataclass(frozen=True)
class B2LinearDefinition:
    """Experimental physical B2 graph with an explicit audited affine plan.

    Shell attachment is not yet implemented by this definition.  The separate
    profile identity is retained for the intended complete workflow; runtime
    capabilities state the smaller currently admitted operation set.
    """

    profile: str
    members: tuple[PhysicalB2Member | CompiledPhysicalB2Member, ...]
    transformation: object
    prescribed_offset: object
    selected_dofs: object
    max_rhs_chunk: int = 8


def create_analysis(*, definition, resources=None):
    """Create the explicitly selected experimental owner for an admitted profile."""
    if type(definition) is LinearDefinition:
        return ExperimentalGEAnalysis(definition, resources=resources)
    if type(definition) is B2LinearDefinition:
        if definition.profile != B2_E4_PL_FAST_LINEAR_V1 or resources is not None:
            raise ValueError("explicit experimental physical B2 definition required")
        return ExperimentalB2Analysis(
            definition.members, definition.transformation,
            definition.prescribed_offset, definition.selected_dofs,
            max_rhs_chunk=definition.max_rhs_chunk)
    raise ValueError("unsupported stiffened-shell definition/profile")


__all__ = [
    "B3_GE_E4_PL_STIFFENED_SHELL_V1", "B2_E4_PL_FAST_LINEAR_V1",
    "ShellPanel", "PointConnection",
    "FixedCoordinate", "NodalAction", "LinearDefinition", "LinearResult",
    "B2LinearDefinition",
    "create_analysis",
]
