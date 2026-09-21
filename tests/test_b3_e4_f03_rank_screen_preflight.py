"""Independent bounded SVD check of the proposed algebraic rank statistic."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest
from scipy import sparse

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_inventory as inventory
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell
import b3_e4_f03_rank_screen as screen


def test_distinct_coupling_inventory_omits_load_only_duplicates():
    cases=screen._cases()
    assert len(cases)==48
    assert len({c.identity for c in cases})==48
    assert all(c.loading=='smooth' for c in cases)
    for mesh in inventory.meshes():
        assert {(c.topology,c.law) for c in cases if c.mesh==mesh}=={
            ('Q4','P0'),('Q4','P1'),('CST','P0'),('CST','P1')}


@pytest.mark.parametrize('topology',('Q4','CST'))
@pytest.mark.parametrize('law',('P0','P1'))
def test_gram_eigen_ratio_matches_direct_small_dense_svd(topology,law):
    mesh=inventory.Mesh(3,6,6,3)
    case=inventory.Case(mesh,topology,'smooth',law)
    got=screen._row_spectrum(case)
    model=shell.panel(mesh.n_s,mesh.n_y,topology)
    cs,cb,_=line.coupling(model,mesh.n_beam,mesh.n_mortar,law)
    fs=np.setdiff1d(np.arange(model.dof_count),model.supported)
    fb=np.setdiff1d(np.arange(beam.dof_count(mesh.n_beam)),
                    beam.root_dofs(mesh.n_beam))
    matrix=sparse.hstack((-cs[:,fs],cb[:,fb])).toarray()
    singular=np.linalg.svd(matrix/np.linalg.norm(matrix,axis=1)[:,None],
                           compute_uv=False)
    np.testing.assert_allclose(got['singular_ratio'],singular[-1]/singular[0],
                               rtol=1e-9,atol=1e-12)
    assert got['rows']==matrix.shape[0] and got['columns']==matrix.shape[1]
    assert got['passes_algebraic_floor']
