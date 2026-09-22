"""Synthetic saved interface/band admission only; no scientific solve."""
from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest

from scripts import _b3_e4_f03_action_enclosure as enclosure
from scripts import _b3_e4_f03_saved_interface_checks as check
from scripts import _b3_e4_f03_local_grid as grid
from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_local_recovery as rec


Z=F(0)
RB=rec.RecoveryBudget(assembly.AssemblyBudget(512,1,128*1024**2,8_000_000),
    1024,128,8_000_000,256*1024**2,1_000_000_000)
AB=enclosure.ActionBudget(64,128,65536,200_000_000,2_000_000,256*1024**2)
BUDGET=check.InterfaceBudget(RB,AB,128,256,500_000_000,50_000_000_000,
                             1024*1024**2)
ETA=(F(7),F(-11),F(13))


def _model():
    return grid.compile_grid((F(-1,2),F(1,2),F(3,2)),
                             (F(-1,2),Z,F(1,2)),1)


def _source():
    g=_model();q=(F(1,10**6),)+(Z,)*(g.free_dofs-1)
    value=rec.recover(g,q,ETA,RB)
    density=np.asarray(value.interface.coefficients,dtype=np.float64)
    cosine=np.asarray(value.interface.cosine,dtype=np.float64)
    atoms=np.asarray(value.interface.atoms,dtype=np.float64)
    total=[];line=[]
    for left,right in check.BANDS:
        actions=rec.band(value,left,right)
        atom=check._atom_action(value.interface,left,right)
        total.append([float(action.decimal_value()) for action in actions])
        line.append([float((action-a).decimal_value()) for action,a in zip(actions,atom)])
    total=np.asarray(total);line=np.asarray(line)
    saved=check.SavedInterface(value.cuts,density,cosine,atoms,
                               total,total.copy(),total.copy(),line)
    return g,q,value,saved


def _replace(saved,**changes):
    values={name:getattr(saved,name) for name in ('cuts','density','cosine','atoms',
        'band_analytic','band48','band64','line_band_analytic')}
    values.update(changes)
    return check.SavedInterface(**values)


def test_complete_saved_interface_and_all_192_band_comparisons_pass():
    g,q,value,saved=_source()
    result=check.verify_interface(g,q,ETA,saved,budget=BUDGET)
    assert result.status=='PASSED' and not result.failures
    assert result.recovery.interface==value.interface
    assert result.diagnostics['comparisons']==192
    assert result.metrics['failed_comparisons']==0
    assert result.metrics['unresolved_comparisons']==0
    assert result.metrics['root_partition_scaled']<=F.from_float(1e-11)
    assert result.metrics['tip_partition_scaled']<=F.from_float(1e-11)
    assert result.diagnostics['endpoint_atoms_per_band']=='once'
    assert result.diagnostics['origin_moment']=='s*Fy+intrinsic'
    assert result.diagnostics['live_action_estimate_bytes']>0
    with pytest.raises(TypeError):result.metrics['density_scaled']=Z
    with pytest.raises(ValueError):saved.density[0,0,0]=999.


@pytest.mark.parametrize('field,index,delta',(
    ('density',(0,0,0),1e-3),('cosine',(1,),1.),('atoms',(0,2),1.),
    ('band_analytic',(0,0),1.),('band48',(2,1),1.),
    ('band64',(4,2),1.),('line_band_analytic',(7,2),1.)))
def test_corrupted_interface_or_each_saved_band_inventory_fails(field,index,delta):
    g,q,_,saved=_source();array=getattr(saved,field).copy();array[index]+=delta
    result=check.verify_interface(g,q,ETA,_replace(saved,**{field:array}),budget=BUDGET)
    assert result.status=='FAILED'
    if field in ('density','cosine','atoms'):
        assert result.metrics[field+'_scaled']>F.from_float(1e-10)
    else:assert result.metrics['failed_comparisons']>0


def test_endpoint_atoms_and_origin_wrench_are_included_once_with_exact_sides():
    _,_,value,_=_source();f=value.interface
    first=check._atom_action(f,*check.BANDS[0])
    middle=check._atom_action(f,*check.BANDS[1])
    last=check._atom_action(f,*check.BANDS[3])
    assert tuple(a.rational for a in first)==(
        f.atoms[0][0],f.atoms[0][1],f.atoms[0][2])
    assert tuple(a.rational for a in middle)==(Z,Z,Z)
    assert tuple(a.rational for a in last)==(
        f.atoms[1][0],f.atoms[1][1],f.atoms[1][1]+f.atoms[1][2])
    total=check._band(f,Z,F(1))
    line=tuple(a-b for a,b in zip(total,check._atom_action(f,Z,F(1))))
    assert total==rec.band(value,Z,F(1))
    assert all(action.cosine_terms==other.cosine_terms for action,other in zip(total,line))


def test_endpoint_partition_uses_stricter_limit_than_general_atom_binding():
    g,q,_,saved=_source();atoms=saved.atoms.copy();atoms[0,0]+=5e-5
    result=check.verify_interface(g,q,ETA,_replace(saved,atoms=atoms),budget=BUDGET)
    assert result.status=='FAILED'
    assert result.metrics['atoms_scaled']<=F.from_float(1e-10)
    assert result.metrics['root_partition_scaled']>F.from_float(1e-11)
    assert any('root_partition' in reason for reason in result.failures)


def test_saved_record_owns_arrays_and_state_hash_binds_grid_q_eta():
    g,q,_,saved=_source();density=saved.density.copy()
    external=density.copy();owned=_replace(saved,density=external)
    external[:]=999.
    result=check.verify_interface(g,q,ETA,owned,budget=BUDGET)
    assert result.status=='PASSED'
    before=result.input_sha256['grid_q_eta']
    changed=(F(2,10**6),)+q[1:]
    result2=check.verify_interface(g,changed,ETA,
        _source()[3],budget=BUDGET)
    assert result2.input_sha256['grid_q_eta']!=before
    with pytest.raises(ValueError):
        check.SavedInterface(saved.cuts,density.astype(np.float32),saved.cosine,
            saved.atoms,saved.band_analytic,saved.band48,saved.band64,
            saved.line_band_analytic)
    bad=saved.band48.copy();bad[0,0]=np.nan
    with pytest.raises(ValueError):_replace(saved,band48=bad)


def test_failed_status_precedes_unresolved_comparisons(monkeypatch):
    g,q,_,saved=_source();count=0
    def mixed(*args,**kwargs):
        nonlocal count;count+=1
        status='HOLD_UNRESOLVED' if count==1 else 'FAILED' if count==2 else 'PASSED'
        return {'status':status,'absolute_error_lower':Z,'absolute_error_upper':Z,
                'saved_exact':Z,'scale_exact':F(1),'limit_exact':F(1),
                'enclosure':{},'comparison_work':{'exact_operations':1,
                                                   'cumulative_integer_bits':1}}
    monkeypatch.setattr(enclosure,'compare_saved',mixed)
    result=check.verify_interface(g,q,ETA,saved,budget=BUDGET)
    assert result.status=='FAILED'
    assert result.metrics['failed_comparisons']==1
    assert result.metrics['unresolved_comparisons']==1
    assert any('unresolved' in reason for reason in result.failures)


def test_partition_and_resource_preflight_precede_recovery(monkeypatch):
    g,q,_,saved=_source()
    baseline=check.verify_interface(g,q,ETA,saved,budget=BUDGET)
    constrained=(baseline.diagnostics['workspace_estimate_bytes']-
                 baseline.diagnostics['live_action_estimate_bytes']//2)
    def forbidden(*args,**kwargs):pytest.fail('recovery entered after failed preflight')
    monkeypatch.setattr(rec,'recover',forbidden)
    with pytest.raises(ValueError,match='workspace estimate'):
        check.verify_interface(g,q,ETA,saved,budget=replace(
            BUDGET,max_work_bytes=constrained))
    with pytest.raises(ValueError,match='comparison inventory'):
        check.verify_interface(g,q,ETA,saved,budget=replace(BUDGET,max_comparisons=1))
    low_recovery=replace(RB,max_free_dofs=1)
    with pytest.raises(ValueError,match='nested recovery inventory'):
        check.verify_interface(g,q,ETA,saved,budget=replace(
            BUDGET,recovery_budget=low_recovery))
    shifted=(Z,F(1,3),F(1))
    bad=check.SavedInterface(shifted,np.zeros((2,3,6)),saved.cosine,saved.atoms,
        saved.band_analytic,saved.band48,saved.band64,saved.line_band_analytic)
    with pytest.raises(ValueError,match='partition mismatch'):
        check.verify_interface(g,q,ETA,bad,budget=BUDGET)
