from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _module():
    path = ROOT / "scripts/profile_nonlinear_representative.py"
    spec = importlib.util.spec_from_file_location("representative_profiler", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_profiler_rejects_unbound_campaign_runner() -> None:
    module = _module()
    with pytest.raises(RuntimeError, match="campaign runner SHA-256 mismatch"):
        module._load_campaign_module("0" * 64, "0" * 64)


def test_profiler_rejects_changed_case_builder() -> None:
    module = _module()
    runner_sha256 = module._sha256(module.CAMPAIGN_RUNNER)
    with pytest.raises(RuntimeError, match="campaign _build_case SHA-256 mismatch"):
        module._load_campaign_module(runner_sha256, "0" * 64)
