"""Bounded F09 development check of a physical constant-area aspect path.

Question: does changing a real rectangular section's bending/torsion ratios,
while holding its area fixed, separate physical/rounded-assembly error from
sparse solve or binary64 state-storage error on the existing mixed elbow?
The earlier homothety changed every section dimension together; it did not
test this anisotropy path.  Use only three predeclared widths/depths, the
existing exact cut-work and high-precision rounded-graph oracles, and both
member orientations.  A failure is retained by layer; no sweep is extended.

This is private Level-A development evidence, not an admission envelope,
F09/G0B acceptance, or a change to historical public B2 behavior.
"""

from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import runpy
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (ROOT / "docs" / "agent_plans" /
          "B3_GE_E4_PL_G0_F09_CONSTANT_AREA_ASPECT_DEV_V1.json")
H_PATH = ROOT / "scripts" / "b2_f09_physical_homothety_state_dev.py"
H = runpy.run_path(str(H_PATH))
THIN = H["THIN"]
F = Fraction

# First member stays 80 x 3 mm.  The second member keeps A=36 mm^2:
# 12 x 3, 48 x 0.75 and 192 x 0.1875 mm.  Relative weak bending and
# torsion approximately follow depth^2; the entire wrench is scaled by
# 1, 1/16 and 1/256 to stay within the earlier linear-response screen.
CASES = (
    (F(12, 1000), F(3, 1000), F(1)),
    (F(48, 1000), F(3, 4000), F(1, 2)),
    (F(192, 1000), F(3, 16000), F(1, 4)),
)


def main() -> int:
    if OUTPUT.exists():
        raise FileExistsError(f"immutable diagnostic already exists: {OUTPUT}")
    start = time.monotonic()
    graph = H["_source_graph"]()
    graph.append({"path": str(Path(__file__).resolve()),
                  "sha256": sha256(Path(__file__).read_bytes()).hexdigest()})
    record = {
        "status": "running",
        "claim": "private bounded development diagnostic; F09/G0B remain open",
        "question": "Does fixed-area rectangular aspect change reveal an oracle, assembly, sparse-solve, or stored-state limit?",
        "competing_explanations": [
            "rounded assembly departs from the independent physical cut-work oracle",
            "scaled sparse factorization loses a response retained by the rounded matrix",
            "binary64 coordinate storage loses a response retained by factored D,z",
            "all sampled sections and representations remain accurate",
        ],
        "source_head": H["subprocess"].check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "source_graph": graph,
        "python": sys.version.split()[0],
        "numpy": H["np"].__version__,
        "scipy": H["__import__"]("scipy").__version__ if "__import__" in H else __import__("scipy").__version__,
        "fixture": {
            "graph": "rooted 2 m + 1.5 m mixed-wrench elbow; second member also reversed",
            "first_section_m": ["2/25", "3/1000"],
            "second_sections_width_depth_load_fourth_root": [
                [str(w), str(d), str(lam)] for w, d, lam in CASES],
            "second_area_m2": "9/250000",
            "section_law": "same exact rectangular A,Iy,Iz and declared Saint-Venant J approximation as prior thin-section probe; E=210 GPa, nu=0.3, 3-4-5 section-axis rotation",
            "load": "complete mixed tip wrench multiplied by fourth power of listed load factor",
        },
        "criteria": {
            "physical_tip": "rtol=1e-8, atol=1e-10",
            "physical_work_relative": 1e-8,
            "station_resultant": "rtol=1e-8, atol=1e-7",
            "station_strain": "rtol=1e-8, atol=1e-10",
            "sparse_vs_rounded_reference": "rtol=1e-9, atol=1e-12",
            "force_and_moment_balance_relative": 1e-9,
            "linear_eligibility": "tip translation <= 1% shortest member; tip rotation <= 0.01 rad",
            "wall_seconds": 120,
            "rss_bytes": 2 * 1024**3,
            "numerical_threads": 1,
        },
        "cases": [],
    }
    try:
        with THIN["threadpool_limits"](limits=1):
            pools = THIN["threadpool_info"]()
            record["threadpools"] = [
                {"internal_api": row.get("internal_api"),
                 "num_threads": row.get("num_threads")} for row in pools]
            if any(row.get("num_threads") != 1 for row in pools):
                raise RuntimeError("numerical thread limit is not effective")
            first = H["_section"](*H["FIRST_SECTION_M"])
            record["first_section"] = first["metadata"]
            for width, depth, load_root in CASES:
                THIN["_check_budget"](start)
                second = H["_section"](width, depth)
                for reverse in (False, True):
                    try:
                        case = H["_run_case"](
                            first, second, load_root, reverse, start)
                    except Exception as exc:
                        case = {
                            "orientation": "reversed-second" if reverse else "forward",
                            "classification": "case_execution_failed",
                            "passed_development_diagnostic": False,
                            "error": {"type": type(exc).__name__, "message": str(exc)},
                        }
                    case["load_fourth_root"] = str(load_root)
                    case["second_section"] = second["metadata"]
                    record["cases"].append(case)
            record["status"] = ("passed_development_diagnostic" if all(
                case["passed_development_diagnostic"] for case in record["cases"])
                else "completed_with_development_failures")
    except Exception as exc:
        record["status"] = "failed_development_diagnostic"
        record["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        record["elapsed_seconds"] = time.monotonic() - start
        record["peak_rss_bytes"] = (THIN["psutil"].Process().memory_info().peak_wset
                                    if sys.platform == "win32" else
                                    THIN["psutil"].Process().memory_info().rss)
        OUTPUT.write_text(json.dumps(record, indent=2, sort_keys=True,
                                     allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": record["status"],
                          "cases": len(record["cases"]),
                          "passed": sum(case["passed_development_diagnostic"]
                                        for case in record["cases"]),
                          "elapsed_seconds": record["elapsed_seconds"],
                          "peak_rss_bytes": record["peak_rss_bytes"],
                          "output": str(OUTPUT)}))
    return 0 if record["status"] == "passed_development_diagnostic" else 1


if __name__ == "__main__":
    raise SystemExit(main())
