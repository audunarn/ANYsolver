"""Raw integrity and spectral inspection, not an independent mechanics oracle.

Both coordinate parts remain in every schema and state hash. This inspector
does not import a producer, local mechanics or a production element.
"""

import math
import json
import re

from docs.reference_cases import ge_beam3_curved_p5_arch_onset_wave as shared
from docs.reference_cases import ge_beam3_curved_p5_compensated32_diagnostic as coordinates
from docs.reference_cases import ge_beam3_curved_p5_compensated_onset_probe as probe


def state_hash(assembly):
    checkpoint = {'epoch': assembly['origin_epoch']+1, 'positions': assembly['positions'],
        'position_low': assembly['position_low'], 'coordinate_schema': assembly['coordinate_schema'],
        'rotations': assembly['rotations'], 'forces': assembly['forces'],
        'histories': [[s['response']['history'] for s in e['stations']] for e in assembly['response']['elements']]}
    return shared.sha(shared.canonical(checkpoint)[:-1])


def initial_hash(count):
    import numpy as np
    t = np.linspace(-1., 1., 2*count+1)
    zero = {'plastic_coordinate': 0., 'accumulated': 0.}
    return shared.sha(shared.canonical({'epoch': 0,
        'positions': np.column_stack((t, .1*(1-t*t), np.zeros(len(t)))),
        'position_low': np.zeros((len(t), 3)), 'coordinate_schema': coordinates.COORDINATES,
        'rotations': np.tile(np.eye(3), (len(t), 1, 1)), 'forces': np.zeros((len(t), 3)),
        'histories': [[zero for _ in range(16)] for _ in range(count)]})[:-1])


def check_raw(raw, sample, count):
    import numpy as np
    from docs.reference_cases.ge_beam3_curved_p5_arch_stability_inspection import classify_matrix
    if (set(raw) != {'schema', 'id', 'origin_id', 'elements', 'sample', 'state_errors', 'trial', 'spectra',
                     'production_qualified', 'origin_checkpoint_sha256', 'checkpoint_sha256'} or
            raw['schema'] != probe.RAW_SCHEMA or raw['production_qualified'] is not False or
            type(raw['elements']) is not int or raw['elements'] != count or
            raw['id'] != sample['id'] or raw['origin_id'] != sample['origin_id'] or
            raw['sample'] != {k:v for k,v in sample.items() if k not in ('id', 'origin_id', 'sign')}):
        raise ValueError('compensated raw identity/sample mismatch')
    trial = raw['trial'];a = trial['assembly'];response = a['response'];n = 2*count+1
    if (set(trial) != {'origin_epoch', 'control_dof', 'target', 'reaction_derivative', 'assembly', 'checkpoints'} or
            set(a) != {'origin_epoch', 'positions', 'position_low', 'coordinate_schema', 'rotations', 'forces',
                       'origins', 'response', 'residual_norm', 'iterations', 'mixed_evaluations'}):
        raise ValueError('exact compensated trial schema required')
    coordinates.check_accuracy(response, count)
    coordinates.check_coordinates(a, count)
    def array(value, shape):
        made = np.asarray(value, dtype=float)
        if made.shape != shape or not np.isfinite(made).all():
            raise ValueError('finite complete raw array required')
        return made
    x = array(a['positions'], (n,3));low = array(a['position_low'], (n,3))
    q = array(a['rotations'], (n,3,3));f = array(a['forces'], (n,3))
    r = array(response['residual'], (6*n,));h = array(response['tangent'], (6*n,6*n))
    scatter_r = np.zeros_like(r);scatter_h = np.zeros_like(h);energy = 0.
    for i,e in enumerate(response['elements']):
        dofs = np.arange(12*i,12*i+18)
        scatter_r[dofs] += array(e['residual'], (18,))
        scatter_h[np.ix_(dofs,dofs)] += array(e['tangent'], (18,18))
        energy += e['potential']
    if not np.array_equal(r,scatter_r) or not np.array_equal(h,scatter_h) or energy != response['potential']:
        raise ValueError('raw element/assembly scatter mismatch')
    expected = np.zeros_like(f);expected[count,1] = -sample['load']
    residual = r.reshape(n,6).copy();residual[:,:3] -= expected
    scaled = residual[1:-1].copy();scaled[:,3:] /= 2.
    norm = float(np.linalg.norm(scaled))/max(1.,float(np.linalg.norm(expected)))
    s = np.diag([1.,1.,-1.])
    checks = {'equilibrium': norm,
        'position_planarity': max(abs(math.fsum((float(hi),float(lo)))) for hi,lo in zip(x[:,2],low[:,2])),
        'rotation_planarity': float(np.max(np.abs(q-s@q@s))),
        'rotation_orthogonality': float(np.max(np.abs(q.transpose(0,2,1)@q-np.eye(3)))),
        'rotation_determinant': float(np.max(np.abs(np.linalg.det(q)-1))),
        'fixed_positions': max(abs(math.fsum((float(x[i,j]),float(low[i,j]),-ref[j])))
            for i,ref in ((0,[-1.,0.,0.]),(-1,[1.,0.,0.])) for j in range(3)),
        'fixed_rotations': float(np.max(np.abs(q[[0,-1]]-np.eye(3)))),
        'load_pattern': float(np.max(np.abs(f-expected)))}
    if (set(raw['state_errors']) != set(checks) or
            any(not math.isfinite(v) or v > probe.search.LIMIT for v in checks.values()) or
            any(type(raw['state_errors'][k]) is not float or raw['state_errors'][k] != v for k,v in checks.items())):
        raise ValueError('compensated physical state checks disagree')
    if (type(trial['control_dof']) is not int or trial['control_dof'] != 6*count+1 or
            trial['target'] != .1-sample['drop'] or x[count,1] != trial['target'] or
            a['residual_norm'] != norm or not 0 <= norm <= 1e-11 or
            type(a['iterations']) is not int or not 0 <= a['iterations'] <= 16 or
            type(a['mixed_evaluations']) is not int or not 0 < a['mixed_evaluations'] <= 256*count or
            type(trial['reaction_derivative']) is not float or not math.isfinite(trial['reaction_derivative'])):
        raise ValueError('raw target/budget mismatch')
    zero = {'accumulated':0., 'plastic_coordinate':0.}
    if (a['origins'] != [[zero for _ in range(16)] for _ in range(count)] or
            any(s['response']['plastic_active'] is not False or s['response']['history'] != zero
                for e in response['elements'] for s in e['stations'])):
        raise ValueError('elastic onset history mismatch')
    checkpoints = trial['checkpoints']
    if len(checkpoints) != a['iterations']+1:
        raise ValueError('complete control checkpoint inventory required')
    previous = -1
    for i,c in enumerate(checkpoints):
        if (set(c) != {'iteration', 'mixed_evaluations', 'residual', 'reaction'} or
                type(c['iteration']) is not int or c['iteration'] != i or
                type(c['mixed_evaluations']) is not int or not previous < c['mixed_evaluations'] <= 256*count or
                type(c['residual']) is not float or not math.isfinite(c['residual']) or c['residual'] < 0. or
                type(c['reaction']) is not float or not math.isfinite(c['reaction'])):
            raise ValueError('invalid control checkpoint')
        previous = c['mixed_evaluations']
    if (checkpoints[-1]['mixed_evaluations'] != a['mixed_evaluations'] or
            checkpoints[-1]['residual'] != norm or checkpoints[-1]['reaction'] != -sample['load']):
        raise ValueError('control checkpoint terminal mismatch')
    if raw['checkpoint_sha256'] != state_hash(a) or not re.fullmatch('[0-9a-f]{64}',raw['origin_checkpoint_sha256']):
        raise ValueError('compensated checkpoint hash mismatch')
    spectra = classify_matrix(h,nodes=n,extent='ARCH_ONSET32')
    if shared.canonical(spectra) != shared.canonical(raw['spectra']):
        raise ValueError('raw spectral reconstruction mismatch')
    odd = spectra['out_of_plane']
    if (sample['lowest'] != odd['values'][0] or sample['uncertainty'] != odd['uncertainty_band'] or
            sample['negative'] != odd['negative'] or sample['unresolved'] != odd['unresolved']):
        raise ValueError('raw spectral summary mismatch')


def check_progress(folder, samples, raws, count):
    data = shared.ordinary(folder/'progress.jsonl')
    if len(data) > 8*(1<<20): raise ValueError('bounded onset progress required')
    rows = []
    for line in data.splitlines(keepends=True):
        row = json.loads(line,object_pairs_hook=coordinates._pairs,parse_constant=coordinates._constant)
        if shared.canonical(row) != line or set(row) != {'phase','id','event'}:
            raise ValueError('canonical onset progress schema required')
        rows.append(row)
    cursor = iter(rows)
    def marker(phase,label):
        if next(cursor,None) != {'phase':phase,'id':label,'event':None}:
            raise ValueError('onset progress phase/coverage mismatch')
    marker('INITIALIZATION',None)
    for sample in samples:
        label = sample['id'];trial = raws[label]['trial'];marker('STATE_START',label)
        events = []
        for row in cursor:
            if row == {'phase':'STATE_COMPLETE','id':label,'event':None}: break
            if row['phase'] != 'CONTROL' or row['id'] != label or not isinstance(row['event'],dict):
                raise ValueError('onset control progress mismatch')
            event = row['event'];metrics = event.get('metrics',{})
            if (set(event) != {'sequence','phase','iteration','backtrack','mixed_evaluations','metrics'} or
                    type(event['sequence']) is not int or event['sequence'] != len(events) or len(events)>=256 or
                    event['phase'] not in coordinates.METRICS or set(metrics) != coordinates.METRICS[event['phase']] or
                    type(event['mixed_evaluations']) is not int or not 0<=event['mixed_evaluations']<=256*count or
                    events and event['mixed_evaluations']<events[-1]['mixed_evaluations'] or
                    any(type(v) not in (int,float,str,bool) or type(v) is float and not math.isfinite(v) for v in metrics.values())):
                raise ValueError('bounded scalar control observations required')
            events.append(event)
        else: raise ValueError('missing state completion')
        if (not events or events[0]['phase'] != 'INITIALIZATION' or events[-1]['phase'] != 'CONVERGED' or
                any(e['phase']=='FAILURE' for e in events) or
                events[0]['metrics'] != {'target':trial['target'],'origin_epoch':trial['origin_epoch']} or
                events[-1]['metrics']['residual'] != trial['assembly']['residual_norm'] or
                events[-1]['mixed_evaluations'] != trial['assembly']['mixed_evaluations']):
            raise ValueError('completed control observation mismatch')
        checkpoints = [{'iteration':e['iteration'],'mixed_evaluations':e['mixed_evaluations'],
            'residual':e['metrics']['residual'],'reaction':e['metrics']['reaction']} for e in events if e['phase']=='ITERATION']
        if checkpoints != trial['checkpoints']: raise ValueError('observed checkpoint mismatch')
    marker('PROBE_COMPLETE',None);marker('COMPLETION',None)
    if next(cursor,None) is not None: raise ValueError('extra progress record')


def inspect_worker(folder, count, frozen, request_id, request_sha, *, schema):
    packet = shared.load(folder/'complete.json')
    if (set(packet) != {'schema','authority','request_id','request_sha256','result'} or
            packet['schema'] != schema or packet['authority'] != frozen or
            packet['request_id'] != request_id or packet['request_sha256'] != request_sha):
        raise ValueError('onset packet identity mismatch')
    result = packet['result'];samples = result['samples'];bindings = result['raw_bindings']
    if (not len(probe.search.DROPS) <= len(samples) <= len(probe.search.DROPS)+probe.search.MAX_BISECTIONS or
            len(bindings) != len(samples) or set(bindings) != {r['id'] for r in samples}):
        raise ValueError('onset bounded raw inventory mismatch')
    cursor = iter(samples);visited = {};raws = {}
    def evaluate(label,drop,origin):
        sample = next(cursor)
        if sample['id'] != label or sample['origin_id'] != origin or sample['drop'] != drop:
            raise ValueError('onset schedule/origin mismatch')
        b = bindings[label]
        if (set(b) != {'name','bytes','sha256'} or b['name'] != label+'.json' or
                type(b['bytes']) is not int or b['bytes'] <= 0):
            raise ValueError('raw binding schema mismatch')
        data = shared.ordinary(folder/b['name'])
        if len(data) != b['bytes'] or shared.sha(data) != b['sha256']:
            raise ValueError('raw hash mismatch')
        raw = shared.load(folder/b['name']);check_raw(raw,sample,count)
        raws[label] = raw
        epoch,origin_hash = (0,initial_hash(count)) if origin is None else visited[origin]
        if (type(raw['trial']['origin_epoch']) is not int or type(raw['trial']['assembly']['origin_epoch']) is not int or
                raw['trial']['origin_epoch'] != epoch or raw['trial']['assembly']['origin_epoch'] != epoch or
                raw['origin_checkpoint_sha256'] != origin_hash):
            raise ValueError('accepted origin state/epoch mismatch')
        visited[label] = (epoch+1,raw['checkpoint_sha256'])
        return raw['sample']
    rebuilt = probe.locate(evaluate);rebuilt.update(elements=count,raw_bindings=bindings)
    if next(cursor,None) is not None or shared.canonical(rebuilt) != shared.canonical(result):
        raise ValueError('onset adjudication mismatch')
    check_progress(folder,samples,raws,count)
    allowed = {b['name'] for b in bindings.values()} | {
        'complete.json','progress.jsonl','stdout.log','stderr.log','process-start.json','process.json'}
    if any(p.name not in allowed or not p.is_file() or p.is_symlink() for p in folder.iterdir()):
        raise ValueError('unregistered onset file')
    return packet
