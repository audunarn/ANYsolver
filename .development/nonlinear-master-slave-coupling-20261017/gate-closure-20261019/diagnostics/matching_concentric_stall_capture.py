"""Observe ONE unchanged matching/concentric nx32/30-degree force solve.

Prepare/run only under separate task-harness authority. No replay, assembly
recomputation, Newton modification or constitutive update is performed here.
Pickles contain trusted local diagnostic data, not solver restart checkpoints.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path
import pickle
import sys
import time


PHASE = Path(__file__).resolve().parents[1]
TASK = PHASE.parent
REPO = TASK.parents[1]
# Import the original fixture/oracle, never another diagnostic's monkeypatches.
sys.path.insert(0, str(TASK / "diagnostics"))

import numpy as np
import arc_reference as arc
import anysolver.nonlinear_static as ns


class DiagnosticPlateauCaptured(BaseException):
    """Intentional observation stop; NEVER an equilibrium/completion result."""


class InstrumentationLayoutError(BaseException):
    """Fail closed if the inspected production force-frame contract changes."""


def array_hash(value):
    a = np.ascontiguousarray(np.asarray(value))
    h = hashlib.sha256()
    h.update(str(a.dtype).encode()); h.update(str(a.shape).encode())
    h.update(a.tobytes())
    return h.hexdigest()


def plain(value):
    """Bounded metadata only: full arrays/history belong in raw pickles."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else str(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if isinstance(value, np.ndarray):
        return {"shape": list(value.shape), "dtype": str(value.dtype),
                "sha256": array_hash(value)}
    return repr(value)[:500]


def source_identity():
    files = [REPO / "src/anysolver" / n for n in (
        "nonlinear_static.py", "nonlinear_performance.py", "elements.py",
        "corotational.py", "_corotational_batch.py", "_director_trace.py",
        "mesh_gen.py", "nonlinear_state.py", "nonlinear_restart.py")]
    files += [Path(__file__).resolve(), TASK / "diagnostics/arc_reference.py",
              TASK / "diagnostics/assessment_support.py",
              TASK / "analytical_derivation.md"]
    return {"sha256": {p.relative_to(REPO).as_posix():
                        hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in files if p.exists()},
            "import_origins": {"nonlinear_static": str(Path(ns.__file__).resolve()),
                               "arc_reference": str(Path(arc.__file__).resolve())}}


def force_frames():
    """Find production locals through wrappers; do not retain live frames."""
    frame = inspect.currentframe()
    inner = outer = None
    expected = Path(ns.__file__).resolve()
    try:
        for _ in range(40):
            if frame is None:
                break
            if Path(frame.f_code.co_filename).resolve() == expected:
                if frame.f_code.co_name == "_newton_increment":
                    inner = dict(frame.f_locals)
                elif frame.f_code.co_name == "_solve_static_nonlinear_under_lease":
                    outer = dict(frame.f_locals)
            frame = frame.f_back
    finally:
        del frame
    return inner, outer


def owned(value):
    # Mapping-backed history is copied, never committed, discarded or evolved.
    if hasattr(value, "items"):
        return copy.deepcopy(dict(value.items()))
    return copy.deepcopy(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    counter = {"raw": 0, "accepted": 0, "iteration": 0,
               "assembly_calls": 0, "assembly_seconds": 0.,
               "factorize_calls": 0, "factorize_seconds": 0.}
    records = []
    last_accepted = {}
    floor_sequence = []
    increment_serial = 0
    floor_status_count = 0
    terminal = {"diagnostic_only": True, "solver_completion_claim": False,
                "status": "started"}

    def atomic_json(path, payload):
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(plain(payload), stream, indent=2, allow_nan=False)
            stream.flush(); os.fsync(stream.fileno())
        temporary.replace(path)

    def event(kind, **fields):
        row = {"kind": kind, "elapsed_seconds": time.perf_counter()-started,
               **fields}
        with (out / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(plain(row), allow_nan=False) + "\n")
            stream.flush()
        return row

    def raw_dump(label, payload):
        counter["raw"] += 1
        path = out / f"raw-{counter['raw']:04d}-{label}.pkl"
        temporary = path.with_suffix(".tmp")
        with temporary.open("xb") as stream:
            pickle.dump(payload, stream, protocol=5)
            stream.flush(); os.fsync(stream.fileno())
        temporary.replace(path)
        event("raw_saved", path=path.name, label=label,
              accepted=payload.get("accepted", False), stamp=payload.get("stamp"))
        return path.name

    def context(required=True):
        c, outer = force_frames()
        if c is None:
            if required:
                raise InstrumentationLayoutError("production force Newton frame not found")
            return None
        if outer is None:
            raise InstrumentationLayoutError("production force outer frame not found")
        necessary = ("u", "q_trial", "q_start", "path_factor", "reference",
                     "iteration", "residual", "residual_norm", "F_int", "K_T",
                     "trial_states", "committed_states", "tolerance")
        missing = [k for k in necessary if k not in c]
        missing += ["outer."+k for k in ("T", "model", "lam", "step_index")
                    if k not in outer]
        if missing:
            raise InstrumentationLayoutError("missing force locals: " + ",".join(missing))
        return c, outer

    def stamp(c, outer):
        return {"increment_serial": increment_serial,
                "accepted_step_index": int(outer["step_index"]),
                "accepted_load_factor": float(outer["lam"]),
                "trial_load_factor": float(c["path_factor"]),
                "iteration": int(c["iteration"]),
                "u_sha256": array_hash(c["u"]),
                "q_sha256": array_hash(c["q_trial"])}

    def near_floor(c):
        reference = float(c["reference"]); tol = float(c["tolerance"])
        norm = float(c["residual_norm"])
        return (np.isfinite(norm) and reference > 0. and tol > 0.
                and 1. <= norm/(reference*tol) <= 5.)

    def capture(c, outer, stage, matrix=None, rhs=None, delta=None, linear_meta=None):
        actual = stamp(c, outer)
        fields = {k: owned(c[k]) for k in (
            "u", "q_trial", "q_start", "residual", "F_int", "K_T",
            "trial_states", "committed_states")}
        for k in ("F_ext_red", "K_ext_red"):
            if k in c:
                fields[k] = owned(c[k])
        for k in ("T", "u0", "prescribed_base", "prescribed_slope", "F_prop",
                  "F_const", "F_prop_reduced", "F_const_reduced",
                  "last_external_force_full"):
            if k in outer:
                fields[k] = owned(outer[k])
        # Dead-load projection reuse may leave last_external_force_full=None.
        # This is explicitly labelled an algebraic observation of stored loads.
        if (outer.get("load_program") is None and "F_const" in outer
                and "F_prop" in outer):
            fields["full_dead_load_from_stored_vectors"] = (
                np.asarray(outer["F_const"]).copy()
                + float(c["path_factor"])*np.asarray(outer["F_prop"]))
        model = outer["model"]
        references = {}
        for name in ("_corotational_cache", "_corotational_centered_shell_cache"):
            cached = getattr(model.mesh, name, None)
            if cached is not None:
                references[name] = {"signature": owned(cached[0]), "elements": {
                    int(eid): {key: owned(getattr(ref, key)) for key in (
                        "coordinates", "centroid", "frame", "category", "center_dN")}
                    for eid, ref in cached[1].items()}}
        fields.update(
            diagnostic_only=True, accepted=False,
            state_meaning="current uncommitted Newton iterate, not accepted equilibrium",
            stage=stage, stamp=actual, reference=float(c["reference"]),
            tolerance=float(c["tolerance"]), residual_norm=float(c["residual_norm"]),
            relative_residual=float(c["residual_norm"])/float(c["reference"]),
            line_search_mode=c.get("line_search_mode"),
            num_layers=int(c.get("num_layers", outer.get("num_layers", -1))),
            kinematics=c.get("kinematics", outer.get("kinematics")),
            resolved_corotational_tangent=c.get("resolved_corotational_tangent",
                                               outer.get("resolved_corotational_tangent")),
            rotating_map_active=outer.get("rotating_mpc_map") is not None,
            references=references,
            matrix=None if matrix is None else matrix.copy(),
            rhs=None if rhs is None else np.asarray(rhs).copy(),
            delta=None if delta is None else np.asarray(delta).copy(),
            linear_system_available=matrix is not None,
            linear_metadata=linear_meta,
            unavailable=[k for k in ("T", "u0", "prescribed_base", "prescribed_slope",
                                     "F_ext_red", "K_ext_red") if k not in fields],
        )
        filename = raw_dump("unaccepted-"+stage, fields)
        records.append({"path": filename, "stage": stage, "stamp": actual,
                        "relative_residual": fields["relative_residual"]})
        return actual, filename

    real_solve = arc.solve_static_nonlinear
    real_factorize, real_assemble = ns.factorize, ns._assemble_nonlinear_system
    real_snapshot = ns._increment_snapshot

    def status(message):
        nonlocal increment_serial, floor_status_count
        c, outer = context()
        if int(c["iteration"]) == 1:
            increment_serial += 1
            floor_sequence.clear()
        counter["iteration"] += 1
        row = stamp(c, outer)
        row.update(message=message, reference=float(c["reference"]),
                   tolerance=float(c["tolerance"]),
                   relative_residual=float(c["residual_norm"])/float(c["reference"]),
                   line_search_mode=c.get("line_search_mode"))
        event("newton_iteration", **row)
        # Small compact stdout; the full unthrottled observer remains on disk.
        print(json.dumps(plain({"kind": "iteration", **row}), allow_nan=False), flush=True)
        if near_floor(c):
            floor_status_count += 1
            # At most 16 pre-factor dumps; post-solve states remain available.
            if floor_status_count <= 16:
                capture(c, outer, "before-factorization")
        else:
            floor_sequence.clear()

    class Handle:
        def __init__(self, handle, matrix, fact_stamp, metadata):
            self._handle, self._matrix = handle, matrix
            self._stamp, self._metadata = fact_stamp, metadata

        def __getattr__(self, name):
            return getattr(self._handle, name)

        def solve(self, rhs):
            c, outer = context()
            if stamp(c, outer) != self._stamp:
                raise InstrumentationLayoutError("factorization/solve state stamp changed")
            if near_floor(c):
                capture(c, outer, "before-linear-solve", self._matrix, rhs,
                        linear_meta=self._metadata)
            value = self._handle.solve(rhs)
            c, outer = context()
            if stamp(c, outer) != self._stamp:
                raise InstrumentationLayoutError("linear solve changed Newton state stamp")
            if near_floor(c):
                actual, filename = capture(c, outer, "after-linear-solve",
                    self._matrix, rhs, value, self._metadata)
                residual = float(c["residual_norm"])/float(c["reference"])
                if (floor_sequence and
                        (actual["increment_serial"] != floor_sequence[-1]["increment_serial"]
                         or actual["trial_load_factor"] != floor_sequence[-1]["trial_load_factor"]
                         or actual["iteration"] != floor_sequence[-1]["iteration"]+1)):
                    floor_sequence.clear()
                floor_sequence.append({**actual, "relative_residual": residual,
                                       "path": filename})
                last = floor_sequence[-4:]
                if len(last) == 4:
                    ratios = [r["relative_residual"] for r in last]
                    if max(ratios)/min(ratios) <= 1.05:
                        event("diagnostic_plateau_stop", criterion="four consecutive same-load near-floor Newton states; max/min<=1.05", sequence=last)
                        raise DiagnosticPlateauCaptured("same-load near-floor sequence saved")
            return value

    def factorize(matrix, *a, **kw):
        found = context(required=False)
        matrix_copy = matrix.copy() if found is not None else None
        fact_stamp = stamp(*found) if found is not None else None
        tic = time.perf_counter()
        try:
            handle = real_factorize(matrix, *a, **kw)
        finally:
            counter["factorize_calls"] += 1
            counter["factorize_seconds"] += time.perf_counter()-tic
        if found is None:
            return handle
        return Handle(handle, matrix_copy, fact_stamp,
                      {"args": plain(a), "kwargs": plain(kw),
                       "backend": getattr(handle, "backend_name", None),
                       "status": getattr(handle, "status", None)})

    def assembly(*a, **kw):
        tic = time.perf_counter()
        try:
            return real_assemble(*a, **kw)
        finally:
            counter["assembly_calls"] += 1
            counter["assembly_seconds"] += time.perf_counter()-tic

    def snapshot(*a, **kw):
        value = real_snapshot(*a, **kw)
        counter["accepted"] += 1
        last_accepted.clear()
        last_accepted.update(step_index=int(value.step_index),
                             load_factor=float(value.load_factor),
                             u_sha256=array_hash(value.displacements))
        raw_dump("accepted", {"accepted": True,
            "state_meaning": "production committed accepted increment snapshot",
            "stamp": dict(last_accepted),
            "step_index": int(value.step_index), "load_factor": float(value.load_factor),
            "u": np.asarray(value.displacements).copy(),
            "element_states": owned(value.element_states),
            "control_value": value.control_value})
        return value

    def progress(value):
        event("accepted_progress_observer", event_type=value.event_type,
              data=dict(value))

    def solve(*a, **kw):
        expected = dict(kinematics="corotational", corotational_tangent="work_conjugate",
                        num_steps=12, max_iterations=40, tolerance=1e-8)
        if any(kw.get(k) != v for k, v in expected.items()):
            raise InstrumentationLayoutError("original arc solver controls changed")
        if any(k in kw for k in ("initial_displacements", "initial_element_states",
                                  "restart_checkpoint", "displacement_control")):
            raise InstrumentationLayoutError("capture must start original force fixture from zero")
        model = a[0]
        fixture = {"nodes": {int(k): {"coordinates": n.coords(), "dofs": n.dofs}
                               for k, n in model.mesh.nodes.items()},
                   "element_classes": {int(k): type(e).__module__+"."+type(e).__qualname__
                                       for k, e in model.mesh.elements.items()},
                   "original_solver_kwargs": owned(kw),
                   "oracle": arc.oracle(0., 30.), "nx": 32, "coupling": "matching",
                   "rebuild": "arc_reference.build_model(32,'matching',arc_reference.oracle(0.,30.))"}
        raw_dump("fixture-inputs", {"accepted": False, "fixture": fixture})
        # Observers/saved snapshots only; no controls, solver policy or physics.
        kw.update(status_callback=status, progress_callback=progress,
                  record_increment_snapshots=True)
        value = real_solve(*a, **kw)
        terminal_u = np.asarray(value.displacements).copy()
        corresponds = bool(last_accepted and
            last_accepted["u_sha256"] == array_hash(terminal_u) and
            last_accepted["load_factor"] == float(value.load_factor))
        raw_dump("solver-returned-state", {
            "accepted": corresponds,
            "state_meaning": "solver returned state; acceptance only from exact last accepted u/load correspondence",
            "last_accepted_stamp": dict(last_accepted),
            "u": terminal_u, "element_states": owned(value.element_states),
            "load_factor": float(value.load_factor), "status": value.status,
            "stop_reason": value.stop_reason, "info": owned(value.info),
            "steps": copy.deepcopy(value.steps),
        })
        event("solver_returned", status=value.status, stop_reason=value.stop_reason,
              load_factor=float(value.load_factor), step_count=len(value.steps),
              u_sha256=array_hash(terminal_u))
        return value

    identity_before = source_identity()
    atomic_json(out / "identity-before.json", identity_before)
    atomic_json(out / "plan.json", {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "argv": sys.argv, "fixture": {"nx": 32, "coupling": "matching",
        "eccentricity": 0., "angle_degrees": 30.},
        "controls": {"num_steps": 12, "max_iterations": 40, "tolerance": 1e-8},
        "observers_only": True, "external_timeout_planned_seconds": 120,
        "runtime_environment": {k: os.environ.get(k) for k in (
            "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
            "NUMBA_NUM_THREADS", "NUMBA_DISABLE_JIT", "PYTHONPATH")},
        "stop_rule": "after saved solve of four consecutive same-increment same-load states in [1,5]*actual tolerance with residual max/min<=1.05; diagnostic-only",
    })
    arc.solve_static_nonlinear = solve
    ns.factorize, ns._assemble_nonlinear_system = factorize, assembly
    ns._increment_snapshot = snapshot
    try:
        result = arc.run_case(32, "matching", 0., 30.)
        atomic_json(out / "arc-result.json", result)
        terminal.update(status="solver_returned", original_result=result,
                        solver_completion_claim=bool(result.get("complete_and_equilibrated")))
    except DiagnosticPlateauCaptured as exc:
        terminal.update(status="diagnostic_plateau_captured", detail=str(exc))
    except BaseException as exc:
        terminal.update(status="exception", exception_type=type(exc).__name__, detail=str(exc))
        raise
    finally:
        arc.solve_static_nonlinear = real_solve
        ns.factorize, ns._assemble_nonlinear_system = real_factorize, real_assemble
        ns._increment_snapshot = real_snapshot
        after = source_identity()
        terminal.update(counters=counter, captures=records,
                        elapsed_seconds=time.perf_counter()-started,
                        source_hashes_unchanged=identity_before["sha256"] == after["sha256"])
        atomic_json(out / "identity-after.json", after)
        atomic_json(out / "terminal.json", terminal)
        event("terminal", status=terminal["status"], counters=counter)
        print(json.dumps(plain({"kind": "terminal", "status": terminal["status"],
                               "counters": counter}), allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
