"""Reject changed source evidence before an apparent positive replay is emitted."""

import json

import pytest

from scripts.b3_e4_f03_q6_positivity_saved_replay import child


def _write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def test_child_rejects_parent_child_source_hash_mismatch_before_result(tmp_path):
    source = tmp_path / "source"
    result = tmp_path / "result"
    source.mkdir()
    result.mkdir()
    _write(source / "measurement.json", {
        "status": "UNREGISTERED_Q6_POSITIVITY_FEASIBILITY", "case_id": "X0"})
    _write(source / "receipt.json", {
        "reason": "completed", "exit_code": 0, "failure": None})
    _write(source / "attempt.json", {"case_id": "X0", "source_sha256": "a"})
    _write(source / "start.json", {"case_id": "X0", "source_sha256": "a"})
    with pytest.raises(ValueError, match="completed matching source"):
        child(source, result, "X0", "0"*64)
    assert not (result / "measurement.json").exists()


def test_child_rejects_uncompleted_source_before_result(tmp_path):
    source = tmp_path / "source"
    result = tmp_path / "result"
    source.mkdir()
    result.mkdir()
    _write(source / "measurement.json", {
        "status": "UNREGISTERED_Q6_POSITIVITY_FEASIBILITY", "case_id": "X0"})
    _write(source / "receipt.json", {
        "reason": "time_limit", "exit_code": 1, "failure": None})
    _write(source / "attempt.json", {"case_id": "X0", "source_sha256": "a"})
    _write(source / "start.json", {"case_id": "X0", "source_sha256": "a"})
    import hashlib
    expected = hashlib.sha256((source / "measurement.json").read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="completed matching source"):
        child(source, result, "X0", expected)
    assert not (result / "measurement.json").exists()
