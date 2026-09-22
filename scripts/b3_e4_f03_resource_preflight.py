"""Single-case assembly resource probe for the proposed classical F03 set.

This executes no physical qualification comparison. The optional solve path
measures one sparse factorization and checks its dimensionally scaled
equations without interpreting its physical response. A supervisor preserves
partial phases and stops its owned child at the preflight time/RSS envelope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import psutil
import scipy
from scipy import sparse
from scipy.sparse.linalg import splu
from threadpoolctl import threadpool_info

import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_inventory as inventory
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell


SOURCES=(Path(__file__),
         Path(beam.__file__),Path(inventory.__file__),
         Path(line.__file__),Path(shell.__file__))
MAX_RSS=8*1024**3
MAX_SECONDS=900
F0=1e6
M0=1e6
U0=F0/(shell.E*shell.THICKNESS)


def _hashes() -> dict[str,str]:
    return {str(path.resolve()):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in SOURCES}


def _mesh(value: str) -> inventory.Mesh:
    try:
        result=inventory.Mesh(*(int(item) for item in value.split(',')))
    except (TypeError,ValueError) as exc:
        raise argparse.ArgumentTypeError('mesh must be Ns,Ny,Nb,Nm') from exc
    if (not 1<=result.n_s<=128 or not 2<=result.n_y<=64 or
            not 1<=result.n_beam<=512 or not 1<=result.n_mortar<=64):
        raise argparse.ArgumentTypeError('reference mesh outside resource envelope')
    return result


def _child(mesh: inventory.Mesh, topology: str, law: str,
           manifest_path: Path, solve: bool) -> None:
    begun=time.perf_counter()
    process=psutil.Process()
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if _hashes()!=manifest['sources']:
        raise ValueError('child source hashes differ from supervisor manifest')
    if (vars(mesh)!=manifest['mesh'] or topology!=manifest['topology'] or
            law!=manifest['law'] or solve!=manifest['solve'] or
            manifest['loading']!=('smooth' if solve else None) or
            manifest['scales']!=dict(force_newton=F0,moment_newton_metre=M0,
                                     displacement_metre=U0)):
        raise ValueError('child case differs from supervisor manifest')
    if any(os.environ.get(name)!=value for name,value in manifest['threads'].items()):
        raise ValueError('child thread environment differs from manifest')

    def phase(name: str, **counts: int | float | bool | None) -> None:
        print(json.dumps(dict(phase=name,elapsed_seconds=time.perf_counter()-begun,
                              rss_bytes=process.memory_info().rss,**counts),
                         sort_keys=True),flush=True)

    pools=threadpool_info()
    print(json.dumps(dict(phase='identity',sources=_hashes(),
                          modules={name:str(Path(module.__file__).resolve())
                                   for name,module in (('numpy',np),('scipy',scipy),
                                                       ('psutil',psutil))},
                          threadpools=pools,
                          threads={name:os.environ.get(name)
                                   for name in manifest['threads']}),sort_keys=True),
          flush=True)
    if any(pool.get('num_threads')!=1 for pool in pools):
        raise ValueError('observed child thread pool is not single-threaded')
    model=shell.panel(mesh.n_s,mesh.n_y,topology)
    phase('panel',**inventory.structural_counts(mesh,topology,law))
    ks=shell.stiffness(model)
    phase('shell_stiffness',shell_nnz=ks.nnz)
    kb=beam.assembled_stiffness(mesh.n_beam)
    phase('beam_stiffness',beam_nnz=kb.nnz)
    cs,cb,knots=line.coupling(model,mesh.n_beam,mesh.n_mortar,law)
    phase('coupling',shell_trace_nnz=cs.nnz,beam_trace_nnz=cb.nnz,
          overlay_intervals=len(knots)-1)
    c=sparse.hstack((-cs,cb),format='csr')
    k=sparse.block_diag((ks,kb),format='csr')
    supported=np.r_[model.supported,
                    model.dof_count+beam.root_dofs(mesh.n_beam)]
    free=np.setdiff1d(np.arange(k.shape[0]),supported)
    a=sparse.bmat(((k[free,:][:,free],c[:,free].T),
                   (c[:,free],None)),format='csc')
    phase('unfactorized_kkt',kkt_nnz=a.nnz,kkt_dimension=a.shape[0],
          physical_free=len(free),multiplier_rows=c.shape[0])
    if solve:
        # This is an algebraic factorization/resource probe. Do not export
        # displacements or interpret a physical response before registration.
        load=beam.assembled_load(mesh.n_beam,'smooth')
        force=np.r_[np.zeros(model.dof_count),load]
        rhs=np.r_[force[free],np.zeros(c.shape[0])]
        factors=splu(a)
        phase('factorized',l_nnz=factors.L.nnz,u_nnz=factors.U.nnz,
              factor_nnz=factors.L.nnz+factors.U.nnz)
        solution=factors.solve(rhs)
        if not np.all(np.isfinite(solution)):
            phase('linear_solve',solution_finite=False,
                  scaled_free_residual_max=None,scaled_weak_residual_max=None)
            raise ValueError('nonfinite factorized reference response')
        residual=a@solution-rhs
        nfree=len(free)
        local=free-model.dof_count
        u=2*mesh.n_beam+1
        v=2*(mesh.n_beam+1)
        moment=(local>=u+v) | ((local>=u)&(local<u+v)&((local-u)%2==1))
        scale=np.where(moment,M0,F0)
        free_max=float(np.max(np.abs(residual[:nfree])/scale))
        tests=mesh.n_mortar+(law=='P1')
        measure=np.full(tests,1/mesh.n_mortar)
        if law=='P1':
            measure[[0,-1]]*=.5
        weak_scale=U0*np.repeat(measure,3)
        weak_max=float(np.max(np.abs(residual[nfree:])/weak_scale))
        phase('linear_solve',solution_finite=True,
              scaled_free_residual_max=free_max if np.isfinite(free_max) else None,
              scaled_weak_residual_max=weak_max if np.isfinite(weak_max) else None)
        if (not np.isfinite(free_max) or not np.isfinite(weak_max) or
                free_max>1e-8 or weak_max>1e-9):
            raise ValueError(f'large scaled KKT residual: free={free_max}, weak={weak_max}')
    if _hashes()!=manifest['sources']:
        raise ValueError('child source changed during assembly')


def _supervise(mesh: inventory.Mesh, topology: str, law: str,
               directory: Path, solve: bool = False) -> int:
    checkout=Path(__file__).resolve().parents[1]
    def git(*args: str) -> str:
        return subprocess.run(('git',*args),cwd=checkout,check=True,
                              capture_output=True,text=True).stdout.strip()
    commit=git('rev-parse','HEAD')
    dirty=git('status','--porcelain')
    proposed=mesh in inventory.meshes()
    if proposed and dirty:
        raise ValueError('proposed inventory resource probe requires clean frozen source')
    directory.mkdir(parents=True,exist_ok=False)
    sources=_hashes()
    manifest_path=directory/'manifest.json'
    command=[sys.executable,'-u',str(Path(__file__).resolve()),
             '--child','--mesh',f'{mesh.n_s},{mesh.n_y},{mesh.n_beam},{mesh.n_mortar}',
             '--topology',topology,'--law',law,
             '--expected-manifest',str(manifest_path.resolve())]
    if solve:
        command.append('--solve')
    environment=os.environ.copy()
    environment.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',
                       MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',
                       PYTHONDONTWRITEBYTECODE='1')
    manifest=dict(purpose=('factorization F03 classical resource preflight' if solve
                           else 'assembly-only F03 classical resource preflight'),
                  mesh=vars(mesh),topology=topology,law=law,
                  solve=solve,loading='smooth' if solve else None,
                  scales=dict(force_newton=F0,moment_newton_metre=M0,
                              displacement_metre=U0),
                  assembly_identity=(f'{topology}-{law}-Ns{mesh.n_s}-Ny{mesh.n_y}-'
                                     f'Nb{mesh.n_beam}-Nm{mesh.n_mortar}'),
                  proposed_inventory_mesh=proposed,
                  source_commit=commit,source_dirty=bool(dirty),
                  limits=dict(max_rss_bytes=MAX_RSS,max_seconds=MAX_SECONDS),
                  command=command,sources=sources,python=sys.version,
                  numpy=np.__version__,scipy=scipy.__version__,
                  psutil=psutil.__version__,platform=platform.platform(),
                  cpu_count=os.cpu_count(),available_bytes=psutil.virtual_memory().available,
                  threads={name:environment[name] for name in
                           ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS',
                            'MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')})
    manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True),
                             encoding='utf-8')
    begun=time.monotonic(); peak=0; reason='process_exit'
    exit_code=None; failure=None; child=None; records=[]; malformed=[]
    try:
        with (directory/'phases.jsonl').open('wb') as stdout, \
             (directory/'stderr.log').open('wb') as stderr, \
             (directory/'rss.jsonl').open('w',encoding='utf-8') as samples:
            child=subprocess.Popen(command,stdout=stdout,stderr=stderr,env=environment,
                                   cwd=checkout)
            tracked=psutil.Process(child.pid)
            while child.poll() is None:
                elapsed=time.monotonic()-begun
                try:
                    rss=tracked.memory_info().rss
                except psutil.NoSuchProcess:
                    rss=0
                peak=max(peak,rss)
                samples.write(json.dumps(dict(elapsed_seconds=elapsed,rss_bytes=rss))+'\n')
                if rss>MAX_RSS or elapsed>MAX_SECONDS:
                    reason='rss_limit' if rss>MAX_RSS else 'time_limit'
                    child.kill()
                    break
                time.sleep(.1)
    except BaseException as exc:
        reason='supervisor_error'
        failure=f'{type(exc).__name__}: {exc}'
    finally:
        if child is not None:
            if child.poll() is None:
                child.kill()
            exit_code=child.wait()
        phase_path=directory/'phases.jsonl'
        if phase_path.exists():
            for number,entry in enumerate(phase_path.read_text(encoding='utf-8',errors='replace').splitlines(),1):
                try:
                    records.append(json.loads(entry))
                except (ValueError,TypeError):
                    malformed.append(number)
        post_hashes=_hashes()
        identities=[record for record in records if record.get('phase')=='identity']
        peak=max([peak]+[record.get('rss_bytes',0) for record in records])
        elapsed=time.monotonic()-begun
        if reason=='process_exit':
            if peak>MAX_RSS:
                reason='rss_limit'
            elif elapsed>MAX_SECONDS:
                reason='time_limit'
            elif (exit_code!=0 or malformed or len(identities)!=1 or
                  identities[0].get('sources')!=sources or
                  identities[0].get('threads')!=manifest['threads'] or
                  any(pool.get('num_threads')!=1 for pool in
                      identities[0].get('threadpools',[])) or
                  not identities[0].get('modules') or
                  post_hashes!=sources or not records or
                  records[-1].get('phase')!=
                  ('linear_solve' if solve else 'unfactorized_kkt')):
                reason='identity_or_phase_failure'
        result=dict(reason=reason,exit_code=exit_code,
                    elapsed_seconds=elapsed,
                    sampled_peak_rss_bytes=peak,
                    completed_phases=[record.get('phase') for record in records],
                    malformed_phase_lines=malformed,post_source_hashes=post_hashes,
                    failure=failure)
        (directory/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True),
                                             encoding='utf-8')
    print(json.dumps(dict(evidence=str(directory.resolve()),reason=reason,
                          exit_code=exit_code,elapsed_seconds=elapsed,
                          sampled_peak_rss_bytes=peak,
                          completed_phases=result['completed_phases']),sort_keys=True))
    return 0 if reason=='process_exit' and exit_code==0 else 1


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--mesh',type=_mesh,required=True)
    parser.add_argument('--topology',choices=('Q4','CST'),required=True)
    parser.add_argument('--law',choices=('P0','P1'),required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--solve',action='store_true',
                        help='also factor and solve a smooth-load algebraic system')
    parser.add_argument('--child',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--expected-manifest',type=Path,help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.child:
        if args.expected_manifest is None:
            parser.error('--expected-manifest is required for child')
        _child(args.mesh,args.topology,args.law,args.expected_manifest,args.solve)
        return 0
    if args.output is None:
        parser.error('--output is required for supervised execution')
    return _supervise(args.mesh,args.topology,args.law,args.output,args.solve)


if __name__=='__main__':
    raise SystemExit(main())
