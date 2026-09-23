from fractions import Fraction as F
import json
import zipfile

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_recovery as recovery
from scripts import _b3_e4_f03_local_scientific_result_storage as saved
from scripts import _b3_e4_f03_local_support_recovery as support
from scripts import _b3_e4_f03_saved_interface_checks as interface


HASH = "ab" * 32


def _summary():
    return saved.CompositionSummary(
        "COMPONENT_CHECKS_PASSED", (), HASH,
        tuple((name, HASH) for name in saved.SAVED_HASH_NAMES),
        (
            ("numerical", "NUMERICAL_MECHANICAL_CHECKS_PASSED"),
            ("interface", "PASSED"), ("work", "PASSED"), ("norm", "PASSED"),
        ),
        tuple((name, True) for name in saved.CROSS_NAMES),
        tuple((name, index) for index, name in enumerate(saved.DIAGNOSTIC_NAMES)),
    )


def _composition_result():
    value = _summary()
    return {
        "scope": "SAVED_RECOVERY_COMPONENT_COMPOSITION_ONLY",
        "status": value.status,
        "reasons": value.reasons,
        "canonical_snapshot_sha256": value.canonical_snapshot_sha256,
        "canonical_saved_sha256s": dict(value.canonical_saved_sha256s),
        "component_statuses": dict(value.component_statuses),
        "cross_bindings": dict(value.cross_bindings),
        "diagnostics": dict(value.diagnostics),
        "components": {"unpersisted": "adjudicator recomputes these"},
    }


def _interface():
    zeros = np.zeros
    return interface.SavedInterface(
        (F(0), F(1)), zeros((1, 3, 6)), zeros(3), np.arange(6.0).reshape(2, 3),
        np.arange(24.0).reshape(8, 3), zeros((8, 3)), zeros((8, 3)),
        np.arange(24.0, 48.0).reshape(8, 3),
    )


def _support():
    result = object.__new__(support.SupportResult)
    actions = tuple(recovery.Action(F(index, 7)) for index in range(14))
    fields = {
        "force_balance_actual": actions[0:2], "force_balance_nominal": actions[2:4],
        "physical_moment_defect": actions[4], "predicted_physical_moment_defect": actions[5],
        "represented_moment_identity": actions[6], "rigid_yaw_functional": actions[7],
        "actual_load": actions[8:10], "nominal_load": actions[10:12],
        "load_actual_minus_nominal": actions[12:14],
    }
    for name, value in fields.items():
        object.__setattr__(result, name, value)
    return result


def test_composition_factory_and_roundtrip_are_exact_and_owned(tmp_path):
    value = saved.composition_summary(_composition_result())
    path = tmp_path / "saved_composition.npz"
    saved.write_composition(path, value)
    restored = saved.read_composition(path)
    assert restored == value
    assert tuple(name for name, _ in restored.cross_bindings) == saved.CROSS_NAMES
    with pytest.raises(FileExistsError):
        saved.write_composition(path, value)


def test_composition_rejects_reordered_or_invented_contract_fields():
    value = _composition_result()
    value["cross_bindings"] = dict(reversed(tuple(value["cross_bindings"].items())))
    with pytest.raises(ValueError, match="noncanonical"):
        saved.composition_summary(value)
    value = _composition_result()
    value["extra"] = True
    with pytest.raises(ValueError, match="inventory"):
        saved.composition_summary(value)


def test_composition_rejects_noncanonical_reason_payload(tmp_path):
    path = tmp_path / "saved_composition.npz"
    saved.write_composition(path, _summary())
    with zipfile.ZipFile(path, "r") as source:
        arrays = {name[:-4]: np.load(source.open(name), allow_pickle=False)
                  for name in source.namelist()}
    payload = json.dumps([], indent=1).encode("ascii")
    arrays["reason_size"][0] = len(payload)
    arrays["reason_bytes"].fill(0)
    arrays["reason_bytes"][:len(payload)] = np.frombuffer(payload, dtype=np.uint8)
    path.unlink()
    with path.open("xb") as raw, zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_STORED) as group:
        for spec in saved.composition_specs():
            with group.open(spec.name + ".npy", "w", force_zip64=True) as stream:
                np.lib.format.write_array(stream, arrays[spec.name], allow_pickle=False)
    with pytest.raises(ValueError, match="noncanonical"):
        saved.read_composition(path)


def test_balance_factory_roundtrip_binds_actions_atoms_and_bands(tmp_path):
    value = saved.balance_snapshot(_support(), _interface())
    path = tmp_path / "balances.npz"
    saved.write_balances(path, value)
    restored = saved.read_balances(path)
    np.testing.assert_array_equal(restored.values, value.values)
    np.testing.assert_array_equal(restored.endpoint_atoms, value.endpoint_atoms)
    np.testing.assert_array_equal(restored.total_bands, value.total_bands)
    np.testing.assert_array_equal(restored.line_bands, value.line_bands)
    assert restored.action_sha256s == value.action_sha256s

    original = restored.total_bands.copy()
    with pytest.raises(ValueError, match="read-only"):
        value.total_bands[:] = -1
    np.testing.assert_array_equal(restored.total_bands, original)


def test_balance_snapshot_rejects_alias_shape_hash_and_nonfinite_data():
    value = saved.balance_snapshot(_support(), _interface())
    with pytest.raises(ValueError):
        saved.BalanceSnapshot(value.values[:-1], value.action_sha256s,
                              value.endpoint_atoms, value.total_bands, value.line_bands)
    bad = list(value.action_sha256s)
    bad[0] = "0"
    with pytest.raises(ValueError, match="SHA"):
        saved.BalanceSnapshot(value.values, tuple(bad), value.endpoint_atoms,
                              value.total_bands, value.line_bands)
    nonfinite = value.values.copy(); nonfinite[0] = np.nan
    with pytest.raises(ValueError, match="balance"):
        saved.BalanceSnapshot(nonfinite, value.action_sha256s, value.endpoint_atoms,
                              value.total_bands, value.line_bands)
