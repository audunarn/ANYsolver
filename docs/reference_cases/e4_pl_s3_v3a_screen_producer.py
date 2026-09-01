"""Bounded source-native MiSP3 local and mixed-macrocell screen.

This research-only producer implements the flat, linear, isotropic plate
operator authorized by the V3 equation maps.  It does not import either failed
S3 mechanics implementation and it never participates in production routing.
"""

from __future__ import annotations

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT_PATH = REFERENCE / "e4_pl_s3_v3a_implementation_screen_contract.json"
for _entry in (str(SRC), str(REFERENCE)):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

FORMULATION_ID = "CANDIDATE_E4_PL_S3_V3A_MISP3_HR_FLAT_LINEAR_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v3a-implementation-screen-proof-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v3a-implementation-screen-aggregate-v1"
YOUNG = 210_000_000_000.0
POISSON = 0.3
THICKNESS = 0.01
PRESSURE = 1000.0
SHEAR_CORRECTION = 5.0 / 6.0
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)
DIAGONALS = ("slash", "backslash", "alternating")
PERMUTATIONS = tuple(itertools.permutations(range(3)))
DEVELOPMENT_IDS = (
    "N20:5PCT:dispersed:slash",
    "N40:5PCT:dispersed:slash",
    "N20:10PCT:dispersed:slash",
    "N40:10PCT:dispersed:slash",
)
THREAD_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}
MEMORY_LIMIT_BYTES = 24 * 1024**3


class ScreenError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def _reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise ScreenError(f"duplicate JSON key {key!r}")
        made[key] = value
    return made


def load_canonical(path: Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_reject_duplicate,
        parse_constant=lambda token: (_ for _ in ()).throw(ScreenError(token)),
    )
    if raw != canonical_bytes(value):
        raise ScreenError(f"{path.name} is not canonical JSON")
    return value


def exclusive_write(path: Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def array_payload(value: np.ndarray) -> dict[str, Any]:
    made = np.asarray(value, dtype=np.float64)
    values = [float(item).hex() for item in made.reshape(-1)]
    return {
        "shape": list(made.shape),
        "sha256": sha256_bytes(canonical_bytes(values)),
        "values_hex": values,
    }


def relative_inf(actual: np.ndarray, expected: np.ndarray) -> float:
    numerator = float(np.linalg.norm(actual - expected, ord=np.inf))
    denominator = max(float(np.linalg.norm(expected, ord=np.inf)), 1.0)
    return numerator / denominator


def validate_authority() -> dict[str, Any]:
    contract = load_canonical(CONTRACT_PATH)
    if contract.get("schema") != "anysolver.e4-pl-s3-v3a-implementation-screen-contract-v1":
        raise ScreenError("unexpected implementation-screen contract schema")
    if contract.get("candidate", {}).get("formulation_id") != FORMULATION_ID:
        raise ScreenError("candidate identity mismatch")
    for item in contract.get("frozen_inputs", []):
        path = ROOT / str(item["path"])
        if not path.is_file() or path.is_symlink():
            raise ScreenError(f"frozen input is not a regular file: {path}")
        if path.stat().st_size != int(item["bytes"]) or sha256_file(path) != item["sha256"]:
            raise ScreenError(f"frozen input identity mismatch: {path}")
    equation = load_canonical(REFERENCE / "e4_pl_s3_v3_equation_authority_result.json")
    if (
        equation.get("terminal") != "PASS_E4_PL_S3_V3A_EQUATION_AUTHORITY"
        or equation.get("next_gate_authorized") is not True
        or equation.get("stage4a_rerun_authorized") is not False
    ):
        raise ScreenError("equation-authority predecessor does not authorize this screen")
    return contract


def _triangle_geometry(coordinates: Sequence[Sequence[float]]) -> tuple[np.ndarray, float, np.ndarray]:
    xy = np.asarray(coordinates, dtype=np.float64)
    if xy.shape != (3, 2) or not np.all(np.isfinite(xy)):
        raise ScreenError("MiSP3 coordinates must be a finite 3x2 array")
    jacobian = np.column_stack((xy[1] - xy[0], xy[2] - xy[0]))
    determinant = float(np.linalg.det(jacobian))
    scale = max(float(np.max(np.sum((xy[:, None] - xy[None, :]) ** 2, axis=2))), 1.0)
    if abs(determinant) <= 64.0 * np.finfo(np.float64).eps * scale:
        raise ScreenError("MiSP3 triangle is degenerate")
    natural = np.asarray(((-1.0, -1.0), (1.0, 0.0), (0.0, 1.0)))
    gradients = natural @ np.linalg.inv(jacobian)
    return xy, 0.5 * abs(determinant), gradients


def _section_matrices(
    elastic_modulus: float,
    poisson_ratio: float,
    thickness: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    isotropic = np.asarray(
        (
            (1.0, poisson_ratio, 0.0),
            (poisson_ratio, 1.0, 0.0),
            (0.0, 0.0, 0.5 * (1.0 - poisson_ratio)),
        ),
        dtype=np.float64,
    )
    membrane = elastic_modulus * thickness / (1.0 - poisson_ratio**2) * isotropic
    bending = (
        elastic_modulus
        * thickness**3
        / (12.0 * (1.0 - poisson_ratio**2))
        * isotropic
    )
    shear = SHEAR_CORRECTION * elastic_modulus / (2.0 * (1.0 + poisson_ratio)) * thickness
    return membrane, bending, float(shear)


def _reduction_coefficients(xy: np.ndarray, gradients: np.ndarray) -> np.ndarray:
    """Return coefficients of R_h(grad w-beta) for every nodal flexural DOF."""

    edge_matrix = np.empty((3, 3), dtype=np.float64)
    right = np.empty((3, 9), dtype=np.float64)
    for edge, (first, second) in enumerate(((0, 1), (1, 2), (2, 0))):
        delta = xy[second] - xy[first]
        midpoint = 0.5 * (xy[first] + xy[second])
        edge_matrix[edge] = (delta[0], delta[1], midpoint[1] * delta[0] - midpoint[0] * delta[1])
        for node in range(3):
            occupancy = 0.5 * (float(node == first) + float(node == second))
            right[edge, 3 * node] = float(gradients[node] @ delta)
            right[edge, 3 * node + 1] = -occupancy * delta[0]
            right[edge, 3 * node + 2] = -occupancy * delta[1]
    return np.linalg.solve(edge_matrix, right)


def misp3_flexural_blocks(
    coordinates: Sequence[Sequence[float]],
    *,
    elastic_modulus: float = YOUNG,
    poisson_ratio: float = POISSON,
    thickness: float = THICKNESS,
) -> dict[str, np.ndarray | float]:
    """Construct the source-derived H, G, and condensed MiSP3 flexural block."""

    xy, area, gradients = _triangle_geometry(coordinates)
    _membrane, bending, shear = _section_matrices(elastic_modulus, poisson_ratio, thickness)
    mass = area / 12.0 * np.asarray(((2.0, 1.0, 1.0), (1.0, 2.0, 1.0), (1.0, 1.0, 2.0)))
    bending_inverse = np.linalg.inv(bending)
    h_bending = np.zeros((9, 9), dtype=np.float64)
    h_shear = np.zeros((9, 9), dtype=np.float64)
    divergences = np.zeros((9, 2), dtype=np.float64)
    for node, (dx, dy) in enumerate(gradients):
        divergences[3 * node] = (dx, 0.0)
        divergences[3 * node + 1] = (0.0, dy)
        divergences[3 * node + 2] = (dy, dx)
    for left_node in range(3):
        for right_node in range(3):
            for left_component in range(3):
                for right_component in range(3):
                    left = 3 * left_node + left_component
                    right = 3 * right_node + right_component
                    h_bending[left, right] = mass[left_node, right_node] * bending_inverse[left_component, right_component]
            block_left = slice(3 * left_node, 3 * left_node + 3)
            block_right = slice(3 * right_node, 3 * right_node + 3)
            h_shear[block_left, block_right] = area / shear * (divergences[block_left] @ divergences[block_right].T)
    h_total = h_bending + h_shear

    reduction = _reduction_coefficients(xy, gradients)
    centroid = np.mean(xy, axis=0)
    # The reduction-space field is z=(a+c*y,b-c*x).
    z_values = np.vstack(
        (
            reduction[0] + centroid[1] * reduction[2],
            reduction[1] - centroid[0] * reduction[2],
        )
    )
    coupling = np.zeros((9, 9), dtype=np.float64)
    for moment_node in range(3):
        for component in range(3):
            row = 3 * moment_node + component
            for flex_node, (dx, dy) in enumerate(gradients):
                curvature_x = np.asarray((dx, 0.0, dy))
                curvature_y = np.asarray((0.0, dy, dx))
                coupling[row, 3 * flex_node + 1] += area / 3.0 * curvature_x[component]
                coupling[row, 3 * flex_node + 2] += area / 3.0 * curvature_y[component]
            coupling[row] -= area * (divergences[row] @ z_values)
    transfer = np.linalg.solve(h_total, coupling)
    condensed = coupling.T @ transfer
    condensed_bending = transfer.T @ h_bending @ transfer
    condensed_shear = transfer.T @ h_shear @ transfer
    condensed = 0.5 * (condensed + condensed.T)
    return {
        "area": area,
        "gradients": gradients,
        "H_bending": h_bending,
        "H_shear": h_shear,
        "H": h_total,
        "G": coupling,
        "reduction": reduction,
        "moment_transfer": transfer,
        "bending": 0.5 * (condensed_bending + condensed_bending.T),
        "shear": 0.5 * (condensed_shear + condensed_shear.T),
        "condensed": condensed,
    }


def _membrane_operator(gradients: np.ndarray) -> np.ndarray:
    made = np.zeros((3, 18), dtype=np.float64)
    for node, (dx, dy) in enumerate(gradients):
        base = 6 * node
        made[0, base] = dx
        made[1, base + 1] = dy
        made[2, base] = dy
        made[2, base + 1] = dx
    return made


def _plate_embedding() -> np.ndarray:
    made = np.zeros((9, 18), dtype=np.float64)
    for node in range(3):
        made[3 * node, 6 * node + 2] = 1.0
        made[3 * node + 1, 6 * node + 4] = 1.0
        made[3 * node + 2, 6 * node + 3] = -1.0
    return made


def _pl_completion(area: float, gradients: np.ndarray, membrane: np.ndarray) -> np.ndarray:
    constraint = np.zeros((3, 18), dtype=np.float64)
    for row in range(3):
        for node, (dx, dy) in enumerate(gradients):
            constraint[row, 6 * node] = 0.5 * dy
            constraint[row, 6 * node + 1] = -0.5 * dx
        constraint[row, 6 * row + 5] = 1.0
    p = np.asarray(((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0)))
    metric = np.diag((2.0, 0.5))
    eigenvalues = np.linalg.eigvals(np.linalg.solve(metric, p.T @ membrane @ p))
    drill_scale = 0.5 * float(np.min(np.real(eigenvalues)))
    shape_mass = area / 12.0 * np.asarray(((2.0, 1.0, 1.0), (1.0, 2.0, 1.0), (1.0, 1.0, 2.0)))
    return drill_scale * constraint.T @ shape_mass @ constraint


def shell_components(
    coordinates: Sequence[Sequence[float]],
    *,
    elastic_modulus: float = YOUNG,
    poisson_ratio: float = POISSON,
    thickness: float = THICKNESS,
) -> dict[str, np.ndarray]:
    blocks = misp3_flexural_blocks(
        coordinates,
        elastic_modulus=elastic_modulus,
        poisson_ratio=poisson_ratio,
        thickness=thickness,
    )
    area = float(blocks["area"])
    gradients = np.asarray(blocks["gradients"])
    membrane_section, _bending_section, _shear = _section_matrices(
        elastic_modulus, poisson_ratio, thickness
    )
    membrane_operator = _membrane_operator(gradients)
    membrane = area * membrane_operator.T @ membrane_section @ membrane_operator
    embedding = _plate_embedding()
    bending = embedding.T @ np.asarray(blocks["bending"]) @ embedding
    shear = embedding.T @ np.asarray(blocks["shear"]) @ embedding
    pl = _pl_completion(area, gradients, membrane_section)
    physical = membrane + bending + shear
    total = physical + pl
    return {
        "membrane": 0.5 * (membrane + membrane.T),
        "bending": 0.5 * (bending + bending.T),
        "shear": 0.5 * (shear + shear.T),
        "physical": 0.5 * (physical + physical.T),
        "pl": 0.5 * (pl + pl.T),
        "hourglass": np.zeros((18, 18), dtype=np.float64),
        "total": 0.5 * (total + total.T),
    }


def _dense(value: Any) -> np.ndarray:
    return np.asarray(value.toarray() if hasattr(value, "toarray") else value, dtype=np.float64)


def _connectivity(diagonal: str, i: int = 0, j: int = 0) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    selected = diagonal
    if selected == "alternating":
        selected = "backslash" if (i + j) % 2 == 0 else "slash"
    if selected == "backslash":
        return ((1, 2, 3), (1, 3, 4))
    if selected == "slash":
        return ((1, 2, 4), (2, 3, 4))
    raise ScreenError(f"unknown diagonal {diagonal!r}")


def _embed(local: np.ndarray, nodes: Sequence[int], node_count: int) -> np.ndarray:
    made = np.zeros((6 * node_count, 6 * node_count), dtype=np.float64)
    for local_i, node_i in enumerate(nodes):
        for local_j, node_j in enumerate(nodes):
            made[6 * (node_i - 1) : 6 * node_i, 6 * (node_j - 1) : 6 * node_j] += local[6 * local_i : 6 * local_i + 6, 6 * local_j : 6 * local_j + 6]
    return made


def _q4_macrocell() -> dict[str, np.ndarray]:
    from anysolver.e4_pl_element import QualifiedE4PLShellElement
    from anysolver.fe_core import FEModel
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    model = FEModel("v3a-q4-macrocell")
    model.add_material("steel", YOUNG, POISSON, density=7850.0)
    for node, xyz in enumerate(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)), 1):
        model.add_node(node, *xyz)
    element = QualifiedE4PLShellElement(
        1,
        (1, 2, 3, 4),
        "steel",
        thickness=THICKNESS,
        reference_normal=NORMAL,
        drilling_stabilization=0.001,
        hourglass_stabilization=0.001,
        pl_stabilization=1.0,
    )
    model.add_element(1, element)
    parts = element.compute_stiffness_components(model.mesh, model.materials["steel"])
    return {
        "physical": np.asarray(parts["physical"], dtype=np.float64),
        "numerical": np.asarray(parts["numerical"], dtype=np.float64),
        "total": _dense(assemble_stiffness_matrix(model)[0]),
    }


def macrocell_components(
    diagonal: str,
    *,
    permutation: Sequence[int] = (0, 1, 2),
    director_polarity: int = 1,
) -> dict[str, np.ndarray]:
    del director_polarity  # Flat source coordinates are physical-global and polarity invariant.
    q4 = _q4_macrocell()
    xy = {1: (0.0, 0.0), 2: (1.0, 0.0), 3: (1.0, 1.0), 4: (0.0, 1.0)}
    sums = {name: np.zeros((24, 24), dtype=np.float64) for name in ("membrane", "bending", "shear", "physical", "pl", "total")}
    for nodes in _connectivity(diagonal):
        ordered = tuple(nodes[index] for index in permutation)
        parts = shell_components([xy[node] for node in ordered])
        for name in sums:
            sums[name] += _embed(parts[name], ordered, 4)
    return {
        "q4_physical": q4["physical"],
        "q4_numerical": q4["numerical"],
        "q4_total": q4["total"],
        **{f"s3_{name}": value for name, value in sums.items()},
    }


def _boundary_indices(size: int) -> np.ndarray:
    nodes = [j * (size + 1) + i for j in range(size + 1) for i in range(size + 1) if i in (0, size) or j in (0, size)]
    return np.asarray([6 * node + dof for node in nodes for dof in range(6)], dtype=np.intp)


def _grid_matrix(size: int, kind: str, diagonal: str) -> np.ndarray:
    from anysolver.e4_pl_element import QualifiedE4PLShellElement
    from anysolver.fe_core import FEModel
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    model = FEModel(f"v3a-grid-{size}-{kind}-{diagonal}")
    model.add_material("steel", YOUNG, POISSON, density=7850.0)
    node_id = lambda i, j: j * (size + 1) + i + 1
    for j in range(size + 1):
        for i in range(size + 1):
            model.add_node(node_id(i, j), i / size, j / size, 0.0)
    element_id = 0
    if kind == "q4":
        for j in range(size):
            for i in range(size):
                element_id += 1
                nodes = (node_id(i, j), node_id(i + 1, j), node_id(i + 1, j + 1), node_id(i, j + 1))
                model.add_element(
                    element_id,
                    QualifiedE4PLShellElement(
                        element_id,
                        nodes,
                        "steel",
                        thickness=THICKNESS,
                        reference_normal=NORMAL,
                        drilling_stabilization=0.001,
                        hourglass_stabilization=0.001,
                        pl_stabilization=1.0,
                    ),
                )
        return _dense(assemble_stiffness_matrix(model)[0])
    total_nodes = (size + 1) ** 2
    assembled = np.zeros((6 * total_nodes, 6 * total_nodes), dtype=np.float64)
    coordinates = {node_id(i, j): (i / size, j / size) for j in range(size + 1) for i in range(size + 1)}
    for j in range(size):
        for i in range(size):
            base = (node_id(i, j), node_id(i + 1, j), node_id(i + 1, j + 1), node_id(i, j + 1))
            local_diagonal = "backslash" if diagonal == "alternating" and (i + j) % 2 == 0 else "slash" if diagonal == "alternating" else diagonal
            pairs = ((base[0], base[1], base[2]), (base[0], base[2], base[3])) if local_diagonal == "backslash" else ((base[0], base[1], base[3]), (base[1], base[2], base[3]))
            for nodes in pairs:
                local = shell_components([coordinates[node] for node in nodes])["total"]
                assembled += _embed(local, nodes, total_nodes)
    return assembled


def boundary_map(size: int, kind: str, diagonal: str) -> np.ndarray:
    stiffness = _grid_matrix(size, kind, diagonal)
    boundary = _boundary_indices(size)
    interior = np.setdiff1d(np.arange(stiffness.shape[0]), boundary)
    if interior.size == 0:
        return stiffness[np.ix_(boundary, boundary)]
    kbb = stiffness[np.ix_(boundary, boundary)]
    kbi = stiffness[np.ix_(boundary, interior)]
    kii = stiffness[np.ix_(interior, interior)]
    condensed = kbb - kbi @ np.linalg.solve(kii, kbi.T)
    return 0.5 * (condensed + condensed.T)


def _macrocell_modes() -> dict[str, np.ndarray]:
    xy = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    modes: dict[str, np.ndarray] = {}
    for name, values in {
        "rigid_tx": lambda x, y: (1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        "rigid_ty": lambda x, y: (0.0, 1.0, 0.0, 0.0, 0.0, 0.0),
        "rigid_tz": lambda x, y: (0.0, 0.0, 1.0, 0.0, 0.0, 0.0),
        "rigid_rx": lambda x, y: (0.0, 0.0, -y, 1.0, 0.0, 0.0),
        "rigid_ry": lambda x, y: (0.0, 0.0, x, 0.0, 1.0, 0.0),
        "rigid_rz": lambda x, y: (-y, x, 0.0, 0.0, 0.0, 1.0),
        "constant_eps_x": lambda x, y: (x, 0.0, 0.0, 0.0, 0.0, 0.0),
        "constant_eps_y": lambda x, y: (0.0, y, 0.0, 0.0, 0.0, 0.0),
        "constant_gamma_xy": lambda x, y: (0.5 * y, 0.5 * x, 0.0, 0.0, 0.0, 0.0),
        "constant_kappa_x": lambda x, y: (0.0, 0.0, 0.5 * x * x, 0.0, x, 0.0),
        "constant_kappa_y": lambda x, y: (0.0, 0.0, 0.5 * y * y, -y, 0.0, 0.0),
        "constant_kappa_xy": lambda x, y: (0.0, 0.0, x * y, -x, y, 0.0),
        "constant_shear_x": lambda x, y: (0.0, 0.0, x, 0.0, 0.0, 0.0),
        "constant_shear_y": lambda x, y: (0.0, 0.0, y, 0.0, 0.0, 0.0),
        "affine_trace": lambda x, y: (x + 0.25 * y, -0.2 * x + y, 0.4 * x - 0.3 * y, 0.1 * x, -0.15 * y, 0.5 * x - 0.5 * y),
    }.items():
        modes[name] = np.asarray([component for point in xy for component in values(*point)], dtype=np.float64)
    return modes


class ResearchMiSP3ShellElement:
    """Minimal assembly adapter; intentionally not a production element class."""

    formulation_id = FORMULATION_ID

    def __init__(self, element_id: int, node_ids: Sequence[int], material_name: str, thickness: float = THICKNESS):
        from anysolver.elements import ShellElement

        # Store a plain ShellElement delegate so the research adapter inherits no
        # failed S3 formulation methods while retaining standard DOF mapping.
        self._delegate = ShellElement(element_id, list(node_ids), material_name, thickness=thickness)
        self.element_id = int(element_id)
        self.node_ids = tuple(int(item) for item in node_ids)
        self.material_name = str(material_name)
        self.thickness = float(thickness)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._delegate, name)

    def compute_stiffness_components(self, mesh: Any, material: Any) -> dict[str, np.ndarray]:
        coordinates = [mesh.nodes[node].coords()[:2] for node in self.node_ids]
        return shell_components(
            coordinates,
            elastic_modulus=float(material.elastic_modulus),
            poisson_ratio=float(material.poisson_ratio),
            thickness=self.thickness,
        )

    def compute_stiffness_matrix(self, mesh: Any, material: Any) -> np.ndarray:
        return self.compute_stiffness_components(mesh, material)["total"]


def _selected_development_records() -> list[tuple[int, dict[str, Any], str]]:
    manifest = load_canonical(REFERENCE / "e4_pl_s3_mixed_mesh_connectivity_manifest.json")
    records = manifest["records"] if isinstance(manifest, dict) else manifest
    selected: dict[str, tuple[int, dict[str, Any], str]] = {}
    for index, record in enumerate(records):
        record_id = f"N{record['level']}:{record['s3_area_fraction_percent']}PCT:{record['mask']}:{record['diagonal']}"
        if record_id in DEVELOPMENT_IDS:
            selected[record_id] = (index, record, record_id)
    if set(selected) != set(DEVELOPMENT_IDS):
        raise ScreenError("registered development cases are absent from the frozen manifest")
    return [selected[record_id] for record_id in DEVELOPMENT_IDS]


def _development_model(record: Mapping[str, Any]) -> tuple[Any, dict[int, str]]:
    from anysolver.boundary import BoundaryCondition, LoadCase
    from anysolver.e4_pl_element import QualifiedE4PLShellElement
    from anysolver.fe_core import FEModel
    import e4_pl_s3_mixed_mesh_manifest as generator

    level = int(record["level"])
    split_count = int(record["split_base_cell_count"])
    selected = generator.selected_base_cells(str(record["mask"]), split_count)
    split_cells = set(generator.expanded_split_cells(selected, level))
    model = FEModel(f"v3a-development-{level}-{record['s3_area_fraction_percent']}")
    model.add_material("steel", YOUNG, POISSON, density=7850.0)
    node_id = lambda i, j: j * (level + 1) + i + 1
    for j in range(level + 1):
        for i in range(level + 1):
            model.add_node(node_id(i, j), i / level, j / level, 0.0)
    kinds: dict[int, str] = {}
    element_id = 0
    for j in range(level):
        for i in range(level):
            for kind, nodes in generator._cell_connectivity(i, j, level, split=(i, j) in split_cells, diagonal=str(record["diagonal"])):
                element_id += 1
                if kind == "Q4":
                    element = QualifiedE4PLShellElement(
                        element_id,
                        tuple(nodes),
                        "steel",
                        thickness=THICKNESS,
                        reference_normal=NORMAL,
                        drilling_stabilization=0.001,
                        hourglass_stabilization=0.001,
                        pl_stabilization=1.0,
                    )
                else:
                    element = ResearchMiSP3ShellElement(element_id, nodes, "steel")
                model.add_element(element_id, element)
                kinds[element_id] = kind
    edge_x = sorted({node_id(0, j) for j in range(level + 1)} | {node_id(level, j) for j in range(level + 1)})
    edge_y = sorted({node_id(i, 0) for i in range(level + 1)} | {node_id(i, level) for i in range(level + 1)})
    edge_all = sorted(set(edge_x) | set(edge_y))
    model.add_boundary_condition(BoundaryCondition("translations", edge_all, {"ux": 0.0, "uy": 0.0, "uz": 0.0}))
    model.add_boundary_condition(BoundaryCondition("rx", edge_x, {"rx": 0.0}))
    model.add_boundary_condition(BoundaryCondition("ry", edge_y, {"ry": 0.0}))
    load = LoadCase("uniform-pressure")
    for registered in model.mesh.elements:
        load.add_pressure_load(int(registered), PRESSURE)
    model.add_load_case(load)
    return model, kinds


def _development_record(index: int, record: Mapping[str, Any], record_id: str) -> dict[str, Any]:
    from scipy.sparse.linalg import spsolve
    from anysolver.matrix_assembly import assemble_load_vector, assemble_stiffness_matrix

    model, kinds = _development_model(record)
    stiffness, _info = assemble_stiffness_matrix(model)
    load, _load_info = assemble_load_vector(model, model.load_cases[0])
    model.apply_boundary_conditions()
    fixed = np.asarray(sorted(model.mesh.dof_manager._constrained_dofs), dtype=np.intp)
    free = np.setdiff1d(np.arange(stiffness.shape[0]), fixed)
    solution = np.zeros(stiffness.shape[0], dtype=np.float64)
    solution[free] = spsolve(stiffness[free][:, free], load[free])
    if not np.all(np.isfinite(solution)):
        raise ScreenError(f"development solve {record_id} produced nonfinite values")
    residual = stiffness[free] @ solution[free] - load[free]
    reference_center, reference_sha = _mindlin_center_reference()
    center_node = (int(record["level"]) // 2) * (int(record["level"]) + 1) + int(record["level"]) // 2
    center = float(solution[6 * center_node + 2])
    error = abs(center - reference_center) / max(abs(reference_center), np.finfo(float).tiny)
    return {
        "connectivity_sha256": str(record["connectivity_sha256"]),
        "element_counts": {"Q4": sum(value == "Q4" for value in kinds.values()), "S3": sum(value == "S3" for value in kinds.values())},
        "level": int(record["level"]),
        "manifest_index": int(index),
        "record_id": record_id,
        "reference_center_hex": float(reference_center).hex(),
        "reference_sha256": reference_sha,
        "response_center_hex": center.hex(),
        "response_relative_error_hex": float(error).hex(),
        "solver_residual_relative_hex": float(np.linalg.norm(residual) / max(np.linalg.norm(load[free]), 1.0)).hex(),
    }


def _mindlin_center_reference() -> tuple[float, str]:
    """Evaluate the independent odd-mode Navier field at the plate centre."""

    odd = np.arange(1, 100, 2, dtype=np.float64)
    m, n = np.meshgrid(odd, odd, indexing="ij")
    wave_x, wave_y = math.pi * m, math.pi * n
    load = 16.0 * PRESSURE / (math.pi**2 * m * n)
    rigidity = YOUNG * THICKNESS**3 / (12.0 * (1.0 - POISSON**2))
    transverse_shear = SHEAR_CORRECTION * YOUNG / (2.0 * (1.0 + POISSON)) * THICKNESS
    systems = np.empty(m.shape + (3, 3), dtype=np.float64)
    systems[..., 0, 0] = transverse_shear * (wave_x**2 + wave_y**2)
    systems[..., 0, 1] = systems[..., 1, 0] = transverse_shear * wave_x
    systems[..., 0, 2] = systems[..., 2, 0] = transverse_shear * wave_y
    systems[..., 1, 1] = transverse_shear + rigidity * (wave_x**2 + 0.5 * (1.0 - POISSON) * wave_y**2)
    systems[..., 2, 2] = transverse_shear + rigidity * (wave_y**2 + 0.5 * (1.0 - POISSON) * wave_x**2)
    systems[..., 1, 2] = systems[..., 2, 1] = rigidity * 0.5 * (1.0 + POISSON) * wave_x * wave_y
    right = np.zeros(m.shape + (3, 1), dtype=np.float64)
    right[..., 0, 0] = load
    transverse = np.linalg.solve(systems, right)[..., 0, 0]
    sine = np.sin(0.5 * math.pi * odd)
    center = float(np.einsum("mn,m,n->", transverse, sine, sine))
    authority = {
        "equation": "INDEPENDENT_NAVIER_REISSNER_MINDLIN_ODD_1_TO_99_V1",
        "parameters_hex": [YOUNG.hex(), POISSON.hex(), THICKNESS.hex(), PRESSURE.hex()],
        "value_hex": center.hex(),
    }
    return center, sha256_bytes(canonical_bytes(authority))


def _local_diagnostics() -> tuple[dict[str, Any], dict[str, Any]]:
    coordinates = ((0.0, 0.0), (1.0, 0.0), (0.2, 0.9))
    blocks = misp3_flexural_blocks(coordinates)
    components = shell_components(coordinates)
    singular_h = np.linalg.svd(np.asarray(blocks["H"]), compute_uv=False)
    singular_physical = np.linalg.svd(components["physical"], compute_uv=False)
    singular_total = np.linalg.svd(components["total"], compute_uv=False)
    tolerance_physical = max(singular_physical[0], 1.0) * 1.0e-10
    tolerance_total = max(singular_total[0], 1.0) * 1.0e-10
    rigid = np.zeros((18, 6), dtype=np.float64)
    for node, (x, y) in enumerate(coordinates):
        base = 6 * node
        rigid[base, 0] = 1.0
        rigid[base + 1, 1] = 1.0
        rigid[base + 2, 2] = 1.0
        rigid[base + 2, 3] = -y
        rigid[base + 3, 3] = 1.0
        rigid[base + 2, 4] = x
        rigid[base + 4, 4] = 1.0
        rigid[base, 5] = -y
        rigid[base + 1, 5] = x
        rigid[base + 5, 5] = 1.0
    rigid_residual = float(
        np.linalg.norm(components["total"] @ rigid, ord=np.inf)
        / max(np.linalg.norm(components["total"], ord=np.inf), 1.0)
    )
    local = {
        "H_positive": bool(singular_h[-1] > singular_h[0] * 1.0e-13),
        "component_sum_relative_inf_hex": relative_inf(components["bending"] + components["shear"], _plate_embedding().T @ np.asarray(blocks["condensed"]) @ _plate_embedding()).hex(),
        "physical_rank": int(np.count_nonzero(singular_physical > tolerance_physical)),
        "rigid_residual_relative_inf_hex": rigid_residual.hex(),
        "symmetry_relative_inf_hex": relative_inf(components["total"], components["total"].T).hex(),
        "total_rank": int(np.count_nonzero(singular_total > tolerance_total)),
    }
    local["gate_passed"] = bool(
        local["H_positive"]
        and local["physical_rank"] == 9
        and local["total_rank"] == 12
        and float.fromhex(local["component_sum_relative_inf_hex"]) <= 3.0e-13
        and float.fromhex(local["rigid_residual_relative_inf_hex"]) <= 3.0e-13
        and float.fromhex(local["symmetry_relative_inf_hex"]) <= 3.0e-13
    )
    payloads = {name: array_payload(np.asarray(value)) for name, value in blocks.items() if isinstance(value, np.ndarray)}
    payloads.update({f"shell_{name}": array_payload(value) for name, value in components.items()})
    return local, payloads


def _static_production_boundary() -> tuple[str, str]:
    tree = ast.parse((SRC / "anysolver" / "elements.py").read_text(encoding="utf-8"))
    values: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if (
            isinstance(target, ast.Name)
            and target.id in {"DEFAULT_Q4_FORMULATION", "DEFAULT_S3_FORMULATION"}
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            values[target.id] = node.value.value
    return values.get("DEFAULT_Q4_FORMULATION", ""), values.get("DEFAULT_S3_FORMULATION", "")


def produce_proof(*, include_development: bool = True) -> dict[str, Any]:
    validate_authority()
    default_q4, default_s3 = _static_production_boundary()
    if default_q4 != "e4-pl" or default_s3 != "legacy-s3":
        raise ScreenError("production formulation boundary changed")
    local, local_payloads = _local_diagnostics()
    if not bool(local["gate_passed"]):
        return {
            "boundary_maps": {},
            "candidate": {"formulation_id": FORMULATION_ID, "scope": "FLAT_LINEAR_ISOTROPIC_RESEARCH_ONLY"},
            "comparisons": {},
            "contract_sha256": sha256_file(CONTRACT_PATH),
            "development_record_ids": [],
            "development_records": [],
            "diagnostics": {
                "full_operator_equality_disposition": "DIAGNOSTIC_ONLY",
                "later_screen_stages": "NOT_EXECUTED_LOCAL_GATE_FAILED",
            },
            "local": local,
            "local_payloads": local_payloads,
            "matrices": {},
            "production_boundary": {"anymesh_untouched": True, "default_q4_formulation": default_q4, "default_s3_formulation": default_s3, "q4_mechanics_unchanged": True},
            "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
            "schema": PROOF_SCHEMA,
            "stage4a_rerun_authorized": False,
        }
    modes = _macrocell_modes()
    matrices: dict[str, Any] = {}
    comparisons: dict[str, Any] = {}
    d3_worst = 0.0
    reversal_worst = 0.0
    for diagonal in DIAGONALS:
        parts = macrocell_components(diagonal)
        matrices[diagonal] = {name: array_payload(value) for name, value in parts.items()}
        mode_rows: dict[str, Any] = {}
        for name, vector in modes.items():
            q4_energy = float(vector @ parts["q4_total"] @ vector)
            s3_energy = float(vector @ parts["s3_total"] @ vector)
            mode_rows[name] = {
                "energy_relative_hex": (abs(s3_energy - q4_energy) / max(abs(q4_energy), 1.0)).hex(),
                "q4_energy_hex": q4_energy.hex(),
                "s3_energy_hex": s3_energy.hex(),
            }
        for permutation in PERMUTATIONS:
            permuted = macrocell_components(diagonal, permutation=permutation)["s3_total"]
            d3_worst = max(d3_worst, relative_inf(permuted, parts["s3_total"]))
            reversed_matrix = macrocell_components(diagonal, permutation=permutation, director_polarity=-1)["s3_total"]
            reversal_worst = max(reversal_worst, relative_inf(reversed_matrix, permuted))
        comparisons[diagonal] = {
            "full_operator_relative_inf_hex": relative_inf(parts["s3_total"], parts["q4_total"]).hex(),
            "mode_energies": mode_rows,
        }
    boundary: dict[str, Any] = {}
    for diagonal in DIAGONALS:
        boundary[diagonal] = {}
        for size in (1, 2, 4):
            q4 = boundary_map(size, "q4", diagonal)
            s3 = boundary_map(size, "s3", diagonal)
            boundary[diagonal][str(size)] = {
                "q4": array_payload(q4),
                "relative_inf_hex": relative_inf(s3, q4).hex(),
                "s3": array_payload(s3),
            }
    development = []
    if include_development:
        for selected in _selected_development_records():
            development.append(_development_record(*selected))
    return {
        "boundary_maps": boundary,
        "candidate": {"formulation_id": FORMULATION_ID, "scope": "FLAT_LINEAR_ISOTROPIC_RESEARCH_ONLY"},
        "comparisons": comparisons,
        "contract_sha256": sha256_file(CONTRACT_PATH),
        "development_record_ids": list(DEVELOPMENT_IDS) if include_development else [],
        "development_records": development,
        "diagnostics": {
            "d3_worst_relative_inf_hex": d3_worst.hex(),
            "director_reversal_worst_relative_inf_hex": reversal_worst.hex(),
            "full_operator_equality_disposition": "DIAGNOSTIC_ONLY",
        },
        "local": local,
        "local_payloads": local_payloads,
        "matrices": matrices,
        "production_boundary": {"anymesh_untouched": True, "default_q4_formulation": "e4-pl", "default_s3_formulation": "legacy-s3", "q4_mechanics_unchanged": True},
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": PROOF_SCHEMA,
        "stage4a_rerun_authorized": False,
    }


def _append_progress(path: Path, *, cycle: int, phase: str, sequence: int) -> None:
    with Path(path).open("ab") as stream:
        stream.write(canonical_bytes({"cycle": cycle, "phase": phase, "sequence": sequence}))
        stream.flush()
        os.fsync(stream.fileno())


def _run_child(command: list[str], timeout_seconds: int) -> None:
    from e4_pl_s3_v2_bounded_process import _ProcessJob

    environment = os.environ.copy()
    environment.update(THREAD_ENV)
    job = _ProcessJob(MEMORY_LIMIT_BYTES)
    process = None
    try:
        process = job.launch(command, cwd=ROOT, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            return_code = process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            if not job.terminate(124):
                raise ScreenError("timed-out process tree did not drain") from exc
            raise ScreenError(f"child exceeded {timeout_seconds} seconds") from exc
        _cpu, active, peak = job.accounting()
        if active:
            if not job.terminate(125):
                raise ScreenError("completed process retained descendants")
            raise ScreenError("completed process retained descendants")
        if peak > MEMORY_LIMIT_BYTES:
            raise ScreenError("child exceeded the 24-GiB process-tree limit")
        if return_code != 0:
            raise ScreenError(f"child failed with exit code {return_code}")
    finally:
        job.close()


def adjudicate(*, checker_identical: bool, report: Mapping[str, Any]) -> str:
    if not checker_identical or not bool(report.get("authority_complete")):
        return "BLOCKED_E4_PL_S3_V3_SOURCE_OR_EVIDENCE"
    if not bool(report.get("source_identity_passed")):
        return "NO_GO_E4_PL_S3_V3_SOURCE_IDENTITY"
    if not bool(report.get("local_operator_passed")):
        return "NO_GO_E4_PL_S3_V3A_LOCAL_OPERATOR"
    if not bool(report.get("mixed_interface_passed")):
        return "NO_GO_E4_PL_S3_V3A_MIXED_INTERFACE"
    if bool(report.get("replacement_required")):
        return "UNCLASSIFIED_E4_PL_S3_V3_FORMULATION_REPLACEMENT_REQUIRED"
    return "PROVISIONAL_GO_E4_PL_S3_V3A_STAGE4A_RERUN"


def run_bounded(
    output_root: Path,
    *,
    timeout_seconds: int = 600,
    wave_timeout_seconds: int = 1800,
) -> dict[str, Any]:
    validate_authority()
    if timeout_seconds <= 0 or timeout_seconds > 600:
        raise ScreenError("child timeout must be in 1..600 seconds")
    if wave_timeout_seconds <= 0 or wave_timeout_seconds > 1800:
        raise ScreenError("wave timeout must be in 1..1800 seconds")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=False)
    progress = root / "progress.jsonl"
    progress.touch(exist_ok=False)
    script = Path(__file__).resolve()
    checker = REFERENCE / "e4_pl_s3_v3a_screen_checker.py"
    deadline = time.monotonic() + wave_timeout_seconds
    cycle_rows: list[dict[str, Any]] = []
    terminal = "BLOCKED_E4_PL_S3_V3_SOURCE_OR_EVIDENCE"
    try:
        for cycle in (1, 2):
            cycle_root = root / f"cycle-{cycle}"
            cycle_root.mkdir()
            proof = cycle_root / "proof.json"
            checkers = (cycle_root / "checker-a.json", cycle_root / "checker-b.json")
            _append_progress(progress, cycle=cycle, phase="INITIALIZATION", sequence=0)
            remaining = int(max(1, min(timeout_seconds, deadline - time.monotonic())))
            _run_child([sys.executable, str(script), "--emit-proof", "--output", str(proof)], remaining)
            _append_progress(progress, cycle=cycle, phase="PROOF_COMPLETE", sequence=1)
            commands = [[sys.executable, str(checker), "--verify-proof", str(proof), "--output", str(path)] for path in checkers]
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(_run_child, command, int(max(1, min(timeout_seconds, deadline - time.monotonic())))) for command in commands]
                for future in futures:
                    future.result()
            _append_progress(progress, cycle=cycle, phase="CHECKERS_COMPLETE", sequence=2)
            identical = checkers[0].read_bytes() == checkers[1].read_bytes()
            report = load_canonical(checkers[0])
            terminal = adjudicate(checker_identical=identical, report=report)
            cycle_rows.append({
                "checker_replicas_byte_identical": identical,
                "checker_sha256": sha256_file(checkers[0]),
                "cycle": cycle,
                "proof_bytes": proof.stat().st_size,
                "proof_sha256": sha256_file(proof),
                "terminal": terminal,
            })
            _append_progress(progress, cycle=cycle, phase="CYCLE_COMPLETE", sequence=3)
        deterministic = cycle_rows[0]["proof_sha256"] == cycle_rows[1]["proof_sha256"] and cycle_rows[0]["checker_sha256"] == cycle_rows[1]["checker_sha256"]
        if not deterministic:
            terminal = "BLOCKED_E4_PL_S3_V3_SOURCE_OR_EVIDENCE"
    except BaseException as exc:
        cycle_rows.append({"error_class": type(exc).__name__, "status": "FAILED_BOUNDED_CHILD"})
        terminal = "BLOCKED_E4_PL_S3_V3_SOURCE_OR_EVIDENCE"
    aggregate = {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "contract_sha256": sha256_file(CONTRACT_PATH),
        "cycles": cycle_rows,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": AGGREGATE_SCHEMA,
        "stage4a_rerun_authorized": terminal == "PROVISIONAL_GO_E4_PL_S3_V3A_STAGE4A_RERUN",
        "terminal": terminal,
    }
    exclusive_write(root / "aggregate.json", aggregate)
    _append_progress(progress, cycle=0, phase="AGGREGATE_COMPLETE", sequence=4)
    return aggregate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-proof", action="store_true")
    mode.add_argument("--run-bounded", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--skip-development", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--wave-timeout-seconds", type=int, default=1800)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.emit_proof:
        if args.output is None:
            raise ScreenError("--output is required")
        exclusive_write(args.output, produce_proof(include_development=not args.skip_development))
    else:
        if args.output_root is None:
            raise ScreenError("--output-root is required")
        run_bounded(args.output_root, timeout_seconds=args.timeout_seconds, wave_timeout_seconds=args.wave_timeout_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
