"""Compose bounded saved F03 component evidence over one owned state."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from types import MappingProxyType

import numpy as np

from scripts import _b3_e4_f03_action_enclosure as action
from scripts import _b3_e4_f03_local_functional as functional
from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_recovery as recovery
from scripts import _b3_e4_f03_saved_interface_checks as interface
from scripts import _b3_e4_f03_saved_norm_checks as norm
from scripts import _b3_e4_f03_saved_work_checks as work
from scripts import _b3_e4_f03_sparse_certificate as sparse_common
from scripts import _b3_e4_f03_sparse_equilibrium_checks as equilibrium
from scripts import _b3_e4_f03_sparse_state_binding as binding


SCOPE='SAVED_RECOVERY_COMPONENT_COMPOSITION_ONLY'


@dataclass(frozen=True,slots=True)
class CompositionBudget:
    equilibrium_budget:equilibrium.EquilibriumBudget
    interface_budget:interface.InterfaceBudget
    work_budget:work.WorkBudget
    norm_budget:norm.NormBudget
    max_owned_bytes:int
    max_comparisons:int
    max_aggregate_operations:int
    max_aggregate_bits:int
    max_work_bytes:int

    def __post_init__(self):
        if (type(self.equilibrium_budget) is not equilibrium.EquilibriumBudget or
                type(self.interface_budget) is not interface.InterfaceBudget or
                type(self.work_budget) is not work.WorkBudget or
                type(self.norm_budget) is not norm.NormBudget or any(
                type(getattr(self,name)) is not int or getattr(self,name)<=0 for name in
                ('max_owned_bytes','max_comparisons','max_aggregate_operations',
                 'max_aggregate_bits','max_work_bytes'))):
            raise ValueError('explicit positive saved-composition budgets required')


def _freeze(value):
    if isinstance(value,dict):
        return MappingProxyType({key:_freeze(item) for key,item in value.items()})
    if isinstance(value,(tuple,list)):
        return tuple(_freeze(item) for item in value)
    return value


def _saved_interface(value):
    if type(value) is not interface.SavedInterface:
        raise ValueError('SavedInterface record required')
    return interface.SavedInterface(**{name:getattr(value,name) for name in
        ('cuts','density','cosine','atoms','band_analytic','band48','band64',
         'line_band_analytic')})


def _saved_work(value):
    if type(value) is not work.SavedWork:raise ValueError('SavedWork record required')
    return work.SavedWork(**{name:getattr(value,name) for name in value.__dataclass_fields__})


def _saved_norm(value):
    if type(value) is not norm.SavedNorm:raise ValueError('SavedNorm record required')
    return norm.SavedNorm(**{name:getattr(value,name) for name in value.__dataclass_fields__})


def _hash_saved_work(value):
    digest=hashlib.sha256(b'F03_SAVED_WORK_RECORD_V1\0')
    digest.update(bytes((value.p,)))
    for item in value.cuts:action._hash_fraction(digest,item)
    encoded=value.lift_family.encode('ascii');digest.update(len(encoded).to_bytes(4,'little'));digest.update(encoded)
    for name in ('lift_coefficients','shell_work','interface_work','edge_route1',
                 'edge_route2','first_free','shift_delta','virtual_terms','virtual_defects'):
        array=np.asarray(getattr(value,name),dtype='<f8')
        digest.update(name.encode('ascii')+b'\0')
        digest.update(np.asarray(array.shape,dtype='<i8').tobytes())
        digest.update(array.tobytes())
    return digest.hexdigest()


def _hash_saved_norm(value):
    digest=hashlib.sha256(b'F03_SAVED_NORM_RECORD_V1\0')
    for name in ('channels','totals','components','channel_flags','total_flags','exact_zero'):
        array=getattr(value,name);digest.update(name.encode('ascii')+b'\0')
        digest.update(np.asarray(array.shape,dtype='<i8').tobytes());digest.update(array.tobytes())
    for records in value.failures:
        digest.update(len(records).to_bytes(4,'little'))
        for stage,channel,reason in records:
            for item in (stage,str(channel),reason):
                encoded=item.encode();digest.update(len(encoded).to_bytes(8,'little'));digest.update(encoded)
    return digest.hexdigest()


def _hash_grid(value):
    """Bind every compiled-grid field consumed by the composed components."""
    digest=hashlib.sha256(b'F03_COMPILED_GRID_V1\0')
    digest.update(value.p.to_bytes(8,'little',signed=True))
    for name,values in (('x_cuts',value.x_cuts),('y_cuts',value.y_cuts),
                        ('x_nodes',value.x_nodes),('y_nodes',value.y_nodes),
                        ('station_cuts',value.station_cuts)):
        digest.update(name.encode('ascii')+b'\0')
        digest.update(len(values).to_bytes(8,'little'))
        for item in values:action._hash_fraction(digest,item)
    digest.update(b'rectangles\0'+len(value.rectangles).to_bytes(8,'little'))
    for rectangle in value.rectangles:
        for item in (rectangle.x0,rectangle.x1,rectangle.y0,rectangle.y1):
            action._hash_fraction(digest,item)
    for name,array in (('free_to_full',value.free_to_full),
                       ('full_to_free',value.full_to_free),
                       ('full_gathers',value.full_gathers),
                       ('free_gathers',value.free_gathers),
                       ('root_incidence',value.root_incidence)):
        data=np.asarray(array,dtype='<i8')
        digest.update(name.encode('ascii')+b'\0')
        digest.update(np.asarray(data.shape,dtype='<i8').tobytes())
        digest.update(data.tobytes())
    digest.update(b'trace_incidence\0'+len(value.trace_incidence).to_bytes(8,'little'))
    for array in value.trace_incidence:
        data=np.asarray(array,dtype='<i8')
        digest.update(np.asarray(data.shape,dtype='<i8').tobytes())
        digest.update(data.tobytes())
    return digest.hexdigest()


def _owned_bytes(grid,matrices,vectors,saved_interface,saved_work,saved_norm,exact):
    total=sum(m.data.nbytes+m.indices.nbytes+m.indptr.nbytes for m in matrices)
    total+=sum(v.nbytes for v in vectors)
    total+=sum(array.nbytes for array in (grid.free_to_full,grid.full_to_free,
        grid.full_gathers,grid.free_gathers,grid.root_incidence,*grid.trace_incidence))
    total+=sum(getattr(saved_interface,name).nbytes for name in
        ('density','cosine','atoms','band_analytic','band48','band64','line_band_analytic'))
    total+=sum(getattr(saved_work,name).nbytes for name in
        ('lift_coefficients','shell_work','interface_work','edge_route1','edge_route2',
         'first_free','shift_delta','virtual_terms','virtual_defects'))
    total+=sum(getattr(saved_norm,name).nbytes for name in
        ('channels','totals','components','channel_flags','total_flags','exact_zero'))
    total+=sum((v.numerator.bit_length()+v.denominator.bit_length()+7)//8+256
               for v in exact)+65536
    return total


def _snapshot_hash(grid,matrices,vectors,state_digest,saved_hashes):
    digest=hashlib.sha256(b'F03_SAVED_RECOVERY_COMPOSITION_V1\0')
    digest.update(b'grid\0'+_hash_grid(grid).encode())
    digest.update(state_digest.encode())
    matrix_names=('K_shell','K_beam','K_shell_plus','K_beam_plus','C_root','H')
    vector_names=('f','D','b','q','eta','z','H_z')
    for name,value in zip(matrix_names,matrices):
        encoded=binding._hash_sparse(value).encode();digest.update(name.encode()+b'\0'+encoded)
    for name,value in zip(vector_names,vectors):
        encoded=binding._hash_vector(value).encode();digest.update(name.encode()+b'\0'+encoded)
    for name,value in sorted(saved_hashes.items()):digest.update(name.encode()+b'\0'+value.encode())
    return digest.hexdigest()


def _preflight(grid,matrices,vectors,exact,saved_interface,saved_work,
               norm_functional,budget,owned_bytes):
    n=grid.free_dofs;ni=len(grid.station_cuts)-1
    ks,kb,ks2,kb2,root,h=matrices
    f,d,b,q,eta,z,h_z=vectors
    if (any(m.shape!=(n,n) for m in (ks,kb,ks2,kb2)) or root.shape!=(3,n) or
            h.shape!=(n+3,n+3) or any(v.shape!=(n,) for v in (f,d,q)) or
            eta.shape!=(3,) or any(v.shape!=(n+3,) for v in (b,z,h_z))):
        raise ValueError('saved composition requires one common numerical state dimension')
    if (saved_interface.cuts!=grid.station_cuts or saved_work.cuts!=grid.station_cuts or
            saved_work.p!=grid.p):
        raise ValueError('saved composition grid degree or partition mismatch')
    ib=budget.interface_budget;wb=budget.work_budget;nb=budget.norm_budget;eb=budget.equilibrium_budget
    nv=3*(ni*(grid.p+2)+1);interface_comparisons=192
    work_comparisons=6*nv+50;norm_comparisons=4
    comparisons=interface_comparisons+work_comparisons+norm_comparisons
    if (ni>ib.max_intervals or ni>nb.max_intervals or
            grid.free_dofs>ib.recovery_budget.max_free_dofs or
            grid.free_dofs>wb.support_budget.max_free_dofs or
            grid.free_dofs>wb.support_budget.recovery_budget.max_free_dofs or
            ni>ib.recovery_budget.max_intervals or ni>wb.support_budget.max_intervals or
            ni>wb.support_budget.recovery_budget.max_intervals or
            nv>wb.max_virtual_tests or interface_comparisons>ib.max_comparisons or
            work_comparisons>wb.max_comparisons or comparisons>budget.max_comparisons):
        raise ValueError('saved composition nested inventory exceeds budget')
    if (interface_comparisons*ib.action_budget.max_operations>ib.max_aggregate_operations or
            interface_comparisons*ib.action_budget.max_total_bits>ib.max_aggregate_bits or
            work_comparisons*wb.action_budget.max_operations>wb.max_aggregate_operations or
            work_comparisons*wb.action_budget.max_total_bits>wb.max_aggregate_bits):
        raise ValueError('saved composition nested Action envelope exceeds budget')
    six_upper=2*sum(m.nnz for m in (ks,kb,ks2,kb2))
    if six_upper>eb.max_six_block_nnz:raise ValueError('saved composition six-block envelope exceeds budget')
    binding_envelope=int(ks.nnz+kb.nnz+2*root.nnz)
    bb=eb.binding_budget;sb=bb.sparse_budget
    if (binding_envelope>min(sb.max_nnz,bb.max_combined_nnz) or
            h.nnz+binding_envelope>bb.max_combined_nnz):
        raise ValueError('saved composition nested binding envelope exceeds budget')
    binding_workspace=1024*(h.nnz+binding_envelope+10*(n+3))+2*bb.max_total_bits
    equilibrium_workspace=1024*(6*six_upper+12*(n+3))+2*eb.max_total_bits
    if (binding_workspace>bb.max_python_work_bytes or
            equilibrium_workspace>eb.max_python_work_bytes):
        raise ValueError('saved composition nested numerical workspace exceeds budget')
    fraction_slot=512+(2*ib.action_budget.max_fraction_bits+7)//8
    saved_interface_bytes=sum(getattr(saved_interface,name).nbytes for name in
        ('density','cosine','atoms','band_analytic','band48','band64','line_band_analytic'))
    interface_workspace=(saved_interface_bytes+ib.recovery_budget.max_work_bytes+
        ib.action_budget.max_work_bytes+interface_comparisons*(32*fraction_slot+4096)+
        (ni*3*6+3+6)*fraction_slot+128*(1+8*ni)*(512+(2*recovery.BITS+7)//8)+
        ni*3*6*256)
    work_workspace=(ni*3*6*(1024+2*recovery.BITS//8)*2+
        sum(getattr(saved_work,name).nbytes for name in ('lift_coefficients','shell_work',
            'interface_work','edge_route1','edge_route2','first_free','shift_delta',
            'virtual_terms','virtual_defects'))*2+
        work_comparisons*(4096+64*(1024+2*wb.action_budget.max_fraction_bits//8))+
        wb.support_budget.max_work_bytes+wb.support_budget.recovery_budget.max_work_bytes+
        wb.action_budget.max_work_bytes)
    norm_count=len(norm_functional.cuts)+ni*18+9
    norm_bits=sum(v.numerator.bit_length()+v.denominator.bit_length()
        for values in (norm_functional.cuts,norm_functional.cosine,*norm_functional.atoms,
            *(p for row in norm_functional.coefficients for p in row)) for v in values)
    norm_operations=2*3*ni*(64**2*96+64*96)+16384
    norm_workspace=(2*norm_count*(512+(2*functional.INPUT_INTEGER_BITS+7)//8)+
                    64**2*8*96+ni*3*8*256+65536)
    if interface_workspace>ib.max_work_bytes or work_workspace>wb.max_work_bytes:
        raise ValueError('saved composition nested component workspace exceeds budget')
    if (norm_bits>nb.max_integer_bits or norm_operations>nb.max_operations or
            norm_workspace>nb.max_work_bytes):
        raise ValueError('saved composition nested norm envelope exceeds budget')
    local=2*(grid.p+1)**2;active=max((len(ids) for ids in grid.trace_incidence),default=0)
    def recovery_envelope(rb):
        operations=(ni*len(grid.rectangles)*256*(grid.p+3)**4+
                    len(grid.rectangles)*local*(local+12))
        workspace=(768*(grid.free_dofs+ni*180+128)+rb.max_integer_bits//8+
                   local*local*768+active*3*(grid.p+3)*768+
                   rb.trace_budget.max_trace_integer_bits//8)
        return operations,workspace
    for rb in (ib.recovery_budget,wb.support_budget.recovery_budget):
        recovery_operations,recovery_workspace=recovery_envelope(rb)
        if (recovery_operations>rb.max_operations or recovery_workspace>rb.max_work_bytes):
            raise ValueError('saved composition nested recovery envelope exceeds budget')
    support_operations=(len(grid.rectangles)*local*(local+24)*32+
                        ni*max(1,active)*(grid.p+3)*96)
    support_workspace=(768*(12*local*len(grid.rectangles)+ni*360+grid.free_dofs)+
                       wb.support_budget.max_integer_bits//8)
    if (support_operations>wb.support_budget.max_operations or
            support_workspace>wb.support_budget.max_work_bytes):
        raise ValueError('saved composition nested support envelope exceeds budget')
    exact_bits=sum(recovery._bits(value) for value in exact)
    if (exact_bits>wb.support_budget.recovery_budget.max_integer_bits or
            exact_bits>wb.support_budget.max_integer_bits):
        raise ValueError('saved composition exact state exceeds nested integer budget')
    operations=(ib.max_aggregate_operations+wb.max_aggregate_operations+nb.max_operations+
        ib.recovery_budget.max_operations+2*wb.support_budget.recovery_budget.max_operations+
        wb.support_budget.max_operations)
    bits=(eb.max_total_bits+ib.max_aggregate_bits+wb.max_aggregate_bits+nb.max_integer_bits+
        ib.recovery_budget.max_integer_bits+2*wb.support_budget.recovery_budget.max_integer_bits+
        wb.support_budget.max_integer_bits)
    workspace=(eb.max_python_work_bytes+ib.max_work_bytes+wb.max_work_bytes+
               nb.max_work_bytes+owned_bytes+65536)
    if operations>budget.max_aggregate_operations:
        raise ValueError('saved composition operation envelope exceeds budget')
    if bits>budget.max_aggregate_bits:
        raise ValueError('saved composition integer envelope exceeds budget')
    if owned_bytes>budget.max_owned_bytes or workspace>budget.max_work_bytes:
        raise ValueError('saved composition owned/workspace envelope exceeds budget')
    return dict(comparisons=comparisons,operation_envelope=operations,
        integer_bit_envelope=bits,workspace_envelope_bytes=workspace,
        owned_snapshot_bytes=owned_bytes,six_block_preflight_upper=six_upper)


def verify_composition(grid,k_shell,k_beam,k_shell_plus,k_beam_plus,c_root,
        f,d,h,b,q,eta,z,h_z,saved_interface,saved_work,saved_norm,*,budget):
    """Re-run and cross-bind four component checks from one owned snapshot."""
    if type(grid) is not topology.CompiledGrid or type(budget) is not CompositionBudget:
        raise ValueError('factory grid and explicit CompositionBudget required')
    sb=budget.equilibrium_budget.binding_budget.sparse_budget
    matrices=(sparse_common.validate_sparse(k_shell,sb),
              sparse_common.validate_sparse(k_beam,sb),
              sparse_common.validate_sparse(k_shell_plus,sb),
              sparse_common.validate_sparse(k_beam_plus,sb),
              sparse_common.validate_sparse(c_root,sb,square=False),
              sparse_common.validate_sparse(h,sb))
    n=grid.free_dofs
    vectors=(sparse_common._vector(f,n,'physical load'),
             sparse_common._vector(d,n,'scaling D'),
             sparse_common._vector(b,n+3,'scaled b'),
             sparse_common._vector(q,n,'physical q'),
             sparse_common._vector(eta,3,'physical eta'),
             sparse_common._vector(z,n+3,'scaled z'),
             sparse_common._vector(h_z,n+3,'saved H_z'))
    si=_saved_interface(saved_interface);sw=_saved_work(saved_work);sn=_saved_norm(saved_norm)
    q_exact=recovery._vector(vectors[3],n,budget.interface_budget.recovery_budget.max_integer_bits)
    eta_exact=recovery._vector(vectors[4],3,budget.interface_budget.recovery_budget.max_integer_bits-
                               sum(recovery._bits(value) for value in q_exact))
    owned=_owned_bytes(grid,matrices,vectors,si,sw,sn,(*q_exact,*eta_exact))
    preflight_functional=interface._saved_functional(si)
    envelope=_preflight(grid,matrices,vectors,(*q_exact,*eta_exact),si,sw,
                        preflight_functional,budget,owned)
    state_digest=interface._hash_state(grid,q_exact,eta_exact)
    saved_hashes={'saved_interface':interface._hash_saved(si),
                  'saved_work':_hash_saved_work(sw),'saved_norm':_hash_saved_norm(sn)}
    snapshot=_snapshot_hash(grid,matrices,vectors,state_digest,saved_hashes)

    ks,kb,ks2,kb2,root,h0=matrices;f0,d0,b0,q0,eta0,z0,hz0=vectors
    numerical=equilibrium.verify_equilibrium(ks,kb,ks2,kb2,root,f0,d0,h0,b0,
        q0,eta0,z0,hz0,budget=budget.equilibrium_budget)
    iface=interface.verify_interface(grid,q_exact,eta_exact,si,budget=budget.interface_budget)
    worked=work.verify_work(grid,q_exact,eta_exact,sw,budget=budget.work_budget)
    normed=norm.verify_norm(iface.saved_functional,sn,budget=budget.norm_budget)

    expected_numerical={name:binding._hash_sparse(value) for name,value in
        (('K_shell',ks),('K_beam',kb),('C_root',root),('H',h0))}
    expected_numerical.update({name:binding._hash_vector(value) for name,value in
        (('f',f0),('D',d0),('q',q0),('eta',eta0),('z',z0),('b',b0),('H_z',hz0))})
    expected_numerical.update({'K_shell_plus':equilibrium._hash_sparse(ks2),
                               'K_beam_plus':equilibrium._hash_sparse(kb2)})
    observed_numerical=numerical['input_sha256']
    cross={f'numerical_{name}':observed_numerical.get(name)==value
           for name,value in expected_numerical.items()}
    cross.update(interface_state=iface.input_sha256['grid_q_eta']==state_digest,
        interface_saved=iface.input_sha256['saved_interface']==saved_hashes['saved_interface'],
        recovery_q=iface.recovery.q==q_exact,recovery_eta=iface.recovery.eta==eta_exact,
        recovery_cuts=iface.recovery.cuts==grid.station_cuts)
    work_identity=work._identity(grid,iface.recovery,sw)
    norm_identity=norm._hash(iface.saved_functional,sn)
    cross.update(work_state_saved=worked['input_sha256']==work_identity,
                 norm_functional_saved=normed['input_sha256']==norm_identity,
                 norm_functional_type=type(iface.saved_functional) is functional.Functional,
                 functional_chain=iface.saved_functional==preflight_functional)

    statuses={'numerical':numerical['status'],'interface':iface.status,
              'work':worked['status'],'norm':normed['status']}
    allowed={'numerical':{'NUMERICAL_MECHANICAL_CHECKS_PASSED','HOLD'},
             'interface':{'PASSED','FAILED','HOLD_UNRESOLVED'},
             'work':{'PASSED','FAILED','HOLD_UNRESOLVED'},
             'norm':{'PASSED','FAILED','HOLD_UNRESOLVED'}}
    if any(value not in allowed[name] for name,value in statuses.items()):
        raise ArithmeticError('unexpected saved component status')
    reasons=[]
    reasons.extend(f'cross-binding failed: {name}' for name,value in cross.items() if not value)
    reasons.extend(iface.failures);reasons.extend(numerical['failures'])
    if worked['status']=='FAILED':reasons.append('saved work component failed')
    if normed['status']=='FAILED':reasons.append('saved norm component failed')
    if (not all(cross.values()) or iface.status=='FAILED' or
            worked['status']=='FAILED' or normed['status']=='FAILED'):
        status='COMPOSITION_FAILED'
    elif numerical['status']=='HOLD':status='HOLD_NUMERICAL'
    elif 'HOLD_UNRESOLVED' in statuses.values():status='HOLD_UNRESOLVED'
    else:status='COMPONENT_CHECKS_PASSED'
    if status=='HOLD_UNRESOLVED':reasons.append('one or more component bounds are unresolved')
    if status=='HOLD_NUMERICAL' and not numerical['failures']:
        reasons.append('sparse numerical component is on hold')
    actual_comparisons=(iface.diagnostics['comparisons']+
                        worked['diagnostics']['comparisons']+4)
    fixed_work=(iface.diagnostics['recovery_recomputations']==1 and
        iface.diagnostics['equilibrium_solves']==0 and
        worked['diagnostics']['state_recoveries']==2 and
        worked['diagnostics']['equilibrium_solves']==0 and
        normed['diagnostics']['norm_evaluations']==2 and
        normed['diagnostics']['equilibrium_solves']==0 and
        numerical['work']['new_equilibrium_solves']==0 and
        numerical['work']['factorizations']==0)
    if actual_comparisons>envelope['comparisons']:
        raise ArithmeticError('unexpected saved composition comparison count')
    if not fixed_work:
        raise ArithmeticError('unexpected saved composition work count')
    diagnostics={**envelope,'actual_comparisons':actual_comparisons,
        'recovery_recomputations':iface.diagnostics['recovery_recomputations']+
                                  worked['diagnostics']['state_recoveries'],
        'norm_evaluations':normed['diagnostics']['norm_evaluations'],
        'equilibrium_solves':numerical['work']['new_equilibrium_solves'],
        'factorizations':numerical['work']['factorizations']}
    canonical_saved={'compiled_grid':_hash_grid(grid),**saved_hashes,
                      'work_state_saved':work_identity,
                      'norm_functional_saved':norm_identity}
    return _freeze(dict(scope=SCOPE,status=status,reasons=tuple(reasons),
        canonical_snapshot_sha256=snapshot,canonical_saved_sha256s=canonical_saved,
        component_statuses=statuses,cross_bindings=cross,diagnostics=diagnostics,
        components={'numerical':numerical,'interface':iface,
                    'work':worked,'norm':normed}))
