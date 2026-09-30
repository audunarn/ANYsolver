"""Explicit experimental entry for the developing stiffened-shell profiles.

Capabilities report the exact implemented subset. G0-G6 qualification and
release are separate decisions tied to final installed artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._b2_physical_linear_definition import (
    PROFILE_ID as B2_E4_PL_FAST_LINEAR_V1,
    PhysicalB2Member, CompiledPhysicalB2Member, MassMetadata,
)
from ._b2_physical_flexibility_linear import (
    LinearSection, RepresentabilityError, OutputRepresentationError,
    OutputRepresentationCertificate,
    OUTPUT_REPRESENTATION_ID as B2_BOUNDED_OUTPUT_REPRESENTATION_V1,
)
from ._stiffened_shell_b2_experimental import ExperimentalB2Analysis
from ._stiffened_shell_b2_q4_point_experimental import (
    ExperimentalB2Q4PointAnalysis,
)
from ._stiffened_shell_b2_q4_panel_experimental import (
    ExperimentalB2Q4PanelAnalysis, Q4PanelShell, Q4B2Point,
    B2ReferenceModesRequest, B2ReferenceModesResult,
)

from ._stiffened_shell_ge_experimental import (
    PROFILE as B3_GE_E4_PL_STIFFENED_SHELL_V1,
    ExperimentalGEAnalysis, ExperimentalL1Line, ExperimentalBL5Line,
    FixedCoordinate,
    LinearDefinition, LinearResult,
    NodalAction, PointConnection, ShellPanel,
    Q4_ALGORITHMIC_PULLBACK_V1,
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


@dataclass(frozen=True)
class B2Q4PointDefinition:
    """One elastic Q4 and one physical B2 member with a reference point tie."""

    profile: str
    member: PhysicalB2Member | CompiledPhysicalB2Member
    shell_vertices_m: object
    shell_E: float
    shell_nu: float
    shell_thickness_m: float
    station: float
    transformation: object
    prescribed_offset: object
    offset_local_m: tuple[float, float, float] = (0., 0., 0.)
    reference_normal: tuple[float, float, float] = (0., 0., 1.)


@dataclass(frozen=True)
class B2Q4PanelDefinition:
    """Experimental multi-Q4/multi-B2 point panel with an affine plan."""

    profile: str
    shell_nodes_m: object
    shells: tuple[Q4PanelShell, ...]
    members: tuple[PhysicalB2Member | CompiledPhysicalB2Member, ...]
    points: tuple[Q4B2Point, ...]
    transformation: object
    prescribed_offset: object


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
    if type(definition) is B2Q4PointDefinition:
        if definition.profile != B2_E4_PL_FAST_LINEAR_V1 or resources is not None:
            raise ValueError("explicit experimental B2/Q4 point definition required")
        return ExperimentalB2Q4PointAnalysis(
            definition.member, definition.shell_vertices_m,
            shell_E=definition.shell_E, shell_nu=definition.shell_nu,
            shell_thickness_m=definition.shell_thickness_m,
            station=definition.station,
            transformation=definition.transformation,
            prescribed_offset=definition.prescribed_offset,
            offset_local_m=definition.offset_local_m,
            reference_normal=definition.reference_normal)
    if type(definition) is B2Q4PanelDefinition:
        if definition.profile != B2_E4_PL_FAST_LINEAR_V1 or resources is not None:
            raise ValueError("explicit experimental B2/Q4 panel definition required")
        return ExperimentalB2Q4PanelAnalysis(
            definition.shell_nodes_m, definition.shells,
            definition.members, definition.points,
            transformation=definition.transformation,
            prescribed_offset=definition.prescribed_offset)
    raise ValueError("unsupported stiffened-shell definition/profile")


__all__ = [
    "Q4_ALGORITHMIC_PULLBACK_V1",
    "B3_GE_E4_PL_STIFFENED_SHELL_V1", "B2_E4_PL_FAST_LINEAR_V1",
    "ShellPanel", "PointConnection",
    "FixedCoordinate", "NodalAction", "LinearDefinition", "LinearResult",
    "B2LinearDefinition", "B2Q4PointDefinition", "B2Q4PanelDefinition",
    "PhysicalB2Member", "LinearSection", "Q4PanelShell", "Q4B2Point",
    "MassMetadata", "B2ReferenceModesRequest", "B2ReferenceModesResult",
    "B2_BOUNDED_OUTPUT_REPRESENTATION_V1", "OutputRepresentationCertificate",
    "OutputRepresentationError", "RepresentabilityError",
    "create_analysis",
]
