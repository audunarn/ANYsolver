"""Phase/cost probe for the 2x2 driver fixture under the guard environment.

Attempt-01 showed that one real 2x2 macro step does not complete inside a
60 s job under NUMBA_DISABLE_JIT=1. This probe does not change any
production mechanic: it wraps the certificate/report/increment entry points
with call-through timing recorders, dumps repeated faulthandler stack
traces into the attempt temp directory, and only if the half solve actually
finishes asserts the same explicit fixture gates (completed single step
with real active contact). The log file is the evidence; no per-solve
timing is invented from a timeout.
"""
import faulthandler
import os
import time

import numpy as np

from test_general_contact_admission_globalization_driver_small_patch import (
    _assert_active_contact,
    _case,
    _enabled,
    _solve,
)
from anysolver.general_contact import s3_patch_static, static_path
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager


def _probe(monkeypatch, log, t0):
    counts = {}

    def wrap(owner, name, label):
        original = getattr(owner, name)

        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return original(*args, **kwargs)
            finally:
                entry = counts.setdefault(
                    label, {"calls": 0, "seconds": 0.0, "last_kwargs": None})
                entry["calls"] += 1
                entry["seconds"] += time.perf_counter() - start
                entry["last_kwargs"] = {
                    key: (value if isinstance(value, (int, float, str, bool,
                                                       type(None)))
                          else repr(value)[:80])
                    for key, value in kwargs.items()}

        setattr(owner, name, wrapper)
        return original

    wrap(s3_patch_static, "matching_projection_swept_lower", "matching")
    wrap(GeneralS3PatchManager, "evaluate", "evaluate")
    wrap(GeneralS3PatchManager, "admissible_step_fraction", "fraction")
    wrap(static_path, "solve_semismooth_increment", "increment")
    witness = getattr(s3_patch_static, "overlap_violating_point_witness",
                      None)
    if witness is not None:
        wrap(s3_patch_static, "overlap_violating_point_witness", "witness")
    return counts


def test_small_patch_solve_phase_probe(monkeypatch):
    log_path = os.path.join(os.environ["TEMP"], "small_patch_probe.log")
    log = open(log_path, "w", buffering=1)
    t0 = time.perf_counter()

    def mark(message):
        log.write(f"{time.perf_counter()-t0:9.3f} {message}\n")

    mark("probe start")
    model, definition, settings, program = _case()
    mark("fixture built")
    counts = _probe(monkeypatch, log, t0)
    faulthandler.dump_traceback_later(20.0, repeat=True, file=log)
    mark("faulthandler armed (20 s repeat); half solve starts")
    result = _solve(model, definition, _enabled(settings), program,
                    max_load_factor=0.5, emit_restart_checkpoint=True)
    faulthandler.cancel_dump_traceback_later()
    mark("half solve returned")
    for label, entry in sorted(counts.items()):
        mark(f"count {label} calls={entry['calls']} "
             f"seconds={entry['seconds']:.3f} "
             f"last_kwargs={entry['last_kwargs']}")
    assert result.status == "completed" and len(result.steps) == 1
    checkpoint = result.to_restart_checkpoint()
    _assert_active_contact(checkpoint["path_state"]["history"][0])
    mark("fixture gates asserted (completed, active contact)")
    log.close()
