"""Single-use diagnostic of F03-K0 finite-difference and KKT parity failures.

The frozen F03-K0 evidence is not rerun, and this diagnostic cannot accept a
line multiplier or close F03/G0. Invoke through the paired supervisor only.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
import traceback

import numpy as np
from scipy import linalg, sparse

from _b3_e4_f03_native_fixture import build
from _b3_e4_f03_shell_trace import make_shell
from probe_b3_ge_e4_pl_g0_f03_kkt import (
    ELL, actual_pose_gap, assemble, exact_partition, scales, solve_exact,
    spaces, supported_stiffness,
)
from run_b3_ge_e4_pl_g0_f03_k0 import (
    EVIDENCE_ROOT, MemoryMonitor, ROOT, actual_identity, sha256,
)


GATE = 'G0_F03_D1_V1'
MANIFEST = 'docs/agent_plans/B3_GE_E4_PL_G0_F03_D1_MANIFEST.md'
SOURCE = 'scripts/run_b3_ge_e4_pl_g0_f03_d1.py'
SUPERVISOR = 'scripts/supervise_b3_ge_e4_pl_g0_f03_d1.py'
DERIVATIVE_MESHES = (('Q4',4,4),('Q4',16,16),
                     ('S3-V2D',4,4),('S3-V2D',16,16))
PARITY_CASES = (('Q4',4,2,'smooth'),('Q4',8,8,'alternating'),
                ('Q4',16,8,'smooth'),('Q4',16,8,'alternating'),
                ('Q4',16,16,'smooth'),('Q4',16,16,'alternating'))
STATIONS = (.337,.5-1e-7,.5+1e-7)
STEPS = (.3,.1,.03,.01,.003,.001,.0003,.0001,.00003,.00001)
ORIGINAL_THRESHOLD = 1e-10
U = 1e6/(210e9*.07)
MULTIPLIER = np.array((.8e6,-.35e6,.21e6))
SCALE3 = np.array((1.,1.,ELL))


def identity() -> dict:
    base = actual_identity()  # clean commit, source tree, environment, threads
    return {'base':base,
            'diagnostic_sha256':{path:sha256(ROOT/path)
                                 for path in (SOURCE,SUPERVISOR,MANIFEST)}}


def verify(registration: dict, observed: dict, evidence: Path) -> None:
    if (registration.get('gate') != GATE
            or registration.get('status') != 'FROZEN'
            or registration.get('identity') != observed
            or registration.get('protocol') != {
                'derivative_meshes':[list(x) for x in DERIVATIVE_MESHES],
                'parity_cases':[list(x) for x in PARITY_CASES],
                'stations':list(STATIONS),'steps':list(STEPS),
                'original_threshold':ORIGINAL_THRESHOLD}
            or registration.get('limits') != {
                'wall_seconds':3600,
                'sampled_rss_limit_bytes':4*1024**3}
            or registration.get('evidence_directory') != str(evidence)
            or evidence.parent != EVIDENCE_ROOT or evidence.exists()):
        raise ValueError('frozen D1 registration or new output path mismatch')
    if observed['base']['total_memory_bytes'] < 4*1024**3:
        raise ValueError('registered RSS limit exceeds physical memory')


def direction(beam, shell, station: float, kind: str):
    # Reconstruct the same rail/cell probe as v2, and a separate beam-only
    # perturbation. The native fixed root must remain exactly unchanged.
    shell_delta = np.zeros(shell.dof_count)
    beam_delta = np.zeros(beam.context.count)
    e,cell,_,_ = beam._locate(station)
    beam_delta[beam.context.nodal_count+24*e+3*cell+2] = U/ELL
    if kind == 'combined':
        host = shell.sample_weights(station)
        width = 2*shell.n_s+1
        lower = int(np.argmax(np.max(host[:2,:width],axis=0)))
        upper = 2*width+int(np.argmax(np.max(host[2:,2*width:],axis=0)))
        if (host[:2,lower].max() < .01 or host[2:,upper].max() < .01):
            raise AssertionError('inactive registered rail probe')
        shell_delta[2*lower] = U
        shell_delta[2*upper] = -U
    elif kind != 'beam_only':
        raise ValueError('unknown frozen direction')
    if any(beam_delta[index] != 0 for index in beam.context.fixed):
        raise AssertionError('fixed native root changed')
    return shell_delta, beam_delta


def derivative_case(topology: str, n_beam: int, n_shell: int):
    beam, shell = build(n_beam), make_shell(n_shell,topology)
    result = {'topology':topology,'n_beam':n_beam,'n_shell':n_shell,
              'stations':[]}
    for station in STATIONS:
        probes = []
        for kind in ('combined','beam_only'):
            sd,bd = direction(beam,shell,station,kind)
            analytic = (beam.planar_trace_jacobian(station)@bd
                        -shell.trace(station)@sd)
            denominator = max(np.linalg.norm(SCALE3*analytic),U)
            calculations = []
            for h in STEPS:
                plus = actual_pose_gap(beam,shell,station,h*sd,h*bd)
                minus = actual_pose_gap(beam,shell,station,-h*sd,-h*bd)
                finite = np.r_[(plus-minus)[:2],(plus-minus)[5]]/(2*h)
                scaled_difference = SCALE3*(finite-analytic)
                work_finite = float(MULTIPLIER@(SCALE3*finite))
                work_analytic = float(MULTIPLIER@(SCALE3*analytic))
                calculations.append({
                    'h':h,'physical_perturbation_m':h*U,
                    'finite_planar_derivative':finite.tolist(),
                    'out_of_plane_translation_derivative_m':float(
                        ((plus-minus)/(2*h))[2]),
                    'out_of_plane_rotation_derivative_rad':(
                        ((plus-minus)/(2*h))[[3,4]]).tolist(),
                    'absolute_scaled_derivative_error':float(
                        np.linalg.norm(scaled_difference)),
                    'normalized_derivative_error':float(
                        np.linalg.norm(scaled_difference)/denominator),
                    'finite_work_density':work_finite,
                    'analytic_work_density':work_analytic,
                    'normalized_work_error':float(abs(work_finite-work_analytic)/
                                                  (1e6*U))})
            probes.append({'direction':kind,
                           'scaled_analytic_derivative':(SCALE3*analytic).tolist(),
                           'normalized_denominator':float(denominator),
                           'results':calculations})
        result['stations'].append({'station':station,'directions':probes})
    return result


def parity_case(topology: str, n_beam: int, n_shell: int, load_kind: str):
    beam, shell = build(n_beam), make_shell(n_shell,topology)
    space = next(x for x in spaces(beam,shell) if x.name == 'p1-shell')
    coupling = assemble(beam,shell,space)
    load = {'smooth':coupling.load_smooth,
            'alternating':coupling.load_alternating}[load_kind]
    measurement, sparse_solution = solve_exact(beam,shell,coupling,load)
    k, (ke, cl, cu, sr, solve_rr), (krr, krp, cr) = exact_partition(
        beam,shell,coupling.matrix)
    physical_count = len(ke)
    rhs = np.r_[load,np.zeros(coupling.matrix.shape[0])]
    scale = np.r_[scales(beam,shell,coupling.matrix.shape[0])[0],
                  scales(beam,shell,coupling.matrix.shape[0])[1]]
    kkt = sparse.bmat(((sparse.csc_matrix(k),coupling.matrix.T),
                       (coupling.matrix,None)),format='csr').toarray()
    work_kkt = (scale[:,None]*kkt)*scale[None,:]
    work_rhs = scale*rhs
    dense_solution = scale*linalg.solve(work_kkt,work_rhs,assume_a='gen')
    reduced = np.block([[ke,cu],[cl,-sr]])
    reduced_scale = np.r_[scale[:physical_count],scale[len(k):]]
    retained_load = solve_rr(load[physical_count:])[:,0]
    reduced_rhs = np.r_[load[:physical_count]-k[:physical_count,physical_count:]@retained_load,
                        -cr@retained_load]
    reduced_solution = reduced_scale*linalg.solve(
        (reduced_scale[:,None]*reduced)*reduced_scale[None,:],
        reduced_scale*reduced_rhs,assume_a='gen')
    recovered = retained_load-solve_rr(
        krp@reduced_solution[:physical_count]
        +cr.T@reduced_solution[physical_count:])[:,0]
    condensed_solution = np.r_[reduced_solution[:physical_count],recovered,
                                reduced_solution[physical_count:]]
    def difference(a,b):
        return float(np.linalg.norm((a-b)/scale)/max(
            np.linalg.norm(a/scale),np.linalg.norm(b/scale)))
    def backward(x):
        y=x/scale
        return float(np.linalg.norm(work_kkt@y-work_rhs)/max(
            np.linalg.norm(work_kkt)*np.linalg.norm(y)
            +np.linalg.norm(work_rhs),np.finfo(float).tiny))
    singular=linalg.svdvals(work_kkt)
    return {'topology':topology,'n_beam':n_beam,'n_shell':n_shell,
            'space':'p1-shell','load':load_kind,
            'v2_sparse_condensed_parity':measurement['scaled_solution_parity'],
            'sparse_dense_parity':difference(sparse_solution,dense_solution),
            'sparse_condensed_parity':difference(sparse_solution,condensed_solution),
            'dense_condensed_parity':difference(dense_solution,condensed_solution),
            'work_scaled_backward':{
                'sparse':backward(sparse_solution),'dense':backward(dense_solution),
                'condensed':backward(condensed_solution)},
            'scaled_kkt_singular_ratio':float(singular[-1]/singular[0]),
            'scaled_krr_condition':measurement['cond_krr'],
            'physical_count':physical_count,
            'retained_count':len(krr),
            'multiplier_count':coupling.matrix.shape[0]}


def run(registration_path: Path, evidence: Path):
    registration_path=registration_path.resolve(strict=True)
    evidence=evidence.resolve()
    registration=json.loads(registration_path.read_text(encoding='utf-8'))
    observed=identity()
    verify(registration,observed,evidence)
    evidence.mkdir(exist_ok=False)
    started=time.monotonic()
    registration_hash=sha256(registration_path)
    with (evidence/'raw.jsonl').open('x',encoding='utf-8') as out, MemoryMonitor() as monitor:
        def emit(row):
            out.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
            out.flush();os.fsync(out.fileno())
        emit({'type':'start','registration_sha256':registration_hash,
              'registration':registration,'identity':observed})
        count=0
        try:
            for case in DERIVATIVE_MESHES:
                count+=1
                emit({'type':'derivative','index':count,'data':derivative_case(*case),
                      'elapsed_seconds':time.monotonic()-started})
            for case in PARITY_CASES:
                count+=1
                emit({'type':'parity','index':count,'data':parity_case(*case),
                      'elapsed_seconds':time.monotonic()-started})
            if (time.monotonic()-started > registration['limits']['wall_seconds']
                    or monitor.maximum > registration['limits']['sampled_rss_limit_bytes']
                    or sha256(registration_path) != registration_hash
                    or identity() != observed):
                raise RuntimeError('resource or identity changed')
            emit({'type':'terminal','status':'DIAGNOSTIC_COMPLETE_NOT_F03_ACCEPTANCE',
                  'records':count,'elapsed_seconds':time.monotonic()-started,
                  'sampled_peak_rss_bytes':monitor.maximum})
            return 0
        except BaseException as exc:
            emit({'type':'terminal','status':'ABORTED_NOT_QUALIFIED',
                  'records':count,'failure_type':type(exc).__name__,
                  'failure':str(exc),'traceback':traceback.format_exc(),
                  'elapsed_seconds':time.monotonic()-started,
                  'sampled_peak_rss_bytes':monitor.maximum})
            raise


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(run(args.registration,args.evidence))
