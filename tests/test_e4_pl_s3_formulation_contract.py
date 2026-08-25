from __future__ import annotations

import json
from decimal import Decimal
import math
from pathlib import Path

import pytest

from anysolver.algebraic_dynamics import (
    DESCRIPTOR_COORDINATE_SHEAR_LIMIT,
    DESCRIPTOR_DENSE_CONDENSATION_LIMIT,
    DESCRIPTOR_MODAL_POLICY_ID,
    DESCRIPTOR_SHIFT_RATIO,
    DESCRIPTOR_TRANSIENT_FIRST_ORDER_POLICY_ID,
    DESCRIPTOR_TRANSIENT_CONSTRAINED_POLICY_ID,
    DESCRIPTOR_TRANSIENT_POLICY_ID,
    DESCRIPTOR_TRANSIENT_STATIC_POLICY_ID,
)
from anysolver.e4_pl_s3_element import (
    ALGEBRAIC_COORDINATE_POLICY_ID,
    BUBBLE_OFFSET_D,
    FORMULATION_ID,
    GEOMETRIC_STIFFNESS_POLICY_ID,
    HOMOGENEOUS_ELASTIC_STRESS_PROFILE_ID,
    MASS_MOMENT_ID,
    MITC3_PLUS_NONLINEAR_EQUATION_MAP,
    MITC3_PLUS_NONLINEAR_SOURCE_BYTES,
    MITC3_PLUS_NONLINEAR_SOURCE_SHA256,
    MITC3_PLUS_SOURCE_BYTES,
    MITC3_PLUS_SOURCE_SHA256,
    QUADRATURE_ID,
    RECOVERY_POLICY_ID,
    REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID,
    RESULTANT_SUMMARY_POLICY_ID,
    TRIANGLE_QUADRATURE,
    TYING_POINTS,
)
from anysolver.e4_pl_s3_state import (
    BUBBLE_CONVENTION as STATE_BUBBLE_CONVENTION,
    BUBBLE_CONDITION_LIMIT,
    BUBBLE_FORCE_CONDENSATION_ID,
    BUBBLE_LINE_SEARCH_MIN_FACTOR,
    BUBBLE_LINE_SEARCH_REDUCTION,
    BUBBLE_MAX_ITERATIONS,
    BUBBLE_PREDICTOR_COMMIT_POLICY_ID,
    BUBBLE_RELATIVE_TOLERANCE,
    BUBBLE_STEP_TOLERANCE,
    CANONICALIZATION_ID,
    DIRECTOR_GAUGE_FALLBACK_AXIS,
    DIRECTOR_GAUGE_ID,
    DIRECTOR_GAUGE_PRIMARY_AXIS,
    DIRECTOR_GAUGE_SWITCH_TOLERANCE,
    EXTERNAL_COORDINATE_LAYOUT_ID,
    EXTERNAL_ROTATION_MAP_ID,
    GENERALIZED_RESULTANT_COMPONENT_ORDER,
    GENERALIZED_SECTION_INTEGRATION_ID,
    GENERALIZED_STRAIN_COMPONENT_ORDER,
    ISOTROPIC_CONSTITUTIVE_INTEGRATION_ID,
    LAYER_STRAIN_COMPONENT_ORDER,
    LAYER_STRESS_COMPONENT_ORDER,
    MATERIAL_DESCRIPTOR_VALIDATION_ID,
    NONLINEAR_KINEMATICS_ID,
    NONLINEAR_POLICY_ID,
    NONLINEAR_STATE_LAYOUT_ID,
    NONLINEAR_STATE_SCHEMA,
    ORTHOTROPIC_CONSTITUTIVE_INTEGRATION_ID,
    REFERENCE_GEOMETRY_VALIDATION_ID,
    STATE_ARRAY_LAYOUT_ID,
    STATE_FIELD_MANIFEST,
    STATE_INTEGRITY_ID,
    STATE_MODE,
    STATE_REDUNDANCY_VALIDATION_ID,
    SUPPORTED_LOBATTO_LAYER_COUNTS,
    THICKNESS_COORDINATE_SIGN_ID,
    THICKNESS_QUADRATURE_ID,
    formulation_fingerprint,
    formulation_mechanics_contract_payload,
    formulation_mechanics_fingerprint,
    lobatto_table_fingerprint,
    state_field_manifest_fingerprint,
    stiffness_station_table_fingerprint,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs/reference_cases/e4_pl_s3_formulation_contract.json"


def _reject_constant(value: str):
    raise ValueError(f"non-finite JSON constant {value}")


def _load_contract_bytes(raw: bytes) -> dict:
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise ValueError("contract must be UTF-8 with exactly LF line endings")

    def reject_duplicate(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    value = json.loads(
        raw.decode("utf-8", errors="strict"),
        object_pairs_hook=reject_duplicate,
        parse_constant=_reject_constant,
    )

    def require_finite(member: object) -> None:
        if isinstance(member, float) and not math.isfinite(member):
            raise ValueError("contract contains a non-finite number")
        if isinstance(member, dict):
            for nested in member.values():
                require_finite(nested)
        elif isinstance(member, list):
            for nested in member:
                require_finite(nested)

    require_finite(value)
    canonical = (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    if raw != canonical:
        raise ValueError("contract JSON is not in sorted canonical form")
    assert isinstance(value, dict)
    return value


def _contract() -> dict:
    return _load_contract_bytes(CONTRACT_PATH.read_bytes())


def test_contract_binds_the_exact_public_source_and_candidate() -> None:
    contract = _contract()
    primary = contract["source_authority"]["primary"]

    assert contract["schema"] == "anysolver.e4-pl-s3-formulation-contract-v1"
    assert contract["candidate_id"] == FORMULATION_ID
    assert primary["bytes"] == MITC3_PLUS_SOURCE_BYTES == 1_146_142
    assert primary["sha256"] == MITC3_PLUS_SOURCE_SHA256
    assert contract["formulation"]["bubble_offset_d"] == "1/10000"
    assert BUBBLE_OFFSET_D == pytest.approx(1.0e-4, rel=0.0, abs=0.0)


def test_contract_binds_the_native_nonlinear_equation_authority() -> None:
    nonlinear = _contract()["source_authority"]["nonlinear"]

    assert nonlinear["bytes"] == MITC3_PLUS_NONLINEAR_SOURCE_BYTES == 2_312_312
    assert nonlinear["sha256"] == MITC3_PLUS_NONLINEAR_SOURCE_SHA256
    assert nonlinear["equation_map"] == {
        "assumed_nonlinear_covariant_shear": "PDF_PAGE_9_EQUATIONS_29_TO_31",
        "current_geometry_and_increment": "PDF_PAGES_4_TO_5_EQUATIONS_7_TO_9",
        "director_update": "PDF_PAGES_5_TO_6_EQUATIONS_10_TO_15",
        "incremental_green_lagrange": "PDF_PAGES_8_TO_9_EQUATIONS_22_TO_28",
        "quadratic_director_increment": "PDF_PAGE_8_EQUATIONS_16_TO_21",
    }
    assert MITC3_PLUS_NONLINEAR_EQUATION_MAP == {
        "current_geometry": "equations_7_to_9",
        "director_update": "equations_10_to_15",
        "quadratic_director_increment": "equations_16_to_21",
        "incremental_green_lagrange": "equations_22_to_28",
        "assumed_nonlinear_covariant_shear": "equations_29_to_31",
    }


def test_contract_binds_native_nonlinear_gauge_rotation_and_state() -> None:
    native = _contract()["native_nonlinear_kinematics"]

    assert native == {
        "bubble_equilibrium_policy": {
            "condition_limit": BUBBLE_CONDITION_LIMIT,
            "force_condensation_id": BUBBLE_FORCE_CONDENSATION_ID,
            "line_search_min_factor": BUBBLE_LINE_SEARCH_MIN_FACTOR,
            "line_search_reduction": BUBBLE_LINE_SEARCH_REDUCTION,
            "max_iterations": BUBBLE_MAX_ITERATIONS,
            "relative_tolerance": BUBBLE_RELATIVE_TOLERANCE,
            "step_tolerance": BUBBLE_STEP_TOLERANCE,
        },
        "commit_rotation": (
            "RODRIGUES_OF_A_EFFECTIVE_V1_PLUS_B_EFFECTIVE_V2_RETAINED_STEP_"
            "CONVENTION_WITH_O3_TARGET_DIRECTOR_DIFFERENCE"
        ),
        "constitutive_integration_ids": {
            "generalized_section": GENERALIZED_SECTION_INTEGRATION_ID,
            "isotropic": ISOTROPIC_CONSTITUTIVE_INTEGRATION_ID,
            "orthotropic": ORTHOTROPIC_CONSTITUTIVE_INTEGRATION_ID,
        },
        "director_gauge": {
            "fallback_axis_global": ["0", "0", "1"],
            "fallback_rule": (
                "USE_FALLBACK_WHEN_NORM_PRIMARY_CROSS_VN_LE_1E_MINUS_12"
            ),
            "id": DIRECTOR_GAUGE_ID,
            "primary_axis_global": ["0", "1", "0"],
            "reconstruction": (
                "V1=NORMALIZE(AXIS_CROSS_VN)_AND_V2=VN_CROSS_V1_AFTER_EVERY_COMMIT"
            ),
            "validation": (
                "STORED_TANGENTS_MUST_EQUAL_RECONSTRUCTION_WITH_ABSOLUTE_"
                "TOLERANCE_1E_MINUS_12"
            ),
        },
        "external_rotation_map": {
            "a": "PHI_DOT_V1",
            "a_effective": "a-(d*b)/2",
            "b": "PHI_DOT_V2",
            "b_effective": "b+(d*a)/2",
            "d": "PHI_DOT_VN",
            "id": EXTERNAL_ROTATION_MAP_ID,
            "mixed_drill_tilt": (
                "RETAINED_SECOND_ORDER_DIRECTOR_COORDINATE_PULLBACK"
            ),
            "pure_drill": "EXACT_PHYSICAL_NULL_WHEN_A_AND_B_ARE_ZERO",
        },
        "hierarchical_source_node": {
            "first_order": (
                "A4=MEAN_A_CORNER_PLUS_ALPHA1_AND_B4=MEAN_B_CORNER_PLUS_ALPHA2"
            ),
            "physical_update": "SOURCE_NODE_4_USES_ITS_OWN_CURRENT_EQ11_GAUGE",
            "second_order": (
                "A4_SECOND=MEAN_A_CORNER_SECOND_AND_B4_SECOND=MEAN_B_CORNER_SECOND"
            ),
        },
        "incremental_director": (
            "MINUS_A_EFFECTIVE_V2_PLUS_B_EFFECTIVE_V1_MINUS_HALF_"
            "(A_SQUARED_PLUS_B_SQUARED)_VN"
        ),
        "policy_id": NONLINEAR_POLICY_ID,
        "quadratic_square_rule": (
            "SQUARE_ONLY_FIRST_ORDER_A_AND_B_NEVER_A_EFFECTIVE_OR_B_EFFECTIVE"
        ),
        "reference_component_basis": (
            "EXPLICIT_FROZEN_REFERENCE_NODES_AND_REFERENCE_FRAME_REQUIRED_NO_"
            "CURRENT_BASIS_FALLBACK"
        ),
        "state": {
            "bubble_convention": STATE_BUBBLE_CONVENTION,
            "bubble_predictor_commit_policy_id": (
                BUBBLE_PREDICTOR_COMMIT_POLICY_ID
            ),
            "canonicalization_id": CANONICALIZATION_ID,
            "external_coordinate_layout_id": EXTERNAL_COORDINATE_LAYOUT_ID,
            "field_manifest_sha256": state_field_manifest_fingerprint(),
            "formulation_fingerprint_sha256": formulation_fingerprint(),
            "formulation_mechanics_sha256": formulation_mechanics_fingerprint(),
            "generalized_resultant_component_order": list(
                GENERALIZED_RESULTANT_COMPONENT_ORDER
            ),
            "generalized_strain_component_order": list(
                GENERALIZED_STRAIN_COMPONENT_ORDER
            ),
            "layer_strain_component_order": list(LAYER_STRAIN_COMPONENT_ORDER),
            "layer_stress_component_order": list(LAYER_STRESS_COMPONENT_ORDER),
            "layout_id": NONLINEAR_STATE_LAYOUT_ID,
            "lobatto_table_sha256": lobatto_table_fingerprint(),
            "material_descriptor_validation_id": (
                MATERIAL_DESCRIPTOR_VALIDATION_ID
            ),
            "nonlinear_kinematics_id": NONLINEAR_KINEMATICS_ID,
            "quadrature_id": QUADRATURE_ID,
            "reference_geometry_validation_id": (
                REFERENCE_GEOMETRY_VALIDATION_ID
            ),
            "recovery_policy_id": RECOVERY_POLICY_ID,
            "schema": NONLINEAR_STATE_SCHEMA,
            "state_array_layout_id": STATE_ARRAY_LAYOUT_ID,
            "state_integrity_id": STATE_INTEGRITY_ID,
            "state_mode": STATE_MODE,
            "state_redundancy_validation_id": (
                STATE_REDUNDANCY_VALIDATION_ID
            ),
            "stiffness_station_table_sha256": (
                stiffness_station_table_fingerprint()
            ),
            "supported_lobatto_layer_counts": list(
                SUPPORTED_LOBATTO_LAYER_COUNTS
            ),
            "thickness_coordinate_sign_id": THICKNESS_COORDINATE_SIGN_ID,
            "thickness_quadrature_id": THICKNESS_QUADRATURE_ID,
        },
    }
    assert tuple(
        float(value)
        for value in native["director_gauge"]["primary_axis_global"]
    ) == DIRECTOR_GAUGE_PRIMARY_AXIS
    assert tuple(
        float(value)
        for value in native["director_gauge"]["fallback_axis_global"]
    ) == DIRECTOR_GAUGE_FALLBACK_AXIS
    assert DIRECTOR_GAUGE_SWITCH_TOLERANCE == 1.0e-12
    assert STATE_FIELD_MANIFEST["station_generalized_resultant"][
        "component_frame"
    ] == "numbered_reference_tensor_resultant"
    assert STATE_FIELD_MANIFEST["layer_strain_material"][
        "point_order"
    ] == "station_major_layer_minor_bottom_to_top"


@pytest.mark.parametrize(
    "raw",
    (
        b'{\n  "a": 1,\n  "a": 2\n}\n',
        b'{\r\n  "a": 1\r\n}\r\n',
        b'{\n  "a": 1e999\n}\n',
        b'{\n  "a": 1\n}',
        b'\xef\xbb\xbf{\n  "a": 1\n}\n',
        b'{"a":1}\n',
    ),
)
def test_contract_loader_rejects_duplicate_nonfinite_and_noncanonical_json(
    raw: bytes,
) -> None:
    with pytest.raises((AssertionError, ValueError, UnicodeError)):
        _load_contract_bytes(raw)


def test_tying_points_and_quadrature_are_transcribed_without_aliases() -> None:
    contract = _contract()
    mechanics = formulation_mechanics_contract_payload()
    assert set(TYING_POINTS) == {"A", "B", "C", "D", "E", "F"}
    expected_points = {
        "A": (1.0 / 6.0, 2.0 / 3.0),
        "B": (2.0 / 3.0, 1.0 / 6.0),
        "C": (1.0 / 6.0, 1.0 / 6.0),
        "D": (1.0 / 3.0 + 1.0e-4, 1.0 / 3.0 - 2.0e-4),
        "E": (1.0 / 3.0 - 2.0e-4, 1.0 / 3.0 + 1.0e-4),
        "F": (1.0 / 3.0 + 1.0e-4, 1.0 / 3.0 + 1.0e-4),
    }
    for label, expected in expected_points.items():
        assert TYING_POINTS[label] == pytest.approx(expected)
        assert tuple(mechanics["bubble"]["tying_point_binary64"][label]) == (
            TYING_POINTS[label]
        )
        assert list(mechanics["bubble"]["tying_point_definitions"][label]) == (
            contract["formulation"]["tying_points"][label]
        )
    assert mechanics["bubble"]["offset_d_exact"] == contract["formulation"][
        "bubble_offset_d"
    ]
    assert mechanics["pl_completion"]["basis_id"] == "BARYCENTRIC_L1_L2_L3_V1"
    assert mechanics["drilling_scale"]["projector"] == (
        (1.0, 0.0),
        (-1.0, 0.0),
        (0.0, 1.0),
    )
    assert contract["quadrature"]["stiffness"]["id"].startswith("DUNAVANT_DEGREE_5")
    assert QUADRATURE_ID == "dunavant_degree5_7point"
    assert len(TRIANGLE_QUADRATURE) == 7
    assert sum(weight for _r, _s, weight in TRIANGLE_QUADRATURE) == pytest.approx(0.5)


def test_pl_and_rank_contract_are_exactly_frozen() -> None:
    contract = _contract()
    pl = contract["pl_completion"]
    ranks = contract["rank_contract"]

    assert pl["one_point_centroid_integration"] == "FORBIDDEN"
    assert pl["saddle_tau_tau"] == "-M/kD"
    assert ranks["uncondensed_physical_17"] == {
        "inertia_negative": 0,
        "inertia_positive": 11,
        "inertia_zero": 6,
        "nullity": 6,
        "rank": 11,
    }
    assert ranks["condensed_external_18"] == {"nullity": 6, "rank": 12}
    assert ranks["full_saddle_23"] == {
        "inertia_negative": 3,
        "inertia_positive": 14,
        "inertia_zero": 6,
        "nullity": 6,
        "rank": 17,
    }
    assert contract["serialization_fingerprint"] == {
        "algebraic_coordinate_policy": ALGEBRAIC_COORDINATE_POLICY_ID,
        "bubble_convention": "hierarchical_rotation_relative_to_corner_average",
        "dynamic_reduction_policy": "GUYAN_STATIC_BUBBLE_FULL_CONSISTENT_MASS_V1",
        "formulation_id": FORMULATION_ID,
        "formulation_schema": "anysolver.e4_pl_s3.linear.v1",
        "geometric_stiffness_policy": GEOMETRIC_STIFFNESS_POLICY_ID,
        "mass_moment_id": MASS_MOMENT_ID,
        "quadrature_id": "dunavant_degree5_7point",
        "recovery_policy_id": RECOVERY_POLICY_ID,
        "state_layout_id": "S3_EXTERNAL18_BUBBLE2_PL3_LINEAR_V1",
    }
    assert contract["recovery_policy"] == {
        "bubble_state": "ELASTIC_SCHUR_BACK_SUBSTITUTION_USED_BY_THE_TANGENT",
        "director_reversal": "EXCLUDED_PENDING_NATIVE_REVERSAL_PARITY",
        "engineering_conventions": (
            "MEMBRANE_AND_CURVATURE_ENGINEERING_SHEAR_WITH_TENSOR_N_AND_M"
        ),
        "failure_policy": (
            "QUALIFIED_RECOVERY_ERRORS_PROPAGATE_WITHOUT_SILENT_ELEMENT_OMISSION"
        ),
        "generalized_sections": (
            "SEVEN_STATION_RESULTANTS_ONLY_WITHOUT_FABRICATED_PHYSICAL_STRESS"
        ),
        "geometric_prestress_provenance": (
            "HOMOGENEOUS_PHYSICAL_RECOVERY_EMITS_REFERENCE_BUBBLE_AND_"
            "THROUGH_THICKNESS_PROFILE_IDS_GENERALIZED_RECOVERY_DOES_NOT"
        ),
        "global_transport": (
            "SURFACE_TENSORS_AND_N_M_BY_FRAME_CONGRUENCE_Q_BY_FRAME_VECTOR_MAP"
        ),
        "hill48_measure": (
            "MAX_TOP_BOTTOM_MATERIAL_AXIS_PLANE_STRESS_TRANSVERSE_SHEAR_"
            "EXCLUDED_UTILIZATION_OVER_X"
        ),
        "homogeneous_surface_stress": "SIGMA_M=N_OVER_H_SIGMA_B=6M_OVER_H_SQUARED",
        "kinematics": "NATIVE_SEVEN_STATION_MITC3_PLUS_WITH_RECOVERED_BUBBLE",
        "material_orientation": (
            "PHYSICAL_SURFACE_DIRECTION_PLUS_SIGNED_ANGLE_ABOUT_OWNER_DIRECTOR"
        ),
        "nonlinear_history_patch": "EXCLUDED_PENDING_FORMULATION_NATIVE_PARITY",
        "numerical_fields": "PL_AND_DRILL_EXCLUDED_FROM_PHYSICAL_RECOVERY",
        "policy_id": RECOVERY_POLICY_ID,
        "resultant_sign": "TENSION_POSITIVE_N_M_Q",
        "summary_policy": RESULTANT_SUMMARY_POLICY_ID,
        "surface_sign": (
            "TOP_PLUS_H_OVER_2_ALONG_AUTHORITATIVE_DIRECTOR_BOTTOM_MINUS_H_OVER_2"
        ),
        "transverse_shear": (
            "Q_OVER_H_EQUALS_FIVE_SIXTHS_G_GAMMA_REPEATED_AT_BOTH_SURFACES"
        ),
        "von_mises_measure": (
            "MAX_TOP_BOTTOM_3D_EQUIVALENT_WITH_AVERAGE_TRANSVERSE_SHEAR"
        ),
    }
    assert contract["dynamic_policy"]["descriptor_modal_policy"] == DESCRIPTOR_MODAL_POLICY_ID
    assert float(contract["dynamic_policy"]["descriptor_shift_ratio"]) == (
        DESCRIPTOR_SHIFT_RATIO
    )
    assert contract["dynamic_policy"]["descriptor_bounded_coordinate_solver"] == (
        "STATIC_CONDENSATION_THROUGH_REDUCED_DIMENSION_512"
    )
    assert int(contract["dynamic_policy"]["descriptor_coordinate_shear_limit"]) == (
        int(DESCRIPTOR_COORDINATE_SHEAR_LIMIT)
    )
    assert DESCRIPTOR_DENSE_CONDENSATION_LIMIT == 512
    assert contract["dynamic_policy"]["descriptor_large_system_policy"] == (
        "SWAPPED_PENCIL_WITH_FAIL_CLOSED_COORDINATE_SHEAR"
    )
    assert contract["dynamic_policy"]["descriptor_transient_policy"] == (
        DESCRIPTOR_TRANSIENT_POLICY_ID
    )
    assert contract["dynamic_policy"]["descriptor_transient_static_policy"] == (
        DESCRIPTOR_TRANSIENT_STATIC_POLICY_ID
    )
    assert contract["dynamic_policy"][
        "descriptor_transient_first_order_policy"
    ] == DESCRIPTOR_TRANSIENT_FIRST_ORDER_POLICY_ID
    assert contract["dynamic_policy"][
        "descriptor_transient_constrained_policy"
    ] == DESCRIPTOR_TRANSIENT_CONSTRAINED_POLICY_ID
    assert int(
        contract["dynamic_policy"][
            "descriptor_transient_coordinate_shear_limit"
        ]
    ) == int(DESCRIPTOR_COORDINATE_SHEAR_LIMIT)
    assert contract["dynamic_policy"][
        "descriptor_transient_effective_factorization"
    ] == "PRECERTIFIED_SPD_MATRIX_CLASS_NO_CALLER_GENERAL_FALLBACK"
    assert contract["geometric_stiffness_policy"] == {
        "bubble_linearization_policy": REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID,
        "bubble_reduction": "Gb_TRANSPOSE_KG_FULL_Gb_SCHUR_DERIVATIVE",
        "component_frame": "NUMBERED_LOCAL_SYMMETRIC_TENSORS_AT_SEVEN_ORDERED_STIFFNESS_STATIONS",
        "director_field": "[u+z*theta_2,v-z*theta_1,w]",
        "excluded_terms": "TRANSVERSE_SHEAR_NORMAL_STRESS_AND_FINITE_PRESTRESS_RECONDENSATION",
        "generalized_section_second_moment": "EXPLICIT_H_REQUIRED_FOR_NONZERO_N_OR_M",
        "homogeneous_elastic_second_moment_default": "H=N*h^2/12_ONLY_WITH_FROZEN_PROFILE",
        "homogeneous_elastic_stress_profile": HOMOGENEOUS_ELASTIC_STRESS_PROFILE_ID,
        "integration": "DUNAVANT_DEGREE_5_SEVEN_POINT",
        "numerical_fields": "PL_AND_DRILL_EXCLUDED",
        "nonzero_state_authority": "EXPLICIT_REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_REQUIRED",
        "policy_id": GEOMETRIC_STIFFNESS_POLICY_ID,
        "resultant_inputs": "COMPRESSION_POSITIVE_N_M_H",
        "resultant_second_moment": "EXPLICIT_H_OR_FROZEN_HOMOGENEOUS_PROFILE_REQUIRED_FOR_EVERY_NONZERO_N_OR_M",
        "schur_linearization": "DERIVATIVE_AT_REFERENCE_MATERIAL_TANGENT",
    }


def test_quadrature_decimal_authority_integrates_reference_area() -> None:
    contract = _contract()
    rows = contract["quadrature"]["stiffness"]["points_r_s_weight"]
    total = sum(Decimal(row[2]) for row in rows)
    assert abs(total - Decimal("0.5")) <= Decimal("2e-15")
    for r_text, s_text, weight_text in rows:
        r = Decimal(r_text)
        s = Decimal(s_text)
        weight = Decimal(weight_text)
        assert r >= 0 and s >= 0 and r + s <= Decimal(1) + Decimal("1e-15")
        assert weight > 0
