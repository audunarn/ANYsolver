"""Small operator-swap controls before source-frozen F03 diagnosis.

The mixed pairs are algebraic attribution experiments, not physical panels.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import io
import sys
import zipfile

import numpy as np
import pytest
from scipy import sparse
from scipy.sparse.linalg import splu

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_inventory as inventory
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling
import _b3_e4_f03_loaded_preflight as loaded
import b3_e4_f03_resource_preflight as runner
import adjudicate_b3_ge_e4_pl_g0_f03_stiffness_trace_v1 as adjudicate


@pytest.mark.parametrize('stiffness_topology',('Q4','CST-CB'))
@pytest.mark.parametrize('trace_topology',('Q4','CST-CB'))
def test_small_mixed_operators_recover_through_selected_trace(
        stiffness_topology,trace_topology):
    ns,ny,nb,nm=4,8,8,4
    stiff=shell.panel(ns,ny,stiffness_topology)
    trace=shell.panel(ns,ny,trace_topology)
    np.testing.assert_array_equal(stiff.nodes,trace.nodes)
    np.testing.assert_array_equal(stiff.supported,trace.supported)
    ks=shell.stiffness(stiff)
    kb=beam.assembled_stiffness(nb)
    cs,cb,_=line.coupling(trace,nb,nm,'P1')
    k=sparse.block_diag((ks,kb),format='csr')
    c=sparse.hstack((-cs,cb),format='csr')
    f=np.r_[np.zeros(stiff.dof_count),beam.assembled_load(nb,'smooth')]
    supported=np.r_[stiff.supported,stiff.dof_count+beam.root_dofs(nb)]
    free=np.setdiff1d(np.arange(k.shape[0]),supported)
    transform=scaling.build(k,c,f,free,stiff.dof_count,nb,nm,'P1')
    qfree,lam=transform.recover(splu(transform.matrix).solve(transform.rhs))
    result=loaded.recover_solved(trace,nb,nm,'P1',4,
                                 ks,kb,cs,cb,k,c,f,free,qfree,lam)
    assert result.free_force_scaled_max<1e-8
    assert result.weak_gap_scaled_max<1e-9
    assert max(abs(value) for value in result.global_balance_scaled)<1e-8
    if stiffness_topology==trace_topology:
        natural=loaded.evaluate(ns,ny,nb,nm,stiffness_topology,
                                'P1','smooth',depth=4)
        for key in ('shell_energy_joule','beam_energy_joule',
                    'integrated_gap_metre','beam_tip_displacement_metre',
                    'shell_station_displacements_metre','support_wrenches'):
            np.testing.assert_allclose(getattr(result,key),getattr(natural,key),
                                       rtol=2e-11,atol=1e-7)
    else:
        qs=np.zeros(stiff.dof_count); qs[free[free<stiff.dof_count]]=qfree[:np.sum(free<stiff.dof_count)]
        recovered=shell.pose(trace,.5)@qs
        np.testing.assert_allclose(result.shell_station_displacements_metre[1],
                                   (recovered[0],recovered[1],
                                    line.YAW_LENGTH*recovered[2]),rtol=1e-11,atol=1e-10)


def test_supervisor_rejects_unregistered_hybrid_modes_before_creating_root():
    mesh=inventory.Mesh(2,8,8,4)
    root=Path(__file__).resolve().parents[1]/'.hybrid-rejection-never-created'
    assert not root.exists()
    with pytest.raises(ValueError,match='requires solved-state payload'):
        runner._supervise(mesh,'Q4','P1',root,
                          solve=True,scaled=True,loaded_probe=True,
                          trace_topology='CST-CB')
    with pytest.raises(ValueError,match='requires loaded probe'):
        runner._supervise(mesh,'Q4','P1',root,
                          state_payload=True)
    assert not root.exists()


@pytest.mark.parametrize('stiffness,trace',(('Q4','Q4'),('Q4','CST-CB')))
def test_payload_phase_contract_requires_every_ordered_phase(stiffness,trace):
    phases=runner._state_phases(stiffness,trace)
    assert len(phases)==(12 if stiffness!=trace else 11)
    records=[{'phase':name} for name in phases]
    assert runner._valid_state_phases(records,stiffness,trace)
    for malformed in (records[:-2]+records[-1:],
                      records[:-1]+[records[-2],records[-2],records[-1]],
                      records[:3]+[records[4],records[3]]+records[5:]):
        assert not runner._valid_state_phases(malformed,stiffness,trace)


def test_payload_archive_validation_preserves_failure_as_invalid(monkeypatch):
    mesh=inventory.Mesh(2,8,8,4)
    q=np.zeros(2*(2*mesh.n_s+1)*(mesh.n_y+1)+beam.dof_count(mesh.n_beam))
    lam=np.arange(3*(mesh.n_mortar+1),dtype=np.float64)
    buffer=io.BytesIO()
    np.savez(buffer,physical_q=q,physical_lambda=lam)
    blob=buffer.getvalue()
    directory=Path(__file__).resolve().parents[1]/'.not-a-real-evidence-root'
    record=dict(phase='state_payload',path='solved_state.npz',
                sha256=hashlib.sha256(blob).hexdigest(),
                q_shape=list(q.shape),lambda_shape=list(lam.shape),
                q_dtype='float64',lambda_dtype='float64',
                q_sha256=hashlib.sha256(q.tobytes()).hexdigest(),
                lambda_sha256=hashlib.sha256(lam.tobytes()).hexdigest())
    original_load=np.load
    monkeypatch.setattr(Path,'is_file',lambda self: True)
    monkeypatch.setattr(Path,'read_bytes',lambda self: blob)
    monkeypatch.setattr(np,'load',lambda path,**kwargs: original_load(io.BytesIO(blob),**kwargs))
    assert runner._valid_state_payload(directory,[record],mesh,'P1')
    monkeypatch.setattr(np,'load',lambda path,**kwargs: (_ for _ in ()).throw(zipfile.BadZipFile()))
    assert not runner._valid_state_payload(directory,[record],mesh,'P1')
    monkeypatch.setattr(np,'load',lambda path,**kwargs: (_ for _ in ()).throw(EOFError()))
    assert not runner._valid_state_payload(directory,[record],mesh,'P1')
    assert not runner._valid_state_payload(directory,[record,record],mesh,'P1')


def test_adjudicator_port_quarters_split_at_mortar_hat_kinks():
    nm=8
    lam=np.zeros(3*(nm+1))
    lam[3*1+1]=100.
    lam[3*1+2]=20.
    quarters=np.asarray(adjudicate._port_quarters(lam,nm))
    h=1/nm
    np.testing.assert_allclose(quarters[0],
                               (0.,100*h,100*h*h+20*h*line.YAW_LENGTH),
                               rtol=1e-13,atol=1e-13)
    np.testing.assert_allclose(quarters[1:],0.,atol=1e-13)
