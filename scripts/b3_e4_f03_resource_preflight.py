"""Single-case assembly resource probe for the proposed classical F03 set.

This executes no physical qualification comparison. The optional loaded path
records full classical response diagnostics as a resource and balance screen;
they are not acceptance of a physical reference. A supervisor preserves
partial phases and stops its owned child at the preflight time/RSS envelope.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import zipfile

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
import _b3_e4_f03_kkt_scaling as scaling
import _b3_e4_f03_loaded_preflight as loaded
import _b3_e4_f03_gap_enclosure as enclosure


SOURCES=(Path(__file__),
         Path(beam.__file__),Path(inventory.__file__),
         Path(line.__file__),Path(shell.__file__),Path(scaling.__file__),
         Path(loaded.__file__),Path(enclosure.__file__))
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
            not 1<=result.n_beam<=512 or not 1<=result.n_mortar<=128):
        raise argparse.ArgumentTypeError('reference mesh outside resource envelope')
    return result


def _state_phases(topology: str, trace_topology: str) -> list[str]:
    phases=['identity','panel']
    if topology!=trace_topology:
        phases.append('trace_panel')
    return phases+['shell_stiffness','beam_stiffness','coupling',
                   'unfactorized_kkt','scaled_kkt','factorized','linear_solve',
                   'state_payload','loaded_observables']


def _valid_state_phases(records: list[dict], topology: str,
                        trace_topology: str) -> bool:
    return [record.get('phase') for record in records]==_state_phases(
        topology,trace_topology)


def _valid_state_payload(directory: Path, records: list[dict],
                         mesh: inventory.Mesh, law: str) -> bool:
    payload_records=[record for record in records if record.get('phase')=='state_payload']
    payload_path=directory/'solved_state.npz'
    if len(payload_records)!=1 or not payload_path.is_file():
        return False
    try:
        record=payload_records[0]
        if (record.get('path')!=payload_path.name or
                hashlib.sha256(payload_path.read_bytes()).hexdigest()!=record.get('sha256')):
            return False
        with np.load(payload_path,allow_pickle=False) as saved:
            q=saved['physical_q']; lam=saved['physical_lambda']
        return bool(q.shape==(2*(2*mesh.n_s+1)*(mesh.n_y+1)+
                              beam.dof_count(mesh.n_beam),) and
                    lam.shape==(3*(mesh.n_mortar+(law=='P1')),) and
                    q.dtype==np.dtype('float64') and
                    lam.dtype==np.dtype('float64') and
                    record.get('q_shape')==list(q.shape) and
                    record.get('lambda_shape')==list(lam.shape) and
                    record.get('q_dtype')=='float64' and
                    record.get('lambda_dtype')=='float64' and
                    q.flags.c_contiguous and lam.flags.c_contiguous and
                    np.all(np.isfinite(q)) and np.all(np.isfinite(lam)) and
                    hashlib.sha256(q.tobytes()).hexdigest()==record.get('q_sha256') and
                    hashlib.sha256(lam.tobytes()).hexdigest()==record.get('lambda_sha256'))
    except (OSError,ValueError,KeyError,EOFError,TypeError,IndexError,
            zipfile.BadZipFile):
        return False


def _child(mesh: inventory.Mesh, topology: str, law: str,
           manifest_path: Path, solve: bool, scaled: bool,
           loaded_probe: bool, trace_topology: str | None = None,
           state_payload: bool = False) -> None:
    begun=time.perf_counter()
    process=psutil.Process()
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if _hashes()!=manifest['sources']:
        raise ValueError('child source hashes differ from supervisor manifest')
    if (vars(mesh)!=manifest['mesh'] or topology!=manifest['topology'] or
            law!=manifest['law'] or solve!=manifest['solve'] or
            scaled!=manifest['scaled'] or
            loaded_probe!=manifest['loaded_probe'] or
            (trace_topology or topology)!=manifest['trace_topology'] or
            state_payload!=manifest['state_payload'] or
            manifest['loading']!=('smooth' if solve else None) or
            manifest['scales']!=dict(force_newton=F0,moment_newton_metre=M0,
                                     displacement_metre=U0)):
        raise ValueError('child case differs from supervisor manifest')
    if any(os.environ.get(name)!=value for name,value in manifest['threads'].items()):
        raise ValueError('child thread environment differs from manifest')

    def phase(name: str, **counts: int | float | bool | None) -> None:
        print(json.dumps(dict(phase=name,elapsed_seconds=time.perf_counter()-begun,
                              rss_bytes=process.memory_info().rss,**counts),
                         sort_keys=True,allow_nan=False),flush=True)

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
    trace_model=(model if trace_topology is None or trace_topology==topology else
                 shell.panel(mesh.n_s,mesh.n_y,trace_topology))
    if (not np.array_equal(model.nodes,trace_model.nodes) or
            not np.array_equal(model.supported,trace_model.supported) or
            model.dof_count!=trace_model.dof_count):
        raise ValueError('mixed trace panel must have identical numbered nodes and supports')
    if trace_model is not model:
        phase('trace_panel',trace_topology=trace_model.topology,
              trace_elements=len(trace_model.elements))
    ks=shell.stiffness(model)
    phase('shell_stiffness',shell_nnz=ks.nnz)
    kb=beam.assembled_stiffness(mesh.n_beam)
    phase('beam_stiffness',beam_nnz=kb.nnz)
    cs,cb,knots=line.coupling(trace_model,mesh.n_beam,mesh.n_mortar,law)
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
        # The optional loaded route records physical observables for resource
        # feasibility only; full reference acceptance remains unregistered.
        load=beam.assembled_load(mesh.n_beam,'smooth')
        force=np.r_[np.zeros(model.dof_count),load]
        physical_rhs=np.r_[force[free],np.zeros(c.shape[0])]
        if scaled:
            transformed=scaling.build(k,c,force,free,model.dof_count,
                                      mesh.n_beam,mesh.n_mortar,law)
            solve_matrix=transformed.matrix; rhs=transformed.rhs
            phase('scaled_kkt',scaled_nnz=solve_matrix.nnz,
                  scaled_dimension=solve_matrix.shape[0])
        else:
            solve_matrix=a; rhs=physical_rhs
        factors=splu(solve_matrix)
        phase('factorized',l_nnz=factors.L.nnz,u_nnz=factors.U.nnz,
              factor_nnz=factors.L.nnz+factors.U.nnz,
              diagonal_scaling=scaled)
        solution=factors.solve(rhs)
        if not np.all(np.isfinite(solution)):
            phase('linear_solve',solution_finite=False,
                  scaled_free_residual_max=None,scaled_weak_residual_max=None)
            raise ValueError('nonfinite factorized reference response')
        if scaled:
            physical_q,physical_lambda=transformed.recover(solution)
            physical=np.r_[physical_q,physical_lambda]
        else:
            physical=solution
        residual=a@physical-physical_rhs
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
        equation=float(np.linalg.norm(solve_matrix@solution-rhs)/
                       max(np.linalg.norm(rhs),1.))
        phase('linear_solve',solution_finite=True,
              dimensionless_equation_residual=(equation if scaled and np.isfinite(equation)
                                               else None),
              mixed_unit_algebraic_residual=(equation if not scaled and
                                             np.isfinite(equation) else None),
              scaled_free_residual_max=free_max if np.isfinite(free_max) else None,
              scaled_weak_residual_max=weak_max if np.isfinite(weak_max) else None)
        if (not np.isfinite(equation) or not np.isfinite(free_max) or
                not np.isfinite(weak_max) or
                free_max>1e-8 or weak_max>1e-9):
            raise ValueError(f'large scaled KKT residual: equation={equation}, '
                             f'free={free_max}, weak={weak_max}')
        if loaded_probe:
            qfree,lam=transformed.recover(solution)
            if state_payload:
                full_q=np.zeros(k.shape[0],dtype=np.float64)
                full_q[free]=qfree
                payload=manifest_path.parent/'solved_state.npz'
                np.savez(payload,physical_q=full_q,
                         physical_lambda=np.ascontiguousarray(lam,dtype=np.float64))
                phase('state_payload',path=payload.name,
                      sha256=hashlib.sha256(payload.read_bytes()).hexdigest(),
                      q_shape=list(full_q.shape),lambda_shape=list(lam.shape),
                      q_dtype=str(full_q.dtype),lambda_dtype=str(lam.dtype),
                      q_sha256=hashlib.sha256(full_q.tobytes()).hexdigest(),
                      lambda_sha256=hashlib.sha256(np.ascontiguousarray(lam).tobytes()).hexdigest())
            observables=loaded.recover_solved(
                trace_model,mesh.n_beam,mesh.n_mortar,law,8,
                ks,kb,cs,cb,k,c,force,free,qfree,lam)
            phase('loaded_observables',**asdict(observables))
            if (not all(np.isfinite(observables.global_balance_scaled)) or
                    max(abs(value) for value in observables.global_balance_scaled)>1e-8 or
                    abs(observables.energy_identity_joule)/scaling.E0>1e-8 or
                    abs(observables.interface_work_joule)/scaling.E0>1e-8):
                raise ValueError('large loaded classical physical balance discrepancy')
    if _hashes()!=manifest['sources']:
        raise ValueError('child source changed during assembly')


def _supervise(mesh: inventory.Mesh, topology: str, law: str,
               directory: Path, solve: bool = False,
               scaled: bool = False, loaded_probe: bool = False,
               trace_topology: str | None = None,
               state_payload: bool = False) -> int:
    if scaled and not solve:
        raise ValueError('diagonal scaling requires a solve probe')
    if loaded_probe and not (solve and scaled):
        raise ValueError('loaded preflight requires scaled solve and supervisor')
    if trace_topology not in (None,'Q4','CST-CB'):
        raise ValueError('unadmitted diagnostic trace topology')
    if state_payload and topology not in ('Q4','CST-CB'):
        raise ValueError('diagnostic payload is restricted to Q4/CST-CB')
    if state_payload and not loaded_probe:
        raise ValueError('solved-state payload requires loaded probe')
    if trace_topology not in (None,topology) and not state_payload:
        raise ValueError('mixed operator diagnostic requires solved-state payload')
    checkout=Path(__file__).resolve().parents[1]
    def git(*args: str) -> str:
        return subprocess.run(('git',*args),cwd=checkout,check=True,
                              capture_output=True,text=True).stdout.strip()
    commit=git('rev-parse','HEAD')
    dirty=git('status','--porcelain')
    proposed=mesh in inventory.meshes()
    if (proposed or state_payload) and dirty:
        raise ValueError('inventory or solved-state probe requires clean frozen source')
    directory.mkdir(parents=True,exist_ok=False)
    sources=_hashes()
    manifest_path=directory/'manifest.json'
    command=[sys.executable,'-u',str(Path(__file__).resolve()),
             '--child','--mesh',f'{mesh.n_s},{mesh.n_y},{mesh.n_beam},{mesh.n_mortar}',
             '--topology',topology,'--law',law,
             '--expected-manifest',str(manifest_path.resolve())]
    if solve:
        command.append('--solve')
    if scaled:
        command.append('--scaled')
    if loaded_probe:
        command.append('--loaded-probe')
    if trace_topology is not None:
        command.extend(('--trace-topology',trace_topology))
    if state_payload:
        command.append('--state-payload')
    environment=os.environ.copy()
    environment.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',
                       MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',
                       PYTHONDONTWRITEBYTECODE='1')
    manifest=dict(purpose=('diagnostic stiffness/trace partition with solved state'
                           if state_payload else
                           'loaded F03 classical resource preflight' if loaded_probe
                           else 'scaled factorization F03 classical resource preflight'
                           if scaled else 'factorization F03 classical resource preflight' if solve
                           else 'assembly-only F03 classical resource preflight'),
                  mesh=vars(mesh),topology=topology,law=law,
                  trace_topology=trace_topology or topology,
                  state_payload=state_payload,
                  solve=solve,scaled=scaled,loaded_probe=loaded_probe,
                  loading='smooth' if solve else None,
                  scales=dict(force_newton=F0,moment_newton_metre=M0,
                              displacement_metre=U0),
                  assembly_identity=(f'{topology}-trace-{trace_topology or topology}-'
                                     f'{law}-Ns{mesh.n_s}-Ny{mesh.n_y}-'
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
            payload_valid=(not state_payload or
                           _valid_state_payload(directory,records,mesh,law))
            phases_valid=(not state_payload or
                          _valid_state_phases(records,topology,trace_topology or topology))
            if peak>MAX_RSS:
                reason='rss_limit'
            elif elapsed>MAX_SECONDS:
                reason='time_limit'
            elif (exit_code!=0 or malformed or not payload_valid or
                  not phases_valid or len(identities)!=1 or
                  identities[0].get('sources')!=sources or
                  identities[0].get('threads')!=manifest['threads'] or
                  any(pool.get('num_threads')!=1 for pool in
                      identities[0].get('threadpools',[])) or
                  not identities[0].get('modules') or
                  post_hashes!=sources or not records or
                  records[-1].get('phase')!=
                  ('loaded_observables' if loaded_probe else
                   'linear_solve' if solve else 'unfactorized_kkt')):
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
    parser.add_argument('--topology',choices=('Q4','CST','CST-CB'),required=True)
    parser.add_argument('--law',choices=('P0','P1'),required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--solve',action='store_true',
                        help='also factor and solve a smooth-load algebraic system')
    parser.add_argument('--scaled',action='store_true',
                        help='use congruent dimensionless KKT scaling with --solve')
    parser.add_argument('--loaded-probe',action='store_true',
                        help='recover full loaded observables under the supervisor')
    parser.add_argument('--trace-topology',choices=('Q4','CST-CB'),
                        help='diagnostic-only trace panel, separate from shell stiffness')
    parser.add_argument('--state-payload',action='store_true',
                        help='preserve solved physical q and signed lambda for independent audit')
    parser.add_argument('--child',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--expected-manifest',type=Path,help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.child:
        if args.expected_manifest is None:
            parser.error('--expected-manifest is required for child')
        _child(args.mesh,args.topology,args.law,args.expected_manifest,
               args.solve,args.scaled,args.loaded_probe,
               args.trace_topology,args.state_payload)
        return 0
    if args.output is None:
        parser.error('--output is required for supervised execution')
    return _supervise(args.mesh,args.topology,args.law,args.output,
                      args.solve,args.scaled,args.loaded_probe,
                      args.trace_topology,args.state_payload)


if __name__=='__main__':
    raise SystemExit(main())
