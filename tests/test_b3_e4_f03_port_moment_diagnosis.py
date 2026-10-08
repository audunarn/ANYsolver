"""Independent moment/virtual-work identities for the classical F03 port.

These are bounded operator diagnostics, not loaded convergence evidence or a
native B3-GE/E4-PL torque-transfer qualification.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell


def _rigid_shell(model,tx,ty,omega):
    q=np.empty(model.dof_count)
    q[::2]=tx-omega*model.nodes[:,1]
    q[1::2]=ty+omega*model.nodes[:,0]
    return q


def _rigid_beam(n,tx,ty,omega):
    q=np.zeros(beam.dof_count(n))
    u=2*n+1; v=2*(n+1)
    q[:u]=tx
    q[u:u+v:2]=ty+omega*np.arange(n+1)/n
    q[u+1:u+v:2]=omega
    q[u+v:]=omega
    return q


@pytest.mark.parametrize('topology',('Q4','CST','CST-CB'))
@pytest.mark.parametrize('index',((0,1),(2,1),(4,2),(0,2),(2,2),(4,1)))
def test_prescribed_p1_port_force_and_yaw_resultants(topology,index):
    # index=(P1 hat number, channel); 1 means transverse force, 2 yaw.
    hat,channel=index
    model=shell.panel(3,6,topology)
    nb=6; nm=4; force=1500.
    cs,cb,_=line.coupling(model,nb,nm,'P1',order=4)
    cs8,cb8,_=line.coupling(model,nb,nm,'P1',order=8)
    lam=np.zeros(3*(nm+1)); lam[3*hat+channel]=force
    shell_dual=np.asarray(-cs.T@lam).ravel()
    beam_dual=np.asarray(cb.T@lam).ravel()
    np.testing.assert_allclose(shell_dual,-cs8.T@lam,rtol=1e-12,atol=1e-9)
    np.testing.assert_allclose(beam_dual,cb8.T@lam,rtol=1e-12,atol=1e-9)

    # Independent analytical P1 hat integrals on [0,1].
    h=1/nm
    measure=h/2 if hat in (0,nm) else h
    first_moment=(h*h/6 if hat==0 else
                  h/2-h*h/6 if hat==nm else hat*h*h)
    expected_fy=-force*measure if channel==1 else 0.
    expected_moment=(-force*first_moment if channel==1 else
                     -force*line.YAW_LENGTH*measure)
    fx=shell_dual[::2]; fy=shell_dual[1::2]
    actual_fy=float(np.sum(fy))
    actual_moment=float(model.nodes[:,0]@fy-model.nodes[:,1]@fx)
    np.testing.assert_allclose((np.sum(fx),actual_fy,actual_moment),
                               (0.,expected_fy,expected_moment),
                               rtol=1e-12,atol=1e-9)
    for tx,ty,omega in ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.),
                        (.17,-.31,.43)):
        qs=_rigid_shell(model,tx,ty,omega)
        qb=_rigid_beam(nb,tx,ty,omega)
        expected=expected_fy*ty+expected_moment*omega
        np.testing.assert_allclose(shell_dual@qs,expected,rtol=1e-12,atol=1e-9)
        np.testing.assert_allclose(beam_dual@qb,-expected,rtol=1e-12,atol=1e-9)

    rng=np.random.default_rng(341)
    qs=rng.normal(size=model.dof_count)*1e-5
    qb=rng.normal(size=beam.dof_count(nb))*1e-5
    direction_s=rng.normal(size=model.dof_count)*1e-5
    direction_b=rng.normal(size=beam.dof_count(nb))*1e-5
    step=.01
    def work(a,b):
        return float(lam@(cb@b-cs@a))
    derivative=(work(qs+step*direction_s,qb+step*direction_b)-
                work(qs-step*direction_s,qb-step*direction_b))/(2*step)
    np.testing.assert_allclose(derivative,
                               shell_dual@direction_s+beam_dual@direction_b,
                               rtol=1e-10,atol=1e-12)


@pytest.mark.parametrize('topology',('Q4','CST-CB'))
@pytest.mark.parametrize('ny',(16,32,64))
def test_yaw_offset_force_couple_is_independent_of_panel_y_mesh(topology,ny):
    model=shell.panel(2,ny,topology)
    s=.37
    wrench=np.array((0.,0.,120.))
    nodal=np.asarray(shell.pose(model,s).T@wrench).ravel()
    force=np.array((np.sum(nodal[::2]),np.sum(nodal[1::2])))
    moment=float((model.nodes[:,0]-s)@nodal[1::2]-
                 model.nodes[:,1]@nodal[::2])
    np.testing.assert_allclose(force,0.,atol=1e-11)
    np.testing.assert_allclose(moment,wrench[2],rtol=1e-12,atol=1e-10)
