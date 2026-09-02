"""Bounded producer for the source-authorized V5A unrelaxed MIN3 screen.

This is research evidence.  It deliberately does not alter or import an S3
production implementation.  The interpolation follows UHM/CE/02-02
equations 2.23--2.28a (equivalently NASA/TP-2018-220079 Appendix A/B) with
``phi**2 == 1``.  The unpublished empirical relaxation coefficient is not
guessed or fitted.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import itertools
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import e4_pl_s3_mixed_mesh_manifest as mesh_manifest
import e4_pl_s3_v4a_screen_producer as q4_source
import e4_pl_s3_v4c_screen_producer as common


CONTRACT = REFERENCE / "e4_pl_s3_v5a_screen_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V5A_MIN3_UNRELAXED_FLAT_LINEAR_SCREEN_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v5a-min3-screen-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v5a-min3-screen-check-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v5a-min3-screen-aggregate-v1"
YOUNG = 210_000_000_000.0
POISSON = 0.3
THICKNESS = 0.01
PRESSURE = 1000.0
SHEAR_CORRECTION = 5.0 / 6.0
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)
PERMUTATIONS = tuple(itertools.permutations(range(3)))
DIAGONALS = ("slash", "backslash", "alternating")
DEVELOPMENT = ((20, 5), (40, 5), (20, 10), (40, 10))
THREAD_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}
MEMORY_LIMIT_BYTES = 24 * 1024**3


class ScreenError(RuntimeError):
    pass


canonical_bytes = q4_source.canonical_bytes
sha256_file = q4_source.sha256_file
load_canonical = q4_source.load_canonical
exclusive_write = q4_source.exclusive_write
array_payload = q4_source.array_payload
relative_inf = q4_source.relative_inf


def validate_authority() -> dict[str, Any]:
    contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v5a-min3-screen-contract-v1":
        raise ScreenError("unexpected V5A screen contract")
    for item in contract["frozen_inputs"]:
        path = ROOT / item["path"]
        if (
            not path.is_file()
            or path.is_symlink()
            or path.stat().st_size != item["bytes"]
            or sha256_file(path) != item["sha256"]
        ):
            raise ScreenError(f"frozen input mismatch: {path}")
    prereg = load_canonical(REFERENCE / "e4_pl_s3_v5a_preregistration_result.json")
    if (
        prereg.get("terminal")
        != "PROVISIONAL_GO_E4_PL_S3_V5A_UNRELAXED_LOCAL_INTERFACE_SCREEN"
        or prereg.get("next_gate") != "BOUNDED_V5A_UNRELAXED_MIN3_LOCAL_INTERFACE_SCREEN"
    ):
        raise ScreenError("V5A source authority does not authorize this screen")
    return contract


def _geometry(vertices: np.ndarray) -> tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    xy = np.asarray(vertices[:, :2], dtype=np.float64)
    jacobian = np.asarray((xy[1] - xy[0], xy[2] - xy[0]), dtype=np.float64)
    determinant = float(np.linalg.det(jacobian))
    if not np.isfinite(determinant) or abs(determinant) <= 1.0e-15:
        raise ScreenError("MIN3 screen triangle is degenerate")
    inverse = np.linalg.inv(jacobian)
    dr = np.asarray((-1.0, 1.0, 0.0))
    ds = np.asarray((-1.0, 0.0, 1.0))
    dx = inverse[0, 0] * dr + inverse[0, 1] * ds
    dy = inverse[1, 0] * dr + inverse[1, 1] * ds
    return xy, abs(determinant) / 2.0, dx, dy


def _shape(
    vertices: np.ndarray, barycentric: Sequence[float]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    xy, _area, dx, dy = _geometry(vertices)
    n = np.asarray(barycentric, dtype=np.float64)
    if n.shape != (3,):
        raise ScreenError("MIN3 barycentric station must have three entries")
    # UHM/CE/02-02 2.23 / NASA A.1--A.4:
    # a_i=x_k-x_j, b_i=y_j-y_k,
    # L_i=N_i(b_k N_j-b_j N_k)/2,
    # M_i=N_i(a_j N_k-a_k N_j)/2.
    a = np.empty(3)
    b = np.empty(3)
    for i, j, k in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        a[i] = xy[k, 0] - xy[j, 0]
        b[i] = xy[j, 1] - xy[k, 1]
    l = np.empty(3)
    m = np.empty(3)
    dl = np.empty((2, 3))
    dm = np.empty((2, 3))
    for i, j, k in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        l[i] = 0.5 * n[i] * (b[k] * n[j] - b[j] * n[k])
        m[i] = 0.5 * n[i] * (a[j] * n[k] - a[k] * n[j])
        for axis, derivative in enumerate((dx, dy)):
            dl[axis, i] = 0.5 * (
                derivative[i] * (b[k] * n[j] - b[j] * n[k])
                + n[i] * (b[k] * derivative[j] - b[j] * derivative[k])
            )
            dm[axis, i] = 0.5 * (
                derivative[i] * (a[j] * n[k] - a[k] * n[j])
                + n[i] * (a[j] * derivative[k] - a[k] * derivative[j])
            )
    return n, l, m, np.vstack((dx, dy)), dl, dm


def _section() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    normalized = np.asarray(
        ((1.0, POISSON, 0.0), (POISSON, 1.0, 0.0), (0.0, 0.0, (1.0 - POISSON) / 2.0))
    )
    membrane = YOUNG * THICKNESS / (1.0 - POISSON**2) * normalized
    bending = YOUNG * THICKNESS**3 / (12.0 * (1.0 - POISSON**2)) * normalized
    shear = SHEAR_CORRECTION * YOUNG / (2.0 * (1.0 + POISSON)) * THICKNESS * np.eye(2)
    return membrane, bending, shear


def _operators(vertices: np.ndarray, barycentric: Sequence[float]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n, _l, _m, derivative, dl, dm = _shape(vertices, barycentric)
    dx, dy = derivative
    membrane = np.zeros((3, 18), dtype=np.float64)
    bending = np.zeros((3, 18), dtype=np.float64)
    shear = np.zeros((2, 18), dtype=np.float64)
    for i in range(3):
        base = 6 * i
        membrane[0, base] = dx[i]
        membrane[1, base + 1] = dy[i]
        membrane[2, base] = dy[i]
        membrane[2, base + 1] = dx[i]
        bending[0, base + 4] = dx[i]
        bending[1, base + 3] = -dy[i]
        bending[2, base + 3] = -dx[i]
        bending[2, base + 4] = dy[i]
        # Source theta_x=-rx, theta_y=ry in ANYsolver shell convention.
        shear[0, base + 2] = dx[i]
        shear[0, base + 3] = -dl[0, i]
        shear[0, base + 4] = dm[0, i] + n[i]
        shear[1, base + 2] = dy[i]
        shear[1, base + 3] = -dl[1, i] - n[i]
        shear[1, base + 4] = dm[1, i]
    return membrane, bending, shear


def _pressure_load(vertices: np.ndarray, pressure: float = PRESSURE) -> np.ndarray:
    _xy, area, _dx, _dy = _geometry(vertices)
    made = np.zeros(18, dtype=np.float64)
    stations = ((2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0), (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0), (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0))
    for station in stations:
        n, l, m, _derivative, _dl, _dm = _shape(vertices, station)
        for i in range(3):
            made[6 * i + 2] += pressure * area * n[i] / 3.0
            made[6 * i + 3] -= pressure * area * l[i] / 3.0
            made[6 * i + 4] += pressure * area * m[i] / 3.0
    return made


def min3_components(
    coordinates: Sequence[Sequence[float]], *, normal: Sequence[float] = NORMAL
) -> dict[str, Any]:
    vertices = np.asarray(coordinates, dtype=np.float64)
    if vertices.shape == (3, 2):
        vertices = np.column_stack((vertices, np.zeros(3)))
    if vertices.shape != (3, 3) or not np.all(np.isfinite(vertices)):
        raise ScreenError("V5A vertices must be finite 3x2 or 3x3 coordinates")
    normal_array = np.asarray(normal, dtype=np.float64)
    if normal_array.shape != (3,) or not np.isfinite(normal_array).all() or np.linalg.norm(normal_array) == 0.0:
        raise ScreenError("V5A normal must be a finite nonzero vector")
    _xy, area, _dx, _dy = _geometry(vertices)
    a_section, d_section, s_section = _section()
    membrane_b, bending_b, _ = _operators(vertices, (1.0 / 3.0,) * 3)
    membrane = area * membrane_b.T @ a_section @ membrane_b
    bending = area * bending_b.T @ d_section @ bending_b
    shear = np.zeros((18, 18), dtype=np.float64)
    for station in ((2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0), (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0), (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0)):
        _bm, _bb, bs = _operators(vertices, station)
        shear += area / 3.0 * bs.T @ s_section @ bs
    constraint, gram, pl, drill_scale = common._native_pl(vertices)
    physical = membrane + bending + shear
    total = physical + pl
    return {
        "bending": 0.5 * (bending + bending.T),
        "drill_scale": drill_scale,
        "membrane": 0.5 * (membrane + membrane.T),
        "physical": 0.5 * (physical + physical.T),
        "pl": pl,
        "pl_constraint": constraint,
        "pl_gram": gram,
        "pressure_load": _pressure_load(vertices),
        "shear": 0.5 * (shear + shear.T),
        "total": 0.5 * (total + total.T),
    }


def _patch_modes(vertices: np.ndarray) -> dict[str, tuple[np.ndarray, str, np.ndarray]]:
    definitions = {
        "membrane_x": (lambda x, y: (x, 0, 0, 0, 0, 0), "membrane", np.asarray((1.0, 0.0, 0.0))),
        "membrane_y": (lambda x, y: (0, y, 0, 0, 0, 0), "membrane", np.asarray((0.0, 1.0, 0.0))),
        "membrane_xy": (lambda x, y: (y / 2.0, x / 2.0, 0, 0, 0, 0), "membrane", np.asarray((0.0, 0.0, 1.0))),
        "shear_x": (lambda x, y: (0, 0, x, 0, 0, 0), "shear", np.asarray((1.0, 0.0))),
        "shear_y": (lambda x, y: (0, 0, y, 0, 0, 0), "shear", np.asarray((0.0, 1.0))),
        "curvature_xx": (lambda x, y: (0, 0, -x * x / 2.0, 0, x, 0), "bending", np.asarray((1.0, 0.0, 0.0))),
        "curvature_yy": (lambda x, y: (0, 0, -y * y / 2.0, -y, 0, 0), "bending", np.asarray((0.0, 1.0, 0.0))),
        "curvature_xy": (lambda x, y: (0, 0, -x * y / 2.0, -x / 2.0, y / 2.0, 0), "bending", np.asarray((0.0, 0.0, 1.0))),
    }
    return {
        name: (
            np.asarray([value for x, y, _z in vertices for value in function(x, y)], dtype=np.float64),
            component,
            target,
        )
        for name, (function, component, target) in definitions.items()
    }


def _rigid_modes(vertices: np.ndarray) -> np.ndarray:
    made = np.zeros((6 * len(vertices), 6), dtype=np.float64)
    for node, (x, y, _z) in enumerate(vertices):
        base = 6 * node
        made[base, 0] = made[base + 1, 1] = made[base + 2, 2] = 1.0
        made[base + 2, 3], made[base + 3, 3] = y, 1.0
        made[base + 2, 4], made[base + 4, 4] = -x, 1.0
        made[base, 5], made[base + 1, 5], made[base + 5, 5] = -y, x, 1.0
    return made


def _edge_shear_worst(vertices: np.ndarray) -> float:
    worst = 0.0
    for left, right, opposite in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        tangent = vertices[right, :2] - vertices[left, :2]
        tangent /= np.linalg.norm(tangent)
        rows = []
        for fraction in (0.0, 0.5, 1.0):
            bary = np.zeros(3)
            bary[left], bary[right], bary[opposite] = 1.0 - fraction, fraction, 0.0
            _bm, _bb, bs = _operators(vertices, bary)
            rows.append(tangent @ bs)
        worst = max(worst, relative_inf(rows[1], rows[0]), relative_inf(rows[2], rows[0]))
    return worst


def local_proof() -> dict[str, Any]:
    vertices = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    made = min3_components(vertices)
    a_section, d_section, s_section = _section()
    sections = {"membrane": a_section, "bending": d_section, "shear": s_section}
    _xy, area, _dx, _dy = _geometry(vertices)
    shape_worst = 0.0
    for station in ((1.0 / 3.0,) * 3, (0.7, 0.2, 0.1), (0.0, 0.4, 0.6)):
        n, l, m, _derivative, _dl, _dm = _shape(vertices, station)
        shape_worst = max(shape_worst, abs(float(np.sum(n)) - 1.0), abs(float(np.sum(l))), abs(float(np.sum(m))))
    patch_rows: dict[str, Any] = {}
    patch_worst = 0.0
    for name, (vector, component, target) in _patch_modes(vertices).items():
        energy = float(vector @ made[component] @ vector)
        expected = float(area * target @ sections[component] @ target)
        error = abs(energy - expected) / max(abs(expected), 1.0)
        operator_index = {"membrane": 0, "bending": 1, "shear": 2}[component]
        field_error = 0.0
        for station in ((2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0), (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0), (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0)):
            field_error = max(field_error, relative_inf(_operators(vertices, station)[operator_index] @ vector, target))
        patch_rows[name] = {"energy_hex": energy.hex(), "expected_energy_hex": expected.hex(), "field_relative_inf_hex": field_error.hex(), "relative_error_hex": error.hex()}
        patch_worst = max(patch_worst, error, field_error)
    d3_worst = 0.0
    reversal_worst = 0.0
    for order in PERMUTATIONS:
        permutation = q4_source._block_permutation(order)
        permuted = min3_components(vertices[np.asarray(order)])
        d3_worst = max(d3_worst, relative_inf(permutation.T @ permuted["total"] @ permutation, made["total"]))
        reversed_made = min3_components(vertices[np.asarray(order)], normal=-NORMAL)
        reversal_worst = max(reversal_worst, relative_inf(permutation.T @ reversed_made["total"] @ permutation, made["total"]))
    rigid = float(np.linalg.norm(made["total"] @ _rigid_modes(vertices), ord=np.inf) / max(np.linalg.norm(made["total"], ord=np.inf), 1.0))
    ranks = {name: common._rank(made[name], 1.0e-10) for name in ("physical", "pl", "total")}
    first, second = np.arange(1.0, 19.0), np.arange(18.0, 0.0, -1.0)
    work = abs(float(first @ made["total"] @ second) - float(second @ made["total"] @ first)) / max(abs(float(first @ made["total"] @ second)), 1.0)
    load = made["pressure_load"]
    rigid_modes = _rigid_modes(vertices)
    centroid = np.mean(vertices[:, :2], axis=0)
    load_errors = (
        abs(float(rigid_modes[:, 2] @ load) - PRESSURE * area),
        abs(float(rigid_modes[:, 3] @ load) - PRESSURE * area * centroid[1]),
        abs(float(rigid_modes[:, 4] @ load) + PRESSURE * area * centroid[0]),
    )
    load_worst = max(load_errors) / max(PRESSURE * area, 1.0)
    diagnostics = {
        "d3_worst_relative_inf_hex": d3_worst.hex(),
        "director_reversal_worst_relative_inf_hex": reversal_worst.hex(),
        "edge_tangential_shear_worst_relative_inf_hex": _edge_shear_worst(vertices).hex(),
        "load_work_worst_relative_inf_hex": load_worst.hex(),
        "patch_worst_relative_error_hex": patch_worst.hex(),
        "physical_rank": ranks["physical"],
        "pl_rank": ranks["pl"],
        "rigid_residual_relative_inf_hex": rigid.hex(),
        "shape_identity_worst_absolute_hex": shape_worst.hex(),
        "symmetry_relative_inf_hex": relative_inf(made["total"], made["total"].T).hex(),
        "total_rank": ranks["total"],
        "work_conjugacy_relative_hex": work.hex(),
    }
    diagnostics["gate_passed"] = bool(
        ranks == {"physical": 9, "pl": 3, "total": 12}
        and max(shape_worst, patch_worst, rigid, load_worst, work) <= 3.0e-12
        and float.fromhex(diagnostics["edge_tangential_shear_worst_relative_inf_hex"]) <= 3.0e-12
        and d3_worst <= 3.0e-12
        and reversal_worst <= 3.0e-12
        and float.fromhex(diagnostics["symmetry_relative_inf_hex"]) <= 3.0e-13
    )
    payloads = {name: array_payload(np.asarray(value)) for name, value in made.items() if isinstance(value, np.ndarray)}
    return {"diagnostics": diagnostics, "patch_modes": patch_rows, "payloads": payloads}


def _scatter_dense(target: np.ndarray, local: np.ndarray, nodes: Sequence[int]) -> None:
    for i, node_i in enumerate(nodes):
        for j, node_j in enumerate(nodes):
            target[6 * node_i : 6 * node_i + 6, 6 * node_j : 6 * node_j + 6] += local[6 * i : 6 * i + 6, 6 * j : 6 * j + 6]


def _scatter_vector(target: np.ndarray, local: np.ndarray, nodes: Sequence[int]) -> None:
    for i, node in enumerate(nodes):
        target[6 * node : 6 * node + 6] += local[6 * i : 6 * i + 6]


def _grid(size: int, diagonal: str, variant: str) -> dict[str, Any]:
    count = (size + 1) ** 2
    coordinates = np.asarray(tuple((i / size, j / size, 0.0) for j in range(size + 1) for i in range(size + 1)))
    total = np.zeros((6 * count, 6 * count), dtype=np.float64)
    load = np.zeros(6 * count, dtype=np.float64)
    q4_only = np.zeros_like(total)
    elements: list[tuple[int, ...]] = []
    for j in range(size):
        for i in range(size):
            q4_nodes = (j * (size + 1) + i, j * (size + 1) + i + 1, (j + 1) * (size + 1) + i + 1, (j + 1) * (size + 1) + i)
            q4 = q4_source._qualified_q4_components(coordinates[np.asarray(q4_nodes)], NORMAL)["total"]
            _scatter_dense(q4_only, q4, q4_nodes)
            split = variant == "all_s3" or (variant == "isolated" and i == size // 2 and j == size // 2) or (variant == "strip" and i == size // 2)
            if split:
                for triangle in common._cell_triangles(i, j, size, diagonal):
                    made = min3_components(coordinates[np.asarray(triangle)])
                    _scatter_dense(total, made["total"], triangle)
                    _scatter_vector(load, made["pressure_load"], triangle)
                    elements.append(tuple(triangle))
            else:
                _scatter_dense(total, q4, q4_nodes)
                area = 1.0 / size**2
                q4_load = np.zeros(24)
                q4_load[2::6] = PRESSURE * area / 4.0
                _scatter_vector(load, q4_load, q4_nodes)
                elements.append(tuple(q4_nodes))
    boundary_nodes = tuple(node for node in range(count) if node % (size + 1) in {0, size} or node // (size + 1) in {0, size})
    interior_nodes = tuple(node for node in range(count) if node not in boundary_nodes)
    boundary = np.concatenate([np.arange(6 * node, 6 * node + 6) for node in boundary_nodes])
    interior = np.concatenate([np.arange(6 * node, 6 * node + 6) for node in interior_nodes]) if interior_nodes else np.asarray([], dtype=np.intp)
    condensed = total[np.ix_(boundary, boundary)]
    q4_condensed = q4_only[np.ix_(boundary, boundary)]
    if interior.size:
        bi = total[np.ix_(boundary, interior)]
        condensed = condensed - bi @ np.linalg.solve(total[np.ix_(interior, interior)], bi.T)
        qbi = q4_only[np.ix_(boundary, interior)]
        q4_condensed = q4_condensed - qbi @ np.linalg.solve(q4_only[np.ix_(interior, interior)], qbi.T)
    return {
        "boundary": boundary,
        "boundary_coordinates": coordinates[np.asarray(boundary_nodes)],
        "condensed": 0.5 * (condensed + condensed.T),
        "coordinates": coordinates,
        "elements": elements,
        "interior": interior,
        "load": load,
        "q4_condensed": 0.5 * (q4_condensed + q4_condensed.T),
        "total": total,
    }


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
            raise ScreenError("macrocell edge has invalid ownership")
    return worst


def _grid_patch_vector(coordinates: np.ndarray, name: str) -> tuple[np.ndarray, str, np.ndarray]:
    return _patch_modes(coordinates)[name]


def macrocell_proof() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    matrices: dict[str, Any] = {}
    hard_worst = 0.0
    dtn_worst = 0.0
    a_section, d_section, s_section = _section()
    sections = {"membrane": a_section, "bending": d_section, "shear": s_section}
    for size in (1, 2, 4):
        variants = ("all_s3",) if size == 1 else ("all_s3", "isolated", "strip")
        for diagonal in DIAGONALS:
            for variant in variants:
                made = _grid(size, diagonal, variant)
                key = f"{size}x{size}:{diagonal}:{variant}"
                matrices[key] = {"condensed": array_payload(made["condensed"]), "q4_condensed": array_payload(made["q4_condensed"])}
                patch_rows: dict[str, Any] = {}
                interface_error = _interface_normal_worst(made["coordinates"], made["elements"])
                hard_worst = max(hard_worst, interface_error)
                for name in ("membrane_x", "membrane_y", "membrane_xy", "shear_x", "shear_y", "curvature_xx", "curvature_yy", "curvature_xy"):
                    vector, component, target = _grid_patch_vector(made["coordinates"], name)
                    energy = float(vector @ made["total"] @ vector)
                    expected = float(target @ sections[component] @ target)
                    energy_error = abs(energy - expected) / max(abs(expected), 1.0)
                    interior_error = 0.0
                    if made["interior"].size:
                        action = made["total"] @ vector
                        interior_error = float(np.linalg.norm(action[made["interior"]], ord=np.inf) / max(np.linalg.norm(action[made["boundary"]], ord=np.inf), 1.0))
                    patch_rows[name] = {"energy_relative_error_hex": energy_error.hex(), "interior_action_classifying": False, "interior_action_relative_inf_hex": interior_error.hex()}
                    hard_worst = max(hard_worst, energy_error)
                rigid = _rigid_modes(made["coordinates"])
                load_work = (
                    abs(float(rigid[:, 2] @ made["load"]) - PRESSURE),
                    abs(float(rigid[:, 3] @ made["load"]) - PRESSURE / 2.0),
                    abs(float(rigid[:, 4] @ made["load"]) + PRESSURE / 2.0),
                )
                load_error = max(load_work) / PRESSURE
                hard_worst = max(hard_worst, load_error)
                dtn = relative_inf(made["condensed"], made["q4_condensed"])
                dtn_worst = max(dtn_worst, dtn)
                records.append({"diagonal": diagonal, "dtn_q4_relative_inf_hex": dtn.hex(), "interface_action_reaction_relative_inf_hex": interface_error.hex(), "load_work_relative_error_hex": load_error.hex(), "patch_modes": patch_rows, "size": size, "variant": variant})
    return {
        "diagnostics": {
            "dtn_q4_diagnostic_worst_relative_inf_hex": dtn_worst.hex(),
            "gate_passed": hard_worst <= 1.0e-10,
            "hard_patch_interface_worst_relative_inf_hex": hard_worst.hex(),
            "record_count": len(records),
        },
        "matrices": matrices,
        "records": records,
    }


def _development_record(level: int, fraction: int) -> dict[str, Any]:
    from scipy import sparse
    from scipy.sparse.linalg import spsolve
    from e4_pl_s3_v2_flat_funnel_producer import mindlin_nodal_reference

    base = mesh_manifest.selected_base_cells("dispersed", fraction * 4)
    split = mesh_manifest.expanded_split_cells(base, level)
    count = (level + 1) ** 2
    coordinates = np.asarray(tuple((i / level, j / level, 0.0) for j in range(level + 1) for i in range(level + 1)))
    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    pl_values: list[float] = []
    load = np.zeros(6 * count)
    h = 1.0 / level
    q4_coords = np.asarray(((0.0, 0.0, 0.0), (h, 0.0, 0.0), (h, h, 0.0), (0.0, h, 0.0)))
    q4 = q4_source._qualified_q4_components(q4_coords, NORMAL)
    q4_load = np.zeros(24)
    q4_load[2::6] = PRESSURE * h * h / 4.0
    s3_cache: dict[tuple[int, ...], dict[str, Any]] = {}
    for j in range(level):
        for i in range(level):
            entries: list[tuple[tuple[int, ...], dict[str, Any], np.ndarray]] = []
            if (i, j) in split:
                for triangle in common._cell_triangles(i, j, level, "slash"):
                    signature = tuple(node - triangle[0] for node in triangle)
                    cached = s3_cache.get(signature)
                    if cached is None:
                        origin = coordinates[triangle[0]]
                        cached = min3_components(coordinates[np.asarray(triangle)] - origin)
                        s3_cache[signature] = cached
                    entries.append((triangle, cached, cached["pressure_load"]))
            else:
                nodes = (j * (level + 1) + i, j * (level + 1) + i + 1, (j + 1) * (level + 1) + i + 1, (j + 1) * (level + 1) + i)
                entries.append((nodes, q4, q4_load))
            for nodes, made, local_load in entries:
                dofs = np.asarray([6 * node + dof for node in nodes for dof in range(6)], dtype=np.intp)
                rr, cc = np.meshgrid(dofs, dofs, indexing="ij")
                rows.extend(rr.reshape(-1).tolist())
                columns.extend(cc.reshape(-1).tolist())
                values.extend(np.asarray(made["total"]).reshape(-1).tolist())
                pl_values.extend(np.asarray(made["pl"] if "pl" in made else np.zeros_like(made["total"])).reshape(-1).tolist())
                np.add.at(load, dofs, local_load)
    shape = (6 * count, 6 * count)
    stiffness = sparse.coo_matrix((values, (rows, columns)), shape=shape).tocsr()
    pl_matrix = sparse.coo_matrix((pl_values, (rows, columns)), shape=shape).tocsr()
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
    free = np.asarray([index for index in range(shape[0]) if index not in fixed], dtype=np.intp)
    displacement = np.zeros(shape[0])
    displacement[free] = spsolve(stiffness[free][:, free], load[free])
    residual = float(np.linalg.norm((stiffness @ displacement - load)[free], ord=np.inf) / max(np.linalg.norm(load[free], ord=np.inf), 1.0))
    reference, reference_sha, reference_center = mindlin_nodal_reference(level)
    center_node = (level // 2) * (level + 1) + level // 2
    center = float(displacement[6 * center_node + 2])
    relative_error = abs(center / reference_center - 1.0)
    total_energy = float(displacement @ stiffness @ displacement)
    pl_energy = float(displacement @ pl_matrix @ displacement)
    return {
        "connectivity_sha256": mesh_manifest.connectivity_sha256(level, split, "slash"),
        "level": level,
        "pl_participation_hex": (abs(pl_energy) / max(abs(total_energy), 1.0)).hex(),
        "record_id": f"N{level}:{fraction}PCT:dispersed:slash",
        "reference_center_hex": float(reference_center).hex(),
        "reference_sha256": reference_sha,
        "response_center_hex": center.hex(),
        "response_relative_error_hex": relative_error.hex(),
        "solve_residual_relative_inf_hex": residual.hex(),
    }


def development_proof() -> dict[str, Any]:
    records = [_development_record(level, fraction) for level, fraction in DEVELOPMENT]
    by_id = {row["record_id"]: row for row in records}
    worst_factor = 0.0
    passed = True
    for fraction in (5, 10):
        coarse = float.fromhex(by_id[f"N20:{fraction}PCT:dispersed:slash"]["response_relative_error_hex"])
        fine = float.fromhex(by_id[f"N40:{fraction}PCT:dispersed:slash"]["response_relative_error_hex"])
        factor = fine / max(coarse, np.finfo(float).tiny)
        worst_factor = max(worst_factor, factor)
        passed = passed and fine <= 1.02 * coarse
    passed = passed and all(float.fromhex(row["solve_residual_relative_inf_hex"]) <= 1.0e-8 for row in records)
    return {"diagnostics": {"gate_passed": bool(passed), "record_count": len(records), "successive_response_factor_worst_hex": worst_factor.hex()}, "records": records}


def produce_proof() -> dict[str, Any]:
    validate_authority()
    local = local_proof()
    base = {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "contract_sha256": sha256_file(CONTRACT),
        "local": local,
        "production_boundary": {"anymesh_untouched": True, "default_q4_formulation": "e4-pl", "default_s3_formulation": "legacy-s3", "q4_mechanics_unchanged": True},
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "relaxation_policy": "PHI_SQUARED_EXACTLY_ONE_FOR_SCREEN_ONLY",
        "schema": PROOF_SCHEMA,
        "stage4a_rerun_authorized": False,
    }
    if not local["diagnostics"]["gate_passed"]:
        return base | {"development": {}, "later_stages": "NOT_EXECUTED_LOCAL_GATE_FAILED", "macrocell": {}}
    macrocell = macrocell_proof()
    if not macrocell["diagnostics"]["gate_passed"]:
        return base | {"development": {}, "later_stages": "NOT_EXECUTED_MACROCELL_GATE_FAILED", "macrocell": macrocell}
    development = development_proof()
    return base | {
        "development": development,
        "later_stages": "RELAXATION_AUTHORITY_REQUIRED" if development["diagnostics"]["gate_passed"] else "DEVELOPMENT_GATE_FAILED",
        "macrocell": macrocell,
    }


def adjudicate(*, identical: bool, report: Mapping[str, Any]) -> str:
    if not identical or not report.get("authority_complete") or not report.get("construction_identity_passed"):
        return "BLOCKED_E4_PL_S3_V5A_PROCESS_OR_EVIDENCE"
    if not report.get("local_operator_passed"):
        return "NO_GO_E4_PL_S3_V5A_SOURCE_OR_LOCAL_OPERATOR"
    if not report.get("mixed_interface_passed") or not report.get("development_passed"):
        return "NO_GO_E4_PL_S3_V5A_MIXED_INTERFACE"
    return "UNCLASSIFIED_E4_PL_S3_V5A_RELAXATION_AUTHORITY_REQUIRED"


def _run_child(command: list[str], timeout_seconds: int) -> None:
    common._run_child(command, timeout_seconds)


def run_bounded(output_root: Path, *, timeout_seconds: int = 600, wave_timeout_seconds: int = 1800) -> dict[str, Any]:
    validate_authority()
    if timeout_seconds not in range(1, 601) or wave_timeout_seconds not in range(1, 1801):
        raise ScreenError("requested limits exceed the frozen process bounds")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=False)
    progress = root / "progress.jsonl"
    progress.touch(exist_ok=False)
    deadline = time.monotonic() + wave_timeout_seconds
    checker = REFERENCE / "e4_pl_s3_v5a_screen_checker.py"
    cycles: list[dict[str, Any]] = []
    terminal = "BLOCKED_E4_PL_S3_V5A_PROCESS_OR_EVIDENCE"
    try:
        for cycle in (1, 2):
            cycle_root = root / f"cycle-{cycle}"
            cycle_root.mkdir()
            proof = cycle_root / "proof.json"
            checks = (cycle_root / "checker-a.json", cycle_root / "checker-b.json")
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "INITIALIZATION", "sequence": 0}))
            remaining = int(max(1, min(timeout_seconds, deadline - time.monotonic())))
            _run_child([sys.executable, str(Path(__file__).resolve()), "--emit-proof", "--output", str(proof)], remaining)
            commands = [[sys.executable, str(checker), "--verify-proof", str(proof), "--output", str(path)] for path in checks]
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(_run_child, command, int(max(1, min(timeout_seconds, deadline - time.monotonic())))) for command in commands]
                for future in futures:
                    future.result()
            identical = checks[0].read_bytes() == checks[1].read_bytes()
            report = load_canonical(checks[0])
            terminal = adjudicate(identical=identical, report=report)
            cycles.append({"checker_replicas_byte_identical": identical, "checker_sha256": sha256_file(checks[0]), "cycle": cycle, "proof_bytes": proof.stat().st_size, "proof_sha256": sha256_file(proof), "terminal": terminal})
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "CYCLE_COMPLETE", "sequence": 1}))
        if cycles[0]["proof_sha256"] != cycles[1]["proof_sha256"] or cycles[0]["checker_sha256"] != cycles[1]["checker_sha256"]:
            terminal = "BLOCKED_E4_PL_S3_V5A_PROCESS_OR_EVIDENCE"
    except BaseException as exc:
        cycles.append({"error_class": type(exc).__name__, "status": "FAILED_BOUNDED_CHILD"})
        terminal = "BLOCKED_E4_PL_S3_V5A_PROCESS_OR_EVIDENCE"
    aggregate = {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "contract_sha256": sha256_file(CONTRACT),
        "cycles": cycles,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "relaxed_successor_screen_authorized": terminal == "UNCLASSIFIED_E4_PL_S3_V5A_RELAXATION_AUTHORITY_REQUIRED",
        "schema": AGGREGATE_SCHEMA,
        "stage4a_rerun_authorized": False,
        "terminal": terminal,
    }
    exclusive_write(root / "aggregate.json", aggregate)
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-proof", action="store_true")
    mode.add_argument("--run-bounded", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--wave-timeout-seconds", type=int, default=1800)
    args = parser.parse_args(argv)
    if args.emit_proof:
        if args.output is None:
            raise ScreenError("--output is required")
        exclusive_write(args.output, produce_proof())
    else:
        if args.output_root is None:
            raise ScreenError("--output-root is required")
        run_bounded(args.output_root, timeout_seconds=args.timeout_seconds, wave_timeout_seconds=args.wave_timeout_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
