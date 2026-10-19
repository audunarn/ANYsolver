"""Slice 3 task harness: bounded, evidenced numerical execution.

Usage (from anywhere):
  <repo>/.venv/Scripts/python.exe harness.py --name ATTEMPT [--timeout 120]
      [--cwd DIR] [--allow-reserve] [--hash-input PATH]... [--src-override DIR]
      [--skip-preflight] -- CMD ARGS...

Records under evidence/<name>/:
  receipt.json  command, cwd, selected-source identity + import-origin
                verification, runtime record, exit/timeout status, precise
                process-wall seconds, cumulative budget, named test counts
  preflight.json  effective versions, import origins, threadpool, effective
                numba DISABLE_JIT state
  stdout.txt / stderr.txt  full streamed output (preserved on timeout and on
                any harness exception)
  running.json  live lock record (removed on completion)

Budget ledger persists in budget.json (allowance 3600 s, final-verification
reserve 900 s). Every attempt, including failures, timeouts and harness-side
exceptions, is charged and recorded. One numerical child at a time is enforced
with a lock file. When --src-override is given it REPLACES the PYTHONPATH
source root (the candidate src is never added), and the receipt verifies the
actual anysolver import origin against the selected root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
REPO = TASK_DIR.parents[2]
EVIDENCE = TASK_DIR / "evidence"
BUDGET_FILE = TASK_DIR.parent / "budget.json"
LOCK_FILE = TASK_DIR.parent / "running.lock"
ALLOWANCE = 3600.0
RESERVE = 900.0

IDENTITY_FILES = [
    "src/anysolver/corotational.py",
    "src/anysolver/_corotational_batch.py",
    "src/anysolver/_director_trace.py",
    "src/anysolver/_nonlinear_events.py",
    "src/anysolver/elements.py",
    "src/anysolver/mesh_gen.py",
    "src/anysolver/nonlinear_static.py",
    "src/anysolver/nonlinear_performance.py",
    "tests/test_corotational_work_conjugate.py",
    "tests/test_nonlinear_beam_shell_coupling.py",
]

CHILD_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "NUMBA_NUM_THREADS": "1",
    "NUMBA_DISABLE_JIT": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    "ANYSOLVER_RUN_RETIRED_PROGRAMME_TESTS": "0",
}

PREFLIGHT_CODE = r"""
import json, sys
info = {"python": sys.version}
try:
    import numpy, scipy
    info["numpy"] = numpy.__version__
    info["scipy"] = scipy.__version__
except Exception as exc:
    info["numpy_error"] = repr(exc)
for name in ("anysolver", "anymaterial", "anygeometry", "anymesher", "anyfileio"):
    try:
        mod = __import__(name)
        info[name] = {
            "version": getattr(mod, "__version__", None),
            "origin": getattr(mod, "__file__", None),
        }
    except Exception as exc:
        info[name] = {"error": repr(exc)}
try:
    import numba
    info["numba"] = numba.__version__
    info["numba_disable_jit_effective"] = bool(numba.config.DISABLE_JIT)
except Exception as exc:
    info["numba"] = None
    info["numba_error"] = repr(exc)
try:
    from threadpoolctl import threadpool_info
    info["threadpools"] = threadpool_info()
except Exception:
    info["threadpools"] = "unavailable"
print(json.dumps(info))
"""

# Named pytest summary parsing: the terminal summary line lists categories in
# any order ("2 failed, 60 passed, 1 skipped", "60 passed", "3 error", ...).
_COUNT_CATEGORY = re.compile(r"(\d+) (passed|failed|skipped|error|errors|xfailed|xpassed|warning|warnings)")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_budget() -> dict:
    if BUDGET_FILE.exists():
        with open(BUDGET_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {
        "allowance_seconds": ALLOWANCE,
        "final_verification_reserve_seconds": RESERVE,
        "used_seconds": 0.0,
        "attempts": [],
    }


def save_budget(budget: dict) -> None:
    with open(BUDGET_FILE, "w", encoding="utf-8") as fh:
        json.dump(budget, fh, indent=2)


def parse_counts(stdout: str) -> dict:
    """Parse named pytest counts from the terminal summary line.

    The last short-summary line is used so per-test progress lines cannot
    shadow a failing summary like "1 failed, 60 passed".
    """
    counts: dict = {}
    summary_line = ""
    for line in stdout.splitlines():
        stripped = line.strip()
        if _COUNT_CATEGORY.search(stripped):
            summary_line = stripped
    if summary_line:
        counts["summary_line"] = summary_line
        for match in _COUNT_CATEGORY.finditer(summary_line):
            value = int(match.group(1))
            category = match.group(2).rstrip("s")
            key = {"error": "errors", "warning": "warnings"}.get(category, category)
            counts[key] = counts.get(key, 0) + value
    return counts


def kill_tree(pid: int) -> None:
    subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(pid)],
        capture_output=True,
        check=False,
    )


def selected_source_root(args) -> Path:
    return Path(args.src_override).resolve() if args.src_override else REPO / "src"


def selected_tree_hashes(root: Path) -> dict:
    """Hash the identity files of the SELECTED source tree (candidate or override)."""
    base = root.parent if root.name == "src" else root
    hashes = {}
    for rel in IDENTITY_FILES:
        p = base / rel
        hashes[str(rel)] = sha256_file(p) if p.exists() else "MISSING"
    return hashes


def verify_import_origin(preflight: dict, root: Path) -> dict:
    """Verify the child's actual anysolver import origin belongs to the selected root."""
    runtime = (preflight or {}).get("runtime") or {}
    origin = ((runtime.get("anysolver") or {}).get("origin"))
    if not origin:
        return {"anysolver_origin": None, "origin_matches_selected_root": False}
    root_str = str(root.resolve())
    return {
        "anysolver_origin": origin,
        "selected_source_root": root_str,
        "origin_matches_selected_root": bool(
            os.path.abspath(origin).startswith(root_str + os.sep)
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--cwd", default=str(REPO))
    parser.add_argument("--allow-reserve", action="store_true")
    parser.add_argument("--hash-input", action="append", default=[])
    parser.add_argument("--diagnostic-bound-record", default=None)
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument(
        "--src-override",
        default=None,
        help="replace the candidate src PYTHONPATH entry (clean-HEAD attribution runs)",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("no command given")
    is_regression = any(
        args.command[i:i + 2] == ["-m", "pytest"]
        for i in range(len(args.command) - 1)
    ) or any(Path(part).name == "run_portable_ci.py" for part in args.command)
    maximum_timeout = 600.0 if is_regression else 120.0
    if args.diagnostic_bound_record:
        record_path = Path(args.diagnostic_bound_record).resolve()
        record = json.loads(record_path.read_text(encoding="utf-8"))
        expiry = datetime.fromisoformat(record["deadline_utc"].replace("Z", "+00:00"))
        permitted = record["attempts"].get(args.name)
        expected_script = (REPO / record["script"]).resolve()
        script_matches = any(Path(part).resolve() == expected_script for part in args.command)
        if (is_regression or not permitted or not script_matches
                or datetime.now(timezone.utc) >= expiry
                or not 120.0 < float(permitted) <= 600.0):
            parser.error("invalid or expired named analytical diagnostic bound")
        maximum_timeout = float(permitted)
        args.hash_input.append(str(record_path))
    if not (0.0 < args.timeout <= maximum_timeout):
        parser.error(f"timeout must be positive and at most {maximum_timeout:g}s "
                     f"for {'regression' if is_regression else 'diagnostic'} execution")

    overnight_path = TASK_DIR / "overnight-authority.json"
    if overnight_path.exists():
        overnight = json.loads(overnight_path.read_text(encoding="utf-8"))
        deadline = datetime.fromisoformat(overnight["deadline_utc"].replace("Z", "+00:00"))
        window_remaining = (deadline - datetime.now(timezone.utc)).total_seconds()
        if args.timeout > window_remaining:
            print("REFUSED: requested process bound exceeds the remaining overnight "
                  "approval window; preserve state for handoff.", file=sys.stderr)
            return 2

    budget = load_budget()
    # Continuations may add explicitly granted authority without resetting the
    # charged attempts. The ledger is the authority, not this file's default.
    allowance = float(budget["allowance_seconds"])
    reserve = float(budget["final_verification_reserve_seconds"])
    used = float(budget["used_seconds"])
    remaining = allowance - used
    available = remaining - reserve
    ceiling_path = TASK_DIR / "product_execution_ceiling.json"
    if ceiling_path.exists():
        allocation = json.loads(ceiling_path.read_text(encoding="utf-8"))
        if allocation.get("active"):
            allocated_remaining = float(allocation["absolute_process_wall_ceiling_seconds"]) - used
            if args.timeout > allocated_remaining:
                print(f"REFUSED: timeout exceeds active product allocation; "
                      f"{allocated_remaining:.3f}s remain under its absolute ledger ceiling.",
                      file=sys.stderr)
                return 2
    if not args.allow_reserve and args.timeout > available:
        print(
            f"REFUSED: timeout {args.timeout}s exceeds available non-reserve "
            f"budget {available:.1f}s (used {used:.1f}s of {allowance}s, "
            f"reserve {reserve}s). Use --allow-reserve only for final verification.",
            file=sys.stderr,
        )
        return 2
    if args.timeout > remaining:
        print(
            f"REFUSED: timeout {args.timeout}s exceeds total remaining {remaining:.1f}s.",
            file=sys.stderr,
        )
        return 2

    if LOCK_FILE.exists():
        try:
            live = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        except Exception:
            live = None
        print(
            f"REFUSED: another numerical child appears active (lock: {live}).",
            file=sys.stderr,
        )
        return 3

    out_dir = EVIDENCE / args.name
    if out_dir.exists():
        print(f"REFUSED: evidence path {out_dir} already exists.", file=sys.stderr)
        return 4
    out_dir.mkdir(parents=True)

    LOCK_FILE.write_text(
        json.dumps(
            {
                "name": args.name,
                "pid": os.getpid(),
                "started_utc": datetime.now(timezone.utc).isoformat(),
            }
        ),
        encoding="utf-8",
    )

    root = selected_source_root(args)
    env = dict(os.environ)
    env.update(CHILD_ENV)
    # Exact import routing: the selected source root REPLACES the inherited
    # PYTHONPATH so a clean-HEAD attribution can never fall back to the
    # candidate tree (or vice versa).
    env["PYTHONPATH"] = str(root)

    hashes = selected_tree_hashes(root)
    hashes["selected_root"] = str(root)
    for extra in args.hash_input:
        p = Path(extra)
        hashes[str(p)] = sha256_file(p) if p.exists() else "MISSING"

    started_utc = datetime.now(timezone.utc).isoformat()
    wall_total = 0.0
    phase_start = None
    status = "ERROR"
    exit_code = None
    preflight = None
    proc = None
    stdout_path = out_dir / "stdout.txt"
    stderr_path = out_dir / "stderr.txt"
    harness_error = None
    receipt_written = False

    try:
        if not args.skip_preflight:
            pre_out = out_dir / "preflight_stdout.txt"
            pre_err_out = out_dir / "preflight_stderr.txt"
            t0 = time.perf_counter()
            phase_start = t0
            with open(pre_out, "wb") as fh, open(pre_err_out, "wb") as err_fh:
                proc = subprocess.Popen(
                    [sys.executable, "-c", PREFLIGHT_CODE],
                    stdout=fh,
                    stderr=err_fh,
                    env=env,
                    cwd=args.cwd,
                )
                try:
                    proc.wait(timeout=max(10.0, args.timeout))
                except subprocess.TimeoutExpired:
                    kill_tree(proc.pid)
                    try:
                        proc.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        pass
            pre_wall = time.perf_counter() - t0
            wall_total += pre_wall
            phase_start = None
            preflight = {
                "wall_seconds": pre_wall,
                "exit_code": proc.returncode,
                "stderr": pre_err_out.read_text(encoding="utf-8", errors="replace")[-4000:],
            }
            try:
                preflight["runtime"] = json.loads(pre_out.read_text(encoding="utf-8"))
            except Exception as exc:
                preflight["runtime_parse_error"] = repr(exc)
            preflight["import_origin_check"] = verify_import_origin(preflight, root)
            (out_dir / "preflight.json").write_text(
                json.dumps(preflight, indent=2), encoding="utf-8"
            )
        proc = None

        t0 = time.perf_counter()
        phase_start = t0
        with open(stdout_path, "wb") as out_fh, open(stderr_path, "wb") as err_fh:
            proc = subprocess.Popen(
                args.command,
                stdout=out_fh,
                stderr=err_fh,
                env=env,
                cwd=args.cwd,
            )
            try:
                proc.wait(timeout=max(1.0, args.timeout - wall_total))
                status = "EXIT" if proc.returncode == 0 else f"EXIT_{proc.returncode}"
                exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                kill_tree(proc.pid)
                try:
                    proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    pass
                status = "TIMEOUT"
                exit_code = proc.returncode
        proc = None
        main_wall = time.perf_counter() - t0
        wall_total += main_wall
        phase_start = None

        stdout_text = (
            stdout_path.read_text(encoding="utf-8", errors="replace")
            if stdout_path.exists()
            else ""
        )
        receipt = {
            "name": args.name,
            "command": args.command,
            "cwd": str(Path(args.cwd)),
            "started_utc": started_utc,
            "ended_utc": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "exit_code": exit_code,
            "timeout_seconds": args.timeout,
            "process_wall_seconds": wall_total,
            "main_wall_seconds": main_wall,
            "identity_hashes": hashes,
            "child_env": CHILD_ENV,
            "preflight_included": preflight is not None,
            "import_origin_check": (
                (preflight or {}).get("import_origin_check")
                if preflight
                else verify_import_origin(None, root)
            ),
            "counts": parse_counts(stdout_text),
            "head": subprocess.run(
                ["git", "-C", str(REPO), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
            ).stdout.strip(),
        }
        (out_dir / "receipt.json").write_text(
            json.dumps(receipt, indent=2), encoding="utf-8"
        )
        receipt_written = True

        budget["used_seconds"] = used + wall_total
        budget["attempts"].append(
            {
                "name": args.name,
                "status": status,
                "wall_seconds": wall_total,
                "cumulative_used": budget["used_seconds"],
                "remaining": allowance - budget["used_seconds"],
                "started_utc": started_utc,
            }
        )
        save_budget(budget)
        print(
            f"[harness] {args.name}: {status} wall={wall_total:.2f}s "
            f"used={budget['used_seconds']:.1f}s "
            f"remaining={allowance - budget['used_seconds']:.1f}s"
        )
        return 0 if status == "EXIT" else 1
    except Exception as exc:  # noqa: BLE001 - accounting must survive any failure
        harness_error = f"{type(exc).__name__}: {exc}"
        status = "HARNESS_ERROR"
        raise
    finally:
        # Unconditional process-tree cleanup and accounting. Any harness-side
        # exception still writes a receipt, charges the measured wall time and
        # removes the lock, preserving partial stdout/stderr.
        if proc is not None and proc.poll() is None:
            kill_tree(proc.pid)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
        # Account an interrupted active phase (preflight or main child) after
        # owned-process cleanup so a harness-side exception cannot undercharge
        # the launched child's elapsed time.
        if phase_start is not None:
            wall_total += time.perf_counter() - phase_start
            phase_start = None
        if not receipt_written:
            try:
                wall_total_final = wall_total if wall_total > 0 else 0.0
                partial = {
                    "name": args.name,
                    "command": args.command,
                    "cwd": str(Path(args.cwd)),
                    "started_utc": started_utc,
                    "ended_utc": datetime.now(timezone.utc).isoformat(),
                    "status": status,
                    "exit_code": exit_code,
                    "timeout_seconds": args.timeout,
                    "process_wall_seconds": wall_total_final,
                    "identity_hashes": hashes,
                    "child_env": CHILD_ENV,
                    "preflight_included": preflight is not None,
                    "import_origin_check": (
                        (preflight or {}).get("import_origin_check")
                        if preflight
                        else verify_import_origin(None, root)
                    ),
                    "harness_error": harness_error,
                    "partial_accounting": True,
                    "head": subprocess.run(
                        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
                        capture_output=True,
                        text=True,
                    ).stdout.strip(),
                }
                (out_dir / "receipt.json").write_text(
                    json.dumps(partial, indent=2), encoding="utf-8"
                )
                budget["used_seconds"] = used + wall_total_final
                budget["attempts"].append(
                    {
                        "name": args.name,
                        "status": status,
                        "wall_seconds": wall_total_final,
                        "cumulative_used": budget["used_seconds"],
                        "remaining": allowance - budget["used_seconds"],
                        "started_utc": started_utc,
                    }
                )
                save_budget(budget)
                print(
                    f"[harness] {args.name}: {status} (partial accounting) "
                    f"wall={wall_total_final:.2f}s "
                    f"used={budget['used_seconds']:.1f}s",
                    file=sys.stderr,
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[harness] accounting failure: {exc!r}", file=sys.stderr)
        try:
            LOCK_FILE.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
