"""Saved-only reference-linear rigid cut-trace work-map check for V7/V5."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
import time

import numba
import psutil
from threadpoolctl import threadpool_info


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from scripts import r8_bl5_weak_continuum_reference as continuum

OUTPUT = HERE / "v8-rigid-cut-work.json"


def saved(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def dot(a: list[float], b: list[float]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def rigid(translation: list[float], spin: list[float], arm: list[float]) -> list[float]:
    x, y, z = spin
    a, b, c = arm
    return [translation[0] + y * c - z * b,
            translation[1] + z * a - x * c,
            translation[2] + x * b - y * a]


def main() -> None:
    start = time.perf_counter()
    if OUTPUT.exists():
        raise SystemExit("V8 output exists; preserve the earlier postprocess")
    process = psutil.Process()
    process.cpu_affinity([0])
    pools = threadpool_info()
    if (process.cpu_affinity() != [0] or numba.config.DISABLE_JIT != 1 or
            numba.get_num_threads() != 1 or not pools or
            any(pool["num_threads"] != 1 for pool in pools)):
        raise ValueError("Effective CPU/thread/JIT settings differ")
    v7, v7_sha = saved(HERE / "case-v7-nodal-port/result.json")
    native, native_sha = saved(HERE / "case-v5/beam-solved.json")
    seam, seam_sha = saved(HERE / "v5-native-seam-work-postprocess-v1.json")
    preflight, preflight_sha = saved(HERE / "case-v5/preflight.json")
    if (v7["identity"] != "BL5_V7_SAVED_C3D20_NODAL_PORT_DEV_V1" or
            native["status"] != "DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED" or
            seam["identity"] != "BL5_V5_SAVED_NATIVE_SEAM_WORK_POSTPROCESS_V1" or
            v7["source_sha256"]["preflight"] != preflight_sha or
            seam["source_sha256"]["result"] != hashlib.sha256(
                (HERE / "case-v5/result.json").read_bytes()).hexdigest()):
        raise ValueError("Saved V5/V7 identities or source bindings changed")
    if (hashlib.sha256(Path(continuum.__file__).read_bytes()).hexdigest() !=
            preflight["source_sha256"]["continuum"]):
        raise ValueError("Saved continuum model source changed")
    model = continuum.specimen()
    if model["model_sha256"] != preflight["model_sha256"]:
        raise ValueError("Saved physical model changed")
    center = v7["center_m"]
    if v7["cut_x_m"] != .5 or len(center) != 3:
        raise ValueError("Expected original midspan section")
    q = native["physical_coordinates"]
    if len(q) != 78 or not all(math.isfinite(value) for value in q):
        raise ValueError("Expected finite native physical/retained coordinates")
    translation = q[12:15]
    node_spin = q[15:18]
    spins = dict(left=q[33:36], right=q[54:57])
    station = next(row for row in seam["stations"] if row["x_m"] == .5)
    jump = [b - a for a, b in zip(spins["left"], spins["right"], strict=True)]
    if max(abs(a - b) for a, b in zip(jump, station["retained_spin_jump_rad"], strict=True)) > 1e-16:
        raise ValueError("Native saved spin jump changed")

    full = {}
    contracted = {}
    for name in ("left", "right"):
        action = v7["sides"][name]["cut_port_nodal_action_N"]
        terms = []
        for label, force in action.items():
            node = int(label)
            point = model["physical_nodes"][node]
            arm = [point[i] - center[i] for i in range(3)]
            terms.append(dot(force, rigid(translation, spins[name], arm)))
        full[name] = math.fsum(terms)
        wrench = v7["sides"][name]["cut_port_wrench_N_Nm"]
        contracted[name] = dot(wrench[:3], translation) + dot(wrench[3:], spins[name])
    full_total = math.fsum(full.values())
    contracted_total = math.fsum(contracted.values())
    if abs(full_total - contracted_total) > 1e-13:
        raise ValueError("Full nodal and rigid six-wrench work disagree")
    common_spin = [
        dot(v7["sides"][name]["cut_port_wrench_N_Nm"][:3], translation) +
        dot(v7["sides"][name]["cut_port_wrench_N_Nm"][3:], node_spin)
        for name in ("left", "right")]
    common_work = math.fsum(common_spin)
    native_work = station["balanced_first_variation_work_J"]
    record = dict(
        identity="BL5_V8_SAVED_RIGID_CUT_WORK_MAP_DEV_V1",
        status="DEVELOPMENT_ALGEBRAIC_MAP_ONLY_NOT_QUALIFIED",
        input_sha256=dict(v7=v7_sha, native=native_sha, seam=seam_sha,
                          preflight=preflight_sha),
        section_x_m=.5, center_m=center,
        translation_m=translation, shared_node_spin_rad=node_spin,
        left_cell_spin_rad=spins["left"], right_cell_spin_rad=spins["right"],
        full_nodal_outward_work_by_side_J=full,
        rigid_wrench_outward_work_by_side_J=contracted,
        full_nodal_outward_work_J=full_total,
        rigid_wrench_outward_work_J=contracted_total,
        nodal_vs_wrench_work_error_J=full_total - contracted_total,
        common_node_spin_work_J=common_work,
        broken_trace_outward_work_J=full_total - common_work,
        native_endpoint_log_reference_work_J=native_work,
        outward_plus_native_work_J=full_total + native_work,
        source_evaluation_wall_seconds=time.perf_counter() - start,
        runtime=dict(cpu_affinity=process.cpu_affinity(),
                     numba_disable_jit=int(numba.config.DISABLE_JIT),
                     numba_threads=int(numba.get_num_threads()),
                     loaded_threadpools=pools),
        solver_executions=0,
        interpretation=(
            "The reference-linear rigid cut lift uses each native retained "
            "half-cell spin on the corresponding saved C3D20 nodal port. "
            "Outward cut action is opposite the native endpoint-log action. "
            "Agreement verifies this restricted dual map and sign only; "
            "identical source balance largely fixes its moment scale. "
            "It does not measure port flexibility, allocate V5 body work, "
            "qualify BL5, or execute F03."))
    OUTPUT.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n",
                      encoding="utf-8")
    print(json.dumps({key: record[key] for key in (
        "full_nodal_outward_work_J", "outward_plus_native_work_J",
        "nodal_vs_wrench_work_error_J", "solver_executions")}))


if __name__ == "__main__":
    main()
