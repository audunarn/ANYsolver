"""Source and budget guards for the bounded c2 current-owner bridge."""
import json
import sys
from copy import deepcopy

import pytest

from scripts.r8_f03_c2_current_owner_bridge_dev import (
    MEMORY, WORKTREE, case, guarded_run, prior_wall, product_provenance,
    source_fingerprint,
)


@pytest.mark.parametrize('level,half_cells,rows', ((32, 64, 80), (64, 128, 160)))
def test_exact_frozen_c2_grid_mapping(level, half_cells, rows):
    definition, policy = case(level)
    assert policy['span_halfcells'] == 4
    assert policy['beam_halfcells'] == half_cells
    assert len(policy['support_membership']) * 5 == rows
    assert definition.lines[0].basis == 'p0'
    assert len(definition.shell.q4_elements) == level * (level // 4)


def test_unregistered_grid_and_check_refused(tmp_path):
    provenance = product_provenance()
    assert all(record['path'].startswith(str(WORKTREE))
               for record in provenance.values())
    assert {'shell_norm', 'beam_and_scalar_norm', 'physical_loads',
            'shell_modal_reference', 'beam_reference', 'actual_primal',
            'discrete_reference', 'model', 'frozen_model_fixture'} <= set(provenance)
    with pytest.raises(ValueError, match='declared'):
        case(16)
    with pytest.raises(ValueError, match='unregistered'):
        guarded_run('other', tmp_path)


def test_provenance_refuses_transitive_helper_outside_worktree(monkeypatch):
    helper = sys.modules['scripts.b3_e4_bl5_riesz_controls_dev']
    monkeypatch.setattr(helper, '__file__', str(WORKTREE.parent / 'outside.py'))
    with pytest.raises(RuntimeError, match='beam_and_scalar_norm import escaped'):
        product_provenance()


def test_64_grid_refuses_missing_or_excessive_memory_evidence(tmp_path):
    source = tmp_path / 'source-check-1'
    source.mkdir()
    (source / 'receipt.json').write_text(json.dumps({
        'process_wall_seconds': 1., 'exit_code': 0, 'stop_reason': 'EXITED',
        'source_sha256': source_fingerprint(),
    }))
    with pytest.raises(RuntimeError, match='32x8 memory evidence'):
        guarded_run('64', tmp_path)
    smaller = tmp_path / 'grid-32x8'
    smaller.mkdir()
    (smaller / 'receipt.json').write_text(json.dumps({
        'process_wall_seconds': 1., 'exit_code': 0,
        'stop_reason': 'EXITED',
        'peak_process_tree_rss_bytes': MEMORY // 4 + 1,
        'source_sha256': source_fingerprint(),
    }))
    assert prior_wall(tmp_path) == 2.
    with pytest.raises(RuntimeError, match='memory estimate'):
        guarded_run('64', tmp_path)
    assert not (tmp_path / 'grid-64x16').exists()


@pytest.mark.parametrize('stale_field', ('helper', 'test'))
def test_numerical_preflight_refuses_stale_source_hash(tmp_path, stale_field):
    source = tmp_path / 'source-check-1'
    source.mkdir()
    stale = deepcopy(source_fingerprint())
    if stale_field == 'helper':
        stale['product_provenance']['physical_loads']['sha256'] = '0' * 64
    else:
        stale['tests/test_r8_f03_c2_current_owner_bridge_dev.py'] = '0' * 64
    (source / 'receipt.json').write_text(json.dumps({
        'process_wall_seconds': 1., 'exit_code': 0, 'stop_reason': 'EXITED',
        'source_sha256': stale,
    }))
    with pytest.raises(RuntimeError, match='matching full source check'):
        guarded_run('32', tmp_path)
    assert not (tmp_path / 'grid-32x8').exists()


def test_prospective_reserve_refuses_new_numerical_child(tmp_path):
    previous = tmp_path / 'source-check-1'
    previous.mkdir()
    (previous / 'receipt.json').write_text(json.dumps({
        'process_wall_seconds': 76.,
    }))
    with pytest.raises(RuntimeError, match='allowance'):
        guarded_run('32', tmp_path)
    assert not (tmp_path / 'grid-32x8').exists()
