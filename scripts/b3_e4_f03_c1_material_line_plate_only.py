"""Bounded plate-only C3D20R action using the fixed matched line dual.

Factor four must reproduce the existing detached solid plate action before
factor two is interpreted. This is a read-only mechanical comparison apart
from new, uniquely named development solver outputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts.b3_e4_f03_c1_material_line_p0_reference import integrated_rows
from scripts.b3_e4_f03_c1_material_line_solid_port import build_flat_solid_line_port
from scripts.b3_e4_f03_ccx_six_channel_compliance import _replace_load, _run
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    EXE, EXE_SHA, digest, unexpected_solver_diagnostics,
)
from scripts.b3_e4_f03_plate_patch_work import build_solid_plate
from scripts.b3_e4_f03_solid_bond_pose_projection import (
    _read_deck_nodes, _read_frd_u,
)


ROOT = Path(__file__).resolve().parents[1]
DETACHED = ROOT / ".qualification/b3-ge-e4-pl/f03-c1-detached-port-dev-20260926-v2/tip_mx"
X_P0 = (.9, .925, .95, .975, 1.)


def _reference_grid(factor):
    if factor == 2:
        return (.9, .95, 1.), tuple(np.linspace(-.05, .05, 5))
    if factor == 4:
        return (.9, .925, .95, .975, 1.), tuple(np.linspace(-.05, .05, 9))
    raise ValueError("bounded factors two/four only")


def _plate_rows(plate_coords, factor):
    x_grid, y_grid = _reference_grid(factor)
    coords = dict(plate_coords)
    fake = set()
    xs = sorted(set(x_grid) | {(a+b)/2. for a, b in zip(x_grid[:-1], x_grid[1:])})
    ys = sorted(set(y_grid) | {(a+b)/2. for a, b in zip(y_grid[:-1], y_grid[1:])})
    next_id = max(coords)+1
    for z in (.0175, .1175):
        for x in xs:
            for y in ys:
                coords[next_id] = np.array((x, y, z))
                fake.add(next_id)
                next_id += 1
    roots, weights = np.polynomial.legendre.leggauss(3)
    intervals = []
    for a, b in zip(X_P0[:-1], X_P0[1:]):
        intervals.append(tuple((float(weight)*(b-a)/2.,
            build_flat_solid_line_port(coords, set(plate_coords), fake,
                (a+b)/2.+float(root)*(b-a)/2.,
                x_edges=x_grid, y_edges=y_grid))
            for root, weight in zip(roots, weights)))
    nodes = tuple(sorted({node for interval in intervals for _, port in interval
                          for node in port.node_ids if node in plate_coords}))
    index = {node: i for i, node in enumerate(nodes)}
    rows = np.zeros((24, 3*len(nodes)))
    for i, interval in enumerate(intervals):
        for weight, port in interval:
            local = np.vstack((port.shell_top_jacobian,
                               -port.shell_orientation_jacobian))
            for k, node in enumerate(port.node_ids):
                if node in index:
                    rows[6*i:6*i+6, 3*index[node]:3*index[node]+3] += (
                        weight*local[:, 3*k:3*k+3])
    return nodes, rows


def _factor_four_parity(coords, nodes, rows):
    source_decks = list(DETACHED.glob("*.inp"))
    if len(source_decks) != 1:
        raise ValueError("one saved detached factor-four source required")
    source_coords = _read_deck_nodes(source_decks[0])
    source_plate, source_bar = _element_domain_nodes(source_decks[0])
    if (len(coords) != len(source_plate) or
            {tuple(np.round(v, 9)) for v in coords.values()} !=
            {tuple(np.round(source_coords[n], 9)) for n in source_plate}):
        raise ValueError("plate-only factor-four geometry differs from detached solid")
    source_nodes, source_rows, _ = integrated_rows(source_coords, source_plate,
                                                   source_bar)
    source_index = {node: i for i, node in enumerate(source_nodes)}
    source_by_location = {tuple(np.round(source_coords[node], 9)): node
                          for node in source_plate}
    mapped = np.zeros_like(rows)
    for i, node in enumerate(nodes):
        other = source_by_location[tuple(np.round(coords[node], 9))]
        j = source_index[other]
        mapped[:, 3*i:3*i+3] = source_rows[:, 3*j:3*j+3]
    defect = float(np.max(np.abs(rows-mapped)))
    if defect > 1e-12:
        raise ArithmeticError("plate-only line action differs from detached factor four")
    return defect, digest(source_decks[0])


def _wrench(coords, nodes, nodal):
    locations = np.array([coords[node] for node in nodes])
    return np.r_[np.sum(nodal, axis=0),
                 np.sum(np.cross(locations, nodal), axis=0)]


def run_one(factor: int, label: str, reconstruction_path: Path,
            same_action_path: Path, output_root: Path, *,
            preflight_only: bool = False) -> dict:
    if factor not in (2, 4) or label not in ("tip_mx", "tip_fz"):
        raise ValueError("bounded factor and load label required")
    reconstruction = json.loads(reconstruction_path.read_text())
    same_action = json.loads(same_action_path.read_text())
    if (reconstruction["status"] != "EXPLORATORY_COMPLETE" or
            same_action["solid_reconstruction_sha256"] != digest(reconstruction_path) or
            digest(EXE) != EXE_SHA):
        raise ValueError("matched dual, action or solver identity changed")
    deck_text, meta = build_solid_plate(factor, "tip_mx", thickness=.035)
    folder = output_root / f"factor-{factor}-{label}"
    if folder.exists():
        raise FileExistsError("preserve prior plate-only action result")
    folder.mkdir(parents=True)
    stem = f"material-line-plate-{factor}-{label}"
    mesh_deck = folder / "plate-source.inp"
    mesh_deck.write_text(deck_text, encoding="utf-8")
    coords = _read_deck_nodes(mesh_deck)
    if meta["plate_nodes"] != len(coords) or meta["thickness_m"] != .035:
        raise ValueError("plate-only mesh metadata changed")
    nodes, rows = _plate_rows(coords, factor)
    parity = None
    detached_hash = None
    if factor == 4:
        parity, detached_hash = _factor_four_parity(coords, nodes, rows)
    dual = np.asarray(reconstruction["cases"][label]["dual_physical_line_density"])
    force = -(rows.T@dual).reshape(-1, 3)
    threshold = 1e-12*float(np.max(np.abs(force)))
    discarded = np.where(np.abs(force) < threshold, force, 0.)
    applied = force-discarded
    if float(np.sum(np.abs(discarded))) > 1e-7:
        raise ArithmeticError("plate action filtering is not numerical zero")
    nodal = {(node, axis): float(value)
             for node, values in zip(nodes, applied)
             for axis, value in enumerate(values) if value != 0.}
    if "*NODE FILE" in deck_text:
        raise ValueError("unexpected existing full-field output card")
    deck_with_output = deck_text.replace("*END STEP", "*NODE FILE\nU\n*END STEP")
    if deck_with_output == deck_text:
        raise ValueError("plate-only step ending changed")
    generated = folder / f"{stem}.inp"
    generated.write_text(_replace_load(deck_with_output, nodal, 1.),
                         encoding="utf-8")
    preflight = {
        "factor_four_row_max_defect": parity,
        "detached_factor_four_deck_sha256": detached_hash,
        "active_action_nodes": len(nodes),
        "row_rank": int(np.linalg.matrix_rank(rows, tol=1e-10)),
        "applied_wrench_N_Nm": _wrench(coords, nodes, applied).tolist(),
        "discarded_absolute_nodal_load_N": float(np.sum(np.abs(discarded))),
    }
    row_failure = ("DEPENDENT_P0_M4_ROWS" if preflight["row_rank"] != 24
                   else None)
    code = None
    elapsed = 0.
    peak = 0
    failure = row_failure
    work = None
    if not preflight_only and failure is None:
        code, stdout, stderr, elapsed, peak, failure = _run(stem, folder)
        (folder / "stdout.log").write_bytes(stdout)
        (folder / "stderr.log").write_bytes(stderr)
        if failure is None:
            if code != 0:
                failure = f"CALCULIX_EXIT_{code}"
            else:
                diagnostics = unexpected_solver_diagnostics(
                    stdout.decode(errors="replace") +
                    stderr.decode(errors="replace") +
                    (folder / f"{stem}.cvg").read_text(errors="replace"),
                    c1_penalty=False)
                if stdout.decode(errors="replace").count("Job finished") != 1 or diagnostics:
                    failure = f"SOLVER_DIAGNOSTICS_{diagnostics[:5]}"
                else:
                    frds = list(folder.glob("*.frd"))
                    if len(frds) != 1:
                        failure = "RESPONSE_ONE_FULL_FIELD_FRD_REQUIRED"
                    else:
                        field = _read_frd_u(frds[0])
                        if set(field) != set(coords):
                            failure = "RESPONSE_INCOMPLETE_PLATE_FIELD"
                        else:
                            u = np.array([field[node] for node in nodes])
                            work = float(np.sum(force*u))
                            if work <= 0. or not np.isfinite(work):
                                failure = "RESPONSE_NONPOSITIVE_WORK"
    result = {
        "status": (("DEVELOPMENT_PREFLIGHT_FAILED" if failure else
                    "DEVELOPMENT_PREFLIGHT_PASSED") if preflight_only else
                   "EXPLORATORY_COMPLETE" if failure is None else "EXPLORATORY_FAILURE"),
        "classification": "fixed matched-line dual on standalone 35 mm quadratic plate",
        "factor": factor, "label": label, "failure": failure,
        "plate_action_work_J": work, "seconds": elapsed,
        "peak_solver_rss_bytes": peak, "exit_code": code,
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 cwd=ROOT, text=True).strip(),
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "same_action_sha256": digest(same_action_path),
        "mesh_deck_sha256": digest(mesh_deck),
        "generated_deck_sha256": digest(generated),
        "solver_sha256": EXE_SHA, "preflight": preflight,
        "limitations": [
            "single fixed dual from factor-four coupled solid; no re-equilibration",
            "two 3D levels only; not convergence or F03/G0B acceptance",
        ],
    }
    (folder / "result.json").write_text(json.dumps(result, indent=2,
        sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--factor", type=int, required=True)
    parser.add_argument("--case", choices=("tip_mx", "tip_fz"), required=True)
    parser.add_argument("--reconstruction", type=Path, required=True)
    parser.add_argument("--same-action", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    result = run_one(args.factor, args.case, args.reconstruction.resolve(),
                     args.same_action.resolve(), args.output_root.resolve(),
                     preflight_only=args.preflight_only)
    print(json.dumps({key: result[key] for key in
                      ("status", "failure", "factor", "label",
                       "plate_action_work_J", "seconds", "peak_solver_rss_bytes")},
                     sort_keys=True))
    if result["failure"] is not None:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
