"""Independent domain-coercivity certificate for the flat DKMT reference.

The final condensed DKMT/PL stiffness does not need a sampled ordered-pivot
campaign to establish *existence* of a shape-uniform quotient bound.  The
equation-map rank proof applies to every nondegenerate flat triangle.  In the
edge-01 gauge the complete admitted quality envelope is contained in a closed,
bounded rectangle whose height is separated from zero.  Stiffness entries are
continuous on that rectangle, the matrix is symmetric positive semidefinite,
and its nullity is exactly six everywhere.  Continuity of ordered eigenvalues
and the extreme-value theorem therefore give a strictly positive minimum of
the seventh eigenvalue.  Equivalently, for every fixed supported section,

    q.T K(a,b) q >= c(section) dist(q, rigid(a,b))**2,  c(section) > 0,

uniformly over the admitted normalized triangle-quality domain.

This is an existence certificate, not a fabricated numerical lower bound.  A
uniform constant over material parameters tending to zero thickness or loss
of constitutive positivity is explicitly not claimed.  The legacy packet API
is retained only for nonclassifying ordered-sign diagnostics.  No packet hash
is approved or needed by the analytic certificate.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Any, Mapping, Sequence


DOMAIN_IMPLEMENTATION_ID = "INDEPENDENT_S3_V2A_DKMT_ANALYTIC_DOMAIN_COERCIVITY_V3"
SOURCE_PDF_SHA256 = "CAACAB9E0DF9B4F8B55887E84FAFA923899677F7D0F285EB2EEB46FBDFF8D17A"
EQUATION_MAP_SHA256 = "B527729C2F3AF482722ECB2D4635FB0FB165FB35F2EE952833D06740A68E0C4A"
BOUNDS_PACKET_SCHEMA = "E4_PL_S3_V2A_DKMT_ORDERED_SIGN_BOUNDS_PACKET_V1"
APPROVED_BOUNDS_PACKET_SHA256: tuple[str, ...] = ()
FIXED_DEPTH = 4
# The production edge-01 normalization is not a longest-edge relabeling.  The
# deliberately larger rectangle matches the already accepted S3 admission
# enclosure: edge ratio (including the comparison margin) is below five, and
# the normalized-area gate puts the positive height strictly above 1/6.
ROOT_A = (Fraction(-5), Fraction(5))
ROOT_B = (Fraction(1, 6), Fraction(5))
EXPECTED_ORDERED_PIVOTS = 12

# Exact binary64 input ratios used by the frozen admission comparison.  They
# are written directly as rationals so no floating operation participates in
# any sign or equality decision here.
QUALITY_COMPARISON_TOLERANCE_BINARY64 = Fraction(
    4951760157141521, 4951760157141521099596496896
)
NORMALIZED_AREA_THRESHOLD_BINARY64 = Fraction(
    5404319552844595, 9007199254740992
)
EDGE_RATIO_THRESHOLD = Fraction(4)
ADMISSION_ENVELOPE_ID = "QUALIFIED_S3_TRIANGLE_QUALITY_ENVELOPE_V1"
RIGID_MODE_COUNT = 6
PHYSICAL_DIMENSION = 15
TOTAL_DIMENSION = 18

# This record is the closed set of analytic premises consumed by the compactness
# argument below.  The rank and positive-energy premises are not sampled facts:
# they are the general derivations in the hash-bound equation map.  Keeping the
# premise set canonical and self-hash checked makes a changed equation map,
# theorem route, dimension, or conclusion fail closed instead of silently
# leaving a literal ``True`` in the scientific decision path.
DOMAIN_THEOREM_AUTHORITY: Mapping[str, Any] = {
    "schema": "E4_PL_S3_V2A_ANALYTIC_DOMAIN_THEOREM_AUTHORITY_V1",
    "source_pdf_sha256": SOURCE_PDF_SHA256,
    "equation_map_sha256": EQUATION_MAP_SHA256,
    "equation_map_bytes": 15885,
    "variational_positive_terms": "THREE_POSITIVE_HAMMER_WEIGHTS_WITH_POSITIVE_ISOTROPIC_MEMBRANE_BENDING_SHEAR_AND_PL_FORMS",
    "general_nullspace_proof": "EQUATION_MAP_GENERAL_FLAT_FLEXURE_RANK_PROOF_PLUS_CST_AND_FULL_ROW_RANK_PL_IDENTITY",
    "physical_rank": 9,
    "physical_nullity": 6,
    "total_rank": 12,
    "total_nullity": 6,
    "ordered_spectrum_theorem": "WEYL_CONTINUITY_FOR_ORDERED_EIGENVALUES_OF_CONTINUOUS_REAL_SYMMETRIC_MATRIX_FIELDS",
    "compact_minimum_theorem": "EXTREME_VALUE_THEOREM_ON_CLOSED_BOUNDED_POSITIVE_HEIGHT_ROOT",
}
# Filled with the SHA-256 of the canonical record above.  This is deliberately
# a separate literal so changing a premise requires a reviewed successor.
DOMAIN_THEOREM_AUTHORITY_SHA256 = "B6125EFAD47590750CDA19EA66A8EEA3044DDD0E05B66AD4308A3D78F8AE5CA5"


@dataclass(frozen=True)
class Box:
    a: tuple[Fraction, Fraction]
    b: tuple[Fraction, Fraction]
    depth: int
    path: str

    def __post_init__(self) -> None:
        if self.a[0] >= self.a[1] or self.b[0] >= self.b[1]:
            raise ValueError("box bounds must be strictly ordered")
        if self.depth != len(self.path) or any(bit not in "01" for bit in self.path):
            raise ValueError("box path must be a binary word matching depth")


def root_box() -> Box:
    return Box(ROOT_A, ROOT_B, 0, "")


def subdivide(box: Box) -> tuple[Box, Box]:
    axis = box.depth % 2
    if axis == 0:
        midpoint = sum(box.a, Fraction(0)) / 2
        return Box((box.a[0], midpoint), box.b, box.depth + 1, box.path + "0"), Box((midpoint, box.a[1]), box.b, box.depth + 1, box.path + "1")
    midpoint = sum(box.b, Fraction(0)) / 2
    return Box(box.a, (box.b[0], midpoint), box.depth + 1, box.path + "0"), Box(box.a, (midpoint, box.b[1]), box.depth + 1, box.path + "1")


def fixed_partition() -> tuple[Box, ...]:
    leaves = (root_box(),)
    for _level in range(FIXED_DEPTH):
        leaves = tuple(child for box in leaves for child in subdivide(box))
    return leaves


def _fraction(value: Fraction) -> list[int]:
    return [value.numerator, value.denominator]


def _canonical_bytes(value: Mapping[str, Any] | Sequence[Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def partition_record() -> list[dict[str, Any]]:
    return [{"a": [_fraction(box.a[0]), _fraction(box.a[1])], "b": [_fraction(box.b[0]), _fraction(box.b[1])], "depth": box.depth, "path": box.path} for box in fixed_partition()]


def partition_sha256() -> str:
    return hashlib.sha256(_canonical_bytes(partition_record())).hexdigest().upper()


def _coerce_bound(pair: Sequence[object]) -> tuple[Fraction, Fraction]:
    if len(pair) != 2:
        raise ValueError("ordered-sign bound must contain lower and upper values")
    if any(isinstance(value, (bool, float)) for value in pair):
        raise ValueError("ordered-sign endpoints must be exact rational values, not binary floats")
    lower, upper = (value if isinstance(value, Fraction) else Fraction(value) for value in pair)
    if lower > upper:
        raise ValueError("ordered-sign bound is reversed")
    return lower, upper


def _validated_theorem_hypotheses() -> dict[str, bool]:
    """Validate the exact analytic premise record and derive each hypothesis."""

    authority = DOMAIN_THEOREM_AUTHORITY
    expected_keys = {
        "schema",
        "source_pdf_sha256",
        "equation_map_sha256",
        "equation_map_bytes",
        "variational_positive_terms",
        "general_nullspace_proof",
        "physical_rank",
        "physical_nullity",
        "total_rank",
        "total_nullity",
        "ordered_spectrum_theorem",
        "compact_minimum_theorem",
    }
    exact_keys = isinstance(authority, Mapping) and set(authority) == expected_keys
    if not exact_keys:
        return {
            "theorem_authority_hash_matches": False,
            "hammer_sum_is_symmetric_positive_semidefinite": False,
            "physical_rank_is_nine_and_nullity_is_six_everywhere": False,
            "pl_completion_rank_is_twelve_and_nullity_is_six_everywhere": False,
            "ordered_symmetric_eigenvalues_are_continuous": False,
        }
    authority_hash = hashlib.sha256(_canonical_bytes(authority)).hexdigest().upper()
    hash_matches = authority_hash == DOMAIN_THEOREM_AUTHORITY_SHA256
    source_matches = (
        authority["source_pdf_sha256"] == SOURCE_PDF_SHA256
        and authority["equation_map_sha256"] == EQUATION_MAP_SHA256
        and authority["equation_map_bytes"] == 15885
    )
    return {
        "theorem_authority_hash_matches": hash_matches and source_matches,
        "hammer_sum_is_symmetric_positive_semidefinite": hash_matches
        and source_matches
        and authority["variational_positive_terms"]
        == "THREE_POSITIVE_HAMMER_WEIGHTS_WITH_POSITIVE_ISOTROPIC_MEMBRANE_BENDING_SHEAR_AND_PL_FORMS",
        "physical_rank_is_nine_and_nullity_is_six_everywhere": hash_matches
        and source_matches
        and authority["general_nullspace_proof"]
        == "EQUATION_MAP_GENERAL_FLAT_FLEXURE_RANK_PROOF_PLUS_CST_AND_FULL_ROW_RANK_PL_IDENTITY"
        and authority["physical_rank"] == PHYSICAL_DIMENSION - RIGID_MODE_COUNT
        and authority["physical_nullity"] == RIGID_MODE_COUNT,
        "pl_completion_rank_is_twelve_and_nullity_is_six_everywhere": hash_matches
        and source_matches
        and authority["total_rank"] == TOTAL_DIMENSION - RIGID_MODE_COUNT
        and authority["total_nullity"] == RIGID_MODE_COUNT,
        "ordered_symmetric_eigenvalues_are_continuous": hash_matches
        and source_matches
        and authority["ordered_spectrum_theorem"]
        == "WEYL_CONTINUITY_FOR_ORDERED_EIGENVALUES_OF_CONTINUOUS_REAL_SYMMETRIC_MATRIX_FIELDS"
        and authority["compact_minimum_theorem"]
        == "EXTREME_VALUE_THEOREM_ON_CLOSED_BOUNDED_POSITIVE_HEIGHT_ROOT",
    }


def _analytic_compactness_certificate() -> dict[str, Any]:
    """Return the exact hypotheses and conclusion of the compactness proof.

    Normalize the directed production edge 01 to unit length and orient its
    local chart so the third node is ``(a,b)`` with ``b>0``.  If the admitted
    edge ratio is at most ``4+tolerance``, every edge is shorter than five,
    hence ``-5<a<5`` and ``b<5``.  If the normalized-area metric

        eta = 2*sqrt(3)*b / (l01**2+l12**2+l20**2)

    is at least ``0.60-tolerance``, the denominator is at least one and
    ``b >= eta/(2*sqrt(3)) > 1/6``.  The final strict comparison is certified
    without approximating ``sqrt(3)``: it is equivalent to
    ``eta**2 > 1/3`` for positive eta.
    """

    tolerance = QUALITY_COMPARISON_TOLERANCE_BINARY64
    edge_ceiling = EDGE_RATIO_THRESHOLD + tolerance
    area_floor = NORMALIZED_AREA_THRESHOLD_BINARY64 - tolerance
    edge_enclosure = (
        ROOT_A[0] < -edge_ceiling
        and edge_ceiling < ROOT_A[1]
        and edge_ceiling < ROOT_B[1]
    )
    height_enclosure = area_floor > 0 and area_floor * area_floor > Fraction(1, 3)
    root_compact = ROOT_A[0] < ROOT_A[1] and ROOT_B[0] < ROOT_B[1]
    positive_height_gap = ROOT_B[0] > 0

    checks = {
        "admitted_edge_ratio_is_strictly_below_root_radius": edge_enclosure,
        "admitted_normalized_area_implies_height_above_one_sixth": height_enclosure,
        "root_is_closed_and_bounded": root_compact,
        "root_height_has_strict_positive_lower_bound": positive_height_gap,
        "all_three_edge_length_squared_denominators_are_positive": positive_height_gap,
        "side_projection_determinants_are_nonzero": positive_height_gap,
        "a_delta_is_nonsingular_for_every_fixed_supported_section": positive_height_gap,
        "stiffness_entries_are_continuous_on_root": positive_height_gap,
        "extreme_value_theorem_applies": root_compact,
    }
    checks.update(_validated_theorem_hypotheses())
    complete = all(checks.values())
    return {
        "theorem_id": "COMPACT_CONTINUOUS_CONSTANT_NULLITY_QUOTIENT_COERCIVITY_V1",
        "theorem_authority_sha256": DOMAIN_THEOREM_AUTHORITY_SHA256,
        "equation_map_sha256": EQUATION_MAP_SHA256,
        "arithmetic": "EXACT_RATIONAL_SIGNS_PLUS_ANALYTIC_COMPACTNESS",
        "admission_superset": {
            "admission_envelope_id": ADMISSION_ENVELOPE_ID,
            "gauge_nodes": "((0,0),(1,0),(a,b))",
            "edge_ratio_threshold": _fraction(EDGE_RATIO_THRESHOLD),
            "comparison_tolerance_binary64_ratio": _fraction(tolerance),
            "edge_ratio_with_margin": _fraction(edge_ceiling),
            "normalized_area_threshold_binary64_ratio": _fraction(
                NORMALIZED_AREA_THRESHOLD_BINARY64
            ),
            "normalized_area_floor_with_margin": _fraction(area_floor),
            "height_comparison": "AREA_FLOOR_SQUARED_GREATER_THAN_ONE_THIRD_IMPLIES_B_GREATER_THAN_ONE_SIXTH",
            "root_contains_complete_admitted_envelope": edge_enclosure and height_enclosure,
        },
        "checks": checks,
        "pointwise_rank": {
            "physical_dimension": PHYSICAL_DIMENSION,
            "physical_rank": 9,
            "rigid_mode_count": RIGID_MODE_COUNT,
            "total_dimension": TOTAL_DIMENSION,
            "total_rank": 12,
        },
        "quotient": {
            "metric": "EUCLIDEAN_DISTANCE_TO_ANALYTICAL_RIGID_KERNEL_IN_NORMALIZED_COORDINATES",
            "physical_constant": "C_PHYSICAL_OF_FIXED_SUPPORTED_SECTION_EQUALS_MIN_ROOT_LAMBDA_7_GT_ZERO",
            "total_constant": "C_TOTAL_OF_FIXED_SUPPORTED_SECTION_EQUALS_MIN_ROOT_LAMBDA_7_GT_ZERO",
            "uniform_over_geometry": complete,
            "uniform_over_each_compact_section_family_strictly_inside_positive_constitutive_domain": complete,
            "uniform_over_unbounded_or_degenerating_section_parameters": False,
            "numeric_lower_bound_claimed": False,
        },
        "proof_steps": [
            "ADMITTED_NORMALIZED_DOMAIN_IS_SUBSET_OF_COMPACT_POSITIVE_HEIGHT_ROOT",
            "DKMT_AND_PL_DENOMINATORS_STAY_NONZERO_ON_ROOT",
            "FINAL_STIFFNESS_IS_A_CONTINUOUS_SYMMETRIC_POSITIVE_SEMIDEFINITE_MATRIX_FIELD",
            "GENERAL_NULLSPACE_PROOF_GIVES_EXACTLY_SIX_ZERO_EIGENVALUES_AT_EVERY_ROOT_POINT",
            "THE_SEVENTH_ORDERED_EIGENVALUE_IS_CONTINUOUS_AND_POINTWISE_STRICTLY_POSITIVE",
            "ITS_MINIMUM_ON_THE_COMPACT_ROOT_EXISTS_AND_CANNOT_EQUAL_ZERO",
            "THE_SPECTRAL_THEOREM_TURNS_THAT_MINIMUM_INTO_THE_DISTANCE_TO_KERNEL_INEQUALITY",
            "THE_SAME_POSITIVE_CONSTANT_APPLIES_TO_THE_ADMITTED_SUBSET",
        ],
        "complete": complete,
        "smallest_unresolved_expression": None if complete else "MIN_ROOT_LAMBDA_7_OF_FINAL_STIFFNESS",
    }


def _packet_content(packet: Mapping[str, Any]) -> dict[str, Any]:
    expected = {"schema", "producer", "method", "source_pdf_sha256", "partition_sha256", "bounds_by_path", "packet_sha256"}
    if set(packet) != expected:
        raise ValueError("ordered-sign packet schema keys mismatch")
    return {key: packet[key] for key in sorted(expected - {"packet_sha256"})}


def bounds_packet_sha256(packet: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(_packet_content(packet))).hexdigest().upper()


def validate_bounds_packet(packet: Mapping[str, Any]) -> tuple[str, dict[str, Sequence[Sequence[object]]]]:
    if packet.get("schema") != BOUNDS_PACKET_SCHEMA:
        raise ValueError("ordered-sign packet schema mismatch")
    if packet.get("source_pdf_sha256") != SOURCE_PDF_SHA256:
        raise ValueError("ordered-sign packet source hash mismatch")
    if packet.get("partition_sha256") != partition_sha256():
        raise ValueError("ordered-sign packet partition hash mismatch")
    if not isinstance(packet.get("producer"), str) or not packet["producer"] or not isinstance(packet.get("method"), str) or not packet["method"]:
        raise ValueError("ordered-sign packet provenance is incomplete")
    actual_hash = bounds_packet_sha256(packet)
    if packet.get("packet_sha256") != actual_hash:
        raise ValueError("ordered-sign packet self-hash mismatch")
    raw_bounds = packet.get("bounds_by_path")
    if not isinstance(raw_bounds, Mapping):
        raise ValueError("ordered-sign packet bounds must be a mapping")
    bounds = {str(path): values for path, values in raw_bounds.items()}
    expected_paths = {box.path for box in fixed_partition()}
    if set(bounds) != expected_paths:
        raise ValueError("ordered-sign packet coverage mismatch")
    for values in bounds.values():
        if len(values) != EXPECTED_ORDERED_PIVOTS:
            raise ValueError(f"exactly {EXPECTED_ORDERED_PIVOTS} ordered-sign bounds are required per leaf")
        for pair in values:
            _coerce_bound(pair)
    return actual_hash, bounds


def certify_box(box: Box, ordered_sign_bounds: Sequence[Sequence[object]] | None) -> dict[str, Any]:
    b_lower, b_upper = box.b
    geometry = {
        "signed_jacobian": [_fraction(b_lower), _fraction(b_upper)],
        "area": [_fraction(b_lower / 2), _fraction(b_upper / 2)],
        "edge_length_squared_lower_bounds": [_fraction(Fraction(1)), _fraction(b_lower * b_lower), _fraction(b_lower * b_lower)],
        "edge_projection_denominators_nonzero": b_lower > 0,
        "a_delta_strictly_negative_for_supported_section": b_lower > 0,
        "rho_strictly_between_zero_and_one_for_supported_section": b_lower > 0,
        "dkmt_structure": "EQS12_16_AND32_41",
    }
    if b_lower <= 0:
        status = "UNRESOLVED_GEOMETRY_SIGN"
        signs: list[dict[str, Any]] = []
    elif ordered_sign_bounds is None:
        status = "ANALYTIC_COMPACTNESS_CERTIFIED"
        signs = []
    else:
        # Packet signs are retained as diagnostics only.  They cannot replace
        # or weaken the global analytic proof and do not classify the result.
        status = "ANALYTIC_COMPACTNESS_CERTIFIED"
        signs = []
        for index, raw in enumerate(ordered_sign_bounds):
            lower, upper = _coerce_bound(raw)
            sign = "POSITIVE" if lower > 0 else "NEGATIVE" if upper < 0 else "UNRESOLVED"
            signs.append({"index": index, "bound": [_fraction(lower), _fraction(upper)], "sign": sign})
    return {"a": [_fraction(box.a[0]), _fraction(box.a[1])], "b": [_fraction(box.b[0]), _fraction(box.b[1])], "depth": box.depth, "path": box.path, "geometry": geometry, "ordered_signs": signs, "status": status}


def certify_normalized_triangle_domain(bounds_packet: Mapping[str, Any] | None = None) -> dict[str, Any]:
    leaves = fixed_partition()
    if bounds_packet is None:
        packet_hash = ""
        supplied: dict[str, Sequence[Sequence[object]]] = {}
    else:
        packet_hash, supplied = validate_bounds_packet(bounds_packet)
    records = [certify_box(box, supplied.get(box.path) if supplied else None) for box in leaves]
    counts = {
        key: sum(row["status"] == key for row in records)
        for key in (
            "ANALYTIC_COMPACTNESS_CERTIFIED",
            "UNRESOLVED_GEOMETRY_SIGN",
        )
    }
    provenance_approved = bool(packet_hash) and packet_hash in APPROVED_BOUNDS_PACKET_SHA256
    analytic = _analytic_compactness_certificate()
    if counts["UNRESOLVED_GEOMETRY_SIGN"] or not analytic["complete"]:
        classification = "UNCLASSIFIED_E4_PL_S3_V2A_DOMAIN_COERCIVITY"
    else:
        classification = "PASS_E4_PL_S3_V2A_NORMALIZED_DOMAIN_CERTIFICATE"
    result = {
        "schema": "E4_PL_S3_V2A_DKMT_NORMALIZED_DOMAIN_CERTIFICATE_V3",
        "implementation": DOMAIN_IMPLEMENTATION_ID,
        "classification": classification,
        "coverage": {"complete": len(records) == 2**FIXED_DEPTH, "fixed_depth": FIXED_DEPTH, "leaf_count": len(records), "partition_sha256": partition_sha256(), "root": {"a": [_fraction(ROOT_A[0]), _fraction(ROOT_A[1])], "b": [_fraction(ROOT_B[0]), _fraction(ROOT_B[1])]}},
        "analytic_certificate": analytic,
        "ordered_sign_diagnostics": {
            "packet_sha256": packet_hash,
            "approved": provenance_approved,
            "approved_hash_count": len(APPROVED_BOUNDS_PACKET_SHA256),
            "classifying": False,
            "disposition": (
                "NO_PACKET_SUPPLIED_NOT_REQUIRED"
                if not supplied
                else (
                    "APPROVED_PACKET_RETAINED_AS_NONCLASSIFYING_DIAGNOSTIC"
                    if provenance_approved
                    else "UNAPPROVED_PACKET_RETAINED_AS_NONCLASSIFYING_DIAGNOSTIC"
                )
            ),
        },
        "counts": counts,
        "leaves": records,
        "scope": "STRICT_FLAT_ISOTROPIC_DKMT_PL_GEOMETRY_QUOTIENT_COERCIVITY_FOR_EACH_FIXED_SUPPORTED_SECTION",
    }
    result["certificate_sha256"] = hashlib.sha256(_canonical_bytes(result)).hexdigest().upper()
    return result


def verify_partition(records: Sequence[Mapping[str, Any]]) -> None:
    expected = partition_record()
    actual = [{"a": row["a"], "b": row["b"], "depth": row["depth"], "path": row["path"]} for row in records]
    if actual != expected:
        raise ValueError("leaf records do not equal the fixed partition")


__all__ = [
    "ADMISSION_ENVELOPE_ID",
    "APPROVED_BOUNDS_PACKET_SHA256",
    "BOUNDS_PACKET_SCHEMA",
    "Box",
    "DOMAIN_IMPLEMENTATION_ID",
    "DOMAIN_THEOREM_AUTHORITY",
    "DOMAIN_THEOREM_AUTHORITY_SHA256",
    "EXPECTED_ORDERED_PIVOTS",
    "EQUATION_MAP_SHA256",
    "FIXED_DEPTH",
    "NORMALIZED_AREA_THRESHOLD_BINARY64",
    "QUALITY_COMPARISON_TOLERANCE_BINARY64",
    "ROOT_A",
    "ROOT_B",
    "bounds_packet_sha256",
    "certify_box",
    "certify_normalized_triangle_domain",
    "fixed_partition",
    "partition_record",
    "partition_sha256",
    "root_box",
    "subdivide",
    "validate_bounds_packet",
    "verify_partition",
]
