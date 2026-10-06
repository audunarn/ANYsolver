from fractions import Fraction as F
from types import SimpleNamespace
import numpy as np
import pytest
from scripts import r8_bl5_body_port_twofold_workflow as w
from scripts import r8_bl5_body_port_twofold as c

def test_returned_field_halves_are_not_coordinate_halves():
    assert w.paired(([.5,0.],[1e-200,1e-200]))==(F(.5)+F(1e-200),F(1e-200))

def test_wrench_retains_low_parts_and_rejects_unbalanced_work():
    r=np.eye(2);load=np.array([.5,1e-200]);support=(-F(.5),-F(1e-200))
    assert w.check_wrench(r,load,support)==(F(0),F(0))
    with pytest.raises(ValueError):w.check_wrench(r,[1.,0.],(F(0),F(0)))

def test_reference_action_preserves_two_pose_parts():
    q=c.TwofoldVector([.5,.5],[1e-200,0.])
    assert w.action([[1.,-1.]],q)==(F(1e-200),)

def test_boundary_and_changed_origin_refused():
    response=dict(origin='origin',history='origin',incremental_dissipation=(0.,0.),stations=[dict(fibres=[SimpleNamespace(branch='YIELD_BOUNDARY',plastic_increment=(0.,0.))])])
    with pytest.raises(ValueError):w.require_elastic(response,'origin')
    response['stations']=[];response['history']='changed'
    with pytest.raises(ValueError):w.require_elastic(response,'origin')

def test_run_material_receives_global_owner_slots(monkeypatch,tmp_path):
    from scipy import sparse
    shell=c.TwofoldVector([0.,0.],[0.,0.]);beam=c.TwofoldVector([3.,4.],[1e-200,0.])
    answers=iter([SimpleNamespace(coordinates=v,report={'status':'DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED'}) for v in (shell,beam)])
    def solve(*a,**k):
        assert all(type(i) is int for i in k.get('fixed',()))
        return next(answers)
    monkeypatch.setattr(c,'solve_body_twofold',solve)
    owner=SimpleNamespace(_shell_count=2,_K=sparse.eye(4,format='csr'),_coordinate_scale=np.ones(4),_fixed=np.array([0],dtype=np.int64),_line_samples=[],_C=sparse.csr_matrix((0,4)),_beam_parts=[(None,np.array([2,3]),None)])
    monkeypatch.setattr(w.original,'continuum_fields',lambda saved:dict(body={n:dict(paired_work_J=1.) for n in ('shell','beam')}))
    monkeypatch.setattr(w.original,'shell_rigid_fields',lambda owner:np.zeros((2,6)))
    monkeypatch.setattr(w.original.matched,'reference_state',lambda owner:None)
    seen=[]
    def receiver(owner,q,diagnostics=None):
        slots=owner._beam_parts[0][1]
        assert q.high[slots].tolist()==[3.,4.]
        assert q.low[slots].tolist()==[1e-200,0.]
        assert len(q.high)==4
        seen.append(True)
        return dict(stored_energy_exact=F(0))
    monkeypatch.setattr(w,'material',receiver)
    result=w.run(None,(owner,np.zeros(4),np.zeros((2,6)),{}),tmp_path/'output')
    assert seen==[True] and result['inventory']==dict(shell_RHS=1,beam_RHS=1)


