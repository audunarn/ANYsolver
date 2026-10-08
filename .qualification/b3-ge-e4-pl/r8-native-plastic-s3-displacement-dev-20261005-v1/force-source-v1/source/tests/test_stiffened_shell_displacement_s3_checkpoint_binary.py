"""Additive paired S3 state framing; mechanical admission remains separate."""
from pathlib import Path
from hashlib import sha256
import numpy as np
import pytest
from anysolver._stiffened_shell_ge_checkpoint_binary import (
    encode_s3, decode_s3, NATIVE_SHELL_DISPLACEMENT_MAGIC)


ARRAYS = (('q', np.array((1., -2., 3.))), ('accepted_factors', np.array((.5, 1.))))
STATES = (b'native-state-a', b'native-state-b')


def shapes(_generation):
    return (('q', (3,)), ('accepted_factors', (2,)))


@pytest.mark.parametrize('native', (False, True))
@pytest.mark.parametrize('anchored', (False, True))
def test_old_s3_checkpoint_bytes_unchanged(native, anchored):
    expected = Path(__file__).parent/'data/native_s3_checkpoint_legacy'/f'native-{int(native)}-anchored-{int(anchored)}.bin'
    raw = encode_s3('model-a', 2, ARRAYS, STATES, native_material=native, anchored=anchored)
    assert raw == expected.read_bytes()
    generation, arrays, states = decode_s3(raw, 'model-a', shapes, 2, native_material=native, anchored=anchored)
    assert generation == 2 and states == STATES
    np.testing.assert_array_equal(arrays['q'], ARRAYS[0][1])


def test_displacement_s3_paired_blobs_distinct_bounded_roundtrip():
    raw = encode_s3('model-a', 2, ARRAYS, STATES, native_material=True, displacement=True)
    assert raw.startswith(NATIVE_SHELL_DISPLACEMENT_MAGIC)
    generation, arrays, states = decode_s3(raw, 'model-a', shapes, 2, native_material=True, displacement=True)
    assert generation == 2 and states == STATES
    assert not arrays['q'].flags.writeable
    np.testing.assert_array_equal(arrays['q'], ARRAYS[0][1])
    with pytest.raises(ValueError):
        decode_s3(raw, 'model-a', shapes, 2, native_material=True)
    with pytest.raises(ValueError):
        decode_s3(raw, 'foreign', shapes, 2, native_material=True, displacement=True)
    with pytest.raises(ValueError):
        decode_s3(raw, 'model-a', shapes, 4, native_material=True, displacement=True)
    with pytest.raises(ValueError):
        decode_s3(raw, 'model-a', lambda _: (('q', (4,)),), 2, native_material=True, displacement=True)
    corrupted = bytearray(raw)
    corrupted[-33] ^= 1
    with pytest.raises(ValueError, match='digest'):
        decode_s3(bytes(corrupted), 'model-a', shapes, 2, native_material=True, displacement=True)
    truncated = raw[:-33]
    truncated += sha256(truncated).digest()
    with pytest.raises(ValueError, match='length'):
        decode_s3(truncated, 'model-a', shapes, 2, native_material=True, displacement=True)


@pytest.mark.parametrize('options,states', (
    ({'native_material': False}, STATES),
    ({'native_material': True, 'anchored': True}, STATES),
    ({'native_material': True}, (STATES[0],)),
    ({'native_material': True}, ()),
))
def test_displacement_s3_rejects_incompatible_configuration(options, states):
    with pytest.raises(ValueError, match='displacement'):
        encode_s3('model-a', 2, ARRAYS, states, displacement=True, **options)
