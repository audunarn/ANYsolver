"""Preserve accepted arrays/history and gracefully stop the unchanged DC path.

Run only under the task harness. The 60-second cancellation limit is a diagnostic
boundary, never a solver completion or scientific acceptance claim.
"""
from __future__ import annotations
import copy
import inspect
import json
from pathlib import Path
import pickle
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests"))
from test_nonlinear_beam_shell_slice3_continuation import _dc_case
from anysolver.control import CancellationToken, SolveCancelled
from assessment_support import source_identity
import anysolver.nonlinear_static as ns


def main():
    output = Path(sys.argv[1])
    output.mkdir(exist_ok=False)
    (output / "identity.json").write_text(json.dumps(source_identity(), indent=2))
    start = time.perf_counter()
    accepted = []
    real_snapshot = ns._increment_snapshot

    def save_snapshot(*a, **kw):
        snapshot = real_snapshot(*a, **kw)
        row = dict(index=len(accepted)+1, control=float(snapshot.control_value),
                   lam=float(snapshot.load_factor), elapsed=time.perf_counter()-start)
        payload = dict(row, displacements=np.array(snapshot.displacements, copy=True),
                       element_states=copy.deepcopy(dict(snapshot.element_states)))
        with (output / f"accepted-{len(accepted)+1:04d}.pkl").open("xb") as stream:
            pickle.dump(payload, stream, protocol=5)
        accepted.append(row)
        print(json.dumps(dict(kind="accepted_checkpoint", **row)), flush=True)
        return snapshot

    class TimedToken(CancellationToken):
        def raise_if_cancelled(self, stage=""):
            if time.perf_counter()-start >= 60 and not self.is_cancelled:
                self.cancel("60-second live diagnostic checkpoint")
                frame = inspect.currentframe().f_back
                try:
                    for _ in range(8):
                        if frame is None or frame.f_code.co_name == "_solve_static_displacement_control":
                            break
                        frame = frame.f_back
                    if frame is not None and frame.f_code.co_name == "_solve_static_displacement_control":
                        c = frame.f_locals
                        payload = {key: copy.deepcopy(c[key]) for key in (
                            "q", "lam", "target", "T", "u0", "row_full",
                            "q_attempt_start", "lam_attempt_start", "committed_states",
                            "iteration", "step_index", "attempt_start_control",
                            "attempt_fraction", "interval_cutbacks", "cutbacks_this_step",
                            "accepted_subincrements", "control_attempts_total",
                            "control_cutbacks_total", "min_control_subincrement",
                        ) if key in c}
                        payload["committed_states"] = copy.deepcopy(dict(c["committed_states"]))
                        with (output / "cancelled-attempt.pkl").open("xb") as stream:
                            pickle.dump(payload, stream, protocol=5)
                        scalar = {k: float(v) for k, v in payload.items()
                                  if isinstance(v, (int, float, np.integer, np.floating))}
                        print(json.dumps(dict(kind="cancelled_attempt", **scalar)), flush=True)
                finally:
                    del frame
            super().raise_if_cancelled(stage)

    token = TimedToken()
    ns._increment_snapshot = save_snapshot
    try:
        try:
            result = _dc_case("direct", -.20, 12, cancellation_token=token,
                              emit_restart_checkpoint=False)["result"]
        except SolveCancelled as error:
            summary = dict(outcome="diagnostic_cancelled", reason=str(error))
        else:
            summary = dict(outcome="returned", status=result.status, reason=result.stop_reason,
                           lam=float(result.load_factor))
    finally:
        ns._increment_snapshot = real_snapshot
    summary.update(diagnostic_only=True, scientific_completion_claim=False,
                   accepted_count=len(accepted), last_accepted=accepted[-1] if accepted else None,
                   elapsed=time.perf_counter()-start)
    (output / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
