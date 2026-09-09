"""Explicit bounded extent tests; no 32-element response or equilibrium solve."""

import ast
from pathlib import Path

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_arch_onset_probe as probe
from docs.reference_cases import ge_beam3_curved_p5_arch_stability_inspection as spectral
from docs.reference_cases.ge_beam3_curved_p5_arch_refinement_case import make_beam, references
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import NonlinearAssemblyHistoryProbe
from docs.reference_cases.ge_beam3_curved_p5_refinement_wave import canonical, sha, git


PARENT = 'ef7964287245829b0112ae81179d314c5c2f00cb'
PROFILE = 'ARCH_ONSET32'
SMALL_HASH = '357c80ede0c6345ff32216cf3cfb749d2c39d7a760eef3cd84ae699862fd89ef'
RAW_HASHES = {'grid-00': (40690, '475cc159011674d23b686db27fc1d4f87398a2a6902d79ba1db135cf8b2c98de'),
              'grid-01': (43591, 'a1102853ff806132b7267cb0dcc698bbb242a6a8392645c2ce53e514d4137fee'),
              'grid-02': (43665, '6e7523853f4ce0c9e82e1736ba954511cafe63f1488ebdffd71407285a1ecb61')}


def test_explicit_32_construction_and_unchanged_default_rejections():
    beam, pattern = make_beam(32, extent=PROFILE)  # Construction only.
    assert len(beam._maps) == 32 and beam._nodes == 65 and beam._extent == PROFILE
    assert len(beam._free) == 378 and np.array_equal(beam._fixed, [0, 64])
    assert sum(map(len, beam.committed.histories)) == 512
    assert pattern[32, 1] == -1. and np.count_nonzero(pattern) == 1
    for extent in ('SMALL8', 'REFINEMENT16'):
        with pytest.raises(ValueError, match='bounded'):
            NonlinearAssemblyHistoryProbe(beam._references, beam._maps, beam._sections, extent=extent)
    with pytest.raises(ValueError): make_beam(32)
    with pytest.raises(ValueError): references(32)
    with pytest.raises(ValueError): probe.records(count=32, progress=None, publish_raw=None)
    with pytest.raises(ValueError, match='bounded'):
        NonlinearAssemblyHistoryProbe(beam._references+(beam._references[-1],),
            beam._maps+(beam._maps[-1],), beam._sections+(beam._sections[-1],), extent=PROFILE)


@pytest.mark.parametrize('count,extent', [(64, PROFILE), (33, PROFILE), (True, PROFILE),
    (32, 'REFINEMENT32'), (32, None), (32, True)])
def test_unregistered_counts_and_profiles_fail_closed(count, extent):
    with pytest.raises(ValueError): make_beam(count, extent=extent)


def test_nested_mesh_geometry_is_unchanged():
    coarse = references(16);fine = references(32, extent=PROFILE)
    for i, old in enumerate(coarse):
        assert np.array_equal(old.coordinates, np.array([fine[2*i].coordinates[0],
            fine[2*i].coordinates[2], fine[2*i+1].coordinates[2]]))
        assert np.array_equal(old.nodal_triads, np.array([fine[2*i].nodal_triads[0],
            fine[2*i].nodal_triads[2], fine[2*i+1].nodal_triads[2]]))
    for n in (2, 4, 8, 16):
        for old, new in zip(references(n), references(n, extent=PROFILE)):
            assert np.array_equal(old.coordinates, new.coordinates)
            assert np.array_equal(old.nodal_triads, new.nodal_triads)


def test_65_node_synthetic_spectra_and_fixed_end_maps():
    # Explicitly synthetic diagonal matrix, not a 32-element mechanics test.
    matrix = np.diag(np.arange(1., 391.))
    matrix[8, 8] = -1.;matrix[11, 11] = -2.
    result = spectral.classify_matrix(matrix, nodes=65, extent=PROFILE)
    assert result['free_dimension'] == 378
    assert result['in_plane_dimension'] == result['out_of_plane_dimension'] == 189
    assert result['full']['negative'] == 2
    assert result['in_plane']['negative'] == result['out_of_plane']['negative'] == 1
    for kind in ('in_plane', 'out_of_plane'):
        assert result[kind]['lowest_nodal_increment'].shape == (65, 6)
        assert np.count_nonzero(result[kind]['lowest_nodal_increment'][[0, 64]]) == 0
    with pytest.raises(ValueError): spectral.classify_matrix(matrix, nodes=65)
    with pytest.raises(ValueError): spectral.classify_matrix(np.eye(396), nodes=66, extent=PROFILE)
    with pytest.raises(ValueError): spectral.spectral(np.eye(379), extent=PROFILE)
    with pytest.raises(ValueError): spectral.spectral(np.eye(187))


def test_profile_does_not_change_existing_spectra_or_uncertainty():
    matrix = np.diag(np.arange(1., 31.));matrix[8, 8] = 1e-16
    old = spectral.classify_matrix(matrix, nodes=5)
    new = spectral.classify_matrix(matrix, nodes=5, extent=PROFILE)
    assert canonical(old) == canonical(new)
    assert new['out_of_plane']['unresolved'] == 1
    matrix[6, 8] = matrix[8, 6] = .01
    with pytest.raises(ValueError, match='reflection'):
        spectral.classify_matrix(matrix, nodes=5, extent=PROFILE)


def test_small_outputs_match_frozen_pre_extension_bytes(monkeypatch):
    monkeypatch.setattr(probe, 'DROPS', (0., .005, .01))
    for extent in ('REFINEMENT16', PROFILE):
        saved = {}
        def publish(label, value):
            data = canonical(value)
            saved[label] = (len(data), sha(data))
            return {'name': label+'.json', 'bytes': len(data), 'sha256': sha(data)}
        result = probe.records(count=2, progress=lambda *args: None, publish_raw=publish, extent=extent)
        assert saved == RAW_HASHES
        assert sha(canonical(result)) == SMALL_HASH and len(canonical(result)) == 1240


def test_assembly_operator_and_transaction_methods_unchanged_from_parent():
    repo = Path(__file__).resolve().parents[1]
    path = 'docs/reference_cases/ge_beam3_curved_p5_assembly_history_probe.py'
    before = ast.parse(git(repo, 'show', PARENT+':'+path))
    after = ast.parse((repo/path).read_text())
    def methods(tree):
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'NonlinearAssemblyHistoryProbe')
        return {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
    old, new = methods(before), methods(after)
    assert set(old) == set(new)
    for name in old.keys()-{'__init__'}:
        assert ast.dump(old[name]) == ast.dump(new[name]), name
    # Only the allowed extent guard and maximum lookup differ in construction.
    assert ast.dump(old['__init__'].args) == ast.dump(new['__init__'].args)
    assert ast.dump(ast.Module(body=old['__init__'].body[3:], type_ignores=[])) == ast.dump(
        ast.Module(body=new['__init__'].body[3:], type_ignores=[]))


def test_search_grid_and_root_rules_unchanged_from_parent():
    repo = Path(__file__).resolve().parents[1]
    path = 'docs/reference_cases/ge_beam3_curved_p5_arch_onset_probe.py'
    old = ast.parse(git(repo, 'show', PARENT+':'+path))
    new = ast.parse((repo/path).read_text())
    def rules(tree):
        return [n for n in tree.body if isinstance(n, ast.Assign) or
                isinstance(n, ast.FunctionDef) and n.name in ('sign', 'locate')]
    assert [ast.dump(n) for n in rules(old)] == [ast.dump(n) for n in rules(new)]
