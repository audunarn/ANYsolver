"""Linear six-channel work preflight on the detached C1 solid reference.

This constructs an independently interpretable solid-side *candidate* for the
native line action. It does not execute CalculiX or qualify a connection law.
The plate-top and bar-bottom faces are distinct node sets in the saved mesh.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_ccx_solid_bond_screen import _quad8_shape
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_deck_nodes


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = (ROOT / ".qualification/b3-ge-e4-pl/"
                "f03-c1-detached-port-dev-20260926-v2/tip_mx")


def _face_weights(coords: dict[int, np.ndarray], *, z: float,
                  factor: int, eligible: set[int] | None,
                  moment_y: bool = False) -> dict[int, float]:
    """Exact Q8 area mean, optionally weighted by transverse position y."""
    lookup: dict[tuple[float, float, float], list[int]] = defaultdict(list)
    for node, xyz in coords.items():
        if eligible is None or node in eligible:
            lookup[tuple(np.round(xyz, 9))].append(node)

    def node(x: float, y: float) -> int:
        ids = lookup.get(tuple(np.round((x, y, z), 9)), ())
        if len(ids) != 1:
            raise ValueError(f"ambiguous or missing sided face node {(x, y, z)}: {len(ids)}")
        return ids[0]

    xs = np.linspace(.9, 1., factor + 1)
    ys = np.linspace(-.05, .05, 2 * factor + 1)
    roots, gauss = np.polynomial.legendre.leggauss(3)
    weights: dict[int, float] = defaultdict(float)
    for x0, x1 in zip(xs[:-1], xs[1:]):
        for y0, y1 in zip(ys[:-1], ys[1:]):
            xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
            ids = (node(x0, y0), node(x1, y0), node(x1, y1), node(x0, y1),
                   node(xm, y0), node(x1, ym), node(xm, y1), node(x0, ym))
            area_scale = (x1 - x0) * (y1 - y0) / (4 * .1 * .1)
            for xi, wx in zip(roots, gauss):
                for eta, wy in zip(roots, gauss):
                    shape = _quad8_shape(float(xi), float(eta))
                    y = ym + (y1 - y0) * float(eta) / 2
                    scale = area_scale * wx * wy * (y if moment_y else 1.)
                    for index, value in zip(ids, scale * shape):
                        weights[index] += float(value)
    result = {key: value for key, value in weights.items() if abs(value) > 1e-16}
    expected = 0. if moment_y else 1.
    if abs(sum(result.values()) - expected) > 2e-12:
        raise AssertionError("sided face quadrature lost its constant/odd field")
    return result


def _element_domain_nodes(deck: Path) -> tuple[set[int], set[int]]:
    """Read the saved C3D20R connectivity, including continuation lines."""
    domains = {"Plate": set(), "Stiffener": set()}
    active = None
    continuation = False
    for raw in deck.read_text().splitlines():
        line = raw.strip()
        if line.startswith("*"):
            active = next((name for name in domains
                           if line.upper() ==
                           f"*ELEMENT,TYPE=C3D20R,ELSET={name.upper()}"), None)
            continuation = False
            continue
        if active is None or not line:
            continue
        ids = [int(value) for value in line.split(",") if value.strip()]
        if not continuation:
            if len(ids) != 16:
                raise ValueError("unexpected saved C3D20R first connectivity line")
            domains[active].update(ids[1:])
        else:
            if len(ids) != 5:
                raise ValueError("unexpected saved C3D20R continuation line")
            domains[active].update(ids)
        continuation = not continuation
    if not all(domains.values()) or continuation:
        raise ValueError("incomplete saved solid element domains")
    return domains["Plate"], domains["Stiffener"]


def six_channel_rows(coords: dict[int, np.ndarray], plate_nodes: set[int],
                     bar_nodes: set[int],
                     *, factor: int, thickness: float = .035,
                     bar_depth: float = .1) -> tuple[list[dict[tuple[int, int], float]], dict]:
    """Solid virtual-work map in native order Fx,Fy,Fz,Mx,My,Mz.

    Surface position means use plate top minus bar bottom. Transverse
    position moments use the same gap. The pitch channel uses plate and
    bar through-thickness x-displacement gradients, with the native
    shell-minus-beam sign. This is a *linear solid idealization* of the
    native E4 director/B3 section-frame pitch, not its nonlinear identity.
    """
    if factor not in (2, 4) or thickness <= 0 or bar_depth <= 0:
        raise ValueError("bounded detached C1 geometry required")
    surfaces = {
        "plate_top": _face_weights(coords, z=thickness / 2,
                                   factor=factor, eligible=plate_nodes),
        "bar_bottom": _face_weights(coords, z=thickness / 2,
                                    factor=factor, eligible=bar_nodes),
        "plate_bottom": _face_weights(coords, z=-thickness / 2,
                                      factor=factor, eligible=plate_nodes),
        "bar_top": _face_weights(coords, z=thickness / 2 + bar_depth,
                                 factor=factor, eligible=bar_nodes),
    }
    moments = {
        side: _face_weights(coords, z=thickness / 2, factor=factor,
                            eligible=(plate_nodes if side == "plate_top"
                                      else bar_nodes), moment_y=True)
        for side in ("plate_top", "bar_bottom")
    }
    transverse_inertia = .1**2 / 12
    rows: list[dict[tuple[int, int], float]] = [defaultdict(float) for _ in range(6)]

    def add(row: int, side: str, component: int, factor_value: float,
            *, transverse: bool = False) -> None:
        weights = moments[side] if transverse else surfaces[side]
        for node, weight in weights.items():
            rows[row][(node, component)] += factor_value * weight

    for component in range(3):
        add(component, "plate_top", component, 1.)
        add(component, "bar_bottom", component, -1.)
    add(3, "plate_top", 2, 1 / transverse_inertia, transverse=True)
    add(3, "bar_bottom", 2, -1 / transverse_inertia, transverse=True)
    # Shell director pitch minus beam section pitch.
    add(4, "plate_top", 0, 1 / thickness)
    add(4, "plate_bottom", 0, -1 / thickness)
    add(4, "bar_top", 0, -1 / bar_depth)
    add(4, "bar_bottom", 0, 1 / bar_depth)
    add(5, "plate_top", 0, -1 / transverse_inertia, transverse=True)
    add(5, "bar_bottom", 0, 1 / transverse_inertia, transverse=True)

    clean = [{key: val for key, val in row.items() if abs(val) > 1e-15}
             for row in rows]
    return clean, {"surface_node_counts": {k: len(v) for k, v in surfaces.items()},
                   "transverse_second_moment_m2": transverse_inertia}


def audit_rows(coords: dict[int, np.ndarray], rows, *,
               supported: set[int]) -> dict:
    variables = sorted({key for row in rows for key in row})
    mat = np.array([[row.get(key, 0.) for key in variables] for row in rows])
    if any(node in supported for node, _ in variables):
        raise AssertionError("joint touches a directly supported node")
    if np.linalg.matrix_rank(mat, tol=1e-10) != 6:
        raise AssertionError("six sided work channels are dependent")
    rigid = np.zeros((len(variables), 6))
    for i, (node, component) in enumerate(variables):
        rigid[i, component] = 1.
        xyz = coords[node]
        rigid[i, 3:] = np.cross(np.eye(3), xyz)[:, component]
    residual = mat @ rigid
    if np.max(np.abs(residual)) > 2e-9:
        raise AssertionError("sided work violates a common rigid motion")
    return {"row_nonzeros": [len(row) for row in rows],
            "unique_nodal_dofs": len(variables),
            "rank": int(np.linalg.matrix_rank(mat, tol=1e-10)),
            "max_rigid_translation_rotation_gap": float(np.max(np.abs(residual))),
            "channel_labels": ["Fx", "Fy", "Fz", "Mx", "My", "Mz"],
            "limitations": ["linear solid-side candidate, not native E4/B3 kinematics",
                            "no CalculiX execution or supported-response comparison",
                            "no physical fidelity, stability or G0B qualification"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, default=DEFAULT_CASE)
    args = parser.parse_args()
    folder = args.case.resolve()
    model_path = folder / "model.json"
    meta = json.loads(model_path.read_text())
    if (meta.get("bar_reference_profile") !=
            "C1_TWO_QUADRATIC_TANGENT_ALIGNED_V1" or
            meta.get("bond_policy") != "detached" or
            meta.get("shared_interface_nodes") != 0 or
            meta.get("plate_thickness_m") != .035):
        raise ValueError("the saved C1 detached solid identity changed")
    decks = list(folder.glob("*.inp"))
    if len(decks) != 1:
        raise ValueError("one saved detached input deck required")
    coords = _read_deck_nodes(decks[0])
    if set(coords) != set(range(1, meta["node_count"] + 1)):
        raise ValueError("saved solid node inventory changed")
    plate_nodes, bar_nodes = _element_domain_nodes(decks[0])
    if plate_nodes & bar_nodes:
        raise ValueError("the saved solid is not detached at every joint node")
    rows, geometry = six_channel_rows(
        coords, plate_nodes, bar_nodes, factor=4)
    audit = audit_rows(coords, rows,
                       supported=set(meta["boundary_node_ids"]))
    print(json.dumps({"case": str(folder), "geometry": geometry, "audit": audit},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
