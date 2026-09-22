from pathlib import Path
import struct
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


def test_writer_preflight_guarantees_its_own_size_bound_and_reader_acceptance(tmp_path):
    rng = np.random.default_rng(123)
    value = rng.integers(0, 256, size=1_000_000, dtype=np.uint8)
    specs = (storage.ArraySpec("noise", value.shape, np.dtype("|u1")),)
    bound = value.nbytes + storage.MAX_ZIP_MEMBER_OVERHEAD
    path = tmp_path / "noise.npz"
    storage.write_group(path, {"noise": value}, specs, max_raw_bytes=bound)
    assert path.stat().st_size <= bound
    restored = storage.read_group(path, specs, max_raw_bytes=bound)
    np.testing.assert_array_equal(restored["noise"], value)


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


def test_complete_value_and_alias_preflight_precedes_ownership_copy(arrays, tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "_owned", lambda *a, **k: pytest.fail("must preflight first"))
    wrong = dict(arrays)
    wrong["flags"] = np.zeros(3, dtype="|b1")
    with pytest.raises(ValueError, match="flags"):
        storage.write_group(tmp_path / "wrong.npz", wrong, SPECS, max_raw_bytes=100_000)
    aliased = dict(arrays)
    aliased["indices"] = arrays["matrix"].view("<i8").reshape(-1)[:3]
    with pytest.raises(ValueError, match="aliased"):
        storage.write_group(tmp_path / "aliased.npz", aliased, SPECS, max_raw_bytes=100_000)


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
        with pytest.raises(ValueError, match="inventory|central-directory"):
            storage.read_group(path, SPECS, max_raw_bytes=100_000)
    duplicate = tmp_path / "duplicate.npz"
    with pytest.warns(UserWarning):
        _write(duplicate, members + [members[0]])
    with pytest.raises(ValueError, match="inventory|central-directory"):
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


def test_oversized_member_rejected_before_member_read(arrays, tmp_path, monkeypatch):
    valid = tmp_path / "valid.npz"
    storage.write_group(valid, arrays, SPECS, max_raw_bytes=100_000)
    members = _members(valid)
    members[0] = (members[0][0], b"x" * 50_000)
    altered = tmp_path / "oversized-member.npz"
    _write(altered, members)
    monkeypatch.setattr(
        storage.zipfile.ZipFile, "read",
        lambda *a, **k: pytest.fail("member size must reject before payload read"),
    )
    with pytest.raises(ValueError, match="inventory|size"):
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


def test_central_directory_count_rejected_before_zipfile_allocation(monkeypatch):
    # Validly placed EOCD shape, but an impossible registered member count.
    payload = struct.pack("<4s4H2LH", b"PK\x05\x06", 0, 0, 5000, 5000, 0, 0, 0)
    monkeypatch.setattr(storage.zipfile, "ZipFile", lambda *a, **k: pytest.fail("preflight first"))
    with pytest.raises(ValueError, match="central-directory"):
        storage._preflight_central_directory(payload, len(SPECS))


@pytest.mark.parametrize("name,shape,dtype,finite", [
    ("Bad", (1,), "<f8", True),
    ("good", (-1,), "<f8", True),
    ("good", (1,), "<f4", True),
    ("good", (1,), "|b1", True),
])
def test_invalid_array_specs_rejected(name, shape, dtype, finite):
    with pytest.raises(ValueError):
        storage.ArraySpec(name, shape, np.dtype(dtype), finite)
