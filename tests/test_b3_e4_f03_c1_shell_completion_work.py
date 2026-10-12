"""Check the fixed-dual physical/completion partition against saved work."""

import json
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

import scripts.b3_e4_f03_c1_shell_completion_work as completion_work
from scripts.b3_e4_f03_c1_shell_completion_work import evaluate


ROOT = Path(__file__).resolve().parents[1] / "docs" / "agent_plans"


UNIT_SOURCE_COMMIT = "UNIT-GIT-REV-PARSE-HEAD-UNAVAILABLE"


class _UnitMetadataSubprocess:
    """Scoped metadata seam for git-free source exports.

    Only the exact return-metadata command ("git", "rev-parse", "HEAD")
    is answered with a clearly non-commit unit placeholder; every other
    attribute lookup and every other command forwards to the real
    subprocess module untouched. The placeholder is not a commit and is
    not an accepted source identity.
    """

    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)

    def check_output(self, *args, **kwargs):
        command = args[0] if args else kwargs.get("args")
        if tuple(command) == ("git", "rev-parse", "HEAD"):
            return UNIT_SOURCE_COMMIT
        return self._real.check_output(*args, **kwargs)


def _bind_unit_metadata_seam_when_git_unavailable(monkeypatch):
    try:
        subprocess.check_output(("git", "rev-parse", "HEAD"), text=True)
    except (OSError, subprocess.CalledProcessError):
        monkeypatch.setattr(completion_work, "subprocess",
                            _UnitMetadataSubprocess(subprocess))


def test_completion_work_partitions_saved_fixed_dual_response(monkeypatch):
    _bind_unit_metadata_seam_when_git_unavailable(monkeypatch)
    result = evaluate(ROOT / "B3_E4_F03_C1_MATERIAL_LINE_P0_SOLID_RECON_DEV_V1.json")
    prior = json.loads((ROOT / "B3_E4_F03_C1_MATERIAL_LINE_SAME_ACTION_DEV_V1.json").read_text())
    for label, case in result["cases"].items():
        np.testing.assert_allclose(
            case["total_action_work_J"],
            prior["cases"][label]["native_shell_action_only_work_J"],
            rtol=1e-11, atol=1e-12,
        )
        np.testing.assert_allclose(
            case["physical_operator_work_J"] +
            case["completion_operator_work_J"],
            case["total_action_work_J"],
            rtol=1e-10, atol=1e-12,
        )
        assert case["equilibrium_ratio"] < 1e-9


def test_unit_metadata_seam_answers_only_exact_head_command():
    class _Recorder:
        def __init__(self):
            self.forwarded = None

        def check_output(self, *args, **kwargs):
            self.forwarded = (args, kwargs)
            return b"forwarded"

    recorder = _Recorder()
    proxy = _UnitMetadataSubprocess(recorder)
    assert proxy.check_output(("git", "rev-parse", "HEAD"), text=True) == UNIT_SOURCE_COMMIT
    assert proxy.check_output(["git", "rev-parse", "HEAD"]) == UNIT_SOURCE_COMMIT
    assert recorder.forwarded is None
    assert proxy.check_output(("git", "status")) == b"forwarded"
    assert recorder.forwarded == ((("git", "status"),), {})
    attributes = _UnitMetadataSubprocess(subprocess)
    assert attributes.PIPE == subprocess.PIPE
    assert attributes.run is subprocess.run
    assert attributes.CalledProcessError is subprocess.CalledProcessError
    assert re.fullmatch("[0-9a-f]{40}", UNIT_SOURCE_COMMIT) is None


def test_unit_metadata_seam_leaves_real_git_path_unpatched(monkeypatch):
    class _Available:
        def check_output(self, *args, **kwargs):
            return "0" * 40

    real = subprocess
    monkeypatch.setattr(sys.modules[__name__], "subprocess", _Available())
    _bind_unit_metadata_seam_when_git_unavailable(monkeypatch)
    assert completion_work.subprocess is real


def test_unit_metadata_seam_engages_only_the_script_module_subprocess(monkeypatch):
    class _Gitless:
        CalledProcessError = subprocess.CalledProcessError
        def check_output(self, *args, **kwargs):
            raise OSError("git unavailable")

    real = subprocess
    monkeypatch.setattr(sys.modules[__name__], "subprocess", _Gitless())
    _bind_unit_metadata_seam_when_git_unavailable(monkeypatch)
    assert completion_work.subprocess is not real
    assert completion_work.subprocess.check_output(
        ("git", "rev-parse", "HEAD")) == UNIT_SOURCE_COMMIT
