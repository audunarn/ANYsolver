"""Canonical bounded rational evidence groups for the F03 local runner."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
import math
from pathlib import Path
import re


SCHEMA = "f03_local_scientific_fraction_group_v1"
NAME = re.compile(r"[a-z][a-z0-9_]{0,63}")
INTEGER = re.compile(r"0|-?[1-9a-f][0-9a-f]*")
POSITIVE_INTEGER = re.compile(r"[1-9a-f][0-9a-f]*")


@dataclass(frozen=True, slots=True)
class FractionSpec:
    name: str
    shape: tuple[int, ...]

    def __post_init__(self):
        if (
            type(self.name) is not str
            or NAME.fullmatch(self.name) is None
            or type(self.shape) is not tuple
            or not 1 <= len(self.shape) <= 5
            or any(type(value) is not int or value < 0 for value in self.shape)
            or math.prod(self.shape) > 10_000_000
        ):
            raise ValueError("invalid bounded F03 fraction specification")

    @property
    def count(self) -> int:
        return math.prod(self.shape)


@dataclass(frozen=True, slots=True)
class FractionLimits:
    max_values: int
    max_fraction_bits: int
    max_total_bits: int
    max_bytes: int

    def __post_init__(self):
        if any(
            type(value) is not int or value <= 0
            for value in (
                self.max_values,
                self.max_fraction_bits,
                self.max_total_bits,
                self.max_bytes,
            )
        ):
            raise ValueError("explicit positive F03 fraction-storage limits required")


def _specs(specs: tuple[FractionSpec, ...], limits: FractionLimits) -> None:
    if (
        type(specs) is not tuple
        or not specs
        or any(type(spec) is not FractionSpec for spec in specs)
        or len({spec.name for spec in specs}) != len(specs)
        or type(limits) is not FractionLimits
        or sum(spec.count for spec in specs) > limits.max_values
    ):
        raise ValueError("unique bounded F03 fraction specifications required")


def _validate_values(
    values: dict[str, tuple[Fraction, ...]],
    specs: tuple[FractionSpec, ...],
    limits: FractionLimits,
) -> int:
    _specs(specs, limits)
    if type(values) is not dict or set(values) != {spec.name for spec in specs}:
        raise ValueError("invalid F03 fraction-group inventory")
    total = 0
    for spec in specs:
        array = values[spec.name]
        if type(array) is not tuple or len(array) != spec.count:
            raise ValueError(f"invalid F03 fraction array: {spec.name}")
        for value in array:
            if type(value) is not Fraction:
                raise ValueError(f"invalid F03 fraction array: {spec.name}")
            bits = value.numerator.bit_length() + value.denominator.bit_length()
            if (
                max(value.numerator.bit_length(), value.denominator.bit_length())
                > limits.max_fraction_bits
            ):
                raise ValueError("F03 individual fraction bit limit exceeded")
            total += bits
            if total > limits.max_total_bits:
                raise ValueError("F03 cumulative fraction bit limit exceeded")
    return total


def _payload(
    values: dict[str, tuple[Fraction, ...]],
    specs: tuple[FractionSpec, ...],
    limits: FractionLimits,
) -> bytes:
    total = _validate_values(values, specs, limits)
    document = {
        "schema": SCHEMA,
        "total_bits": total,
        "arrays": [
            {
                "name": spec.name,
                "shape": list(spec.shape),
                "values": [
                    [format(value.numerator, "x"), format(value.denominator, "x")]
                    for value in values[spec.name]
                ],
            }
            for spec in specs
        ],
    }
    payload = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "ascii"
    )
    if len(payload) > limits.max_bytes:
        raise ValueError("F03 fraction group exceeds byte limit")
    return payload


def write_group(
    path: Path,
    values: dict[str, tuple[Fraction, ...]],
    specs: tuple[FractionSpec, ...],
    *,
    limits: FractionLimits,
) -> None:
    payload = _payload(values, specs, limits)
    with Path(path).open("xb") as stream:
        stream.write(payload)


def _bounded_payload(path: Path, limit: int) -> bytes:
    with Path(path).open("rb") as stream:
        payload = stream.read(limit + 1)
    if len(payload) > limit:
        raise ValueError("F03 fraction group exceeds byte limit")
    return payload


def read_group(
    path: Path,
    specs: tuple[FractionSpec, ...],
    *,
    limits: FractionLimits,
) -> dict[str, tuple[Fraction, ...]]:
    _specs(specs, limits)
    payload = _bounded_payload(Path(path), limits.max_bytes)
    try:
        document = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid F03 fraction-group JSON") from exc
    if (
        type(document) is not dict
        or set(document) != {"schema", "total_bits", "arrays"}
        or document["schema"] != SCHEMA
        or type(document["total_bits"]) is not int
        or type(document["arrays"]) is not list
        or len(document["arrays"]) != len(specs)
    ):
        raise ValueError("invalid F03 fraction-group document inventory")
    values = {}
    for item, spec in zip(document["arrays"], specs):
        if (
            type(item) is not dict
            or set(item) != {"name", "shape", "values"}
            or item["name"] != spec.name
            or item["shape"] != list(spec.shape)
            or type(item["values"]) is not list
            or len(item["values"]) != spec.count
        ):
            raise ValueError("invalid F03 fraction-array inventory")
        decoded = []
        for pair in item["values"]:
            if (
                type(pair) is not list
                or len(pair) != 2
                or type(pair[0]) is not str
                or type(pair[1]) is not str
                or INTEGER.fullmatch(pair[0]) is None
                or POSITIVE_INTEGER.fullmatch(pair[1]) is None
                or len(pair[0]) > (limits.max_fraction_bits + 3) // 4 + 1
                or len(pair[1]) > (limits.max_fraction_bits + 3) // 4
            ):
                raise ValueError("invalid canonical F03 fraction encoding")
            value = Fraction(int(pair[0], 16), int(pair[1], 16))
            if pair != [format(value.numerator, "x"), format(value.denominator, "x")]:
                raise ValueError("noncanonical F03 fraction encoding")
            decoded.append(value)
        values[spec.name] = tuple(decoded)
    total = _validate_values(values, specs, limits)
    if document["total_bits"] != total or _payload(values, specs, limits) != payload:
        raise ValueError("stale or noncanonical F03 fraction-group payload")
    return values
