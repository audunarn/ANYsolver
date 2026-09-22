from pathlib import Path
import zipfile

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_scientific_storage as storage


SPECS = (
    storage.ArraySpec("matrix", (3, 3), np.dtype("<f8")),
    storage.ArraySpec("indices", (3,), np.dtype("<i8")),
    storage.ArraySpec("flags", (2,), np.dtype("|b1"), finite=False),
)


@pytest.fixture
def arrays():
    return {
        "matrix": np.eye(3, dtype="<f8"),
        "indices": np.arange(3, dtype="<i8"),
        "flags": np.array([True, False], dtype="|b1"),
    }


def test_strict_group_roundtrip_owns_arrays(arrays, tmp_path):
    path = tmp_path / "group.npz"
    storage.write_group(path, arrays, SPECS, max_raw_bytes=100_000)
    restored = storage.read_group(path, SPECS, max_raw_bytes=100_000)
    for name in arrays:
        np.testing.assert_array_equal(restored[name], arrays[name])
        assert not np.shares_memory(restored[name], arrays[name])
    with pytest.raises(FileExistsError):
        storage.write_group(path, arrays, SPECS, max_raw_bytes=100_000)


def test_missing_extra_wrong_shape_dtype_nonfinite_and_alias_rejected(arrays, tmp_path):
    invalid = []
    missing = dict(arrays); missing.pop("flags"); invalid.append(missing)
    invalid.append(dict(arrays, extra=np.zeros(1)))
    wrong_shape = dict(arrays); wrong_shape["indices"] = np.arange(4, dtype="<i8"); invalid.append(wrong_shape)
    wrong_type = dict(arrays); wrong_type["matrix"] = np.eye(3, dtype="<f4"); invalid.append(wrong_type)
    nonfinite = {name: value.copy() for name, value in arrays.items()}; nonfinite["matrix"][0, 0] = np.nan; invalid.append(nonfinite)
    aliased = dict(arrays); aliased["indices"] = arrays["matrix"].view("<i8").reshape(-1)[:3]; invalid.append(aliased)
    for index, value in enumerate(invalid):
        with pytest.raises(ValueError):
            storage.write_group(tmp_path / f"bad-{index}.npz", value, SPECS, max_raw_bytes=100_000)


def _members(path: Path):
    with zipfile.ZipFile(path) as source:
        return [(info.filename, source.read(info)) for info in source.infolist()]


def _write(path: Path, members):
    with zipfile.ZipFile(path, "w") as target:
        for name, payload in members:
            target.writestr(name, payload)


def test_duplicate_missing_extra_and_reordered_zip_members_rejected(arrays, tmp_path):
    valid = tmp_path / "valid.npz"
    storage.write_group(valid, arrays, SPECS, max_raw_bytes=100_000)
    members = _members(valid)
    variants = (members[:-1], members + [("extra.npy", members[0][1])],
                list(reversed(members)))
    for index, value in enumerate(variants):
        path = tmp_path / f"inventory-{index}.npz"
        _write(path, value)
        with pytest.raises(ValueError, match="inventory"):
            storage.read_group(path, SPECS, max_raw_bytes=100_000)
    duplicate = tmp_path / "duplicate.npz"
    with pytest.warns(UserWarning):
        _write(duplicate, members + [members[0]])
    with pytest.raises(ValueError, match="inventory"):
        storage.read_group(duplicate, SPECS, max_raw_bytes=100_000)


def test_wrong_header_rejected_before_array_allocation(arrays, tmp_path, monkeypatch):
    valid = tmp_path / "valid.npz"
    storage.write_group(valid, arrays, SPECS, max_raw_bytes=100_000)
    members = _members(valid)
    replacement = tmp_path / "replacement.npy"
    with replacement.open("wb") as stream:
        np.lib.format.write_array(stream, np.zeros((30,), dtype="<f8"), allow_pickle=False)
    members[0] = (members[0][0], replacement.read_bytes())
    altered = tmp_path / "altered.npz"
    _write(altered, members)
    monkeypatch.setattr(np.lib.format, "read_array", lambda *a, **k: pytest.fail("header must reject first"))
    with pytest.raises(ValueError, match="header"):
        storage.read_group(altered, SPECS, max_raw_bytes=100_000)


def test_raw_and_compressed_bounds_checked_before_load(arrays, tmp_path, monkeypatch):
    path = tmp_path / "group.npz"
    storage.write_group(path, arrays, SPECS, max_raw_bytes=100_000)
    with pytest.raises(ValueError, match="specification"):
        storage.read_group(path, SPECS, max_raw_bytes=10)
    path.write_bytes(path.read_bytes() + b"x" * 20_000)
    monkeypatch.setattr(storage.zipfile, "ZipFile", lambda *a, **k: pytest.fail("size must reject first"))
    with pytest.raises(ValueError, match="compressed-byte"):
        storage.read_group(path, SPECS, max_raw_bytes=15_000)


@pytest.mark.parametrize("name,shape,dtype,finite", [
    ("Bad", (1,), "<f8", True),
    ("good", (-1,), "<f8", True),
    ("good", (1,), "<f4", True),
    ("good", (1,), "|b1", True),
])
def test_invalid_array_specs_rejected(name, shape, dtype, finite):
    with pytest.raises(ValueError):
        storage.ArraySpec(name, shape, np.dtype(dtype), finite)
