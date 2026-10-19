"""Summarize retained registered assessments; performs no new solves."""
from __future__ import annotations

import json
from pathlib import Path
import sys

from mesh_study import summarize as mesh_summary
from arc_reference import summarize as arc_summary


def main():
    task = Path(__file__).resolve().parents[1]
    paths = sorted((task / "evidence").glob("final-assessment-*/result.json"))
    rows = [json.loads(p.read_text()) for p in paths]
    mesh_names = ["R1", "R2", "R3", "R4", "M1", "M2", "M3", "M4", "P1", "P2", "P3", "P4"]
    arc_cases = [(c, e, a, n) for c in ("matching", "nonmatching")
                 for e in (0.0, 0.002) for a in (30.0, 60.0) for n in (8, 16, 32)]
    mesh_present = {r["case"] for r in rows if r.get("kind") == "mesh"}
    arc_present = {(r["coupling"], r["eccentricity"], r["angle_degrees"], r["nx"])
                   for r in rows if r.get("kind") == "analytical_arc"}
    mesh, arc = mesh_summary(paths), arc_summary(paths)
    attempts = []
    for path in sorted((task / "evidence").glob("final-assessment-*/receipt.json")):
        r = json.loads(path.read_text())
        attempts.append({"name": r["name"], "status": r["status"],
                         "process_wall_seconds": r["process_wall_seconds"],
                         "receipt": str(path)})
    report = {
        "scope": "development acceptance only; no qualification or release",
        "result_paths": [str(p) for p in paths], "attempts": attempts,
        "missing_mesh_cases": [n for n in mesh_names if n not in mesh_present],
        "missing_base_arc_cases": [list(c) for c in arc_cases if c not in arc_present],
        "mesh": mesh, "analytical": arc,
        "all_required_assessments_passed": bool(mesh["passed"] and arc["passed"]),
    }
    payload = json.dumps(report, indent=2, allow_nan=False) + "\n"
    (task / "assessment-summary.json").write_text(payload)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(payload)
    print(json.dumps({"mesh_results": len(mesh_present), "arc_results": len(arc_present),
                      "mesh_passed": mesh["passed"], "analytical_passed": arc["passed"],
                      "report": str(task / "assessment-summary.json")}))


if __name__ == "__main__":
    main()
