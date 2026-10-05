import json

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_prolongation as transfer
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_prolongation_storage as saved
from scripts import _b3_e4_f03_local_scientific_storage as storage


LIMITS = {
    "max_entries": 100_000,
    "max_integer_bits": cases.ASSEMBLY_BUDGET.max_trace_integer_bits,
    "max_work_bytes": cases.ASSEMBLY_BUDGET.max_work_bytes,
}


def _value(case):
    source = saved.predecessor(case)
    if source is None:
        return None
    return transfer.prolongation(
        cases.compile_case(source), cases.compile_case(case), **LIMITS,
    )


@pytest.mark.parametrize("case", cases.CASES)
def test_exact_prolongation_roundtrip_for_complete_case_inventory(case, tmp_path):
    directory = tmp_path / case.case_id
    directory.mkdir()
    source = _value(case)
    saved.write(directory, source, case)
    restored = saved.read(directory, case)
    if source is None:
        assert restored is None
        return
    assert restored.source_dofs == source.source_dofs
    assert restored.target_dofs == source.target_dofs
    assert restored.weights == source.weights
    assert restored.integer_bits == source.integer_bits
    np.testing.assert_array_equal(restored.rows, source.rows)
    np.testing.assert_array_equal(restored.columns, source.columns)
    assert not np.shares_memory(restored.rows, source.rows)
    with pytest.raises(ValueError):
        restored.rows.setflags(write=True)


def test_missing_nested_and_unexpected_coarse_evidence_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="coarsest"):
        saved.write(tmp_path, _value(cases.CASES[1]), cases.CASES[0])
    directory = tmp_path / "missing"
    directory.mkdir()
    with pytest.raises(ValueError, match="required"):
        saved.write(directory, None, cases.CASES[1])


def test_padding_and_fraction_canonicality_are_rechecked(tmp_path):
    case = cases.CASES[1]
    directory = tmp_path / "hostile"
    directory.mkdir()
    saved.write(directory, _value(case), case)
    specs = saved.array_specs(case)
    arrays = storage.read_group(
        directory / "prolongations.npz", specs, max_raw_bytes=saved._group_bound(specs),
    )
    count = int(arrays["entry_count"][0])
    arrays["rows"] = arrays["rows"].copy()
    arrays["rows"][count] = 0
    (directory / "prolongations.npz").unlink()
    storage.write_group(
        directory / "prolongations.npz", arrays, specs,
        max_raw_bytes=saved._group_bound(specs),
    )
    with pytest.raises(ValueError, match="padded"):
        saved.read(directory, case)

    clean = tmp_path / "noncanonical"
    clean.mkdir()
    saved.write(clean, _value(case), case)
    path = clean / "prolongation_weights.json"
    document = json.loads(path.read_text("ascii"))
    document["arrays"][0]["values"][0][0] = "00"
    path.write_bytes(
        (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    )
    with pytest.raises(ValueError):
        saved.read(clean, case)


def test_exact_bit_and_topology_mismatch_rejected_before_file_creation(tmp_path):
    case = cases.CASES[1]
    value = _value(case)
    object.__setattr__(value, "integer_bits", value.integer_bits + 1)
    with pytest.raises(ValueError, match="bit count"):
        saved.write(tmp_path, value, case)
    assert not (tmp_path / "prolongations.npz").exists()
