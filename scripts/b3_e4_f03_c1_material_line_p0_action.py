"""One bounded CalculiX unit action for the matched material-line P0 law."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts.b3_e4_f03_c1_material_line_p0_reference import integrated_rows
from scripts.b3_e4_f03_c1_solid_trace_residual import RECON, SOURCE
from scripts.b3_e4_f03_ccx_six_channel_compliance import (
    ROOT, _replace_load, _run, _source,
)
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    EXE, EXE_SHA, digest, unexpected_solver_diagnostics,
)
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


def run_one(channel: int, output_root: Path) -> dict:
    if type(channel) is not int or not 0 <= channel < 24:
        raise ValueError("one of 24 bounded P0 action channels required")
    reconstruction = json.loads(RECON.read_text())
    deck, meta, coords, _, _, _ = _source(SOURCE / "tip_mx")
    if (reconstruction["status"] != "EXPLORATORY_COMPLETE" or
            digest(deck) != reconstruction["cases"]["tip_mx"]["source_deck_sha256"] or
            digest(EXE) != EXE_SHA):
        raise ValueError("source deck, reconstruction or solver identity changed")
    from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
    plate, bar = _element_domain_nodes(deck)
    nodes, rows, _ = integrated_rows(coords, plate, bar)
    if set(nodes) & set(meta["boundary_node_ids"]):
        raise ValueError("line action overlaps saved support")
    action = rows[channel].reshape(-1, 3)
    # Integrated gap rows contain dx. These densities yield approximately
    # 1 kN or 100 Nm total action on a 25 mm P0 interval.
    scale = 40000. if channel % 6 < 3 else 4000.
    nodal = {(node, axis): float(value)
             for node, values in zip(nodes, action)
             for axis, value in enumerate(values) if value != 0.}
    folder = output_root / f"channel-{channel}"
    if folder.exists():
        raise FileExistsError("preserve previous action result")
    folder.mkdir(parents=True)
    stem = f"material-line-p0-{channel}"
    generated = folder / f"{stem}.inp"
    generated.write_text(_replace_load(deck.read_text(), nodal, scale),
                         encoding="utf-8")
    code, stdout, stderr, elapsed, peak, failure = _run(stem, folder)
    (folder / "stdout.log").write_bytes(stdout)
    (folder / "stderr.log").write_bytes(stderr)
    response = None
    self_work = None
    if failure is None:
        if code != 0:
            failure = f"CALCULIX_EXIT_{code}"
        else:
            cvg = folder / f"{stem}.cvg"
            all_output = (stdout.decode(errors="replace") +
                          stderr.decode(errors="replace") +
                          cvg.read_text(errors="replace"))
            diagnostics = unexpected_solver_diagnostics(
                all_output, c1_penalty=False)
            if stdout.decode(errors="replace").count("Job finished") != 1 or diagnostics:
                failure = f"SOLVER_DIAGNOSTICS_{diagnostics[:5]}"
            else:
                try:
                    frds = list(folder.glob("*.frd"))
                    if len(frds) != 1:
                        raise ValueError("one full-field FRD required")
                    field = _read_frd_u(frds[0])
                    if set(field) != set(coords):
                        raise ValueError("incomplete solid displacement")
                    values = np.array([field[node] for node in nodes]).ravel()
                    if not np.isfinite(values).all():
                        raise ValueError("nonfinite solid displacement")
                    response = (rows@values).tolist()
                    self_work = float(scale*response[channel])
                    if self_work <= 0.:
                        raise ArithmeticError("nonpositive supported self compliance")
                except (OSError, ValueError, KeyError, ArithmeticError) as exc:
                    failure = f"RESPONSE_{type(exc).__name__}: {exc}"
    result = {
        "status": "EXPLORATORY_COMPLETE" if failure is None else "EXPLORATORY_FAILURE",
        "classification": "one external solid action column of matched P0 material-line law",
        "failure": failure,
        "channel": channel,
        "applied_density_scale": scale,
        "gap_response": response,
        "self_work_j": self_work,
        "seconds": elapsed,
        "peak_solver_rss_bytes": peak,
        "exit_code": code,
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 cwd=ROOT, text=True).strip(),
        "source_deck_sha256": digest(deck),
        "source_model_sha256": digest(SOURCE / "tip_mx" / "model.json"),
        "reference_reconstruction_sha256": digest(RECON),
        "generated_deck_sha256": digest(generated),
        "solver_sha256": EXE_SHA,
        "limitations": [
            "one column does not establish reciprocity or a constrained solution",
            "different connection from old area-mean F4 and no contact",
            "not F03/G0B acceptance or P0 selection",
        ],
    }
    (folder / "result.json").write_text(json.dumps(result, indent=2,
        sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    result = run_one(args.channel, args.output_root)
    print(json.dumps({key: result[key] for key in (
        "status", "failure", "channel", "self_work_j", "seconds",
        "peak_solver_rss_bytes")}), flush=True)
    if result["status"] != "EXPLORATORY_COMPLETE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
