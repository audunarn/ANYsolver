"""Bounded physical observables before registering the F03 inventory."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest
from scipy import sparse
from scipy.sparse.linalg import spsolve

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_loaded_preflight as loaded
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell


@pytest.mark.parametrize('topology',('Q4','CST'))
@pytest.mark.parametrize('law',('P0','P1'))
@pytest.mark.parametrize('loading',('smooth','sine'))
def test_loaded_classical_balance_and_finite_field_enclosure(topology,law,loading):
    result=loaded.evaluate(2,3,4,2,topology,law,loading,depth=5)
    work_scale=max(1.,abs(result.external_work_joule))
    assert abs(result.energy_identity_joule)/work_scale<1e-9
    assert result.free_force_scaled_max<1e-8
    assert result.weak_gap_scaled_max<1e-9
    assert result.shell_energy_joule>=0
    assert result.beam_energy_joule>=0
    assert result.integrated_gap_metre>=0
    bounds=result.finite_field_component_bounds_metre
    assert len(bounds)==3
    assert all(0<=lower<=upper for lower,upper in bounds)
    # Length is 1 m. The componentwise continuous-field upper enclosures
    # bound the L2 gap; sampled stations or weak rows cannot establish this.
    assert result.integrated_gap_metre<=np.linalg.norm([b[1] for b in bounds])+1e-12
    assert all(np.isfinite(result.beam_tip_displacement_metre))
    scalar_outputs=(result.shell_energy_joule,result.beam_energy_joule,
                    result.external_work_joule,result.interface_work_joule,
                    result.integrated_gap_metre,
                    *(number for pair in bounds for number in pair))
    assert np.all(np.isfinite(scalar_outputs))


def test_tip_yaw_is_physical_length_scaled_not_raw_rotation():
    model=shell.panel(2,3,'Q4'); nb=4
    ks=shell.stiffness(model); kb=beam.assembled_stiffness(nb)
    cs,cb,_=line.coupling(model,nb,2,'P1')
    k=sparse.block_diag((ks,kb),format='csr')
    c=sparse.hstack((-cs,cb),format='csr')
    fixed=np.r_[model.supported,model.dof_count+beam.root_dofs(nb)]
    free=np.setdiff1d(np.arange(k.shape[0]),fixed)
    f=np.r_[np.zeros(model.dof_count),beam.assembled_load(nb,'smooth')]
    a=sparse.bmat(((k[free,:][:,free],c[:,free].T),(c[:,free],None)),format='csc')
    solved=spsolve(a,np.r_[f[free],np.zeros(c.shape[0])])
    full=np.zeros(k.shape[0]); full[free]=solved[:len(free)]
    raw_tip=beam.trace(nb,1.)@full[model.dof_count:]
    assert abs(raw_tip[2])>1e-9
    expected=np.array((raw_tip[0],raw_tip[1],line.YAW_LENGTH*raw_tip[2]))
    actual=loaded.evaluate(2,3,nb,2,'Q4','P1','smooth')
    np.testing.assert_allclose(actual.beam_tip_displacement_metre,expected,
                               rtol=1e-7,atol=1e-9)


@pytest.mark.parametrize('kwargs',(
    dict(n_s=128,n_y=64,n_beam=512,n_mortar=64,depth=8),
    dict(n_s=2,n_y=3,n_beam=4,n_mortar=2,depth=12),
))
def test_unsupervised_large_loaded_cases_are_rejected_before_assembly(monkeypatch,kwargs):
    def forbidden(*args,**options):
        raise AssertionError('large case reached assembly')
    monkeypatch.setattr(shell,'panel',forbidden)
    with pytest.raises(ValueError,match='outside bounded'):
        loaded.evaluate(topology='Q4',law='P1',loading='smooth',**kwargs)
