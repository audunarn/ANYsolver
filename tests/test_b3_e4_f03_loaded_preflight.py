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
    assert abs(result.interface_work_joule)/loaded.scaling.E0<1e-8
    assert abs(result.shell_interface_work_joule+
               result.beam_interface_work_joule-
               result.interface_work_joule)/loaded.scaling.E0<1e-10
    assert result.free_force_scaled_max<1e-8
    assert result.weak_gap_scaled_max<1e-9
    assert result.shell_energy_joule>=0
    assert result.beam_energy_joule>=0
    assert result.integrated_gap_metre>=0
    assert result.motion_rms_metre>=0
    np.testing.assert_allclose(result.fixed_scale_gap,
                               result.integrated_gap_metre/loaded.scaling.U0,
                               rtol=1e-10,atol=1e-12)
    np.testing.assert_allclose(result.motion_scale_gap,
                               result.integrated_gap_metre/
                               max(result.motion_rms_metre,.1*loaded.scaling.U0),
                               rtol=1e-10,atol=1e-12)
    expected_moment=(loaded.scaling.F0/2 if loading=='smooth' else
                     -loaded.scaling.F0/(2*np.pi))
    expected_force=(loaded.scaling.F0 if loading=='smooth' else 0.)
    np.testing.assert_allclose(result.applied_resultant,
                               (0.,expected_force,expected_moment),
                               rtol=0,atol=2e-9*loaded.scaling.F0)
    assert np.max(np.abs(result.global_balance_scaled))<1e-8
    np.testing.assert_allclose(
        np.sum(np.asarray(result.support_wrenches),axis=0),
        -np.asarray(result.applied_resultant),rtol=0,
        atol=1e-8*loaded.scaling.F0)
    assert len(result.shell_station_displacements_metre)==3
    assert all(len(pose)==3 and np.all(np.isfinite(pose))
               for pose in result.shell_station_displacements_metre)
    bounds=result.finite_field_component_bounds_metre
    assert len(bounds)==3
    assert all(0<=lower<=upper for lower,upper in bounds)
    # Length is 1 m. The componentwise continuous-field upper enclosures
    # bound the L2 gap; sampled stations or weak rows cannot establish this.
    assert result.integrated_gap_metre<=np.linalg.norm([b[1] for b in bounds])+1e-12
    assert all(np.isfinite(result.beam_tip_displacement_metre))
    scalar_outputs=(result.shell_energy_joule,result.beam_energy_joule,
                    result.external_work_joule,result.interface_work_joule,
                    result.shell_interface_work_joule,
                    result.beam_interface_work_joule,
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
    recovered=loaded.recover_solved(
        model,nb,2,'P1',8,ks,kb,cs,cb,k,c,f,free,
        solved[:len(free)],solved[len(free):])
    for field in ('shell_energy_joule','beam_energy_joule',
                  'integrated_gap_metre','fixed_scale_gap','motion_scale_gap',
                  'free_force_scaled_max','weak_gap_scaled_max'):
        np.testing.assert_allclose(getattr(recovered,field),getattr(actual,field),
                                   rtol=1e-6,atol=1e-8)
    np.testing.assert_allclose(recovered.support_wrenches,actual.support_wrenches,
                               rtol=1e-7,atol=1e-5)
    residual=k@full+c.T@solved[len(free):]-f
    nx=2*model.n_s
    for edge,wrench in ((0,actual.support_wrenches[0]),
                        (nx,actual.support_wrenches[1])):
        nodes=np.array([j*(nx+1)+edge for j in range(model.n_y+1)])
        forces=np.column_stack((residual[2*nodes],residual[2*nodes+1]))
        moment=np.sum(model.nodes[nodes,0]*forces[:,1]-
                      model.nodes[nodes,1]*forces[:,0])
        np.testing.assert_allclose(wrench,
                                   (np.sum(forces[:,0]),np.sum(forces[:,1]),moment),
                                   rtol=1e-7,atol=1e-5)
    root=model.dof_count+beam.root_dofs(nb)
    np.testing.assert_allclose(actual.support_wrenches[2],residual[root],
                               rtol=1e-7,atol=1e-5)


@pytest.mark.parametrize('topology',('Q4','CST'))
def test_motion_quadrature_order_parity_for_continuous_fe_fields(topology):
    model=shell.panel(2,3,topology)
    rng=np.random.default_rng(73)
    qs=rng.standard_normal(model.dof_count)*1e-5
    qb=rng.standard_normal(beam.dof_count(4))*1e-5
    assert abs((shell.pose(model,.43)@qs)[2])>1e-8
    a=loaded._motion_integrals(model,4,2,qs,qb,order=4)
    b=loaded._motion_integrals(model,4,2,qs,qb,order=6)
    np.testing.assert_allclose(a,b,rtol=1e-12,atol=1e-18)


@pytest.mark.parametrize('topology',('Q4','CST'))
def test_constant_displaced_traces_give_hand_gap_and_motion(topology):
    model=shell.panel(2,3,topology); nb=4
    shell_u=2e-5; beam_u=5e-5
    qs=np.zeros(model.dof_count); qs[::2]=shell_u
    qb=np.zeros(beam.dof_count(nb)); qb[:2*nb+1]=beam_u
    gap_sq,motion_sq=loaded._motion_integrals(model,nb,2,qs,qb)
    np.testing.assert_allclose(np.sqrt(gap_sq),abs(beam_u-shell_u),
                               rtol=1e-12,atol=1e-16)
    np.testing.assert_allclose(np.sqrt(motion_sq),
                               np.sqrt((beam_u**2+shell_u**2)/2),
                               rtol=1e-12,atol=1e-16)


def test_nonfinite_derived_observable_cannot_enter_evidence(monkeypatch):
    monkeypatch.setattr(line,'integrated_gap',lambda *args,**kwargs: float('nan'))
    with pytest.raises(ValueError,match='nonfinite loaded classical observables'):
        loaded.evaluate(2,3,4,2,'Q4','P1','smooth')


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
