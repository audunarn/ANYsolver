import json
from pathlib import Path

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_inverse_storage as inverse


SOURCE = "a" * 40


@pytest.fixture(scope="module")
def plan():
    records = cases.preflight_inventory()
    return archive.make_case_plan(records[0], records, SOURCE)


def _write_all(directory: Path, plan):
    directory.mkdir()
    inverse.prepare_directory(directory)
    expected = {}
    for block in plan.inverse_blocks:
        value = (
            np.arange(block.rows * block.columns, dtype=np.float64)
            .reshape(block.rows, block.columns)
            + block.start
        )
        inverse.write_block(directory, plan, block.start, value)
        expected[block.start] = value
    return expected


def test_complete_inverse_stream_roundtrip_and_index(plan, tmp_path):
    directory = tmp_path / "case"
    expected = _write_all(directory, plan)
    index, digest = inverse.write_index(directory, plan)
    restored, observed = inverse.read_index(directory, plan)
    assert restored == index
    assert observed == digest
    assert restored.total_raw_bytes == 8 * plan.kkt_order**2
    assert tuple(item.start for item in restored.blocks) == tuple(
        block.start for block in plan.inverse_blocks
    )
    for block in plan.inverse_blocks:
        value = inverse.read_block(directory, plan, block.start)
        np.testing.assert_array_equal(value, expected[block.start])
        assert value.flags.owndata
    with pytest.raises(FileExistsError):
        inverse.write_index(directory, plan)


def test_block_shape_start_nonfinite_and_duplicate_rejected(plan, tmp_path):
    directory = tmp_path / "bad-block"
    directory.mkdir()
    inverse.prepare_directory(directory)
    block = plan.inverse_blocks[0]
    with pytest.raises(ValueError, match="unplanned"):
        inverse.write_block(directory, plan, 1, np.zeros((block.rows, block.columns)))
    with pytest.raises(ValueError, match="block"):
        inverse.write_block(directory, plan, block.start, np.zeros((1, 1)))
    value = np.zeros((block.rows, block.columns)); value[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        inverse.write_block(directory, plan, block.start, value)
    value[0, 0] = 0.0
    inverse.write_block(directory, plan, block.start, value)
    with pytest.raises(FileExistsError):
        inverse.write_block(directory, plan, block.start, value)


def test_missing_extra_and_mutated_block_rejected(plan, tmp_path):
    missing = tmp_path / "missing"
    _write_all(missing, plan)
    inverse._path(missing, plan.inverse_blocks[-1]).unlink()
    with pytest.raises(ValueError, match="missing"):
        inverse.write_index(missing, plan)

    extra = tmp_path / "extra"
    _write_all(extra, plan)
    (extra / "inverse" / "rogue.npy").write_bytes(b"rogue")
    with pytest.raises(ValueError, match="extra"):
        inverse.write_index(extra, plan)

    changed = tmp_path / "changed"
    _write_all(changed, plan)
    inverse.write_index(changed, plan)
    path = inverse._path(changed, plan.inverse_blocks[0])
    payload = bytearray(path.read_bytes()); payload[-1] ^= 1; path.write_bytes(payload)
    with pytest.raises(ValueError, match="stale|mismatched"):
        inverse.read_index(changed, plan)


def test_header_shape_dtype_and_size_are_exact(plan, tmp_path):
    directory = tmp_path / "headers"
    _write_all(directory, plan)
    block = plan.inverse_blocks[0]
    path = inverse._path(directory, block)
    np.save(path, np.zeros((block.rows, block.columns), dtype=np.float32), allow_pickle=False)
    with pytest.raises(ValueError, match="size|header"):
        inverse.read_block(directory, plan, block.start)


def _rewrite(path: Path, mutate):
    value = json.loads(path.read_text("ascii"))
    mutate(value)
    path.write_bytes(
        (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    )


def test_noncanonical_extra_reordered_and_stale_index_rejected(plan, tmp_path):
    mutations = (
        lambda value: value.update(extra=True),
        lambda value: value["blocks"].reverse(),
        lambda value: value["blocks"][0].update(name="inverse/stale.npy"),
    )
    for number, mutate in enumerate(mutations):
        directory = tmp_path / f"index-{number}"
        _write_all(directory, plan)
        inverse.write_index(directory, plan)
        _rewrite(directory / "inverse_index.json", mutate)
        with pytest.raises(ValueError):
            inverse.read_index(directory, plan)
