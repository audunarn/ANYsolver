"""Installed public owner versus saved nested coarse operators and solutions."""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import zipfile

import anysolver
from anysolver import stiffened_shell as api
import numba
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_info

from scripts.b3_e4_bl5_coherent_aggregation_dev import model,physical_transfer,LOADS
from scripts.r8_bl5_nested_projected_kernel_dev import saved_csr,relative
from scripts.r8_bl5_affine_flexible_native_dev import exact_transfer_moments

# The runtime requires the exact artifact declared by the caller and verifies
# source/wheel/site bytes, rather than rebuilding an artifact for this check.
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def evaluate(site,wheel,source,old_root,kernel,output):
    if output.exists():raise FileExistsError(output)
    if not Path(anysolver.__file__).resolve().is_relative_to(site.resolve()):
        raise ValueError('declared installed package required')
    modules={}
    source_files={'anysolver/'+p.relative_to(source/'src/anysolver').as_posix():p
                  for p in (source/'src/anysolver').rglob('*.py')}
    with zipfile.ZipFile(wheel) as z:
        names={n for n in z.namelist() if n.startswith('anysolver/') and n.endswith('.py')}
        if len(names)!=417 or names!=set(source_files):raise ValueError('complete417-module graph required')
        for name in sorted(names):
            raw=z.read(name)
            if raw!=(site/name).read_bytes() or raw!=source_files[name].read_bytes():
                raise ValueError('module identity mismatch: '+name)
            modules[name]=hashlib.sha256(raw).hexdigest()
    previous=json.loads(kernel.read_text())
    if previous['status']!='COMPLETED_DEVELOPMENT_ONLY' or not all(previous['predicates'].values()):
        raise ValueError('completed enlarged-kernel evidence required')
    with np.load(old_root/'native/operators.npz',allow_pickle=False) as z:
        old_k=saved_csr(z,'K',(1092,1092));fixed=z['fixed'].copy();free=z['free'].copy()
    with np.load(kernel.with_suffix('.npz'),allow_pickle=False) as z:
        expected_c=saved_csr(z,'C',(40,1092));x=z['physical_slots'].copy();pp=z['resultant_slots'].copy()
        saved={case:{key:z[case+'_'+key].copy() for key in ('q','multipliers','reactions','load')}
               for case in LOADS}
    base,policy=model(16,4,32,2,basis='discontinuous_p1')
    line=replace(base.lines[0],basis='discontinuous_p1_cell_average',multiplier_span=8)
    definition=replace(base,lines=(line,))
    owner=api.create_analysis(definition=definition)
    try:
        if owner.capabilities['status']!='EXPERIMENTAL_NOT_QUALIFIED':raise ValueError('qualification boundary changed')
        np.testing.assert_array_equal(owner._fixed,fixed)
        np.testing.assert_array_equal(owner._free,free)
        k_error=float(sparse.linalg.norm(owner._K-old_k)/max(1.,sparse.linalg.norm(old_k)))
        c_error=float(sparse.linalg.norm(owner._C-expected_c)/max(1.,sparse.linalg.norm(expected_c)))
        if max(k_error,c_error)>1e-12:raise ArithmeticError('installed nested operator mismatch')
        cases={};states={}
        for case,wrench in LOADS.items():
            result=owner.solve_linear((api.NodalAction('beam',owner._beam_ids[-1],wrench),))
            q=np.r_[result.shell_displacement,result.beam_coordinates]
            check=saved[case]
            parity=dict(physical=relative(q[x]/owner._coordinate_scale[x],check['q'][x]/owner._coordinate_scale[x]),
                resultants=relative(q[pp]/owner._coordinate_scale[pp],check['q'][pp]/owner._coordinate_scale[pp]),
                multipliers=relative(result.multipliers,check['multipliers']),
                reactions=relative(result.reactions*owner._coordinate_scale,check['reactions']*owner._coordinate_scale))
            recovered=physical_transfer(owner,result)
            exact=exact_transfer_moments(recovered['station_records'])
            work=float(q@check['load'])
            cases[case]=dict(parity=parity,equilibrium=result.free_equilibrium_ratio,
                weak_gap=result.constraint_max,work_J=work,physical_transfer=recovered,
                exact_transfer_moments=exact)
            states.update({case+'_q':q,case+'_multipliers':result.multipliers,
                           case+'_reactions':result.reactions,case+'_load':check['load']})
        np.savez(output.with_suffix('.npz'),**states)
        predicates=dict(operator_parity=max(k_error,c_error)<=1e-12,
            solve_parity=all(max(v['parity'].values())<=1e-10 for v in cases.values()),
            equilibrium=all(v['equilibrium']<=1e-8 for v in cases.values()),
            weak_gap=all(v['weak_gap']<=1e-9 for v in cases.values()),
            one_factorization=owner._linear_factorizations==1,
            one_accurate_correction_per_case=owner._linear_refinements==3)
        result=dict(status='COMPLETED_INSTALLED_DEVELOPMENT_ONLY' if all(predicates.values()) else 'UNRESOLVED_INSTALLED_CHECK',
            identity='BL5_P1_discontinuous_cell_average_span_8',policy='four shell intervals, complete five-channel pair, same coarse model',
            predicates=predicates,cases=cases,operator_parity=dict(K=k_error,C=c_error),
            factorization_count=owner._linear_factorizations,accurate_refinements=owner._linear_refinements,
            imported_anysolver=anysolver.__file__,wheel_sha256=sha(wheel),module_sha256=modules,
            source_sha256=sha(__file__),helper_sha256={Path(f.__code__.co_filename).name:sha(f.__code__.co_filename)
                for f in (model,physical_transfer,saved_csr,exact_transfer_moments)},
            input_sha256=dict(kernel_json=sha(kernel),kernel_npz=sha(kernel.with_suffix('.npz'))),
            numba_threads=numba.get_num_threads(),jit_disabled=bool(numba.config.DISABLE_JIT),pools=threadpool_info(),
            limitations='one installed coarse reference-linear owner; no transfer accuracy, growing-space, nonlinear/material-envelope or F03 qualification')
        output.write_text(json.dumps(result,indent=2)+'\n')
        return result
    finally:owner.close()


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for arg in ('site','wheel','source','old-root','kernel','output'):p.add_argument('--'+arg,type=Path,required=True)
    p.add_argument('--wheel-sha',required=True)
    args=p.parse_args()
    if sha(args.wheel)!=args.wheel_sha:raise ValueError('frozen artifact hash mismatch')
    if args.output.exists() or args.output.with_suffix('.npz').exists():raise FileExistsError(args.output)
    if numba.get_num_threads()!=1 or not numba.config.DISABLE_JIT or any(r['num_threads']!=1 for r in threadpool_info()):
        raise RuntimeError('effective one-thread/JIT-off settings required')
    r=evaluate(args.site,args.wheel,args.source,args.old_root,args.kernel,args.output)
    print(json.dumps({key:r[key] for key in ('status','operator_parity','factorization_count','predicates')}))
    raise SystemExit(0 if all(r['predicates'].values()) else 1)
