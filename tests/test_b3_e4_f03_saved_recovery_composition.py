"""Bounded saved-component composition over one manufactured state."""
from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_action_enclosure as enclosure
from scripts import _b3_e4_f03_local_grid as grid
from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_local_recovery as rec
from scripts import _b3_e4_f03_local_support_recovery as support
from scripts import _b3_e4_f03_saved_interface_checks as interface
from scripts import _b3_e4_f03_saved_norm_checks as norm
from scripts import _b3_e4_f03_saved_recovery_composition as composition
from scripts import _b3_e4_f03_saved_work_checks as work
from scripts import _b3_e4_f03_sparse_certificate as sparse_common
from scripts import _b3_e4_f03_sparse_equilibrium_checks as equilibrium
from scripts import _b3_e4_f03_sparse_state_binding as binding
from scripts import _b3_e4_f03_spatial_contract as c


Z=F(0)
RB=rec.RecoveryBudget(assembly.AssemblyBudget(512,1,128*1024**2,8_000_000),
    1024,128,8_000_000,256*1024**2,1_000_000_000)
AB=enclosure.ActionBudget(64,128,65536,200_000_000,2_000_000,256*1024**2)
IB=interface.InterfaceBudget(RB,AB,128,256,500_000_000,50_000_000_000,
                             1024*1024**2)
SB=support.SupportBudget(RB,1024,128,1_000_000_000,80_000_000,512*1024**2)
WB=work.WorkBudget(SB,AB,4096,30000,10**12,10**14,2*1024**3)
NB=norm.NormBudget(128,32_000_000,1_000_000_000,128*1024**2)
SP=sparse_common.SparseBudget(64,4096,4,16*1024**2)
BB=binding.BindingBudget(SP,8192,16384,16_000_000,64*1024**2)
EB=equilibrium.EquilibriumBudget(BB,8192,16384,32_000_000,128*1024**2)
CB=composition.CompositionBudget(EB,IB,WB,NB,256*1024**2,40000,
    2*10**12,2*10**14,4*1024**3)


def _numerical_virtual(value,rows):
    nodes,weights=np.polynomial.legendre.leggauss(48)
    tau=(nodes+1)/2;weights=weights/2;terms=np.zeros(4)
    for a,b,row,stress,density in zip(value.cuts,value.cuts[1:],rows,
                                      value.resultants,value.interface.coefficients):
        h=float(b-a);s=float(a)+h*tau
        test=np.array([np.polynomial.polynomial.polyval(tau,np.array(p,float)) for p in row])
        dt=np.array([np.polynomial.polynomial.polyval(tau,
            np.arange(1,6)*np.array(p[1:],float))/h for p in row])
        nqm=np.array([np.polynomial.polynomial.polyval(tau,np.array(p,float)) for p in stress])
        mu=np.array([np.polynomial.polynomial.polyval(tau,np.array(p,float))+
                     float(amp)*np.cos(c.OMEGA*s) for p,amp in zip(density,value.interface.cosine)])
        terms[0]+=h*np.sum(weights*np.sum(mu*test,axis=0))
        terms[1]+=h*np.sum(weights*(nqm[0]*dt[0]+nqm[1]*(dt[1]-test[2])+nqm[2]*dt[2]))
        terms[2]+=h*np.sum(weights*c.F0*(1+.25*np.cos(c.OMEGA*s))*test[1])
    endpoint0=np.array([float(p[0]) for p in rows[0]])
    endpoint1=np.array([float(sum(p)) for p in rows[-1]])
    terms[0]+=np.array(value.interface.atoms[0],float)@endpoint0
    terms[0]+=np.array(value.interface.atoms[1],float)@endpoint1
    terms[3]=np.array(value.eta,float)@endpoint0
    return terms


def _saved_interface(value):
    density=np.asarray(value.interface.coefficients,dtype=np.float64)
    cosine=np.asarray(value.interface.cosine,dtype=np.float64)
    atoms=np.asarray(value.interface.atoms,dtype=np.float64)
    total=[];line=[]
    for left,right in interface.BANDS:
        actions=rec.band(value,left,right);atom=interface._atom_action(value.interface,left,right)
        total.append([float(action.decimal_value()) for action in actions])
        line.append([float((action-a).decimal_value()) for action,a in zip(actions,atom)])
    total=np.asarray(total);line=np.asarray(line)
    return interface.SavedInterface(value.cuts,density,cosine,atoms,total,
                                    total.copy(),total.copy(),line)


def _saved_work(g,value):
    result=support.support_recovery(g,value,SB)
    terms=np.array([_numerical_virtual(value,rows)
                    for _,rows in work.virtual_inventory(value.cuts,g.p)]).reshape(3,-1,4)
    defects=terms[:,:,0]+terms[:,:,1]-terms[:,:,2]+terms[:,:,3]
    values=lambda actions:np.asarray([float(a.decimal_value()) for a in actions],dtype=np.float64)
    return work.SavedWork(g.p,value.cuts,result.lift_family,
        np.array([support.lift_pose(value.cuts,side,ch,g.p)
                  for side in ('left','right') for ch in range(3)],float),
        np.array(result.shell_work,float),values(result.interface_work),
        values(result.route1),values(result.route2),
        values((result.first_free_route1_residual,result.first_free_route2_residual)),
        values((result.shift_route1_delta,result.shift_route2_delta)),terms,defects)


def _case(scale=.25):
    g=grid.compile_grid((F(-1,2),F(1,2),F(3,2)),(F(-1,2),Z,F(1,2)),1)
    n=g.free_dofs;shell=sparse.diags([1e7]*n,format='csr');beam=shell.copy()
    root=sparse.csr_matrix(np.eye(3,n));stiffness=shell+beam
    d=np.sqrt(c.E0/stiffness.diagonal());r=np.array((1/c.U0,1/c.U0,.46/c.U0))
    kbar=((stiffness.toarray()*d[:,None])*d[None,:])/c.E0
    cbar=(root.toarray()*r[:,None])*d[None,:]
    h=sparse.csr_matrix(np.block([[kbar,cbar.T],[cbar,np.zeros((3,3))]]))
    z=np.zeros(n+3);z[3]=scale;q=d*z[:n];eta=c.E0*r*z[n:]
    f=stiffness@q;b=np.r_[d*f/c.E0,np.zeros(3)];h_z=h@z
    q_exact=tuple(F.from_float(float(v)) for v in q)
    eta_exact=tuple(F.from_float(float(v)) for v in eta)
    recovered=rec.recover(g,q_exact,eta_exact,RB)
    si=_saved_interface(recovered);sw=_saved_work(g,recovered)
    saved_functional=interface._saved_functional(si)
    sn=norm._pack(tuple(rec.functional.norm_observation_at_order(saved_functional,order)
                        for order in (48,64)))
    args=(g,shell,beam,shell.copy(),beam.copy(),root,f,d,h,b,q,eta,z,h_z,si,sw,sn)
    return args


def _verify(args,**kwargs):
    return composition.verify_composition(*args,budget=kwargs.pop('budget',CB),**kwargs)


def _replace_interface(result,**updates):
    replacement=object.__new__(interface.InterfaceResult)
    for name in result.__dataclass_fields__:
        object.__setattr__(replacement,name,updates.get(name,getattr(result,name)))
    return replacement


def _replace_grid(result,**updates):
    replacement=object.__new__(grid.CompiledGrid)
    for name in result.__dataclass_fields__:
        object.__setattr__(replacement,name,updates.get(name,getattr(result,name)))
    return replacement


def test_complete_composition_passes_and_reports_fixed_work_counts(monkeypatch):
    args=_case();recoveries=observations=0
    original_recover=rec.recover;original_observe=rec.functional.norm_observation_at_order
    def counted_recover(*values,**options):
        nonlocal recoveries;recoveries+=1;return original_recover(*values,**options)
    def counted_observe(*values,**options):
        nonlocal observations;observations+=1;return original_observe(*values,**options)
    monkeypatch.setattr(rec,'recover',counted_recover)
    monkeypatch.setattr(rec.functional,'norm_observation_at_order',counted_observe)
    result=_verify(args)
    assert result['status']=='COMPONENT_CHECKS_PASSED'
    assert all(result['cross_bindings'].values())
    assert set(result['component_statuses'].values())=={'NUMERICAL_MECHANICAL_CHECKS_PASSED','PASSED'}
    assert recoveries==result['diagnostics']['recovery_recomputations']==3
    assert observations==result['diagnostics']['norm_evaluations']==2
    assert result['diagnostics']['equilibrium_solves']==0
    assert result['diagnostics']['factorizations']==0
    assert result['diagnostics']['actual_comparisons']<=result['diagnostics']['comparisons']
    assert result['canonical_saved_sha256s']['compiled_grid']==composition._hash_grid(args[0])
    with pytest.raises(TypeError):result['cross_bindings']['recovery_q']=False


def test_compiled_grid_identity_binds_execution_and_incidence_maps():
    value=_case()[0];baseline=composition._hash_grid(value)
    full_to_free=value.full_to_free.copy();full_to_free[0]+=1
    root=value.root_incidence.copy();root[0]+=1
    trace=list(value.trace_incidence);changed=trace[0].copy();changed[0]+=1;trace[0]=changed
    for candidate in (_replace_grid(value,full_to_free=full_to_free),
                      _replace_grid(value,root_incidence=root),
                      _replace_grid(value,trace_incidence=tuple(trace))):
        assert composition._hash_grid(candidate)!=baseline


def test_aggregate_preflight_stops_every_component(monkeypatch):
    args=_case()
    def forbidden(*values,**options):pytest.fail('component started after failed composition preflight')
    for module,name in ((equilibrium,'verify_equilibrium'),(interface,'verify_interface'),
                        (work,'verify_work'),(norm,'verify_norm')):
        monkeypatch.setattr(module,name,forbidden)
    with pytest.raises(ValueError,match='owned/workspace envelope'):
        _verify(args,budget=replace(CB,max_owned_bytes=1))


def test_every_nested_resource_preflight_stops_all_components(monkeypatch):
    args=_case()
    def forbidden(*values,**options):pytest.fail('component started after nested preflight failure')
    for module,name in ((equilibrium,'verify_equilibrium'),(interface,'verify_interface'),
                        (work,'verify_work'),(norm,'verify_norm')):
        monkeypatch.setattr(module,name,forbidden)
    budgets=(
        replace(CB,equilibrium_budget=replace(EB,max_six_block_nnz=1)),
        replace(CB,interface_budget=replace(IB,max_comparisons=1)),
        replace(CB,work_budget=replace(WB,max_comparisons=1)),
        replace(CB,norm_budget=replace(NB,max_operations=1)),
        replace(CB,work_budget=replace(WB,
            support_budget=replace(SB,max_operations=1))),
    )
    for budget in budgets:
        with pytest.raises(ValueError,match='saved composition'):_verify(args,budget=budget)


def test_partition_mismatch_is_rejected_before_components(monkeypatch):
    args=list(_case());saved=args[15];ni=len(saved.cuts)-1
    args[15]=replace(saved,cuts=tuple(F(i*i,ni*ni) for i in range(ni+1)))
    def forbidden(*values,**options):pytest.fail('component started after partition mismatch')
    for module,name in ((equilibrium,'verify_equilibrium'),(interface,'verify_interface'),
                        (work,'verify_work'),(norm,'verify_norm')):
        monkeypatch.setattr(module,name,forbidden)
    with pytest.raises(ValueError,match='degree or partition mismatch'):_verify(tuple(args))


def test_retained_workspace_cap_is_checked_before_components(monkeypatch):
    args=_case();baseline=_verify(args)
    def forbidden(*values,**options):pytest.fail('component started after retained workspace failure')
    for module,name in ((equilibrium,'verify_equilibrium'),(interface,'verify_interface'),
                        (work,'verify_work'),(norm,'verify_norm')):
        monkeypatch.setattr(module,name,forbidden)
    with pytest.raises(ValueError,match='owned/workspace envelope'):
        _verify(args,budget=replace(CB,
            max_work_bytes=baseline['diagnostics']['workspace_envelope_bytes']-1))


def test_caller_mutation_during_first_component_cannot_change_later_bindings(monkeypatch):
    args=list(_case());external_shell=args[1];external_q=args[10];external_eta=args[11]
    original=equilibrium.verify_equilibrium
    def hostile(*values,**options):
        external_shell.data[:]=123.;external_q[:]=99.;external_eta[:]=-77.
        return original(*values,**options)
    monkeypatch.setattr(equilibrium,'verify_equilibrium',hostile)
    result=_verify(tuple(args))
    assert result['status']=='COMPONENT_CHECKS_PASSED'
    assert all(result['cross_bindings'].values())
    assert (external_shell.data==123.).all()
    assert (external_q==99.).all()
    assert (external_eta==-77.).all()


def test_norm_receives_exact_interface_owned_functional(monkeypatch):
    args=_case();seen={};original_interface=interface.verify_interface;original_norm=norm.verify_norm
    def capture_interface(*values,**options):
        result=original_interface(*values,**options);seen['functional']=result.saved_functional;return result
    def capture_norm(value,*values,**options):
        assert value is seen['functional'];return original_norm(value,*values,**options)
    monkeypatch.setattr(interface,'verify_interface',capture_interface)
    monkeypatch.setattr(norm,'verify_norm',capture_norm)
    assert _verify(args)['status']=='COMPONENT_CHECKS_PASSED'


def test_consistent_q_change_rebinds_every_state_identity():
    first=_verify(_case(.25));second=_verify(_case(.5))
    assert first['status']==second['status']=='COMPONENT_CHECKS_PASSED'
    assert first['canonical_snapshot_sha256']!=second['canonical_snapshot_sha256']
    assert (first['components']['numerical']['input_sha256']['q']!=
            second['components']['numerical']['input_sha256']['q'])
    assert (first['components']['interface'].input_sha256['grid_q_eta']!=
            second['components']['interface'].input_sha256['grid_q_eta'])
    assert (first['components']['work']['input_sha256']!=
            second['components']['work']['input_sha256'])
    assert all(first['cross_bindings'].values()) and all(second['cross_bindings'].values())


def test_passing_component_status_cannot_waive_stale_identity(monkeypatch):
    args=_case();original=equilibrium.verify_equilibrium
    def stale(*values,**options):
        result=original(*values,**options);identities=dict(result['input_sha256'])
        identities['q']='0'*64
        return {**result,'status':'NUMERICAL_MECHANICAL_CHECKS_PASSED',
                'input_sha256':identities}
    monkeypatch.setattr(equilibrium,'verify_equilibrium',stale)
    result=_verify(args)
    assert result['status']=='COMPOSITION_FAILED'
    assert not result['cross_bindings']['numerical_q']


@pytest.mark.parametrize('component',('interface','work','norm'))
def test_passing_saved_component_cannot_waive_stale_identity(monkeypatch,component):
    args=_case()
    if component=='interface':
        original=interface.verify_interface
        def stale(*values,**options):
            result=original(*values,**options);identities=dict(result.input_sha256)
            identities['saved_interface']='0'*64
            return _replace_interface(result,input_sha256=identities,status='PASSED')
        monkeypatch.setattr(interface,'verify_interface',stale)
        failed_key='interface_saved'
    elif component=='work':
        original=work.verify_work
        def stale(*values,**options):
            result=original(*values,**options)
            return {**result,'input_sha256':'0'*64,'status':'PASSED'}
        monkeypatch.setattr(work,'verify_work',stale)
        failed_key='work_state_saved'
    else:
        original=norm.verify_norm
        def stale(*values,**options):
            result=dict(original(*values,**options))
            result.update(input_sha256='0'*64,status='PASSED')
            return result
        monkeypatch.setattr(norm,'verify_norm',stale)
        failed_key='norm_functional_saved'
    result=_verify(args)
    assert result['status']=='COMPOSITION_FAILED'
    assert not result['cross_bindings'][failed_key]


def test_passing_interface_cannot_substitute_an_unbound_functional(monkeypatch):
    args=_case();original=interface.verify_interface
    def stale(*values,**options):
        result=original(*values,**options);value=result.saved_functional
        altered=rec.functional.Functional(value.cuts,value.coefficients,
            (value.cosine[0]+1,*value.cosine[1:]),value.atoms)
        return _replace_interface(result,saved_functional=altered,status='PASSED')
    monkeypatch.setattr(interface,'verify_interface',stale)
    result=_verify(args)
    assert result['status']=='COMPOSITION_FAILED'
    assert not result['cross_bindings']['functional_chain']


def test_component_reported_work_counts_are_enforced(monkeypatch):
    args=_case();original=work.verify_work
    def misreported(*values,**options):
        result=original(*values,**options);diagnostics=dict(result['diagnostics'])
        diagnostics['state_recoveries']=1
        return {**result,'diagnostics':diagnostics}
    monkeypatch.setattr(work,'verify_work',misreported)
    with pytest.raises(ArithmeticError,match='work count'):_verify(args)


def test_corrupted_saved_norm_dominates_as_composition_failure():
    args=list(_case());saved=args[16];channels=saved.channels.copy();channels[0,0]+=1.
    args[16]=replace(saved,channels=channels)
    result=_verify(tuple(args))
    assert result['component_statuses']['norm']=='FAILED'
    assert result['status']=='COMPOSITION_FAILED'


def test_numerical_hold_precedes_unresolved_component_hold(monkeypatch):
    args=_case();original_equilibrium=equilibrium.verify_equilibrium;original_norm=norm.verify_norm
    def held_equilibrium(*values,**options):
        result=original_equilibrium(*values,**options);return {**result,'status':'HOLD',
            'failures':('injected numerical hold',)}
    def held_norm(*values,**options):
        result=dict(original_norm(*values,**options));result['status']='HOLD_UNRESOLVED';return result
    monkeypatch.setattr(equilibrium,'verify_equilibrium',held_equilibrium)
    monkeypatch.setattr(norm,'verify_norm',held_norm)
    result=_verify(args)
    assert result['status']=='HOLD_NUMERICAL'


def test_unresolved_norm_remains_component_hold(monkeypatch):
    args=_case();original=norm.verify_norm
    def held(*values,**options):
        result=dict(original(*values,**options));result['status']='HOLD_UNRESOLVED';return result
    monkeypatch.setattr(norm,'verify_norm',held)
    result=_verify(args)
    assert result['status']=='HOLD_UNRESOLVED'


def test_programming_error_propagates(monkeypatch):
    args=_case()
    def failure(*values,**options):raise RuntimeError('programming failure')
    monkeypatch.setattr(norm,'verify_norm',failure)
    with pytest.raises(RuntimeError,match='programming failure'):_verify(args)
