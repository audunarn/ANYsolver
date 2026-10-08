"""Bounded physical F09 diagnostic for two unlike sections at one junction.

This is private development evidence, not a section range or F09 admission.
The cut-wrench oracle uses rational geometry, material and section compliance;
the separate graph solve uses the product's stored binary64 matrices.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
              "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
THIN_PATH = ROOT / "scripts" / "b2_f09_thin_section_dev.py"
PROBE_PATH = ROOT / "scripts" / "probe_b3_ge_e4_pl_g0_f09_graph_reversal.py"
THIN = runpy.run_path(str(THIN_PATH))
G = THIN["_run_case"].__globals__
F = Fraction
ZERO = F(0)
ONE = F(1)
SECTIONS_M = {"m0": (F(80, 1000), F(3, 1000)),
              "m1": (F(12, 1000), F(3, 1000))}
# One fixed mixed wrench, scaled to keep both sampled members in the linear range.
TIP_WRENCH_EXACT = tuple(value / 10 for value in THIN["TIP_WRENCH_EXACT"])
G["TIP_WRENCH_EXACT"] = TIP_WRENCH_EXACT
G["TIP_WRENCH"] = tuple(float(value) for value in TIP_WRENCH_EXACT)


def _oracle(members, compliance_by_member):
    """Differentiate 1/2 integral(w^T C_member w) for six tip DOFs."""
    energy, response = ZERO, [ZERO] * 6
    station_data = {}
    for member in members:
        length = F(float(member.length_m))
        compliance = compliance_by_member[member.member_id]
        frame = THIN["_frame"](member)
        for station, weight in ((ZERO, 1), (F(1, 2), 4), (ONE, 1)):
            wrench, strain, lever = THIN["_cut"](
                member, station, TIP_WRENCH_EXACT, compliance)
            density = sum((wrench[i] * strain[i] for i in range(6)), ZERO)
            energy += length * weight * density / 12
            for i in range(6):
                direction = [ZERO] * 6
                direction[i] = ONE
                dforce, dcouple = direction[:3], direction[3:]
                arm_moment = THIN["_cross"](lever, dforce)
                dmoment = tuple(dcouple[k] + arm_moment[k] for k in range(3))
                dw = [sum((frame[j][k] * vector[k] for k in range(3)), ZERO)
                      for vector in (dforce, dmoment) for j in range(3)]
                response[i] += length * weight * sum(
                    (dw[k] * strain[k] for k in range(6)), ZERO) / 6
            sign = -ONE if member.node_ids == (2, 1) else ONE
            station_data[(member.member_id, str(station))] = (
                [sign * value for value in wrench],
                [sign * value for value in strain])
    return energy, response, station_data


G["_physical_oracle"] = _oracle


def _make_sections():
    sections = {}
    metadata = {}
    for member_id, (width, depth) in SECTIONS_M.items():
        G["WIDTH_M"] = width
        G["DEPTH_M"] = depth
        _, compliance, stored, principal, area, iy, iz, torsion = THIN["_section"]()
        sections[member_id] = (compliance, stored)
        metadata[member_id] = {
            "width_m": str(width), "depth_m": str(depth),
            "A_m2": str(area), "Iy_m4": str(iy), "Iz_m4": str(iz),
            "J_approx_m4": str(torsion),
            "principal_stiffness": [str(value) for value in principal],
            "stored_stiffness_sha256": sha256(stored.tobytes()).hexdigest(),
        }
    return sections, metadata


def _members(sections, reverse):
    first, second = THIN["PROBE"]["members"](reverse)
    sign = np.diag([-1., 1., -1., -1., 1., -1.])
    first = replace(first, section_id="steel-flat-bar-80x3-345",
                    section=THIN["LinearSection"].generalized(sections["m0"][1]))
    second_stored = sections["m1"][1]
    if reverse:
        second_stored = sign @ second_stored @ sign
    second = replace(second, section_id=("steel-flat-bar-12x3-345-reversed"
                                         if reverse else "steel-flat-bar-12x3-345"),
                     section=THIN["LinearSection"].generalized(second_stored))
    return first, second


def main():
    output = (ROOT / "docs" / "agent_plans" /
              "B3_GE_E4_PL_G0_F09_HETEROGENEOUS_JUNCTION_DEV_V2.json")
    if output.exists():
        raise FileExistsError(f"immutable diagnostic already exists: {output}")
    start = time.monotonic()
    source_paths = [Path(__file__).resolve(), THIN_PATH, PROBE_PATH]
    for symbol in (THIN["LinearSection"], THIN["CompiledB2AffineBatch"],
                   THIN["PROBE"]["PhysicalB2Member"]):
        module = sys.modules[symbol.__module__]
        source_paths.append(Path(module.__file__).resolve())
    source_paths = list(dict.fromkeys(source_paths))
    result = {
        "status": "running",
        "claim": "bounded private development diagnostic; no F09/G0B admission",
        "source_head": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "source_graph": [{"path": str(path),
                          "sha256": sha256(path.read_bytes()).hexdigest()}
                         for path in source_paths],
        "source_path": str(Path(__file__).resolve()),
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "thin_dependency_path": str(THIN_PATH),
        "thin_dependency_sha256": sha256(THIN_PATH.read_bytes()).hexdigest(),
        "python": sys.version.split()[0],
        "geometry_m": {"member_lengths": [2., 1.5],
                       "sections": "m0=80x3 mm, m1=12x3 mm"},
        "material": {"E_Pa": "210000000000", "nu": "3/10",
                     "shear_factors": ["5/6", "5/6"],
                     "torsion": "declared Saint-Venant rectangle approximation"},
        "axis_rotation": {"cos": "4/5", "sin": "3/5"},
        "tip_wrench_exact_N_Nm": [str(v) for v in TIP_WRENCH_EXACT],
        "limits": {"physical_force_moment_relative": 1e-8,
                   "tip_component": "rtol=1e-8, atol=1e-10 (development)",
                   "station_resultant": "rtol=1e-8, atol=1e-7 (development)",
                   "station_strain": "rtol=1e-8, atol=1e-10 (development)",
                   "work_relative": 1e-8,
                   "linear_eligibility": "tip translation <= 1% shortest member; tip rotation <= 0.01 rad",
                   "wall_seconds": 120, "rss_bytes": 2 * 1024**3,
                   "numerical_threads": 1},
        "cases": [],
    }
    try:
        with THIN["threadpool_limits"](limits=1):
            pools = THIN["threadpool_info"]()
            result["threadpools"] = [
                {"internal_api": row.get("internal_api"),
                 "num_threads": row.get("num_threads")} for row in pools]
            if any(row.get("num_threads") != 1 for row in pools):
                raise RuntimeError("numerical thread limit is not effective")
            sections, result["sections"] = _make_sections()
            compliance = {key: value[0] for key, value in sections.items()}
            for reverse in (False, True):
                THIN["_check_budget"](start)
                result["cases"].append(
                    THIN["_run_case"](_members(sections, reverse), compliance, start))
            result["status"] = ("passed_development_diagnostic" if all(
                case["passed_development_diagnostic"] for case in result["cases"])
                else "failed_development_diagnostic")
    except Exception as exc:
        result["status"] = "failed_development_diagnostic"
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        result["elapsed_seconds"] = time.monotonic() - start
        result["peak_rss_bytes"] = (THIN["psutil"].Process().memory_info().peak_wset
                                    if sys.platform == "win32" else
                                    THIN["psutil"].Process().memory_info().rss)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
        print(json.dumps({"status": result["status"],
                          "cases": len(result["cases"]),
                          "output": str(output),
                          "elapsed_seconds": result["elapsed_seconds"]}))
    return 0 if result["status"] == "passed_development_diagnostic" else 1


if __name__ == "__main__":
    raise SystemExit(main())
