import io
from pathlib import Path
import zipfile

import pytest

from scripts import run_ge_beam3_g6_confirmation as confirmation
from scripts import run_ge_beam3_g6_package as package


def test_runner_canonical_and_strict_duplicate_nonfinite_rejection():
    raw = confirmation.canonical({"b": True, "a": 1})
    assert raw == b'{"a":1,"b":true}\n'
    assert confirmation.strict(raw) == {"a": 1, "b": True}
    with pytest.raises(ValueError, match="duplicate"):
        confirmation.strict(b'{"a":1,"a":2}\n')
    with pytest.raises(ValueError, match="nonfinite"):
        confirmation.strict(b'{"a":NaN}\n')


def test_package_safe_extract_rejects_escape(tmp_path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("../escape", "bad")
    with pytest.raises(ValueError, match="unsafe"):
        package.safe_extract(archive, tmp_path / "target")


def test_bounded_process_and_scope_guards_are_present():
    package_source = Path(package.__file__).read_text(encoding="utf-8")
    confirmation_source = Path(confirmation.__file__).read_text(encoding="utf-8")
    assert 'process.wait(timeout=seconds)' in package_source
    assert '["taskkill", "/PID", str(process.pid), "/T", "/F"]' in package_source
    assert 'GE_BEAM3_G6_SCALE_ELEMENTS="1024"' in confirmation_source
    assert 'len(selected) != 8' in confirmation_source
    assert 'production_default_qualified":False' in confirmation_source


def test_exclusive_writes_reject_reuse(tmp_path):
    target = tmp_path / "record.json"
    package.write_new(target, {"ok": True})
    with pytest.raises(FileExistsError):
        package.write_new(target, {"ok": True})
