"""Affected public partial-front lifecycle/restart and old-identity rejection."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[2]
SUPPORT = ROOT / "docs/d1_review_support"
STEM = "d2_partial_swept_workflow_v1_20260930"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(name, arguments):
    sys.argv = [str(SUPPORT / name), *arguments]
    try:
        runpy.run_path(str(SUPPORT / name), run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (None, 0):
            raise


def main():
    import anysolver
    assert Path(anysolver.__file__).resolve().is_relative_to(ROOT / "src")
    assert all(os.environ.get(name) == "1" for name in
               ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"))
    baseline = SUPPORT / (STEM + ".baseline.json")
    restart = SUPPORT / (STEM + ".restart.json")
    inputs = SUPPORT / (STEM + ".inputs.json")
    result = SUPPORT / (STEM + ".json")
    assert not any(p.exists() for p in (baseline, restart, inputs, result))
    files = {str(p.relative_to(ROOT)): digest(p) for p in
             sorted((ROOT / "src/anysolver").rglob("*.py"))}
    files.update({name: digest(SUPPORT / name) for name in
                  ("d2_active_prescribed_edge_dev.py", "d2_moving_edge_restart_dev.py",
                   "d2_projected_penalty_shell_dev.py", Path(__file__).name)})
    inputs.write_text(json.dumps({"scope": "development_only", "source_sha256": files,
        "time_limit_s": 180, "memory_limit_bytes": 1073741824,
        "path": "existing ten-pose partial front press/slide/open/recontact",
        "restart": "authentic fresh-model active/open prefix, unchanged gates",
        "old_identity": "reject unmodified older partial swept checkpoint"}, indent=2) + "\n")
    invoke("d2_active_prescribed_edge_dev.py", ["--slide", "--output", str(baseline)])
    invoke("d2_moving_edge_restart_dev.py", ["--reference", str(baseline), "--output", str(restart)])
    from anysolver import solve_static_nonlinear
    from anysolver.nonlinear_restart import load_nonlinear_checkpoint, NonlinearCheckpointError
    from docs.d1_review_support.d2_active_prescribed_edge_dev import build
    old = SUPPORT / "d2_moving_edge_restart_v1_20260930_open.checkpoint.json"
    original = old.read_bytes()
    model, definition, settings, program = build(slide=True)
    rejection = None
    try:
        solve_static_nonlinear(model, contact=definition, contact_settings=settings,
            contact_path_program=program, restart_checkpoint=load_nonlinear_checkpoint(original),
            max_iterations=18, tolerance=1e-8)
    except NonlinearCheckpointError as exc:
        rejection = str(exc)
    checks = {"baseline": json.loads(baseline.read_text())["development_checks_met"],
              "authentic_restart": json.loads(restart.read_text())["development_checks_met"],
              "old_analysis_rejected": rejection is not None and "analysis" in rejection.lower(),
              "old_bytes_unchanged": original == old.read_bytes(),
              "source_unchanged": all(digest(ROOT / name) == sha for name, sha in files.items()
                  if name.startswith("src/"))}
    result.write_text(json.dumps({"checks": checks, "development_checks_met": all(checks.values()),
        "old_checkpoint_sha256": hashlib.sha256(original).hexdigest(),
        "rejection": rejection, "accepted": False, "released": False}, indent=2) + "\n")
    print(json.dumps({"development_checks_met": all(checks.values()), "checks": checks}), flush=True)
    if not all(checks.values()):
        raise RuntimeError("affected workflow failed")


if __name__ == "__main__":
    main()
