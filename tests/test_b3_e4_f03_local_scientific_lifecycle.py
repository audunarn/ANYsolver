import json
from pathlib import Path

import pytest

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_lifecycle as lifecycle
from scripts import _b3_e4_f03_local_scientific_supervisor as supervisor


SOURCE = "a" * 40
REGISTRATION = "b" * 64


@pytest.fixture(scope="module")
def plan():
    records = cases.preflight_inventory()
    return archive.make_case_plan(records[0], records, SOURCE)


def receipt(reason="completed"):
    return supervisor.SupervisionReceipt(reason, 0, 10, 1.5, 1024, (10, 11), (), None)


def test_exclusive_start_and_terminal_roundtrip(plan, tmp_path):
    directory = tmp_path / plan.case_id
    directory.mkdir()
    start_digest = lifecycle.write_start(directory, plan, REGISTRATION, 10)
    start, observed_start = lifecycle.read_start(directory, plan, REGISTRATION)
    assert observed_start == start_digest
    assert start["pid"] == 10
    terminal_digest = lifecycle.write_terminal(directory, plan, REGISTRATION, receipt())
    terminal, observed_terminal = lifecycle.read_terminal(directory, plan, REGISTRATION)
    assert observed_terminal == terminal_digest
    assert terminal["start_sha256"] == start_digest
    with pytest.raises(ValueError):
        lifecycle.write_start(directory, plan, REGISTRATION, 10)
    with pytest.raises(FileExistsError):
        lifecycle.write_terminal(directory, plan, REGISTRATION, receipt())
    with pytest.raises(ValueError, match="identity"):
        lifecycle.read_start(directory, plan, "bad")
    with pytest.raises(ValueError, match="identity"):
        lifecycle.read_terminal(directory, plan, "bad")


def test_launch_failure_terminal_explicitly_has_no_start(plan, tmp_path):
    directory = tmp_path / plan.case_id
    directory.mkdir()
    failed = supervisor.SupervisionReceipt(
        "launch_failure", None, None, 0.1, 0, (), (), "OSError: launch",
    )
    lifecycle.write_terminal(directory, plan, REGISTRATION, failed)
    terminal, _ = lifecycle.read_terminal(directory, plan, REGISTRATION)
    assert terminal["start_sha256"] is None
    assert terminal["reason"] == "launch_failure"


def test_launched_child_without_start_is_preserved_as_incomplete(plan, tmp_path):
    directory = tmp_path / plan.case_id
    directory.mkdir()
    lifecycle.write_terminal(directory, plan, REGISTRATION, receipt("time_limit"))
    terminal, _ = lifecycle.read_terminal(directory, plan, REGISTRATION)
    assert terminal["start_sha256"] is None
    assert terminal["reason"] == "time_limit"


def test_terminal_cannot_consume_start_from_another_process(plan, tmp_path):
    directory = tmp_path / plan.case_id
    directory.mkdir()
    lifecycle.write_start(directory, plan, REGISTRATION, 999)
    with pytest.raises(ValueError, match="own"):
        lifecycle.write_terminal(directory, plan, REGISTRATION, receipt())


def _rewrite(path: Path, change):
    value = json.loads(path.read_text("ascii"))
    change(value)
    path.write_bytes(
        (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    )


def test_stale_extra_and_unconsumed_markers_rejected(plan, tmp_path):
    directory = tmp_path / plan.case_id
    directory.mkdir()
    lifecycle.write_start(directory, plan, REGISTRATION, 10)
    lifecycle.write_terminal(directory, plan, REGISTRATION, receipt())
    _rewrite(directory / "terminal.json", lambda value: value.update(start_sha256="0" * 64))
    with pytest.raises(ValueError, match="consume"):
        lifecycle.read_terminal(directory, plan, REGISTRATION)
    _rewrite(directory / "start.json", lambda value: value.update(extra=True))
    with pytest.raises(ValueError, match="inventory"):
        lifecycle.read_start(directory, plan, REGISTRATION)


def test_corrupt_noncanonical_and_oversize_receipts_rejected(plan, tmp_path, monkeypatch):
    directory = tmp_path / plan.case_id
    directory.mkdir()
    lifecycle.write_start(directory, plan, REGISTRATION, 10)
    start = directory / "start.json"
    start.write_bytes(start.read_bytes() + b" ")
    with pytest.raises(ValueError, match="encoding"):
        lifecycle.read_start(directory, plan, REGISTRATION)
    monkeypatch.setattr(lifecycle, "MAX_RECEIPT_BYTES", 2)
    with pytest.raises(ValueError, match="bound"):
        lifecycle.read_start(directory, plan, REGISTRATION)
