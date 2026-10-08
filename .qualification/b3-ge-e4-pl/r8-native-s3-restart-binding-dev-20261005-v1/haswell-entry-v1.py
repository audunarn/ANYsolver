"""Fixed archived coordinates under real Haswell BLAS; no history replay."""
from pathlib import Path
from hashlib import sha256
import json, os, sys
import numpy as np
import scipy.linalg
import numba, llvmlite, psutil
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_s3_algorithmic_pullback import local_coordinates
from anysolver._stiffened_shell_displacement_adaptive import decode as decode_adaptive
from anysolver._stiffened_shell_displacement_checkpoint import decode_snapshot
from examples.stiffened_shell_coupled_s3_adaptive_history import definition
ROOT = Path(__file__).resolve().parent; REPO = ROOT.parents[2]
SITE = ROOT/'ci-site-network-v2'
modules = (np, scipy, numba, llvmlite)
runtime = dict(python=sys.executable, coretype=os.environ.get('OPENBLAS_CORETYPE'),
    versions={m.__name__:m.__version__ for m in modules},
    imports={m.__name__:m.__file__ for m in modules}, threadpools=threadpool_info(),
    affinity=psutil.Process().cpu_affinity(), jit_disabled=bool(numba.config.DISABLE_JIT))
(ROOT/'haswell-runtime-v1.json').write_text(json.dumps(runtime, indent=2)+'\n')
for module, version in ((np,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
    assert module.__version__ == version and Path(module.__file__).resolve().is_relative_to(SITE.resolve())
assert runtime['coretype'] == 'Haswell'
assert len(runtime['affinity']) == 1 and runtime['jit_disabled']
assert runtime['threadpools'] and all(row['num_threads'] == 1 and row.get('architecture') == 'Haswell'
                                    for row in runtime['threadpools'])
binding = json.loads((ROOT/'backend-ci-binding-v2.json').read_text())
assert all(sha256((REPO/name).read_bytes()).hexdigest() == digest for name,digest in binding['files'].items())
witness = json.loads((ROOT/'eigenvalue-witness-v1.json').read_text())
reference = {(row['family'],row['element_id']):np.array(row['shifts'][0]['baseline']) for row in witness['records']}
fixture = REPO/'tests/data/native_s3_fibre_history/unloaded-v1.bin'
raw = fixture.read_bytes(); assert sha256(raw).hexdigest() == witness['checkpoint_sha256']
owner = ss.create_analysis(definition=definition())
try:
    # Decode framing and numerical payload only. Never restore or assemble an
    # accepted/predecessor history, and never run a continuation/eigenvalue shift.
    _, inner = decode_adaptive(owner, raw)
    _, arrays = decode_snapshot(owner, inner)
    count = len(owner._shell_parts); blobs = arrays['s3_states']
    original = np.linalg.eigh; records = []
    for family, coordinates, anchors, selected in (
        ('accepted', arrays['q'], arrays['shell_anchors'], blobs[:count]),
        ('predecessor', arrays['shell_origin_q'], arrays['shell_origin_anchors'], blobs[count:])):
        for (_eid,element,slots,_),blob in zip(owner._shell_parts,selected,strict=True):
            saved = np.array(json.loads(blob)['committed_total_u'])
            baseline = reference[(family,int(_eid))]
            assert np.array_equal(saved,baseline)
            eigenpairs = []
            def measured(matrix,*args,**kwargs):
                values,vectors = original(matrix,*args,**kwargs)
                q = vectors[:,-1]; eigenvalue = values[-1]
                eigenpairs.append(dict(eigenvalue=float(eigenvalue),
                    relative_residual=float(np.linalg.norm(matrix@q-eigenvalue*q)/np.linalg.norm(matrix)),
                    relative_work_residual=float(abs(q@matrix@q-eigenvalue)/max(abs(eigenvalue),np.finfo(float).tiny))))
                return values,vectors
            np.linalg.eigh = measured
            try:
                actual = local_coordinates(owner._shell_model,element,coordinates[slots],
                    rotation_anchors=anchors[slots[::6]//6])
            finally:
                np.linalg.eigh = original
            delta = actual-saved
            records.append(dict(family=family,element_id=int(_eid),exact_saved_binding=np.array_equal(actual,saved),
                exact_unforced_reference=np.array_equal(actual,baseline),changed_rows=np.flatnonzero(delta).tolist(),
                maximum_absolute_delta=float(np.max(abs(delta))),saved=saved.tolist(),actual=actual.tolist(),
                eigenpairs=eigenpairs))
    assert owner._finite_driver is None and owner._generation == 0
    assert fixture.read_bytes() == raw
    result = dict(status='DIAGNOSTIC_COMPLETED',runtime=runtime,checkpoint_sha256=sha256(raw).hexdigest(),
        history_replayed=False,checkpoint_unchanged=True,eigenvalues_perturbed=False,records=records,
        unforced_reference_sha256=sha256((ROOT/'eigenvalue-witness-v1.json').read_bytes()).hexdigest())
    (ROOT/'haswell-result-v1.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=result['status'],states=len(records),
        failed_exact_bindings=sum(not row['exact_saved_binding'] for row in records),
        maximum_absolute_delta=max(row['maximum_absolute_delta'] for row in records),
        maximum_eigenpair_relative_residual=max(e['relative_residual'] for row in records for e in row['eigenpairs']))))
finally:
    owner.close()
