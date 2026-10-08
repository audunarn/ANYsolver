"""Immutable postprocessing of the registered finite-pad axis snapshots.

No new equilibrium solve is performed. Signed P1 traction integrals and
floating endpoint diagnostics describe the saved finite-model solutions;
they do not assign continuum, stability or native-coupling acceptance.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess
import time

import numpy as np

import _b3_e4_f03_area_endpoint as endpoint
import _b3_e4_f03_area_line as area
import _b3_e4_f03_area_port as port
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as original
import _b3_e4_f03_independent_shell as shell


ROOT=Path(__file__).resolve().parents[1]
SOURCES=(Path(__file__).resolve(),*(Path(module.__file__).resolve() for module in
          (endpoint,area,port,beam,original,shell)))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def _new_json(path: Path, value: object) -> None:
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False)
        stream.write('\n')


def _validate_adjudication(registration: dict, adjudication: dict) -> None:
    if (adjudication['identity']!=registration['identity'] or
            set(adjudication['cases'])!=set(registration['cases']) or
            any(row['status']!='PASSED_ALGEBRAIC_SCREEN'
                for row in adjudication['cases'].values())):
        raise ValueError('complete source-matched accepted algebraic input inventory required')


def _validate_receipt(directory: Path, name: str, registration: dict,
                      registration_sha: str) -> None:
    events=[json.loads(line) for line in (directory/'stdout.jsonl').read_text().splitlines()]
    receipt=_json(directory/'supervision.json')
    observed_sha=_sha(directory/'observables.json')
    if (len(events)!=2 or not all(isinstance(event,dict) for event in events) or
            events[0].get('phase')!='identity' or events[0].get('case')!=name or
            events[0].get('identity')!=registration['identity'] or
            events[0].get('registration_sha256')!=registration_sha or
            not events[0].get('threadpools') or
            any(pool.get('num_threads')!=1 for pool in events[0]['threadpools']) or
            events[1]!={'phase':'observables','case':name,'sha256':observed_sha,
                        'state_sha256':_sha(directory/'solved_state.npz')}):
        raise ValueError(f'{name}: source/state/thread identity mismatch')
    limits=registration['limits']
    if (receipt['reason']!='completed' or receipt['exit_code']!=0 or
            receipt['registration_sha256']!=registration_sha or
            receipt['phases']!=['identity','observables'] or
            receipt['observables_sha256']!=observed_sha or
            receipt['failure'] is not None or
            not math.isfinite(receipt['elapsed_seconds']) or
            not 0<=receipt['elapsed_seconds']<=limits['seconds_per_case'] or
            not isinstance(receipt['sampled_peak_rss_bytes'],int) or
            not 0<=receipt['sampled_peak_rss_bytes']<=limits['rss_bytes_per_case']):
        raise ValueError(f'{name}: unsuccessful or inconsistent supervision receipt')
    parity=registration['parity_reference']
    if name in parity and observed_sha!=parity[name]:
        raise ValueError(f'{name}: frozen baseline parity mismatch')


def _density(values: np.ndarray, n: int, s: float) -> np.ndarray:
    cell=min(int(s*n),n-1)
    t=s*n-cell
    return (1-t)*values[cell]+t*values[cell+1]


def multiplier_wrench(lam: np.ndarray, n: int,
                      left: float, right: float) -> np.ndarray:
    """Exact P1 force and origin moment on a physical subinterval, L=1 m."""
    values=np.asarray(lam,dtype=float)
    if (not isinstance(n,int) or n<1 or values.shape!=(3*(n+1),) or
            not np.all(np.isfinite(values)) or
            not 0<=left<right<=1):
        raise ValueError('invalid P1 force-density interval')
    values=values.reshape(n+1,3)
    knots=sorted({left,right,*(j/n for j in range(1,n) if left<j/n<right)})
    result=np.zeros(3)
    for a,b in zip(knots[:-1],knots[1:]):
        va,vb=_density(values,n,a),_density(values,n,b)
        integrated=(b-a)*(va+vb)/2
        result[:2]+=integrated[:2]
        result[2]+=(b-a)*((2*a+b)*va[1]+(a+2*b)*vb[1])/6
        result[2]+=original.YAW_LENGTH*integrated[2]
    return result


def root_port_force(lam: np.ndarray, n_mortar: int, n_beam: int) -> float:
    """Integrate the independent root Hermite weight against vertical P1 force."""
    raw=np.asarray(lam,dtype=float)
    if (not isinstance(n_mortar,int) or n_mortar<1 or
            not isinstance(n_beam,int) or n_beam<1 or
            raw.shape!=(3*(n_mortar+1),) or not np.all(np.isfinite(raw))):
        raise ValueError('invalid root-port integration field')
    values=raw.reshape(n_mortar+1,3)
    width=1/n_beam
    knots=sorted({0.,width,*(j/n_mortar for j in range(1,n_mortar)
                            if j/n_mortar<width)})
    nodes,weights=np.polynomial.legendre.leggauss(3)
    result=0.
    for a,b in zip(knots[:-1],knots[1:]):
        for node,weight in zip(nodes,weights):
            s=(a+b)/2+(b-a)*node/2
            t=s/width
            result+=(b-a)*weight/2*(1-3*t*t+2*t**3)*_density(values,n_mortar,s)[1]
    return float(result)


def describe(spec: dict, observations: dict, q: np.ndarray, lam: np.ndarray) -> dict:
    ns,ny,nb,nm=(spec[k] for k in ('n_s','n_y','n_beam','n_mortar'))
    model=shell.panel(ns,ny,spec['topology'])
    qs,qb=q[:model.dof_count],q[model.dof_count:]
    values=lam.reshape(nm+1,3)
    quarters=np.array([multiplier_wrench(lam,nm,j/4,(j+1)/4) for j in range(4)])
    np.testing.assert_allclose(quarters,observations['beam_port_quarter_wrenches'],
                               rtol=2e-12,atol=1e-7)
    root_force=root_port_force(lam,nm,nb)
    if not math.isclose(root_force,observations['beam_root_port_wrench'][1],
                        rel_tol=2e-12,abs_tol=1e-7):
        raise ValueError('independent P1/Hermite root-force reconstruction differs')
    derivative=endpoint.first_cell_gap_diagnostic(model,nb,nm,.05,qs,qb,order=10)
    check=endpoint.first_cell_gap_diagnostic(model,nb,nm,.05,qs,qb,order=12)
    a=np.array((*derivative.endpoint_gap_m,derivative.gap_derivative_l2,
                *derivative.weighted_derivative_m))
    b=np.array((*check.endpoint_gap_m,check.gap_derivative_l2,
                *check.weighted_derivative_m))
    if not np.allclose(a,b,rtol=1e-9,atol=1e-12):
        raise ValueError('first-cell floating quadrature orders disagree')
    if max(map(abs,derivative.first_hat_identity_residual_m))>1e-10:
        raise ValueError('saved equilibrium fails independent first-hat identity')
    bands={name:multiplier_wrench(lam,nm,left,right).tolist()
           for name,left,right in (('zero_to_1_over_32',0.,1/32),
                                   ('1_over_32_to_1_over_16',1/32,1/16),
                                   ('first_mortar_cell',0.,1/nm))}
    square=(values[:-1]**2+values[:-1]*values[1:]+values[1:]**2)/(3*nm)
    return {'mesh':[ns,ny,nb,nm],
            'tip_uy_m':observations['displacement_tip_m'][1],
            'root_wrench':observations['support_wrenches'][2],
            'root_elastic_wrench':observations['beam_root_elastic_wrench'],
            'root_port_wrench':observations['beam_root_port_wrench'],
            'root_load_wrench':observations['beam_root_load_wrench'],
            'independently_integrated_root_port_Fy_N':root_force,
            'physical_quarter_wrenches':quarters.tolist(),
            'fixed_band_wrenches':bands,
            'first_three_lambda_coefficients_N_per_m':values[:3].tolist(),
            'lambda_peak_absolute_N_per_m':np.max(np.abs(values),axis=0).tolist(),
            'lambda_l2_N_per_sqrt_m':np.sqrt(np.sum(square,axis=0)).tolist(),
            'stored_gap_l2_m':observations['gap_l2_m'],
            'energy_J':observations['shell_energy_j']+observations['beam_energy_j'],
            'first_cell':asdict(derivative),
            'quadrature_order_10_12_max_absolute_difference':float(np.max(np.abs(a-b)))}


def run(input_root: Path, output_root: Path) -> None:
    registration=_json(input_root/'registration.json')
    if _sha(input_root/'registration.json')!=(input_root/'registration.sha256').read_text().strip():
        raise ValueError('input registration hash mismatch')
    physical=registration['physical_model']
    if (registration['kind']!='experimental-classical-finite-pad-axis-refinement-v1' or
            len(registration['cases'])!=18 or not registration['capture_state'] or
            physical['halfwidth_m']!=.05 or physical['load']!='smooth' or
            physical['mortar']!='P1'):
        raise ValueError('registered 18-case fixed finite-pad axis model required')
    for module in (area,port,beam,original,shell):
        path=Path(module.__file__).resolve()
        key=path.relative_to(ROOT).as_posix()
        if _sha(path)!=registration['identity']['sources'][key]:
            raise ValueError('mechanical postprocessing source differs from saved case')
    adjudication=_json(input_root/'adjudication.json')
    _validate_adjudication(registration,adjudication)
    inputs={}
    saved_cases={}
    for name,spec in registration['cases'].items():
        directory=input_root/name
        _validate_receipt(directory,name,registration,_sha(input_root/'registration.json'))
        with np.load(directory/'solved_state.npz',allow_pickle=False) as state:
            q=state['physical_q']; lam=state['physical_lambda']
        count=2*(2*spec['n_s']+1)*(spec['n_y']+1)+6*spec['n_beam']+4
        if (q.shape!=(count,) or lam.shape!=(3*(spec['n_mortar']+1),) or
                q.dtype!=np.dtype('float64') or lam.dtype!=np.dtype('float64') or
                not np.all(np.isfinite(q)) or not np.all(np.isfinite(lam))):
            raise ValueError(f'{name}: invalid state layout')
        inputs[name]={k:_sha(directory/k) for k in
                      ('observables.json','solved_state.npz','stdout.jsonl','supervision.json')}
        saved_cases[name]=(_json(directory/'observables.json'),q,lam)
    status=subprocess.check_output(('git','status','--porcelain'),cwd=ROOT,
                                    text=True,stderr=subprocess.DEVNULL).strip()
    if status:
        raise ValueError('commit analysis candidate before consuming output root')
    head=subprocess.check_output(('git','rev-parse','HEAD'),cwd=ROOT,text=True).strip()
    output_root.mkdir(parents=True,exist_ok=False)
    manifest={'kind':'finite-model-snapshot-endpoint-analysis-v1',
              'created_utc':datetime.now(timezone.utc).isoformat(),
              'source_head':head,'source_hashes':{str(p.relative_to(ROOT)):_sha(p) for p in SOURCES},
              'dependencies':{n:importlib.metadata.version(n) for n in ('numpy','scipy')},
              'input_root':str(input_root),'parent_registration_sha256':_sha(input_root/'registration.json'),
              'parent_adjudication_sha256':_sha(input_root/'adjudication.json'),
              'input_files':inputs,
              'scope':'saved-state diagnostic, no new equilibrium solve or physical qualification',
              'checks':{'quarter_and_root_relative':2e-12,'force_absolute_N':1e-7,
                        'first_hat_absolute_m':1e-10,'quadrature_relative':1e-9,
                        'quadrature_absolute':1e-12}}
    _new_json(output_root/'analysis_registration.json',manifest)
    begun=time.monotonic()
    try:
        result={}
        for name,spec in registration['cases'].items():
            result[name]=describe(spec,*saved_cases[name])
            _new_json(output_root/(name+'.json'),result[name])
        for path in SOURCES:
            if _sha(path)!=manifest['source_hashes'][str(path.relative_to(ROOT))]:
                raise ValueError('analysis source changed during execution')
        for name,files in inputs.items():
            if any(_sha(input_root/name/filename)!=digest
                   for filename,digest in files.items()):
                raise ValueError('input evidence changed during analysis')
        _new_json(output_root/'results.json',result)
        _new_json(output_root/'completion.json',{
            'status':'COMPLETED_DESCRIPTIVE_ANALYSIS','count':len(result),
            'results_sha256':_sha(output_root/'results.json'),
            'elapsed_seconds':time.monotonic()-begun,
            'scope':manifest['scope']})
        print(json.dumps({'cases':len(result),'output':str(output_root),
                          'status':'COMPLETED_DESCRIPTIVE_ANALYSIS'}))
    except BaseException as exc:
        _new_json(output_root/'analysis_failure.json',{
            'status':'FAILED_ANALYSIS','error':f'{type(exc).__name__}: {exc}'})
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.input.resolve(),args.output.resolve())
