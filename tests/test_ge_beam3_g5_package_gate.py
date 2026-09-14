"""Fast structural tests for the external installed-wheel gate."""
import io
from pathlib import Path
import zipfile

import pytest

from scripts import run_ge_beam3_g5_package as gate


def test_canonical_rejects_nonfinite_and_is_stable():
    assert gate.canonical({"b": True, "a": 1}) == b'{"a":1,"b":true}\n'
    with pytest.raises(ValueError):
        gate.canonical({"value": float("nan")})


def test_safe_extract_rejects_parent_escape(tmp_path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("../escape.txt", "bad")
    with pytest.raises(ValueError, match="unsafe"):
        gate.safe_extract(archive, tmp_path / "target")


def test_package_gate_declares_bounded_process_tree_termination():
    source = Path(gate.__file__).read_text(encoding="utf-8")
    assert 'timeout=seconds' in source
    assert '["taskkill", "/PID", str(process.pid), "/T", "/F"]' in source
    assert '"OMP_NUM_THREADS"' in source and '"NUMEXPR_NUM_THREADS"' in source


def test_package_gate_rejects_workspace_output_before_creating_parent(tmp_path, monkeypatch):
    output = tmp_path / "missing" / "evidence"
    monkeypatch.setattr(gate.subprocess, "check_output", lambda *args, **kwargs: b"dirty\n")
    with pytest.raises(ValueError, match="external package"):
        gate.run("0" * 40, output)
    assert not output.exists() and not output.parent.exists()
