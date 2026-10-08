"""One bounded hard-mortar screen on the saved C1 penalty contact deck.

Only the contact interaction changes. This is external-reference development,
not native coupling qualification or a general contact runner.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import numpy as np

from scripts.b3_e4_f03_c1_split_unbonded_gap import (
    _same_xy_plate_gap, _sample_faces,
)
from scripts.b3_e4_f03_ccx_six_channel_compliance import EXE, EXE_SHA, _run
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    _quad8_shape, digest, parse_nodal_vectors, split_left_root_support_wrenches,
    unexpected_solver_diagnostics,
)
from scripts.b3_e4_f03_solid_bond_pose_projection import (
    _read_deck_nodes, _read_frd_u,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / ".qualification/b3-ge-e4-pl/"
          "f03-ccx-c1-matched-penalty-dev-20260925-v1/solid-4-tip_mx")
EXPECTED_DECK = "54c15a39ea0d37fb0e801719c101ce32d4238af7fd88ad0df53bb86da55cb537"
EXPECTED_MODEL = "684656f6ca8e3df43c43e9a2480995de891d37b05980010ce954edee190e7402"
PENALTY = ("*SURFACE INTERACTION,NAME=PenaltyUnbonded\n"
           "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR\n"
           "4.2e14,1\n"
           "*CONTACT PAIR,INTERACTION=PenaltyUnbonded,TYPE=SURFACE TO SURFACE\n"
           "BarBottomUnbonded,PlateTopUnbonded")
MORTAR = ("*SURFACE INTERACTION,NAME=HardUnbonded\n"
          "*CONTACT PAIR,INTERACTION=HardUnbonded,TYPE=MORTAR\n"
          "BarBottomUnbonded,PlateTopUnbonded")


def _deck_and_model():
    decks = list(SOURCE.glob("*.inp"))
    if (len(decks) != 1 or digest(decks[0]) != EXPECTED_DECK or
            digest(SOURCE / "model.json") != EXPECTED_MODEL or
            digest(EXE) != EXE_SHA):
        raise ValueError("paired source deck, model or solver identity changed")
    model = json.loads((SOURCE / "model.json").read_text())
    if (model["contact_policy"] != "c1_penalty" or
            model["bar_reference_profile"] !=
            "C1_TWO_QUADRATIC_TANGENT_ALIGNED_V1" or
            len(model["plate_contact_face_element_ids"]) != 128 or
            len(model["bar_contact_face_element_ids"]) != 128 or
            len(model["unbonded_face_pairs"]) != 128 or
            model["factor"] != 4 or model["shear"] != "tip_mx"):
        raise ValueError("saved C1 contact model changed")
    source_text = decks[0].read_text()
    if source_text.count(PENALTY) != 1:
        raise ValueError("one exact source contact interaction required")
    candidate_text = source_text.replace(PENALTY, MORTAR)
    if candidate_text.replace(MORTAR, PENALTY) != source_text:
        raise ArithmeticError("contact-only deck edit cannot be reversed")
    return decks[0], model, candidate_text


def _wrench_balance(model, coords, dat):
    supports = set(map(int, model["boundary_node_ids"]))
    reaction = parse_nodal_vectors(dat, supports, "forces", "SUPPORTS")
    support = split_left_root_support_wrenches(model, reaction)
    external = np.zeros(6)
    for key, components in model["applied_nodal_forces_N"].items():
        node = int(key)
        force = np.asarray(components, dtype=float)
        external[:3] += force
        external[3:] += np.cross(coords[node], force)
    total = np.asarray(support["total_support_wrench_N_Nm"])+external
    return {"external_N_Nm": external.tolist(),
            "support": support,
            "external_plus_support_N_Nm": total.tolist(),
            "force_relative": float(np.linalg.norm(total[:3]) /
                                    max(1., np.linalg.norm(external[:3]))),
            "moment_relative": float(np.linalg.norm(total[3:]) /
                                     max(1., np.linalg.norm(external[3:])))}


def _all_same_xy_gap(coords, field, faces):
    """Sample all face interiors; unresolved projections bar separation claims."""
    roots, _ = np.polynomial.legendre.leggauss(9)
    count = negative = unresolved = 0
    minimum = float("inf")
    witness = None
    for index, face in enumerate(faces):
        plate = np.array([coords[node]+field[node] for node in face[:, 0]])
        bar = np.array([coords[node]+field[node] for node in face[:, 1]])
        for xi in roots:
            for eta in roots:
                sample = _quad8_shape(float(xi), float(eta))@bar
                matched = _same_xy_plate_gap(
                    plate, sample, float(xi), float(eta))
                count += 1
                if matched is None:
                    unresolved += 1
                    continue
                gap, parameters, defect = matched
                negative += gap < 0.
                if gap < minimum:
                    minimum = gap
                    witness = (index, float(xi), float(eta),
                               parameters.tolist(), defect)
    return {"samples": count, "unresolved": unresolved,
            "negative": negative,
            "minimum_projected_gap_m": minimum if witness else None,
            "minimum_sample": witness,
            "meaning": "all 9x9 face-interior samples projected to the same deformed XY on paired Q8 plate faces; sampling does not certify a global contact condition"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_root.resolve()
    if output.exists():
        raise FileExistsError("preserve prior contact screen")
    source_deck, model, candidate = _deck_and_model()
    output.mkdir(parents=True)
    stem = "c1-hard-mortar-tip-mx"
    deck = output / f"{stem}.inp"
    deck.write_text(candidate)
    code, stdout, stderr, elapsed, peak, failure = _run(stem, output)
    (output / "stdout.log").write_bytes(stdout)
    (output / "stderr.log").write_bytes(stderr)
    report = {
        "classification": "one-contact-method matched C1 external reference screen; development only",
        "source_deck_sha256": digest(source_deck),
        "source_model_sha256": digest(SOURCE / "model.json"),
        "candidate_deck_sha256": digest(deck),
        "runner_sha256": digest(Path(__file__)),
        "solver_sha256": EXE_SHA,
        "change": "finite linear penalty surface-to-surface to hard mortar only",
        "contact_face_counts": {"plate": 128, "bar": 128},
        "elapsed_seconds": elapsed, "peak_solver_rss_bytes": peak,
        "exit_code": code, "failure": failure,
        "status": "EXPLORATORY_FAILURE",
        "limitations": ["one C1 quadratic torque mesh and one contact method",
                        "no matched opening/shear or mesh/contact convergence",
                        "not F03/G0B or native accuracy acceptance"],
    }
    if failure is None and code != 0:
        failure = f"CALCULIX_EXIT_{code}"
    if failure is None:
        try:
            stdout_text = stdout.decode(errors="replace")
            stderr_text = stderr.decode(errors="replace")
            cvg = (output / f"{stem}.cvg").read_text(errors="replace")
            diagnostics = unexpected_solver_diagnostics(
                stdout_text+stderr_text+cvg, c1_penalty=True)
            if stdout_text.count("Job finished") != 1 or diagnostics:
                failure = f"SOLVER_DIAGNOSTICS_{diagnostics[:5]}"
            else:
                coords = _read_deck_nodes(deck)
                field = _read_frd_u(output / f"{stem}.frd")
                if set(coords) != set(field):
                    raise ValueError("incomplete full-field displacement")
                faces = [np.asarray(face, dtype=int)
                         for face in model["unbonded_face_pairs"]]
                gap = _sample_faces(coords, field, faces)
                complete_gap = _all_same_xy_gap(coords, field, faces)
                dat = (output / f"{stem}.dat").read_text(errors="replace")
                balance = _wrench_balance(model, coords, dat)
                contacts = re.findall(r"(?mi)^\s*total number of contact elements.*?\n\s*(\d+)\s*$", dat)
                report.update({"gap": gap, "all_same_xy_gap": complete_gap,
                               "balance": balance,
                               "contact_count_reported": [int(x) for x in contacts],
                               "displacement_sha256": digest(output / f"{stem}.frd"),
                               "dat_sha256": digest(output / f"{stem}.dat")})
                if (complete_gap["negative"] == 0 and
                        complete_gap["unresolved"] == 0 and
                        balance["force_relative"] <= 1e-8 and
                        balance["moment_relative"] <= 1e-8):
                    report["status"] = "EXPLORATORY_SCREEN_PASS"
                else:
                    failure = "SAMPLED_OVERLAP_PROJECTION_OR_BALANCE_FAILURE"
        except (OSError, ValueError, KeyError, ArithmeticError) as error:
            failure = f"RECOVERY_{type(error).__name__}: {error}"
    report["failure"] = failure
    report["raw_files_sha256"] = {
        path.name: digest(path) for path in sorted(output.iterdir())
        if path.is_file() and path.name != "result.json"}
    (output / "result.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+"\n")
    print(json.dumps({key: report.get(key) for key in
                      ("status", "failure", "elapsed_seconds",
                       "peak_solver_rss_bytes", "contact_count_reported")}),
          flush=True)
    return 0 if report["status"] == "EXPLORATORY_SCREEN_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
