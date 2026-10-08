import importlib.util
from pathlib import Path
import zipfile

import numpy as np
import pytest

_path = Path(__file__).resolve().parents[1]/'scripts/_b3_e4_f03_primal_archive.py'
_spec = importlib.util.spec_from_file_location('_f03_primal_archive_test', _path)
module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(module)


@pytest.fixture
def arrays(monkeypatch):
    monkeypatch.setattr(module, '_shapes', lambda n: {'K': (3, 3), 'q': (3,)})
    return {'K': np.eye(3), 'q': np.arange(3, dtype=np.float64)}


def test_archive_roundtrip_owned_and_case_bound(arrays, tmp_path):
    payload = module.pack(arrays, 4)
    path = tmp_path/'case.npz'
    np.savez_compressed(path, **payload)
    restored = module.unpack(path, 4)
    for name in arrays:
        np.testing.assert_array_equal(arrays[name], restored[name])
        assert not np.shares_memory(arrays[name], restored[name])
    with pytest.raises(ValueError, match='identity'):
        module.unpack(path, 8)


def test_digest_corruption_and_alias_rejected(arrays):
    payload = module.pack(arrays, 4)
    payload['q'][1] += 1
    with pytest.raises(ValueError, match='digest'):
        module.unpack(payload, 4)
    arrays['q'] = arrays['K'][0]
    with pytest.raises(ValueError, match='aliased'):
        module.pack(arrays, 4)


def test_missing_extra_nonfinite_and_dtype_rejected(arrays):
    for bad in ({'K': arrays['K']}, dict(arrays, extra=np.zeros(1)),
                dict(arrays, q=np.array([np.nan, 0, 0])),
                dict(arrays, q=np.zeros(3, dtype=np.int64))):
        with pytest.raises(ValueError):
            module.pack(bad, 4)


def test_duplicate_zip_and_header_shape_rejected_before_array_load(arrays, tmp_path, monkeypatch):
    path = tmp_path/'duplicate.npz'
    np.savez_compressed(path, **module.pack(arrays, 4))
    with zipfile.ZipFile(path, 'a') as archive:
        raw = archive.read('q.npy')
        with pytest.warns(UserWarning):
            archive.writestr('q.npy', raw)
    with pytest.raises(ValueError, match='inventory'):
        module.unpack(path, 4)
    payload = module.pack(arrays, 4)
    payload['q'] = np.zeros(30)
    altered = tmp_path/'wrong-shape.npz'
    np.savez_compressed(altered, **payload)
    monkeypatch.setattr(np, 'load', lambda *a, **kw: pytest.fail('header must reject before allocation'))
    with pytest.raises(ValueError, match='header'):
        module.unpack(altered, 4)


def test_archive_bound(arrays, monkeypatch):
    monkeypatch.setattr(module, 'MAX_BYTES', 12)
    with pytest.raises(ValueError, match='storage bound'):
        module.pack(arrays, 4)


def test_undefined_norm_requires_explicit_marker_and_never_admits_nonfinite_state(monkeypatch):
    monkeypatch.setattr(module, '_shapes', lambda n: {'q': (3,), 'norms_squared': (2,),
        'norm_channels_squared': (2, 3), 'norms_squared_valid': (2,)})
    arrays = {'q': np.ones(3), 'norms_squared': np.array([np.nan, 6.]),
        'norm_channels_squared': np.array([[np.nan]*3, [1., 2., 3.]]),
        'norms_squared_valid': np.array([0., 1.])}
    restored = module.unpack(module.pack(arrays, 4), 4)
    assert np.isnan(restored['norms_squared'][0])
    bad = {k: v.copy() for k, v in arrays.items()}; bad['norms_squared_valid'][0] = 1
    with pytest.raises(ValueError, match='validity marker'):
        module.pack(bad, 4)
    bad = {k: v.copy() for k, v in arrays.items()}; bad['q'][0] = np.nan
    with pytest.raises(ValueError, match='invalid primal array: q'):
        module.pack(bad, 4)
    bad = {k: v.copy() for k, v in arrays.items()}; bad['norm_channels_squared'][0, 0] = np.inf
    with pytest.raises(ValueError, match='invalid primal array'):
        module.pack(bad, 4)
