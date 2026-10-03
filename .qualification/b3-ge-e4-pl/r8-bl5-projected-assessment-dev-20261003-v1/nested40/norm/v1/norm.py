"""Register a four-shell-interval density, then assess its saved auxiliary norm.

Exact nested subspaces reuse complete all-column lower/upper Grams. Independent
physical density integrals verify the nesting. No mechanical inverse or new mesh.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import linalg
from threadpoolctl import threadpool_info

IDENTITY='BL5_PROJECTED_AFFINE_FOUR_SHELL_INTERVALS_COARSE_DEV_V1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def nesting():
    a=np.zeros((16,8))
    for pair in range(4):
        a[4*pair:4*pair+4,2*pair]=(1.,0.,1.,0.)
        a[4*pair:4*pair+4,2*pair+1]=(-.5,.5,.5,.5)
    p=np.zeros((32,8))
    for cell in range(32):
        j=cell//8
        p[cell,2*j]=1.
        p[cell,2*j+1]=float(2*(Fraction(2*cell+1,64)-Fraction(j,4))/Fraction(1,4)-1)
    full=linalg.block_diag(a,a,a,a,a)
    return a,p,full


def eigen(g,m):
    skew=max(np.linalg.norm(g-g.T)/np.linalg.norm(g),np.linalg.norm(m-m.T)/np.linalg.norm(m))
    if skew>1e-10: raise ArithmeticError('congruent Gram symmetry unresolved')
    values,vectors=linalg.eigh(g,m)
    residual=float(np.linalg.norm(g@vectors-(m@vectors)*values)/np.linalg.norm(g@vectors))
    return values,residual,float(skew)


def register(inputs,output):
    with np.load(inputs/'scalar.npz',allow_pickle=False) as z:
        old={name:z[name].copy() for name in z.files}
    scalar=json.loads((inputs/'scalar.json').read_text())
    if scalar['fixture']!=dict(nx=16,ny=4,halfcells=32,supports=8):
        raise ValueError('saved coarse fixture required')
    a,p,full=nesting()
    np.testing.assert_array_equal(old['projection']@a,p)
    g=a.T@old['discrete_lower']@a
    lower=a.T@old['reference_lower']@a;upper=a.T@old['reference_upper']@a
    mass=p.T@p/32
    expected=np.tile((.25,21/256),4)
    np.testing.assert_array_equal(mass,np.diag(expected))
    d=np.diag(1/np.sqrt(expected))
    vals,residual,skew=eigen(d@upper@d,d@g@d)
    cs2=float(vals[-1]);rho=np.hypot(.05,.05)/.4
    product2=max(2*cs2,max(2.,1+2*rho*rho)*max(2*cs2,1+rho*rho))
    safe=float(1/np.sqrt(product2)/np.sqrt(1.001)-1e-6)
    error=float(linalg.eigvalsh(upper-lower,lower)[-1])
    cond=dict(discrete=float(np.linalg.cond(d@g@d)),reference=float(np.linalg.cond(d@upper@d)))
    # Verify endpoints and interior quarter-support action with rational hats,
    # independently of either saved constraint matrix or nested Grams.
    from scripts.r8_bl5_projected_reference_action_dev import integrated_projected_weights
    exact=np.zeros((17,8))
    for j in range(4):
        weights,_=integrated_projected_weights(Fraction(j,4),Fraction(j+1,4),16,32)
        for degree,rows in enumerate(weights):
            for node,w in rows.items():exact[node,2*j+degree]=float(w)
    # Supported scalar action has80 rows: x-fast ordering, x=0 omitted.
    action=old['action']@a
    np.testing.assert_allclose(action[:16],exact[1:],rtol=0.,atol=1e-13)
    assert np.max(np.abs(action[16:]))==0.
    assert np.all(exact[np.arange(4)*4+1,np.arange(4)*2+1]!=0.)
    assert np.all(exact[np.arange(4)*4+3,np.arange(4)*2+1]!=0.)
    predicates=dict(positive_complete_scalar_space=bool(np.all(vals>0)),
        reference_error=error<=1e-3,eigen_residual=residual<=1e-10,symmetry=skew<=1e-10,
        physical_L2_condition=max(cond.values())<=1e4)
    record=dict(status='REGISTERED_COARSE_DEVELOPMENT_BOUND' if all(predicates.values()) else 'UNRESOLVED_COARSE_BOUND',
        identity=IDENTITY,source_sha256=sha(__file__),source_inputs={n:sha(inputs/n) for n in ('scalar.json','scalar.npz')},
        old_scalar_status=scalar['status'],predicates=predicates,conditions=cond,
        cs_squared_upper=cs2,safe_case_floor=safe,scalar_relative_reference_error=error,
        scalar_eigen_residual=residual,all_scalar_eigenvalues=vals.tolist(),
        physical_L2_basis_scale=np.diag(d).tolist(),
        fixed_criteria=dict(reference_error=1e-3,inverse_eigen_symmetry=1e-10,
            condition_budget=1e4,arithmetic_beta_margin=1e-6,variational_ceiling=(1+1e-6)**2),
        limitations='same coarse fixture; sufficient scalar product bound only, not policy/growing-family/F03 selection')
    np.savez(output.with_suffix('.npz'),scalar_nesting=a,physical_nesting=full,
             scalar_lower=g,reference_lower=lower,reference_upper=upper,projection=p,
             scalar_action=action,independent_endpoint_action=exact,density_L2_scale=d)
    record['arrays_sha256']=sha(output.with_suffix('.npz'))
    record['rational_work_helper_sha256']=sha(integrated_projected_weights.__code__.co_filename)
    output.write_text(json.dumps(record,indent=2)+'\n')
    return record


def assess(inputs,registration,output):
    record=json.loads(registration.read_text())
    if record['status']!='REGISTERED_COARSE_DEVELOPMENT_BOUND' or record['identity']!=IDENTITY:
        raise ValueError('eligible distinct nested registration required')
    if record['source_sha256']!=sha(__file__) or record['arrays_sha256']!=sha(registration.with_suffix('.npz')):
        raise ValueError('changed registered source/arrays')
    if record['fixed_criteria']!=dict(reference_error=1e-3,inverse_eigen_symmetry=1e-10,
        condition_budget=1e4,arithmetic_beta_margin=1e-6,variational_ceiling=(1+1e-6)**2):
        raise ValueError('changed registered numerical criteria')
    parent=json.loads((inputs/'physical-v3.json').read_text())
    if parent['status']!='COMPLETED_COARSE_DEVELOPMENT_ONLY' or not all(parent['predicates'].values()):
        raise ValueError('ineligible saved physical dual')
    for n,h in record['source_inputs'].items():
        if sha(inputs/n)!=h:raise ValueError('changed scalar source')
    a,p,A=nesting();d=np.diag(np.tile(record['physical_L2_basis_scale'],5))
    with np.load(registration.with_suffix('.npz'),allow_pickle=False) as z:
        np.testing.assert_array_equal(z['physical_nesting'],A)
        floor_values=linalg.eigvalsh(z['reference_upper'],z['scalar_lower'])
        cs2=float(floor_values[-1]);rho=np.hypot(.05,.05)/.4
        derived=max(2*cs2,max(2.,1+2*rho*rho)*max(2*cs2,1+rho*rho))
        if abs(record['safe_case_floor']-(1/np.sqrt(derived)/np.sqrt(1.001)-1e-6))>1e-12:
            raise ValueError('changed registered product bound')
        np.testing.assert_allclose(d.diagonal(),np.tile(1/np.sqrt(np.diag(p.T@p/32)),5),atol=1e-14,rtol=0.)
    with np.load(inputs/'physical-v3.npz',allow_pickle=False) as z:
        g=A.T@z['native_lower']@A
        ml=A.T@z['reference_lower']@A;mu=A.T@z['reference_upper']@A
        physical_density=np.einsum('cij,jk->cik',z['physical_density'],A)
        physical_action=z['all_column_work']@A
        oldg=z['native_lower'].copy();oldm=z['reference_upper'].copy()
    # Every channel uses exactly the same physical projected density space.
    expected=np.zeros((32,5,40))
    for channel,q in enumerate((1.,1.,1.,.4,.4)):
        expected[:,channel,8*channel:8*(channel+1)]=q*p
    np.testing.assert_array_equal(physical_density,expected)
    values,residual,skew=eigen(d@g@d,d@mu@d)
    error=float(linalg.eigvalsh(mu-ml,ml)[-1])
    conditions=dict(native=float(np.linalg.cond(d@g@d)),reference=float(np.linalg.cond(d@mu@d)))
    beta=float(np.sqrt(values[0])) if values[0]>0 else None
    safe=record['safe_case_floor']
    # Nested variational interlacing: no reduced physical kernel claim follows.
    oldvals=linalg.eigvalsh(oldg,oldm)
    interlace=bool(values[0]>=oldvals[0]-1e-10 and values[-1]<=oldvals[-1]+1e-10)
    predicates=dict(reference_error=error<=1e-3,eigen_residual=residual<=1e-10,
        symmetry=skew<=1e-10,condition=max(conditions.values())<=1e4,
        positive_all_modes=bool(np.all(values>0)),nested_interlacing=interlace,
        product_floor=beta is not None and beta>=safe,
        variational_upper_bound=bool(values[-1]<=(1+1e-6)**2))
    result=dict(status='COMPLETED_COARSE_DEVELOPMENT_ONLY' if all(predicates.values()) else 'UNRESOLVED_COARSE_CHECK',
        identity=IDENTITY,predicates=predicates,beta=beta,safe_case_floor=safe,conditions=conditions,
        reference_error=error,eigen_residual=residual,gram_skew=skew,
        all_generalized_eigenvalues=values.tolist(),old_beta=float(np.sqrt(oldvals[0])),
        source_sha256=sha(__file__),registration_sha256=sha(registration),
        input_sha256={n:sha(inputs/n) for n in ('physical-v3.json','physical-v3.npz')},
        limitations='weaker40-row constraints, not a representation-only correction; mechanical kernel and transfer must be checked separately; no space/F03 qualification')
    np.savez(output.with_suffix('.npz'),native_lower=g,reference_lower=ml,reference_upper=mu,
             physical_density=physical_density,physical_action=physical_action,nesting=A)
    output.write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=('register','assess'))
    parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--registration',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or args.output.with_suffix('.npz').exists():raise FileExistsError(args.output)
    pools=threadpool_info()
    if not pools or any(p['num_threads']!=1 for p in pools):raise RuntimeError('effective one-thread pools required')
    r=register(args.inputs,args.output) if args.stage=='register' else assess(args.inputs,args.registration,args.output)
    print(json.dumps({key:r[key] for key in ('status','safe_case_floor','conditions')}|({'beta':r['beta']} if 'beta'in r else {'cs_squared_upper':r['cs_squared_upper']})))
    raise SystemExit(0 if all(r['predicates'].values()) else 1)
