"""Strict bounded storage for independent primal Ritz diagnostic evidence."""
from __future__ import annotations

import hashlib
import hmac
from pathlib import Path
import zipfile
import numpy as np

MAX_BYTES = 256*1024**2
METADATA = {'__schema': ((1,), np.dtype('int64')),
            '__degree': ((1,), np.dtype('int64')),
            '__digest': ((32,), np.dtype('uint8'))}


def _shapes(n):
    from _b3_e4_f03_primal_checks import expected_shapes
    if type(n) is not int or not 2 <= n <= 24:
        raise ValueError('invalid bounded Ritz degree')
    return expected_shapes(n)


def _digest(payload):
    digest = hashlib.sha256()
    for name in sorted(payload):
        array = np.ascontiguousarray(payload[name])
        digest.update(name.encode('ascii')+b'\0')
        digest.update(array.dtype.str.encode('ascii')+b'\0')
        digest.update(np.asarray(array.shape, dtype='<i8').tobytes())
        digest.update(array.tobytes())
    return np.frombuffer(digest.digest(), dtype=np.uint8).copy()


def _validate(arrays, n):
    shapes = _shapes(n)
    if not isinstance(arrays, dict) or set(arrays) != set(shapes):
        raise ValueError('invalid primal array inventory')
    for name, shape in shapes.items():
        value = arrays[name]
        diagnostic_norm = name in ('norms_squared', 'norm_channels_squared')
        if (not isinstance(value, np.ndarray) or value.dtype != np.float64
                or value.shape != shape or
                (np.isinf(value).any() if diagnostic_norm else not np.isfinite(value).all())):
            raise ValueError(f'invalid primal array: {name}')
    if 'norms_squared_valid' in shapes:
        valid = arrays['norms_squared_valid']
        if not np.isin(valid, [0., 1.]).all():
            raise ValueError('invalid norm measurement validity')
        for i, flag in enumerate(valid):
            total = arrays['norms_squared'][i]
            channels = arrays['norm_channels_squared'][i]
            if ((flag == 1 and (not np.isfinite(total) or not np.isfinite(channels).all()))
                    or (flag == 0 and not np.isnan(total))):
                raise ValueError('undefined norm measurement lacks matching validity marker')
    values = list(arrays.values())
    if any(np.shares_memory(a, b) for i, a in enumerate(values) for b in values[i+1:]):
        raise ValueError('aliased primal evidence arrays')
    if sum(a.nbytes+512 for a in values)+2048 > MAX_BYTES:
        raise ValueError('primal evidence exceeds storage bound')


def pack(arrays, n):
    _validate(arrays, n)
    payload = {name: value.copy(order='C') for name, value in arrays.items()}
    payload['__schema'] = np.array([1], dtype=np.int64)
    payload['__degree'] = np.array([n], dtype=np.int64)
    payload['__digest'] = _digest(payload)
    return payload


def unpack(source, n):
    shapes = _shapes(n)
    types = {name: (shape, np.dtype('float64')) for name, shape in shapes.items()}
    types.update(METADATA)
    if isinstance(source, (str, Path)):
        path = Path(source)
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if (len(names) != len(types) or set(names) != {name+'.npy' for name in types}
                    or sum(info.file_size for info in archive.infolist()) > MAX_BYTES):
                raise ValueError('invalid primal ZIP inventory or size')
            # Inspect bounded NPY headers before allowing NumPy to allocate arrays.
            for name, (shape, dtype) in types.items():
                with archive.open(name+'.npy') as stream:
                    version = np.lib.format.read_magic(stream)
                    reader = {(1, 0): np.lib.format.read_array_header_1_0,
                              (2, 0): np.lib.format.read_array_header_2_0}.get(version)
                    if reader is None:
                        raise ValueError('unsupported primal NPY header version')
                    stored_shape, fortran, stored_dtype = reader(stream, max_header_size=4096)
                    if stored_shape != shape or stored_dtype != dtype or fortran:
                        raise ValueError('primal NPY header disagrees with exact case layout')
                    size = stream.tell()+int(np.prod(shape))*dtype.itemsize
                    if size != archive.getinfo(name+'.npy').file_size:
                        raise ValueError('primal NPY payload size mismatch')
        with np.load(path, allow_pickle=False) as archive:
            payload = {name: archive[name].copy() for name in types}
    elif isinstance(source, dict):
        if set(source) != set(types):
            raise ValueError('invalid primal payload inventory')
        values = list(source.values())
        if any(not isinstance(value, np.ndarray) for value in values):
            raise ValueError('invalid primal payload type')
        for name, (shape, dtype) in types.items():
            if source[name].shape != shape or source[name].dtype != dtype:
                raise ValueError('invalid primal payload shape or dtype')
        if sum(value.nbytes+512 for value in values) > MAX_BYTES:
            raise ValueError('primal payload exceeds storage bound')
        if any(np.shares_memory(a, b) for i, a in enumerate(values) for b in values[i+1:]):
            raise ValueError('aliased primal payload')
        payload = {name: value.copy() for name, value in source.items()}
    else:
        raise ValueError('invalid primal archive source')
    for name, (shape, dtype) in types.items():
        if payload[name].shape != shape or payload[name].dtype != dtype:
            raise ValueError('invalid primal payload shape or dtype')
    if payload['__schema'][0] != 1 or payload['__degree'][0] != n:
        raise ValueError('primal case/schema identity mismatch')
    if not hmac.compare_digest(payload['__digest'].tobytes(),
            _digest({k: v for k, v in payload.items() if k != '__digest'}).tobytes()):
        raise ValueError('primal payload digest mismatch')
    arrays = {name: payload[name].copy() for name in shapes}
    _validate(arrays, n)
    return arrays
