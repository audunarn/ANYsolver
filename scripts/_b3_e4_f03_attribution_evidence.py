"""Bounded, independently recomputable Q4 saved-action evidence.

The archive is a strict NPZ of physical CSR operators and owned float64
vectors. Verification performs matrix actions and off-grid interpolation;
it never factors or solves an equilibrium or structural Schur system.
"""

from __future__ import annotations

from hashlib import sha256
import hmac
from pathlib import Path
import zipfile

import numpy as np
from scipy import sparse

import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling


MAX_UNCOMPRESSED_BYTES=64*1024*1024
_MATRICES=('P','K_coarse','K_fine','C_fine')
_VECTORS=('f_coarse','f_fine','q_middle','q_fine','lambda_fine',
          'prolonged_q','e','Kf_e','Cf_e','r_fine','Kc_qmiddle',
          'Kf_qfine','Kf_prolonged_q','Cf_qfine','Cf_prolonged_q','CfT_lambda')
_FAMILY={'P1':0,'hybrid':1,'enriched':2}
_META=('__schema','__case','__family')
LIMITS={
    'action_parity_scaled':1e-11,
    'support_preservation_max_abs':0.,
    'scaled_pullback_relative_fro':1e-11,
    'scaled_load_pullback_relative_inf':1e-11,
    'shell_energy_preservation_scaled':1e-11,
    'beam_energy_preservation_scaled':1e-11,
    'load_work_preservation_scaled':1e-11,
    'identity_defect_scaled':1e-11,
    'fine_free_equilibrium_scaled':1e-8,
    'fine_compatibility_scaled':1e-9,
    'offgrid_field_scaled':1e-11,
    'offgrid_strain_scaled':1e-10,
}


def _layout(middle_mesh: tuple[int,int,int,int], family: str) -> dict[str,int]:
    if (not isinstance(middle_mesh,(tuple,list)) or len(middle_mesh)!=4 or
            any(type(v) is not int for v in middle_mesh) or
            type(family) is not str or family not in _FAMILY):
        raise ValueError('invalid bounded attribution evidence case')
    ns,ny,nb,nm=middle_mesh
    if not 1<=ns<=8 or not 2<=ny<=16 or not 1<=nb<=16 or not 2<=nm<=8:
        raise ValueError('outside bounded attribution evidence case')
    sc=2*(2*ns+1)*(ny+1)
    sf=2*(4*ns+1)*(2*ny+1)
    nc=sc+beam.dof_count(nb)
    nf=sf+beam.dof_count(2*nb)
    rows=3*(2*nm+1+(2 if family=='enriched' else 0))
    return {'sc':sc,'sf':sf,'nc':nc,'nf':nf,'rows':rows,
            'ns':ns,'ny':ny,'nb':nb,'nm':nm}


def _shapes(layout: dict[str,int]) -> dict[str,tuple[int,...]]:
    nc,nf,rows=layout['nc'],layout['nf'],layout['rows']
    return {'P':(nf,nc),'K_coarse':(nc,nc),'K_fine':(nf,nf),
            'C_fine':(rows,nf),
            'f_coarse':(nc,),'f_fine':(nf,),
            'q_middle':(nc,),'q_fine':(nf,),'lambda_fine':(rows,),
            'prolonged_q':(nf,),'e':(nf,),'Kf_e':(nf,),
            'Cf_e':(rows,),'r_fine':(nf,),'Kc_qmiddle':(nc,),
            'Kf_qfine':(nf,),'Kf_prolonged_q':(nf,),
            'Cf_qfine':(rows,),'Cf_prolonged_q':(rows,),
            'CfT_lambda':(nf,)}


def _validate_actions(actions: dict, layout: dict[str,int]) -> None:
    shapes=_shapes(layout)
    if not isinstance(actions,dict) or set(actions)!=set(shapes):
        raise ValueError('incorrect attribution action inventory')
    storage=[]
    for name,shape in shapes.items():
        value=actions[name]
        if name in _MATRICES:
            if (not sparse.isspmatrix_csr(value) or value.shape!=shape or
                    value.data.dtype!=np.float64 or
                    value.indptr[0]!=0 or value.indptr[-1]!=len(value.data) or
                    np.any(np.diff(value.indptr)<0) or
                    np.any(value.indices<0) or np.any(value.indices>=shape[1]) or
                    not np.all(np.isfinite(value.data))):
                raise ValueError(f'invalid attribution CSR {name}')
            storage.extend((value.data,value.indices,value.indptr))
        else:
            if (not isinstance(value,np.ndarray) or value.dtype!=np.float64 or
                    value.shape!=shape or not np.all(np.isfinite(value))):
                raise ValueError(f'invalid attribution vector {name}')
            storage.append(value)
    for i,left in enumerate(storage):
        if any(np.shares_memory(left,right) for right in storage[i+1:]):
            raise ValueError('aliased attribution action storage')


def _payload_keys() -> set[str]:
    return (set(_VECTORS)|set(_META)|
            {f'{name}.{part}' for name in _MATRICES
             for part in ('data','indices','indptr','shape')})


def _digest(payload: dict[str,np.ndarray]) -> np.ndarray:
    digest=sha256()
    for name in sorted(payload):
        value=np.ascontiguousarray(payload[name])
        digest.update(name.encode('ascii')+b'\0')
        digest.update(value.dtype.str.encode('ascii')+b'\0')
        digest.update(np.asarray(value.shape,dtype='<i8').tobytes())
        digest.update(value.tobytes())
    return np.frombuffer(digest.digest(),dtype=np.uint8).copy()


def pack_actions(actions: dict, *, middle_mesh: tuple[int,int,int,int],
                 family: str) -> dict[str,np.ndarray]:
    """Strict owned NPZ payload; write with np.savez_compressed(**payload)."""
    layout=_layout(middle_mesh,family)
    _validate_actions(actions,layout)
    payload={'__schema':np.array([1],dtype=np.int64),
             '__case':np.array(middle_mesh,dtype=np.int64),
             '__family':np.array([_FAMILY[family]],dtype=np.int64)}
    for name in _MATRICES:
        value=actions[name].copy()
        value.sum_duplicates()
        value.sort_indices()
        value.eliminate_zeros()
        payload.update({f'{name}.data':value.data.copy(),
                        f'{name}.indices':value.indices.astype(np.int64,copy=True),
                        f'{name}.indptr':value.indptr.astype(np.int64,copy=True),
                        f'{name}.shape':np.array(value.shape,dtype=np.int64)})
    for name in _VECTORS:
        payload[name]=actions[name].copy()
    if sum(v.nbytes+256 for v in payload.values())+288>MAX_UNCOMPRESSED_BYTES:
        raise ValueError('attribution archive exceeds uncompressed bound')
    payload['__digest']=_digest(payload)
    return payload


def _load_archive(source: Path | dict[str,np.ndarray]) -> dict[str,np.ndarray]:
    expected=_payload_keys()|{'__digest'}
    if isinstance(source,(str,Path)):
        path=Path(source)
        try:
            with zipfile.ZipFile(path) as zf:
                names=zf.namelist()
                if (len(names)!=len(expected) or set(names)!=
                        {f'{name}.npy' for name in expected} or
                        sum(info.file_size for info in zf.infolist())>
                        MAX_UNCOMPRESSED_BYTES):
                    raise ValueError('invalid attribution ZIP inventory or size')
            with np.load(path,allow_pickle=False) as npz:
                payload={name:npz[name].copy() for name in expected}
        except (zipfile.BadZipFile,OSError) as exc:
            raise ValueError('corrupt attribution ZIP') from exc
    else:
        if not isinstance(source,dict) or set(source)!=expected:
            raise ValueError('invalid attribution archive inventory')
        if any(not isinstance(v,np.ndarray) for v in source.values()):
            raise ValueError('invalid attribution archive arrays')
        if sum(v.nbytes+256 for v in source.values())>MAX_UNCOMPRESSED_BYTES:
            raise ValueError('attribution archive exceeds uncompressed bound')
        values=list(source.values())
        if any(np.shares_memory(a,b) for i,a in enumerate(values) for b in values[i+1:]):
            raise ValueError('aliased attribution archive arrays')
        payload={name:value.copy() for name,value in source.items()}
    if set(payload)!=expected:
        raise ValueError('invalid attribution archive inventory')
    if (payload['__digest'].dtype!=np.uint8 or payload['__digest'].shape!=(32,) or
            not hmac.compare_digest(payload['__digest'].tobytes(),
                                    _digest({k:v for k,v in payload.items()
                                             if k!='__digest'}).tobytes())):
        raise ValueError('corrupt attribution archive digest')
    return payload


def unpack_actions(source: str | Path | dict[str,np.ndarray], *,
                   middle_mesh: tuple[int,int,int,int], family: str) -> dict:
    """Preflight ZIP metadata before decompression; own and validate actions."""
    layout=_layout(middle_mesh,family)
    payload=_load_archive(source)
    if (payload['__schema'].dtype!=np.int64 or
            payload['__schema'].shape!=(1,) or payload['__schema'][0]!=1 or
            payload['__case'].dtype!=np.int64 or
            payload['__case'].shape!=(4,) or
            not np.array_equal(payload['__case'],middle_mesh) or
            payload['__family'].dtype!=np.int64 or
            payload['__family'].shape!=(1,) or
            payload['__family'][0]!=_FAMILY[family]):
        raise ValueError('attribution archive case/schema mismatch')
    actions={}
    shapes=_shapes(layout)
    for name in _MATRICES:
        data=payload[f'{name}.data']
        indices=payload[f'{name}.indices']
        indptr=payload[f'{name}.indptr']
        dimensions=payload[f'{name}.shape']
        target=shapes[name]
        if (data.dtype!=np.float64 or indices.dtype!=np.int64 or
                indptr.dtype!=np.int64 or dimensions.dtype!=np.int64 or
                dimensions.shape!=(2,) or tuple(dimensions)!=target or
                data.ndim!=1 or indices.ndim!=1 or indptr.ndim!=1 or
                len(data)!=len(indices) or
                len(indptr)!=target[0]+1 or indptr[0]!=0 or
                indptr[-1]!=len(data) or np.any(np.diff(indptr)<0) or
                np.any(indices<0) or np.any(indices>=target[1]) or
                not np.all(np.isfinite(data))):
            raise ValueError(f'corrupt attribution CSR {name}')
        matrix=sparse.csr_matrix((data.copy(),indices.copy(),indptr.copy()),
                                 shape=target,copy=True)
        if not matrix.has_canonical_format:
            raise ValueError(f'noncanonical attribution CSR {name}')
        actions[name]=matrix
    for name in _VECTORS:
        value=payload[name]
        if (value.dtype!=np.float64 or value.shape!=shapes[name] or
                not np.all(np.isfinite(value))):
            raise ValueError(f'corrupt attribution vector {name}')
        actions[name]=value.copy()
    _validate_actions(actions,layout)
    return actions


def _full_scales(shell_dofs: int, elements: int) -> np.ndarray:
    u=2*elements+1
    v=2*(elements+1)
    scale=np.full(shell_dofs+beam.dof_count(elements),scaling.U0)
    start=shell_dofs+u
    scale[start+1:start+v:2]=scaling.U0/scaling.L0
    scale[shell_dofs+u+v:]=scaling.U0/scaling.L0
    return scale


def _sample_shell(model: shell.Panel, q: np.ndarray, x: float,y: float
                  ) -> tuple[np.ndarray,np.ndarray]:
    nodes,weights=shell.sample(model,x,y)
    _,grad,_=shell.shape(model.nodes[list(nodes)],'Q4',(x,y))
    local=q[np.array([2*i+axis for i in nodes for axis in (0,1)])]
    return np.asarray(weights)@local.reshape(-1,2),shell.strain_matrix(grad)@local


def _sample_beam(elements: int, q: np.ndarray,s: float
                 ) -> tuple[np.ndarray,np.ndarray]:
    k=min(int(s*elements),elements-1)
    n,b=beam.fields(s*elements-k,1/elements)
    local=q[beam.element_dofs(elements,k)]
    return n@local,b@local


def _offgrid(layout: dict[str,int], qm: np.ndarray,v: np.ndarray
             ) -> tuple[float,float]:
    ns,ny,nb=layout['ns'],layout['ny'],layout['nb']
    coarse=shell.panel(ns,ny,'Q4')
    fine=shell.panel(2*ns,2*ny,'Q4')
    sf=layout['sf']; sc=layout['sc']
    field_error=0.; strain_error=0.
    points=(.211324865405187,.788675134594813)
    for j in range(ny):
        for i in range(2*ns):
            for ty in points:
                for tx in points:
                    x=-.5+(i+tx)/ns
                    y=-.5+(j+ty)/ny
                    uc,ec=_sample_shell(coarse,qm[:sc],x,y)
                    uf,ef=_sample_shell(fine,v[:sf],x,y)
                    field_error=max(field_error,float(np.max(np.abs(uc-uf))/scaling.U0))
                    strain_error=max(strain_error,float(np.max(np.abs(ec-ef))/
                                                       (scaling.U0/scaling.L0)))
    for k in range(nb):
        for xi in (.13,.37,.71,.91):
            s=(k+xi)/nb
            uc,ec=_sample_beam(nb,qm[sc:],s)
            uf,ef=_sample_beam(2*nb,v[sf:],s)
            field_scale=np.array((scaling.U0,scaling.U0,scaling.U0/scaling.L0))
            strain_scale=np.array((scaling.U0/scaling.L0,
                                   scaling.U0/scaling.L0**2,
                                   scaling.U0/scaling.L0))
            field_error=max(field_error,float(np.max(np.abs(uc-uf)/field_scale)))
            strain_error=max(strain_error,float(np.max(np.abs(ec-ef)/strain_scale)))
    return field_error,strain_error


def verify_actions(actions: dict, *, middle_mesh: tuple[int,int,int,int],
                   family: str) -> dict[str,dict[str,float]]:
    """Recompute acceptance checks and signed physical terms from saved actions."""
    layout=_layout(middle_mesh,family)
    _validate_actions(actions,layout)
    ns,ny,nb,nm=(layout[key] for key in ('ns','ny','nb','nm'))
    p,kc,kf,cf=(actions[name] for name in _MATRICES)
    fc,ff,qm,qf,lam=(actions[name] for name in
                     ('f_coarse','f_fine','q_middle','q_fine','lambda_fine'))
    v,e=(actions[name] for name in ('prolonged_q','e'))
    sc,sf=layout['sc'],layout['sf']
    coarse=shell.panel(ns,ny,'Q4'); fine=shell.panel(2*ns,2*ny,'Q4')
    fixed_c=np.r_[coarse.supported,sc+beam.root_dofs(nb)]
    fixed_f=np.r_[fine.supported,sf+beam.root_dofs(2*nb)]
    free_c=np.setdiff1d(np.arange(layout['nc']),fixed_c)
    free_f=np.setdiff1d(np.arange(layout['nf']),fixed_f)
    dc=_full_scales(sc,nb); df=_full_scales(sf,2*nb)
    h=1/(2*nm)
    measures=np.full(2*nm+1,h)
    measures[[0,-1]]*=.5
    if family=='hybrid':
        measures=np.r_[np.full(2*nm-1,h),np.ones(2)]
    elif family=='enriched':
        measures=np.r_[measures,np.ones(2)]
    row_scale=scaling.U0*np.repeat(measures,3)
    action_residuals=(
        ((p@qm)-v)/df,(v-qf-e)/df,
        ((kf@e)-actions['Kf_e'])*df/scaling.E0,
        ((cf@e)-actions['Cf_e'])/row_scale,
        ((kc@qm)-actions['Kc_qmiddle'])*dc/scaling.E0,
        ((kf@qf)-actions['Kf_qfine'])*df/scaling.E0,
        ((kf@v)-actions['Kf_prolonged_q'])*df/scaling.E0,
        ((cf@qf)-actions['Cf_qfine'])/row_scale,
        ((cf@v)-actions['Cf_prolonged_q'])/row_scale,
        ((cf.T@lam)-actions['CfT_lambda'])*df/scaling.E0,
        ((kf@qf+cf.T@lam-ff)-actions['r_fine'])*df/scaling.E0)
    action_parity=max(float(np.max(np.abs(item))) for item in action_residuals)
    support=max(float(np.max(np.abs(qm[fixed_c]))),
                float(np.max(np.abs(qf[fixed_f]))),
                float(np.max(np.abs(v[fixed_f]))),
                float(np.max(np.abs((p[fixed_f,:][:,free_c]).data),initial=0.)))
    pbar=(sparse.diags(1/df)@p@sparse.diags(dc)).tocsr()
    kcbar=(sparse.diags(dc)@kc@sparse.diags(dc))*(1/scaling.E0)
    kfbar=(sparse.diags(df)@kf@sparse.diags(df))*(1/scaling.E0)
    kd=(pbar.T@kfbar@pbar-kcbar).tocsr()
    pullback=float(np.linalg.norm(kd.data)/max(np.linalg.norm(kcbar.data),1e-30))
    fcbar=dc*fc/scaling.E0; ffbar=df*ff/scaling.E0
    fd=pbar.T@ffbar-fcbar
    load_pullback=float(np.max(np.abs(fd))/max(1.,float(np.max(np.abs(fcbar)))))
    kcq=kc@qm; kfq=kf@qf; kfv=kf@v; kfe=kf@e
    cfe=cf@e; cfq=cf@qf
    r=kfq+cf.T@lam-ff
    shell_distance=float(.5*e[:sf]@kfe[:sf]); beam_distance=float(.5*e[sf:]@kfe[sf:])
    mismatch=float(-lam@cfe); residual_work=float(e@r)
    middle_shell=float(.5*qm[:sc]@kcq[:sc]); middle_beam=float(.5*qm[sc:]@kcq[sc:])
    prolonged_shell=float(.5*v[:sf]@kfv[:sf]); prolonged_beam=float(.5*v[sf:]@kfv[sf:])
    fine_shell=float(.5*qf[:sf]@kfq[:sf]); fine_beam=float(.5*qf[sf:]@kfq[sf:])
    middle_energy=middle_shell+middle_beam
    prolonged_energy=prolonged_shell+prolonged_beam
    fine_energy=fine_shell+fine_beam
    middle_load=float(fc@qm); prolonged_load=float(ff@v); fine_load=float(ff@qf)
    pi_v=prolonged_energy-prolonged_load; pi_f=fine_energy-fine_load
    direct=pi_v-pi_f
    attributed=shell_distance+beam_distance+mismatch+residual_work
    defect=direct-attributed
    denominator=max(scaling.E0,abs(pi_v)+abs(pi_f)+
                    abs(shell_distance+beam_distance)+abs(mismatch)+abs(residual_work))
    weak=np.asarray(cfq)/row_scale
    field,strain=_offgrid(layout,qm,v)
    checks={
        'action_parity_scaled':action_parity,
        'support_preservation_max_abs':support,
        'scaled_pullback_relative_fro':pullback,
        'scaled_load_pullback_relative_inf':load_pullback,
        'shell_energy_preservation_scaled':abs(prolonged_shell-middle_shell)/scaling.E0,
        'beam_energy_preservation_scaled':abs(prolonged_beam-middle_beam)/scaling.E0,
        'load_work_preservation_scaled':abs(prolonged_load-middle_load)/scaling.E0,
        'identity_defect_scaled':abs(defect)/denominator,
        'fine_free_equilibrium_scaled':float(np.max(np.abs(df[free_f]*r[free_f]/
                                                          scaling.E0))),
        'fine_compatibility_scaled':float(np.max(np.abs(weak))),
        'offgrid_field_scaled':field,
        'offgrid_strain_scaled':strain,
    }
    attribution={
        'shell_distance_j':shell_distance,'beam_distance_j':beam_distance,
        'constraint_mismatch_work_j':mismatch,'residual_work_j':residual_work,
        'direct_potential_change_j':direct,
        'attributed_potential_change_j':attributed,
        'prolonged_fine_potential_j':pi_v,'fine_potential_j':pi_f,
        'identity_error_j':defect,'identity_denominator_j':denominator,
        'identity_defect_scaled':checks['identity_defect_scaled'],
        'middle_elastic_energy_j':middle_energy,
        'prolonged_fine_elastic_energy_j':prolonged_energy,
        'fine_elastic_energy_j':fine_energy,
        'middle_shell_energy_j':middle_shell,'middle_beam_energy_j':middle_beam,
        'prolonged_fine_shell_energy_j':prolonged_shell,
        'prolonged_fine_beam_energy_j':prolonged_beam,
        'fine_shell_energy_j':fine_shell,'fine_beam_energy_j':fine_beam,
        'shell_energy_preservation_error_j':prolonged_shell-middle_shell,
        'beam_energy_preservation_error_j':prolonged_beam-middle_beam,
        'elastic_energy_preservation_error_j':prolonged_energy-middle_energy,
        'middle_load_work_j':middle_load,
        'prolonged_fine_load_work_j':prolonged_load,
        'fine_load_work_j':fine_load,
        'load_work_preservation_error_j':prolonged_load-middle_load,
        'fixed_dof_count_coarse':len(fixed_c),'fixed_dof_count_fine':len(fixed_f),
        'prolonged_fixed_max_abs':float(np.max(np.abs(v[fixed_f]))),
        'fine_free_residual_max':float(np.max(np.abs(r[free_f]))),
        'fine_constraint_max_abs_mixed_units':float(np.max(np.abs(cfq))),
        'shell_dofs_coarse':sc,'shell_dofs_fine':sf,
        'middle_mesh':[ns,ny,nb,nm],
        'fine_mesh':[2*ns,2*ny,2*nb,2*nm],
        'family':family,
    }
    if set(checks)!=set(LIMITS) or not all(np.isfinite(list(checks.values()))):
        raise ValueError('nonfinite or incomplete attribution verification')
    return {'checks':checks,'attribution':attribution}
