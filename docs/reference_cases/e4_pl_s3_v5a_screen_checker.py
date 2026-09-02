"""Independent checker for the V5A source-authorized unrelaxed MIN3 screen."""

from __future__ import annotations

import argparse
import itertools
import os
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import e4_pl_s3_mixed_mesh_manifest as mesh_manifest
import e4_pl_s3_v4a_screen_checker as independent_q4
import e4_pl_s3_linear_reference as independent_pl


CONTRACT = REFERENCE / "e4_pl_s3_v5a_screen_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V5A_MIN3_UNRELAXED_FLAT_LINEAR_SCREEN_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v5a-min3-screen-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v5a-min3-screen-check-v1"
YOUNG = 210_000_000_000.0
POISSON = 0.3
THICKNESS = 0.01
PRESSURE = 1000.0
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)
DEVELOPMENT = ((20, 5), (40, 5), (20, 10), (40, 10))


canonical_bytes = independent_q4.canonical_bytes
sha256_file = independent_q4.sha256_file
load_document = independent_q4.load_document
decode_array = independent_q4._decode
relative_inf = independent_q4._relative_inf
rank = independent_q4._rank


def _metric(vertices: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    xy = np.asarray(vertices[:, :2], dtype=np.float64)
    jacobian = np.asarray((xy[1] - xy[0], xy[2] - xy[0]))
    determinant = float(np.linalg.det(jacobian))
    inverse = np.linalg.inv(jacobian)
    natural = np.asarray(((-1.0, 1.0, 0.0), (-1.0, 0.0, 1.0)))
    gradient = inverse @ natural
    return abs(determinant) / 2.0, gradient[0], gradient[1]


def _interpolation(vertices: np.ndarray, coordinate: Sequence[float]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    xy = np.asarray(vertices[:, :2], dtype=np.float64)
    _area, nx, ny = _metric(vertices)
    n = np.asarray(coordinate, dtype=np.float64)
    # Independently transcribed NASA/TP-2018-220079 A.1--A.4.
    ax = np.roll(xy[:, 0], 1) - np.roll(xy[:, 0], -1)
    by = np.roll(xy[:, 1], -1) - np.roll(xy[:, 1], 1)
    l = np.zeros(3)
    m = np.zeros(3)
    l_gradient = np.zeros((2, 3))
    m_gradient = np.zeros((2, 3))
    for i in range(3):
        j, k = (i + 1) % 3, (i + 2) % 3
        l[i] = n[i] * (by[k] * n[j] - by[j] * n[k]) / 2.0
        m[i] = n[i] * (ax[j] * n[k] - ax[k] * n[j]) / 2.0
        for axis, dn in enumerate((nx, ny)):
            l_gradient[axis, i] = (dn[i] * (by[k] * n[j] - by[j] * n[k]) + n[i] * (by[k] * dn[j] - by[j] * dn[k])) / 2.0
            m_gradient[axis, i] = (dn[i] * (ax[j] * n[k] - ax[k] * n[j]) + n[i] * (ax[j] * dn[k] - ax[k] * dn[j])) / 2.0
    return n, l, m, l_gradient, m_gradient


def _constitutive() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    plane = np.asarray(((1.0, POISSON, 0.0), (POISSON, 1.0, 0.0), (0.0, 0.0, (1.0 - POISSON) / 2.0)))
    return (
        YOUNG * THICKNESS / (1.0 - POISSON**2) * plane,
        YOUNG * THICKNESS**3 / (12.0 * (1.0 - POISSON**2)) * plane,
        (5.0 / 6.0) * YOUNG * THICKNESS / (2.0 * (1.0 + POISSON)) * np.eye(2),
    )


def _strain_maps(vertices: np.ndarray, coordinate: Sequence[float]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    _area, nx, ny = _metric(vertices)
    n, _l, _m, lg, mg = _interpolation(vertices, coordinate)
    bm = np.zeros((3, 18))
    bk = np.zeros((3, 18))
    bs = np.zeros((2, 18))
    for i in range(3):
        c = 6 * i
        bm[:, c : c + 2] = ((nx[i], 0.0), (0.0, ny[i]), (ny[i], nx[i]))
        bk[:, c + 3 : c + 5] = ((0.0, nx[i]), (-ny[i], 0.0), (-nx[i], ny[i]))
        # NASA B.6 after theta_x(source)=-rx, theta_y(source)=ry.
        bs[:, c + 2 : c + 5] = (
            (nx[i], -lg[0, i], mg[0, i] + n[i]),
            (ny[i], -lg[1, i] - n[i], mg[1, i]),
        )
    return bm, bk, bs


def reconstruct(vertices: np.ndarray) -> dict[str, np.ndarray]:
    area, _nx, _ny = _metric(vertices)
    membrane_section, bending_section, shear_section = _constitutive()
    bm, bk, _bs = _strain_maps(vertices, (1.0 / 3.0,) * 3)
    membrane = area * bm.T @ membrane_section @ bm
    bending = area * bk.T @ bending_section @ bk
    shear = np.zeros((18, 18))
    pressure = np.zeros(18)
    stations = ((2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0), (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0), (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0))
    for coordinate in stations:
        _bm, _bk, bs = _strain_maps(vertices, coordinate)
        shear += area / 3.0 * bs.T @ shear_section @ bs
        n, l, m, _lg, _mg = _interpolation(vertices, coordinate)
        for i in range(3):
            pressure[6 * i + 2] += PRESSURE * area * n[i] / 3.0
            pressure[6 * i + 3] -= PRESSURE * area * l[i] / 3.0
            pressure[6 * i + 4] += PRESSURE * area * m[i] / 3.0
    _local, inverse, determinant = independent_pl._geometry(vertices[:, :2])
    constraint, gram, pl = independent_pl._pl_blocks(inverse, determinant, independent_pl.invariant_drill_scale(membrane_section))
    physical = membrane + bending + shear
    total = physical + pl
    return {
        "bending": 0.5 * (bending + bending.T),
        "membrane": 0.5 * (membrane + membrane.T),
        "physical": 0.5 * (physical + physical.T),
        "pl": 0.5 * (pl + pl.T),
        "pl_constraint": constraint,
        "pl_gram": gram,
        "pressure_load": pressure,
        "shear": 0.5 * (shear + shear.T),
        "total": 0.5 * (total + total.T),
    }


def _patch(coordinates: np.ndarray, name: str) -> tuple[np.ndarray, str, np.ndarray]:
    fields = {
        "membrane_x": (lambda x, y: (x, 0, 0, 0, 0, 0), "membrane", (1.0, 0.0, 0.0)),
        "membrane_y": (lambda x, y: (0, y, 0, 0, 0, 0), "membrane", (0.0, 1.0, 0.0)),
        "membrane_xy": (lambda x, y: (y / 2.0, x / 2.0, 0, 0, 0, 0), "membrane", (0.0, 0.0, 1.0)),
        "shear_x": (lambda x, y: (0, 0, x, 0, 0, 0), "shear", (1.0, 0.0)),
        "shear_y": (lambda x, y: (0, 0, y, 0, 0, 0), "shear", (0.0, 1.0)),
        "curvature_xx": (lambda x, y: (0, 0, -x * x / 2.0, 0, x, 0), "bending", (1.0, 0.0, 0.0)),
        "curvature_yy": (lambda x, y: (0, 0, -y * y / 2.0, -y, 0, 0), "bending", (0.0, 1.0, 0.0)),
        "curvature_xy": (lambda x, y: (0, 0, -x * y / 2.0, -x / 2.0, y / 2.0, 0), "bending", (0.0, 0.0, 1.0)),
    }
    function, component, target = fields[name]
    vector = np.asarray([item for x, y, _z in coordinates for item in function(x, y)])
    return vector, component, np.asarray(target)


def _rigid(coordinates: np.ndarray) -> np.ndarray:
    result = np.zeros((6 * len(coordinates), 6))
    for node, (x, y, _z) in enumerate(coordinates):
        c = 6 * node
        result[c, 0] = result[c + 1, 1] = result[c + 2, 2] = 1.0
        result[c + 2, 3], result[c + 3, 3] = y, 1.0
        result[c + 2, 4], result[c + 4, 4] = -x, 1.0
        result[c, 5], result[c + 1, 5], result[c + 5, 5] = -y, x, 1.0
    return result


def _triangles(i: int, j: int, n: int, diagonal: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    ll = j * (n + 1) + i
    lr, ul, ur = ll + 1, ll + n + 1, ll + n + 2
    selected = diagonal
    if diagonal == "alternating":
        selected = "slash" if (i + j) % 2 == 0 else "backslash"
    return ((ll, lr, ul), (lr, ur, ul)) if selected == "slash" else ((ll, lr, ur), (ll, ur, ul))


def _scatter(target: np.ndarray, local: np.ndarray, nodes: Sequence[int]) -> None:
    indices = np.concatenate([np.arange(6 * node, 6 * node + 6) for node in nodes])
    target[np.ix_(indices, indices)] += local


def _scatter_load(target: np.ndarray, local: np.ndarray, nodes: Sequence[int]) -> None:
    indices = np.concatenate([np.arange(6 * node, 6 * node + 6) for node in nodes])
    target[indices] += local


def _grid(size: int, diagonal: str, variant: str) -> dict[str, Any]:
    count = (size + 1) ** 2
    coordinates = np.asarray(tuple((i / size, j / size, 0.0) for j in range(size + 1) for i in range(size + 1)))
    matrix = np.zeros((6 * count, 6 * count))
    q4_matrix = np.zeros_like(matrix)
    load = np.zeros(6 * count)
    elements: list[tuple[int, ...]] = []
    for j in range(size):
        for i in range(size):
            nodes4 = (j * (size + 1) + i, j * (size + 1) + i + 1, (j + 1) * (size + 1) + i + 1, (j + 1) * (size + 1) + i)
            q4 = independent_q4._q4(coordinates[np.asarray(nodes4)], NORMAL)["total"]
            _scatter(q4_matrix, q4, nodes4)
            split = variant == "all_s3" or (variant == "isolated" and i == size // 2 and j == size // 2) or (variant == "strip" and i == size // 2)
            if split:
                for triangle in _triangles(i, j, size, diagonal):
                    local = reconstruct(coordinates[np.asarray(triangle)])
                    _scatter(matrix, local["total"], triangle)
                    _scatter_load(load, local["pressure_load"], triangle)
                    elements.append(tuple(triangle))
            else:
                _scatter(matrix, q4, nodes4)
                q4_load = np.zeros(24)
                q4_load[2::6] = PRESSURE / (4.0 * size**2)
                _scatter_load(load, q4_load, nodes4)
                elements.append(tuple(nodes4))
    boundary_nodes = [node for node in range(count) if node % (size + 1) in (0, size) or node // (size + 1) in (0, size)]
    interior_nodes = [node for node in range(count) if node not in set(boundary_nodes)]
    boundary = np.concatenate([np.arange(6 * node, 6 * node + 6) for node in boundary_nodes])
    interior = np.concatenate([np.arange(6 * node, 6 * node + 6) for node in interior_nodes]) if interior_nodes else np.asarray([], dtype=int)
    condensed = matrix[np.ix_(boundary, boundary)]
    q4_condensed = q4_matrix[np.ix_(boundary, boundary)]
    if interior.size:
        coupling = matrix[np.ix_(boundary, interior)]
        condensed -= coupling @ np.linalg.solve(matrix[np.ix_(interior, interior)], coupling.T)
        q4_coupling = q4_matrix[np.ix_(boundary, interior)]
        q4_condensed -= q4_coupling @ np.linalg.solve(q4_matrix[np.ix_(interior, interior)], q4_coupling.T)
    return {"boundary": boundary, "condensed": 0.5 * (condensed + condensed.T), "coordinates": coordinates, "elements": elements, "interior": interior, "load": load, "q4_condensed": 0.5 * (q4_condensed + q4_condensed.T), "total": matrix}


def _interface_normal_worst(coordinates: np.ndarray, elements: Sequence[Sequence[int]]) -> float:
    owners: dict[tuple[int, int], list[np.ndarray]] = {}
    for element in elements:
        for left, right in zip(element, (*element[1:], element[0])):
            edge = coordinates[right, :2] - coordinates[left, :2]
            normal = np.asarray((edge[1], -edge[0])) / np.linalg.norm(edge)
            owners.setdefault(tuple(sorted((left, right))), []).append(normal)
    worst = 0.0
    for normals in owners.values():
        if len(normals) == 2:
            worst = max(worst, float(np.linalg.norm(normals[0] + normals[1], ord=np.inf)))
        elif len(normals) != 1:
            raise ValueError("macrocell edge has invalid ownership")
    return worst


def _local_checks(expected: Mapping[str, np.ndarray], vertices: np.ndarray) -> dict[str, Any]:
    sections = dict(zip(("membrane", "bending", "shear"), _constitutive()))
    area, _nx, _ny = _metric(vertices)
    patch_worst = 0.0
    for name in ("membrane_x", "membrane_y", "membrane_xy", "shear_x", "shear_y", "curvature_xx", "curvature_yy", "curvature_xy"):
        vector, component, target = _patch(vertices, name)
        actual = float(vector @ expected[component] @ vector)
        reference = float(area * target @ sections[component] @ target)
        patch_worst = max(patch_worst, abs(actual - reference) / max(abs(reference), 1.0))
        operator_index = {"membrane": 0, "bending": 1, "shear": 2}[component]
        for coordinate in ((2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0), (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0), (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0)):
            patch_worst = max(patch_worst, relative_inf(_strain_maps(vertices, coordinate)[operator_index] @ vector, target))
    shape_worst = 0.0
    for coordinate in ((1.0 / 3.0,) * 3, (0.7, 0.2, 0.1), (0.0, 0.4, 0.6)):
        n, l, m, _lg, _mg = _interpolation(vertices, coordinate)
        shape_worst = max(shape_worst, abs(float(n.sum()) - 1.0), abs(float(l.sum())), abs(float(m.sum())))
    edge_worst = 0.0
    for left, right, opposite in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        tangent = vertices[right, :2] - vertices[left, :2]
        tangent /= np.linalg.norm(tangent)
        rows = []
        for fraction in (0.0, 0.5, 1.0):
            coordinate = np.zeros(3)
            coordinate[left], coordinate[right], coordinate[opposite] = 1.0 - fraction, fraction, 0.0
            rows.append(tangent @ _strain_maps(vertices, coordinate)[2])
        edge_worst = max(edge_worst, relative_inf(rows[1], rows[0]), relative_inf(rows[2], rows[0]))
    rigid = float(np.linalg.norm(expected["total"] @ _rigid(vertices), ord=np.inf) / max(np.linalg.norm(expected["total"], ord=np.inf), 1.0))
    ranks = {name: rank(expected[name], 1.0e-10) for name in ("physical", "pl", "total")}
    passed = ranks == {"physical": 9, "pl": 3, "total": 12} and max(shape_worst, edge_worst, patch_worst, rigid) <= 3.0e-12
    return {"edge_worst": edge_worst, "passed": bool(passed), "patch_worst": patch_worst, "ranks": ranks, "rigid": rigid, "shape_worst": shape_worst}


def _development(level: int, fraction: int) -> dict[str, Any]:
    from scipy import sparse
    from scipy.sparse.linalg import spsolve
    from e4_pl_s3_v2_flat_funnel_checker import reference_vector_document

    base = mesh_manifest.selected_base_cells("dispersed", fraction * 4)
    split = mesh_manifest.expanded_split_cells(base, level)
    count = (level + 1) ** 2
    coordinates = np.asarray(tuple((i / level, j / level, 0.0) for j in range(level + 1) for i in range(level + 1)))
    row: list[int] = []
    column: list[int] = []
    value: list[float] = []
    pl_value: list[float] = []
    load = np.zeros(6 * count)
    h = 1.0 / level
    q4 = independent_q4._q4(np.asarray(((0.0, 0.0, 0.0), (h, 0.0, 0.0), (h, h, 0.0), (0.0, h, 0.0))), NORMAL)
    q4_load = np.zeros(24)
    q4_load[2::6] = PRESSURE * h * h / 4.0
    cache: dict[tuple[int, ...], dict[str, np.ndarray]] = {}
    for j in range(level):
        for i in range(level):
            entries: list[tuple[tuple[int, ...], Mapping[str, np.ndarray], np.ndarray]] = []
            if (i, j) in split:
                for triangle in _triangles(i, j, level, "slash"):
                    signature = tuple(node - triangle[0] for node in triangle)
                    local = cache.get(signature)
                    if local is None:
                        local = reconstruct(coordinates[np.asarray(triangle)] - coordinates[triangle[0]])
                        cache[signature] = local
                    entries.append((triangle, local, local["pressure_load"]))
            else:
                nodes = (j * (level + 1) + i, j * (level + 1) + i + 1, (j + 1) * (level + 1) + i + 1, (j + 1) * (level + 1) + i)
                entries.append((nodes, q4, q4_load))
            for nodes, local, local_load in entries:
                dofs = np.asarray([6 * node + dof for node in nodes for dof in range(6)])
                rr, cc = np.meshgrid(dofs, dofs, indexing="ij")
                row.extend(rr.reshape(-1).tolist())
                column.extend(cc.reshape(-1).tolist())
                value.extend(np.asarray(local["total"]).reshape(-1).tolist())
                pl_value.extend(np.asarray(local["pl"]).reshape(-1).tolist())
                np.add.at(load, dofs, local_load)
    shape = (6 * count, 6 * count)
    matrix = sparse.coo_matrix((value, (row, column)), shape=shape).tocsr()
    pl = sparse.coo_matrix((pl_value, (row, column)), shape=shape).tocsr()
    fixed: set[int] = set()
    for j in range(level + 1):
        for i in range(level + 1):
            node = j * (level + 1) + i
            if i in (0, level) or j in (0, level):
                fixed.update((6 * node, 6 * node + 1, 6 * node + 2))
            if i in (0, level):
                fixed.add(6 * node + 3)
            if j in (0, level):
                fixed.add(6 * node + 4)
    free = np.asarray([index for index in range(shape[0]) if index not in fixed])
    displacement = np.zeros(shape[0])
    displacement[free] = spsolve(matrix[free][:, free], load[free])
    reference_document, reference_center = reference_vector_document(level)
    reference_sha = independent_q4.sha256_bytes(canonical_bytes(reference_document))
    center = float(displacement[6 * ((level // 2) * (level + 1) + level // 2) + 2])
    residual = float(np.linalg.norm((matrix @ displacement - load)[free], ord=np.inf) / max(np.linalg.norm(load[free], ord=np.inf), 1.0))
    total_energy = float(displacement @ matrix @ displacement)
    return {
        "connectivity_sha256": mesh_manifest.connectivity_sha256(level, split, "slash"),
        "level": level,
        "pl_participation_hex": (abs(float(displacement @ pl @ displacement)) / max(abs(total_energy), 1.0)).hex(),
        "record_id": f"N{level}:{fraction}PCT:dispersed:slash",
        "reference_center_hex": float(reference_center).hex(),
        "reference_sha256": reference_sha,
        "response_center_hex": center.hex(),
        "response_relative_error_hex": abs(center / reference_center - 1.0).hex(),
        "solve_residual_relative_inf_hex": residual.hex(),
    }


def verify(proof: Mapping[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != PROOF_SCHEMA or proof.get("candidate_formulation_id") != FORMULATION_ID:
        raise ValueError("unexpected V5A proof identity")
    if proof.get("contract_sha256") != sha256_file(CONTRACT):
        raise ValueError("V5A proof contract hash mismatch")
    if proof.get("production_boundary") != {"anymesh_untouched": True, "default_q4_formulation": "e4-pl", "default_s3_formulation": "legacy-s3", "q4_mechanics_unchanged": True}:
        raise ValueError("V5A production boundary mismatch")
    if proof.get("stage4a_rerun_authorized") is not False or proof.get("activation_authorized") is not False:
        raise ValueError("V5A screen improperly authorizes a later stage")
    contract = load_document(CONTRACT)
    vertices = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    expected = reconstruct(vertices)
    payloads = proof["local"]["payloads"]
    local_identity = max(relative_inf(decode_array(payloads[name]), value) for name, value in expected.items())
    local = _local_checks(expected, vertices)
    construction = local_identity <= 3.0e-13
    macro_identity = 0.0
    macro_hard = 0.0
    macro_count = 0
    macro = proof.get("macrocell", {})
    if local["passed"] and macro:
        sections = dict(zip(("membrane", "bending", "shear"), _constitutive()))
        for size in (1, 2, 4):
            variants = ("all_s3",) if size == 1 else ("all_s3", "isolated", "strip")
            for diagonal in ("slash", "backslash", "alternating"):
                for variant in variants:
                    made = _grid(size, diagonal, variant)
                    stored = macro["matrices"][f"{size}x{size}:{diagonal}:{variant}"]
                    macro_identity = max(macro_identity, relative_inf(decode_array(stored["condensed"]), made["condensed"]), relative_inf(decode_array(stored["q4_condensed"]), made["q4_condensed"]))
                    for name in ("membrane_x", "membrane_y", "membrane_xy", "shear_x", "shear_y", "curvature_xx", "curvature_yy", "curvature_xy"):
                        vector, component, target = _patch(made["coordinates"], name)
                        energy = float(vector @ made["total"] @ vector)
                        expected_energy = float(target @ sections[component] @ target)
                        macro_hard = max(macro_hard, abs(energy - expected_energy) / max(abs(expected_energy), 1.0))
                    macro_hard = max(macro_hard, _interface_normal_worst(made["coordinates"], made["elements"]))
                    rigid = _rigid(made["coordinates"])
                    load_error = max(
                        abs(float(rigid[:, 2] @ made["load"]) - PRESSURE),
                        abs(float(rigid[:, 3] @ made["load"]) - PRESSURE / 2.0),
                        abs(float(rigid[:, 4] @ made["load"]) + PRESSURE / 2.0),
                    ) / PRESSURE
                    macro_hard = max(macro_hard, load_error)
                    macro_count += 1
    mixed = bool(local["passed"] and macro_count == 21 and macro_identity <= 3.0e-13 and macro_hard <= 1.0e-10)
    development_identity = 0.0
    development_passed = False
    supplied_development = proof.get("development", {})
    if mixed and supplied_development:
        produced_rows = {row["record_id"]: row for row in supplied_development["records"]}
        checked_rows: dict[str, Any] = {}
        for level, fraction in DEVELOPMENT:
            row = _development(level, fraction)
            checked_rows[row["record_id"]] = row
        if produced_rows.keys() == checked_rows.keys():
            development_identity = max(0.0, *(
                abs(float.fromhex(produced_rows[key][field]) - float.fromhex(checked_rows[key][field])) / max(abs(float.fromhex(checked_rows[key][field])), 1.0)
                for key in checked_rows
                for field in ("reference_center_hex", "response_center_hex", "pl_participation_hex")
            ))
            hashes_match = all(produced_rows[key]["connectivity_sha256"] == checked_rows[key]["connectivity_sha256"] and produced_rows[key]["reference_sha256"] == checked_rows[key]["reference_sha256"] for key in checked_rows)
            response_claims_consistent = all(
                abs(
                    float.fromhex(produced_rows[key]["response_relative_error_hex"])
                    - abs(
                        float.fromhex(produced_rows[key]["response_center_hex"])
                        / float.fromhex(produced_rows[key]["reference_center_hex"])
                        - 1.0
                    )
                )
                <= 1.0e-15
                for key in checked_rows
            )
            residuals_bounded = all(
                float.fromhex(produced_rows[key]["solve_residual_relative_inf_hex"]) <= 1.0e-8
                and float.fromhex(checked_rows[key]["solve_residual_relative_inf_hex"]) <= 1.0e-8
                for key in checked_rows
            )
            development_passed = hashes_match and response_claims_consistent and residuals_bounded and development_identity <= 3.0e-12
            for fraction in (5, 10):
                coarse = float.fromhex(checked_rows[f"N20:{fraction}PCT:dispersed:slash"]["response_relative_error_hex"])
                fine = float.fromhex(checked_rows[f"N40:{fraction}PCT:dispersed:slash"]["response_relative_error_hex"])
                development_passed = development_passed and fine <= 1.02 * coarse
    construction = construction and (not macro or macro_identity <= 3.0e-13) and (not supplied_development or development_identity <= 3.0e-12)
    return {
        "authority_complete": contract.get("schema") == "anysolver.e4-pl-s3-v5a-min3-screen-contract-v1",
        "candidate_formulation_id": FORMULATION_ID,
        "construction_identity_passed": bool(construction),
        "development_identity_worst_relative_inf_hex": development_identity.hex(),
        "development_passed": bool(development_passed),
        "independent_edge_shear_worst_relative_inf_hex": local["edge_worst"].hex(),
        "independent_local_identity_worst_relative_inf_hex": local_identity.hex(),
        "independent_macrocell_hard_worst_relative_inf_hex": macro_hard.hex(),
        "independent_macrocell_identity_worst_relative_inf_hex": macro_identity.hex(),
        "independent_macrocell_record_count": macro_count,
        "independent_patch_worst_relative_error_hex": local["patch_worst"].hex(),
        "independent_physical_rank": local["ranks"]["physical"],
        "independent_pl_rank": local["ranks"]["pl"],
        "independent_total_rank": local["ranks"]["total"],
        "local_operator_passed": bool(local["passed"]),
        "mixed_interface_passed": mixed,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": CHECK_SCHEMA,
    }


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    exclusive_write(args.output, verify(load_document(args.verify_proof)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
