from fractions import Fraction
import json

import pytest

from scripts import _b3_e4_f03_local_scientific_exact_storage as storage


SPECS = (
    storage.FractionSpec("cuts", (3,)),
    storage.FractionSpec("weights", (2, 2)),
)
LIMITS = storage.FractionLimits(16, 128, 1024, 16_384)


@pytest.fixture
def values():
    return {
        "cuts": (Fraction(0), Fraction(1, 2), Fraction(1)),
        "weights": (Fraction(-2, 3), Fraction(0), Fraction(10, 11), Fraction(1)),
    }


def test_canonical_fraction_group_roundtrip_and_exclusive_write(values, tmp_path):
    path = tmp_path / "exact.json"
    storage.write_group(path, values, SPECS, limits=LIMITS)
    restored = storage.read_group(path, SPECS, limits=LIMITS)
    assert restored == values
    with pytest.raises(FileExistsError):
        storage.write_group(path, values, SPECS, limits=LIMITS)


def test_large_valid_binary_rationals_do_not_depend_on_decimal_int_conversion(tmp_path):
    specs = (storage.FractionSpec("large", (1,)),)
    limits = storage.FractionLimits(1, 16_384, 40_000, 20_000)
    value = Fraction((1 << 12_000) + 1, (1 << 11_999) + 1)
    path = tmp_path / "large.json"
    storage.write_group(path, {"large": (value,)}, specs, limits=limits)
    assert storage.read_group(path, specs, limits=limits) == {"large": (value,)}


def test_missing_extra_wrong_count_type_and_bit_limits_rejected(values, tmp_path):
    invalid = []
    missing = dict(values); missing.pop("cuts"); invalid.append(missing)
    invalid.append(dict(values, extra=(Fraction(0),)))
    wrong_count = dict(values); wrong_count["cuts"] = values["cuts"][:-1]; invalid.append(wrong_count)
    wrong_type = dict(values); wrong_type["cuts"] = (Fraction(0), 1, Fraction(1)); invalid.append(wrong_type)
    for index, item in enumerate(invalid):
        with pytest.raises(ValueError):
            storage.write_group(tmp_path / f"bad-{index}.json", item, SPECS, limits=LIMITS)
    huge = dict(values); huge["cuts"] = (Fraction(0), Fraction(1 << 200), Fraction(1))
    with pytest.raises(ValueError, match="individual"):
        storage.write_group(tmp_path / "huge.json", huge, SPECS, limits=LIMITS)
    with pytest.raises(ValueError, match="cumulative"):
        storage.write_group(
            tmp_path / "total.json", values, SPECS,
            limits=storage.FractionLimits(16, 128, 4, 16_384),
        )


def test_byte_limit_stops_streaming_before_remaining_fraction_encoding(values, tmp_path, monkeypatch):
    observed = []
    original = storage._hex_integer

    def record(value):
        observed.append(value)
        return original(value)

    monkeypatch.setattr(storage, "_hex_integer", record)
    with pytest.raises(ValueError, match="byte"):
        storage.write_group(
            tmp_path / "small.json", values, SPECS,
            limits=storage.FractionLimits(16, 128, 1024, 90),
        )
    assert len(observed) < 2 * sum(spec.count for spec in SPECS)


def test_reader_rejects_cumulative_bits_before_remaining_fraction_construction(
    values, tmp_path, monkeypatch,
):
    path = tmp_path / "exact.json"
    storage.write_group(path, values, SPECS, limits=LIMITS)
    document = json.loads(path.read_text("ascii"))
    document["total_bits"] = 2
    path.write_bytes(
        (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    )
    observed = []
    original = storage._fraction

    def record(numerator, denominator):
        observed.append((numerator, denominator))
        return original(numerator, denominator)

    monkeypatch.setattr(storage, "_fraction", record)
    with pytest.raises(ValueError, match="cumulative"):
        storage.read_group(
            path, SPECS,
            limits=storage.FractionLimits(16, 128, 2, 16_384),
        )
    assert len(observed) < sum(spec.count for spec in SPECS)


def _rewrite(path, mutate):
    value = json.loads(path.read_text("ascii"))
    mutate(value)
    path.write_bytes(
        (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    )


@pytest.mark.parametrize("mutation", [
    lambda value: value.update(extra=True),
    lambda value: value["arrays"].reverse(),
    lambda value: value["arrays"][0].update(name="stale"),
    lambda value: value["arrays"][0]["values"][0].__setitem__(0, "00"),
    lambda value: value["arrays"][0]["values"][1].__setitem__(1, "02"),
    lambda value: value.update(total_bits=value["total_bits"] + 1),
])
def test_extra_reordered_stale_noncanonical_and_total_mutations_rejected(
    values, tmp_path, mutation,
):
    path = tmp_path / "exact.json"
    storage.write_group(path, values, SPECS, limits=LIMITS)
    _rewrite(path, mutation)
    with pytest.raises(ValueError):
        storage.read_group(path, SPECS, limits=LIMITS)


def test_bounded_single_read_rejects_oversize(values, tmp_path, monkeypatch):
    path = tmp_path / "exact.json"
    storage.write_group(path, values, SPECS, limits=LIMITS)
    limit = path.stat().st_size - 1
    with pytest.raises(ValueError, match="byte"):
        storage.read_group(
            path, SPECS,
            limits=storage.FractionLimits(16, 128, 1024, limit),
        )


@pytest.mark.parametrize("name,shape", [
    ("Bad", (1,)), ("good", ()), ("good", (-1,)), ("good", (10_000_001,)),
])
def test_invalid_fraction_specs_rejected(name, shape):
    with pytest.raises(ValueError):
        storage.FractionSpec(name, shape)
