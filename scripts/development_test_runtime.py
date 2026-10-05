"""Opt-in pytest record for focused source development; never artifact acceptance."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time


_timings = {}


def pytest_sessionstart(session):
    _timings.clear()
    _timings.update(session_started=time.perf_counter(), collection_seconds=None,
                    collection_reports=[], nodes=[])


def pytest_collection(session):
    _timings["collection_started"] = time.perf_counter()


def pytest_collectreport(report):
    _timings["collection_reports"].append({"nodeid": report.nodeid, "outcome": report.outcome})


def pytest_collection_finish(session):
    _timings["collection_seconds"] = time.perf_counter() - _timings["collection_started"]


def pytest_runtest_logreport(report):
    entry = {"nodeid": report.nodeid, "phase": report.when, "outcome": report.outcome,
             "duration_seconds": report.duration}
    if hasattr(report, "wasxfail"):
        entry["wasxfail"] = str(report.wasxfail)
    _timings["nodes"].append(entry)


def runtime_record(modules, source, pools=None, compilation_cache=None):
    errors = []
    origins = {name: Path(module.__file__).resolve() for name, module in modules.items()
               if getattr(module, "__file__", None)}
    imported = {name: str(path) for name, path in origins.items()
                if name == "anysolver" or name.startswith("anysolver.")}
    if any(not Path(path).is_relative_to(source) for path in imported.values()):
        errors.append("ANYsolver imports escaped the selected source checkout")
    numba = modules.get("numba")
    actual_jit = bool(numba.config.DISABLE_JIT) if numba is not None else None
    actual_threads = int(numba.get_num_threads()) if numba is not None else None
    if numba is not None and (actual_threads != 1 or actual_jit != (os.environ["NUMBA_DISABLE_JIT"] == "1")):
        errors.append("effective Numba settings differ from requested focused mode")
    if pools is not None and any(pool["num_threads"] != 1 for pool in pools):
        errors.append("effective numerical pools are not single-threaded")
    unbound_imports = []
    if compilation_cache and compilation_cache.get("enabled"):
        for dependency in compilation_cache.get("unbound_dependencies", []):
            roots = [Path(root) for root in dependency.get("module_roots", [dependency["root"]])]
            top_levels = set(dependency["top_levels"])
            matched = [name for name, module in modules.items() if
                       name.partition(".")[0] in top_levels or
                       (name in origins and any(origins[name].is_relative_to(root) for root in roots))]
            if matched:
                unbound_imports.append({"dependency": dependency["name"], "modules": sorted(matched)})
                errors.append(f"cache-enabled run imported unbound dependency {dependency['name']}; rerun with cold development (omit --development-cache)")
        watched_root = compilation_cache.get("watched_root")
        if watched_root:
            repository = Path(watched_root)
            watched = [repository / directory for directory in ("src", "scripts", "tests")]
            outside = sorted(name for name, path in origins.items() if path.suffix == ".py" and
                             path.is_relative_to(repository) and not any(path.is_relative_to(root) for root in watched))
            if outside:
                errors.append("cache-enabled run imported repository Python helpers outside watched source: " +
                              ", ".join(outside) + "; rerun with cold development (omit --development-cache)")
    return {"scope": "source development only", "imports": imported, "effective_pools": pools,
            "numba_threads": actual_threads, "jit_disabled": actual_jit, "errors": errors,
            "unbound_dependency_imports": unbound_imports,
            "plugin_autoload_disabled": os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"}


def pytest_sessionfinish(session, exitstatus):
    pools = None
    if "numpy" in sys.modules or "scipy" in sys.modules:
        from threadpoolctl import threadpool_info
        pools = threadpool_info()
    cache = json.loads(os.environ.get("ANYSOLVER_DEVELOPMENT_CACHE", '{"enabled": false}'))
    record = runtime_record(dict(sys.modules), Path(os.environ["ANYSOLVER_DEVELOPMENT_SOURCE"]).resolve(), pools, cache)
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    record.update(collected=session.testscollected, failed=session.testsfailed, pytest_exit_code=int(exitstatus),
                  outcomes={name: len(rows) for name, rows in reporter.stats.items()
                            if name in ("passed", "failed", "skipped", "error", "xfailed", "xpassed", "deselected")}
                  if reporter is not None else {})
    record["timings"] = {"collection_seconds": _timings.get("collection_seconds"),
                         "session_seconds": time.perf_counter() - _timings["session_started"],
                         "collection_reports": _timings["collection_reports"],
                         "nodes": _timings["nodes"]}
    record["compilation_cache"] = cache
    record["bytecode"] = {"write_enabled": not sys.dont_write_bytecode,
                          "prefix": sys.pycache_prefix}
    if record["errors"] and int(exitstatus) == 0:
        session.exitstatus = 1
    record["exit_code"] = int(session.exitstatus)
    Path(os.environ["ANYSOLVER_DEVELOPMENT_RECORD"]).write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    for error in record["errors"]:
        if reporter is not None:
            reporter.write_line("[development runtime failure] "+error)
