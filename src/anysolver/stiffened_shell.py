"""Explicit experimental entry for the developing stiffened-shell profiles.

Capabilities report the exact implemented subset. G0-G6 qualification and
release are separate decisions tied to final installed artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from ._stiffened_shell_staged_load_experimental import StagedDeadLoadProgramme
from ._stiffened_shell_ge_reference_modal import (
    GEReferenceModesRequest, GEReferenceModesResult, GEFreeReferenceModesResult,
    GE_FREE_FREE_MODAL_ONLY_V1,
)

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
from ._stiffened_shell_point_recovery import PointTransferWrench
from ._stiffened_shell_nodal_footprint import (
    INCREMENT_ORIGIN_CHART_POLICY as GE_NODAL_FOOTPRINT_INCREMENT_ORIGIN_CHART_V2,
)
from ._stiffened_shell_increment_control import (
    AdaptiveIncrementControl, IncrementAttempt, FiniteIncrementFailure,
    AdaptiveIncrementExhausted,
)
from ._stiffened_shell_b2_q4_point_experimental import (
    ExperimentalB2Q4PointAnalysis,
)
from ._stiffened_shell_b2_q4_panel_experimental import (
    ExperimentalB2Q4PanelAnalysis, Q4PanelShell, Q4B2Point,
    ExperimentalB2MixedPanelAnalysis, S3V2DPanelShell,
    ExperimentalB2MixedPanelCapabilities,
    ExperimentalB2Q4PanelResponseEnvelope,
    B2ReferenceModesRequest, B2ReferenceModesResult,
    B2FootprintReferenceModesResult, B2ModalConstraintRow,
    ExperimentalB2Q4FootprintResult, ExperimentalB2Q4FootprintSelectedCase,
    ExperimentalB2Q4FootprintBatchResult, ExperimentalB2Q4FootprintCapabilities,
)
from ._stiffened_shell_b2_nodal_footprint import (
    B2NodalRigidFootprint, B2NodalRigidFootprintSelection,
    B2NodalRigidFootprintWrench, B2NodalFootprintNodeAction,
)

from ._stiffened_shell_ge_experimental import (
    PROFILE as B3_GE_E4_PL_STIFFENED_SHELL_V1,
    ExperimentalGEAnalysis, ExperimentalL1Line, ExperimentalBL5Line,
    FixedCoordinate,
    LinearDefinition, LinearResult,
    NodalAction, PointConnection, ShellPanel,
    NodalRigidFootprint, NodalRigidFootprintSelection, NodalRigidFootprintWrench,
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
    """Experimental reference-linear Q4/B2 points or explicit nodal footprints.

    Empty footprints preserve the historical finite-vertex point route.
    Nonempty footprints admit virgin supported reference modes with complete
    physical mass and coordinate supports. They lock normal spin and retain
    incomplete mechanical qualification.
    """

    profile: str
    shell_nodes_m: object
    shells: tuple[Q4PanelShell, ...]
    members: tuple[PhysicalB2Member | CompiledPhysicalB2Member, ...]
    points: tuple[Q4B2Point, ...]
    transformation: object
    prescribed_offset: object
    footprints: tuple[B2NodalRigidFootprint, ...] = ()


@dataclass(frozen=True)
class B2MixedPanelDefinition:
    """Opt-in elastic Q4/native S3 V2D/B2 finite-vertex point panel.

    Any S3 facet restricts this definition to static solves. S3 inertia,
    spectral analysis and nodal footprints remain deferred.
    """

    profile: str
    shell_nodes_m: object
    shells: tuple[Q4PanelShell | S3V2DPanelShell, ...]
    members: tuple[PhysicalB2Member | CompiledPhysicalB2Member, ...]
    points: tuple[Q4B2Point, ...]
    transformation: object
    prescribed_offset: object
    footprints: tuple[B2NodalRigidFootprint, ...] = ()


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
            prescribed_offset=definition.prescribed_offset,
            footprints=definition.footprints)
    if type(definition) is B2MixedPanelDefinition:
        if definition.profile != B2_E4_PL_FAST_LINEAR_V1 or resources is not None:
            raise ValueError("explicit experimental B2 mixed-panel definition required")
        return ExperimentalB2MixedPanelAnalysis(
            definition.shell_nodes_m, definition.shells,
            definition.members, definition.points,
            transformation=definition.transformation,
            prescribed_offset=definition.prescribed_offset,
            footprints=definition.footprints)
    raise ValueError("unsupported stiffened-shell definition/profile")


__all__ = [
    "AdaptiveIncrementControl", "IncrementAttempt", "FiniteIncrementFailure",
    "AdaptiveIncrementExhausted",
    "Q4_ALGORITHMIC_PULLBACK_V1",
    "B3_GE_E4_PL_STIFFENED_SHELL_V1", "B2_E4_PL_FAST_LINEAR_V1",
    "ShellPanel", "PointConnection", "PointTransferWrench",
    "NodalRigidFootprint", "NodalRigidFootprintSelection", "NodalRigidFootprintWrench",
    "FixedCoordinate", "NodalAction", "LinearDefinition", "LinearResult",
    "StagedDeadLoadProgramme",
    "GEReferenceModesRequest", "GEReferenceModesResult",
    "GEFreeReferenceModesResult", "GE_FREE_FREE_MODAL_ONLY_V1",
    "GE_NODAL_FOOTPRINT_INCREMENT_ORIGIN_CHART_V2",
    "B2LinearDefinition", "B2Q4PointDefinition", "B2Q4PanelDefinition",
    "B2MixedPanelDefinition", "S3V2DPanelShell", "ExperimentalB2MixedPanelCapabilities",
    "PhysicalB2Member", "LinearSection", "Q4PanelShell", "Q4B2Point",
    "MassMetadata", "B2ReferenceModesRequest", "B2ReferenceModesResult",
    "B2FootprintReferenceModesResult", "B2ModalConstraintRow",
    "B2NodalRigidFootprint", "B2NodalRigidFootprintSelection",
    "B2NodalRigidFootprintWrench", "B2NodalFootprintNodeAction",
    "ExperimentalB2Q4FootprintResult", "ExperimentalB2Q4FootprintSelectedCase",
    "ExperimentalB2Q4FootprintBatchResult", "ExperimentalB2Q4FootprintCapabilities",
    "B2_BOUNDED_OUTPUT_REPRESENTATION_V1", "OutputRepresentationCertificate",
    "OutputRepresentationError", "RepresentabilityError",
    "create_analysis",
]
