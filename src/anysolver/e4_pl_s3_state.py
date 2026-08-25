"""Committed-state primitives for the qualified E4-PL S3 companion.

This module deliberately contains no element or solver integration.  It
freezes the identity, shape, and canonical-fingerprint boundary needed before
the formulation-native incremental-director implementation can consume or
persist nonlinear state.

The physical bubble orientation is the fourth reconstructed director triad.
``bubble_rotation_last_increment`` is a reserved exact-zero slot: every new
inner solve starts from zero and no converged bubble increment is persisted.
It is intentionally distinct from ``alpha``, the material-hardening
coordinate.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy
from dataclasses import fields as dataclass_fields, is_dataclass
import hashlib
import json
import math
import re
from types import MappingProxyType
from typing import Any

import numpy as np

from anymaterial import StructuralMaterial, elastic_compliance_matrix, material_symmetry


FORMULATION_ID = "E4_PL_QUALIFIED_S3_COMPANION_V1"
FORMULATION_SCHEMA = "anysolver.e4_pl_s3.linear.v1"
MITC3_PLUS_SOURCE_URL = (
    "https://web.mit.edu/kjb/www/Principal_Publications/"
    "The_MITC3%2B_shell_element_and_its_performance.pdf"
)
MITC3_PLUS_SOURCE_BYTES = 1_146_142
MITC3_PLUS_SOURCE_SHA256 = (
    "182F52217277B55E17627B8C41A3A4626ED91ED5378399088E0EA1748AD93EF0"
)
MITC3_PLUS_EQUATION_MAP = MappingProxyType(
    {
        "bubble_interpolation": "equations_6_to_8",
        "internal_tying_directions": "equations_12_to_15",
        "assumed_covariant_shear": "equations_16_and_17",
    }
)
MITC3_PLUS_NONLINEAR_SOURCE_URL = (
    "https://web.mit.edu/kjb/www/Principal_Publications/"
    "The_MITC3%2B_shell_element_in_geometric_nonlinear_analysis.pdf"
)
MITC3_PLUS_NONLINEAR_SOURCE_BYTES = 2_312_312
MITC3_PLUS_NONLINEAR_SOURCE_SHA256 = (
    "8006F7EBB9A8A3D72F29C356F6C9D76668A38CC5DC80A9B48D489FC2A87E082A"
)
MITC3_PLUS_NONLINEAR_EQUATION_MAP = MappingProxyType(
    {
        "current_geometry": "equations_7_to_9",
        "director_update": "equations_10_to_15",
        "quadratic_director_increment": "equations_16_to_21",
        "incremental_green_lagrange": "equations_22_to_28",
        "assumed_nonlinear_covariant_shear": "equations_29_to_31",
    }
)
EXTERNAL_COORDINATE_LAYOUT_ID = "S3_EXTERNAL18_BUBBLE2_PL3_V1"
NONLINEAR_STATE_SCHEMA = "anysolver.e4_pl_s3.committed_state.v1"
NONLINEAR_STATE_VERSION = 1
NONLINEAR_STATE_LAYOUT_ID = "S3_TL_Q18_TRIADS4_BUBBLE2_STATION7_LAYERED_V1"
NONLINEAR_KINEMATICS_ID = (
    "MITC3_PLUS_TOTAL_LAGRANGIAN_INCREMENTAL_DIRECTORS_EQ7_31_V1"
)
DIRECTOR_GAUGE_ID = "MITC3_PLUS_EQ11_GLOBAL_EY_WITH_EZ_PARALLEL_FALLBACK_V1"
EXTERNAL_ROTATION_MAP_ID = (
    "GLOBAL_ADDITIVE_ROTATION_TO_EQ14_MINIMAL_DIRECTOR_SECOND_ORDER_V1"
)
BUBBLE_STATE_ROLE = "RESERVED_ZERO_NEW_INCREMENT_PREDICTOR_ONLY"
BUBBLE_PREDICTOR_COMMIT_POLICY_ID = "RESET_TO_ZERO_AFTER_EVERY_ACCEPTED_STEP_V1"
COMMIT_STATUS = "committed_converged"
STATE_MODE = "layered_material"

BUBBLE_CONVENTION = "hierarchical_rotation_relative_to_corner_average"
QUADRATURE_ID = "dunavant_degree5_7point"
NONLINEAR_POLICY_ID = "TOTAL_LAGRANGIAN_MITC3_PLUS_QUADRATIC_DIRECTOR_SCHUR_V1"
RECOVERY_POLICY_ID = "S3_NATIVE_LINEAR_PHYSICAL_RECOVERY_V1"
NONLINEAR_SOURCE_SHA256 = MITC3_PLUS_NONLINEAR_SOURCE_SHA256
BUBBLE_OFFSET_D = 1.0e-4
BUBBLE_OFFSET_EXACT = "1/10000"
BUBBLE_POLYNOMIAL_SCALE = 27.0
TYING_POINTS = MappingProxyType(
    {
        "A": (1.0 / 6.0, 2.0 / 3.0),
        "B": (2.0 / 3.0, 1.0 / 6.0),
        "C": (1.0 / 6.0, 1.0 / 6.0),
        "D": (1.0 / 3.0 + BUBBLE_OFFSET_D, 1.0 / 3.0 - 2.0 * BUBBLE_OFFSET_D),
        "E": (1.0 / 3.0 - 2.0 * BUBBLE_OFFSET_D, 1.0 / 3.0 + BUBBLE_OFFSET_D),
        "F": (1.0 / 3.0 + BUBBLE_OFFSET_D, 1.0 / 3.0 + BUBBLE_OFFSET_D),
    }
)
TYING_POINT_DEFINITIONS = MappingProxyType(
    {
        "A": ("1/6", "2/3"),
        "B": ("2/3", "1/6"),
        "C": ("1/6", "1/6"),
        "D": ("1/3+d", "1/3-2*d"),
        "E": ("1/3-2*d", "1/3+d"),
        "F": ("1/3+d", "1/3+d"),
    }
)
PL_BASIS_ID = "BARYCENTRIC_L1_L2_L3_V1"
PL_CONSTRAINT_ID = "THETA_D_MINUS_ONE_HALF_V_X_MINUS_U_Y_AT_NODES_V1"
PL_GRAM_SCALE_ID = "AREA_OVER_12_V1"
PL_GRAM_NUMERATOR = ((2.0, 1.0, 1.0), (1.0, 2.0, 1.0), (1.0, 1.0, 2.0))
PL_BLOCK_SIGN_ID = "KQT_EQ_C_TRANSPOSE_M_KTT_EQ_MINUS_M_OVER_KD_V1"
PL_CONDENSATION_ID = "KD_EQ_KD_C_TRANSPOSE_M_C_V1"
DRILL_SCALE_POLICY_ID = "HALF_MIN_GENERALIZED_EIGENVALUE_PTAP_AGAINST_G_V1"
DRILL_SCALE_PROJECTOR = ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0))
DRILL_SCALE_METRIC = ((2.0, 0.0), (0.0, 0.5))
DRILL_SCALE_INVERSE_METRIC_SQRT = (
    (1.0 / math.sqrt(2.0), 0.0),
    (0.0, math.sqrt(2.0)),
)
BUBBLE_MAX_ITERATIONS = 32
BUBBLE_RELATIVE_TOLERANCE = 5.0e-11
BUBBLE_STEP_TOLERANCE = 5.0e-13
BUBBLE_CONDITION_LIMIT = 1.0e14
BUBBLE_LINE_SEARCH_MIN_FACTOR = 1.0 / 128.0
BUBBLE_LINE_SEARCH_REDUCTION = 0.5
BUBBLE_FORCE_CONDENSATION_ID = "FQ_MINUS_KQA_SOLVE_KAA_FA_V1"
ISOTROPIC_CONSTITUTIVE_INTEGRATION_ID = "PLANE_STRESS_RETURN_MAP_CONSISTENT_V1"
ORTHOTROPIC_CONSTITUTIVE_INTEGRATION_ID = (
    "HILL48_PLANE_STRESS_RETURN_MAP_CONSISTENT_V1"
)
GENERALIZED_SECTION_INTEGRATION_ID = "STATELESS_TOTAL_GENERALIZED_STRAIN_V1"

CANONICALIZATION_ID = "RFC8259_SORTED_UTF8_COMPACT_LF_SIGNED_ZERO_NORMALIZED_V1"
ELEMENT_CONFIGURATION_DESCRIPTOR_SCHEMA = (
    "anysolver.e4_pl_s3.element_configuration.layered.v1"
)
MATERIAL_DESCRIPTOR_SCHEMA = "anysolver.e4_pl_s3.material.dataclass.v1"
MATERIAL_DESCRIPTOR_VALIDATION_ID = (
    "REGISTERED_ANYMATERIAL_DATACLASS_COMPLIANCE_CROSSCHECK_V1"
)
THICKNESS_QUADRATURE_ID = "GAUSS_LOBATTO_3_5_7_9_11_V1"
SUPPORTED_LOBATTO_LAYER_COUNTS = (3, 5, 7, 9, 11)
STATE_ARRAY_LAYOUT_ID = "S3_STATION_MAJOR_LAYER_BOTTOM_TO_TOP_MINOR_V1"
THICKNESS_COORDINATE_SIGN_ID = (
    "ZETA_MINUS_ONE_BOTTOM_OPPOSITE_DIRECTOR_TO_PLUS_ONE_TOP_ALONG_DIRECTOR_V1"
)
STATE_INTEGRITY_ID = "SHA256_CANONICAL_COMPLETE_STATE_EXCLUDING_DIGEST_V1"
STATE_REDUNDANCY_TOLERANCE_FACTOR = 128.0
STATE_REDUNDANCY_VALIDATION_ID = (
    "KINEMATIC_FROM_GENERALIZED_AND_INPLANE_RESULTANT_FROM_LAYER_STRESS_V1"
)
REFERENCE_GEOMETRY_VALIDATION_ID = (
    "QUALIFIED_ADMISSION_DERIVED_NUMBERED_FRAME_EXACT_IDENTITY_V1"
)
DIRECTOR_ORTHONORMALITY_TOLERANCE = 1.0e-12
DIRECTOR_GAUGE_SWITCH_TOLERANCE = 1.0e-12
DIRECTOR_GAUGE_PRIMARY_AXIS = (0.0, 1.0, 0.0)
DIRECTOR_GAUGE_FALLBACK_AXIS = (0.0, 0.0, 1.0)
MINIMUM_OWNER_NORMAL_ALIGNMENT = 1.0e-8
MINIMUM_NORMALIZED_TWICE_AREA = max(64.0 * np.finfo(np.float64).eps, 1.0e-14)
MINIMUM_ANGLE_DEG = 30.0
MAXIMUM_ANGLE_DEG = 150.0
MAXIMUM_EDGE_RATIO = 4.0
MINIMUM_CORNER_SCALED_JACOBIAN = 0.20
MINIMUM_NORMALIZED_AREA = 0.60
QUALITY_COMPARISON_TOLERANCE = 1.0e-12
REFERENCE_FRAME_MATCH_TOLERANCE = 1.0e-12
NUM_INTEGRATION_STATIONS = 7
GENERALIZED_COMPONENTS = 8
GENERALIZED_STRAIN_COMPONENT_ORDER = (
    "membrane_xx",
    "membrane_yy",
    "membrane_xy_engineering",
    "curvature_xx",
    "curvature_yy",
    "curvature_xy_engineering",
    "transverse_shear_xz_engineering",
    "transverse_shear_yz_engineering",
)
GENERALIZED_RESULTANT_COMPONENT_ORDER = (
    "membrane_force_xx",
    "membrane_force_yy",
    "membrane_force_xy_tensor",
    "bending_moment_xx",
    "bending_moment_yy",
    "bending_moment_xy_tensor",
    "transverse_shear_force_xz_tensor",
    "transverse_shear_force_yz_tensor",
)
LAYER_STRAIN_COMPONENT_ORDER = (
    "inplane_xx",
    "inplane_yy",
    "inplane_xy_engineering",
)
LAYER_STRESS_COMPONENT_ORDER = (
    "inplane_xx",
    "inplane_yy",
    "inplane_xy_tensor",
)
# Compatibility aliases are retained for research callers, but the fingerprint
# and field manifest below always use the unambiguous strain/resultant names.
GENERALIZED_COMPONENT_ORDER = GENERALIZED_STRAIN_COMPONENT_ORDER
LAYER_COMPONENT_ORDER = LAYER_STRAIN_COMPONENT_ORDER

EXTERNAL_NODE_COORDINATE_ORDER = (
    "translation_global_x",
    "translation_global_y",
    "translation_global_z",
    "additive_rotation_global_x",
    "additive_rotation_global_y",
    "additive_rotation_global_z",
)
EXTERNAL_NODE_FORCE_ORDER = (
    "force_global_x",
    "force_global_y",
    "force_global_z",
    "moment_global_x",
    "moment_global_y",
    "moment_global_z",
)

INITIAL_FIELD_NAMES = (
    "initial_membrane_stress",
    "initial_bending_stress",
    "initial_membrane_prestrain",
    "initial_curvature_prestrain",
)

STIFFNESS_STATION_TABLE = (
    (1.0 / 3.0, 1.0 / 3.0, 0.1125),
    (0.470142064105115, 0.470142064105115, 0.066197076394253),
    (0.059715871789770, 0.470142064105115, 0.066197076394253),
    (0.470142064105115, 0.059715871789770, 0.066197076394253),
    (0.101286507323456, 0.101286507323456, 0.062969590272414),
    (0.797426985353087, 0.101286507323456, 0.062969590272414),
    (0.101286507323456, 0.797426985353087, 0.062969590272414),
)

LOBATTO_NORMALIZED_TABLES = (
    (
        3,
        (-1.0, 0.0, 1.0),
        (0.3333333333333333, 1.3333333333333333, 0.3333333333333333),
    ),
    (
        5,
        (-1.0, -0.6546536707079771, 0.0, 0.6546536707079771, 1.0),
        (0.1, 0.5444444444444444, 0.7111111111111111, 0.5444444444444444, 0.1),
    ),
    (
        7,
        (-1.0, -0.830223896278567, -0.468848793470714, 0.0, 0.468848793470714, 0.830223896278567, 1.0),
        (0.047619047619048, 0.276826047361566, 0.431745381209863, 0.487619047619048, 0.431745381209863, 0.276826047361566, 0.047619047619048),
    ),
    (
        9,
        (-1.0, -0.89975799541146, -0.677186279510738, -0.363117463826178, 0.0, 0.363117463826178, 0.677186279510738, 0.89975799541146, 1.0),
        (0.027777777777778, 0.165495361560806, 0.274538712500162, 0.346428510973046, 0.371519274376417, 0.346428510973046, 0.274538712500162, 0.165495361560806, 0.027777777777778),
    ),
    (
        11,
        (-1.0, -0.934001430408059, -0.784483473663144, -0.565235326996205, -0.295758135586939, 0.0, 0.295758135586939, 0.565235326996205, 0.784483473663144, 0.934001430408059, 1.0),
        (0.018181818181818, 0.109612273266995, 0.187169881780305, 0.248048104264028, 0.286879124779008, 0.300217595455691, 0.286879124779008, 0.248048104264028, 0.187169881780305, 0.109612273266995, 0.018181818181818),
    ),
)

STATE_FIELD_MANIFEST = {
    "committed_total_u": {
        "role": "authoritative",
        "component_frame": "global",
        "component_order": EXTERNAL_NODE_COORDINATE_ORDER,
        "point_order": "ordered_connectivity_nodes",
    },
    "committed_director_triads": {
        "role": "authoritative",
        "component_frame": "global_xyz_rows",
        "component_order": ("V1", "V2", "VN"),
        "point_order": "source_nodes_corner_1_2_3_then_bubble_4",
    },
    "bubble_rotation_last_increment": {
        "role": "reserved_zero",
        "component_frame": "current_source_node_4_eq11_tangent_gauge",
        "component_order": ("A4_hierarchical", "B4_hierarchical"),
        "point_order": "single_source_bubble_node",
    },
    "committed_internal_force": {
        "role": "derived_integrity_protected",
        "component_frame": "global",
        "component_order": EXTERNAL_NODE_FORCE_ORDER,
        "point_order": "ordered_connectivity_nodes",
    },
    "station_generalized_strain": {
        "role": "authoritative",
        "component_frame": "numbered_reference_engineering_strain",
        "component_order": GENERALIZED_STRAIN_COMPONENT_ORDER,
        "point_order": "ordered_surface_stations",
    },
    "station_generalized_resultant": {
        "role": "derived_integrity_protected",
        "component_frame": "numbered_reference_tensor_resultant",
        "component_order": GENERALIZED_RESULTANT_COMPONENT_ORDER,
        "point_order": "ordered_surface_stations",
    },
    "plastic_strain": {
        "role": "authoritative_material_history",
        "component_frame": "physical_material_engineering_strain",
        "component_order": LAYER_STRAIN_COMPONENT_ORDER,
        "point_order": "station_major_layer_minor_bottom_to_top",
    },
    "alpha": {
        "role": "authoritative_material_history",
        "component_frame": "scalar",
        "component_order": ("equivalent_plastic_strain",),
        "point_order": "station_major_layer_minor_bottom_to_top",
    },
    "kinematic_layer_strain": {
        "role": "authoritative_redundant_validated",
        "component_frame": "numbered_reference_engineering_strain",
        "component_order": LAYER_STRAIN_COMPONENT_ORDER,
        "point_order": "station_major_layer_minor_bottom_to_top",
    },
    "layer_strain": {
        "role": "derived_integrity_protected",
        "component_frame": "numbered_reference_engineering_strain",
        "component_order": LAYER_STRAIN_COMPONENT_ORDER,
        "point_order": "station_major_layer_minor_bottom_to_top",
    },
    "layer_strain_material": {
        "role": "derived_integrity_protected",
        "component_frame": "physical_material_engineering_strain",
        "component_order": LAYER_STRAIN_COMPONENT_ORDER,
        "point_order": "station_major_layer_minor_bottom_to_top",
    },
    "layer_stress": {
        "role": "derived_integrity_protected",
        "component_frame": "numbered_reference_tensor_stress",
        "component_order": LAYER_STRESS_COMPONENT_ORDER,
        "point_order": "station_major_layer_minor_bottom_to_top",
    },
    "layer_stress_material": {
        "role": "derived_integrity_protected",
        "component_frame": "physical_material_tensor_stress",
        "component_order": LAYER_STRESS_COMPONENT_ORDER,
        "point_order": "station_major_layer_minor_bottom_to_top",
    },
    "initial_membrane_stress": {
        "role": "authoritative_initial_field",
        "component_frame": "numbered_reference_tensor_stress",
        "component_order": LAYER_STRESS_COMPONENT_ORDER,
        "point_order": "ordered_surface_stations",
    },
    "initial_bending_stress": {
        "role": "authoritative_initial_field",
        "component_frame": "numbered_reference_tensor_stress",
        "component_order": LAYER_STRESS_COMPONENT_ORDER,
        "point_order": "ordered_surface_stations",
    },
    "initial_membrane_prestrain": {
        "role": "authoritative_initial_field",
        "component_frame": "numbered_reference_engineering_strain",
        "component_order": LAYER_STRAIN_COMPONENT_ORDER,
        "point_order": "ordered_surface_stations",
    },
    "initial_curvature_prestrain": {
        "role": "authoritative_initial_field",
        "component_frame": "numbered_reference_engineering_curvature",
        "component_order": LAYER_STRAIN_COMPONENT_ORDER,
        "point_order": "ordered_surface_stations",
    },
    "initial_field_provenance": {
        "role": "authoritative_initial_field_metadata",
        "component_frame": "canonical_metadata",
        "component_order": ("sorted_string_keys",),
        "point_order": "not_applicable",
    },
}

_ROOT_MATERIAL_FIELDS = {
    "anymaterial.isotropic.IsotropicMaterial": frozenset(
        {
            "name",
            "elastic_modulus",
            "poisson_ratio",
            "density",
            "yield_stress",
            "hardening_curve",
        }
    ),
    "anymaterial.orthotropic.OrthotropicMaterial": frozenset(
        {
            "name",
            "elastic_modulus_1",
            "elastic_modulus_2",
            "elastic_modulus_3",
            "poisson_ratio_12",
            "poisson_ratio_13",
            "poisson_ratio_23",
            "shear_modulus_12",
            "shear_modulus_13",
            "shear_modulus_23",
            "density",
            "hill_yield",
            "hardening_curve",
        }
    ),
}
_MATERIAL_SYMMETRY_BY_TYPE = {
    "anymaterial.isotropic.IsotropicMaterial": "isotropic",
    "anymaterial.orthotropic.OrthotropicMaterial": "orthotropic",
}
_HARDENING_CURVE_FIELDS = {
    "anymaterial.curves.LinearHardeningCurve": frozenset(
        {"sigma_yield", "hardening_modulus_value"}
    ),
    "anymaterial.curves.PiecewiseLinearCurve": frozenset(
        {"plastic_strain", "flow_stress_values"}
    ),
    "anymaterial.curves.PowerLawHardeningCurve": frozenset({"K", "n", "eps_0"}),
    "anymaterial.curves.DNVC208MaterialCurve": frozenset(
        {"sigma_prop", "sigma_yield", "sigma_yield_2", "eps_p_y1", "eps_p_y2", "K", "n"}
    ),
}
_HILL48_TYPE_ID = "anymaterial.yield_criteria.Hill48Yield"
_HILL48_FIELDS = frozenset({"X", "Y", "Z", "S12", "S13", "S23"})

_HEX_SHA256 = re.compile(r"[0-9A-F]{64}\Z")
_IDENTITY_KEYS = frozenset(
    {
        "formulation_fingerprint",
        "element_id",
        "element_configuration_fingerprint",
        "node_ids",
        "node_order_fingerprint",
        "reference_geometry_fingerprint",
        "reference_frame_fingerprint",
        "material_fingerprint",
        "initial_fields_fingerprint",
        "state_mode",
        "thickness_quadrature_id",
        "thickness",
        "num_layers",
        "material_symmetry",
        "equivalent_stress_measure",
    }
)
_ARRAY_SHAPES_FIXED = {
    "committed_total_u": (18,),
    "committed_director_triads": (4, 3, 3),
    "bubble_rotation_last_increment": (2,),
    "committed_internal_force": (18,),
    "station_generalized_strain": (NUM_INTEGRATION_STATIONS, GENERALIZED_COMPONENTS),
    "station_generalized_resultant": (NUM_INTEGRATION_STATIONS, GENERALIZED_COMPONENTS),
    **{name: (NUM_INTEGRATION_STATIONS, 3) for name in INITIAL_FIELD_NAMES},
}
_LAYER_VECTOR_FIELDS = (
    "plastic_strain",
    "layer_strain",
    "layer_strain_material",
    "kinematic_layer_strain",
    "layer_stress",
    "layer_stress_material",
)
_STATE_KEYS = frozenset(
    {
        "state_schema",
        "state_version",
        "commit_status",
        "state_mode",
        "formulation_id",
        "formulation_schema",
        "external_coordinate_layout_id",
        "nonlinear_state_layout_id",
        "nonlinear_kinematics_id",
        "director_gauge_id",
        "external_rotation_map_id",
        "bubble_convention",
        "bubble_state_role",
        "bubble_predictor_commit_policy_id",
        "quadrature_id",
        "nonlinear_policy_id",
        "recovery_policy_id",
        "canonicalization_id",
        "state_integrity_id",
        "state_array_layout_id",
        "thickness_coordinate_sign_id",
        "stiffness_station_table_sha256",
        "lobatto_table_sha256",
        "state_field_manifest_sha256",
        "formulation_fingerprint",
        "state_integrity_sha256",
        "element_id",
        "element_configuration_fingerprint",
        "node_ids",
        "node_order_fingerprint",
        "reference_geometry_fingerprint",
        "material_fingerprint",
        "initial_fields_fingerprint",
        "reference_frame_fingerprint",
        "thickness_quadrature_id",
        "thickness",
        "num_layers",
        "material_symmetry",
        "equivalent_stress_measure",
        "committed_total_u",
        "committed_director_triads",
        "bubble_rotation_last_increment",
        "committed_internal_force",
        "station_generalized_strain",
        "station_generalized_resultant",
        "plastic_strain",
        "alpha",
        "layer_strain",
        "layer_strain_material",
        "kinematic_layer_strain",
        "layer_stress",
        "layer_stress_material",
        *INITIAL_FIELD_NAMES,
        "initial_field_provenance",
    }
)


class S3CommittedStateError(ValueError):
    """Raised when qualified-S3 committed state is malformed or incompatible."""


def _key_labels(values: set[Any] | frozenset[Any]) -> list[str]:
    return sorted(repr(value) for value in values)


def _canonical_value(value: Any, *, path: str = "$") -> Any:
    if isinstance(value, np.ndarray):
        return _canonical_value(value.tolist(), path=path)
    if isinstance(value, np.generic):
        return _canonical_value(value.item(), path=path)
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise S3CommittedStateError(f"nonfinite canonical value at {path}")
        return 0.0 if value == 0.0 else value
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, member in value.items():
            if not isinstance(key, str):
                raise S3CommittedStateError(f"non-string canonical key at {path}")
            if key in result:
                raise S3CommittedStateError(f"duplicate canonical key {key!r} at {path}")
            result[key] = _canonical_value(member, path=f"{path}.{key}")
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [
            _canonical_value(member, path=f"{path}[{index}]")
            for index, member in enumerate(value)
        ]
    raise S3CommittedStateError(
        f"unsupported canonical value {type(value).__name__} at {path}"
    )


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes with one terminal LF."""

    normalized = _canonical_value(value)
    text = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return (text + "\n").encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return the uppercase SHA-256 of :func:`canonical_json_bytes`."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest().upper()


def _binary64_rows(rows: Sequence[Sequence[float]]) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(float(value).hex() for value in row) for row in rows)


def stiffness_station_table_fingerprint() -> str:
    """Bind exact ordered binary64 ``(r, s, weight)`` surface stations."""

    return canonical_sha256(
        {
            "quadrature_id": QUADRATURE_ID,
            "ordered_r_s_weight_binary64": _binary64_rows(STIFFNESS_STATION_TABLE),
        }
    )


def lobatto_table_fingerprint() -> str:
    """Bind every ordered normalized Lobatto point and weight."""

    return canonical_sha256(
        {
            "quadrature_id": THICKNESS_QUADRATURE_ID,
            "order": STATE_ARRAY_LAYOUT_ID,
            "thickness_sign": THICKNESS_COORDINATE_SIGN_ID,
            "rules": tuple(
                {
                    "num_layers": count,
                    "zeta_binary64": tuple(float(value).hex() for value in points),
                    "weight_binary64": tuple(float(value).hex() for value in weights),
                }
                for count, points, weights in LOBATTO_NORMALIZED_TABLES
            ),
        }
    )


def state_field_manifest_fingerprint() -> str:
    return canonical_sha256(
        {"layout_id": STATE_ARRAY_LAYOUT_ID, "fields": STATE_FIELD_MANIFEST}
    )


def qualified_s3_lobatto_layers(
    num_layers: Any, thickness: Any
) -> tuple[np.ndarray, np.ndarray]:
    """Return the frozen S3 Lobatto rule with strict count and thickness types."""

    layers = _layer_count(num_layers, "num_layers")
    if isinstance(thickness, (bool, np.bool_)) or not isinstance(
        thickness, (int, float, np.integer, np.floating)
    ):
        raise S3CommittedStateError("thickness must be a finite positive scalar")
    made_thickness = float(thickness)
    if not math.isfinite(made_thickness) or made_thickness <= 0.0:
        raise S3CommittedStateError("thickness must be a finite positive scalar")
    for count, normalized_points, normalized_weights in LOBATTO_NORMALIZED_TABLES:
        if count == layers:
            points = 0.5 * made_thickness * np.asarray(
                normalized_points, dtype=np.float64
            )
            weights = 0.5 * made_thickness * np.asarray(
                normalized_weights, dtype=np.float64
            )
            return points, weights
    raise AssertionError("supported S3 Lobatto table is missing")


def _state_integrity_sha256(state: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in state.items() if key != "state_integrity_sha256"}
    return canonical_sha256({"integrity_id": STATE_INTEGRITY_ID, "state": payload})


def seal_committed_s3_state(state: Mapping[str, Any]) -> dict[str, Any]:
    """Return an owned state carrying a digest of every persisted value."""

    if not isinstance(state, Mapping):
        raise S3CommittedStateError("qualified S3 committed state must be a mapping")
    sealed = copy.deepcopy(dict(state))
    sealed.pop("state_integrity_sha256", None)
    if "bubble_rotation_last_increment" in sealed:
        predictor = _finite_state_array(
            sealed["bubble_rotation_last_increment"],
            (2,),
            "bubble_rotation_last_increment",
        )
        if np.any(predictor != 0.0):
            raise S3CommittedStateError(
                "committed bubble predictor must reset to exact zero"
            )
        sealed["bubble_rotation_last_increment"] = predictor
    sealed["state_integrity_sha256"] = _state_integrity_sha256(sealed)
    return sealed


def strict_canonical_json_loads(raw: bytes) -> Any:
    """Decode canonical bytes while rejecting duplicate or alternate JSON.

    This is a codec primitive, not a checkpoint loader.  Callers must still
    pass a decoded state through :func:`validate_committed_s3_state` with the
    current model identity.
    """

    if not isinstance(raw, bytes):
        raise S3CommittedStateError("canonical JSON input must be bytes")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise S3CommittedStateError("canonical JSON must not contain a UTF-8 BOM")

    def reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise S3CommittedStateError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> Any:
        raise S3CommittedStateError(f"nonfinite JSON constant {value}")

    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicate,
            parse_constant=reject_constant,
        )
        canonical = canonical_json_bytes(value)
    except S3CommittedStateError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise S3CommittedStateError("invalid canonical JSON") from exc
    if raw != canonical:
        raise S3CommittedStateError("JSON bytes are not in canonical form")
    return value


def _closed_keys(value: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    non_string = {key for key in value if not isinstance(key, str)}
    if non_string:
        raise S3CommittedStateError(
            f"{label} keys must be strings: " + ", ".join(_key_labels(non_string))
        )
    missing = expected - set(value)
    unknown = set(value) - expected
    if missing or unknown:
        raise S3CommittedStateError(
            f"{label} keys mismatch; missing={_key_labels(missing)}, "
            f"unknown={_key_labels(unknown)}"
        )


def _qualified_dataclass_descriptor(value: Any, *, path: str) -> Any:
    """Return an exact structural descriptor without object stringification."""

    if value is None or isinstance(value, (str, bool, int, float, np.generic)):
        return _canonical_value(value, path=path)
    if isinstance(value, np.ndarray):
        return _canonical_value(value, path=path)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [
            _qualified_dataclass_descriptor(member, path=f"{path}[{index}]")
            for index, member in enumerate(value)
        ]
    if isinstance(value, Mapping):
        canonical = _canonical_value(value, path=path)
        assert isinstance(canonical, dict)
        return canonical
    if not is_dataclass(value) or isinstance(value, type):
        raise S3CommittedStateError(
            f"unsupported state-bearing object {type(value).__module__}."
            f"{type(value).__qualname__} at {path}"
        )
    type_id = f"{type(value).__module__}.{type(value).__qualname__}"
    members = {
        field.name: _qualified_dataclass_descriptor(
            getattr(value, field.name), path=f"{path}.{field.name}"
        )
        for field in dataclass_fields(value)
    }
    return {"type_id": type_id, "fields": members}


def _validate_nested_dataclass_descriptor(
    value: Any,
    allowed: Mapping[str, frozenset[str]],
    *,
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise S3CommittedStateError(f"{label} must be a registered dataclass descriptor")
    _closed_keys(value, frozenset({"type_id", "fields"}), label)
    type_id = value["type_id"]
    fields_value = value["fields"]
    if not isinstance(type_id, str) or type_id not in allowed:
        raise S3CommittedStateError(f"unsupported {label} type_id")
    if not isinstance(fields_value, Mapping):
        raise S3CommittedStateError(f"{label} fields must be a mapping")
    _closed_keys(fields_value, allowed[type_id], f"{label} fields")
    canonical = _canonical_value(dict(value), path=f"$.{label}")
    assert isinstance(canonical, dict)
    return canonical


def _validate_resolved_material_tree(value: Any) -> tuple[dict[str, Any], str, str]:
    root = _validate_nested_dataclass_descriptor(
        value,
        _ROOT_MATERIAL_FIELDS,
        label="resolved_material",
    )
    type_id = root["type_id"]
    fields_value = root["fields"]
    assert isinstance(fields_value, dict)
    hardening = fields_value["hardening_curve"]
    if hardening is not None:
        fields_value["hardening_curve"] = _validate_nested_dataclass_descriptor(
            hardening,
            _HARDENING_CURVE_FIELDS,
            label="hardening_curve",
        )
    symmetry = _MATERIAL_SYMMETRY_BY_TYPE[type_id]
    if symmetry == "orthotropic":
        hill = fields_value["hill_yield"]
        if hill is not None:
            fields_value["hill_yield"] = _validate_nested_dataclass_descriptor(
                hill,
                {_HILL48_TYPE_ID: _HILL48_FIELDS},
                label="hill_yield",
            )
        if hardening is not None and hill is None:
            raise S3CommittedStateError(
                "orthotropic hardening requires a registered Hill48 yield descriptor"
            )
        measure = "hill48" if hill is not None else "von_mises"
    else:
        measure = "von_mises"
    return root, symmetry, measure


def _validated_compliance(value: Any) -> np.ndarray:
    matrix = _finite_array(
        value,
        (6, 6),
        "elastic_compliance_engineering_6x6",
    )
    scale = max(float(np.max(np.abs(matrix))), np.finfo(np.float64).tiny)
    if float(np.max(np.abs(matrix - matrix.T))) > 1.0e-12 * scale:
        raise S3CommittedStateError("elastic compliance must be symmetric")
    eigenvalues = np.linalg.eigvalsh(0.5 * (matrix + matrix.T))
    if not np.all(np.isfinite(eigenvalues)) or float(np.min(eigenvalues)) <= 0.0:
        raise S3CommittedStateError("elastic compliance must be positive definite")
    return matrix


def _compliance_from_registered_fields(resolved: Mapping[str, Any]) -> np.ndarray:
    type_id = resolved["type_id"]
    fields_value = resolved["fields"]
    assert isinstance(type_id, str) and isinstance(fields_value, Mapping)
    if type_id == "anymaterial.isotropic.IsotropicMaterial":
        elastic_modulus = float(fields_value["elastic_modulus"])
        poisson_ratio = float(fields_value["poisson_ratio"])
        shear_modulus = elastic_modulus / (2.0 * (1.0 + poisson_ratio))
        matrix = np.asarray(
            (
                (1.0 / elastic_modulus, -poisson_ratio / elastic_modulus, -poisson_ratio / elastic_modulus, 0.0, 0.0, 0.0),
                (-poisson_ratio / elastic_modulus, 1.0 / elastic_modulus, -poisson_ratio / elastic_modulus, 0.0, 0.0, 0.0),
                (-poisson_ratio / elastic_modulus, -poisson_ratio / elastic_modulus, 1.0 / elastic_modulus, 0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0, 1.0 / shear_modulus, 0.0, 0.0),
                (0.0, 0.0, 0.0, 0.0, 1.0 / shear_modulus, 0.0),
                (0.0, 0.0, 0.0, 0.0, 0.0, 1.0 / shear_modulus),
            ),
            dtype=np.float64,
        )
    elif type_id == "anymaterial.orthotropic.OrthotropicMaterial":
        elastic_1 = float(fields_value["elastic_modulus_1"])
        elastic_2 = float(fields_value["elastic_modulus_2"])
        elastic_3 = float(fields_value["elastic_modulus_3"])
        poisson_12 = float(fields_value["poisson_ratio_12"])
        poisson_13 = float(fields_value["poisson_ratio_13"])
        poisson_23 = float(fields_value["poisson_ratio_23"])
        matrix = np.zeros((6, 6), dtype=np.float64)
        matrix[0, 0] = 1.0 / elastic_1
        matrix[1, 1] = 1.0 / elastic_2
        matrix[2, 2] = 1.0 / elastic_3
        matrix[0, 1] = matrix[1, 0] = -poisson_12 / elastic_1
        matrix[0, 2] = matrix[2, 0] = -poisson_13 / elastic_1
        matrix[1, 2] = matrix[2, 1] = -poisson_23 / elastic_2
        matrix[3, 3] = 1.0 / float(fields_value["shear_modulus_23"])
        matrix[4, 4] = 1.0 / float(fields_value["shear_modulus_13"])
        matrix[5, 5] = 1.0 / float(fields_value["shear_modulus_12"])
    else:
        raise S3CommittedStateError("unsupported resolved material type_id")
    return _validated_compliance(matrix)


def resolved_material_descriptor(material: Any) -> dict[str, Any]:
    """Describe every dataclass field of one supported material exactly."""

    if (
        not is_dataclass(material)
        or isinstance(material, type)
        or not isinstance(material, StructuralMaterial)
    ):
        raise S3CommittedStateError(
            "qualified S3 layered state requires a registered dataclass "
            "StructuralMaterial"
        )
    descriptor = _qualified_dataclass_descriptor(material, path="$.material")
    assert isinstance(descriptor, dict)
    descriptor, registered_symmetry, measure = _validate_resolved_material_tree(
        descriptor
    )
    try:
        actual_symmetry = material_symmetry(material)
        compliance = _validated_compliance(elastic_compliance_matrix(material))
    except (TypeError, ValueError, FloatingPointError, np.linalg.LinAlgError) as exc:
        raise S3CommittedStateError(
            "qualified S3 material does not provide valid structural compliance"
        ) from exc
    if actual_symmetry != registered_symmetry:
        raise S3CommittedStateError(
            "material symmetry does not match its registered descriptor type"
        )
    return {
        "descriptor_schema": MATERIAL_DESCRIPTOR_SCHEMA,
        "material_symmetry": registered_symmetry,
        "equivalent_stress_measure": measure,
        "elastic_compliance_engineering_6x6": compliance.tolist(),
        "resolved_material": descriptor,
    }


def build_element_configuration_descriptor(
    *,
    thickness: float,
    reference_normal: Any,
    material_direction: Any | None,
    material_angle_deg: float,
    shell_section: Any | None,
) -> dict[str, Any]:
    """Build the complete layered-state configuration descriptor.

    A pre-integrated generalized section has a different state mode and is
    intentionally rejected by this V1 layered-state builder.
    """

    if shell_section is not None:
        raise S3CommittedStateError(
            "layered qualified S3 state cannot describe a generalized section"
        )
    if isinstance(thickness, (bool, np.bool_)) or not isinstance(
        thickness, (int, float, np.integer, np.floating)
    ):
        raise S3CommittedStateError("thickness must be a finite positive scalar")
    thickness_value = float(thickness)
    if not math.isfinite(thickness_value) or thickness_value <= 0.0:
        raise S3CommittedStateError("thickness must be a finite positive scalar")
    normal = _finite_array(reference_normal, (3,), "reference_normal")
    normal_norm = float(np.linalg.norm(normal))
    if not math.isfinite(normal_norm) or normal_norm <= np.finfo(float).tiny:
        raise S3CommittedStateError("reference_normal must have positive norm")
    normal /= normal_norm
    if material_direction is None:
        direction: list[float] | None = None
    else:
        made_direction = _finite_array(
            material_direction, (3,), "material_direction"
        )
        tangent = made_direction - float(made_direction @ normal) * normal
        tangent_norm = float(np.linalg.norm(tangent))
        if not math.isfinite(tangent_norm) or tangent_norm <= np.finfo(float).tiny:
            raise S3CommittedStateError(
                "material_direction must define a surface tangent"
            )
        direction = (tangent / tangent_norm).tolist()
    if isinstance(material_angle_deg, (bool, np.bool_)) or not isinstance(
        material_angle_deg, (int, float, np.integer, np.floating)
    ):
        raise S3CommittedStateError("material_angle_deg must be finite")
    angle = float(material_angle_deg)
    if not math.isfinite(angle):
        raise S3CommittedStateError("material_angle_deg must be finite")
    if direction is None and angle != 0.0:
        raise S3CommittedStateError(
            "material_angle_deg requires a physical material_direction"
        )
    return {
        "descriptor_schema": ELEMENT_CONFIGURATION_DESCRIPTOR_SCHEMA,
        "thickness": thickness_value,
        "reference_normal": normal.tolist(),
        "material_direction": direction,
        "material_angle_deg": angle,
        "section_mode": "homogeneous_layered_material",
    }


def _validate_element_descriptor(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise S3CommittedStateError("element_descriptor must be a mapping")
    expected = frozenset(
        {
            "descriptor_schema",
            "thickness",
            "reference_normal",
            "material_direction",
            "material_angle_deg",
            "section_mode",
        }
    )
    _closed_keys(value, expected, "element_descriptor")
    rebuilt = build_element_configuration_descriptor(
        thickness=value["thickness"],
        reference_normal=value["reference_normal"],
        material_direction=value["material_direction"],
        material_angle_deg=value["material_angle_deg"],
        shell_section=None,
    )
    if value["descriptor_schema"] != ELEMENT_CONFIGURATION_DESCRIPTOR_SCHEMA:
        raise S3CommittedStateError("incompatible element descriptor schema")
    if value["section_mode"] != "homogeneous_layered_material":
        raise S3CommittedStateError("incompatible element section mode")
    if _canonical_value(dict(value)) != rebuilt:
        raise S3CommittedStateError("element descriptor is not normalized")
    return rebuilt


def _validate_material_descriptor(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise S3CommittedStateError("material_descriptor must be a mapping")
    expected = frozenset(
        {
            "descriptor_schema",
            "material_symmetry",
            "equivalent_stress_measure",
            "elastic_compliance_engineering_6x6",
            "resolved_material",
        }
    )
    _closed_keys(value, expected, "material_descriptor")
    if value["descriptor_schema"] != MATERIAL_DESCRIPTOR_SCHEMA:
        raise S3CommittedStateError("incompatible material descriptor schema")
    resolved, symmetry, measure = _validate_resolved_material_tree(
        value["resolved_material"]
    )
    compliance = _validated_compliance(value["elastic_compliance_engineering_6x6"])
    try:
        expected_compliance = _compliance_from_registered_fields(resolved)
    except S3CommittedStateError:
        raise
    except (TypeError, ValueError, OverflowError, ZeroDivisionError) as exc:
        raise S3CommittedStateError(
            "registered material fields cannot define structural compliance"
        ) from exc
    if not np.array_equal(compliance, expected_compliance):
        raise S3CommittedStateError(
            "elastic compliance does not match the registered material fields"
        )
    if value["material_symmetry"] != symmetry:
        raise S3CommittedStateError(
            "material_symmetry does not match the registered material descriptor"
        )
    if value["equivalent_stress_measure"] != measure:
        raise S3CommittedStateError(
            "equivalent_stress_measure does not match the registered material descriptor"
        )
    _constitutive_identity(symmetry, measure)
    canonical = _canonical_value(dict(value), path="$.material_descriptor")
    assert isinstance(canonical, dict)
    canonical["resolved_material"] = resolved
    return canonical


def formulation_mechanics_contract_payload() -> dict[str, Any]:
    """Return the exact formulation mechanics authority used by production."""

    return {
        "linear_source": {
            "url": MITC3_PLUS_SOURCE_URL,
            "byte_count": MITC3_PLUS_SOURCE_BYTES,
            "sha256": MITC3_PLUS_SOURCE_SHA256,
            "equation_map": MITC3_PLUS_EQUATION_MAP,
        },
        "nonlinear_source": {
            "url": MITC3_PLUS_NONLINEAR_SOURCE_URL,
            "byte_count": MITC3_PLUS_NONLINEAR_SOURCE_BYTES,
            "sha256": MITC3_PLUS_NONLINEAR_SOURCE_SHA256,
            "equation_map": MITC3_PLUS_NONLINEAR_EQUATION_MAP,
        },
        "bubble": {
            "polynomial": "27*L1*L2*L3",
            "polynomial_scale": BUBBLE_POLYNOMIAL_SCALE,
            "offset_d_exact": BUBBLE_OFFSET_EXACT,
            "offset_d_binary64": BUBBLE_OFFSET_D,
            "tying_point_definitions": TYING_POINT_DEFINITIONS,
            "tying_point_binary64": TYING_POINTS,
        },
        "pl_completion": {
            "basis_id": PL_BASIS_ID,
            "constraint_id": PL_CONSTRAINT_ID,
            "gram_scale_id": PL_GRAM_SCALE_ID,
            "gram_numerator": PL_GRAM_NUMERATOR,
            "block_sign_id": PL_BLOCK_SIGN_ID,
            "condensation_id": PL_CONDENSATION_ID,
        },
        "drilling_scale": {
            "policy_id": DRILL_SCALE_POLICY_ID,
            "projector": DRILL_SCALE_PROJECTOR,
            "metric": DRILL_SCALE_METRIC,
            "inverse_metric_sqrt": DRILL_SCALE_INVERSE_METRIC_SQRT,
            "factor": 0.5,
            "material_state": "elastic_membrane_section_matrix_A",
            "required": "finite_strictly_positive",
        },
    }


def formulation_mechanics_fingerprint() -> str:
    """Return the canonical hash of exact state-relevant mechanics authority."""

    return canonical_sha256(formulation_mechanics_contract_payload())


def formulation_fingerprint_payload() -> dict[str, Any]:
    """Return the frozen state-relevant qualified-S3 formulation identity."""

    return {
        "formulation_id": FORMULATION_ID,
        "formulation_schema": FORMULATION_SCHEMA,
        "external_coordinate_layout_id": EXTERNAL_COORDINATE_LAYOUT_ID,
        "nonlinear_state_schema": NONLINEAR_STATE_SCHEMA,
        "nonlinear_state_version": NONLINEAR_STATE_VERSION,
        "nonlinear_state_layout_id": NONLINEAR_STATE_LAYOUT_ID,
        "nonlinear_kinematics_id": NONLINEAR_KINEMATICS_ID,
        "director_gauge_id": DIRECTOR_GAUGE_ID,
        "director_gauge_primary_axis": DIRECTOR_GAUGE_PRIMARY_AXIS,
        "director_gauge_fallback_axis": DIRECTOR_GAUGE_FALLBACK_AXIS,
        "director_gauge_switch_tolerance": DIRECTOR_GAUGE_SWITCH_TOLERANCE,
        "external_rotation_map_id": EXTERNAL_ROTATION_MAP_ID,
        "bubble_state_role": BUBBLE_STATE_ROLE,
        "bubble_predictor_commit_policy_id": BUBBLE_PREDICTOR_COMMIT_POLICY_ID,
        "bubble_convention": BUBBLE_CONVENTION,
        "quadrature_id": QUADRATURE_ID,
        "nonlinear_policy_id": NONLINEAR_POLICY_ID,
        "recovery_policy_id": RECOVERY_POLICY_ID,
        "nonlinear_source_sha256": NONLINEAR_SOURCE_SHA256,
        "formulation_mechanics": formulation_mechanics_contract_payload(),
        "formulation_mechanics_sha256": formulation_mechanics_fingerprint(),
        "bubble_equilibrium_policy": {
            "max_iterations": BUBBLE_MAX_ITERATIONS,
            "relative_tolerance": BUBBLE_RELATIVE_TOLERANCE,
            "step_tolerance": BUBBLE_STEP_TOLERANCE,
            "condition_limit": BUBBLE_CONDITION_LIMIT,
            "line_search_min_factor": BUBBLE_LINE_SEARCH_MIN_FACTOR,
            "line_search_reduction": BUBBLE_LINE_SEARCH_REDUCTION,
            "force_condensation_id": BUBBLE_FORCE_CONDENSATION_ID,
        },
        "constitutive_integration_ids": {
            "isotropic": ISOTROPIC_CONSTITUTIVE_INTEGRATION_ID,
            "orthotropic": ORTHOTROPIC_CONSTITUTIVE_INTEGRATION_ID,
            "generalized_section": GENERALIZED_SECTION_INTEGRATION_ID,
        },
        "canonicalization_id": CANONICALIZATION_ID,
        "state_integrity_id": STATE_INTEGRITY_ID,
        "state_redundancy_tolerance_factor": STATE_REDUNDANCY_TOLERANCE_FACTOR,
        "state_redundancy_validation_id": STATE_REDUNDANCY_VALIDATION_ID,
        "reference_geometry_validation_id": REFERENCE_GEOMETRY_VALIDATION_ID,
        "state_mode": STATE_MODE,
        "element_configuration_descriptor_schema": (
            ELEMENT_CONFIGURATION_DESCRIPTOR_SCHEMA
        ),
        "material_descriptor_schema": MATERIAL_DESCRIPTOR_SCHEMA,
        "material_descriptor_validation_id": MATERIAL_DESCRIPTOR_VALIDATION_ID,
        "thickness_quadrature_id": THICKNESS_QUADRATURE_ID,
        "supported_lobatto_layer_counts": SUPPORTED_LOBATTO_LAYER_COUNTS,
        "stiffness_station_table_sha256": stiffness_station_table_fingerprint(),
        "lobatto_table_sha256": lobatto_table_fingerprint(),
        "state_array_layout_id": STATE_ARRAY_LAYOUT_ID,
        "thickness_coordinate_sign_id": THICKNESS_COORDINATE_SIGN_ID,
        "state_field_manifest_sha256": state_field_manifest_fingerprint(),
        "director_orthonormality_tolerance": DIRECTOR_ORTHONORMALITY_TOLERANCE,
        "geometry_admission": {
            "minimum_owner_normal_alignment": MINIMUM_OWNER_NORMAL_ALIGNMENT,
            "minimum_normalized_twice_area": MINIMUM_NORMALIZED_TWICE_AREA,
            "minimum_angle_deg": MINIMUM_ANGLE_DEG,
            "maximum_angle_deg": MAXIMUM_ANGLE_DEG,
            "maximum_edge_ratio": MAXIMUM_EDGE_RATIO,
            "minimum_corner_scaled_jacobian": MINIMUM_CORNER_SCALED_JACOBIAN,
            "minimum_normalized_area": MINIMUM_NORMALIZED_AREA,
            "comparison_tolerance": QUALITY_COMPARISON_TOLERANCE,
            "reference_frame_match_tolerance": REFERENCE_FRAME_MATCH_TOLERANCE,
        },
        "generalized_strain_component_order": GENERALIZED_STRAIN_COMPONENT_ORDER,
        "generalized_resultant_component_order": (
            GENERALIZED_RESULTANT_COMPONENT_ORDER
        ),
        "layer_strain_component_order": LAYER_STRAIN_COMPONENT_ORDER,
        "layer_stress_component_order": LAYER_STRESS_COMPONENT_ORDER,
        "registered_material_descriptor_fields": {
            "root": {
                key: tuple(sorted(value))
                for key, value in sorted(_ROOT_MATERIAL_FIELDS.items())
            },
            "hardening": {
                key: tuple(sorted(value))
                for key, value in sorted(_HARDENING_CURVE_FIELDS.items())
            },
            "hill48": tuple(sorted(_HILL48_FIELDS)),
        },
        "initial_field_names": INITIAL_FIELD_NAMES,
        "fixed_array_shapes": {
            key: shape for key, shape in sorted(_ARRAY_SHAPES_FIXED.items())
        },
        "layer_vector_fields": _LAYER_VECTOR_FIELDS,
        "state_keys": tuple(sorted(_STATE_KEYS)),
        "identity_keys": tuple(sorted(_IDENTITY_KEYS)),
    }


def formulation_fingerprint() -> str:
    """Return the canonical fingerprint of the frozen state formulation."""

    return canonical_sha256(formulation_fingerprint_payload())


def _node_ids(value: Sequence[int]) -> tuple[int, int, int]:
    if isinstance(value, (str, bytes, bytearray)):
        raise S3CommittedStateError("qualified S3 state requires exactly three node IDs")
    try:
        size = len(value)
    except TypeError as exc:
        raise S3CommittedStateError(
            "qualified S3 state requires exactly three node IDs"
        ) from exc
    if size != 3:
        raise S3CommittedStateError("qualified S3 state requires exactly three node IDs")
    result: list[int] = []
    for raw in value:
        if isinstance(raw, (bool, np.bool_)) or not isinstance(raw, (int, np.integer)):
            raise S3CommittedStateError("qualified S3 node IDs must be integers")
        result.append(int(raw))
    if len(set(result)) != 3:
        raise S3CommittedStateError("qualified S3 state requires three distinct node IDs")
    return tuple(result)  # type: ignore[return-value]


def _layer_count(value: Any, label: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, np.integer)
    ):
        raise S3CommittedStateError(
            f"{label} must be one of {list(SUPPORTED_LOBATTO_LAYER_COUNTS)}"
        )
    made = int(value)
    if made not in SUPPORTED_LOBATTO_LAYER_COUNTS:
        raise S3CommittedStateError(
            f"{label} must be one of {list(SUPPORTED_LOBATTO_LAYER_COUNTS)}"
        )
    return made


def _constitutive_identity(
    material_symmetry: Any,
    equivalent_stress_measure: Any,
) -> tuple[str, str]:
    if not isinstance(material_symmetry, str) or material_symmetry not in {
        "isotropic",
        "orthotropic",
    }:
        raise S3CommittedStateError(
            "material_symmetry must be 'isotropic' or 'orthotropic'"
        )
    if not isinstance(equivalent_stress_measure, str) or (
        equivalent_stress_measure not in {"von_mises", "hill48"}
    ):
        raise S3CommittedStateError("unsupported equivalent_stress_measure")
    if material_symmetry == "isotropic" and equivalent_stress_measure != "von_mises":
        raise S3CommittedStateError("isotropic state requires von_mises")
    return material_symmetry, equivalent_stress_measure


def _validate_numeric_values(value: Any, label: str) -> None:
    if isinstance(value, np.ndarray):
        if value.dtype.kind not in {"i", "u", "f"}:
            raise S3CommittedStateError(
                f"{label} must contain real numeric values, not {value.dtype}"
            )
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for member in value:
            _validate_numeric_values(member, label)
        return
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise S3CommittedStateError(f"{label} must contain real numeric values")


def _finite_array(value: Any, shape: tuple[int, ...], label: str) -> np.ndarray:
    _validate_numeric_values(value, label)
    try:
        result = np.asarray(value, dtype=np.float64)
    except (OverflowError, TypeError, ValueError) as exc:
        raise S3CommittedStateError(f"{label} must contain numeric values") from exc
    if result.shape != shape:
        raise S3CommittedStateError(
            f"{label} has shape {result.shape}; expected {shape}"
        )
    if not np.all(np.isfinite(result)):
        raise S3CommittedStateError(f"{label} contains nonfinite values")
    result = np.array(result, dtype=np.float64, order="C", copy=True)
    result[result == 0.0] = 0.0
    return result


def _validate_state_float_values(value: Any, label: str) -> None:
    """Require canonical binary64 spellings for persisted state arrays."""

    if isinstance(value, np.ndarray):
        if value.dtype != np.dtype(np.float64):
            raise S3CommittedStateError(
                f"{label} must contain canonical binary64 floating values"
            )
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for member in value:
            _validate_state_float_values(member, label)
        return
    if type(value) is not float:
        raise S3CommittedStateError(
            f"{label} must contain canonical binary64 floating values"
        )


def _finite_state_array(
    value: Any, shape: tuple[int, ...], label: str
) -> np.ndarray:
    _validate_state_float_values(value, label)
    return _finite_array(value, shape, label)


def qualified_s3_triangle_frame(
    coordinates: Any,
    owner_normal: Any | None,
    *,
    enforce_admission: bool = True,
    enforce_positive_winding: bool = True,
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    """Derive the unique numbered reference frame and qualified quality data."""

    nodes = _finite_array(coordinates, (3, 3), "reference_coordinates")
    edge_r = nodes[1] - nodes[0]
    edge_s = nodes[2] - nodes[0]
    normal_raw = np.cross(edge_r, edge_s)
    twice_area = float(np.linalg.norm(normal_raw))
    lengths = np.asarray(
        (
            np.linalg.norm(nodes[1] - nodes[0]),
            np.linalg.norm(nodes[2] - nodes[1]),
            np.linalg.norm(nodes[0] - nodes[2]),
        ),
        dtype=np.float64,
    )
    maximum_edge = float(np.max(lengths))
    minimum_edge = float(np.min(lengths))
    if (
        not math.isfinite(maximum_edge)
        or maximum_edge <= 0.0
        or minimum_edge <= 0.0
    ):
        raise S3CommittedStateError("qualified S3 requires three distinct nodes")
    normalized_twice_area = twice_area / (maximum_edge * maximum_edge)
    if (
        not math.isfinite(normalized_twice_area)
        or normalized_twice_area <= MINIMUM_NORMALIZED_TWICE_AREA
    ):
        raise S3CommittedStateError(
            "qualified S3 has a zero or near-zero signed area"
        )

    first = edge_r / float(np.linalg.norm(edge_r))
    normal = normal_raw / twice_area
    connectivity_sign = 1.0
    owner_alignment = 1.0
    if owner_normal is not None:
        supplied = _finite_array(owner_normal, (3,), "reference_normal")
        supplied_norm = float(np.linalg.norm(supplied))
        if supplied_norm <= np.finfo(np.float64).tiny:
            raise S3CommittedStateError(
                "qualified S3 reference_normal must have positive norm"
            )
        supplied /= supplied_norm
        signed_alignment = float(normal @ supplied)
        if abs(signed_alignment) <= MINIMUM_OWNER_NORMAL_ALIGNMENT:
            raise S3CommittedStateError(
                "qualified S3 reference_normal is tangential to the facet"
            )
        if signed_alignment < 0.0:
            normal = -normal
            connectivity_sign = -1.0
        owner_alignment = abs(signed_alignment)
    second = np.cross(normal, first)
    second /= float(np.linalg.norm(second))
    first = np.cross(second, normal)
    first /= float(np.linalg.norm(first))
    frame = np.column_stack((first, second, normal))
    local = (nodes - nodes[0]) @ frame[:, :2]

    cosines = np.empty(3, dtype=np.float64)
    for index in range(3):
        left = nodes[(index + 1) % 3] - nodes[index]
        right = nodes[(index - 1) % 3] - nodes[index]
        denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
        cosines[index] = float(np.clip(float(left @ right) / denominator, -1.0, 1.0))
    angles = np.degrees(np.arccos(cosines))
    corner_scaled_jacobian = float(np.min(np.sin(np.radians(angles))))
    normalized_area = float(
        2.0 * math.sqrt(3.0) * twice_area / float(lengths @ lengths)
    )
    quality = {
        "area": 0.5 * twice_area,
        "normalized_twice_area": normalized_twice_area,
        "minimum_angle_deg": float(np.min(angles)),
        "maximum_angle_deg": float(np.max(angles)),
        "edge_ratio": maximum_edge / minimum_edge,
        "minimum_scaled_jacobian": corner_scaled_jacobian,
        "normalized_area": normalized_area,
        "connectivity_sign": connectivity_sign,
        "reference_normal_alignment": owner_alignment,
    }
    if enforce_admission:
        require_qualified_s3_quality(
            quality,
            enforce_positive_winding=enforce_positive_winding,
        )
    return frame, local, quality


def require_qualified_s3_quality(
    quality: Mapping[str, Any],
    *,
    enforce_positive_winding: bool = True,
) -> None:
    """Fail closed unless a triangle satisfies the frozen admission envelope."""

    required = frozenset(
        {
            "area",
            "normalized_twice_area",
            "minimum_angle_deg",
            "maximum_angle_deg",
            "edge_ratio",
            "minimum_scaled_jacobian",
            "normalized_area",
            "connectivity_sign",
            "reference_normal_alignment",
        }
    )
    if not isinstance(quality, Mapping):
        raise S3CommittedStateError("qualified S3 quality data is incomplete")
    _closed_keys(quality, required, "qualified S3 quality data")
    values: dict[str, float] = {}
    for key in required:
        raw = quality[key]
        if isinstance(raw, (bool, np.bool_)) or not isinstance(
            raw, (int, float, np.integer, np.floating)
        ):
            raise S3CommittedStateError(
                f"qualified S3 quality metric {key!r} must be a real scalar"
            )
        made = float(raw)
        if not math.isfinite(made):
            raise S3CommittedStateError(
                f"qualified S3 quality metric {key!r} must be finite"
            )
        values[key] = made
    failures: list[str] = []
    tolerance = QUALITY_COMPARISON_TOLERANCE
    if values["area"] <= 0.0:
        failures.append("area must be strictly positive")
    if values["normalized_twice_area"] <= MINIMUM_NORMALIZED_TWICE_AREA:
        failures.append("normalized signed area is below the admitted threshold")
    if values["reference_normal_alignment"] <= MINIMUM_OWNER_NORMAL_ALIGNMENT:
        failures.append("owner-normal alignment is below the admitted threshold")
    if values["reference_normal_alignment"] > 1.0 + tolerance:
        failures.append("owner-normal alignment exceeds one")
    if values["connectivity_sign"] not in (-1.0, 1.0):
        failures.append("connectivity sign must be exactly minus or plus one")
    if enforce_positive_winding and values["connectivity_sign"] <= 0.0:
        failures.append("connectivity winding opposes the authoritative owner normal")
    if values["minimum_angle_deg"] < MINIMUM_ANGLE_DEG - tolerance:
        failures.append("minimum angle is below 30 degrees")
    if values["maximum_angle_deg"] > MAXIMUM_ANGLE_DEG + tolerance:
        failures.append("maximum angle exceeds 150 degrees")
    if values["edge_ratio"] > MAXIMUM_EDGE_RATIO + tolerance:
        failures.append("edge ratio exceeds 4.0")
    if (
        values["minimum_scaled_jacobian"]
        < MINIMUM_CORNER_SCALED_JACOBIAN - tolerance
    ):
        failures.append("minimum scaled Jacobian is below 0.20")
    if values["normalized_area"] < MINIMUM_NORMALIZED_AREA - tolerance:
        failures.append("normalized area is below 0.60")
    if failures:
        raise S3CommittedStateError(
            "qualified S3 quality admission failed: " + "; ".join(failures)
        )


def reconstruct_director_triad(normal: Any) -> np.ndarray:
    """Return the frozen MITC3+ Eq. (11) tangent gauge for ``normal``.

    The published construction uses global ``e_y``.  Bathe's stated parallel
    special case uses global ``e_z``; the frozen switch only covers the
    numerically singular neighbourhood of exact parallelism.  The returned
    columns are ``(V1, V2, Vn)`` with ``V1 = axis x Vn`` and
    ``V2 = Vn x V1``.
    """

    made = _finite_array(normal, (3,), "director_normal")
    norm = float(np.linalg.norm(made))
    if not math.isfinite(norm) or norm <= np.finfo(np.float64).tiny:
        raise S3CommittedStateError("director_normal must have positive norm")
    unit = made / norm
    primary = np.asarray(DIRECTOR_GAUGE_PRIMARY_AXIS, dtype=np.float64)
    first = np.cross(primary, unit)
    first_norm = float(np.linalg.norm(first))
    if first_norm <= DIRECTOR_GAUGE_SWITCH_TOLERANCE:
        fallback = np.asarray(DIRECTOR_GAUGE_FALLBACK_AXIS, dtype=np.float64)
        first = np.cross(fallback, unit)
        first_norm = float(np.linalg.norm(first))
    if not math.isfinite(first_norm) or first_norm <= np.finfo(np.float64).tiny:
        raise S3CommittedStateError("director Eq. (11) gauge is singular")
    first /= first_norm
    second = np.cross(unit, first)
    second /= float(np.linalg.norm(second))
    result = np.column_stack((first, second, unit))
    result[result == 0.0] = 0.0
    return result


def _validate_right_handed_triad(triad: np.ndarray, label: str) -> None:
    identity = np.eye(3, dtype=np.float64)
    gram_error = float(np.max(np.abs(triad.T @ triad - identity)))
    determinant = float(np.linalg.det(triad))
    if (
        not math.isfinite(gram_error)
        or gram_error > DIRECTOR_ORTHONORMALITY_TOLERANCE
        or not math.isfinite(determinant)
        or determinant <= 0.0
        or abs(determinant - 1.0) > DIRECTOR_ORTHONORMALITY_TOLERANCE
    ):
        raise S3CommittedStateError(
            f"{label} is not a right-handed orthonormal triad"
        )


def _validate_triads(triads: np.ndarray) -> None:
    for index, triad in enumerate(triads):
        _validate_right_handed_triad(
            triad, f"committed_director_triads[{index}]"
        )
        expected = reconstruct_director_triad(triad[:, 2])
        gauge_error = float(np.max(np.abs(triad - expected)))
        if (
            not math.isfinite(gauge_error)
            or gauge_error > DIRECTOR_ORTHONORMALITY_TOLERANCE
        ):
            raise S3CommittedStateError(
                f"committed_director_triads[{index}] does not satisfy the "
                "frozen MITC3+ Eq. (11) gauge"
            )


def _fingerprint(value: Any, label: str) -> str:
    if not isinstance(value, str) or _HEX_SHA256.fullmatch(value) is None:
        raise S3CommittedStateError(f"{label} must be an uppercase SHA-256")
    return value


def node_order_fingerprint(node_ids: Sequence[int]) -> str:
    nodes = _node_ids(node_ids)
    return canonical_sha256(
        {"layout": "ORDERED_S3_CONNECTIVITY_V1", "node_ids": nodes}
    )


def reference_geometry_fingerprint(
    node_ids: Sequence[int], reference_coordinates: Any
) -> str:
    nodes = _node_ids(node_ids)
    coordinates = _finite_array(
        reference_coordinates, (3, 3), "reference_coordinates"
    )
    return canonical_sha256(
        {
            "layout": "ORDERED_S3_REFERENCE_XYZ_GLOBAL_V1",
            "node_ids": nodes,
            "coordinates": coordinates,
        }
    )


def reference_frame_fingerprint(reference_frame: Any) -> str:
    frame = _finite_array(reference_frame, (3, 3), "reference_frame")
    _validate_right_handed_triad(frame, "reference_frame")
    return canonical_sha256(
        {
            "layout": "QUALIFIED_S3_REFERENCE_FRAME_GLOBAL_COLUMNS_V1",
            "frame": frame,
        }
    )


def material_fingerprint(material_descriptor: Mapping[str, Any]) -> str:
    descriptor = _validate_material_descriptor(material_descriptor)
    return canonical_sha256(
        {
            "layout": "QUALIFIED_S3_MATERIAL_OR_SECTION_DESCRIPTOR_V1",
            "descriptor": descriptor,
        }
    )


def element_configuration_fingerprint(
    element_id: int,
    node_ids: Sequence[int],
    element_descriptor: Mapping[str, Any],
) -> str:
    """Bind every state-relevant element option supplied by the caller."""

    if isinstance(element_id, (bool, np.bool_)) or not isinstance(
        element_id, (int, np.integer)
    ):
        raise S3CommittedStateError("element_id must be an integer")
    descriptor = _validate_element_descriptor(element_descriptor)
    return canonical_sha256(
        {
            "layout": "QUALIFIED_S3_ELEMENT_CONFIGURATION_V1",
            "element_id": int(element_id),
            "node_ids": _node_ids(node_ids),
            "descriptor": descriptor,
        }
    )


def build_state_identity(
    *,
    element_id: int,
    node_ids: Sequence[int],
    reference_coordinates: Any,
    reference_frame: Any,
    element_descriptor: Mapping[str, Any],
    material_descriptor: Mapping[str, Any],
    num_layers: int,
    material_symmetry: str,
    equivalent_stress_measure: str,
    initial_fields: Mapping[str, Any] | None = None,
    initial_field_provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the exact model-bound identity consumed by state validation."""

    nodes = _node_ids(node_ids)
    if isinstance(element_id, (bool, np.bool_)) or not isinstance(
        element_id, (int, np.integer)
    ):
        raise S3CommittedStateError("element_id must be an integer")
    layers = _layer_count(num_layers, "num_layers")
    symmetry, measure = _constitutive_identity(
        material_symmetry, equivalent_stress_measure
    )
    frame = _finite_array(reference_frame, (3, 3), "reference_frame")
    _validate_right_handed_triad(frame, "reference_frame")
    descriptor = _validate_element_descriptor(element_descriptor)
    material_description = _validate_material_descriptor(material_descriptor)
    if material_description["material_symmetry"] != symmetry:
        raise S3CommittedStateError(
            "material_symmetry does not match the resolved material descriptor"
        )
    if material_description["equivalent_stress_measure"] != measure:
        raise S3CommittedStateError(
            "equivalent_stress_measure does not match the resolved material descriptor"
        )
    coordinates = _finite_array(
        reference_coordinates,
        (3, 3),
        "reference_coordinates",
    )
    descriptor_normal = np.asarray(descriptor["reference_normal"], dtype=np.float64)
    derived_frame, _local, _quality = qualified_s3_triangle_frame(
        coordinates,
        descriptor_normal,
        enforce_admission=True,
        enforce_positive_winding=True,
    )
    frame_error = float(np.max(np.abs(frame - derived_frame)))
    if frame_error > REFERENCE_FRAME_MATCH_TOLERANCE:
        raise S3CommittedStateError(
            "reference_frame does not match the admitted numbered geometry"
        )
    fields = _normalized_initial_fields(initial_fields)
    provenance_value = {} if initial_field_provenance is None else initial_field_provenance
    if not isinstance(provenance_value, Mapping):
        raise S3CommittedStateError("initial_field_provenance must be a mapping")
    provenance = _canonical_value(provenance_value, path="$.initial_field_provenance")
    assert isinstance(provenance, dict)
    return {
        "formulation_fingerprint": formulation_fingerprint(),
        "element_id": int(element_id),
        "element_configuration_fingerprint": element_configuration_fingerprint(
            int(element_id), nodes, element_descriptor
        ),
        "node_ids": nodes,
        "node_order_fingerprint": node_order_fingerprint(nodes),
        "reference_geometry_fingerprint": reference_geometry_fingerprint(
            nodes, coordinates
        ),
        "reference_frame_fingerprint": reference_frame_fingerprint(frame),
        "material_fingerprint": material_fingerprint(material_descriptor),
        "initial_fields_fingerprint": _initial_fields_fingerprint(fields, provenance),
        "state_mode": STATE_MODE,
        "thickness_quadrature_id": THICKNESS_QUADRATURE_ID,
        "thickness": descriptor["thickness"],
        "num_layers": layers,
        "material_symmetry": symmetry,
        "equivalent_stress_measure": measure,
    }


def _normalized_initial_fields(
    initial_fields: Mapping[str, Any] | None,
) -> dict[str, np.ndarray]:
    supplied = {} if initial_fields is None else dict(initial_fields)
    non_string = {key for key in supplied if not isinstance(key, str)}
    if non_string:
        raise S3CommittedStateError(
            "qualified S3 initial-field keys must be strings: "
            + ", ".join(_key_labels(non_string))
        )
    unknown = sorted(set(supplied) - set(INITIAL_FIELD_NAMES))
    if unknown:
        raise S3CommittedStateError(
            "unknown qualified S3 initial fields: " + ", ".join(unknown)
        )
    normalized: dict[str, np.ndarray] = {}
    for name in INITIAL_FIELD_NAMES:
        value = supplied.get(name, np.zeros((NUM_INTEGRATION_STATIONS, 3)))
        _validate_numeric_values(value, name)
        try:
            array = np.asarray(value, dtype=np.float64)
        except (OverflowError, TypeError, ValueError) as exc:
            raise S3CommittedStateError(f"{name} must contain numeric values") from exc
        if array.shape == (3,):
            array = np.broadcast_to(array, (NUM_INTEGRATION_STATIONS, 3))
        elif array.shape == (1, 3):
            array = np.broadcast_to(array, (NUM_INTEGRATION_STATIONS, 3))
        normalized[name] = _finite_array(
            array, (NUM_INTEGRATION_STATIONS, 3), name
        )
    return normalized


def _initial_fields_fingerprint(
    fields: Mapping[str, np.ndarray], provenance: Mapping[str, Any]
) -> str:
    return canonical_sha256(
        {
            "layout": "S3_INITIAL_FIELDS_STATION7_V1",
            "fields": {name: fields[name] for name in INITIAL_FIELD_NAMES},
            "provenance": provenance,
        }
    )


def initialize_zero_committed_s3_state(
    *,
    element_id: int,
    node_ids: Sequence[int],
    reference_coordinates: Any,
    reference_frame: Any,
    element_descriptor: Mapping[str, Any],
    material_descriptor: Mapping[str, Any],
    num_layers: int,
    material_symmetry: str = "isotropic",
    equivalent_stress_measure: str | None = None,
    initial_fields: Mapping[str, Any] | None = None,
    initial_field_provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return owned, validated zero-history committed state.

    ``reference_frame`` contains global ``(V1, V2, Vn)`` as columns and is
    repeated for the three corner directors and the internal bubble director.
    """

    layers = _layer_count(num_layers, "num_layers")
    measure = equivalent_stress_measure
    if measure is None:
        measure = "von_mises"
    symmetry, measure = _constitutive_identity(material_symmetry, measure)

    frame = _finite_array(reference_frame, (3, 3), "reference_frame")
    _validate_right_handed_triad(frame, "reference_frame")
    reference_triad = reconstruct_director_triad(frame[:, 2])
    triads = np.repeat(reference_triad[np.newaxis, :, :], 4, axis=0)
    _validate_triads(triads)
    fields = _normalized_initial_fields(initial_fields)
    provenance_value = {} if initial_field_provenance is None else initial_field_provenance
    if not isinstance(provenance_value, Mapping):
        raise S3CommittedStateError("initial_field_provenance must be a mapping")
    provenance = _canonical_value(provenance_value, path="$.initial_field_provenance")
    assert isinstance(provenance, dict)
    identity = build_state_identity(
        element_id=element_id,
        node_ids=node_ids,
        reference_coordinates=reference_coordinates,
        reference_frame=frame,
        element_descriptor=element_descriptor,
        material_descriptor=material_descriptor,
        num_layers=layers,
        material_symmetry=symmetry,
        equivalent_stress_measure=measure,
        initial_fields=fields,
        initial_field_provenance=provenance,
    )

    points = NUM_INTEGRATION_STATIONS * layers
    zero_vectors = lambda: np.zeros((points, 3), dtype=np.float64)
    state: dict[str, Any] = {
        "state_schema": NONLINEAR_STATE_SCHEMA,
        "state_version": NONLINEAR_STATE_VERSION,
        "commit_status": COMMIT_STATUS,
        "state_mode": STATE_MODE,
        "formulation_id": FORMULATION_ID,
        "formulation_schema": FORMULATION_SCHEMA,
        "external_coordinate_layout_id": EXTERNAL_COORDINATE_LAYOUT_ID,
        "nonlinear_state_layout_id": NONLINEAR_STATE_LAYOUT_ID,
        "nonlinear_kinematics_id": NONLINEAR_KINEMATICS_ID,
        "director_gauge_id": DIRECTOR_GAUGE_ID,
        "external_rotation_map_id": EXTERNAL_ROTATION_MAP_ID,
        "bubble_convention": BUBBLE_CONVENTION,
        "bubble_state_role": BUBBLE_STATE_ROLE,
        "bubble_predictor_commit_policy_id": BUBBLE_PREDICTOR_COMMIT_POLICY_ID,
        "quadrature_id": QUADRATURE_ID,
        "nonlinear_policy_id": NONLINEAR_POLICY_ID,
        "recovery_policy_id": RECOVERY_POLICY_ID,
        "canonicalization_id": CANONICALIZATION_ID,
        "state_integrity_id": STATE_INTEGRITY_ID,
        "state_array_layout_id": STATE_ARRAY_LAYOUT_ID,
        "thickness_coordinate_sign_id": THICKNESS_COORDINATE_SIGN_ID,
        "stiffness_station_table_sha256": stiffness_station_table_fingerprint(),
        "lobatto_table_sha256": lobatto_table_fingerprint(),
        "state_field_manifest_sha256": state_field_manifest_fingerprint(),
        "thickness_quadrature_id": THICKNESS_QUADRATURE_ID,
        **identity,
        "committed_total_u": np.zeros(18, dtype=np.float64),
        "committed_director_triads": triads,
        "bubble_rotation_last_increment": np.zeros(2, dtype=np.float64),
        "committed_internal_force": np.zeros(18, dtype=np.float64),
        "station_generalized_strain": np.zeros(
            (NUM_INTEGRATION_STATIONS, GENERALIZED_COMPONENTS), dtype=np.float64
        ),
        "station_generalized_resultant": np.zeros(
            (NUM_INTEGRATION_STATIONS, GENERALIZED_COMPONENTS), dtype=np.float64
        ),
        "plastic_strain": zero_vectors(),
        "alpha": np.zeros(points, dtype=np.float64),
        "layer_strain": zero_vectors(),
        "layer_strain_material": zero_vectors(),
        "kinematic_layer_strain": zero_vectors(),
        "layer_stress": zero_vectors(),
        "layer_stress_material": zero_vectors(),
        **fields,
        "initial_field_provenance": provenance,
    }
    return validate_committed_s3_state(
        seal_committed_s3_state(state),
        expected_identity=identity,
    )


def _validate_identity(identity: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(identity, Mapping):
        raise S3CommittedStateError("expected_identity must be a mapping")
    unknown = set(identity) - _IDENTITY_KEYS
    missing = _IDENTITY_KEYS - set(identity)
    if unknown or missing:
        raise S3CommittedStateError(
            f"expected_identity keys mismatch; missing={_key_labels(missing)}, "
            f"unknown={_key_labels(unknown)}"
        )
    nodes = _node_ids(identity["node_ids"])
    result = {
        "formulation_fingerprint": _fingerprint(
            identity["formulation_fingerprint"], "formulation_fingerprint"
        ),
        "element_id": identity["element_id"],
        "element_configuration_fingerprint": _fingerprint(
            identity["element_configuration_fingerprint"],
            "element_configuration_fingerprint",
        ),
        "node_ids": nodes,
        "node_order_fingerprint": _fingerprint(
            identity["node_order_fingerprint"], "node_order_fingerprint"
        ),
        "reference_geometry_fingerprint": _fingerprint(
            identity["reference_geometry_fingerprint"],
            "reference_geometry_fingerprint",
        ),
        "reference_frame_fingerprint": _fingerprint(
            identity["reference_frame_fingerprint"],
            "reference_frame_fingerprint",
        ),
        "material_fingerprint": _fingerprint(
            identity["material_fingerprint"], "material_fingerprint"
        ),
        "initial_fields_fingerprint": _fingerprint(
            identity["initial_fields_fingerprint"], "initial_fields_fingerprint"
        ),
        "state_mode": identity["state_mode"],
        "thickness_quadrature_id": identity["thickness_quadrature_id"],
        "thickness": identity["thickness"],
        "num_layers": identity["num_layers"],
        "material_symmetry": identity["material_symmetry"],
        "equivalent_stress_measure": identity["equivalent_stress_measure"],
    }
    if isinstance(result["element_id"], (bool, np.bool_)) or not isinstance(
        result["element_id"], (int, np.integer)
    ):
        raise S3CommittedStateError("expected_identity element_id must be an integer")
    result["element_id"] = int(result["element_id"])
    if result["state_mode"] != STATE_MODE:
        raise S3CommittedStateError("expected_identity state_mode mismatch")
    if result["thickness_quadrature_id"] != THICKNESS_QUADRATURE_ID:
        raise S3CommittedStateError(
            "expected_identity thickness_quadrature_id mismatch"
        )
    if isinstance(result["thickness"], (bool, np.bool_)) or not isinstance(
        result["thickness"], (int, float, np.integer, np.floating)
    ):
        raise S3CommittedStateError("expected_identity thickness must be finite and positive")
    result["thickness"] = float(result["thickness"])
    if not math.isfinite(result["thickness"]) or result["thickness"] <= 0.0:
        raise S3CommittedStateError("expected_identity thickness must be finite and positive")
    result["num_layers"] = _layer_count(
        result["num_layers"], "expected_identity num_layers"
    )
    result["material_symmetry"], result["equivalent_stress_measure"] = (
        _constitutive_identity(
            result["material_symmetry"], result["equivalent_stress_measure"]
        )
    )
    if result["node_order_fingerprint"] != node_order_fingerprint(nodes):
        raise S3CommittedStateError("expected_identity node-order fingerprint mismatch")
    return result


def validate_committed_s3_state(
    state: Mapping[str, Any],
    *,
    expected_identity: Mapping[str, Any],
    expected_num_layers: int | None = None,
    expected_committed_total_u: Any | None = None,
) -> dict[str, Any]:
    """Strictly validate state and return a normalized, deeply owned mapping.

    Model compatibility for geometry and material is established only when the
    caller supplies ``expected_identity`` built from the current model.
    """

    if not isinstance(state, Mapping):
        raise S3CommittedStateError("qualified S3 committed state must be a mapping")
    non_string = {key for key in state if not isinstance(key, str)}
    if non_string:
        raise S3CommittedStateError(
            "committed state keys must be strings: "
            + ", ".join(_key_labels(non_string))
        )
    missing = _STATE_KEYS - set(state)
    unknown = set(state) - _STATE_KEYS
    if missing or unknown:
        raise S3CommittedStateError(
            f"committed state keys mismatch; missing={_key_labels(missing)}, "
            f"unknown={_key_labels(unknown)}"
        )

    expected_constants = {
        "state_schema": NONLINEAR_STATE_SCHEMA,
        "state_version": NONLINEAR_STATE_VERSION,
        "commit_status": COMMIT_STATUS,
        "state_mode": STATE_MODE,
        "formulation_id": FORMULATION_ID,
        "formulation_schema": FORMULATION_SCHEMA,
        "external_coordinate_layout_id": EXTERNAL_COORDINATE_LAYOUT_ID,
        "nonlinear_state_layout_id": NONLINEAR_STATE_LAYOUT_ID,
        "nonlinear_kinematics_id": NONLINEAR_KINEMATICS_ID,
        "director_gauge_id": DIRECTOR_GAUGE_ID,
        "external_rotation_map_id": EXTERNAL_ROTATION_MAP_ID,
        "bubble_convention": BUBBLE_CONVENTION,
        "bubble_state_role": BUBBLE_STATE_ROLE,
        "bubble_predictor_commit_policy_id": BUBBLE_PREDICTOR_COMMIT_POLICY_ID,
        "quadrature_id": QUADRATURE_ID,
        "nonlinear_policy_id": NONLINEAR_POLICY_ID,
        "recovery_policy_id": RECOVERY_POLICY_ID,
        "canonicalization_id": CANONICALIZATION_ID,
        "state_integrity_id": STATE_INTEGRITY_ID,
        "state_array_layout_id": STATE_ARRAY_LAYOUT_ID,
        "thickness_coordinate_sign_id": THICKNESS_COORDINATE_SIGN_ID,
        "stiffness_station_table_sha256": stiffness_station_table_fingerprint(),
        "lobatto_table_sha256": lobatto_table_fingerprint(),
        "state_field_manifest_sha256": state_field_manifest_fingerprint(),
        "thickness_quadrature_id": THICKNESS_QUADRATURE_ID,
    }
    for key, expected in expected_constants.items():
        actual = state[key]
        if key == "state_version":
            matches = isinstance(actual, (int, np.integer)) and not isinstance(
                actual, (bool, np.bool_)
            ) and int(actual) == expected
        else:
            matches = isinstance(actual, str) and actual == expected
        if not matches:
            raise S3CommittedStateError(f"incompatible {key}")

    nodes = _node_ids(state["node_ids"])
    fingerprint_values = {
        "formulation_fingerprint": _fingerprint(
            state["formulation_fingerprint"], "formulation_fingerprint"
        ),
        "element_configuration_fingerprint": _fingerprint(
            state["element_configuration_fingerprint"],
            "element_configuration_fingerprint",
        ),
        "node_order_fingerprint": _fingerprint(
            state["node_order_fingerprint"], "node_order_fingerprint"
        ),
        "reference_geometry_fingerprint": _fingerprint(
            state["reference_geometry_fingerprint"],
            "reference_geometry_fingerprint",
        ),
        "reference_frame_fingerprint": _fingerprint(
            state["reference_frame_fingerprint"],
            "reference_frame_fingerprint",
        ),
        "material_fingerprint": _fingerprint(
            state["material_fingerprint"], "material_fingerprint"
        ),
        "initial_fields_fingerprint": _fingerprint(
            state["initial_fields_fingerprint"], "initial_fields_fingerprint"
        ),
        "state_integrity_sha256": _fingerprint(
            state["state_integrity_sha256"], "state_integrity_sha256"
        ),
    }
    element_id_value = state["element_id"]
    if isinstance(element_id_value, (bool, np.bool_)) or not isinstance(
        element_id_value, (int, np.integer)
    ):
        raise S3CommittedStateError("element_id must be an integer")
    element_id = int(element_id_value)
    if fingerprint_values["node_order_fingerprint"] != node_order_fingerprint(nodes):
        raise S3CommittedStateError("node-order fingerprint mismatch")
    if fingerprint_values["formulation_fingerprint"] != formulation_fingerprint():
        raise S3CommittedStateError("formulation fingerprint mismatch")

    layers = _layer_count(state["num_layers"], "num_layers")
    thickness_value = state["thickness"]
    if isinstance(thickness_value, (bool, np.bool_)) or not isinstance(
        thickness_value, (int, float, np.integer, np.floating)
    ):
        raise S3CommittedStateError("thickness must be finite and positive")
    thickness = float(thickness_value)
    if not math.isfinite(thickness) or thickness <= 0.0:
        raise S3CommittedStateError("thickness must be finite and positive")
    if expected_num_layers is not None:
        expected_layers = _layer_count(
            expected_num_layers, "expected_num_layers"
        )
        if layers != expected_layers:
            raise S3CommittedStateError("num_layers does not match the current analysis")

    symmetry, measure = _constitutive_identity(
        state["material_symmetry"], state["equivalent_stress_measure"]
    )

    normalized: dict[str, Any] = dict(expected_constants)
    normalized.update(
        {
            "formulation_fingerprint": fingerprint_values["formulation_fingerprint"],
            "element_id": element_id,
            "element_configuration_fingerprint": fingerprint_values[
                "element_configuration_fingerprint"
            ],
            "node_ids": nodes,
            "node_order_fingerprint": fingerprint_values["node_order_fingerprint"],
            "reference_geometry_fingerprint": fingerprint_values[
                "reference_geometry_fingerprint"
            ],
            "reference_frame_fingerprint": fingerprint_values[
                "reference_frame_fingerprint"
            ],
            "material_fingerprint": fingerprint_values["material_fingerprint"],
            "initial_fields_fingerprint": fingerprint_values[
                "initial_fields_fingerprint"
            ],
            "state_integrity_sha256": fingerprint_values[
                "state_integrity_sha256"
            ],
            "num_layers": layers,
            "thickness": thickness,
            "material_symmetry": symmetry,
            "equivalent_stress_measure": measure,
        }
    )
    for key, shape in _ARRAY_SHAPES_FIXED.items():
        normalized[key] = _finite_state_array(state[key], shape, key)
    _validate_triads(normalized["committed_director_triads"])
    if np.any(normalized["bubble_rotation_last_increment"] != 0.0):
        raise S3CommittedStateError(
            "committed bubble predictor must reset to exact zero in the frozen gauge policy"
        )

    points = NUM_INTEGRATION_STATIONS * layers
    for key in _LAYER_VECTOR_FIELDS:
        normalized[key] = _finite_state_array(state[key], (points, 3), key)
    normalized["alpha"] = _finite_state_array(
        state["alpha"], (points,), "alpha"
    )
    if np.any(normalized["alpha"] < 0.0):
        raise S3CommittedStateError("material hardening alpha must be nonnegative")

    z_layers, layer_weights = qualified_s3_lobatto_layers(layers, thickness)
    station_strain = normalized["station_generalized_strain"]
    expected_kinematic = (
        station_strain[:, None, :3]
        + z_layers[None, :, None] * station_strain[:, None, 3:6]
    ).reshape(points, 3)
    redundancy_scale = max(
        1.0,
        float(np.max(np.abs(expected_kinematic))),
        float(np.max(np.abs(normalized["kinematic_layer_strain"]))),
    )
    redundancy_tolerance = (
        STATE_REDUNDANCY_TOLERANCE_FACTOR
        * np.finfo(np.float64).eps
        * redundancy_scale
    )
    if not np.allclose(
        normalized["kinematic_layer_strain"],
        expected_kinematic,
        rtol=0.0,
        atol=redundancy_tolerance,
    ):
        raise S3CommittedStateError(
            "kinematic layer strain contradicts station generalized strain"
        )

    local_stress = normalized["layer_stress"].reshape(
        NUM_INTEGRATION_STATIONS,
        layers,
        3,
    )
    expected_membrane = np.einsum("l,gli->gi", layer_weights, local_stress)
    expected_bending = np.einsum(
        "l,l,gli->gi",
        layer_weights,
        z_layers,
        local_stress,
    )
    expected_inplane_resultants = np.concatenate(
        (expected_membrane, expected_bending),
        axis=1,
    )
    stored_inplane_resultants = normalized["station_generalized_resultant"][:, :6]
    resultant_scale = max(
        1.0,
        float(np.max(np.abs(expected_inplane_resultants))),
        float(np.max(np.abs(stored_inplane_resultants))),
    )
    resultant_tolerance = (
        STATE_REDUNDANCY_TOLERANCE_FACTOR
        * np.finfo(np.float64).eps
        * resultant_scale
    )
    if not np.allclose(
        stored_inplane_resultants,
        expected_inplane_resultants,
        rtol=0.0,
        atol=resultant_tolerance,
    ):
        raise S3CommittedStateError(
            "station generalized resultants contradict stored layer stress"
        )

    provenance_value = state["initial_field_provenance"]
    if not isinstance(provenance_value, Mapping):
        raise S3CommittedStateError("initial_field_provenance must be a mapping")
    provenance = _canonical_value(
        provenance_value, path="$.initial_field_provenance"
    )
    assert isinstance(provenance, dict)
    normalized["initial_field_provenance"] = provenance
    current_initial_fingerprint = _initial_fields_fingerprint(normalized, provenance)
    if current_initial_fingerprint != normalized["initial_fields_fingerprint"]:
        raise S3CommittedStateError("initial-fields fingerprint mismatch")

    state_identity = {
        "formulation_fingerprint": normalized["formulation_fingerprint"],
        "element_id": normalized["element_id"],
        "element_configuration_fingerprint": normalized[
            "element_configuration_fingerprint"
        ],
        "node_ids": nodes,
        "node_order_fingerprint": normalized["node_order_fingerprint"],
        "reference_geometry_fingerprint": normalized[
            "reference_geometry_fingerprint"
        ],
        "reference_frame_fingerprint": normalized["reference_frame_fingerprint"],
        "material_fingerprint": normalized["material_fingerprint"],
        "initial_fields_fingerprint": normalized["initial_fields_fingerprint"],
        "state_mode": normalized["state_mode"],
        "thickness_quadrature_id": normalized["thickness_quadrature_id"],
        "thickness": normalized["thickness"],
        "num_layers": normalized["num_layers"],
        "material_symmetry": normalized["material_symmetry"],
        "equivalent_stress_measure": normalized["equivalent_stress_measure"],
    }
    expected = _validate_identity(expected_identity)
    if state_identity != expected:
        mismatched = sorted(
            key for key in _IDENTITY_KEYS if state_identity[key] != expected[key]
        )
        raise S3CommittedStateError(
            "state identity does not match current model: " + ", ".join(mismatched)
        )

    if expected_committed_total_u is not None:
        expected_u = _finite_array(
            expected_committed_total_u, (18,), "expected_committed_total_u"
        )
        if not np.array_equal(normalized["committed_total_u"], expected_u):
            raise S3CommittedStateError(
                "committed_total_u does not match the current global displacement slice"
            )

    actual_integrity = _state_integrity_sha256(normalized)
    if actual_integrity != normalized["state_integrity_sha256"]:
        raise S3CommittedStateError("committed state integrity fingerprint mismatch")

    return normalized


__all__ = [
    "BUBBLE_CONVENTION",
    "BUBBLE_CONDITION_LIMIT",
    "BUBBLE_FORCE_CONDENSATION_ID",
    "BUBBLE_LINE_SEARCH_MIN_FACTOR",
    "BUBBLE_LINE_SEARCH_REDUCTION",
    "BUBBLE_MAX_ITERATIONS",
    "BUBBLE_OFFSET_D",
    "BUBBLE_OFFSET_EXACT",
    "BUBBLE_POLYNOMIAL_SCALE",
    "BUBBLE_PREDICTOR_COMMIT_POLICY_ID",
    "BUBBLE_RELATIVE_TOLERANCE",
    "BUBBLE_STATE_ROLE",
    "BUBBLE_STEP_TOLERANCE",
    "CANONICALIZATION_ID",
    "COMMIT_STATUS",
    "DIRECTOR_GAUGE_FALLBACK_AXIS",
    "DIRECTOR_GAUGE_ID",
    "DIRECTOR_GAUGE_PRIMARY_AXIS",
    "DIRECTOR_GAUGE_SWITCH_TOLERANCE",
    "DIRECTOR_ORTHONORMALITY_TOLERANCE",
    "DRILL_SCALE_INVERSE_METRIC_SQRT",
    "DRILL_SCALE_METRIC",
    "DRILL_SCALE_POLICY_ID",
    "DRILL_SCALE_PROJECTOR",
    "ELEMENT_CONFIGURATION_DESCRIPTOR_SCHEMA",
    "EXTERNAL_COORDINATE_LAYOUT_ID",
    "EXTERNAL_ROTATION_MAP_ID",
    "FORMULATION_ID",
    "FORMULATION_SCHEMA",
    "GENERALIZED_COMPONENTS",
    "GENERALIZED_COMPONENT_ORDER",
    "GENERALIZED_RESULTANT_COMPONENT_ORDER",
    "GENERALIZED_SECTION_INTEGRATION_ID",
    "GENERALIZED_STRAIN_COMPONENT_ORDER",
    "INITIAL_FIELD_NAMES",
    "ISOTROPIC_CONSTITUTIVE_INTEGRATION_ID",
    "LAYER_COMPONENT_ORDER",
    "LAYER_STRAIN_COMPONENT_ORDER",
    "LAYER_STRESS_COMPONENT_ORDER",
    "LOBATTO_NORMALIZED_TABLES",
    "MATERIAL_DESCRIPTOR_SCHEMA",
    "MATERIAL_DESCRIPTOR_VALIDATION_ID",
    "MINIMUM_OWNER_NORMAL_ALIGNMENT",
    "MITC3_PLUS_EQUATION_MAP",
    "MITC3_PLUS_NONLINEAR_EQUATION_MAP",
    "MITC3_PLUS_NONLINEAR_SOURCE_BYTES",
    "MITC3_PLUS_NONLINEAR_SOURCE_SHA256",
    "MITC3_PLUS_NONLINEAR_SOURCE_URL",
    "MITC3_PLUS_SOURCE_BYTES",
    "MITC3_PLUS_SOURCE_SHA256",
    "MITC3_PLUS_SOURCE_URL",
    "NONLINEAR_KINEMATICS_ID",
    "NONLINEAR_POLICY_ID",
    "NONLINEAR_SOURCE_SHA256",
    "NONLINEAR_STATE_LAYOUT_ID",
    "NONLINEAR_STATE_SCHEMA",
    "NONLINEAR_STATE_VERSION",
    "NUM_INTEGRATION_STATIONS",
    "ORTHOTROPIC_CONSTITUTIVE_INTEGRATION_ID",
    "PL_BASIS_ID",
    "PL_BLOCK_SIGN_ID",
    "PL_CONDENSATION_ID",
    "PL_CONSTRAINT_ID",
    "PL_GRAM_NUMERATOR",
    "PL_GRAM_SCALE_ID",
    "QUADRATURE_ID",
    "RECOVERY_POLICY_ID",
    "REFERENCE_GEOMETRY_VALIDATION_ID",
    "S3CommittedStateError",
    "STATE_ARRAY_LAYOUT_ID",
    "STATE_FIELD_MANIFEST",
    "STATE_INTEGRITY_ID",
    "STATE_MODE",
    "STATE_REDUNDANCY_VALIDATION_ID",
    "STIFFNESS_STATION_TABLE",
    "SUPPORTED_LOBATTO_LAYER_COUNTS",
    "THICKNESS_COORDINATE_SIGN_ID",
    "THICKNESS_QUADRATURE_ID",
    "TYING_POINTS",
    "TYING_POINT_DEFINITIONS",
    "build_element_configuration_descriptor",
    "build_state_identity",
    "canonical_json_bytes",
    "canonical_sha256",
    "element_configuration_fingerprint",
    "formulation_fingerprint",
    "formulation_fingerprint_payload",
    "formulation_mechanics_contract_payload",
    "formulation_mechanics_fingerprint",
    "initialize_zero_committed_s3_state",
    "lobatto_table_fingerprint",
    "material_fingerprint",
    "node_order_fingerprint",
    "reference_frame_fingerprint",
    "reference_geometry_fingerprint",
    "reconstruct_director_triad",
    "qualified_s3_lobatto_layers",
    "qualified_s3_triangle_frame",
    "require_qualified_s3_quality",
    "resolved_material_descriptor",
    "seal_committed_s3_state",
    "state_field_manifest_fingerprint",
    "stiffness_station_table_fingerprint",
    "strict_canonical_json_loads",
    "validate_committed_s3_state",
]
