from __future__ import annotations

import importlib
import sys
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
if str(REFERENCE_CASES) not in sys.path:
    sys.path.insert(0, str(REFERENCE_CASES))


def _sample(module: object, field: object, offset: int) -> object:
    coeff = tuple(Fraction((index + 1) * offset, index + 2) for index in range(field.dimension))
    return module.Alg(field, coeff)


def _identity(module: object, field: object) -> list[list[object]]:
    result = module.zeros(field, 3, 3)
    for index in range(3):
        result[index][index] = field.rational(1)
    return result


def test_q1v_exact_backend_equation7_diagnosis_and_conformance() -> None:
    module = importlib.import_module("e4_pl_q1v_reference")
    assert module.CANDIDATE_ID == "candidate_e4_pl_q1v.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
    assert module.STUDY_ID == "study_e4_pl_q1v.q1u_backend_repair_and_local_completion_v1"

    geometry_contract = module.load_json(REFERENCE_CASES / "e4_pl_q1r_geometry_contract.json")
    frame_contract = module.load_json(REFERENCE_CASES / "e4_pl_q1r_frame_contract.json")
    geometries = module._geometries(geometry_contract)
    operations = module._operations(frame_contract)
    assert len(geometries) == 7
    assert len(operations) == 8

    fields = []
    frames: dict[tuple[str, str], object] = {}
    denominator_count = 0
    for geometry in geometries:
        field = module._equation7_context(geometry)
        fields.append(field)
        assert field.dimension <= 32
        assert len(field.radicands) <= 5

        x, y, z = (_sample(module, field, offset) for offset in (1, 2, 3))
        zero, one = field.rational(0), field.rational(1)
        assert x + zero == x and x * one == x and one * x == x
        assert x * y == y * x
        assert (x * y) * z == x * (y * z)
        assert x * (y + z) == x * y + x * z
        invertible = x + field.rational(7)
        inverse = invertible.inverse()
        assert invertible * inverse == one
        assert inverse * invertible == one

        for level, radicand_coeff in enumerate(field.radicands):
            subfield = module.Field(field.radicands[:level])
            extension = module.Field(field.radicands[: level + 1])
            radicand = module.Alg(subfield, radicand_coeff)
            root_coeff = [Fraction(0) for _ in range(extension.dimension)]
            root_coeff[1 << level] = Fraction(1)
            root = module.Alg(extension, tuple(root_coeff))
            assert root * root == radicand.lift(extension)
            a = _sample(module, subfield, level + 1)
            b = _sample(module, subfield, level + 2)
            assert (a * b).lift(extension) == a.lift(extension) * b.lift(extension)

        e_d1 = tuple(field.rational(geometry.nodes[2][index] - geometry.nodes[0][index]) for index in range(3))
        e_d2 = tuple(field.rational(geometry.nodes[1][index] - geometry.nodes[3][index]) for index in range(3))
        e_g1 = field.sqrt(module._dot3(e_d1, e_d1))
        e_g2 = field.sqrt(module._dot3(e_d2, e_d2))
        e_a = tuple(value / e_g1 for value in e_d1)
        e_b = tuple(value / e_g2 for value in e_d2)
        e_plus = tuple(left + right for left, right in zip(e_a, e_b))
        e_g3 = field.sqrt(module._dot3(e_plus, e_plus))
        e_cross = module._cross3(e_d1, e_d2)
        e_g4 = field.sqrt(module._dot3(e_cross, e_cross))
        e_complement = 2 * e_g4 / (e_g1 * e_g2 * e_g3)

        for operation in operations:
            numbered_field, nodes, frame, coords = module._equation7_frame(geometry, operation)
            assert numbered_field == field
            frames[(geometry.id, operation.id)] = frame
            assert module.matmul(module.transpose(frame), frame) == _identity(module, field)
            columns = [tuple(frame[row][column] for row in range(3)) for column in range(3)]
            assert module._cross3(columns[0], columns[1]) == columns[2]

            d1 = tuple(nodes[2][index] - nodes[0][index] for index in range(3))
            d2 = tuple(nodes[1][index] - nodes[3][index] for index in range(3))
            g1 = field.sqrt(module._dot3(d1, d1))
            g2 = field.sqrt(module._dot3(d2, d2))
            a = tuple(value / g1 for value in d1)
            b = tuple(value / g2 for value in d2)
            plus = tuple(left + right for left, right in zip(a, b))
            minus = tuple(left - right for left, right in zip(a, b))
            plus_squared = module._dot3(plus, plus)
            if e_g3 * e_g3 == plus_squared:
                g3 = e_g3
            else:
                assert e_complement * e_complement == plus_squared
                g3 = e_complement
            cross = module._cross3(d1, d2)
            g4 = field.sqrt(module._dot3(cross, cross))
            denominator = g1 * g2 * g3
            assert not denominator.is_zero
            denominator_inverse = denominator.inverse()
            assert denominator * denominator_inverse == field.rational(1)
            assert denominator_inverse * denominator == field.rational(1)
            denominator_count += 1
            direct_squared = module._dot3(minus, minus)
            derived = 2 * g4 / denominator
            assert derived * derived == direct_squared

            centre_jacobian, centre_det, _, _ = module._centre_geometry_terms(field, coords)
            assert len(centre_jacobian) == 2 and len(centre_jacobian[0]) == 2
            centre_inverse = centre_det.inverse()
            assert centre_det * centre_inverse == field.rational(1)
            assert centre_inverse * centre_det == field.rational(1)
            denominator_count += 1
            for r, s in module._gauss(field):
                _, dr, ds = module._shape(field, r, s)
                _, determinant = module._jacobian(coords, dr, ds)
                determinant_inverse = determinant.inverse()
                assert determinant * determinant_inverse == field.rational(1)
                assert determinant_inverse * determinant == field.rational(1)
                denominator_count += 1

        base_frame = frames[(geometry.id, "E")]
        for operation in operations:
            ahat = module.zeros(field, 3, 3)
            for row in range(2):
                for column in range(2):
                    ahat[row][column] = field.rational(operation.A[row][column])
            ahat[2][2] = field.rational(operation.det)
            assert frames[(geometry.id, operation.id)] == module.matmul(base_frame, ahat)

    assert len(fields) == 7
    assert denominator_count == 7 * 8 * 6
