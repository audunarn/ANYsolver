"""Bounded binary checkpoints for the experimental mixed GE owner only.

The existing JSON V1 checkpoints retain their decoding contract. V2 carries
small canonical metadata followed by exact-shape little-endian float64 arrays
and a byte-integrity digest; restoration still performs mechanical validation.
An incompatible future mechanics change must receive a new schema. This format
does not authenticate the source or installed artifact that produced the bytes.
"""

from __future__ import annotations

from hashlib import sha256
import json
from math import prod

import numpy as np


MAGIC = b"ANYSGECP2\0"
MAX_HEADER_BYTES = 8192
MAX_CHECKPOINT_BYTES = 128 * 1024 * 1024
SCHEMAS = {
    "linear": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_LINEAR_V2",
    "finite": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_FINITE_V2",
    "finite_material": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_FINITE_MATERIAL_V3",
    "finite_shell_material": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_FINITE_SHELL_J2_V4",
}


def encode(kind: str, model: str, generation: int,
           arrays: tuple[tuple[str, np.ndarray], ...]) -> bytes:
    """Encode owned-state arrays without JSON's model-size-dependent growth."""
    if (type(kind) is not str or kind not in SCHEMAS or type(model) is not str or
            type(generation) is not int or generation < 1 or
            type(arrays) is not tuple):
        raise ValueError("valid experimental binary checkpoint fields required")
    names = [name for name, _ in arrays]
    if any(type(name) is not str for name in names) or len(names) != len(set(names)):
        raise ValueError("unique binary checkpoint array names required")
    packed = []
    shapes = []
    total = 0
    for name, values in arrays:
        value = np.asarray(values, dtype=np.float64)
        if not np.isfinite(value).all():
            raise ValueError("finite binary checkpoint arrays required")
        data = value.astype("<f8", copy=False).tobytes(order="C")
        total += len(data)
        if total > MAX_CHECKPOINT_BYTES:
            raise ValueError("binary checkpoint exceeds resource envelope")
        packed.append(data)
        shapes.append([name, list(value.shape)])
    metadata = {"schema": SCHEMAS[kind], "model": model,
                "generation": generation, "arrays": shapes}
    header = json.dumps(metadata, sort_keys=True, separators=(",", ":"),
                        allow_nan=False).encode("ascii")
    if len(header) > MAX_HEADER_BYTES:
        raise ValueError("binary checkpoint metadata exceeds bound")
    content = MAGIC + len(header).to_bytes(4, "little") + header + b"".join(packed)
    if len(content) + sha256().digest_size > MAX_CHECKPOINT_BYTES:
        raise ValueError("binary checkpoint exceeds resource envelope")
    return content + sha256(content).digest()


def decode(raw: bytes, model: str, expected_shapes) -> tuple[str, int, dict]:
    """Validate byte framing before exposing model-sized array views.

    expected_shapes(kind, generation) returns ordered (name, shape) pairs from
    the compiled owner. Header shapes cannot allocate or redefine state.
    """
    if (type(raw) is not bytes or not raw.startswith(MAGIC) or
            len(raw) > MAX_CHECKPOINT_BYTES or
            len(raw) < len(MAGIC) + 4 + sha256().digest_size):
        raise ValueError("bounded experimental binary checkpoint required")
    start = len(MAGIC) + 4
    header_size = int.from_bytes(raw[len(MAGIC):start], "little")
    if (header_size < 1 or header_size > MAX_HEADER_BYTES or
            start + header_size + sha256().digest_size > len(raw)):
        raise ValueError("invalid experimental binary checkpoint header")
    content_end = len(raw) - sha256().digest_size
    if sha256(raw[:content_end]).digest() != raw[content_end:]:
        raise ValueError("experimental binary checkpoint digest mismatch")
    header_bytes = raw[start:start + header_size]
    try:
        header = json.loads(header_bytes.decode("ascii"))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("invalid experimental binary checkpoint metadata") from exc
    try:
        canonical = json.dumps(header, sort_keys=True, separators=(",", ":"),
                               allow_nan=False).encode("ascii")
    except (TypeError, ValueError, RecursionError, UnicodeError) as exc:
        raise ValueError("invalid experimental binary checkpoint metadata") from exc
    if canonical != header_bytes:
        raise ValueError("noncanonical experimental binary checkpoint metadata")
    if (type(header) is not dict or set(header) !=
            {"schema", "model", "generation", "arrays"} or
            header["model"] != model or
            type(header["generation"]) is not int or
            not 1 <= header["generation"] <= MAX_CHECKPOINT_BYTES // 8 or
            type(header["arrays"]) is not list):
        raise ValueError("incompatible experimental binary checkpoint")
    kind = next((name for name, schema in SCHEMAS.items()
                 if header["schema"] == schema), None)
    if kind is None:
        raise ValueError("unknown experimental binary checkpoint schema")
    generation = header["generation"]
    expected = tuple(expected_shapes(kind, generation))
    if header["arrays"] != [[name, list(shape)] for name, shape in expected]:
        raise ValueError("incompatible experimental binary checkpoint layout")
    total = sum(8 * prod(shape) for _name, shape in expected)
    offset = start + header_size
    if offset + total != content_end:
        raise ValueError("invalid experimental binary checkpoint length")
    arrays = {}
    for name, shape in expected:
        count = prod(shape)
        value = np.frombuffer(raw, dtype="<f8", count=count,
                              offset=offset).reshape(shape)
        if not np.isfinite(value).all():
            raise ValueError("nonfinite experimental binary checkpoint")
        arrays[name] = value
        offset += 8 * count
    return kind, generation, arrays
