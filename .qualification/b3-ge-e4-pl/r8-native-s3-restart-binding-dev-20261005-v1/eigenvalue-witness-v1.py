"""Diagnostic only: fixed archived coordinates, one-ULP LAPACK eigenvalue delta."""
from pathlib import Path
from hashlib import sha256
import json, os, sys
import numpy as np
import scipy
import numba
import psutil
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_s3_algorithmic_pullback import local_coordinates
from examples.stiffened_shell_coupled_s3_adaptive_history import definition

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
assert len(psutil.Process().cpu_affinity()) == 1 and numba.config.DISABLE_JIT
assert all(row['num_threads'] == 1 for row in threadpool_info())
raw = (REPO/'tests/data/native_s3_fibre_history/unloaded-v1.bin').read_bytes()
owner = ss.create_analysis(definition=definition())
try:
    owner.restore(raw)
    assert owner.checkpoint() == raw
    _, metadata, arrays = owner._displacement_snapshot
    q = arrays['q']; anchors = arrays['shell_anchors']
    blobs = arrays['s3_states']; count = len(owner._shell_parts)
    original = np.linalg.eigh
    records = []
    for family, coordinates, frames, selected in (
        ('accepted', q, anchors, blobs[:count]),
        ('predecessor', arrays['shell_origin_q'], arrays['shell_origin_anchors'], blobs[count:])):
        for (_eid, element, slots, _), blob in zip(owner._shell_parts, selected, strict=True):
            saved = json.loads(blob)
            state = np.array(saved['committed_total_u'])
            baseline = local_coordinates(owner._shell_model, element, coordinates[slots],
                rotation_anchors=frames[slots[::6]//6])
            assert np.array_equal(state, baseline)
            shifts = []
            for toward in (np.inf, -np.inf):
                calls = []
                def shifted(matrix, *args, **kwargs):
                    values, vectors = original(matrix, *args, **kwargs)
                    values = values.copy(); old = values[-1]
                    values[-1] = np.nextafter(old, toward)
                    residual = np.linalg.norm(matrix@vectors[:, -1]-values[-1]*vectors[:, -1])
                    calls.append(dict(original=float(old), shifted=float(values[-1]),
                        eigenpair_relative_residual=float(residual/np.linalg.norm(matrix))))
                    return values, vectors
                np.linalg.eigh = shifted
                try:
                    perturbed = local_coordinates(owner._shell_model, element, coordinates[slots],
                        rotation_anchors=frames[slots[::6]//6])
                finally:
                    np.linalg.eigh = original
                diff = perturbed-state
                shifts.append(dict(toward='positive' if toward>0 else 'negative',
                    changed_rows=np.flatnonzero(diff).tolist(), maximum_absolute_delta=float(np.max(abs(diff))),
                    baseline=state.tolist(), perturbed=perturbed.tolist(), eigenpairs=calls))
            records.append(dict(family=family, element_id=int(_eid), saved_state_keys=sorted(saved), shifts=shifts))
    result = dict(status='DIAGNOSTIC_COMPLETED', scope='One ULP diagnostic eigenvalue perturbation only; unchanged product/fixture',
        checkpoint_sha256=sha256(raw).hexdigest(), checkpoint_unchanged=owner.checkpoint()==raw,
        python=sys.executable, numpy_version=np.__version__, scipy_version=scipy.__version__,
        threadpools=threadpool_info(), jit_disabled=bool(numba.config.DISABLE_JIT),
        affinity=psutil.Process().cpu_affinity(), metadata=metadata, records=records)
    (ROOT/'eigenvalue-witness-v1.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(status=result['status'], states=len(records),
        changed_states=sum(any(s['changed_rows'] for s in row['shifts']) for row in records),
        maximum_absolute_delta=max(s['maximum_absolute_delta'] for row in records for s in row['shifts']),
        checkpoint_unchanged=result['checkpoint_unchanged'])))
finally:
    owner.close()
