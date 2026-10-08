"""Failure-sensitive controls for the external modal observable decoder."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('us3_modal_canary',
    Path(__file__).parents[1]/'scripts/r8_us3_reference_modal_canary_dev.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def _fixture(tmp_path):
    (tmp_path/'run').mkdir()
    (tmp_path/'run/stdout.log').write_text('CalculiX 2.23 finished\n')
    (tmp_path/'run/stderr.log').write_text('')
    (tmp_path/'run/execution.json').write_text(json.dumps(dict(exit_code=0, resource_limit=None)))
    (tmp_path/'plate-modes.inp').write_text('synthetic observable parser control\n')
    (tmp_path/'identity.json').write_text(json.dumps(dict(node_ids=[1, 2], roots=[1],
        deck_sha256=runner.sha(tmp_path/'plate-modes.inp'))))
    lines = ['E I G E N V A L U E   O U T P U T']
    for n in range(1, 7):
        lines.append(f'{n} {n*n:.7E} {n:.7E} {n/(2*np.pi):.7E} {0:.7E}')
    for n in range(1, 7):
        lines += [f'E I G E N V A L U E    N U M B E R {n}',
            'displacements (vx,vy,vz,rx,ry,rz) for set ALLNODES and time 0.',
            '1 '+' '.join(f'{0:.6E}' for _ in range(6)),
            '2 '+' '.join(f'{n*i/10:.6E}' for i in range(1, 7)), '']
    (tmp_path/'plate-modes.dat').write_text('\n'.join(lines))
    return tmp_path/'plate-modes.dat'


def test_complete_headers_associate_all_six_mode_fields(tmp_path):
    _fixture(tmp_path)
    result = runner.parse(tmp_path)
    assert result['qualification'] is False
    assert result['reference_eigen_residual'] == 'NOT_VERIFIED'
    assert len(result['director_rotation_norm_by_mode']) == 6
    assert all(v > 0. for v in result['director_rotation_norm_by_mode'])
    with np.load(tmp_path/'reference-modes.npz') as saved:
        assert saved['modes'].shape == (6, 2, 6)
        assert saved['modes'][5, 1, 5] == 3.6
        assert np.array_equal(saved['eigenvalues'], np.arange(1, 7)**2)


def test_refined_reference_preserves_physical_plate_and_root_definition(tmp_path):
    runner.prepare(tmp_path/'n32', nx=32)
    record = json.loads((tmp_path/'n32/identity.json').read_text())
    assert (record['nx'], record['ny'], record['nodes'], record['elements']) == (32,8,297,512)
    assert record['dimensions_m'] == [1., .2]
    assert record['thickness_m'] == .035 and record['density_kg_m3'] == 7850.
    assert record['roots'] == list(range(1,298,33))
    deck = (tmp_path/'n32/plate-modes.inp').read_text()
    assert '*DENSITY\n7850.' in deck and '*FREQUENCY\n6' in deck
    assert all(f'{node},1,6,0.' in deck for node in record['roots'])


def test_execution_record_uses_runtime_allowlist_not_process_environment(tmp_path, monkeypatch):
    output = tmp_path/'record'
    runner.prepare(output)
    executable, supervisor = tmp_path/'dummy.exe', tmp_path/'supervisor.py'
    executable.write_bytes(b'unexecuted identity fixture')
    supervisor.write_text("ENV={'OMP_NUM_THREADS':'1','NUMBA_DISABLE_JIT':'1',"
        "'PYTHONPATH':'declared-site','FUTURE_CREDENTIAL':'do-not-record',"
        "'MISTRAL_API_KEY':'synthetic-do-not-record'}\n"
        "def supervised(command, folder):\n"
        "    return {'exit_code':0,'resource_limit':None}\n")
    monkeypatch.setattr(runner, 'EXE_SHA', runner.sha(executable))
    monkeypatch.setattr(runner, 'SUPERVISOR_SHA', runner.sha(supervisor))
    monkeypatch.setattr(runner, 'parse', lambda path: {'mocked': True})
    assert runner.run(output, executable, supervisor) == {'mocked': True}
    text = (output/'execution-identity.json').read_text()
    record = json.loads(text)
    assert record['environment'] == {'OMP_NUM_THREADS':'1',
        'NUMBA_DISABLE_JIT':'1','PYTHONPATH':'declared-site'}
    assert 'do-not-record' not in text and 'CREDENTIAL' not in text
    assert 'MISTRAL_API_KEY' not in text


@pytest.mark.parametrize('defect', ('missing-node', 'duplicate-node', 'missing-rotation',
    'missing-mode', 'duplicate-mode', 'negative-eigenvalue', 'complex-frequency',
    'nonfinite', 'support-motion', 'frequency-unit', 'arpack-warning', 'changed-deck',
    'failed-execution', 'resource-abort', 'fatal'))
def test_corrupt_or_failed_external_output_does_not_publish_modes(tmp_path, defect):
    dat = _fixture(tmp_path)
    text = dat.read_text()
    node = '2 '+' '.join(f'{i/10:.6E}' for i in range(1, 7))
    root = '1 '+' '.join(f'{0:.6E}' for _ in range(6))
    if defect == 'missing-node': text = text.replace(node, '', 1)
    elif defect == 'duplicate-node': text = text.replace(node, node+'\n'+node, 1)
    elif defect == 'missing-rotation': text = text.replace(node, ' '.join(node.split()[:4]), 1)
    elif defect == 'missing-mode': text = text[:text.index('E I G E N V A L U E    N U M B E R 6')]
    elif defect == 'duplicate-mode': text = text.replace('N U M B E R 6', 'N U M B E R 5')
    elif defect == 'negative-eigenvalue': text = text.replace('1 1.0000000E+00', '1 -1.0000000E+00', 1)
    elif defect == 'complex-frequency': text = text.replace('0.0000000E+00', '1.0000000E+00', 1)
    elif defect == 'nonfinite': text = text.replace(node, node.replace('1.000000E-01', 'NaN'), 1)
    elif defect == 'support-motion': text = text.replace(root, root.replace('0.000000E+00', '1.000000E+00', 1), 1)
    elif defect == 'frequency-unit': text = text.replace('1.5915494E-01', '1.5915494E+01', 1)
    elif defect == 'arpack-warning': (tmp_path/'run/stdout.log').write_text('*WARNING: ARPACK incomplete\n')
    elif defect == 'changed-deck': (tmp_path/'plate-modes.inp').write_text('different model\n')
    elif defect == 'failed-execution': (tmp_path/'run/execution.json').write_text(json.dumps(dict(exit_code=1, resource_limit=None)))
    elif defect == 'resource-abort': (tmp_path/'run/execution.json').write_text(json.dumps(dict(exit_code=0, resource_limit='timeout')))
    elif defect == 'fatal': (tmp_path/'run/stdout.log').write_text('FATAL: numerical failure\n')
    dat.write_text(text)
    with pytest.raises((ValueError, ArithmeticError)):
        runner.parse(tmp_path)
    assert not (tmp_path/'result.json').exists()
    assert not (tmp_path/'reference-modes.npz').exists()
