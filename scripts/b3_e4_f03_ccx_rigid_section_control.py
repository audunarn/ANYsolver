"""Bounded external rigid-section control for the full solid bond.

This changes only the bar's cross-section kinematics at solid element stations.
It is a development discriminator, not a B3/E4 reference qualification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

import numpy as np

from scripts import b3_e4_f03_ccx_solid_bond_screen as solid


TIMEOUT_SECONDS = 120


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _node_inventory(deck: str) -> dict[int, tuple[float, float, float]]:
    block = deck.split("*NODE,NSET=AllNodes\n", 1)[1].split("*ELEMENT", 1)[0]
    nodes: dict[int, tuple[float, float, float]] = {}
    for line in block.splitlines():
        fields = line.split(",")
        if len(fields) != 4:
            raise ValueError("unexpected full-bond node record")
        node = int(fields[0])
        if node in nodes:
            raise ValueError("duplicate full-bond node")
        nodes[node] = tuple(float(v) for v in fields[1:])
    return nodes


def _bar_nodes(deck: str) -> set[int]:
    block = deck.split("*ELEMENT,TYPE=C3D20R,ELSET=Stiffener\n", 1)[1]
    block = block.split("*MATERIAL", 1)[0]
    pending: list[int] = []
    nodes: set[int] = set()
    for line in block.splitlines():
        pending.extend(int(field) for field in line.split(",") if field.strip())
        if len(pending) == 21:
            nodes.update(pending[1:])
            pending.clear()
        elif len(pending) > 21:
            raise ValueError("unexpected quadratic stiffener connectivity")
    if pending or not nodes:
        raise ValueError("incomplete quadratic stiffener connectivity")
    return nodes


def rigid_section_deck(factor: int = 2) -> tuple[str, dict]:
    """Add disjoint solid-section rigid bodies at non-root bar stations."""
    if factor not in (2, 4):
        raise ValueError("bounded rigid-section factor must be 2 or 4")
    deck, model = solid.build(
        factor, "tip_mx", boundary_policy="left_root", bond_policy="full",
        element_family="C3D20R", plate_thickness_mm=35,
        tip_load_map="quadratic_face")
    nodes = _node_inventory(deck)
    bar = _bar_nodes(deck)
    if not bar.issubset(nodes):
        raise ValueError("stiffener connectivity references absent nodes")
    if model["unbonded_face_pairs"] or model["detached_interface_nodes"]:
        raise ValueError("rigid-section control requires the full shared bond")

    added_nodes: list[str] = []
    cards: list[str] = []
    sections: list[dict] = []
    used: set[int] = set()
    next_node = max(nodes) + 1
    for station in range(1, 4 * factor + 1):
        x = station / (4 * factor)
        section = sorted(node for node in bar
                         if abs(nodes[node][0] - x) < 1e-12)
        if len(section) < 9 or used.intersection(section):
            raise ValueError("incomplete or overlapping stiffener section")
        if (max(nodes[node][1] for node in section) -
                min(nodes[node][1] for node in section) < .099 or
                max(nodes[node][2] for node in section) -
                min(nodes[node][2] for node in section) < .099):
            raise ValueError("rigid section lacks two transverse directions")
        used.update(section)
        ref, rot = next_node, next_node + 1
        next_node += 2
        added_nodes.extend((f"{ref},{x:.12g},0,0.0675",
                            f"{rot},{x:.12g},0,0.0675"))
        name = f"RigidSection{station}"
        cards.append(f"*NSET,NSET={name}")
        cards.extend(",".join(str(node) for node in section[i:i + 12])
                     for i in range(0, len(section), 12))
        cards.append(f"*RIGID BODY,NSET={name},REF NODE={ref},ROT NODE={rot}")
        sections.append({"station_x_m": x, "node_count": len(section),
                         "node_ids": section, "reference_node": ref,
                         "rotation_node": rot})

    if set(model["boundary_node_ids"]).intersection(used):
        raise ValueError("rigid sections overlap existing root support")
    applied = {int(node) for node in model["applied_nodal_forces_N"]}
    if not applied.issubset(sections[-1]["node_ids"]):
        raise ValueError("tip load is not fully carried by the tip section")
    element_card = "*ELEMENT,TYPE=C3D20R,ELSET=Plate"
    if deck.count(element_card) != 1 or deck.count("*STEP\n") != 1:
        raise ValueError("unexpected full-bond deck structure")
    deck = deck.replace(element_card,
                        "*NODE\n" + "\n".join(added_nodes) + "\n" + element_card,
                        1)
    deck = deck.replace("*STEP\n", "\n".join(cards) + "\n*STEP\n", 1)
    model = dict(model)
    model["rigid_section_control"] = {
        "type": "CalculiX *RIGID BODY on solid section nodes",
        "sections": sections,
        "root_face_excluded": True,
        "shared_interface_nodes_included": True,
        "reference": "https://dhondt.de/ccx_2.23.pdf, section 7.113",
    }
    return deck, model


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--factor", type=int, choices=(2, 4), default=2)
    args = parser.parse_args()
    if args.root.exists():
        parser.error("evidence root already exists")
    if not solid.EXE.is_file() or _sha(solid.EXE) != solid.EXE_SHA:
        parser.error("pinned CalculiX executable unavailable or changed")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        parser.error("source-bound development control requires a clean checkout")

    deck, model = rigid_section_deck(args.factor)
    root = args.root.resolve()
    root.mkdir(parents=True)
    name = f"rigid-{args.factor}-tip_mx"
    case = root / name
    case.mkdir()
    deck_file = case / f"{name}.inp"
    deck_file.write_text(deck)
    (case / "model.json").write_text(json.dumps(model, indent=2) + "\n")
    manifest = {
        "status": "EXPLORATORY_NOT_G0_ACCEPTANCE",
        "question": "Does suppressing solid stiffener section warping at its element stations change full-bond torque work and support transfer toward the native six-channel line?",
        "outcome_rule": "A shift toward the native response implicates rigid-section/interface idealization; no shift points to other transfer differences. Failure or incomplete solves are not mechanics results.",
        "source_head": head,
        "source_sha256": _sha(Path(__file__)),
        "base_source_sha256": _sha(Path(solid.__file__)),
        "executable": str(solid.EXE),
        "executable_sha256": solid.EXE_SHA,
        "factor": args.factor,
        "deck_sha256": _sha(deck_file),
        "constraint": "Each non-root solid cross-section is rigid; shared plate/bar nodes on that section participate. This is stronger than a weak beam/shell mortar and is not B3 equivalence.",
        "limit": {"omp_threads": 1, "timeout_seconds": TIMEOUT_SECONDS},
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               MKL_NUM_THREADS="1")
    started = time.perf_counter()
    try:
        run = subprocess.run([str(solid.EXE), "-i", name], cwd=case,
                             capture_output=True, timeout=TIMEOUT_SECONDS,
                             env=env, check=False)
        stdout = run.stdout.decode(errors="replace")
        stderr = run.stderr.decode(errors="replace")
        (case / "stdout.log").write_text(stdout)
        (case / "stderr.log").write_text(stderr)
        dat_path = case / f"{name}.dat"
        sta_path = case / f"{name}.sta"
        dat = dat_path.read_text(errors="replace") if dat_path.exists() else ""
        sta = sta_path.read_text(errors="replace") if sta_path.exists() else ""
        complete = [match for line in sta.splitlines()
                    if (match := re.match(
                        r"^\s*1\s+1\s+1\s+\d+\s+([\d.Ee+-]+)\s+"
                        r"([\d.Ee+-]+)\s+([\d.Ee+-]+)\s*$", line))]
        if (run.returncode != 0 or stdout.count("Job finished") != 1 or
                len(complete) != 1 or
                abs(float(complete[0].group(1)) - 1.) > 1e-10 or
                re.search(r"(?i)\b(warning|error|fatal)\b", stdout + stderr + sta + dat)):
            raise ValueError("solver diagnostic or incomplete rigid-section job")
        probes = solid.parse_probe_displacements(dat, set(model["probe_node_ids"]))
        reactions = solid.parse_nodal_vectors(
            dat, set(model["boundary_node_ids"]), "forces", model["support_set"])
        response = solid.recover(model, probes, reactions)
        result = {"status": "EXPLORATORY_COMPLETE", "response": response,
                  "seconds": time.perf_counter() - started,
                  "exit_code": run.returncode}
    except BaseException as exc:
        result = {"status": "EXPLORATORY_FAILED", "failure": {
            "type": type(exc).__name__, "message": str(exc)},
            "seconds": time.perf_counter() - started}
    result["files_sha256"] = {
        path.name: _sha(path) for path in case.iterdir() if path.is_file()}
    (case / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"case": name, "status": result["status"],
                      "failure": result.get("failure"),
                      "seconds": result["seconds"]}))
    return 0 if result["status"] == "EXPLORATORY_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
