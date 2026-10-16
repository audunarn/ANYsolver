"""Opt-in pytest record for focused source development; never artifact acceptance."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


def _requested_profile():
    """Return (threads, jit_disabled) explicitly requested for this session.

    The focused contract is validated against the profile the runner
    requested; it is never assumed.  A missing or malformed profile is a
    recorded error, not a silently accepted default.
    """
    threads_text = os.environ.get("ANYSOLVER_DEVELOPMENT_NUMBA_THREADS")
    jit_text = os.environ.get("NUMBA_DISABLE_JIT")
    if threads_text is None or jit_text is None:
        return None
    try:
        threads = int(threads_text)
    except ValueError:
        return None
    if not 1 <= threads <= 8 or jit_text not in ("0", "1"):
        return None
    return threads, jit_text == "1"


def _numba_state(module):
    values = dict(numba_available=module is not None, jit_disabled=None,
                  numba_threads=None, numba_max_threads=None)
    errors = []
    if module is not None:
        try:
            values.update(jit_disabled=bool(module.config.DISABLE_JIT),
                          numba_threads=int(module.get_num_threads()),
                          numba_max_threads=int(module.config.NUMBA_NUM_THREADS))
        except Exception as exc:
            errors.append("Numba runtime observation failed: " + str(exc))
    return values, errors


def runtime_record(modules, source, pools=None):
    errors = []
    imported = {name: str(Path(module.__file__).resolve()) for name, module in modules.items()
                if (name == "anysolver" or name.startswith("anysolver.")) and getattr(module, "__file__", None)}
    if any(not Path(path).is_relative_to(source) for path in imported.values()):
        errors.append("ANYsolver imports escaped the selected source checkout")
    profile = _requested_profile()
    if profile is None:
        errors.append("requested runtime profile is not recorded for this session")
        requested_threads, requested_jit_disabled = None, None
    else:
        requested_threads, requested_jit_disabled = profile
    numba = modules.get("numba")
    observed, observation_errors = _numba_state(numba)
    errors.extend(observation_errors)
    actual_jit = observed["jit_disabled"]
    actual_threads = observed["numba_threads"]
    max_threads = observed["numba_max_threads"]
    if profile is not None and not requested_jit_disabled and numba is None:
        errors.append("requested compiled profile requires an available Numba runtime")
    if numba is not None and profile is not None:
        if actual_jit != requested_jit_disabled:
            errors.append("effective Numba settings differ from requested focused mode")
        if max_threads != requested_threads:
            errors.append("effective Numba thread capacity differs from the requested profile")
        if actual_threads != 1:
            errors.append("effective Numba active threads were not restored to the single-thread baseline")
    if pools is not None and profile is not None:
        for pool in pools:
            if not isinstance(pool, dict):
                errors.append("numerical pool observation is malformed")
                continue
            count = pool.get("num_threads")
            api = pool.get("user_api")
            if type(count) is not int or count < 1:
                errors.append("numerical pool has no valid observed thread count")
            elif api == "blas":
                if count != 1:
                    errors.append("effective BLAS pools must remain single-threaded")
            elif api == "openmp":
                if count > requested_threads:
                    errors.append("effective OpenMP capacity exceeds the requested profile")
            else:
                errors.append("numerical pool has an unsupported or missing API")
    return {"scope": "source development only", "imports": imported, "effective_pools": pools,
            "requested_threads": requested_threads, "numba_max_threads": max_threads,
            "numba_threads": actual_threads, "jit_disabled": actual_jit,
            "numba_available": observed["numba_available"],
            "requested_jit_disabled": requested_jit_disabled, "errors": errors,
            "native_deadline_scale": os.environ.get("ANYSOLVER_GE_BEAM3_DEADLINE_SCALE"),
            "plugin_autoload_disabled": os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"}


def _observed_runtime():
    values, errors = _numba_state(sys.modules.get("numba"))
    pools = None
    if "numpy" in sys.modules or "scipy" in sys.modules:
        try:
            from threadpoolctl import threadpool_info
            pools = threadpool_info()
        except Exception as exc:
            errors.append("numerical pool observation failed: " + str(exc))
    return {**values, "pools": pools, "errors": errors}


_INITIAL_RUNTIME = None
_STARTUP_ERRORS = []


def pytest_configure(config):
    global _INITIAL_RUNTIME, _STARTUP_ERRORS
    _STARTUP_ERRORS = []
    profile = _requested_profile()
    # NUMBA_NUM_THREADS sets capacity, not the active baseline. Initialize the
    # actual runtime before collection, then retain capacity for scoped tests.
    try:
        import numba
    except Exception as exc:
        if profile is not None and not profile[1]:
            _STARTUP_ERRORS.append("requested compiled runtime initialization failed: " + str(exc))
    before = _observed_runtime()
    if profile is not None and sys.modules.get("numba") is not None:
        try:
            sys.modules["numba"].set_num_threads(1)
        except Exception as exc:
            _STARTUP_ERRORS.append("Numba baseline initialization failed: " + str(exc))
    _INITIAL_RUNTIME = {**_observed_runtime(), "before_initialization": before}
    _STARTUP_ERRORS.extend(_INITIAL_RUNTIME["errors"])


def pytest_sessionfinish(session, exitstatus):
    final = _observed_runtime()
    record = runtime_record(dict(sys.modules),
                            Path(os.environ["ANYSOLVER_DEVELOPMENT_SOURCE"]).resolve(),
                            final["pools"])
    record["errors"].extend(_STARTUP_ERRORS + final["errors"])
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    record.update(collected=session.testscollected, failed=session.testsfailed, pytest_exit_code=int(exitstatus),
                  outcomes={name: len(rows) for name, rows in reporter.stats.items()
                            if name in ("passed", "failed", "skipped", "error", "xfailed", "xpassed", "deselected")}
                  if reporter is not None else {})
    record["initial_runtime"] = _INITIAL_RUNTIME
    if record["errors"] and int(exitstatus) == 0:
        session.exitstatus = 1
    record["exit_code"] = int(session.exitstatus)
    Path(os.environ["ANYSOLVER_DEVELOPMENT_RECORD"]).write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    for error in record["errors"]:
        if reporter is not None:
            reporter.write_line("[development runtime failure] "+error)
