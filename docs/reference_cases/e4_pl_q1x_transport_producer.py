"""Emit one exact, transport-only Q1X geometry proof containing eight D4 cases."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

from e4_pl_q1x_common import (
    GAUSS_IDS,
    GEOMETRY_IDS,
    OPERATION_IDS,
    PATCH_IDS,
    PROOF_SCHEMA,
    PROOF_WRAPPER_SCHEMA,
    Q1XError,
    canonical_bytes,
    read_json,
    sha256,
    validate_contract,
    verify_file,
    write_exclusive,
)


def F(value: Any = 0) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        return Fraction(value)
    raise Q1XError(f"cannot convert {value!r} to Fraction")


def fs(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _factor_square(value: Fraction) -> tuple[Fraction, Fraction]:
    if value < 0:
        raise Q1XError("negative exact radicand")
    if value == 0:
        return Fraction(), Fraction(1)
    numerator, denominator = value.numerator, value.denominator
    combined = numerator * denominator
    outside = 1
    inside = 1
    factor = 2
    while factor * factor <= combined:
        exponent = 0
        while combined % factor == 0:
            combined //= factor
            exponent += 1
        outside *= factor ** (exponent // 2)
        if exponent % 2:
            inside *= factor
        factor += 1 if factor == 2 else 2
    if combined > 1:
        inside *= combined
    return Fraction(outside, denominator), Fraction(inside)


@dataclass(frozen=True)
class Field:
    radicands: tuple[tuple[Fraction, ...], ...] = ()

    @property
    def dimension(self) -> int:
        return 1 << len(self.radicands)

    def rational(self, value: Any = 0) -> "Alg":
        coefficients = [Fraction() for _ in range(self.dimension)]
        coefficients[0] = F(value)
        return Alg(self, tuple(coefficients))

    def with_sqrt(self, value: "Alg") -> tuple["Field", "Alg"]:
        if value.field != self:
            raise Q1XError("radicand belongs to another exact tower")
        scale = Fraction(1)
        reduced = value
        if value.is_rational:
            scale, radicand = _factor_square(value.coefficients[0])
            if scale == 0:
                return self, self.rational()
            if radicand == 1:
                return self, self.rational(scale)
            reduced = self.rational(radicand)
        for index, stored in enumerate(self.radicands):
            padded = stored + (Fraction(),) * (self.dimension - len(stored))
            if reduced.coefficients == padded:
                coefficients = [Fraction() for _ in range(self.dimension)]
                coefficients[1 << index] = scale
                return self, Alg(self, tuple(coefficients))
        if len(self.radicands) >= 5:
            raise Q1XError("equation-7 exact field exceeds formal degree 32")
        result = Field(self.radicands + (reduced.coefficients,))
        coefficients = [Fraction() for _ in range(result.dimension)]
        coefficients[1 << len(self.radicands)] = scale
        return result, Alg(result, tuple(coefficients))

    def sqrt(self, value: "Alg") -> "Alg":
        result, root = self.with_sqrt(value)
        if result != self:
            raise Q1XError("radicand absent from frozen E-numbering field")
        return root

    def subfield(self) -> "Field":
        if not self.radicands:
            raise Q1XError("rational field has no subfield")
        return Field(self.radicands[:-1])


@dataclass(frozen=True)
class Alg:
    field: Field
    coefficients: tuple[Fraction, ...]

    def __post_init__(self) -> None:
        if len(self.coefficients) != self.field.dimension:
            raise Q1XError("algebraic coefficient dimension mismatch")

    @property
    def is_rational(self) -> bool:
        return all(value == 0 for value in self.coefficients[1:])

    @property
    def is_zero(self) -> bool:
        return all(value == 0 for value in self.coefficients)

    def _coerce(self, value: Any) -> "Alg":
        if isinstance(value, Alg):
            if value.field != self.field:
                raise Q1XError("cannot mix distinct exact fields")
            return value
        return self.field.rational(value)

    def lift(self, field: Field) -> "Alg":
        if field == self.field:
            return self
        if field.radicands[: len(self.field.radicands)] != self.field.radicands:
            raise Q1XError("target is not an extension of the exact tower")
        return Alg(field, self.coefficients + (Fraction(),) * (field.dimension - len(self.coefficients)))

    def __add__(self, value: Any) -> "Alg":
        other = self._coerce(value)
        return Alg(self.field, tuple(a + b for a, b in zip(self.coefficients, other.coefficients, strict=True)))

    __radd__ = __add__

    def __neg__(self) -> "Alg":
        return Alg(self.field, tuple(-value for value in self.coefficients))

    def __sub__(self, value: Any) -> "Alg":
        return self + (-self._coerce(value))

    def __rsub__(self, value: Any) -> "Alg":
        return self._coerce(value) - self

    def __mul__(self, value: Any) -> "Alg":
        other = self._coerce(value)
        if not self.field.radicands:
            return Alg(self.field, (self.coefficients[0] * other.coefficients[0],))
        half = self.field.dimension // 2
        subfield = self.field.subfield()
        a = Alg(subfield, self.coefficients[:half])
        b = Alg(subfield, self.coefficients[half:])
        c = Alg(subfield, other.coefficients[:half])
        d = Alg(subfield, other.coefficients[half:])
        radicand = Alg(subfield, self.field.radicands[-1])
        real = a * c + (b * d) * radicand
        radical = a * d + b * c
        return Alg(self.field, real.coefficients + radical.coefficients)

    __rmul__ = __mul__

    def inverse(self) -> "Alg":
        if self.is_zero:
            raise Q1XError("inverse of exact zero")

        def recursive(values: list[Fraction], field: Field) -> list[Fraction]:
            if not field.radicands:
                return [1 / values[0]]
            half = len(values) // 2
            subfield = field.subfield()
            a = Alg(subfield, tuple(values[:half]))
            b = Alg(subfield, tuple(values[half:]))
            radicand = Alg(subfield, field.radicands[-1])
            inverse_norm = Alg(subfield, tuple(recursive(list((a * a - radicand * (b * b)).coefficients), subfield)))
            return list((a * inverse_norm).coefficients) + list((-b * inverse_norm).coefficients)

        return Alg(self.field, tuple(recursive(list(self.coefficients), self.field)))

    def __truediv__(self, value: Any) -> "Alg":
        return self * self._coerce(value).inverse()

    def __rtruediv__(self, value: Any) -> "Alg":
        return self._coerce(value) / self


def token(value: Alg) -> list[str]:
    return [fs(item) for item in value.coefficients]


def vector_tokens(values: Iterable[Alg]) -> list[list[str]]:
    return [token(value) for value in values]


def matrix_tokens(values: Sequence[Sequence[Alg]]) -> list[list[list[str]]]:
    return [vector_tokens(row) for row in values]


def fraction_vector_tokens(values: Iterable[Fraction]) -> list[str]:
    return [fs(value) for value in values]


def fraction_matrix_tokens(values: Sequence[Sequence[Fraction]]) -> list[list[str]]:
    return [fraction_vector_tokens(row) for row in values]


def dot(left: Sequence[Alg], right: Sequence[Alg]) -> Alg:
    return sum((a * b for a, b in zip(left, right, strict=True)), left[0].field.rational())


def cross(left: Sequence[Alg], right: Sequence[Alg]) -> list[Alg]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def transpose(matrix: Sequence[Sequence[Any]]) -> list[list[Any]]:
    return [list(row) for row in zip(*matrix, strict=True)]


def matvec(matrix: Sequence[Sequence[Any]], vector: Sequence[Any]) -> list[Any]:
    return [sum((a * b for a, b in zip(row, vector, strict=True)), vector[0] * 0) for row in matrix]


def matmul(left: Sequence[Sequence[Any]], right: Sequence[Sequence[Any]]) -> list[list[Any]]:
    return [matvec(transpose(right), row) for row in left]


def inverse_fraction(matrix: Sequence[Sequence[Fraction]]) -> list[list[Fraction]]:
    size = len(matrix)
    rows = [list(row) + [Fraction(int(i == j)) for j in range(size)] for i, row in enumerate(matrix)]
    for column in range(size):
        pivot = next((row for row in range(column, size) if rows[row][column]), None)
        if pivot is None:
            raise Q1XError("singular D4 map")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        rows[column] = [value / divisor for value in rows[column]]
        for row in range(size):
            if row != column:
                factor = rows[row][column]
                rows[row] = [a - factor * b for a, b in zip(rows[row], rows[column], strict=True)]
    return [row[size:] for row in rows]


def _progress(geometry_id: str, phase: str, started: float, **extra: Any) -> None:
    row = {"elapsed_ms": int((time.monotonic() - started) * 1000), "geometry_id": geometry_id, "phase": phase, **extra}
    sys.stderr.buffer.write(canonical_bytes(row))
    sys.stderr.buffer.flush()


def _geometry_rows(geometry_contract: dict[str, Any]) -> dict[str, list[list[str]]]:
    result = {str(row["id"]): row["nodes"] for row in geometry_contract["geometries"]}
    transform = geometry_contract["global_transform"]
    result[str(transform["id"])] = transform["derived_nodes"]
    return result


def _fraction_nodes(rows: Sequence[Sequence[Any]]) -> list[list[Fraction]]:
    return [[F(value) for value in row] for row in rows]


def build_field(nodes: Sequence[Sequence[Fraction]]) -> Field:
    d1 = [nodes[2][i] - nodes[0][i] for i in range(3)]
    d2 = [nodes[1][i] - nodes[3][i] for i in range(3)]
    field = Field()
    field, root1 = field.with_sqrt(field.rational(sum(value * value for value in d1)))
    field, root2 = field.with_sqrt(field.rational(sum(value * value for value in d2)))
    root1 = root1.lift(field)
    a = [field.rational(value) / root1 for value in d1]
    b = [field.rational(value) / root2 for value in d2]
    plus = [left + right for left, right in zip(a, b, strict=True)]
    field, _ = field.with_sqrt(dot(plus, plus))
    d1a = [field.rational(value) for value in d1]
    d2a = [field.rational(value) for value in d2]
    diagonal_cross = cross(d1a, d2a)
    field, _ = field.with_sqrt(dot(diagonal_cross, diagonal_cross))
    field, _ = field.with_sqrt(field.rational(3))
    return field


def frame_and_coords(
    nodes_fraction: Sequence[Sequence[Fraction]],
    node_tuple: Sequence[int],
    field: Field,
) -> tuple[list[list[Alg]], list[list[Alg]], list[list[Alg]]]:
    numbered_fraction = [nodes_fraction[int(index) - 1] for index in node_tuple]
    nodes = [[field.rational(value) for value in row] for row in numbered_fraction]
    d1 = [nodes[2][i] - nodes[0][i] for i in range(3)]
    d2 = [nodes[1][i] - nodes[3][i] for i in range(3)]
    root1 = field.sqrt(dot(d1, d1))
    root2 = field.sqrt(dot(d2, d2))
    a = [value / root1 for value in d1]
    b = [value / root2 for value in d2]
    plus = [left + right for left, right in zip(a, b, strict=True)]
    minus = [left - right for left, right in zip(a, b, strict=True)]
    plus_squared = dot(plus, plus)
    diagonal_cross = cross(d1, d2)
    cross_norm = field.sqrt(dot(diagonal_cross, diagonal_cross))

    base_d1 = [field.rational(nodes_fraction[2][i] - nodes_fraction[0][i]) for i in range(3)]
    base_d2 = [field.rational(nodes_fraction[1][i] - nodes_fraction[3][i]) for i in range(3)]
    g1 = field.sqrt(dot(base_d1, base_d1))
    g2 = field.sqrt(dot(base_d2, base_d2))
    base_a = [value / g1 for value in base_d1]
    base_b = [value / g2 for value in base_d2]
    base_plus = [left + right for left, right in zip(base_a, base_b, strict=True)]
    g3 = field.sqrt(dot(base_plus, base_plus))
    g4 = field.sqrt(dot(cross(base_d1, base_d2), cross(base_d1, base_d2)))
    complement = 2 * g4 / (g1 * g2 * g3)
    if g3 * g3 == plus_squared:
        t1_norm = g3
    elif complement * complement == plus_squared:
        t1_norm = complement
    else:
        raise Q1XError("numbered equation-7 first normalization not in E field")
    t2_norm = 2 * cross_norm / (root1 * root2 * t1_norm)
    if t2_norm * t2_norm != dot(minus, minus):
        raise Q1XError("equation-7 second normalization identity failed")
    t1 = [value / t1_norm for value in plus]
    t2 = [value / t2_norm for value in minus]
    t3 = cross(t1, t2)
    frame = [[t1[row], t2[row], t3[row]] for row in range(3)]
    centre = [sum((node[i] for node in nodes), field.rational()) / 4 for i in range(3)]
    coords = [[dot([node[i] - centre[i] for i in range(3)], t1), dot([node[i] - centre[i] for i in range(3)], t2)] for node in nodes]
    return nodes, frame, coords


def _dag_rational(value: Fraction) -> dict[str, Any]:
    return {"denominator": value.denominator, "numerator": value.numerator, "operation": "rational"}


def _dag_coefficients(coefficients: Sequence[Fraction], roots: Sequence[dict[str, Any]]) -> dict[str, Any]:
    terms: list[dict[str, Any]] = []
    for mask, coefficient in enumerate(coefficients):
        if coefficient == 0:
            continue
        term = _dag_rational(coefficient)
        for index, root in enumerate(roots):
            if mask & (1 << index):
                term = {"arguments": [term, root], "operation": "multiply"}
        terms.append(term)
    if not terms:
        return _dag_rational(Fraction())
    result = terms[0]
    for term in terms[1:]:
        result = {"arguments": [result, term], "operation": "add"}
    return result


def field_record(field: Field, nodes: Sequence[Sequence[Fraction]]) -> dict[str, Any]:
    roots: list[dict[str, Any]] = []
    generators: list[dict[str, Any]] = []
    for index, radicand in enumerate(field.radicands):
        dag = _dag_coefficients(radicand, roots)
        root = {"arguments": [dag], "operation": "positive_sqrt"}
        generators.append(
            {
                "id": f"alpha_{index + 1}",
                "radicand_coefficients": [fs(value) for value in radicand],
                "radicand_dag": dag,
                "root_dag": root,
            }
        )
        roots.append(root)
    d1 = [field.rational(nodes[2][i] - nodes[0][i]) for i in range(3)]
    d2 = [field.rational(nodes[1][i] - nodes[3][i]) for i in range(3)]
    g1 = field.sqrt(dot(d1, d1))
    g2 = field.sqrt(dot(d2, d2))
    a = [value / g1 for value in d1]
    b = [value / g2 for value in d2]
    g3 = field.sqrt(dot([x + y for x, y in zip(a, b, strict=True)], [x + y for x, y in zip(a, b, strict=True)]))
    c = cross(d1, d2)
    g4 = field.sqrt(dot(c, c))
    g5 = field.sqrt(field.rational(3))
    return {
        "dimension": field.dimension,
        "formal_degree_limit": 32,
        "generators": generators,
        "schedule": [
            {"id": name, "root_coefficients": token(value)}
            for name, value in zip(("g1", "g2", "g3", "g4", "g5"), (g1, g2, g3, g4, g5), strict=True)
        ],
    }


def _field_maps(operation: dict[str, Any]) -> dict[str, list[list[Fraction]]]:
    (a, b), (c, d) = [[F(value) for value in row] for row in operation["A"]]
    determinant = F(operation["det"])
    return {
        "C_eng": [[a * a, b * b, a * b], [c * c, d * d, c * d], [2 * a * c, 2 * b * d, a * d + b * c]],
        "C_res": [[a * a, b * b, 2 * a * b], [c * c, d * d, 2 * c * d], [a * c, b * d, a * d + b * c]],
        "multiplier": [[determinant, 0, 0], [0, determinant * a, determinant * b], [0, determinant * c, determinant * d]],
        "pseudo_vector": [[determinant * a, determinant * b], [determinant * c, determinant * d]],
    }


def _patch_vector(field: Field, coords: Sequence[Sequence[Alg]], field_id: str) -> list[Alg]:
    result: list[Alg] = []
    for x, y in coords:
        zero = field.rational()
        u = v = w = tx = ty = td = zero
        if field_id in ("MEMBRANE_PATCH", "COMBINED_PHYSICAL_PATCH"):
            u, v, td = 2 * x + y / 3, -2 * x / 5 + 4 * y / 3, field.rational(F("-11/30"))
        if field_id in ("BENDING_PATCH", "COMBINED_PHYSICAL_PATCH"):
            w = -x * x / 5 + y * y / 6 - 3 * x * y / 14
            tx, ty = y / 3 - 3 * x / 14, 2 * x / 5 + 3 * y / 14
        if field_id in ("SHEAR_PATCH", "COMBINED_PHYSICAL_PATCH"):
            tx, ty = tx + F("1/4"), ty + F("2/3")
        result.extend((u, v, w, tx, ty, td))
    return result


def _transport_patch(
    base_patch: Sequence[Alg],
    base_frame: Sequence[Sequence[Alg]],
    numbered_frame: Sequence[Sequence[Alg]],
    node_tuple: Sequence[int],
) -> list[Alg]:
    to_numbered = transpose(numbered_frame)
    result: list[Alg] = []
    for old_node in node_tuple:
        block = list(base_patch[6 * (int(old_node) - 1) : 6 * int(old_node)])
        result.extend(matvec(to_numbered, matvec(base_frame, block[:3])))
        result.extend(matvec(to_numbered, matvec(base_frame, block[3:])))
    return result


def _normalise_recovery_row(row: dict[str, Any], dimension: int) -> dict[str, Any]:
    if row.get("station_id") not in GAUSS_IDS:
        raise Q1XError("historical station ID mismatch")
    result: dict[str, Any] = {"station_id": row["station_id"]}
    for key, length in (("compatible", 8), ("independent", 8), ("N", 3), ("M", 3), ("Q", 2)):
        values = row.get(key)
        if not isinstance(values, list) or len(values) != length:
            raise Q1XError(f"historical recovery {key} shape mismatch")
        scalars: list[str] = []
        for value in values:
            if not isinstance(value, list) or len(value) != dimension or any(F(item) for item in value[1:]):
                raise Q1XError("bounded recovery expected rational local components")
            scalars.append(fs(F(value[0])))
        result[key] = scalars
    return result


def _expected(operation: dict[str, Any], material: dict[str, Any], patch_id: str) -> dict[str, list[Fraction]]:
    maps = _field_maps(operation)
    determinant = F(operation["det"])
    eps0 = [F(2), F("4/3"), F("-1/15")] if patch_id in ("MEMBRANE_PATCH", "COMBINED_PHYSICAL_PATCH") else [F(), F(), F()]
    kap0 = [F("2/5"), F("-1/3"), F("3/7")] if patch_id in ("BENDING_PATCH", "COMBINED_PHYSICAL_PATCH") else [F(), F(), F()]
    shr0 = [F("2/3"), F("-1/4")] if patch_id in ("SHEAR_PATCH", "COMBINED_PHYSICAL_PATCH") else [F(), F()]
    eps = matvec(inverse_fraction(maps["C_eng"]), eps0)
    kap = [determinant * value for value in matvec(inverse_fraction(maps["C_eng"]), kap0)]
    shear = matvec(inverse_fraction(maps["pseudo_vector"]), shr0)
    constitutive = material["constitutive"]
    membrane = [[F(value) for value in row] for row in constitutive["membrane_A"]]
    bending = [[F(value) for value in row] for row in constitutive["bending_D"]]
    transverse = [[F(value) for value in row] for row in constitutive["transverse_shear_A_s"]]
    return {"M": matvec(bending, kap), "N": matvec(membrane, eps), "Q": matvec(transverse, shear), "strain": eps + kap + shear}


def _residuals(row: dict[str, Any], expected: dict[str, list[Fraction]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for key, target in (("compatible", "strain"), ("independent", "strain"), ("N", "N"), ("M", "M"), ("Q", "Q")):
        result[key] = fraction_vector_tokens(F(actual) - wanted for actual, wanted in zip(row[key], expected[target], strict=True))
    return result


def _nonzero_paths(stations: Sequence[dict[str, Any]], residual_name: str) -> list[str]:
    result: list[str] = []
    for station in stations:
        for field, values in station[residual_name].items():
            result.extend(f"{station['station_id']}.{field}[{index}]" for index, value in enumerate(values) if F(value))
    return result


def _alg_nonzero_paths(prefix: str, values: Sequence[Alg]) -> list[str]:
    return [f"{prefix}[{index}]" for index, value in enumerate(values) if not value.is_zero]


def _case_record(
    *,
    geometry_id: str,
    nodes_fraction: list[list[Fraction]],
    field: Field,
    base_frame: list[list[Alg]],
    base_coords: list[list[Alg]],
    operation: dict[str, Any],
    historical_case: dict[str, Any],
    material: dict[str, Any],
    started: float,
) -> dict[str, Any]:
    operation_id = str(operation["id"])
    case_id = f"{geometry_id}::{operation_id}"
    numbered_nodes, numbered_frame, numbered_coords = frame_and_coords(nodes_fraction, operation["node_tuple"], field)
    a = [[F(value) for value in row] for row in operation["A"]]
    determinant = F(operation["det"])
    ahat_fraction = [[a[0][0], a[0][1], 0], [a[1][0], a[1][1], 0], [0, 0, determinant]]
    ahat = [[field.rational(value) for value in row] for row in ahat_fraction]
    expected_frame = matmul(base_frame, ahat)
    frame_residuals = [numbered_frame[i][j] - expected_frame[i][j] for i in range(3) for j in range(3)]
    maps = _field_maps(operation)
    patches: list[dict[str, Any]] = []
    for patch_id in PATCH_IDS:
        base_patch = _patch_vector(field, base_coords, patch_id)
        numbered_patch = _transport_patch(base_patch, base_frame, numbered_frame, operation["node_tuple"])
        patches.append({"base_local": vector_tokens(base_patch), "field_id": patch_id, "numbered_local": vector_tokens(numbered_patch)})
    if historical_case["recovery"]["station_count"] != 4:
        raise Q1XError("historical recovery station count mismatch")
    rows = [_normalise_recovery_row(row, field.dimension) for row in historical_case["recovery"]["rows"]]
    if [row["station_id"] for row in rows] != list(GAUSS_IDS):
        raise Q1XError("historical recovery station order mismatch")
    expected = _expected(operation, material, "COMBINED_PHYSICAL_PATCH")
    legacy = _expected({"A": [[1, 0], [0, 1]], "det": 1}, material, "COMBINED_PHYSICAL_PATCH")
    signs = {"GP_MM": (-1, -1), "GP_PM": (1, -1), "GP_PP": (1, 1), "GP_MP": (-1, 1)}
    stations: list[dict[str, Any]] = []
    for station_index, row in enumerate(rows):
        r_sign, s_sign = signs[row["station_id"]]
        mapped = (
            int(a[0][0]) * r_sign + int(a[0][1]) * s_sign,
            int(a[1][0]) * r_sign + int(a[1][1]) * s_sign,
        )
        station = {
            **row,
            "base_natural_coordinates": [f"{mapped[0]}*sqrt(3)/3", f"{mapped[1]}*sqrt(3)/3"],
            "expected_transported": {key: fraction_vector_tokens(values) for key, values in expected.items()},
            "legacy_untransformed_residuals": _residuals(row, legacy),
            "numbered_natural_coordinates": [f"{r_sign}*sqrt(3)/3", f"{s_sign}*sqrt(3)/3"],
            "transport_residuals": _residuals(row, expected),
        }
        stations.append(station)
        _progress(geometry_id, "STATION_COMPLETED", started, case_id=case_id, station_index=station_index, station_id=row["station_id"])
    base_expected = _expected({"A": [[1, 0], [0, 1]], "det": 1}, material, "COMBINED_PHYSICAL_PATCH")
    base_work = sum(a0 * b0 for a0, b0 in zip(base_expected["N"] + base_expected["M"] + base_expected["Q"], base_expected["strain"], strict=True))
    numbered_work = sum(a0 * b0 for a0, b0 in zip(expected["N"] + expected["M"] + expected["Q"], expected["strain"], strict=True))
    transport_nonzero = _nonzero_paths(stations, "transport_residuals") + _alg_nonzero_paths("frame", frame_residuals)
    legacy_nonzero = _nonzero_paths(stations, "legacy_untransformed_residuals")
    return {
        "case_id": case_id,
        "exact_nonzero_transport_residuals": transport_nonzero,
        "field_maps": {key: fraction_matrix_tokens(value) for key, value in maps.items()},
        "frame": matrix_tokens(numbered_frame),
        "frame_transport_residuals": vector_tokens(frame_residuals),
        "legacy_untransformed_nonzero_residuals": legacy_nonzero,
        "node_tuple": operation["node_tuple"],
        "nodes": matrix_tokens(numbered_nodes),
        "operation_id": operation_id,
        "patch_vectors": patches,
        "source_coordinates": matrix_tokens(numbered_coords),
        "stations": stations,
        "work": {"base": fs(base_work), "numbered": fs(numbered_work), "residual": fs(numbered_work - base_work)},
    }


def _global_transform_record(
    *,
    geometry_contract: dict[str, Any],
    frame_contract: dict[str, Any],
    wrapper_cases: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    geometries = _geometry_rows(geometry_contract)
    source_nodes = _fraction_nodes(geometries["Q3_TAPERED_SKEW"])
    target_nodes = _fraction_nodes(geometries["Q3_TAPERED_SKEW_RSTAR_TRANSLATED"])
    source_field = build_field(source_nodes)
    target_field = build_field(target_nodes)
    if source_field != target_field:
        raise Q1XError("proper global transform changed the exact E field")
    field = source_field
    transform = geometry_contract["global_transform"]
    rotation_f = [[F(value) for value in row] for row in transform["R_star"]]
    rotation = [[field.rational(value) for value in row] for row in rotation_f]
    translation = [F(value) for value in transform["b_star"]]
    node_residuals: list[Fraction] = []
    for source, target in zip(source_nodes, target_nodes, strict=True):
        expected = [sum(rotation_f[i][j] * source[j] for j in range(3)) + translation[i] for i in range(3)]
        node_residuals.extend(target[i] - expected[i] for i in range(3))
    operations: list[dict[str, Any]] = []
    all_nonzero = [f"nodes[{index}]" for index, value in enumerate(node_residuals) if value]
    for operation in frame_contract["d4"]["operations"]:
        operation_id = str(operation["id"])
        _, source_frame, source_coords = frame_and_coords(source_nodes, operation["node_tuple"], field)
        _, target_frame, target_coords = frame_and_coords(target_nodes, operation["node_tuple"], field)
        expected_frame = matmul(rotation, source_frame)
        frame_residuals = [target_frame[i][j] - expected_frame[i][j] for i in range(3) for j in range(3)]
        coordinate_residuals = [target_coords[i][j] - source_coords[i][j] for i in range(4) for j in range(2)]
        source_patch = _patch_vector(field, source_coords, "COMBINED_PHYSICAL_PATCH")
        target_patch = _patch_vector(field, target_coords, "COMBINED_PHYSICAL_PATCH")
        patch_residuals = [a - b for a, b in zip(target_patch, source_patch, strict=True)]
        source_case = wrapper_cases[f"Q3_TAPERED_SKEW::{operation_id}"]
        target_case = wrapper_cases[f"Q3_TAPERED_SKEW_RSTAR_TRANSLATED::{operation_id}"]
        source_rows = [_normalise_recovery_row(row, field.dimension) for row in source_case["recovery"]["rows"]]
        target_rows = [_normalise_recovery_row(row, field.dimension) for row in target_case["recovery"]["rows"]]
        recovery_residuals: dict[str, list[str]] = {}
        for station_index, (source_row, target_row) in enumerate(zip(source_rows, target_rows, strict=True)):
            for key in ("compatible", "independent", "N", "M", "Q"):
                name = f"{GAUSS_IDS[station_index]}.{key}"
                recovery_residuals[name] = fraction_vector_tokens(F(a) - F(b) for a, b in zip(target_row[key], source_row[key], strict=True))
        nonzero = (
            _alg_nonzero_paths("frame", frame_residuals)
            + _alg_nonzero_paths("coordinates", coordinate_residuals)
            + _alg_nonzero_paths("patch", patch_residuals)
            + [f"recovery.{name}[{index}]" for name, values in recovery_residuals.items() for index, value in enumerate(values) if F(value)]
        )
        all_nonzero.extend(f"{operation_id}.{path}" for path in nonzero)
        operations.append(
            {
                "coordinate_residuals": vector_tokens(coordinate_residuals),
                "exact_nonzero_residuals": nonzero,
                "frame_residuals": vector_tokens(frame_residuals),
                "operation_id": operation_id,
                "patch_residuals": vector_tokens(patch_residuals),
                "recovery_residuals": recovery_residuals,
            }
        )
    return {
        "exact_nonzero_residuals": all_nonzero,
        "node_residuals": fraction_vector_tokens(node_residuals),
        "operations": operations,
        "rotation": fraction_matrix_tokens(rotation_f),
        "translation": fraction_vector_tokens(translation),
    }


def emit_geometry_proof(
    *,
    repository_root: Path,
    contract_path: Path,
    contract_sha256: str,
    historical_reference: Path,
    historical_reference_sha256: str,
    geometry_id: str,
) -> dict[str, Any]:
    started = time.monotonic()
    contract = validate_contract(repository_root, contract_path, contract_sha256)
    if geometry_id not in GEOMETRY_IDS:
        raise Q1XError("geometry is outside the frozen shard set")
    _progress(geometry_id, "AUTHORITY_VALIDATED", started)
    historical = contract["historical_reference"]
    raw = verify_file(historical_reference, size=int(historical["bytes"]), digest=historical_reference_sha256)
    if historical_reference_sha256.upper() != historical["sha256"]:
        raise Q1XError("historical wrapper caller hash mismatch")
    wrapper = read_json(historical_reference)[1]
    if wrapper.get("certificate_payload_sha256") != historical["certificate_payload_sha256"]:
        raise Q1XError("historical payload authority mismatch")
    if sha256(canonical_bytes(wrapper["certificate_payload"])) != historical["certificate_payload_sha256"]:
        raise Q1XError("historical payload bytes mismatch")
    root = repository_root.resolve(strict=True)
    geometry_contract = read_json(root / "docs/reference_cases/e4_pl_q1r_geometry_contract.json")[1]
    frame_contract = read_json(root / "docs/reference_cases/e4_pl_q1r_frame_contract.json")[1]
    material = read_json(root / "docs/reference_cases/e4_pl_q1r_material_contract.json")[1]
    geometries = _geometry_rows(geometry_contract)
    nodes_fraction = _fraction_nodes(geometries[geometry_id])
    field = build_field(nodes_fraction)
    _, base_frame, base_coords = frame_and_coords(nodes_fraction, (1, 2, 3, 4), field)
    wrapper_cases = {str(row["id"]): row for row in wrapper["implementation_diagnostics"]["cases"]}
    _progress(geometry_id, "FIELD_CONSTRUCTED", started, dimension=field.dimension)
    cases: list[dict[str, Any]] = []
    for operation in frame_contract["d4"]["operations"]:
        case_id = f"{geometry_id}::{operation['id']}"
        if case_id not in wrapper_cases:
            raise Q1XError(f"historical wrapper lacks {case_id}")
        cases.append(
            _case_record(
                geometry_id=geometry_id,
                nodes_fraction=nodes_fraction,
                field=field,
                base_frame=base_frame,
                base_coords=base_coords,
                operation=operation,
                historical_case=wrapper_cases[case_id],
                material=material,
                started=started,
            )
        )
    if [row["operation_id"] for row in cases] != list(OPERATION_IDS):
        raise Q1XError("operation order drift")
    global_transform = (
        _global_transform_record(geometry_contract=geometry_contract, frame_contract=frame_contract, wrapper_cases=wrapper_cases)
        if geometry_id == "Q3_TAPERED_SKEW_RSTAR_TRANSLATED"
        else None
    )
    proof = {
        "base_frame": matrix_tokens(base_frame),
        "candidate_id": contract["candidate_id"],
        "cases": cases,
        "exact_field": field_record(field, nodes_fraction),
        "frozen_inputs": contract["frozen_inputs"],
        "geometry_id": geometry_id,
        "global_transform": global_transform,
        "historical_reference": {
            "bytes": len(raw),
            "certificate_payload_sha256": wrapper["certificate_payload_sha256"],
            "role": historical["role"],
            "sha256": sha256(raw),
        },
        "producer_scope": contract["scope"],
        "schema": PROOF_SCHEMA,
        "study_id": contract["study_id"],
    }
    body = canonical_bytes(proof)
    result = {"proof": proof, "proof_sha256": sha256(body), "schema": PROOF_WRAPPER_SCHEMA}
    _progress(geometry_id, "PROOF_COMPLETED", started, proof_sha256=result["proof_sha256"])
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-proof", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--transport-contract", type=Path, required=True)
    parser.add_argument("--transport-contract-sha256", required=True)
    parser.add_argument("--historical-reference", type=Path, required=True)
    parser.add_argument("--historical-reference-sha256", required=True)
    parser.add_argument("--geometry-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        value = emit_geometry_proof(
            repository_root=args.repository_root,
            contract_path=args.transport_contract,
            contract_sha256=args.transport_contract_sha256,
            historical_reference=args.historical_reference,
            historical_reference_sha256=args.historical_reference_sha256,
            geometry_id=args.geometry_id,
        )
        write_exclusive(args.output, canonical_bytes(value))
        return 0
    except (Q1XError, KeyError, ValueError, OSError) as exc:
        print(f"BLOCKED_E4_PL_Q1X_PROOF_OR_REVIEW: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
