"""Two-interval exact solid six-channel work map and bounded action runner.

This isolates longitudinal connection resolution on the *same* saved C1
detached linear solid. Each half patch carries a normalized physical six-row
mean pose law. It is a development discriminator, not the formal F03 run.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts.b3_e4_f03_ccx_six_channel_compliance import (
    ACTION_SCALES, EXE, EXE_SHA, ROOT, _replace_load, _response, _run, _source,
)
from scripts.b3_e4_f03_ccx_six_channel_preflight import (
    _element_domain_nodes, six_channel_rows,
)
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    _quad8_shape, digest, unexpected_solver_diagnostics,
)


REFERENCE = (ROOT / ".qualification/b3-ge-e4-pl/"
             "f03-c1-six-channel-compliance-dev-20260927-v1/"
             "reconstruction_v5.json")


def _half_face_weights(coords, eligible, z, interval, *, moment_y=False):
    lookup = defaultdict(list)
    for node in eligible:
        lookup[tuple(np.round(coords[node], 9))].append(node)

    def face_node(x, y):
        found = lookup[tuple(np.round((x, y, z), 9))]
        if len(found) != 1:
            raise ValueError("ambiguous half-patch face node")
        return found[0]

    xs = np.linspace(.9+.05*interval, .95+.05*interval, 3)
    ys = np.linspace(-.05, .05, 9)
    roots, gauss = np.polynomial.legendre.leggauss(3)
    weights = defaultdict(float)
    for x0, x1 in zip(xs[:-1], xs[1:]):
        for y0, y1 in zip(ys[:-1], ys[1:]):
            xm, ym = (x0+x1)/2, (y0+y1)/2
            ids = (face_node(x0,y0), face_node(x1,y0),
                   face_node(x1,y1), face_node(x0,y1),
                   face_node(xm,y0), face_node(x1,ym),
                   face_node(xm,y1), face_node(x0,ym))
            for xi, wx in zip(roots, gauss):
                for eta, wy in zip(roots, gauss):
                    shape = _quad8_shape(float(xi), float(eta))
                    y = ym+(y1-y0)*float(eta)/2
                    # Each half-patch area is 0.05 x 0.1 = 0.005 m2.
                    scale = (x1-x0)*(y1-y0)*float(wx*wy)/(.005*4)
                    for node, value in zip(ids, shape):
                        weights[node] += scale*value*(y if moment_y else 1.)
    result = {node: value for node, value in weights.items()
              if abs(value) > 1e-16}
    if abs(sum(result.values())-(0. if moment_y else 1.)) > 2e-12:
        raise ArithmeticError("half-patch mean/first moment lost normalization")
    return result


def split_rows(coords, plate_nodes, bar_nodes):
    transverse_inertia = .1**2/12
    all_rows = []
    for interval in (0, 1):
        surfaces = {
            "plate_top": _half_face_weights(coords, plate_nodes, .0175, interval),
            "plate_bottom": _half_face_weights(coords, plate_nodes, -.0175, interval),
            "bar_bottom": _half_face_weights(coords, bar_nodes, .0175, interval),
            "bar_top": _half_face_weights(coords, bar_nodes, .1175, interval),
        }
        moments = {side: _half_face_weights(
            coords, plate_nodes if side == "plate_top" else bar_nodes,
            .0175, interval, moment_y=True)
            for side in ("plate_top", "bar_bottom")}
        rows = [defaultdict(float) for _ in range(6)]

        def add(index, side, component, scale, *, moment=False):
            for node, value in (moments if moment else surfaces)[side].items():
                rows[index][node, component] += scale*value

        for component in range(3):
            add(component, "plate_top", component, 1.)
            add(component, "bar_bottom", component, -1.)
        add(3, "plate_top", 2, 1/transverse_inertia, moment=True)
        add(3, "bar_bottom", 2, -1/transverse_inertia, moment=True)
        add(4, "plate_top", 0, 1/.035)
        add(4, "plate_bottom", 0, -1/.035)
        add(4, "bar_top", 0, -1/.1)
        add(4, "bar_bottom", 0, 1/.1)
        add(5, "plate_top", 0, -1/transverse_inertia, moment=True)
        add(5, "bar_bottom", 0, 1/transverse_inertia, moment=True)
        all_rows.extend({key: value for key, value in row.items()
                         if abs(value) > 1e-15} for row in rows)
    return all_rows


def preflight(coords, rows, supported, plate_nodes, bar_nodes):
    if len(rows) != 12:
        raise ValueError("two six-channel intervals required")
    variables = sorted({key for row in rows for key in row})
    if any(node in supported for node, _ in variables):
        raise ValueError("split joint touches a directly supported node")
    matrix = np.array([[row.get(key, 0.) for key in variables]
                       for row in rows])
    rank = int(np.linalg.matrix_rank(matrix, tol=1e-10))
    if rank != 12:
        raise ArithmeticError("split physical channel rows are dependent")
    rigid = np.zeros((len(variables), 6))
    for index, (node, axis) in enumerate(variables):
        rigid[index, axis] = 1.
        rigid[index, 3:] = np.cross(np.eye(3), coords[node])[:, axis]
    rigid_gap = float(np.max(np.abs(matrix@rigid)))
    if rigid_gap > 2e-9:
        raise ArithmeticError("split work map violates common rigid motion")
    original, _ = six_channel_rows(coords, plate_nodes, bar_nodes, factor=4)
    keys = {key for row in rows+original for key in row}
    composite = max(abs((rows[j].get(key,0.)+rows[j+6].get(key,0.))/2-
                        original[j].get(key,0.))
                    for j in range(6) for key in keys)
    if composite > 1e-12:
        raise ArithmeticError("two split means do not reproduce original mean")
    return {"rank": rank, "row_nonzeros": [len(row) for row in rows],
            "unique_nodal_dofs": len(variables),
            "max_rigid_gap": rigid_gap,
            "max_mean_recomposition_defect": float(composite)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--channel", type=int, choices=range(12), required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output_root.resolve() / f"channel-{args.channel}"
    if output.exists():
        raise FileExistsError("preserve previous split action result")
    deck, meta, coords, _, _, _ = _source(source)
    reference = json.loads(REFERENCE.read_text())
    if (digest(deck) != reference["cases"]["tip_mx"]["source_deck_sha256"]
            or digest(source / "model.json") !=
            reference["cases"]["tip_mx"]["source_model_sha256"]
            or digest(EXE) != EXE_SHA):
        raise ValueError("matched solid or solver identity changed")
    plate, bar = _element_domain_nodes(deck)
    rows = split_rows(coords, plate, bar)
    audit = preflight(coords, rows, set(meta["boundary_node_ids"]),
                      plate, bar)
    output.mkdir(parents=True)
    stem = f"split-six-channel-{args.channel}"
    generated = output / f"{stem}.inp"
    scale = ACTION_SCALES[args.channel % 6]
    generated.write_text(_replace_load(deck.read_text(), rows[args.channel],
                                       scale))
    code, stdout, stderr, seconds, peak, failure = _run(stem, output)
    (output / "stdout.log").write_bytes(stdout)
    (output / "stderr.log").write_bytes(stderr)
    gaps = None
    if failure is None:
        if code != 0:
            failure = f"CALCULIX_EXIT_{code}"
        else:
            try:
                convergence_log = (output / f"{stem}.cvg").read_text(
                    errors="replace")
            except OSError as error:
                failure = f"CONVERGENCE_LOG_{type(error).__name__}: {error}"
            if failure is None:
                log = (stdout.decode(errors="replace")+
                       stderr.decode(errors="replace")+convergence_log)
                diagnostics = unexpected_solver_diagnostics(log,
                                                            c1_penalty=False)
                if (stdout.decode(errors="replace").count("Job finished") != 1
                        or diagnostics):
                    failure = f"SOLVER_DIAGNOSTICS_{diagnostics[:5]}"
                else:
                    try:
                        gaps = _response(output, coords, rows)
                    except (OSError, ValueError, KeyError) as error:
                        failure = f"RESPONSE_{type(error).__name__}: {error}"
    result = {
        "classification": "external linear two-interval split six-channel development response",
        "status": "EXPLORATORY_COMPLETE" if failure is None else "EXPLORATORY_FAILURE",
        "failure": failure, "channel": args.channel,
        "applied_dual_scale": scale, "gap_response": gaps,
        "seconds": seconds, "peak_solver_rss_bytes": peak,
        "exit_code": code, "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip(),
        "source_deck_sha256": digest(deck),
        "source_model_sha256": digest(source / "model.json"),
        "generated_deck_sha256": digest(generated),
        "solver_sha256": EXE_SHA, "runner_sha256": digest(Path(__file__)),
        "reference_sha256": digest(REFERENCE), "preflight": audit,
        "limitations": ["same saved C1 detached linear no-contact solid",
                        "one split-law compliance column; no reconstructed joint yet",
                        "not formal F03 or G0B acceptance"],
    }
    (output / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n")
    print(json.dumps({key: result[key] for key in
                      ("status", "failure", "channel", "seconds",
                       "peak_solver_rss_bytes", "gap_response")}), flush=True)
    return 0 if failure is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
