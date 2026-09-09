"""Independent Map-B checker for the GE-B3 P4 curved-reference proof.

The reconstruction deliberately uses scalar first-order jets.  It never
imports ANYsolver, the production reference module, or beam mechanics.
Malformed/hash/process evidence raises before an output is created; only
well-formed scientific outcomes are serialized.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np


CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_CURVED_Q2_MACRO_V1"
PROOF_SCHEMA = "anysolver.ge-beam3-curved-p4-reference-proof-v2"
CHECK_SCHEMA = "anysolver.ge-beam3-curved-p4-reference-check-v2"
CHECKER_ID = "P4_INDEPENDENT_REFERENCE_RECONSTRUCTION_V2"
PRODUCER_ID = "P4_PRODUCTION_REFERENCE_MODULE_PRODUCER_V2"
BLOCKED = "BLOCKED_GE_BEAM3_P4_REFERENCE_PROCESS_OR_EVIDENCE"
NO_GO_REGULARITY = "NO_GO_GE_BEAM3_P4_REFERENCE_REGULARITY"
NO_GO_FRAME = "NO_GO_GE_BEAM3_P4_REFERENCE_FRAME_IDENTITY"
NO_GO_REVERSAL = "NO_GO_GE_BEAM3_P4_REFERENCE_REVERSAL_OR_OBJECTIVITY"
PASS = "PROVISIONAL_GO_GE_BEAM3_P4_PRIVATE_CURVED_REFERENCE_CORE"
RESTRICTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"

REGULARITY_TOLERANCE = max(64.0 * np.finfo(np.float64).eps, 1.0e-14)
INVARIANT_TOLERANCE = 1.0e-11
FRAME_TOLERANCE = 1.0e-12
BRANCH_LIMIT = 0.9 * math.pi
REVERSAL = np.diag((-1.0, 1.0, -1.0))
COMPONENT_REVERSAL = -REVERSAL
FROZEN_POSITIVE_FIXTURE_MANIFEST_SHA256 = (
    "1493EF8C32B7206C65A18F6CABFEAA5F15104ED0AB519BE852F382C11E6DF2A5"
)
POSITIVE_FIXTURE_IDS = (
    "STRAIGHT_LIMIT", "PLANAR_SHALLOW", "PLANAR_DEEP",
    "PLANAR_ASYMMETRIC", "INITIALLY_TWISTED", "EMBEDDED_SPATIAL_PLANE",
)
REGISTERED_OBLIGATION_IDS = (
    "P2_BASIS_AND_DERIVATIVE_IDENTITY", "P2_NODAL_INTERPOLATION",
    "ANALYTIC_INTERVAL_REGULARITY", "STRAIGHT_REFERENCE_LIMIT",
    "PLANAR_SHALLOW_ARCH", "PLANAR_DEEP_ARCH", "ASYMMETRIC_PLANAR_CURVE",
    "TRANSFORMED_AND_SCALED_COPIES", "INITIALLY_TWISTED_CURVE",
    "MULTIELEMENT_SPATIAL_CHAIN", "CURVED_STIFFENER_SEGMENT",
    "AUTHORITATIVE_ANISOTROPIC_ROLL", "RIGID_REFERENCE_OBJECTIVITY",
    "CONNECTIVITY_REVERSAL", "FRAME_CONTINUITY",
    "ZERO_INTRINSIC_REFERENCE_STRAINS", "COINCIDENT_NODE_REJECTION",
    "ZERO_TANGENT_REJECTION", "NEAR_FOLD_REJECTION",
    "HALF_FRAME_BRANCH_CUTOFF_REJECTION", "TRIAD_TANGENT_MISMATCH_REJECTION",
    "IMPROPER_TRIAD_REJECTION", "RING_SEAM_MISMATCH_REJECTION",
    "CANONICAL_SERIALIZATION_AND_MUTATION", "STRAIGHT_CORE_BLOB_FREEZE",
    "PRODUCTION_BOUNDARY",
)
STATION_SCHEDULE = (
    (-1.0, "VALUE"), (-0.75, "VALUE"), (-0.25, "VALUE"),
    (0.0, "LEFT"), (0.0, "RIGHT"), (0.25, "VALUE"),
    (0.75, "VALUE"), (1.0, "VALUE"),
)
REGISTERED_MUTATION_COVERAGE = {
    "AUTHORITY_ARTIFACT_HASH": 18,
    "HALF_ORDERING": 1,
    "NODE": 3,
    "P2_DERIVATIVE_COEFFICIENT": 15,
    "P2_SHAPE_COEFFICIENT": 15,
    "PRODUCTION_SOURCE_HASH": 1,
    "REVERSAL_MAP": 1,
    "ROLL_SIGN": 2,
    "TANGENT_SIGN": 1,
    "TRIAD": 3,
}
REGISTERED_MUTATION_COUNT = 60
REGISTERED_MUTATION_ORDER_SHA256 = (
    "3E5C18031BA051D829E29D905200B82A97B9A49ADE0857B343DC84234674C918"
)


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, allow_nan=False, ensure_ascii=True,
                       separators=(",", ":"), sort_keys=True) + "\n").encode("ascii")


def _compact_bytes(value: Any) -> bytes:
    return json.dumps(value, allow_nan=False, ensure_ascii=True,
                      separators=(",", ":"), sort_keys=True).encode("ascii")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


OBLIGATION_ORDER_SHA256 = _sha256(_canonical_bytes(list(REGISTERED_OBLIGATION_IDS)))
PREREGISTRATION_COMMIT = "5cf0fc884685b454ea645c2052c7cba60c66cbbb"
INITIAL_CORE_COMMIT = "214d6de76795bb7d656dc377166bd05cc35c6a3f"
CORRECTED_CORE_COMMIT = "d59ed224cabae23fac4ef68a74bc53ef5602b3db"
IMPLEMENTATION_REVIEW_COMMIT = "8fcf827b6e5364f0e1bc8221a3f74602e3f39261"
COMMIT_AUTHORITIES = (
    {"commit": PREREGISTRATION_COMMIT, "parent": "8ac156cbb7632f2442f904e3ab73d6a7eb867670",
     "role": "PREREGISTRATION", "subject": "docs: preregister GE Beam3 curved P4 reference core",
     "tree": "d2a9ccd5db3e4fee25fb1be07a49fceceb887bd5"},
    {"commit": INITIAL_CORE_COMMIT, "parent": PREREGISTRATION_COMMIT,
     "role": "REFERENCE_CORE_INITIAL", "subject": "feat: add private GE Beam3 curved P4 reference core",
     "tree": "4cb6fc861edf721fcb246fb521a64b24aa58eeab"},
    {"commit": CORRECTED_CORE_COMMIT, "parent": INITIAL_CORE_COMMIT,
     "role": "REFERENCE_CORE_CORRECTION", "subject": "fix: align GE Beam3 curved frame admission",
     "tree": "2235c5f868384f0122ec5eda766cdf01c0923a1f"},
    {"commit": IMPLEMENTATION_REVIEW_COMMIT, "parent": CORRECTED_CORE_COMMIT,
     "role": "IMPLEMENTATION_REVIEW", "subject": "docs: accept corrected GE Beam3 curved P4 reference core",
     "tree": "61001446006971d32ac3294800f3760ba43df948"},
)
AUTHORITY_INPUT_PATHS = (
    "docs/agent_plans/GE_BEAM3_CURVED_P4_REFERENCE_CORE_PLAN.md",
    "docs/reference_cases/ge_beam3_curved_p4_baseline.json",
    "docs/reference_cases/ge_beam3_curved_p4_cases.json",
    "docs/reference_cases/ge_beam3_curved_p4_contract.json",
    "docs/reference_cases/ge_beam3_curved_p4_equation_map_a.json",
    "docs/reference_cases/ge_beam3_curved_p4_equation_map_b.json",
    "docs/reference_cases/ge_beam3_curved_p4_implementation_review.json",
    "docs/reference_cases/ge_beam3_curved_p4_plan_review.json",
    "docs/reference_cases/ge_beam3_curved_p4_reference_checker.py",
    "docs/reference_cases/ge_beam3_curved_p4_reference_producer.py",
    "docs/reference_cases/ge_beam3_curved_p4_reference_runner.py",
    "docs/reference_cases/ge_beam3_curved_p4_reference_schema.json",
    "docs/reference_cases/ge_beam3_curved_p4_source_ledger.json",
    "src/anysolver/ge_beam3_curved_reference.py",
    "tests/test_ge_beam3_curved_p4_formal_runner.py",
    "tests/test_ge_beam3_curved_p4_implementation_review.py",
    "tests/test_ge_beam3_curved_p4_preregistration.py",
    "tests/test_ge_beam3_curved_p4_reference.py",
)
NEGATIVE_RECIPES = (
    ("COINCIDENT_NODE_REJECTION", "COINCIDENT_1_2", "COINCIDENT_END_AND_MIDDLE", "GeBeam3CurvedGeometryError"),
    ("ZERO_TANGENT_REJECTION", "FOLDED_ZERO_TANGENT", "FOLDED_ENDPOINT_COINCIDENCE", "GeBeam3CurvedGeometryError"),
    ("NEAR_FOLD_REJECTION", "NEAR_FOLD_SCALE_1E_NEG8", "NEAR_FOLD_SCALE_1E_NEG8", "GeBeam3CurvedGeometryError"),
    ("NEAR_FOLD_REJECTION", "NEAR_FOLD_SCALE_1", "NEAR_FOLD_SCALE_1", "GeBeam3CurvedGeometryError"),
    ("NEAR_FOLD_REJECTION", "NEAR_FOLD_SCALE_1E8", "NEAR_FOLD_SCALE_1E8", "GeBeam3CurvedGeometryError"),
    ("HALF_FRAME_BRANCH_CUTOFF_REJECTION", "TANGENT_TURN_0P91_PI", "HALF_TANGENT_TURN_0P91_PI", "GeBeam3CurvedFrameError"),
    ("HALF_FRAME_BRANCH_CUTOFF_REJECTION", "RESIDUAL_ROLL_PI", "HALF_RESIDUAL_ROLL_PI", "GeBeam3CurvedFrameError"),
    ("TRIAD_TANGENT_MISMATCH_REJECTION", "WRONG_FIRST_AXIS", "TRIAD_FIRST_AXIS_FROM_OTHER_NODE", "GeBeam3CurvedFrameError"),
    ("IMPROPER_TRIAD_REJECTION", "REFLECTED_TRIAD", "REFLECT_THIRD_AXIS", "GeBeam3CurvedFrameError"),
    ("IMPROPER_TRIAD_REJECTION", "NONORTHOGONAL_TRIAD", "PERTURB_SECOND_AXIS", "GeBeam3CurvedFrameError"),
    ("IMPROPER_TRIAD_REJECTION", "NONFINITE_TRIAD", "INSERT_NAN_IN_TRIAD", "GeBeam3CurvedReferenceError"),
)
PROTECTED_STRAIGHT_BLOBS = {
    "pyproject.toml": "16da1c1ca1be9f56de4c0c3505cdfabb8752bd99",
    "src/anysolver/__init__.py": "2aa4911f538b6cb08e66dbb4590d0d1545dd7560",
    "src/anysolver/elements.py": "4dfe4212b9ee9947969b087809e72b9973e88e07",
    "src/anysolver/ge_beam3_element.py": "70542da7fea26dcb2da5b5f9da5fc0b0b8d484ab",
    "src/anysolver/ge_beam3_mixed_element.py": "f49062b55b4bf749a1654100cf3a4ed6ffb61d37",
    "src/anysolver/ge_beam3_mixed_state.py": "74caa1814448245f907bd3efdb6c8a1cc1d2269d",
    "src/anysolver/ge_beam3_state.py": "ba8f65761197c62cb2b7ce74bf488e75f2c24818",
}
REFERENCE_BOUNDARY_PATHS = {
    "docs/agent_plans/GE_BEAM3_CURVED_P4_REFERENCE_CORE_PLAN.md",
    "docs/reference_cases/ge_beam3_curved_p4_baseline.json",
    "docs/reference_cases/ge_beam3_curved_p4_cases.json",
    "docs/reference_cases/ge_beam3_curved_p4_contract.json",
    "docs/reference_cases/ge_beam3_curved_p4_equation_map_a.json",
    "docs/reference_cases/ge_beam3_curved_p4_equation_map_b.json",
    "docs/reference_cases/ge_beam3_curved_p4_implementation_review.json",
    "docs/reference_cases/ge_beam3_curved_p4_plan_review.json",
    "docs/reference_cases/ge_beam3_curved_p4_reference_schema.json",
    "docs/reference_cases/ge_beam3_curved_p4_source_ledger.json",
    "src/anysolver/ge_beam3_curved_reference.py",
    "tests/test_ge_beam3_curved_p4_implementation_review.py",
    "tests/test_ge_beam3_curved_p4_preregistration.py",
    "tests/test_ge_beam3_curved_p4_reference.py",
}


class ProofError(ValueError):
    """Malformed, incomplete, or hash-invalid process evidence."""


class AdmissionError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class ScientificContradiction(AssertionError):
    terminal = BLOCKED


class RegularityContradiction(ScientificContradiction):
    terminal = NO_GO_REGULARITY


class FrameContradiction(ScientificContradiction):
    terminal = NO_GO_FRAME


class ReversalContradiction(ScientificContradiction):
    terminal = NO_GO_REVERSAL


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProofError(f"duplicate key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ProofError(f"nonfinite JSON value: {value}")


def _canonical_file_bytes(path: Path) -> bytes:
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in raw:
        raise ProofError(f"noncanonical carriage return in {path.name}")
    return raw


def _git_blob_sha1(path: Path) -> str:
    raw = _canonical_file_bytes(path)
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


def _strict_load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=_unique,
                           parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProofError("proof is not strict ASCII JSON") from exc
    if not isinstance(value, dict) or raw != _canonical_bytes(value):
        raise ProofError("proof is not sorted compact LF canonical JSON")
    return raw, value


def _write_exclusive(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(_canonical_bytes(value))


def _require_keys(value: Any, keys: Iterable[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ProofError(f"{label} exact keys differ")
    return value


def _require_hash(value: Any, label: str) -> str:
    if (not isinstance(value, str) or len(value) != 64 or value != value.upper()
            or any(character not in "0123456789ABCDEF" for character in value)):
        raise ProofError(f"{label} is not an uppercase SHA-256")
    return value


def _array(value: Any, shape: tuple[int, ...], label: str) -> np.ndarray:
    try:
        made = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ProofError(f"{label} is not a binary64 array") from exc
    if made.shape != shape or not np.all(np.isfinite(made)):
        raise ProofError(f"{label} shape/nonfinite mismatch")
    return made


def _scaled_inf_error(actual: Any, expected: Any) -> float:
    left, right = np.asarray(actual, dtype=np.float64), np.asarray(expected, dtype=np.float64)
    if left.shape != right.shape or not np.all(np.isfinite(left)) or not np.all(np.isfinite(right)):
        return math.inf
    return float(np.max(np.abs(left - right), initial=0.0)) / max(
        1.0, float(np.max(np.abs(right), initial=0.0)))


def _assert_close(actual: Any, expected: Any, tolerance: float,
                  contradiction: type[ScientificContradiction]) -> None:
    if _scaled_inf_error(actual, expected) > tolerance:
        raise contradiction()


def _hex(value: float) -> str:
    scalar = float(value)
    if not math.isfinite(scalar):
        raise ProofError("nonfinite canonical binary64")
    return (0.0 if scalar == 0.0 else scalar).hex().lower()


def _hex_array(value: np.ndarray) -> Any:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim == 0:
        return _hex(float(array))
    return [_hex_array(row) for row in array]


@dataclass(frozen=True)
class Jet:
    """Scalar value and first-order chain-rule derivative in xi."""
    value: float
    derivative: float = 0.0

    @staticmethod
    def make(value: float | Jet) -> Jet:
        return value if isinstance(value, Jet) else Jet(float(value))

    def __add__(self, other: float | Jet) -> Jet:
        rhs = Jet.make(other)
        return Jet(self.value + rhs.value, self.derivative + rhs.derivative)
    __radd__ = __add__
    def __neg__(self) -> Jet:
        return Jet(-self.value, -self.derivative)
    def __sub__(self, other: float | Jet) -> Jet:
        return self + (-Jet.make(other))
    def __rsub__(self, other: float | Jet) -> Jet:
        return Jet.make(other) - self
    def __mul__(self, other: float | Jet) -> Jet:
        rhs = Jet.make(other)
        return Jet(self.value * rhs.value,
                   self.derivative * rhs.value + self.value * rhs.derivative)
    __rmul__ = __mul__
    def reciprocal(self) -> Jet:
        if self.value == 0.0:
            raise AdmissionError("ZERO_REFERENCE_DERIVATIVE")
        return Jet(1.0 / self.value, -self.derivative / self.value**2)
    def __truediv__(self, other: float | Jet) -> Jet:
        return self * Jet.make(other).reciprocal()
    def __rtruediv__(self, other: float | Jet) -> Jet:
        return Jet.make(other) / self


def _j_sqrt(value: Jet) -> Jet:
    if value.value <= 0.0:
        raise AdmissionError("ZERO_REFERENCE_DERIVATIVE")
    root = math.sqrt(value.value)
    return Jet(root, .5 * value.derivative / root)


def _j_sin(value: Jet) -> Jet:
    return Jet(math.sin(value.value), math.cos(value.value) * value.derivative)


def _j_cos(value: Jet) -> Jet:
    return Jet(math.cos(value.value), -math.sin(value.value) * value.derivative)


def _jvec(values: Sequence[float], derivatives: Sequence[float] | None = None) -> list[Jet]:
    derivatives = (0.0,) * len(values) if derivatives is None else derivatives
    return [Jet(float(value), float(derivative)) for value, derivative in zip(values, derivatives)]


def _jdot(left: Sequence[Jet], right: Sequence[Jet]) -> Jet:
    return sum((a * b for a, b in zip(left, right)), Jet(0.0))


def _jcross(left: Sequence[Jet], right: Sequence[Jet]) -> list[Jet]:
    return [left[1]*right[2]-left[2]*right[1], left[2]*right[0]-left[0]*right[2],
            left[0]*right[1]-left[1]*right[0]]


def _jnorm(vector: Sequence[Jet]) -> Jet:
    return _j_sqrt(_jdot(vector, vector))


def _jscale(scalar: Jet, vector: Sequence[Jet]) -> list[Jet]:
    return [scalar * component for component in vector]


def _jskew(vector: Sequence[Jet]) -> list[list[Jet]]:
    zero, (x, y, z) = Jet(0.0), vector
    return [[zero, -z, y], [z, zero, -x], [-y, x, zero]]


def _jidentity() -> list[list[Jet]]:
    return [[Jet(float(i == j)) for j in range(3)] for i in range(3)]


def _jmat_constant(value: np.ndarray) -> list[list[Jet]]:
    return [[Jet(float(value[i, j])) for j in range(3)] for i in range(3)]


def _jmat_add(left: Sequence[Sequence[Jet]], right: Sequence[Sequence[Jet]]) -> list[list[Jet]]:
    return [[left[i][j] + right[i][j] for j in range(3)] for i in range(3)]


def _jmat_scale(scalar: Jet, matrix: Sequence[Sequence[Jet]]) -> list[list[Jet]]:
    return [[scalar * matrix[i][j] for j in range(3)] for i in range(3)]


def _jmatmul(left: Sequence[Sequence[Jet]], right: Sequence[Sequence[Jet]]) -> list[list[Jet]]:
    return [[sum((left[i][k] * right[k][j] for k in range(3)), Jet(0.0))
             for j in range(3)] for i in range(3)]


def _jvalues(matrix: Sequence[Sequence[Jet]]) -> np.ndarray:
    return np.asarray([[entry.value for entry in row] for row in matrix])


def _jderivatives(matrix: Sequence[Sequence[Jet]]) -> np.ndarray:
    return np.asarray([[entry.derivative for entry in row] for row in matrix])


def _skew(vector: np.ndarray) -> np.ndarray:
    x, y, z = np.asarray(vector, dtype=np.float64)
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def _proper_rotation(axis: np.ndarray, angle: float) -> np.ndarray:
    # Copy: callers may supply an authoritative triad-column view.  The checker
    # must never normalize or otherwise mutate the evidence it is validating.
    unit = np.array(axis, dtype=np.float64, copy=True)
    unit /= np.linalg.norm(unit)
    cross = _skew(unit)
    return np.eye(3) + math.sin(angle)*cross + (1.-math.cos(angle))*(cross @ cross)


def _jet_rotation(axis: Sequence[Jet], angle: Jet) -> list[list[Jet]]:
    cross = _jskew(axis)
    return _jmat_add(_jmat_add(_jidentity(), _jmat_scale(_j_sin(angle), cross)),
                     _jmat_scale(Jet(1.)-_j_cos(angle), _jmatmul(cross, cross)))


def _jet_shortest(left: np.ndarray, right: Sequence[Jet]) -> list[list[Jet]]:
    left_jet = _jvec(left)
    cosine = _jdot(left_jet, right)
    if cosine.value <= math.cos(BRANCH_LIMIT):
        raise AdmissionError("HALF_FRAME_TANGENT_BRANCH_EXCEEDED")
    cross = _jskew(_jcross(left_jet, right))
    return _jmat_add(_jmat_add(_jidentity(), cross),
                     _jmat_scale((Jet(1.)+cosine).reciprocal(), _jmatmul(cross, cross)))


def _triad(tangent: np.ndarray, hint: np.ndarray, roll: float = 0.0) -> np.ndarray:
    first = np.asarray(tangent, dtype=np.float64)
    first /= np.linalg.norm(first)
    second = np.asarray(hint, dtype=np.float64) - float(first @ hint)*first
    second /= np.linalg.norm(second)
    third = np.cross(first, second)
    second = math.cos(roll)*second + math.sin(roll)*third
    return np.column_stack((first, second, np.cross(first, second)))


def _fixture_manifest() -> list[dict[str, Any]]:
    definitions = (
        ("STRAIGHT_LIMIT", ((0,0,0),(.5,0,0),(1,0,0)), ((0,1,0),)*3, (0,0,0)),
        ("PLANAR_SHALLOW", ((-1,0,0),(0,.15,0),(1,0,0)), ((0,0,1),)*3, (0,0,0)),
        ("PLANAR_DEEP", ((-1,0,0),(0,.8,0),(1,0,0)), ((0,0,1),)*3, (0,0,0)),
        ("PLANAR_ASYMMETRIC", ((-1.2,-.1,0),(.15,.55,0),(1.1,.1,0)), ((0,0,1),)*3, (0,0,0)),
        ("INITIALLY_TWISTED", ((-1,0,0),(0,.35,0),(1,0,0)), ((0,0,1),)*3, (0,.22,.47)),
        ("EMBEDDED_SPATIAL_PLANE", ((-1.2,-.2,.4),(.1,.7,.9),(1.4,.3,-.1)), ((.2,-.6,1),)*3, (0,-.18,.31)),
    )
    rows: list[dict[str, Any]] = []
    for case_id, raw_coordinates, hints, rolls in definitions:
        coordinates = np.asarray(raw_coordinates, dtype=np.float64)
        triads = []
        for index, xi in enumerate((-1., 0., 1.)):
            triads.append(_triad(np.array((xi-.5, -2.*xi, xi+.5)) @ coordinates,
                                 np.asarray(hints[index]), rolls[index]))
        rows.append({"case_id": case_id, "coordinates": coordinates.tolist(),
                     "expected": "ACCEPT", "nodal_triads": np.asarray(triads).tolist()})
    return rows


@dataclass(frozen=True)
class Regularity:
    characteristic_length: float
    minimum_admissible_jacobian: float
    minimum_jacobian_squared: float
    minimizer_xi: float


class MapBReference:
    """Map-B curve/frame reconstructed with no production implementation."""
    def __init__(self, coordinates: Any, triads: Any):
        self.coordinates = _array(coordinates, (3,3), "coordinates")
        self.triads = _array(triads, (3,3,3), "nodal_triads")
        if len({tuple(row) for row in self.coordinates.tolist()}) != 3:
            raise AdmissionError("COINCIDENT_REFERENCE_NODE")
        self.affine_constant = .5*(self.coordinates[2]-self.coordinates[0])
        self.affine_linear = self.coordinates[0]-2.*self.coordinates[1]+self.coordinates[2]
        length = float(max(np.linalg.norm(self.coordinates[1]-self.coordinates[0]),
                           np.linalg.norm(self.coordinates[2]-self.coordinates[1]),
                           np.linalg.norm(self.coordinates[2]-self.coordinates[0])))
        if not length > 0.:
            raise AdmissionError("COINCIDENT_REFERENCE_NODE")
        denominator = float(self.affine_linear @ self.affine_linear)
        if denominator == 0.:
            candidates = (0.,)
        else:
            stationary = min(1., max(-1.,
                -float(self.affine_constant @ self.affine_linear)/denominator))
            candidates = (-1., stationary, 1.)
        squared = [float((self.affine_constant+x*self.affine_linear) @
                         (self.affine_constant+x*self.affine_linear)) for x in candidates]
        index = min(range(len(candidates)), key=squared.__getitem__)
        threshold = REGULARITY_TOLERANCE*length
        if squared[index] <= threshold**2:
            raise AdmissionError("ZERO_REFERENCE_DERIVATIVE" if squared[index] == 0.
                                 else "NEAR_FOLD_REFERENCE_DERIVATIVE")
        self.regularity = Regularity(length, threshold, squared[index], candidates[index])
        for index, xi in enumerate((-1., 0., 1.)):
            if not np.array_equal(self.position(xi), self.coordinates[index]):
                raise AdmissionError("P2_NODAL_INTERPOLATION_FAILURE")
            triad = self.triads[index]
            if (np.linalg.norm(triad.T@triad-np.eye(3), ord=np.inf) > INVARIANT_TOLERANCE
                    or abs(float(np.linalg.det(triad))-1.) > INVARIANT_TOLERANCE):
                raise AdmissionError("IMPROPER_NODAL_TRIAD")
            if np.linalg.norm(triad[:,0]-self.tangent(xi), ord=np.inf) > INVARIANT_TOLERANCE:
                raise AdmissionError("NODAL_TRIAD_TANGENT_MISMATCH")
        self.half_rolls: list[float] = []
        self.half_turns: list[float] = []
        for cell in (0, 1):
            left, right = self.triads[cell,:,0], self.triads[cell+1,:,0]
            turn = float(np.arccos(np.clip(float(left@right), -1., 1.)))
            if not turn < BRANCH_LIMIT:
                raise AdmissionError("HALF_FRAME_TANGENT_BRANCH_EXCEEDED")
            base = _jvalues(_jmatmul(_jet_shortest(left, _jvec(right)),
                                     _jmat_constant(self.triads[cell])))
            roll = float(np.arctan2(float(base[:,2]@self.triads[cell+1,:,1]),
                                    float(base[:,1]@self.triads[cell+1,:,1])))
            if not abs(roll) < BRANCH_LIMIT:
                raise AdmissionError("HALF_FRAME_ROLL_BRANCH_EXCEEDED")
            if _scaled_inf_error(_proper_rotation(right, roll)@base,
                                 self.triads[cell+1]) > INVARIANT_TOLERANCE:
                raise AdmissionError("INCOMPATIBLE_NODAL_ROLL")
            self.half_turns.append(turn)
            self.half_rolls.append(roll)

    def position(self, xi: float) -> np.ndarray:
        return np.array((.5*xi*(xi-1.), 1.-xi*xi, .5*xi*(xi+1.))) @ self.coordinates
    def derivative(self, xi: float) -> np.ndarray:
        return self.affine_constant + float(xi)*self.affine_linear
    def jacobian(self, xi: float) -> float:
        return float(np.linalg.norm(self.derivative(xi)))
    def tangent(self, xi: float) -> np.ndarray:
        value = self.derivative(xi)
        return value/np.linalg.norm(value)
    def _frame_jet(self, xi: float, trace: str) -> list[list[Jet]]:
        coordinate = Jet(float(xi), 1.)
        derivative = [Jet(float(self.affine_constant[i])) + coordinate*float(self.affine_linear[i])
                      for i in range(3)]
        tangent = _jscale(_jnorm(derivative).reciprocal(), derivative)
        cell = 0 if xi < 0. or (xi == 0. and trace == "LEFT") else 1
        fraction = coordinate - (-1. if cell == 0 else 0.)
        base = _jmatmul(_jet_shortest(self.triads[cell,:,0], tangent),
                        _jmat_constant(self.triads[cell]))
        return _jmatmul(_jet_rotation(tangent, fraction*self.half_rolls[cell]), base)
    def frame_and_derivative(self, xi: float, trace: str) -> tuple[np.ndarray,np.ndarray]:
        field = self._frame_jet(xi, trace)
        return _jvalues(field), _jderivatives(field)
    def curvature(self, xi: float, trace: str) -> np.ndarray:
        frame, derivative = self.frame_and_derivative(xi, trace)
        spin = frame.T @ derivative / self.jacobian(xi)
        return np.array((spin[2,1], spin[0,2], spin[1,0]))
    def _canonical_half_data(self) -> list[tuple[float, float]]:
        """Map-B metadata in binary64 array arithmetic, separate from jets."""
        rows: list[tuple[float, float]] = []
        for cell in (0, 1):
            left, right = self.triads[cell,:,0], self.triads[cell+1,:,0]
            cross = _skew(np.cross(left, right))
            transport = np.eye(3) + cross + (cross@cross)/(1.+float(left@right))
            base = transport@self.triads[cell]
            turn = float(np.arccos(np.clip(float(left@right), -1., 1.)))
            roll = float(np.arctan2(float(base[:,2]@self.triads[cell+1,:,1]),
                                    float(base[:,1]@self.triads[cell+1,:,1])))
            rows.append((turn, roll))
        return rows
    def canonical_record(self) -> dict[str, Any]:
        regularity = self.regularity
        half_data = self._canonical_half_data()
        return {
            "coordinates_binary64": _hex_array(self.coordinates),
            "frame_branch_data_by_half_cell": [
                {"residual_roll_binary64": _hex(half_data[i][1]),
                 "tangent_turn_binary64": _hex(half_data[i][0])} for i in range(2)],
            "frame_interpolation": {"authority": "INDEPENDENT_DERIVATION",
                "id": "PIECEWISE_SHORTEST_TRANSPORT_LINEAR_ROLL_V1_INDEPENDENT_DERIVATION"},
            "node_parameter_coordinates_binary64": [_hex(x) for x in (-1.,0.,1.)],
            "nodal_triads_binary64": _hex_array(self.triads),
            "regularity": {
                "affine_constant_binary64": _hex_array(self.affine_constant),
                "affine_linear_binary64": _hex_array(self.affine_linear),
                "characteristic_length_binary64": _hex(regularity.characteristic_length),
                "minimum_admissible_jacobian_binary64": _hex(regularity.minimum_admissible_jacobian),
                "minimum_jacobian_squared_binary64": _hex(regularity.minimum_jacobian_squared),
                "minimizer_xi_binary64": _hex(regularity.minimizer_xi),
                "regularity_id": "ANALYTIC_AFFINE_TANGENT_INTERVAL_MINIMUM_V1"},
            "reversal_id": "XI_NEGATION_NODE_1_3_AND_FRAME_DIAG_NEG_POS_NEG_V1",
            "schema": "GE_BEAM3_CURVED_Q2_REFERENCE_GEOMETRY_SCHEMA_V1",
            "tolerances_binary64": {"frame": _hex(FRAME_TOLERANCE),
                "regularity_relative": _hex(REGULARITY_TOLERANCE),
                "rotation": _hex(INVARIANT_TOLERANCE)}}
    def fingerprint(self) -> str:
        return _sha256(_compact_bytes(self.canonical_record()))


def _station_expectation(reference: MapBReference, xi: float, trace: str) -> dict[str, Any]:
    frame, frame_derivative = reference.frame_and_derivative(xi, trace)
    tangent = reference.derivative(xi)/reference.jacobian(xi)
    curvature = reference.curvature(xi, trace)
    force = frame.T@tangent
    return {"current_curvature": curvature, "current_force_measure": force,
            "derivative": reference.derivative(xi), "frame": frame,
            "frame_derivative": frame_derivative, "intrinsic_curvature": curvature,
            "jacobian": reference.jacobian(xi), "position": reference.position(xi),
            "reference_curvature": curvature, "reference_force_measure": force,
            "zero_curvature_strain": np.zeros(3), "zero_force_strain": np.zeros(3)}


def _verify_geometry(record: Any) -> MapBReference:
    geometry = _require_keys(record, {"canonical_geometry_sha256", "coordinates",
        "nodal_triads", "regularity", "stations"}, "geometry record")
    try:
        reference = MapBReference(geometry["coordinates"], geometry["nodal_triads"])
    except AdmissionError as exc:
        if exc.code in {"ZERO_REFERENCE_DERIVATIVE", "NEAR_FOLD_REFERENCE_DERIVATIVE"}:
            raise RegularityContradiction() from exc
        raise FrameContradiction() from exc
    if _require_hash(geometry["canonical_geometry_sha256"], "geometry fingerprint") != reference.fingerprint():
        raise ProofError("canonical geometry fingerprint differs")
    regularity = _require_keys(geometry["regularity"], {"characteristic_length",
        "minimum_admissible_jacobian", "minimum_jacobian_squared", "minimizer_xi"},
        "regularity record")
    for key in regularity:
        _assert_close(regularity[key], getattr(reference.regularity, key),
                      FRAME_TOLERANCE, RegularityContradiction)
    stations = geometry["stations"]
    if not isinstance(stations, list) or len(stations) != len(STATION_SCHEDULE):
        raise ProofError("station record count differs")
    station_keys = {"current_curvature", "current_force_measure", "derivative", "frame",
        "frame_derivative", "intrinsic_curvature", "jacobian", "position",
        "reference_curvature", "reference_force_measure", "trace", "xi",
        "zero_curvature_strain", "zero_force_strain"}
    for station, (xi, trace) in zip(stations, STATION_SCHEDULE):
        row = _require_keys(station, station_keys, "station record")
        if row["trace"] != trace or float(row["xi"]) != xi:
            raise ProofError("station order differs")
        for key, expected in _station_expectation(reference, xi, trace).items():
            kind = RegularityContradiction if key in {"position","derivative","jacobian"} else FrameContradiction
            _assert_close(row[key], expected, FRAME_TOLERANCE, kind)
        frame = np.asarray(row["frame"], dtype=np.float64)
        _assert_close(frame.T@frame, np.eye(3), INVARIANT_TOLERANCE, FrameContradiction)
        if abs(float(np.linalg.det(frame))-1.) > INVARIANT_TOLERANCE:
            raise FrameContradiction()
    left_frame, _ = reference.frame_and_derivative(0., "LEFT")
    right_frame, _ = reference.frame_and_derivative(0., "RIGHT")
    _assert_close(left_frame, right_frame, FRAME_TOLERANCE, FrameContradiction)
    _assert_close(left_frame, reference.triads[1], FRAME_TOLERANCE, FrameContradiction)
    return reference


def _verify_case(case: Any, expected_fixture: dict[str, Any]) -> None:
    row = _require_keys(case, {"base", "case_id", "expected", "objectivity_input",
        "rigidly_transformed", "reversed"}, "positive case")
    if row["case_id"] != expected_fixture["case_id"] or row["expected"] != "ACCEPT":
        raise ProofError("positive fixture identity differs")
    if (row["base"]["coordinates"] != expected_fixture["coordinates"]
            or row["base"]["nodal_triads"] != expected_fixture["nodal_triads"]):
        raise ProofError("positive fixture inputs differ")
    base, transformed, reversed_reference = (_verify_geometry(row[name])
        for name in ("base", "rigidly_transformed", "reversed"))
    transform = _require_keys(row["objectivity_input"], {"rotation","translation"},
                              "objectivity input")
    rotation = _array(transform["rotation"], (3,3), "objectivity rotation")
    translation = _array(transform["translation"], (3,), "objectivity translation")
    _assert_close(rotation.T@rotation, np.eye(3), INVARIANT_TOLERANCE, ReversalContradiction)
    if abs(float(np.linalg.det(rotation))-1.) > INVARIANT_TOLERANCE:
        raise ReversalContradiction()
    _assert_close(transformed.coordinates, base.coordinates@rotation.T+translation,
                  INVARIANT_TOLERANCE, ReversalContradiction)
    _assert_close(transformed.triads, np.einsum("ij,njk->nik", rotation, base.triads),
                  INVARIANT_TOLERANCE, ReversalContradiction)
    _assert_close(reversed_reference.coordinates, base.coordinates[::-1],
                  INVARIANT_TOLERANCE, ReversalContradiction)
    _assert_close(reversed_reference.triads, np.einsum("nij,jk->nik", base.triads[::-1], REVERSAL),
                  INVARIANT_TOLERANCE, ReversalContradiction)
    for xi, trace in STATION_SCHEDULE:
        transformed_frame, transformed_derivative = transformed.frame_and_derivative(xi, trace)
        base_frame, base_derivative = base.frame_and_derivative(xi, trace)
        _assert_close(transformed.position(xi), rotation@base.position(xi)+translation,
                      INVARIANT_TOLERANCE, ReversalContradiction)
        _assert_close(transformed.derivative(xi), rotation@base.derivative(xi),
                      INVARIANT_TOLERANCE, ReversalContradiction)
        _assert_close(transformed_frame, rotation@base_frame, INVARIANT_TOLERANCE, ReversalContradiction)
        _assert_close(transformed_derivative, rotation@base_derivative, INVARIANT_TOLERANCE, ReversalContradiction)
        _assert_close(transformed.curvature(xi, trace), base.curvature(xi, trace),
                      INVARIANT_TOLERANCE, ReversalContradiction)
        mapped_trace = "RIGHT" if trace == "LEFT" else "LEFT" if trace == "RIGHT" else trace
        reversed_frame, _ = reversed_reference.frame_and_derivative(xi, trace)
        source_frame, _ = base.frame_and_derivative(-xi, mapped_trace)
        _assert_close(reversed_reference.position(xi), base.position(-xi), INVARIANT_TOLERANCE, ReversalContradiction)
        _assert_close(reversed_reference.jacobian(xi), base.jacobian(-xi), INVARIANT_TOLERANCE, ReversalContradiction)
        _assert_close(reversed_frame, source_frame@REVERSAL, INVARIANT_TOLERANCE, ReversalContradiction)
        _assert_close(reversed_reference.curvature(xi, trace),
                      COMPONENT_REVERSAL@base.curvature(-xi, mapped_trace),
                      INVARIANT_TOLERANCE, ReversalContradiction)


def _verify_basis_and_straight_limit(cases: list[dict[str, Any]]) -> None:
    for xi in (Fraction(-1), Fraction(0), Fraction(1), Fraction(2,7)):
        shapes = (xi*(xi-1)/2, 1-xi*xi, xi*(xi+1)/2)
        derivatives = (xi-Fraction(1,2), -2*xi, xi+Fraction(1,2))
        if sum(shapes) != 1 or sum(derivatives) != 0:
            raise FrameContradiction()
    straight = MapBReference(cases[0]["base"]["coordinates"], cases[0]["base"]["nodal_triads"])
    if np.any(straight.affine_linear != 0.):
        raise FrameContradiction()
    for xi, trace in STATION_SCHEDULE:
        frame, derivative = straight.frame_and_derivative(xi, trace)
        _assert_close(frame, straight.triads[0], FRAME_TOLERANCE, FrameContradiction)
        _assert_close(derivative, np.zeros((3,3)), FRAME_TOLERANCE, FrameContradiction)
        _assert_close(straight.curvature(xi, trace), np.zeros(3), FRAME_TOLERANCE, FrameContradiction)


def _expect_admission(code: str, coordinates: Any, triads: Any) -> None:
    try:
        MapBReference(coordinates, triads)
    except AdmissionError as exc:
        if exc.code != code:
            raise FrameContradiction() from exc
    else:
        raise FrameContradiction()


def _verify_independent_negative_obligations() -> None:
    straight = _fixture_manifest()[0]
    coordinates, triads = np.asarray(straight["coordinates"]), np.asarray(straight["nodal_triads"])
    coincident = coordinates.copy(); coincident[1] = coincident[0]
    _expect_admission("COINCIDENT_REFERENCE_NODE", coincident, triads)
    # u=(.1,0,0), v=(1,0,0): g vanishes at xi=-.1 while all nodes differ.
    zero = np.array(((.4,0.,0.), (0.,0.,0.), (.6,0.,0.)))
    _expect_admission("ZERO_REFERENCE_DERIVATIVE", zero, triads)
    # u=(0,1e-15,0), v=(1,0,0): positive interior minimum below the bound.
    near = np.array(((.5,-1e-15,0.), (0.,0.,0.), (.5,1e-15,0.)))
    _expect_admission("NEAR_FOLD_REFERENCE_DERIVATIVE", near, triads)
    mismatch = triads.copy(); mismatch[1] = _proper_rotation(np.array((0.,0.,1.)),1e-4)@mismatch[1]
    _expect_admission("NODAL_TRIAD_TANGENT_MISMATCH", coordinates, mismatch)
    improper = triads.copy(); improper[1,:,2] *= -1.
    _expect_admission("IMPROPER_NODAL_TRIAD", coordinates, improper)
    try:
        _jet_shortest(np.array((1.,0.,0.)), _jvec((math.cos(BRANCH_LIMIT),math.sin(BRANCH_LIMIT),0.)))
    except AdmissionError as exc:
        if exc.code != "HALF_FRAME_TANGENT_BRANCH_EXCEEDED":
            raise FrameContradiction() from exc
    else:
        raise FrameContradiction()
    positive = _triad(np.array((1.,0.,0.)), np.array((0.,1.,0.)))
    negative = _triad(np.array((1.,0.,0.)), np.array((0.,-1.,0.)))
    _expect_admission("HALF_FRAME_ROLL_BRANCH_EXCEEDED", coordinates,
                      np.asarray((positive, negative, negative)))
    # Repeated end point is a closed single-element seam and violates distinctness.
    closed = coordinates.copy(); closed[2] = closed[0]
    _expect_admission("COINCIDENT_REFERENCE_NODE", closed, triads)


def _verify_independent_scaling_and_chain(cases: list[dict[str, Any]]) -> None:
    for case in cases:
        base = MapBReference(case["base"]["coordinates"], case["base"]["nodal_triads"])
        factor, shift = 3.25, np.array((-.7,1.1,.4))
        scaled = MapBReference(base.coordinates*factor+shift, base.triads)
        _assert_close(scaled.regularity.minimum_jacobian_squared,
                      factor**2*base.regularity.minimum_jacobian_squared,
                      INVARIANT_TOLERANCE, RegularityContradiction)
        for xi, trace in STATION_SCHEDULE:
            _assert_close(scaled.frame_and_derivative(xi,trace)[0],
                          base.frame_and_derivative(xi,trace)[0],
                          INVARIANT_TOLERANCE, FrameContradiction)
            _assert_close(scaled.curvature(xi,trace), base.curvature(xi,trace)/factor,
                          INVARIANT_TOLERANCE, FrameContradiction)
    spatial = MapBReference(cases[-1]["base"]["coordinates"], cases[-1]["base"]["nodal_triads"])
    shared = spatial.triads[2]
    start = spatial.coordinates[2]
    points = np.asarray((start, start + .5*shared[:,0], start + shared[:,0]))
    continuation = MapBReference(points, np.asarray((shared, shared, shared)))
    _assert_close(continuation.triads[0], spatial.triads[2], INVARIANT_TOLERANCE, FrameContradiction)


def _value_sha256(value: Any) -> str:
    return _sha256(_canonical_bytes(value))


def _case_named(cases: list[dict[str, Any]], case_id: str) -> dict[str, Any]:
    found = [row for row in cases if row.get("case_id") == case_id]
    if len(found) != 1:
        raise ProofError(f"case inventory differs for {case_id}")
    return found[0]


def _claim_geometry(record: dict[str, Any]) -> dict[str, Any]:
    """Recompute the producer-facing invariant summary from raw station data."""
    regularity = record["regularity"]
    minimum_squared = float(regularity["minimum_jacobian_squared"])
    threshold = float(regularity["minimum_admissible_jacobian"])
    orthogonality = determinant = tangent = zero_strain = 0.0
    for station in record["stations"]:
        frame = np.asarray(station["frame"], dtype=np.float64)
        derivative = np.asarray(station["derivative"], dtype=np.float64)
        jacobian = float(station["jacobian"])
        orthogonality = max(
            orthogonality,
            float(np.linalg.norm(frame.T @ frame - np.eye(3), ord=np.inf)),
        )
        determinant = max(determinant, abs(float(np.linalg.det(frame)) - 1.0))
        tangent = max(
            tangent,
            float(np.linalg.norm(frame[:, 0] - derivative / jacobian, ord=np.inf)),
        )
        zero_strain = max(
            zero_strain,
            float(np.linalg.norm(station["zero_force_strain"], ord=np.inf)),
            float(np.linalg.norm(station["zero_curvature_strain"], ord=np.inf)),
        )
    passed = bool(
        minimum_squared > threshold * threshold
        and orthogonality <= INVARIANT_TOLERANCE
        and determinant <= INVARIANT_TOLERANCE
        and tangent <= INVARIANT_TOLERANCE
        and zero_strain <= FRAME_TOLERANCE
    )
    return {
        "geometry_sha256": _value_sha256(record),
        "maximum_determinant_error_binary64": _hex(determinant),
        "maximum_orthogonality_error_binary64": _hex(orthogonality),
        "maximum_tangent_error_binary64": _hex(tangent),
        "maximum_zero_strain_error_binary64": _hex(zero_strain),
        "minimum_admissible_jacobian_binary64": _hex(threshold),
        "minimum_jacobian_squared_binary64": _hex(minimum_squared),
        "passed": passed,
    }


def _claim_positive_case(cases: list[dict[str, Any]], case_id: str) -> dict[str, Any]:
    case = _case_named(cases, case_id)
    variants = {name: _claim_geometry(case[name]) for name in (
        "base", "reversed", "rigidly_transformed")}
    return {
        "case_id": case_id,
        "case_sha256": _value_sha256(case),
        "passed": all(value["passed"] for value in variants.values()),
        "variants": variants,
    }


def _claim_nodal_interpolation(cases: list[dict[str, Any]]) -> dict[str, Any]:
    selectors = ((-1.0, "VALUE", 0), (0.0, "LEFT", 1),
                 (0.0, "RIGHT", 1), (1.0, "VALUE", 2))
    rows: list[dict[str, Any]] = []
    overall = 0.0
    exact = True
    for case in cases:
        coordinates = np.asarray(case["base"]["coordinates"], dtype=np.float64)
        station_by_key = {
            (float(row["xi"]), str(row["trace"])): row
            for row in case["base"]["stations"]
        }
        gap = 0.0
        for xi, trace, node in selectors:
            position = np.asarray(station_by_key[(xi, trace)]["position"])
            gap = max(gap, float(np.linalg.norm(position - coordinates[node], ord=np.inf)))
            exact = exact and np.array_equal(position, coordinates[node])
        overall = max(overall, gap)
        rows.append({
            "case_id": case["case_id"],
            "case_sha256": _value_sha256(case),
            "maximum_nodal_position_gap_binary64": _hex(gap),
        })
    return {
        "case_rows": rows,
        "maximum_nodal_position_gap_binary64": _hex(overall),
        "passed": bool(overall == 0.0 and exact),
    }


def _claim_regularity(cases: list[dict[str, Any]], scaled: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        variants = {name: _claim_geometry(case[name]) for name in (
            "base", "reversed", "rigidly_transformed")}
        rows.append({
            "case_id": case["case_id"],
            "case_sha256": _value_sha256(case),
            "passed": all(value["passed"] for value in variants.values()),
            "variants": variants,
        })
    return {
        "case_rows": rows,
        "passed": bool(all(row["passed"] for row in rows) and scaled.get("passed") is True),
        "transformed_scaled_sha256": _value_sha256(scaled),
    }


def _claim_straight(cases: list[dict[str, Any]]) -> dict[str, Any]:
    case = _case_named(cases, "STRAIGHT_LIMIT")
    first_frame = np.asarray(case["base"]["nodal_triads"][0], dtype=np.float64)
    frame_gap = curvature = 0.0
    for station in case["base"]["stations"]:
        frame_gap = max(frame_gap, float(np.linalg.norm(
            np.asarray(station["frame"]) - first_frame, ord=np.inf)))
        curvature = max(curvature, float(np.linalg.norm(
            station["intrinsic_curvature"], ord=np.inf)))
    return {
        "case_sha256": _value_sha256(case),
        "maximum_curvature_binary64": _hex(curvature),
        "maximum_frame_gap_binary64": _hex(frame_gap),
        "passed": bool(frame_gap <= FRAME_TOLERANCE and curvature <= FRAME_TOLERANCE),
    }


def _claim_twisted(cases: list[dict[str, Any]]) -> dict[str, Any]:
    case = _case_named(cases, "INITIALLY_TWISTED")
    triads = np.asarray(case["base"]["nodal_triads"], dtype=np.float64)
    frame_change = max(float(np.linalg.norm(triads[index] - triads[0], ord=np.inf))
                       for index in (1, 2))
    curvature = max(float(np.linalg.norm(station["intrinsic_curvature"], ord=np.inf))
                    for station in case["base"]["stations"])
    geometry = _claim_geometry(case["base"])
    return {
        "base_geometry": geometry,
        "case_sha256": _value_sha256(case),
        "maximum_intrinsic_curvature_binary64": _hex(curvature),
        "maximum_nodal_frame_change_binary64": _hex(frame_change),
        "passed": bool(geometry["passed"] and frame_change > 0.0 and curvature > 0.0),
    }


def _claim_objectivity(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    overall = 0.0
    for case in cases:
        rotation = np.asarray(case["objectivity_input"]["rotation"], dtype=np.float64)
        translation = np.asarray(case["objectivity_input"]["translation"], dtype=np.float64)
        error = 0.0
        for base, target in zip(case["base"]["stations"],
                                case["rigidly_transformed"]["stations"]):
            error = max(
                error,
                float(np.linalg.norm(np.asarray(target["position"]) -
                    (rotation @ np.asarray(base["position"]) + translation), ord=np.inf)),
                float(np.linalg.norm(np.asarray(target["derivative"]) -
                    rotation @ np.asarray(base["derivative"]), ord=np.inf)),
                float(np.linalg.norm(np.asarray(target["frame"]) -
                    rotation @ np.asarray(base["frame"]), ord=np.inf)),
                float(np.linalg.norm(np.asarray(target["frame_derivative"]) -
                    rotation @ np.asarray(base["frame_derivative"]), ord=np.inf)),
                float(np.linalg.norm(np.asarray(target["intrinsic_curvature"]) -
                    np.asarray(base["intrinsic_curvature"]), ord=np.inf)),
            )
        overall = max(overall, error)
        rows.append({"case_id": case["case_id"], "case_sha256": _value_sha256(case),
                     "maximum_error_binary64": _hex(error)})
    return {"case_rows": rows, "maximum_error_binary64": _hex(overall),
            "passed": overall <= INVARIANT_TOLERANCE}


def _claim_reversal(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    overall = 0.0
    for case in cases:
        base = {(float(row["xi"]), str(row["trace"])): row
                for row in case["base"]["stations"]}
        target = {(float(row["xi"]), str(row["trace"])): row
                  for row in case["reversed"]["stations"]}
        error = 0.0
        for (xi, trace), reversed_station in target.items():
            source_trace = "RIGHT" if trace == "LEFT" else "LEFT" if trace == "RIGHT" else trace
            source = base[(-xi, source_trace)]
            error = max(
                error,
                float(np.linalg.norm(np.asarray(reversed_station["position"]) -
                                     np.asarray(source["position"]), ord=np.inf)),
                float(np.linalg.norm(np.asarray(reversed_station["derivative"]) +
                                     np.asarray(source["derivative"]), ord=np.inf)),
                float(np.linalg.norm(np.asarray(reversed_station["frame"]) -
                                     np.asarray(source["frame"]) @ REVERSAL, ord=np.inf)),
                float(np.linalg.norm(np.asarray(reversed_station["frame_derivative"]) +
                                     np.asarray(source["frame_derivative"]) @ REVERSAL, ord=np.inf)),
                float(np.linalg.norm(np.asarray(reversed_station["intrinsic_curvature"]) -
                                     COMPONENT_REVERSAL @ np.asarray(source["intrinsic_curvature"]), ord=np.inf)),
            )
        overall = max(overall, error)
        rows.append({"case_id": case["case_id"], "case_sha256": _value_sha256(case),
                     "maximum_error_binary64": _hex(error)})
    return {"case_rows": rows, "maximum_error_binary64": _hex(overall),
            "passed": overall <= INVARIANT_TOLERANCE}


def _claim_continuity(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    overall = 0.0
    for case in cases:
        stations = {(float(row["xi"]), str(row["trace"])): row
                    for row in case["base"]["stations"]}
        left = np.asarray(stations[(0.0, "LEFT")]["frame"])
        right = np.asarray(stations[(0.0, "RIGHT")]["frame"])
        node = np.asarray(case["base"]["nodal_triads"][1])
        gap = max(float(np.linalg.norm(left-right, ord=np.inf)),
                  float(np.linalg.norm(left-node, ord=np.inf)),
                  float(np.linalg.norm(right-node, ord=np.inf)))
        overall = max(overall, gap)
        rows.append({"case_id": case["case_id"], "case_sha256": _value_sha256(case),
                     "midpoint_frame_gap_binary64": _hex(gap)})
    return {"case_rows": rows, "maximum_gap_binary64": _hex(overall),
            "passed": overall <= FRAME_TOLERANCE}


def _claim_zero_strain(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    overall = 0.0
    for case in cases:
        error = 0.0
        for variant in ("base", "reversed", "rigidly_transformed"):
            for station in case[variant]["stations"]:
                error = max(error,
                    float(np.linalg.norm(station["zero_force_strain"], ord=np.inf)),
                    float(np.linalg.norm(station["zero_curvature_strain"], ord=np.inf)))
        overall = max(overall, error)
        rows.append({"case_id": case["case_id"], "case_sha256": _value_sha256(case),
                     "maximum_zero_strain_error_binary64": _hex(error)})
    return {"case_rows": rows, "maximum_error_binary64": _hex(overall),
            "passed": overall <= FRAME_TOLERANCE}


def _payload_record(case_id: str, predicate_id: str, evidence: Any,
                    passed: bool) -> dict[str, Any]:
    return {"case_id": case_id, "evidence": evidence, "passed": bool(passed),
            "predicate_id": predicate_id}


def _independent_obligation_payloads(proof: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = proof["cases"]
    auxiliary = proof["auxiliary_evidence"]
    negative_by_case: dict[str, list[dict[str, Any]]] = {}
    for row in auxiliary["negative_admission"]:
        negative_by_case.setdefault(str(row["case_id"]), []).append(row)
    payloads: dict[str, dict[str, Any]] = {}

    basis = auxiliary["basis_identity"]
    basis_passed = bool(
        isinstance(basis.get("samples"), list) and len(basis["samples"]) == 5
        and all(row["partition_unity_binary64"] == _hex(1.0)
                and row["derivative_sum_binary64"] == _hex(0.0)
                for row in basis["samples"])
    )
    payloads[REGISTERED_OBLIGATION_IDS[0]] = _payload_record(
        REGISTERED_OBLIGATION_IDS[0], "EXACT_P2_SAMPLE_IDENTITIES_V1", basis, basis_passed)
    nodal = _claim_nodal_interpolation(cases)
    payloads[REGISTERED_OBLIGATION_IDS[1]] = _payload_record(
        REGISTERED_OBLIGATION_IDS[1], "ALL_POSITIVE_CASE_NODAL_STATION_MATCH_V1",
        nodal, nodal["passed"])
    regularity = _claim_regularity(cases, auxiliary["transformed_scaled"])
    payloads[REGISTERED_OBLIGATION_IDS[2]] = _payload_record(
        REGISTERED_OBLIGATION_IDS[2], "ALL_VARIANT_ANALYTIC_INTERVAL_MINIMA_V1",
        regularity, regularity["passed"])
    straight = _claim_straight(cases)
    payloads[REGISTERED_OBLIGATION_IDS[3]] = _payload_record(
        REGISTERED_OBLIGATION_IDS[3], "CONSTANT_FRAME_ZERO_INTRINSIC_CURVATURE_V1",
        straight, straight["passed"])
    for obligation_id, case_id in (
        ("PLANAR_SHALLOW_ARCH", "PLANAR_SHALLOW"),
        ("PLANAR_DEEP_ARCH", "PLANAR_DEEP"),
        ("ASYMMETRIC_PLANAR_CURVE", "PLANAR_ASYMMETRIC"),
    ):
        evidence = _claim_positive_case(cases, case_id)
        payloads[obligation_id] = _payload_record(
            obligation_id, "POSITIVE_CASE_ALL_VARIANTS_REFERENCE_INVARIANTS_V1",
            evidence, evidence["passed"])
    scaled = auxiliary["transformed_scaled"]
    payloads["TRANSFORMED_AND_SCALED_COPIES"] = _payload_record(
        "TRANSFORMED_AND_SCALED_COPIES", "THREE_SCALE_DIMENSIONLESS_REGULARITY_V1",
        scaled, scaled.get("passed") is True)
    twisted = _claim_twisted(cases)
    payloads["INITIALLY_TWISTED_CURVE"] = _payload_record(
        "INITIALLY_TWISTED_CURVE",
        "NONZERO_EXPLICIT_NODAL_ROLL_AND_INTRINSIC_CURVATURE_V1",
        twisted, twisted["passed"])
    chain = auxiliary["spatial_chain"]
    chain_passed = bool(chain.get("passed") is True and len(chain.get("segments", [])) == 2)
    payloads["MULTIELEMENT_SPATIAL_CHAIN"] = _payload_record(
        "MULTIELEMENT_SPATIAL_CHAIN", "TWO_SEGMENT_SHARED_POSITION_TANGENT_FRAME_V1",
        chain, chain_passed)
    stiffener = auxiliary["curved_stiffener"]
    stiffener_geometry = _claim_geometry(stiffener["geometry"])
    stiffener_passed = bool(stiffener.get("passed") is True and stiffener_geometry["passed"]
        and stiffener.get("physical_roll_authority") == "EXPLICIT_NODAL_TRIADS")
    payloads["CURVED_STIFFENER_SEGMENT"] = _payload_record(
        "CURVED_STIFFENER_SEGMENT", "CURVED_STIFFENER_EXPLICIT_ROLL_GEOMETRY_V1",
        {"geometry": stiffener_geometry, "packet_sha256": _value_sha256(stiffener),
         "physical_roll_authority": stiffener.get("physical_roll_authority")},
        stiffener_passed)
    anisotropic = {
        "curved_stiffener_sha256": _value_sha256(stiffener),
        "explicit_roll_authority": stiffener.get("physical_roll_authority"),
        "passed": bool(twisted["passed"] and stiffener_passed),
        "stiffener_geometry": stiffener_geometry,
        "twisted_reference": twisted,
    }
    payloads["AUTHORITATIVE_ANISOTROPIC_ROLL"] = _payload_record(
        "AUTHORITATIVE_ANISOTROPIC_ROLL", "EXPLICIT_NODAL_TRIADS_ONLY_V1",
        anisotropic, anisotropic["passed"])
    for obligation_id, predicate_id, evidence in (
        ("RIGID_REFERENCE_OBJECTIVITY", "ALL_CASE_SPATIAL_RIGID_COVARIANCE_V1",
         _claim_objectivity(cases)),
        ("CONNECTIVITY_REVERSAL", "ALL_CASE_XI_NEGATION_FRAME_AND_CURVATURE_MAP_V1",
         _claim_reversal(cases)),
        ("FRAME_CONTINUITY", "ALL_CASE_TWO_TRACE_NODE2_FRAME_IDENTITY_V1",
         _claim_continuity(cases)),
        ("ZERO_INTRINSIC_REFERENCE_STRAINS", "ALL_VARIANT_ALL_STATION_GAMMA_KAPPA_ZERO_V1",
         _claim_zero_strain(cases)),
    ):
        payloads[obligation_id] = _payload_record(
            obligation_id, predicate_id, evidence, evidence["passed"])
    for case_id in REGISTERED_OBLIGATION_IDS[16:22]:
        rows = negative_by_case.get(case_id, [])
        evidence = {"observations": rows, "observations_sha256": _value_sha256(rows),
                    "passed": bool(rows and all(row.get("status") == "REJECTED_AS_REGISTERED"
                                                for row in rows))}
        payloads[case_id] = _payload_record(
            case_id, "REGISTERED_NEGATIVE_REJECTION_AND_EXCEPTION_TYPE_V1",
            evidence, evidence["passed"])
    ring = _independent_ring_seam(proof)
    payloads["RING_SEAM_MISMATCH_REJECTION"] = _payload_record(
        "RING_SEAM_MISMATCH_REJECTION",
        "CONCRETE_INCOMPATIBLE_SHARED_POSITION_FRAME_AND_NO_CHAIN_API_V1",
        ring, ring.get("passed") is True)
    integrity = _independent_canonical_integrity(proof)
    matrix = integrity["mutation_matrix"]
    integrity_passed = bool(integrity.get("repeat_identical") is True
        and integrity.get("mutation_detected") is True
        and integrity.get("first_sha256") == integrity.get("repeated_sha256")
        and integrity.get("first_sha256") != integrity.get("mutated_sha256")
        and matrix["passed"] is True
        and matrix["detected_count"] == matrix["mutation_count"]
        and matrix["mutation_count"] == len(matrix["mutations"]))
    payloads["CANONICAL_SERIALIZATION_AND_MUTATION"] = _payload_record(
        "CANONICAL_SERIALIZATION_AND_MUTATION",
        "REPEAT_AND_MUTATED_FINGERPRINT_RELATION_V1", integrity, integrity_passed)
    scope = auxiliary["static_scope"]
    protected = scope["protected_straight_blob_rows"]
    straight_passed = bool(scope.get("straight_blob_freeze") is True and protected
        and all(row.get("status") == "PASS"
                and row.get("observed_git_blob") == row.get("expected_git_blob")
                for row in protected))
    straight_evidence = {"protected_straight_blob_rows": protected,
                         "rows_sha256": _value_sha256(protected)}
    payloads["STRAIGHT_CORE_BLOB_FREEZE"] = _payload_record(
        "STRAIGHT_CORE_BLOB_FREEZE", "EVERY_PROTECTED_STRAIGHT_GIT_BLOB_ROW_V1",
        straight_evidence, straight_passed)
    boundary = scope["production_boundary_record"]
    boundary_passed = bool(scope.get("production_boundary") is True
        and boundary.get("status") == "PASS"
        and boundary.get("independent_checker_authority") is True)
    payloads["PRODUCTION_BOUNDARY"] = _payload_record(
        "PRODUCTION_BOUNDARY", "HASH_BOUND_CHANGED_PATH_AND_REVIEW_BOUNDARY_V1",
        boundary, boundary_passed)
    if set(payloads) != set(REGISTERED_OBLIGATION_IDS):
        raise ProofError("independent obligation payload map differs")
    return payloads


def _independent_ring_seam(proof: dict[str, Any]) -> dict[str, Any]:
    """Rebuild the registered incompatible seam without importing production."""
    root = Path(__file__).resolve().parents[2]
    module_path = root / "src/anysolver/ge_beam3_curved_reference.py"
    try:
        module_tree = ast.parse(module_path.read_text(encoding="utf-8"),
                                filename=str(module_path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise ProofError("production reference module is not statically inspectable") from exc
    top_level_symbols = {
        node.name for node in module_tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    chain_api_names = (
        "ClosedCurvedBeam3ReferenceGeometry",
        "CurvedBeam3ReferenceChain",
        "validate_closed_reference_chain",
        "validate_reference_chain",
    )
    present = [name for name in chain_api_names if name in top_level_symbols]
    shared_position = np.array((1.0, 0.0, 0.0), dtype=np.float64)
    tangent = np.array((1.0, 0.0, 0.0), dtype=np.float64)
    mismatch_roll = 0.25
    cosine, sine = math.cos(mismatch_roll), math.sin(mismatch_roll)
    skew = np.array(((0.0, -tangent[2], tangent[1]),
                     (tangent[2], 0.0, -tangent[0]),
                     (-tangent[1], tangent[0], 0.0)), dtype=np.float64)
    upstream_frame = np.eye(3, dtype=np.float64)
    downstream_frame = (
        np.eye(3, dtype=np.float64)
        + sine * skew
        + (1.0 - cosine) * (skew @ skew)
    ) @ upstream_frame
    position_gap = float(np.linalg.norm(shared_position - shared_position, ord=np.inf))
    frame_gap = float(np.linalg.norm(upstream_frame - downstream_frame, ord=np.inf))
    disposition = "FAIL_CLOSED_NO_REFERENCE_CHAIN_OR_HOLONOMY_API"
    return {
        "chain_api_symbols_present": present,
        "disposition": disposition,
        "downstream_initial": {
            "frame": downstream_frame.tolist(),
            "position": shared_position.tolist(),
        },
        "fixture_id": "INCOMPATIBLE_CLOSED_CHAIN_LOCAL_SEAM",
        "frame_gap_binary64": _hex(frame_gap),
        "mismatch_roll_binary64": _hex(mismatch_roll),
        "passed": bool(position_gap == 0.0 and frame_gap > INVARIANT_TOLERANCE
                       and not present),
        "position_gap_binary64": _hex(position_gap),
        "upstream_terminal": {
            "frame": upstream_frame.tolist(),
            "position": shared_position.tolist(),
        },
    }


def _independent_basis_samples() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for xi in (-1.0, -0.5, 0.0, 0.5, 1.0):
        shape = np.asarray((0.5 * xi * (xi - 1.0), 1.0 - xi * xi,
                            0.5 * xi * (xi + 1.0)), dtype=np.float64)
        derivative = np.asarray((xi - 0.5, -2.0 * xi, xi + 0.5),
                                dtype=np.float64)
        rows.append({
            "derivative_sum_binary64": _hex(float(np.sum(derivative))),
            "derivatives": derivative.tolist(),
            "partition_unity_binary64": _hex(float(np.sum(shape))),
            "shape_functions": shape.tolist(),
            "xi_binary64": _hex(xi),
        })
    return rows


def _json_clone(value: Any) -> Any:
    return json.loads(_compact_bytes(value))


def _changed_hash_nibble(value: str) -> str:
    _require_hash(value, "mutation hash target")
    return ("0" if value[0] != "0" else "1") + value[1:]


def _mutation_path(path: tuple[str | int, ...]) -> str:
    return "$" + "".join(
        f"[{component}]" if isinstance(component, int) else f".{component}"
        for component in path
    )


def _independent_mutation_row(
    baseline: dict[str, Any], *, mutation_id: str, category: str,
    path: tuple[str | int, ...], operation: str, after: Any,
) -> dict[str, Any]:
    altered = _json_clone(baseline)
    target: Any = altered
    for component in path[:-1]:
        target = target[component]
    leaf = path[-1]
    before = _json_clone(target[leaf])
    target[leaf] = _json_clone(after)
    baseline_hash = _value_sha256(baseline)
    altered_hash = _value_sha256(altered)
    status = "DETECTED" if altered_hash != baseline_hash else "NOT_DETECTED"
    return {
        "after": _json_clone(after),
        "before": before,
        "category": category,
        "expected_status": "DETECTED",
        "mutated_payload_sha256": altered_hash,
        "mutation_id": mutation_id,
        "operation": operation,
        "status": status,
        "target_path": _mutation_path(path),
    }


def _registered_mutation_ids(authority_count: int) -> tuple[str, ...]:
    ids: list[str] = [f"NODE_{index}_COORDINATES" for index in range(1, 4)]
    ids.extend(f"TRIAD_{index}_PHYSICAL_ROLL" for index in range(1, 4))
    for sample in range(1, 6):
        ids.extend(f"P2_SAMPLE_{sample}_N{coefficient}" for coefficient in range(1, 4))
        ids.extend(f"P2_SAMPLE_{sample}_DN{coefficient}" for coefficient in range(1, 4))
    ids.extend((
        "TANGENT_ORIENTATION_SIGN", "HALF_1_RESIDUAL_ROLL_SIGN",
        "HALF_2_RESIDUAL_ROLL_SIGN", "HALF_CELL_ORDERING",
        "REVERSAL_MAP_DIAGONAL", "PRODUCTION_REFERENCE_SOURCE_SHA256",
    ))
    ids.extend(f"AUTHORITY_ARTIFACT_SHA256_{index:02d}"
               for index in range(1, authority_count + 1))
    return tuple(ids)


def _independent_mutation_matrix(proof: dict[str, Any]) -> dict[str, Any]:
    fixture = _fixture_manifest()[-1]
    reference = MapBReference(fixture["coordinates"], fixture["nodal_triads"])
    inputs = sorted(proof["authority_manifest"]["inputs"],
                    key=lambda row: str(row["path"]))
    authority_artifacts = [
        {"path": row["path"], "sha256": row["sha256"]} for row in inputs
    ]
    source_rows = [row for row in authority_artifacts
                   if row["path"] == "src/anysolver/ge_beam3_curved_reference.py"]
    if len(source_rows) != 1:
        raise ProofError("mutation matrix source authority differs")
    baseline = {
        "authority_artifact_hashes": authority_artifacts,
        "case_id": fixture["case_id"],
        "frame_branch_data_by_half_cell": _json_clone(
            reference.canonical_record()["frame_branch_data_by_half_cell"]),
        "half_cell_order": ["XI_MINUS1_TO_ZERO", "XI_ZERO_TO_PLUS1"],
        "nodes": _json_clone(fixture["coordinates"]),
        "p2_basis_samples": _independent_basis_samples(),
        "production_source_sha256": source_rows[0]["sha256"],
        "reversal_map_diagonal": [-1, 1, -1],
        "tangent_orientation": (
            (np.asarray((-1.25, 1.5, -0.25), dtype=np.float64)
             @ np.asarray(fixture["coordinates"], dtype=np.float64))
            / np.linalg.norm(np.asarray((-1.25, 1.5, -0.25), dtype=np.float64)
                             @ np.asarray(fixture["coordinates"], dtype=np.float64))
        ).tolist(),
        "triads": _json_clone(fixture["nodal_triads"]),
    }
    rows: list[dict[str, Any]] = []
    for node_index in range(3):
        after = np.asarray(baseline["nodes"][node_index], dtype=np.float64).copy()
        after[node_index] += 2.0**-5
        rows.append(_independent_mutation_row(
            baseline, mutation_id=f"NODE_{node_index + 1}_COORDINATES",
            category="NODE", path=("nodes", node_index),
            operation=f"ADD_BINARY64_0X1P_MINUS5_TO_COMPONENT_{node_index}",
            after=after.tolist()))
    for triad_index in range(3):
        before = np.asarray(baseline["triads"][triad_index], dtype=np.float64)
        after = _proper_rotation(before[:, 0], 2.0**-10) @ before
        rows.append(_independent_mutation_row(
            baseline, mutation_id=f"TRIAD_{triad_index + 1}_PHYSICAL_ROLL",
            category="TRIAD", path=("triads", triad_index),
            operation=("LEFT_MULTIPLY_BY_BINARY64_0X1P_MINUS10_RADIAN_"
                       "FIRST_AXIS_ROTATION"), after=after.tolist()))
    for sample_index, sample in enumerate(baseline["p2_basis_samples"]):
        for field, category, label in (
            ("shape_functions", "P2_SHAPE_COEFFICIENT", "N"),
            ("derivatives", "P2_DERIVATIVE_COEFFICIENT", "DN"),
        ):
            for coefficient in range(3):
                after = float(sample[field][coefficient]) + 2.0**-20
                rows.append(_independent_mutation_row(
                    baseline,
                    mutation_id=(f"P2_SAMPLE_{sample_index + 1}_{label}"
                                 f"{coefficient + 1}"),
                    category=category,
                    path=("p2_basis_samples", sample_index, field, coefficient),
                    operation="ADD_BINARY64_0X1P_MINUS20", after=after))
    rows.append(_independent_mutation_row(
        baseline, mutation_id="TANGENT_ORIENTATION_SIGN", category="TANGENT_SIGN",
        path=("tangent_orientation",), operation="NEGATE_EVERY_TANGENT_COMPONENT",
        after=[-float(value) for value in baseline["tangent_orientation"]]))
    for half_index in range(2):
        roll = float.fromhex(str(baseline["frame_branch_data_by_half_cell"]
                                 [half_index]["residual_roll_binary64"]))
        if roll == 0.0:
            raise ProofError("mutation fixture has zero residual roll")
        rows.append(_independent_mutation_row(
            baseline, mutation_id=f"HALF_{half_index + 1}_RESIDUAL_ROLL_SIGN",
            category="ROLL_SIGN",
            path=("frame_branch_data_by_half_cell", half_index,
                  "residual_roll_binary64"),
            operation="NEGATE_CANONICAL_BINARY64_RESIDUAL_ROLL", after=_hex(-roll)))
    rows.append(_independent_mutation_row(
        baseline, mutation_id="HALF_CELL_ORDERING", category="HALF_ORDERING",
        path=("half_cell_order",), operation="SWAP_LEFT_AND_RIGHT_HALF_CELL_RECORDS",
        after=list(reversed(baseline["half_cell_order"]))))
    rows.append(_independent_mutation_row(
        baseline, mutation_id="REVERSAL_MAP_DIAGONAL", category="REVERSAL_MAP",
        path=("reversal_map_diagonal", 1),
        operation="NEGATE_MIDDLE_DIAGONAL_COMPONENT",
        after=-int(baseline["reversal_map_diagonal"][1])))
    rows.append(_independent_mutation_row(
        baseline, mutation_id="PRODUCTION_REFERENCE_SOURCE_SHA256",
        category="PRODUCTION_SOURCE_HASH", path=("production_source_sha256",),
        operation="REPLACE_FIRST_HEXADECIMAL_NIBBLE",
        after=_changed_hash_nibble(str(baseline["production_source_sha256"]))))
    for artifact_index, artifact in enumerate(authority_artifacts):
        rows.append(_independent_mutation_row(
            baseline,
            mutation_id=f"AUTHORITY_ARTIFACT_SHA256_{artifact_index + 1:02d}",
            category="AUTHORITY_ARTIFACT_HASH",
            path=("authority_artifact_hashes", artifact_index, "sha256"),
            operation="REPLACE_FIRST_HEXADECIMAL_NIBBLE",
            after=_changed_hash_nibble(str(artifact["sha256"]))))
    mutation_ids = tuple(row["mutation_id"] for row in rows)
    registered_ids = _registered_mutation_ids(len(authority_artifacts))
    if mutation_ids != registered_ids:
        raise ProofError("independent mutation target order differs")
    coverage: dict[str, int] = {}
    for row in rows:
        coverage[row["category"]] = coverage.get(row["category"], 0) + 1
    order_hash = _value_sha256(list(mutation_ids))
    if (len(rows) != REGISTERED_MUTATION_COUNT
            or coverage != REGISTERED_MUTATION_COVERAGE
            or order_hash != REGISTERED_MUTATION_ORDER_SHA256):
        raise ProofError("independent registered mutation matrix differs")
    detected_count = sum(row["status"] == "DETECTED" for row in rows)
    return {
        "baseline_payload": baseline,
        "baseline_payload_sha256": _value_sha256(baseline),
        "coverage": coverage,
        "detected_count": detected_count,
        "mutation_count": len(rows),
        "mutation_ids": list(mutation_ids),
        "mutation_order_sha256": order_hash,
        "mutations": rows,
        "passed": bool(detected_count == len(rows)
                       and all(row["status"] == row["expected_status"] for row in rows)),
    }


def _independent_canonical_integrity(proof: dict[str, Any]) -> dict[str, Any]:
    fixture = _fixture_manifest()[-1]
    first = MapBReference(fixture["coordinates"], fixture["nodal_triads"]).fingerprint()
    coordinates = np.asarray(fixture["coordinates"], dtype=np.float64).copy()
    coordinates[1, 1] += 0.03125
    hints = (np.asarray((0.2, -0.6, 1.0), dtype=np.float64),) * 3
    rolls = (0.0, -0.18, 0.31)
    triads = np.asarray([
        _triad(np.asarray((xi - 0.5, -2.0 * xi, xi + 0.5)) @ coordinates,
               hints[index], rolls[index])
        for index, xi in enumerate((-1.0, 0.0, 1.0))
    ])
    changed = MapBReference(coordinates, triads).fingerprint()
    matrix = _independent_mutation_matrix(proof)
    return {
        "first_sha256": first,
        "mutated_sha256": changed,
        "mutation_detected": bool(first != changed and matrix["passed"]),
        "mutation_matrix": matrix,
        "repeated_sha256": first,
        "repeat_identical": True,
    }


def _verify_canonical_integrity_evidence(
    proof: dict[str, Any], value: Any,
) -> dict[str, Any]:
    integrity = _require_keys(value, {
        "first_sha256", "mutated_sha256", "mutation_detected",
        "mutation_matrix", "repeated_sha256", "repeat_identical",
    }, "canonical integrity")
    for key in ("first_sha256", "mutated_sha256", "repeated_sha256"):
        _require_hash(integrity[key], key)
    matrix = _require_keys(integrity["mutation_matrix"], {
        "baseline_payload", "baseline_payload_sha256", "coverage",
        "detected_count", "mutation_count", "mutation_ids",
        "mutation_order_sha256", "mutations", "passed",
    }, "canonical mutation matrix")
    _require_hash(matrix["baseline_payload_sha256"], "mutation baseline payload")
    _require_hash(matrix["mutation_order_sha256"], "mutation order")
    if not isinstance(matrix["mutations"], list):
        raise ProofError("canonical mutation rows are malformed")
    for row in matrix["mutations"]:
        made = _require_keys(row, {
            "after", "before", "category", "expected_status",
            "mutated_payload_sha256", "mutation_id", "operation", "status",
            "target_path",
        }, "canonical mutation row")
        _require_hash(made["mutated_payload_sha256"], "mutated payload")
    expected = _independent_canonical_integrity(proof)
    if integrity != expected:
        raise ProofError("canonical mutation matrix or repeat evidence differs")
    return expected


def _verify_auxiliary(proof: dict[str, Any]) -> None:
    """Reconstruct every auxiliary producer packet instead of trusting flags."""
    auxiliary = _require_keys(proof["auxiliary_evidence"], {
        "basis_identity", "canonical_integrity", "curved_stiffener",
        "negative_admission", "ring_seam", "spatial_chain", "static_scope",
        "transformed_scaled",
    }, "auxiliary evidence")
    basis = _require_keys(auxiliary["basis_identity"], {"passed", "samples"}, "basis identity")
    if basis["passed"] is not True or not isinstance(basis["samples"], list) or len(basis["samples"]) != 5:
        raise FrameContradiction()
    for row, xi in zip(basis["samples"], (-1., -.5, 0., .5, 1.)):
        sample = _require_keys(row, {"derivative_sum_binary64", "derivatives",
            "partition_unity_binary64", "shape_functions", "xi_binary64"}, "basis sample")
        shapes = np.array((.5*xi*(xi-1.), 1.-xi*xi, .5*xi*(xi+1.)))
        derivatives = np.array((xi-.5, -2.*xi, xi+.5))
        if (sample["xi_binary64"] != _hex(xi)
                or sample["partition_unity_binary64"] != _hex(float(np.sum(shapes)))
                or sample["derivative_sum_binary64"] != _hex(float(np.sum(derivatives)))):
            raise FrameContradiction()
        _assert_close(sample["shape_functions"], shapes, 0., FrameContradiction)
        _assert_close(sample["derivatives"], derivatives, 0., FrameContradiction)

    transformed = _require_keys(auxiliary["transformed_scaled"], {
        "base_dimensionless_minimum_jacobian_binary64", "copies", "passed",
        "rotation", "translation"}, "transformed scaled")
    if transformed["passed"] is not True:
        raise ReversalContradiction()
    base_fixture = _fixture_manifest()[-1]
    base = MapBReference(base_fixture["coordinates"], base_fixture["nodal_triads"])
    ratio = math.sqrt(base.regularity.minimum_jacobian_squared) / base.regularity.characteristic_length
    if transformed["base_dimensionless_minimum_jacobian_binary64"] != _hex(ratio):
        raise RegularityContradiction()
    rotation = _array(transformed["rotation"], (3,3), "scaled rotation")
    translation = _array(transformed["translation"], (3,), "scaled translation")
    if _scaled_inf_error(rotation.T@rotation, np.eye(3)) > INVARIANT_TOLERANCE or abs(np.linalg.det(rotation)-1.) > INVARIANT_TOLERANCE:
        raise ReversalContradiction()
    copies = transformed["copies"]
    if not isinstance(copies, list) or len(copies) != 3:
        raise ProofError("scaled copy count differs")
    for copy, scale in zip(copies, (1e-8, 1., 1e8)):
        row = _require_keys(copy, {"dimensionless_minimum_jacobian_binary64", "geometry",
                                  "scale_binary64"}, "scaled copy")
        if row["scale_binary64"] != _hex(scale):
            raise ProofError("scaled copy order differs")
        geometry = _verify_geometry(row["geometry"])
        _assert_close(geometry.coordinates,
                      scale*(base.coordinates@rotation.T+translation),
                      INVARIANT_TOLERANCE, ReversalContradiction)
        _assert_close(geometry.triads, np.einsum("ij,njk->nik", rotation, base.triads),
                      INVARIANT_TOLERANCE, ReversalContradiction)
        observed_ratio = math.sqrt(geometry.regularity.minimum_jacobian_squared) / geometry.regularity.characteristic_length
        if row["dimensionless_minimum_jacobian_binary64"] != _hex(observed_ratio):
            raise RegularityContradiction()

    chain = _require_keys(auxiliary["spatial_chain"], {"passed", "segments",
        "shared_frame_gap_binary64", "shared_position_gap_binary64",
        "shared_tangent_gap_binary64"}, "spatial chain")
    if chain["passed"] is not True or not isinstance(chain["segments"], list) or len(chain["segments"]) != 2:
        raise FrameContradiction()
    first, second = (_verify_geometry(row) for row in chain["segments"])
    position_gap = float(np.linalg.norm(first.coordinates[2]-second.coordinates[0]))
    frame_gap = float(np.linalg.norm(first.triads[2]-second.triads[0], ord=np.inf))
    tangent_gap = float(np.linalg.norm(first.tangent(1.)-second.tangent(-1.)))
    for encoded, observed in (
        (chain["shared_position_gap_binary64"], position_gap),
        (chain["shared_frame_gap_binary64"], frame_gap),
        (chain["shared_tangent_gap_binary64"], tangent_gap),
    ):
        try:
            claimed = float.fromhex(encoded)
        except (TypeError, ValueError) as exc:
            raise ProofError("spatial chain binary64 encoding differs") from exc
        _assert_close(claimed, observed, FRAME_TOLERANCE, FrameContradiction)
    _assert_close(position_gap, 0., 0., FrameContradiction)
    _assert_close(frame_gap, 0., 0., FrameContradiction)
    _assert_close(tangent_gap, 0., INVARIANT_TOLERANCE, FrameContradiction)

    stiffener = _require_keys(auxiliary["curved_stiffener"], {
        "geometry", "passed", "physical_roll_authority"}, "curved stiffener")
    if stiffener["passed"] is not True or stiffener["physical_roll_authority"] != "EXPLICIT_NODAL_TRIADS":
        raise FrameContradiction()
    _verify_geometry(stiffener["geometry"])

    ring = _require_keys(auxiliary["ring_seam"], {
        "chain_api_symbols_present", "disposition", "downstream_initial",
        "fixture_id", "frame_gap_binary64", "mismatch_roll_binary64", "passed",
        "position_gap_binary64", "upstream_terminal",
    }, "ring seam")
    independently_reconstructed_ring = _independent_ring_seam(proof)
    if ring != independently_reconstructed_ring:
        raise ReversalContradiction()
    if ring["passed"] is not True:
        raise ReversalContradiction()

    negative_rows = auxiliary["negative_admission"]
    manifest = proof["negative_fixture_manifest"]
    if not isinstance(negative_rows, list) or len(negative_rows) != len(manifest):
        raise ProofError("negative admission count differs")
    for result, registered in zip(negative_rows, manifest):
        row = _require_keys(result, {"case_id", "exception_type", "fixture_id", "status"},
                            "negative admission")
        if (row["case_id"] != registered["case_id"]
                or row["fixture_id"] != registered["fixture_id"]):
            raise ProofError("negative admission identity differs")
        if row["status"] != "REJECTED_AS_REGISTERED" or row["exception_type"] != registered["expected_exception"]:
            category = RegularityContradiction if row["case_id"] in {
                "COINCIDENT_NODE_REJECTION", "ZERO_TANGENT_REJECTION", "NEAR_FOLD_REJECTION"} else FrameContradiction
            raise category()

    _verify_canonical_integrity_evidence(proof, auxiliary["canonical_integrity"])

    scope = _require_keys(auxiliary["static_scope"], {
        "production_boundary", "production_boundary_record",
        "protected_straight_blob_rows", "ring_seam_disposition",
        "straight_blob_freeze",
    }, "static scope")
    if (scope["production_boundary"] is not True or scope["straight_blob_freeze"] is not True
            or scope["ring_seam_disposition"] != "TYPED_REJECTION_REQUIRED_NO_P4_SEAM_AUTHORITY"):
        raise ProofError("static scope authority differs")
    if scope["production_boundary_record"] != proof["authority_manifest"]["production_boundary"]:
        raise ProofError("static production-boundary record differs")
    if scope["protected_straight_blob_rows"] != proof["authority_manifest"]["protected_straight_blobs"]:
        raise ProofError("static protected-straight rows differ")


def _verify_authority(proof: dict[str, Any]) -> None:
    root = Path(__file__).resolve().parents[2]
    local_paths = {relative: root/relative for relative in AUTHORITY_INPUT_PATHS}
    for field, path_name in {"cases_definition":"docs/reference_cases/ge_beam3_curved_p4_cases.json",
            "contract":"docs/reference_cases/ge_beam3_curved_p4_contract.json",
            "production_reference_module":"src/anysolver/ge_beam3_curved_reference.py"}.items():
        identity = _require_keys(proof[field], {"bytes","path","sha256"}, field)
        raw = _canonical_file_bytes(local_paths[path_name])
        if identity["path"] != path_name or identity["bytes"] != len(raw) or identity["sha256"] != _sha256(raw):
            raise ProofError(f"{field} local identity differs")
    producer_raw = _canonical_file_bytes(local_paths["docs/reference_cases/ge_beam3_curved_p4_reference_producer.py"])
    if _require_hash(proof["producer_script_sha256"], "producer script") != _sha256(producer_raw):
        raise ProofError("producer script local identity differs")
    authority = proof["authority_manifest"]
    if proof["authority_manifest_sha256"] != _sha256(_canonical_bytes(authority)):
        raise ProofError("authority manifest hash differs")
    if set(authority) != {"candidate_id", "commits", "inputs", "production_boundary",
                          "protected_straight_blobs", "schema"}:
        raise ProofError("authority manifest keys differ")
    if (authority.get("candidate_id") != CANDIDATE_ID
            or authority.get("schema") != "anysolver.ge-beam3-curved-p4-run-authority-manifest-v1"):
        raise ProofError("authority candidate differs")
    commits = authority.get("commits")
    if commits != list(COMMIT_AUTHORITIES):
        raise ProofError("authority commit chain differs")
    inputs = authority.get("inputs")
    if not isinstance(inputs,list):
        raise ProofError("authority inputs malformed")
    by_path = {row.get("path"):row for row in inputs if isinstance(row,dict)}
    if len(by_path) != len(inputs):
        raise ProofError("authority inputs duplicate/malformed")
    if set(by_path) != set(AUTHORITY_INPUT_PATHS):
        raise ProofError("authority input path set differs")
    for path_name, local_path in local_paths.items():
        raw = _canonical_file_bytes(local_path)
        row = by_path.get(path_name)
        if (not isinstance(row,dict) or set(row) != {"bytes", "path", "sha256"}
                or row.get("bytes") != len(raw) or row.get("sha256") != _sha256(raw)):
            raise ProofError(f"authority input differs: {path_name}")
    protected = authority.get("protected_straight_blobs")
    if (not isinstance(protected,list)
            or {row.get("path"): row.get("expected_git_blob") for row in protected
                if isinstance(row,dict)} != PROTECTED_STRAIGHT_BLOBS
            or any(set(row) != {"expected_git_blob", "observed_git_blob", "path", "status"}
                   or row["observed_git_blob"] != row["expected_git_blob"]
                   or row["status"] != "PASS" for row in protected)):
        raise ProofError("protected straight blobs differ")
    for path_name, expected_blob in PROTECTED_STRAIGHT_BLOBS.items():
        if _git_blob_sha1(root / path_name) != expected_blob:
            raise ProofError(f"protected straight working blob differs: {path_name}")
    boundary = authority.get("production_boundary")
    if (not isinstance(boundary,dict)
            or set(boundary) != {"base_commit", "changed_paths", "independent_checker_authority",
                                "review_commit", "status"}
            or boundary["base_commit"] != COMMIT_AUTHORITIES[0]["parent"]
            or boundary["review_commit"] != IMPLEMENTATION_REVIEW_COMMIT
            or boundary["independent_checker_authority"] is not True
            or boundary["status"] != "PASS"
            or boundary["changed_paths"] != sorted(REFERENCE_BOUNDARY_PATHS)):
        raise ProofError("production boundary differs")


def _validate_proof(raw: bytes, proof: dict[str, Any]) -> list[dict[str, Any]]:
    keys = {"schema","candidate_id","producer_id","producer_script_sha256",
        "production_reference_module","cases_definition","contract","authority_manifest",
        "authority_manifest_sha256","obligation_order","obligation_order_sha256",
        "station_schedule","positive_fixture_manifest","positive_fixture_manifest_sha256",
        "negative_fixture_manifest","negative_fixture_manifest_sha256","cases",
        "auxiliary_evidence","obligation_records","coverage_count","reason","terminal",
        "production_restriction","payload_sha256"}
    _require_keys(proof, keys, "proof")
    if (proof["schema"] != PROOF_SCHEMA or proof["candidate_id"] != CANDIDATE_ID
            or proof["producer_id"] != PRODUCER_ID):
        raise ProofError("proof identity differs")
    producer_reasons = {
        PASS: "ALL_26_PREREGISTERED_OBLIGATIONS_EXECUTED",
        NO_GO_REGULARITY: "PRODUCER_OBSERVED_SCIENTIFIC_CONTRADICTION",
        NO_GO_FRAME: "PRODUCER_OBSERVED_SCIENTIFIC_CONTRADICTION",
        NO_GO_REVERSAL: "PRODUCER_OBSERVED_SCIENTIFIC_CONTRADICTION",
    }
    if (proof["terminal"] not in producer_reasons
            or proof["reason"] != producer_reasons[proof["terminal"]]
            or proof["production_restriction"] != RESTRICTION):
        raise ProofError("producer terminal/reason/restriction differs")
    payload = dict(proof); claimed = payload.pop("payload_sha256")
    if claimed != _sha256(_canonical_bytes(payload)):
        raise ProofError("proof payload hash differs")
    if tuple(proof["obligation_order"]) != REGISTERED_OBLIGATION_IDS:
        raise ProofError("obligation order differs")
    if proof["obligation_order_sha256"] != OBLIGATION_ORDER_SHA256:
        raise ProofError("obligation order hash differs")
    expected_schedule = [{"index":i,"trace":trace,"xi_binary64":_hex(xi)}
                         for i,(xi,trace) in enumerate(STATION_SCHEDULE)]
    if proof["station_schedule"] != expected_schedule:
        raise ProofError("station schedule differs")
    fixtures = _fixture_manifest()
    if _sha256(_canonical_bytes(fixtures)) != FROZEN_POSITIVE_FIXTURE_MANIFEST_SHA256:
        raise ProofError("independent fixture reconstruction drifted")
    if proof["positive_fixture_manifest"] != fixtures or proof["positive_fixture_manifest_sha256"] != FROZEN_POSITIVE_FIXTURE_MANIFEST_SHA256:
        raise ProofError("positive fixture manifest differs")
    negative = proof["negative_fixture_manifest"]
    expected_negative = [
        {"case_id": case_id, "expected": "REJECT", "expected_exception": exception,
         "fixture_id": fixture_id, "recipe_id": recipe_id}
        for case_id, fixture_id, recipe_id, exception in NEGATIVE_RECIPES
    ]
    if negative != expected_negative:
        raise ProofError("negative fixture manifest differs")
    if proof["negative_fixture_manifest_sha256"] != _sha256(_canonical_bytes(negative)):
        raise ProofError("negative fixture hash differs")
    obligations = proof["obligation_records"]
    if not isinstance(obligations,list) or tuple(row.get("case_id") for row in obligations
            if isinstance(row,dict)) != REGISTERED_OBLIGATION_IDS:
        raise ProofError("obligation records differ")
    for row in obligations:
        _require_keys(row, {"case_id","evidence_sha256","status"}, "obligation record")
        _require_hash(row["evidence_sha256"], "obligation evidence")
        if row["status"] not in {"PASS", "FAIL"}:
            raise ProofError("producer obligation status differs")
    if proof["coverage_count"] != sum(row["status"] == "PASS" for row in obligations):
        raise ProofError("producer coverage count differs")
    if proof["terminal"] == PASS and proof["coverage_count"] != len(REGISTERED_OBLIGATION_IDS):
        raise ProofError("producer PASS lacks complete coverage")
    cases = proof["cases"]
    if not isinstance(cases,list) or tuple(row.get("case_id") for row in cases
            if isinstance(row,dict)) != POSITIVE_FIXTURE_IDS:
        raise ProofError("positive case order differs")
    if not isinstance(proof["auxiliary_evidence"],dict):
        raise ProofError("auxiliary evidence malformed")
    _verify_authority(proof)
    return cases


def _all_checks(value: bool = False) -> dict[str,bool]:
    return {key:value for key in ("authority_identity", "canonical_proof",
        "complete_coverage", "exact_case_and_station_order",
        "independent_reconstruction", "scientific_identities")}


def _scientific_no_go(checks: dict[str, bool], checked_count: int) -> None:
    """Preserve completed process checks and report scientific coverage truthfully."""
    checks["authority_identity"] = True
    checks["canonical_proof"] = True
    checks["complete_coverage"] = checked_count == len(REGISTERED_OBLIGATION_IDS)
    checks["exact_case_and_station_order"] = True
    checks["independent_reconstruction"] = True
    checks["scientific_identities"] = False


def _scientific_disposition(failed_ids: set[str]) -> type[ScientificContradiction]:
    regularity = {
        "ANALYTIC_INTERVAL_REGULARITY", "COINCIDENT_NODE_REJECTION",
        "ZERO_TANGENT_REJECTION", "NEAR_FOLD_REJECTION",
    }
    frame = {
        "HALF_FRAME_BRANCH_CUTOFF_REJECTION",
        "TRIAD_TANGENT_MISMATCH_REJECTION", "IMPROPER_TRIAD_REJECTION",
    }
    if failed_ids & regularity:
        return RegularityContradiction
    if failed_ids & frame:
        return FrameContradiction
    return ReversalContradiction


def _verify_obligation_evidence(
    proof: dict[str, Any], payloads: dict[str, dict[str, Any]],
) -> tuple[int, type[ScientificContradiction] | None]:
    """Verify every evidence hash, then identify the first scientific stop point."""
    records = proof["obligation_records"]
    failed_ids: set[str] = set()
    first_failure_index: int | None = None
    for index, (case_id, record) in enumerate(zip(REGISTERED_OBLIGATION_IDS, records), 1):
        payload = payloads[case_id]
        expected_hash = _value_sha256(payload)
        expected_status = "PASS" if payload["passed"] else "FAIL"
        if record["evidence_sha256"] != expected_hash:
            raise ProofError(f"producer obligation evidence hash differs: {case_id}")
        if record["status"] != expected_status:
            raise ProofError(f"producer obligation status differs: {case_id}")
        if not payload["passed"]:
            failed_ids.add(case_id)
            if first_failure_index is None:
                first_failure_index = index
    if not failed_ids:
        return len(REGISTERED_OBLIGATION_IDS), None
    assert first_failure_index is not None
    return first_failure_index, _scientific_disposition(failed_ids)


def check(proof_path: Path, output: Path) -> dict[str, Any]:
    raw, proof = _strict_load(proof_path)
    cases = _validate_proof(raw, proof)
    checks, terminal, reason = _all_checks(), PASS, "ALL_26_OBLIGATIONS_VERIFIED"
    checked_count = 0
    try:
        for key in ("authority_identity", "canonical_proof",
                    "exact_case_and_station_order"):
            checks[key] = True
        payloads = _independent_obligation_payloads(proof)
        checks["independent_reconstruction"] = True
        checked_count, contradiction = _verify_obligation_evidence(proof, payloads)
        checks["complete_coverage"] = checked_count == len(REGISTERED_OBLIGATION_IDS)
        if contradiction is not None:
            raise contradiction()
        for case, fixture in zip(cases, _fixture_manifest()):
            _verify_case(case, fixture)
        _verify_auxiliary(proof)
        _verify_basis_and_straight_limit(cases)
        _verify_independent_scaling_and_chain(cases)
        _verify_independent_negative_obligations()
        checks["scientific_identities"] = True
    except RegularityContradiction:
        _scientific_no_go(checks, checked_count)
        terminal, reason = NO_GO_REGULARITY, "REGULARITY_CONTRADICTION"
    except FrameContradiction:
        _scientific_no_go(checks, checked_count)
        terminal, reason = NO_GO_FRAME, "FRAME_IDENTITY_CONTRADICTION"
    except ReversalContradiction:
        _scientific_no_go(checks, checked_count)
        terminal, reason = NO_GO_REVERSAL, "REVERSAL_OR_OBJECTIVITY_CONTRADICTION"
    if proof["terminal"] != PASS and terminal != proof["terminal"]:
        raise ProofError("producer/checker scientific disposition disagrees")
    result = {"candidate_id":CANDIDATE_ID, "checker_id":CHECKER_ID, "checks":checks,
        "coverage_count":checked_count,
        "obligation_order_sha256":OBLIGATION_ORDER_SHA256,
        "production_restriction":RESTRICTION, "proof_sha256":_sha256(raw),
        "reason":reason, "schema":CHECK_SCHEMA, "terminal":terminal}
    _write_exclusive(output, result)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    check(arguments.proof.resolve(), arguments.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
