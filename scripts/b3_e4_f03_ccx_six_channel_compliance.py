"""Bounded external solid unit-action solves for the sided six-channel joint.

The final 6x6 compliance can enforce the same linear constraints without a
wide CalculiX MPC. Each source action is an ordinary nodal load, and every
run retains its deck, binary identity, solver outputs and raw displacement.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np
import psutil

from scripts.b3_e4_f03_ccx_six_channel_preflight import (
    DEFAULT_CASE, _element_domain_nodes, audit_rows, six_channel_rows,
)
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    EXE, EXE_SHA, digest, unexpected_solver_diagnostics,
)
from scripts.b3_e4_f03_solid_bond_pose_projection import (
    _read_deck_nodes, _read_frd_u,
)


ROOT = Path(__file__).resolve().parents[1]
LIMIT_SECONDS = 120
LIMIT_BYTES = 2 * 1024**3
ACTION_SCALES = (1000., 1000., 1000., 100., 100., 100.)


def _source(folder: Path):
    meta = json.loads((folder / "model.json").read_text())
    if (meta.get("bar_reference_profile") !=
            "C1_TWO_QUADRATIC_TANGENT_ALIGNED_V1" or
            meta.get("bond_policy") != "detached" or
            meta.get("shared_interface_nodes") != 0 or
            meta.get("plate_thickness_m") != .035 or
            meta.get("node_count") != 38162):
        raise ValueError("matched C1 detached source identity changed")
    decks = list(folder.glob("*.inp"))
    if len(decks) != 1:
        raise ValueError("one saved detached solid deck required")
    deck = decks[0]
    coords = _read_deck_nodes(deck)
    plate, bar = _element_domain_nodes(deck)
    if plate & bar or set(coords) != set(plate | bar):
        raise ValueError("detached domain ownership changed")
    rows, geometry = six_channel_rows(coords, plate, bar, factor=4)
    audit = audit_rows(coords, rows,
                       supported=set(meta["boundary_node_ids"]))
    return deck, meta, coords, rows, geometry, audit


def _replace_load(deck: str, row: dict[tuple[int, int], float],
                  scale: float) -> str:
    start = deck.find("*CLOAD\n")
    end = deck.find("*NODE PRINT", start)
    if start < 0 or end < 0 or deck.count("*CLOAD\n") != 1:
        raise ValueError("saved detached load/output deck structure changed")
    lines = ["*CLOAD"]
    lines.extend(f"{node},{axis+1},{scale*value:.17g}"
                 for (node, axis), value in sorted(row.items()))
    return deck[:start] + "\n".join(lines) + "\n" + deck[end:]


def _run(stem: str, folder: Path):
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    start = time.perf_counter()
    proc = subprocess.Popen((str(EXE), "-i", stem), cwd=folder,
                            env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    monitor = psutil.Process(proc.pid)
    peak = 0
    while True:
        try:
            peak = max(peak, monitor.memory_info().rss)
        except psutil.NoSuchProcess:
            pass
        elapsed = time.perf_counter() - start
        failure = ("MEMORY_LIMIT_2_GIB" if peak > LIMIT_BYTES else
                   "TIMEOUT_120_SECONDS" if elapsed > LIMIT_SECONDS else None)
        if failure:
            proc.kill()
            stdout, stderr = proc.communicate()
            return None, stdout, stderr, elapsed, peak, failure
        try:
            stdout, stderr = proc.communicate(timeout=.5)
            return (proc.returncode, stdout, stderr,
                    time.perf_counter() - start, peak, None)
        except subprocess.TimeoutExpired:
            continue


def _response(folder: Path, coords, rows):
    frds = list(folder.glob("*.frd"))
    if len(frds) != 1:
        raise ValueError("one completed full-field displacement file required")
    u = _read_frd_u(frds[0])
    if set(u) != set(coords):
        raise ValueError("incomplete solid full-field displacement")
    if not all(np.isfinite(value).all() for value in u.values()):
        raise ValueError("nonfinite solid displacement")
    return [float(sum(value * u[node][axis]
                      for (node, axis), value in row.items()))
            for row in rows]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--channel", type=int, choices=range(6), required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output_root.resolve() / f"channel-{args.channel}"
    if output.exists():
        raise FileExistsError("preserve any previous external unit-action result")
    deck, meta, coords, rows, geometry, audit = _source(source)
    if digest(EXE) != EXE_SHA:
        raise ValueError("CalculiX executable identity changed")
    output.mkdir(parents=True)
    stem = f"six-channel-{args.channel}"
    generated = output / f"{stem}.inp"
    generated.write_text(_replace_load(deck.read_text(), rows[args.channel],
                                       ACTION_SCALES[args.channel]))
    code, stdout, stderr, elapsed, peak, failure = _run(stem, output)
    (output / "stdout.log").write_bytes(stdout)
    (output / "stderr.log").write_bytes(stderr)
    gaps = None
    if failure is None:
        if code != 0:
            failure = f"CALCULIX_EXIT_{code}"
        else:
            all_output = (stdout.decode(errors="replace") +
                          stderr.decode(errors="replace") +
                          (output / f"{stem}.cvg").read_text(errors="replace"))
            diagnostics = unexpected_solver_diagnostics(
                all_output, c1_penalty=False)
            if stdout.decode(errors="replace").count("Job finished") != 1 or diagnostics:
                failure = f"SOLVER_DIAGNOSTICS_{diagnostics[:5]}"
            else:
                try:
                    gaps = _response(output, coords, rows)
                except (OSError, ValueError, KeyError) as exc:
                    failure = f"RESPONSE_{type(exc).__name__}: {exc}"
    result = {
        "classification": "external linear six-channel compliance development response",
        "status": "EXPLORATORY_COMPLETE" if failure is None else "EXPLORATORY_FAILURE",
        "failure": failure, "channel": args.channel,
        "applied_dual_scale": ACTION_SCALES[args.channel],
        "gap_response": gaps, "seconds": elapsed,
        "peak_solver_rss_bytes": peak, "exit_code": code,
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 cwd=ROOT, text=True).strip(),
        "source_deck_sha256": digest(deck),
        "source_model_sha256": digest(source / "model.json"),
        "generated_deck_sha256": digest(generated),
        "solver_sha256": EXE_SHA, "geometry": geometry, "preflight": audit,
        "limitations": ["linear detached solid reference; not native E4/B3 state",
                        "one compliance column; no constrained solution yet",
                        "no physical fidelity or G0B acceptance"],
    }
    (output / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: result[k] for k in
                      ("status", "failure", "channel", "seconds",
                       "peak_solver_rss_bytes", "gap_response")}), flush=True)
    return 0 if failure is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
