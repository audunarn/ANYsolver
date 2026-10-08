"""Split already-saved independent Fz weak modes into beam strain actions.

No mesh or multiplier candidate is added here. This is a bounded diagnostic
of the bending-to-shear interpretation, not an interface stability proof.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import scipy
from scipy import linalg
from threadpoolctl import threadpool_info, threadpool_limits

from scripts.b3_e4_f03_independent_transverse_reference import (
    BEAM_I, BEAM_J, BEAM_SHEAR_AREA, E, G, _quadrature, _spline,
    assemble, beam_strain_rows,
)


def split(saved_row: dict, norm: str) -> dict:
    intervals = saved_row["intervals"]
    ks, kb, c, _, _, _ = assemble(
        16, 4, 8, intervals, origin="strip", director="strip",
        basis="spline", multiplier="p0", thickness=.07,
        strip_half_length=.05, strip_half_width=.05)
    mode = np.asarray(saved_row[norm]["mode"], dtype=float)
    if mode.shape != (intervals,) or not np.isfinite(mode).all():
        raise ValueError("saved physical weak vector changed")
    fz_rows = c[0::3]
    shell_rows, beam_rows = fz_rows[:, :len(ks)], fz_rows[:, len(ks):]
    shell_q = linalg.solve(ks, shell_rows.T @ mode, assume_a="pos")
    beam_q = linalg.solve(kb, beam_rows.T @ mode, assume_a="pos")
    shell_action = float(shell_q @ ks @ shell_q)
    beam_action = float(beam_q @ kb @ beam_q)
    strain_action = np.zeros(3)
    for station, weight in _quadrature(5, _spline(8, 0., 1.)[2]):
        strains = beam_strain_rows(8, float(station), basis="spline") @ beam_q
        strain_action += weight * np.array((G * BEAM_J, E * BEAM_I,
                                            G * BEAM_SHEAR_AREA)) * strains**2
    if abs(float(strain_action.sum()) - beam_action) > 2e-9 * max(beam_action, 1e-20):
        raise ArithmeticError("beam strain action fails assembled stiffness closure")
    return {
        "shell_action": shell_action,
        "beam_action": beam_action,
        "beam_torsion_bending_shear_actions": strain_action.tolist(),
        "beam_torsion_bending_shear_shares": (strain_action / beam_action).tolist(),
        "shell_beam_shares": [shell_action / (shell_action + beam_action),
                              beam_action / (shell_action + beam_action)],
        "beam_strain_closure_relative": float(
            (strain_action.sum() - beam_action) / beam_action),
        "saved_mode_sign_changes": int(np.count_nonzero(
            np.sign(mode[1:]) != np.sign(mode[:-1]))),
    }


def run(output_dir: Path) -> None:
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise RuntimeError("run requires clean source")
    mode_file = (output_dir.parent / "f03-finite-strip-dual-norm-dev-20260925-v1" /
                 "results.jsonl")
    split_file = (output_dir.parent /
                  "f03-independent-fz-action-decomposition-dev-20260925-v1" /
                  "results.jsonl")
    modes = [json.loads(line) for line in mode_file.read_text().splitlines()]
    prior = [json.loads(line) for line in split_file.read_text().splitlines()]
    if [item["intervals"] for item in modes] != [4, 8] or [
            item["intervals"] for item in prior] != [4, 8]:
        raise ValueError("saved case identities changed")
    output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "question": "Does the saved alternating Fz action shift from beam bending to transverse shear as rows double?",
        "decision": "A shift supports a finite bending/shear crossover hypothesis, but does not certify exact-multiplier stability; absence of shift rejects that explanation.",
        "source_sha": source, "python": platform.python_version(),
        "numpy": np.__version__, "scipy": scipy.__version__, "threads": 1,
        "mode_file": str(mode_file),
        "mode_sha256": hashlib.sha256(mode_file.read_bytes()).hexdigest(),
        "prior_split_file": str(split_file),
        "prior_split_sha256": hashlib.sha256(split_file.read_bytes()).hexdigest(),
        "mesh": "independent square-strip RM plate x16/y4, Timoshenko spline beam8, fixed .05/.05 m half-strip",
        "scope": "existing four/eight-row weak vectors; no new mesh or qualification",
    }
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"] = threadpool_info()
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        with (output_dir / "results.jsonl").open("w") as stream:
            for saved, comparison in zip(modes, prior):
                row = {"intervals": saved["intervals"]}
                for norm in ("HminusHalf", "HminusOne"):
                    result = split(saved, norm)
                    for field in ("shell_action", "beam_action"):
                        if abs(result[field] - comparison[norm][field]) > (
                                2e-9 * max(result[field], 1e-20)):
                            raise ArithmeticError("saved domain-action parity failed")
                    row[norm] = result
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                print(row["intervals"],
                      row["HminusOne"]["beam_torsion_bending_shear_shares"],
                      flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    run(parser.parse_args().output_dir)
