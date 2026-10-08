"""Saved-array work decomposition only: no assembly, factorization or solve."""
from pathlib import Path
import hashlib, json, sys, zipfile
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_info

ROOT = Path(__file__).resolve().parent
PINS = {
    'prepared-v1.json': '25a956ee13cf2a36a9dbd6c3e93a06e4db5537cc8a00d78926bf8e9db62028e2',
    'prepared-v1.npz': '423b4171ed678275345340140f34714dc8c76e6f421a081dca4ece3cc65f8ab9',
    'control-v1.json': '88e062423e21c04621f293b6afdf06accb0da54c7024c47666dd76253c896b35',
    'control-v1.npz': 'c80832ade6f8f9094f98fadee5d5aeb6b77238e44c8480c33a3146fbfcc7fde1',
}
def require(value, message):
    if not value:
        raise ValueError(message)
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def csr(data, name):
    return sparse.csr_matrix((data[name+'_data'], data[name+'_indices'],
                             data[name+'_indptr']), shape=tuple(data[name+'_shape']))

require(not sys.flags.optimize, 'unoptimized guards required')
out = ROOT/'analysis-v1.json'
require(not out.exists(), 'fresh output required')
for name, pin in PINS.items():
    require(digest(ROOT/name) == pin, 'frozen successful pair required: '+name)
    if name.endswith('.npz'):
        with zipfile.ZipFile(ROOT/name) as archive:
            require(sum(item.file_size for item in archive.infolist()) < 128*1024**2,
                    'bounded input required')
prepare = json.loads((ROOT/'prepared-v1.json').read_text())
control = json.loads((ROOT/'control-v1.json').read_text())
require(prepare['status'] == 'PREPARED_DEVELOPMENT_CONTROL', 'successful preparation required')
require(control['status'] == 'COMPLETED_SAVED_OPERATOR_CONTROL_DEVELOPMENT_ONLY',
        'successful control required')
pools = threadpool_info()
require(pools and all(pool['num_threads'] == 1 for pool in pools), 'effective pools1 required')
with np.load(ROOT/'prepared-v1.npz', allow_pickle=False) as parent, \
     np.load(ROOT/'control-v1.npz', allow_pickle=False) as child:
    k, cf, cc = (csr(parent, name) for name in ('K', 'fine_C', 'child_C'))
    p, q = parent['parent_q'], child['q']
    lp, lq, load = parent['parent_lambda'], child['lambda_coarse'], parent['load']
    require(k.shape == (6924,6924) and cf.shape == (40,6924)
            and cc.shape == (20,6924) and lp.shape == (40,), 'fixed roles required')
    gp, gq = cf@q, cc@p
    rf, rc = k@p+cf.T@lp-load, k@q+cc.T@lq-load
    fine_terms = (lp*gp).reshape(5,8).sum(axis=1)
    cross_skew = float(q@(k@p)-p@(k@q))
    parent_child_gap_work = float(lq@gq)
    residual_work = float(-q@rf+p@rc)
    delta = float((q-p)@load)
    reconstructed = float(fine_terms.sum()+cross_skew-parent_child_gap_work+residual_work)
    scale = max(abs(float(q@load)), abs(float(p@load)), 1e-12)
    check = abs(delta-reconstructed)/scale
    require(np.isfinite(check) and check <= 1e-8, 'unchanged scaled work identity required')
    def profiles(configuration):
        weights = np.array([record['measure_m'] for record in control['station_records']])
        gaps = np.array([j@configuration[slots] for j,slots in
                         zip(parent['local_J'],parent['local_slots'],strict=True)])
        require(weights.shape == (128,) and gaps.shape == (128,5), 'same station inventory required')
        return {'max_abs_by_channel': np.max(np.abs(gaps),axis=0).tolist(),
                'measure_rms_by_channel': np.sqrt((weights[:,None]*gaps*gaps).sum(axis=0)/weights.sum()).tolist()}
    report = dict(identity='BL5_SAVED_DENSITY_WORK_DECOMPOSITION_DEV_V1',
        inputs=PINS, source_sha256=digest(Path(__file__)), effective_pools=pools,
        formal_f03_authority_consumed=False, qualification=False, solve_count=0,
        channel_order=['translation_x','translation_y','translation_z','director_x','director_y'],
        work_difference_J=delta, parent_action_on_child_fine_gap_J=fine_terms.tolist(),
        cross_skew_J=cross_skew, child_action_on_parent_child_gap_J=parent_child_gap_work,
        residual_work_J=residual_work, reconstructed_difference_J=reconstructed,
        scaled_identity_error=check,
        parent_continuous_station_gap=profiles(p),
        child_continuous_station_gap=profiles(q),
        limitation='Signed action attribution on these two saved solutions only; no channel tuning, '
                   'SPD, stability, law selection, convergence or physical accuracy inference.')
    out.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({key:report[key] for key in ('work_difference_J',
        'parent_action_on_child_fine_gap_J','cross_skew_J','residual_work_J','scaled_identity_error')}))
