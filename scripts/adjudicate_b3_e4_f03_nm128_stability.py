"""Read-only adjudication of registered F03 supported stability matrices."""

from __future__ import annotations

import argparse
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import traceback

import numpy as np
from scipy import linalg

import run_b3_e4_f03_nm128_stability as runner


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _close(actual: float, reported: float, label: str,
           *, absolute_floor: float=1e-10) -> None:
    _require(math.isfinite(actual) and math.isfinite(reported) and
             math.isclose(actual,reported,rel_tol=1e-8,abs_tol=absolute_floor),
             f'{label} differs from independently recomputed value')


def _reference_norm(nm: int) -> tuple[np.ndarray,np.ndarray]:
    """Independent elementwise P1 integration, avoiding the runner's builder."""
    h=1/nm
    mass=np.zeros((nm+1,nm+1))
    gradient=np.zeros_like(mass)
    for cell in range(nm):
        ids=np.array((cell,cell+1))
        mass[np.ix_(ids,ids)]+=h*np.array(((1/3,1/6),(1/6,1/3)))
        gradient[np.ix_(ids,ids)]+=np.array(((1,-1),(-1,1)))/h
    mu,v=linalg.eigh(gradient,mass,check_finite=True)
    _require(mu[0]>=-1e-10*max(1.,mu[-1]),'invalid P1 derivative norm')
    mv=mass@v
    dual=(mv*(1+np.maximum(mu,0))**-.5)@mv.T
    return np.kron(mass,np.eye(3)),np.kron(dual,np.eye(3))


def _case(root: Path,registered: dict,name: str) -> dict:
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    phases=[json.loads(row) for row in (root/'phases.jsonl').read_text(
        encoding='utf-8').splitlines()]
    result=json.loads((root/'result.json').read_text(encoding='utf-8'))
    _require(manifest['case']==name and manifest['kind']==registered['kind'],
             'case or kind identity changed')
    _require(manifest['command']==[
        registered['python_executable'],'-u',registered['runner_path'],
        '--child','--case',name,'--expected-manifest',
        str((root/'manifest.json').resolve())],'child command changed')
    _require(manifest['source_commit']==registered['execution_head'] and
             manifest['source_dirty'] is False,'source identity changed')
    _require(manifest['sources']==registered['runner_source_hashes']==runner._hashes(),
             'source hashes changed')
    _require(manifest['limits']==registered['limits']==dict(
        max_rss_bytes=8*1024**3,max_seconds=900),'resource limits changed')
    _require(manifest['threads']==registered['threads'],'thread settings changed')
    _require(all(manifest[key]==value for key,value in registered['runtime'].items()),
             'runtime identity changed')
    _require(manifest['mesh']==dict(n_s=128,n_y=64,n_beam=512,
                                  n_mortar=runner.CASES[name][1]),'mesh changed')
    _require(manifest['topology']==runner.CASES[name][0],'topology changed')
    _require(len(phases)==2 and all(isinstance(row,dict) for row in phases) and
             [row.get('phase') for row in phases]==['identity','stability'],
             'missing or malformed phase')
    _require(phases[0]['sources']==manifest['sources'] and
             phases[0]['threads']==manifest['threads'] and
             phases[0]['threadpools']==registered['threadpools'] and
             bool(phases[0]['threadpools']) and all(
                 item['num_threads']==1 for item in phases[0]['threadpools']) and
             phases[0]['modules']==registered['module_paths'],
             'observed child identity changed')
    _require(result['post_source_hashes']==manifest['sources'] and
             result['post_head']==registered['execution_head'] and
             result['post_dirty'] is False and result['post_checkout_error'] is None,
             'post-run source identity changed')
    _require(result['reason']=='process_exit' and result['exit_code']==0 and
             result['malformed_phase_lines']==[] and
             result['completed_phases']==['identity','stability'],
             'execution did not finish cleanly')
    _require((root/'stderr.log').stat().st_size==0,'unexpected child stderr')
    _require(phases[1]['case']==name and
             phases[1]['payload_sha256']==_sha(root/'schur.npz'),
             'Schur payload identity changed')
    samples=[json.loads(row) for row in (root/'rss.jsonl').read_text(
        encoding='utf-8').splitlines()]
    _require(bool(samples) and all(isinstance(row,dict) and
             isinstance(row.get('rss_bytes'),int) and row['rss_bytes']>=0 and
             isinstance(row.get('elapsed_seconds'),(int,float)) and
             math.isfinite(row['elapsed_seconds']) and row['elapsed_seconds']>=0
             for row in samples),'invalid RSS samples')
    elapsed=result['elapsed_seconds']
    _require(isinstance(elapsed,(int,float)) and math.isfinite(elapsed) and
             0<=elapsed<=registered['limits']['max_seconds'] and
             all(row['elapsed_seconds']<=elapsed for row in samples) and
             all(a['elapsed_seconds']<=b['elapsed_seconds'] for a,b in
                 zip(samples,samples[1:])), 'elapsed time or RSS sample changed')
    phase_rss=[row['rss_bytes'] for row in phases]
    _require(all(isinstance(value,int) and value>=0 for value in phase_rss) and
             isinstance(result['sampled_peak_rss_bytes'],int) and
             result['sampled_peak_rss_bytes']==max(
                 [row['rss_bytes'] for row in samples]+phase_rss) and
             result['sampled_peak_rss_bytes']<=registered['limits']['max_rss_bytes'] and
             0<=phases[1]['elapsed_seconds']<=elapsed,
             'resource evidence differs from observed samples')
    metrics=phases[1]['measures']
    nm=runner.CASES[name][1]
    _require(metrics['mesh']==manifest['mesh'] and
             metrics['topology']==manifest['topology'],'metric mesh changed')
    _require(metrics['physical_free']==36223 and
             metrics['multiplier_rows']==3*(nm+1) and
             metrics['kkt_dimension']==36223+3*(nm+1),
             'assembled dimensions changed')
    _require(metrics['numerical_checks_pass'] is True,
             'numerical preflight did not pass')
    with np.load(root/'schur.npz',allow_pickle=False) as payload:
        _require(set(payload.files)=={'schur','dual','mass'},
                 'unexpected Schur payload fields')
        s=payload['schur'].copy();r=payload['dual'].copy();m=payload['mass'].copy()
    _require(all(x.shape==(3*(nm+1),)*2 and x.dtype==np.float64 and
                 np.all(np.isfinite(x)) for x in (s,r,m)),
             'invalid Schur payload matrices')
    ref_mass,ref_dual=_reference_norm(nm)
    np.testing.assert_allclose(m,ref_mass,rtol=1e-12,atol=1e-12)
    np.testing.assert_allclose(r,ref_dual,rtol=1e-10,atol=1e-12)
    _require(max(np.max(np.abs(x-x.T))/max(np.max(np.abs(x)),1e-300)
                 for x in (s,r,m))<=1e-10,'asymmetric Schur or norm')
    eig=linalg.eigh(s,r,eigvals_only=True,check_finite=True)
    l2=linalg.eigh(s,m,eigvals_only=True,check_finite=True)
    _require(eig[-1]>0 and eig[0]>0,'nonpositive Schur spectrum')
    for actual,reported in ((eig[0],metrics['minimum_generalized_eigen']),
                            (eig[-1],metrics['maximum_generalized_eigen']),
                            (l2[0],metrics['l2_minimum_generalized_eigen']),
                            (l2[-1],metrics['l2_maximum_generalized_eigen'])):
        np.testing.assert_allclose(actual,reported,rtol=1e-8,atol=1e-10)
    for key,limit in (('kbar_skew',1e-10),('schur_skew',1e-10),
                      ('max_stiffness_solve_residual',1e-9),
                      ('max_supported_mode_residual',1e-8),
                      ('max_generalized_eigen_residual',1e-8)):
        value=metrics[key]
        _require(isinstance(value,(int,float)) and math.isfinite(value) and
                 0<=value<=limit,f'{key} failed')
    modes=metrics['supported_near_zero_eigenvalues']
    _require(len(modes)==2 and all(math.isfinite(value) and value>0
                                  for value in modes),'near-zero probe failed')
    margin=max(1e-10*eig[-1],20*eig[-1]*(
        metrics['max_stiffness_solve_residual']+
        metrics['max_generalized_eigen_residual']+metrics['schur_skew']))
    _close(margin,metrics['minimum_eigen_screening_margin'],
           'screening margin',absolute_floor=1e-16)
    _require(eig[0]>margin,'minimum below screening margin')
    for value,key in ((math.sqrt(eig[0]),'beta_min'),
                      (math.sqrt(eig[-1]),'beta_max'),
                      (math.sqrt(eig[0]/eig[-1]),'beta_ratio')):
        _close(value,metrics[key],key)
    return dict(case=name,mesh=metrics['mesh'],topology=metrics['topology'],
                manifest_sha256=_sha(root/'manifest.json'),
                phases_sha256=_sha(root/'phases.jsonl'),
                result_sha256=_sha(root/'result.json'),
                payload_sha256=_sha(root/'schur.npz'),
                stderr_sha256=_sha(root/'stderr.log'),
                rss_sha256=_sha(root/'rss.jsonl'),
                beta_min=float(math.sqrt(eig[0])),
                beta_max=float(math.sqrt(eig[-1])),
                beta_ratio=float(math.sqrt(eig[0]/eig[-1])),
                l2_minimum_generalized_eigen=float(l2[0]),
                heuristic_screening_margin=float(margin),
                stiffness_solve_residual=metrics['max_stiffness_solve_residual'],
                elapsed_seconds=result['elapsed_seconds'],
                peak_rss_bytes=result['sampled_peak_rss_bytes'],
                kbar_nnz=metrics['kbar_nnz'],coupling_nnz=metrics['coupling_nnz'],
                overlay_intervals=metrics['overlay_intervals'])


def adjudicate(registration: Path,evidence: Path) -> dict:
    registered=json.loads(registration.read_text(encoding='utf-8'))
    _require(registered['cases']==list(runner.CASES),'case inventory changed')
    _require(registered['adjudicator_sha256']==_sha(Path(__file__)),
             'adjudicator source changed')
    _require(registered['runner_source_hashes']==runner._hashes(),
             'runner source changed')
    _require(bool(registered['dependency_file_sha256']) and all(
             _sha(Path(path))==digest for path,digest in
             registered['dependency_file_sha256'].items()),
             'dependency identity changed')
    _require(len(registered['commands'])==len(registered['cases'])==4,
             'command inventory changed')
    _require(all(command==[registered['python_executable'],
                         registered['runner_path'],'--case',name,'--output',
                         str((evidence/name).resolve()),'--registration',
                         str(registration.resolve())]
                 for command,name in zip(registered['commands'],registered['cases'])),
             'registered commands changed')
    rows=[_case(evidence/name,registered,name) for name in registered['cases']]
    paired={topology:dict(beta_min_ratio_nm128_over_nm64=
                          rows[high]['beta_min']/rows[low]['beta_min'],
                          beta_ratio_nm64=rows[low]['beta_ratio'],
                          beta_ratio_nm128=rows[high]['beta_ratio'])
            for topology,low,high in (('Q4',0,1),('CST-CB',2,3))}
    return dict(status='FINITE_STABILITY_DIAGNOSTIC_ONLY',
                physical_admission='STABILITY_ADMISSION_UNRESOLVED',
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                registration_sha256=_sha(registration),
                adjudicator_sha256=_sha(Path(__file__)),
                execution_head=registered['execution_head'],
                inventory=len(rows),cases=rows,paired=paired)


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--registration',type=Path,required=True)
    parser.add_argument('--evidence-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    try:
        result=adjudicate(args.registration,args.evidence_root)
        (args.output/'adjudication.json').write_text(
            json.dumps(result,indent=2,sort_keys=True,allow_nan=False),
            encoding='utf-8')
        print(json.dumps(dict(status=result['status'],inventory=result['inventory'],
                              output=str(args.output.resolve()))))
        return 0
    except Exception:
        (args.output/'failure.txt').write_text(traceback.format_exc(),
                                               encoding='utf-8')
        raise


if __name__=='__main__':
    raise SystemExit(main())
