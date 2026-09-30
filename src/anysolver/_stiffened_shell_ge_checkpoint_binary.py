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
S3_MAGIC = b"ANYSGECP5\0"
S3_SCHEMA = "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_FINITE_S3_J2_V5"
CHART_MAGIC = b"ANYSGECP6\0"
CHART_SCHEMA = "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_OWNED_CHART_V6"
CHART_S3_SCHEMA = "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_ANCHORED_S3_J2_V6"
NATIVE_SHELL_MAGIC = b"ANYSGECP8\0"
NATIVE_SHELL_SCHEMA = "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_NATIVE_SHELL_J2_V8"
CHART_NATIVE_SHELL_SCHEMA = "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_ANCHORED_NATIVE_SHELL_J2_V8"
MAX_HEADER_BYTES = 8192
MAX_CHECKPOINT_BYTES = 128 * 1024 * 1024
MAX_S3_STATE_BYTES = 128 * 1024
SCHEMAS = {
    "linear": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_LINEAR_V2",
    "finite": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_FINITE_V2",
    "finite_material": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_FINITE_MATERIAL_V3",
    "finite_shell_material": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_FINITE_SHELL_J2_V4",
    "finite_chart": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_ANCHORED_FINITE_V6",
    "finite_chart_material": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_ANCHORED_MATERIAL_V6",
    "finite_chart_shell_material": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_ANCHORED_SHELL_J2_V6",
    "finite_native_material": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_NATIVE_MATERIAL_V7",
    "finite_chart_native_material": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_ANCHORED_NATIVE_MATERIAL_V7",
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


def encode_s3(model: str, generation: int,
              arrays: tuple[tuple[str, np.ndarray], ...],
              states: tuple[bytes, ...], *, anchored: bool = False,
              native_material: bool = False) -> bytes:
    """Pack fixed numeric state and bounded native S3 model-bound blobs.

    V1–V4 framing and decoding are unaffected. Native S3 deserialization and
    mechanical endpoint checks remain the mixed owner's responsibility.
    """
    if (type(model) is not str or type(generation) is not int or
            generation < 1 or type(arrays) is not tuple or
            type(states) is not tuple or (not states and not native_material) or
            type(native_material) is not bool):
        raise ValueError("valid S3 mixed checkpoint fields required")
    names = [name for name, _ in arrays]
    if any(type(name) is not str for name in names) or len(names) != len(set(names)):
        raise ValueError("unique S3 checkpoint array names required")
    packed = []
    shapes = []
    total = 0
    for name, values in arrays:
        value = np.asarray(values, dtype=np.float64)
        if not np.isfinite(value).all():
            raise ValueError("finite S3 checkpoint arrays required")
        data = value.astype("<f8", copy=False).tobytes(order="C")
        total += len(data)
        if total > MAX_CHECKPOINT_BYTES:
            raise ValueError("S3 checkpoint exceeds resource envelope")
        packed.append(data)
        shapes.append([name, list(value.shape)])
    for state in states:
        if (type(state) is not bytes or not state or
                len(state) > MAX_S3_STATE_BYTES):
            raise ValueError("bounded native S3 checkpoint state required")
        total += 4 + len(state)
        if total > MAX_CHECKPOINT_BYTES:
            raise ValueError("S3 checkpoint exceeds resource envelope")
    if type(anchored) is not bool:
        raise ValueError("explicit S3 checkpoint chart policy required")
    schema = ((CHART_NATIVE_SHELL_SCHEMA if anchored else NATIVE_SHELL_SCHEMA)
              if native_material else (CHART_S3_SCHEMA if anchored else S3_SCHEMA))
    magic = NATIVE_SHELL_MAGIC if native_material else S3_MAGIC
    metadata = {"schema": schema, "model": model,
                "generation": generation, "arrays": shapes,
                "s3_states": len(states)}
    header = json.dumps(metadata, sort_keys=True, separators=(",", ":"),
                        allow_nan=False).encode("ascii")
    if len(header) > MAX_HEADER_BYTES:
        raise ValueError("S3 checkpoint metadata exceeds bound")
    content = (magic + len(header).to_bytes(4, "little") + header +
               b"".join(packed) +
               b"".join(len(state).to_bytes(4, "little") + state
                        for state in states))
    if len(content) + sha256().digest_size > MAX_CHECKPOINT_BYTES:
        raise ValueError("S3 checkpoint exceeds resource envelope")
    return content + sha256(content).digest()


def decode_s3(raw: bytes, model: str, expected_shapes,
              expected_s3_states: int, *, anchored: bool = False,
              native_material: bool = False) -> tuple[int, dict, tuple[bytes, ...]]:
    """Decode V5 only after digest, compiled shapes, and blob counts agree."""
    magic = NATIVE_SHELL_MAGIC if native_material else S3_MAGIC
    schema = ((CHART_NATIVE_SHELL_SCHEMA if anchored else NATIVE_SHELL_SCHEMA)
              if native_material else (CHART_S3_SCHEMA if anchored else S3_SCHEMA))
    if (type(native_material) is not bool or type(anchored) is not bool or
            type(raw) is not bytes or not raw.startswith(magic) or
            len(raw) > MAX_CHECKPOINT_BYTES or
            len(raw) < len(magic) + 4 + sha256().digest_size or
            type(expected_s3_states) is not int or
            expected_s3_states < (0 if native_material else 1)):
        raise ValueError("bounded S3 mixed checkpoint required")
    start = len(magic) + 4
    header_size = int.from_bytes(raw[len(magic):start], "little")
    if (header_size < 1 or header_size > MAX_HEADER_BYTES or
            start + header_size + sha256().digest_size > len(raw)):
        raise ValueError("invalid S3 checkpoint header")
    content_end = len(raw) - sha256().digest_size
    if sha256(raw[:content_end]).digest() != raw[content_end:]:
        raise ValueError("S3 checkpoint digest mismatch")
    header_bytes = raw[start:start + header_size]
    try:
        header = json.loads(header_bytes.decode("ascii"))
        canonical = json.dumps(header, sort_keys=True, separators=(",", ":"),
                               allow_nan=False).encode("ascii")
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError,
            RecursionError) as exc:
        raise ValueError("invalid S3 checkpoint metadata") from exc
    if canonical != header_bytes:
        raise ValueError("noncanonical S3 checkpoint metadata")
    if (type(header) is not dict or set(header) !=
            {"schema", "model", "generation", "arrays", "s3_states"} or
            header["schema"] != schema or header["model"] != model or
            type(header["generation"]) is not int or
            not 1 <= header["generation"] <= MAX_CHECKPOINT_BYTES // 8 or
            type(header["arrays"]) is not list or
            type(header["s3_states"]) is not int or
            header["s3_states"] != expected_s3_states):
        raise ValueError("incompatible S3 mixed checkpoint")
    generation = header["generation"]
    expected = tuple(expected_shapes(generation))
    if header["arrays"] != [[name, list(shape)] for name, shape in expected]:
        raise ValueError("incompatible S3 checkpoint layout")
    numeric_bytes = sum(8 * prod(shape) for _name, shape in expected)
    offset = start + header_size
    if offset + numeric_bytes > content_end:
        raise ValueError("invalid S3 checkpoint length")
    arrays = {}
    for name, shape in expected:
        count = prod(shape)
        value = np.frombuffer(raw, dtype="<f8", count=count,
                              offset=offset).reshape(shape)
        if not np.isfinite(value).all():
            raise ValueError("nonfinite S3 checkpoint arrays")
        arrays[name] = value
        offset += 8 * count
    states = []
    for _ in range(expected_s3_states):
        if offset + 4 > content_end:
            raise ValueError("truncated S3 checkpoint state length")
        length = int.from_bytes(raw[offset:offset + 4], "little")
        offset += 4
        if length < 1 or length > MAX_S3_STATE_BYTES or offset + length > content_end:
            raise ValueError("invalid S3 checkpoint state length")
        states.append(raw[offset:offset + length])
        offset += length
    if offset != content_end:
        raise ValueError("unexpected S3 checkpoint trailing data")
    return generation, arrays, tuple(states)


def encode_chart(model, generation, anchors, physical_witness, inner):
    """Distinct pose-chart framing around a distinctly identified numeric layout.

    Event generation is separate from the inner accepted load-step count.
    The witness is the issued accepted physical orientation, not authentication.
    """
    from ._stiffened_shell_rotation_charts import owned_anchors
    anchors = np.asarray(anchors, dtype=float)
    if anchors.ndim != 3:
        raise ValueError("complete shell chart anchors required")
    anchors = owned_anchors(anchors, len(anchors))
    witness = owned_anchors(physical_witness, len(anchors))
    if (type(model) is not str or type(generation) is not int or generation < 2 or
            type(inner) is not bytes or not inner.startswith((MAGIC, S3_MAGIC, NATIVE_SHELL_MAGIC))):
        raise ValueError("accepted chart event and bounded numeric snapshot required")
    metadata = {"schema": CHART_SCHEMA, "model": model,
                "generation": generation, "inner_bytes": len(inner)}
    header = json.dumps(metadata, sort_keys=True, separators=(",", ":"),
                        allow_nan=False).encode("ascii")
    total = len(CHART_MAGIC)+4+len(header)+2*anchors.size*8+len(inner)+32
    if len(header) > MAX_HEADER_BYTES or total > MAX_CHECKPOINT_BYTES:
        raise ValueError("shell chart checkpoint exceeds resource envelope")
    content = (CHART_MAGIC+len(header).to_bytes(4, "little")+header+
               anchors.astype("<f8", copy=False).tobytes()+
               witness.astype("<f8", copy=False).tobytes()+inner)
    return content+sha256(content).digest()


def decode_chart(raw, model, nodes):
    """Validate framing and compiled pose shape before exposing owned arrays."""
    from ._stiffened_shell_rotation_charts import owned_anchors
    if (type(raw) is not bytes or not raw.startswith(CHART_MAGIC) or
            type(nodes) is not int or nodes < 1 or len(raw) > MAX_CHECKPOINT_BYTES or
            len(raw) < len(CHART_MAGIC)+4+32):
        raise ValueError("bounded shell chart checkpoint required")
    end = len(raw)-32
    if sha256(raw[:end]).digest() != raw[end:]:
        raise ValueError("shell chart checkpoint digest mismatch")
    start = len(CHART_MAGIC)+4
    size = int.from_bytes(raw[len(CHART_MAGIC):start], "little")
    if not 1 <= size <= MAX_HEADER_BYTES or start+size > end:
        raise ValueError("invalid shell chart checkpoint header")
    try:
        metadata = json.loads(raw[start:start+size].decode("ascii"))
        canonical = json.dumps(metadata, sort_keys=True, separators=(",", ":"),
                               allow_nan=False).encode("ascii")
    except (ValueError, UnicodeError, RecursionError, TypeError) as exc:
        raise ValueError("invalid shell chart checkpoint metadata") from exc
    if (canonical != raw[start:start+size] or type(metadata) is not dict or
            set(metadata) != {"schema", "model", "generation", "inner_bytes"} or
            metadata["schema"] != CHART_SCHEMA or metadata["model"] != model or
            type(metadata["generation"]) is not int or
            not 2 <= metadata["generation"] <= MAX_CHECKPOINT_BYTES//8 or
            type(metadata["inner_bytes"]) is not int or metadata["inner_bytes"] < 1):
        raise ValueError("incompatible shell chart checkpoint")
    offset = start+size
    length = nodes*9*8
    if offset+2*length+metadata["inner_bytes"] != end:
        raise ValueError("shell chart checkpoint shape mismatch")
    anchors = owned_anchors(np.frombuffer(raw, dtype="<f8", count=nodes*9,
                                          offset=offset).reshape(nodes, 3, 3), nodes)
    witness = owned_anchors(np.frombuffer(raw, dtype="<f8", count=nodes*9,
                                          offset=offset+length).reshape(nodes, 3, 3), nodes)
    inner = raw[offset+2*length:end]
    if not inner.startswith((MAGIC, S3_MAGIC, NATIVE_SHELL_MAGIC)):
        raise ValueError("distinct numeric chart snapshot required")
    return metadata["generation"], anchors, witness, inner
