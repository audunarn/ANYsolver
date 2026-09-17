"""Process-control coverage for the bounded spectral benchmark gate."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "benchmark_spectral_medium_fine.py"
SPEC = importlib.util.spec_from_file_location("spectral_gate", SCRIPT)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)


def _child(source: str) -> list[str]:
    return [sys.executable, "-c", source]


def test_fixture_and_fidelity_choices_are_explicit() -> None:
    parser = gate._parser()
    parsed = parser.parse_args(["--solver-root", "solver", "--adapter-root", "adapter", "--output-dir", "out", "--fixture", "cylinder", "--fidelity", "fine", "--route", "modal"])
    assert (parsed.fixture, parsed.fidelity, parsed.modes, parsed.repetitions) == ("cylinder", "fine", 5, 1)
    with pytest.raises(SystemExit):
        parser.parse_args(["--solver-root", "solver", "--adapter-root", "adapter", "--output-dir", "out", "--fixture", "not-a-fixture", "--fidelity", "fine", "--route", "modal"])


def test_bounded_child_reports_tree_rss_for_small_fake_child() -> None:
    result = gate._run_bounded_child(_child("import time; time.sleep(0.05)"), process_timeout=2, rss_limit=512 * 1024**2)
    assert result["wall_seconds"] < 2
    assert result["peak_tree_rss_bytes"] > 0


def test_bounded_child_terminates_timeout() -> None:
    with pytest.raises(RuntimeError, match="exceeded"):
        gate._run_bounded_child(_child("import time; time.sleep(5)"), process_timeout=0.15, rss_limit=512 * 1024**2)


def test_bounded_child_rejects_memory_limit() -> None:
    with pytest.raises(RuntimeError, match="RSS"):
        gate._run_bounded_child(_child("import time; time.sleep(2)"), process_timeout=2, rss_limit=1)


def test_output_directory_must_be_exclusive(tmp_path: Path) -> None:
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "old.json").write_text("old", encoding="utf-8")
    args = gate._parser().parse_args(["--solver-root", str(tmp_path), "--adapter-root", str(tmp_path), "--output-dir", str(occupied), "--fixture", "girder_panel", "--fidelity", "medium", "--route", "modal"])
    with pytest.raises(RuntimeError, match="exclusive"):
        gate._coordinator(args)


def test_cylinder_snapshot_preserves_loads_without_application_import(monkeypatch) -> None:
    from anystruct import fem_integration as fem
    app = fem.example_runtime_app("cylinder")
    gate._complete_example_snapshot_inputs(app)
    def unexpected_application_lookup(self, name):
        raise AssertionError(f"snapshot attempted application import for {name}")
    monkeypatch.setattr(type(app), "__getattr__", unexpected_application_lookup)
    snapshot = fem.active_line_snapshot(app)
    assert snapshot.is_cylinder
    assert snapshot.pressure_pa == 100_000.0
    assert snapshot.axial_force_n == 0.0
    assert snapshot.top_bottom_moment_nm == 0.0
