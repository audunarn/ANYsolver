"""Observe the unchanged analytical solve; callbacks only, no control changes."""
from __future__ import annotations

import json
import time

import arc_reference
import anysolver.nonlinear_static as nonlinear_static

_solve = arc_reference.solve_static_nonlinear


def observed_solve(*args, **kwargs):
    started = time.perf_counter()
    last_status = [-1.0]
    timings = {"assembly_calls": 0, "assembly_seconds": 0.,
               "factorize_calls": 0, "factorize_seconds": 0.}
    original_assembly = nonlinear_static._assemble_nonlinear_system
    original_factorize = nonlinear_static.factorize

    def assembly(*a, **kw):
        tic = time.perf_counter()
        try:
            return original_assembly(*a, **kw)
        finally:
            timings["assembly_calls"] += 1
            timings["assembly_seconds"] += time.perf_counter()-tic

    def factorize(*a, **kw):
        tic = time.perf_counter()
        try:
            return original_factorize(*a, **kw)
        finally:
            timings["factorize_calls"] += 1
            timings["factorize_seconds"] += time.perf_counter()-tic

    def status(message):
        elapsed = time.perf_counter() - started
        if elapsed - last_status[0] >= .25:
            print(json.dumps(dict(kind="iteration", elapsed=elapsed, message=message,
                                  timings=dict(timings))), flush=True)
            last_status[0] = elapsed

    def progress(event):
        print(json.dumps(dict(kind="accepted_progress", elapsed=time.perf_counter()-started,
                              event_type=event.event_type,
                              data=dict(event))), flush=True)

    kwargs["status_callback"] = status
    kwargs["progress_callback"] = progress
    nonlinear_static._assemble_nonlinear_system = assembly
    nonlinear_static.factorize = factorize
    try:
        return _solve(*args, **kwargs)
    finally:
        nonlinear_static._assemble_nonlinear_system = original_assembly
        nonlinear_static.factorize = original_factorize
        print(json.dumps(dict(kind="phase_totals", timings=timings,
                              elapsed=time.perf_counter()-started)), flush=True)


if __name__ == "__main__":
    arc_reference.solve_static_nonlinear = observed_solve
    arc_reference.main()
