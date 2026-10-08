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

def test_run_keeps_global_vector_with_beam_local_member_slots(monkeypatch,tmp_path):
    from scipy import sparse
    shell=c.TwofoldVector([900.,901.],[-1e-200,-2e-200]);beam=c.TwofoldVector([3.,4.],[1e-200,0.])
    answers=iter([SimpleNamespace(coordinates=v,report={'status':'DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED'}) for v in (shell,beam)])
    def solve(*a,**k):
        assert all(type(i) is int for i in k.get('fixed',()))
        return next(answers)
    monkeypatch.setattr(c,'solve_body_twofold',solve)
    owner=SimpleNamespace(_shell_count=2,_K=sparse.eye(4,format='csr'),_coordinate_scale=np.ones(4),_fixed=np.array([0],dtype=np.int64),_line_samples=[],_C=sparse.csr_matrix((0,4)),_beam_parts=[(None,np.array([0,1]),None)])
    monkeypatch.setattr(w.original,'continuum_fields',lambda saved:dict(body={n:dict(paired_work_J=1.) for n in ('shell','beam')}))
    monkeypatch.setattr(w.original,'shell_rigid_fields',lambda owner:np.zeros((2,6)))
    monkeypatch.setattr(w.original.matched,'reference_state',lambda owner:None)
    seen=[]
    def receiver(owner,q,diagnostics=None):
        slots=owner._shell_count+owner._beam_parts[0][1]
        assert q.high[slots].tolist()==[3.,4.]
        assert q.low[slots].tolist()==[1e-200,0.]
        assert len(q.high)==4
        seen.append(True)
        return dict(stored_energy_exact=F(0))
    monkeypatch.setattr(w,'material',receiver)
    result=w.run(None,(owner,np.zeros(4),np.zeros((2,6)),{}),tmp_path/'output')
    assert seen==[True] and result['inventory']==dict(shell_RHS=1,beam_RHS=1)




def test_actual_material_gather_feeds_beam_local_resultant_parts_to_cell():
    # Authentic one-member local layout:18 nodal coordinates, then6 cell
    # rotations+18 resultants in the first24-coordinate retained block.
    # Beam nodal inventory30 means the retained block starts at30, not18.
    ns=6
    beam_hi=np.arange(1.,79.)
    beam_lo=np.arange(1.,79.)*1e-200
    q=c.TwofoldVector(np.r_[np.arange(900.,906.),beam_hi],
                      np.r_[-np.arange(1.,7.)*1e-200,beam_lo])
    local_slots=np.r_[np.arange(18),np.arange(30,54)]
    origin=SimpleNamespace(stations=())
    calls=[]
    def cell_response(resultants,predecessor,*,check,include_energy):
        assert predecessor is origin and include_energy is True
        assert all(type(v) is float for v in resultants)
        check()
        calls.append(list(resultants))
        return dict(origin=origin,history=origin,incremental_dissipation=(0.,0.),
                    gradient=([0.]*18,[0.]*18),potential=([0.],[0.]),
                    stored_energy=(0.,0.),stations=[])
    cell=SimpleNamespace(virgin=lambda:origin,response=cell_response,identity='mock-native-cell')
    op=SimpleNamespace(cell=cell,guard=lambda:None,
                       reference=SimpleNamespace(coordinates=np.zeros((3,3)),nodal_triads=np.tile(np.eye(3),(3,1,1))),
                       evaluate=lambda *args,**kwargs:SimpleNamespace(hessian=np.zeros((42,42))))
    element=SimpleNamespace(operator=op,node_ids=(101,102,103))
    owner=SimpleNamespace(_shell_count=ns,_beam_parts=((element,local_slots,origin),))
    result=w.material(owner,q)
    # This executes material's real gather and zero/pHi/pLo native-call seam;
    # no stub material receiver can make the asserted resultant fields pass.
    assert calls==[[0.]*18,beam_hi[36:54].tolist(),beam_lo[36:54].tolist()]
    row=result['elements'][0]
    assert row['p_hi']==beam_hi[36:54].tolist()
    assert row['p_lo']==beam_lo[36:54].tolist()
    assert result['stored_energy_exact']==F(0)
