"""Actual nodal Newton preload, exact-support family checks and Euler search."""
from dataclasses import replace
from hashlib import sha256
import json
import numpy as np
import pytest
from anysolver import _ge_beam3_retained_nodal_loading as nodal
from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
from anysolver._ge_beam3_native_line_loading import LinePattern
from anysolver._ge_beam3_p5_seeded.core import canonical,sha
from anysolver._native_paired_factor_chain_modes import solve_paired_factor_chain_modes as paired
from docs.reference_cases.ge_beam3_exact_family_partition import partition
from test_ge_beam3_native_generalized_modal import make
from test_ge_beam3_schur_line_program import save

EMPTY=DistributedPattern(LinePattern(()),())


def capture(compression,macros):
    m,_,masses=make(False,macros,clamped=True,coupled=False)
    tip=max(m.mesh.nodes)
    p=nodal.Program((.5,1.),EMPTY,nodal.NodalDeadForces(((tip,float(-compression),0.,0.),)))
    result=nodal.solve(m,p)
    return m,p,masses,result


def family_modes(family):
    return paired(family['left'],family['right'],family['geometric'],family['kinetic'],
        family['free'],family['algebraic'],bounds=(-100.,1e6),num_modes=1)


@pytest.mark.parametrize('mutation',('valid','material','kinetic','geometric','nonfinite','layout'))
def test_original_support_partition(mutation,tmp_path):
    m,p,masses,result=capture(0.,1);assert result.status=='completed',result.failure
    packet,guard=nodal.prepare(m,p,result.checkpoint,masses,expected_sha256=sha256(result.checkpoint).hexdigest())
    n=m.mesh.dof_manager.total_dofs
    if mutation=='valid':
        families=partition(packet,n,guard)
        roots={name:float(family_modes(f).eigenvalues[0]) for name,f in families.items()}
        full=paired(packet.left,packet.right,packet.geometric,packet.kinetic,packet.free_dofs,packet.algebraic_dofs,bounds=(-100.,1e6),num_modes=1)
        assert abs(min(roots.values())-full.eigenvalues[0])<=1e-11*max(1.,abs(full.eigenvalues[0]))
        save(tmp_path/'partition.json',dict(roots=roots,full_root=float(full.eigenvalues[0]),families=families))
        return
    if mutation=='material':
        right=packet.right.copy();row=int(np.flatnonzero(np.any(right[:,::6]!=0.,axis=1))[0]);right[row,1]=1e-200
        packet=replace(packet,right=right)
    elif mutation=='kinetic':
        b=packet.kinetic.copy();row=int(np.flatnonzero(np.any(b[:,::6]!=0.,axis=1))[0]);b[row,1]=1e-200
        packet=replace(packet,kinetic=b)
    elif mutation=='geometric':
        g=packet.geometric.copy();g[0,1]=g[1,0]=1e-200;packet=replace(packet,geometric=g)
    elif mutation=='nonfinite':
        right=packet.right.copy();right[0,0]=np.nan;packet=replace(packet,right=right)
    else:n+=1
    with pytest.raises(ValueError):partition(packet,n)
    save(tmp_path/'rejected.json',dict(mutation=mutation,rejected_without_small_entry_threshold=True))


@pytest.mark.parametrize('macros',(1,2,4,8))
def test_actual_prestress_euler(macros,tmp_path):
    euler=float(np.pi**2/16);rows=[];constant_families={}
    def evaluate(compression):
        index=len(rows);print(dict(stage='actual-preload',macros=macros,index=index,compression=compression),flush=True)
        m,p,masses,result=capture(compression,macros)
        save(tmp_path/('state-%02d.json'%index),result.checkpoint)
        assert result.status=='completed',result.failure
        before=canonical(result.state);state=result.state.mechanical
        reference=np.array([m.mesh.nodes[node].coords() for node in sorted(m.mesh.nodes)])
        displacement=state.positions-reference+state.position_low
        expected=np.zeros_like(displacement);expected[:,0]=-compression*reference[:,0]/1000.
        axial_error=float(np.linalg.norm(displacement-expected));assert axial_error<=1e-11
        record=json.loads(result.checkpoint)['records'][-1]
        reaction_error=abs(record['residual'][0]-compression);assert reaction_error<=1e-11
        packet,guard=nodal.prepare(m,p,result.checkpoint,masses,expected_sha256=sha256(result.checkpoint).hexdigest())
        families=partition(packet,m.mesh.dof_manager.total_dofs,guard)
        modes={}
        for name in ('axial','torsion'):
            f=families[name]
            if name not in constant_families:
                mode=family_modes(f);assert mode.eigenvalues[0]>0.;constant_families[name]=f
            else:
                for key,value in f.items():
                    assert np.array_equal(value,constant_families[name][key]),name+' family unexpectedly depends on preload'
        for name in ('bend-y','bend-z'):modes[name]=family_modes(families[name])
        lam=min(float(mode.eigenvalues[0]) for mode in modes.values())
        full_error=None
        if macros==1 and index<4:
            full=paired(packet.left,packet.right,packet.geometric,packet.kinetic,packet.free_dofs,
                packet.algebraic_dofs,bounds=(-100.,1e6),num_modes=1)
            full_error=abs(lam-float(full.eigenvalues[0]))/max(1.,abs(lam));assert full_error<=1e-11
        guard();assert canonical(result.state)==before
        row=dict(index=index,compression=compression,lambda_min=lam,axial_error=axial_error,
            reaction_error=reaction_error,checkpoint_sha256=sha256(result.checkpoint).hexdigest(),
            full_partition_root_error=full_error)
        save(tmp_path/('point-%02d.json'%index),dict(row=row,packet=packet,families=families,modes=modes,
            global_newton_programme_run=True,manufactured_uniform_axial_equilibrium=False,production_qualified=False))
        rows.append(row);print(dict(stage='signed-spectrum',**row),flush=True)
        return lam
    tension=evaluate(-.5*euler);unloaded=evaluate(0.);compressed=evaluate(.5*euler)
    assert tension>unloaded>compressed>0.
    low,high=0.,2*euler;assert evaluate(high)<0.
    low_value,high_value=unloaded,rows[-1]['lambda_min']
    for _ in range(18):
        midpoint=float((low+high)/2);value=evaluate(midpoint)
        if value>0.:low,low_value=midpoint,value
        else:high,high_value=midpoint,value
    critical=float((low+high)/2);error=abs(critical/euler-1.)
    assert low_value>0. and high_value<=0. and (high-low)/euler<1e-5
    if macros==8:assert error<.02
    save(tmp_path/'buckling.json',dict(macros=macros,rows=rows,critical_bracket=[low,high],
        bracket_eigenvalues=[low_value,high_value],critical_midpoint=critical,euler_reference=euler,
        relative_euler_error=error,finest_engineering_gate=(macros==8),
        search='18_BISECTIONS_OF_ACTUAL_NODAL_NEWTON_PRELOADED_SIGNED_FACTOR_FAMILIES',
        current_frequency_is_not_a_load_factor=True,production_qualified=False,full_spatial_postbuckling_qualified=False))
