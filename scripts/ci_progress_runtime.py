"""Opt-in CI progress evidence; never alters runtime, mechanics, or tolerances.

The portable CI runner loads this module explicitly with ``-p`` while plugin
autoload is disabled, so ordinary and focused-development sessions never see
it.  Every hook only appends diagnostic records to the file named by
``ANYSOLVER_CI_PROGRESS_RECORD``; the module never touches environment
settings, numerical state, collection, or the session exit status.  A missing
record path leaves every hook inert.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

RECORD_ENV = "ANYSOLVER_CI_PROGRESS_RECORD"

_STATE: dict[str, object] = {}


def _record_path() -> Path | None:
    text = os.environ.get(RECORD_ENV)
    return Path(text) if text else None


def _snapshot() -> dict[str, object]:
    return {
        "scope": "ci progress evidence only; not qualification",
        "allocated_modules": list(_STATE["allocated_modules"]),
        "collected": _STATE["collected"],
        "started": _STATE["started"],
        "completed": _STATE["completed"],
        "current_node": _STATE["current_node"],
        "current_phase": _STATE["current_phase"],
        "outcomes": dict(_STATE["outcomes"]),
    }


def _write(path: Path, record: dict[str, object]) -> None:
    record["updated_utc"] = datetime.now(timezone.utc).isoformat()
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    os.replace(partial, path)


def _persist() -> None:
    path = _record_path()
    if path is None:
        return
    try:
        _write(path, _snapshot())
    except OSError:
        pass


def pytest_configure(config) -> None:
    global _STATE
    _STATE = {
        "allocated_modules": [
            argument
            for argument in getattr(config, "args", ())
            if not argument.startswith("-")
        ],
        "collected": None,
        "started": 0,
        "completed": 0,
        "current_node": None,
        "current_phase": None,
        "outcomes": {},
    }
    _persist()


def pytest_collection_finish(session) -> None:
    if _record_path() is None:
        return
    _STATE["collected"] = len(getattr(session, "items", ()))
    _persist()


def pytest_runtest_logstart(nodeid, location) -> None:
    if _record_path() is None:
        return
    _STATE["started"] += 1
    _STATE["current_node"] = nodeid
    _STATE["current_phase"] = "setup"
    _persist()


def pytest_runtest_logreport(report) -> None:
    if _record_path() is None:
        return
    # TestReport.outcome is only passed/failed/skipped; setup and teardown
    # failures therefore arrive as "failed", never as "error".
    when = report.when
    outcome = report.outcome
    outcomes = _STATE["outcomes"]

    def count(key: str) -> None:
        outcomes[key] = int(outcomes.get(key, 0)) + 1

    if when == "setup":
        if outcome == "failed":
            count("setup_error")
            _STATE["current_phase"] = "teardown"
        elif outcome == "skipped":
            count("skipped")
            _STATE["current_phase"] = "teardown"
        else:
            _STATE["current_phase"] = "call"
    elif when == "call":
        count(outcome)
        _STATE["current_phase"] = "teardown"
    elif when == "teardown":
        if outcome == "failed":
            count("teardown_error")
    else:
        return
    _persist()


def pytest_runtest_logfinish(nodeid, location) -> None:
    if _record_path() is None:
        return
    # A lifecycle counts as completed only once teardown has finished; a node
    # killed mid-teardown stays current and uncompleted in the record.
    _STATE["completed"] += 1
    _STATE["current_node"] = None
    _STATE["current_phase"] = None
    _persist()


def pytest_sessionfinish(session, exitstatus) -> None:
    if _record_path() is None:
        return
    record = _snapshot()
    record["pytest_exit_code"] = int(exitstatus)
    try:
        _write(_record_path(), record)
    except OSError:
        pass
