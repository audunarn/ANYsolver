"""Stricter same-cell review on retained states; no mechanical reevaluation."""
from pathlib import Path
from types import SimpleNamespace as NS
import hashlib, importlib.util, json, sys
import numpy as np
from scipy.spatial.transform import Rotation

root = Path(__file__).resolve().parent
repo = root.parents[2]
case = root/'pytest-v1/test_loaded_native_fibre_cycli0'
sys.path.insert(0,str(repo/'tests'))
spec = importlib.util.spec_from_file_location('chart_test',repo/'tests/test_stiffened_shell_native_plastic_chart.py')
test = importlib.util.module_from_spec(spec); spec.loader.exec_module(test)
sha = lambda b:hashlib.sha256(b).hexdigest()
def station(element,cell,increment):
    return NS(element_id=element,cell=cell,fibres=(NS(plastic_increment=(increment,0.)),))
def result(position,cellframes,stations):
    return dict(result=NS(load_position=position,cell_frames=np.array((np.tile(np.eye(3),(2,1,1)),cellframes)),
                         beam_fibre_material=stations))
# Reject exactly the reviewed counterexample: rotation in cell0, flow in cell1.
a = Rotation.from_rotvec((.1,0.,0.)).as_matrix()
b = Rotation.from_rotvec((0.,.1,0.)).as_matrix()@a
first = result(1.,np.array((a,np.eye(3))),(station(2,0,0.),station(2,1,1e-4)))
wrong = result(2.,np.array((b,np.eye(3))),(station(2,0,0.),station(2,1,1e-4)))
assert test.active_noncommuting_positions([first,wrong]) == []
right = result(2.,np.array((b,np.eye(3))),(station(2,0,1e-4),station(2,1,0.)))
assert [v['cell'] for v in test.active_noncommuting_positions([first,right])] == [0]
wrong_member = result(2.,np.array((b,np.eye(3))),(station(1,0,1e-4),station(2,1,0.)))
assert test.active_noncommuting_positions([first,wrong_member]) == []
digests = {}
def read(path):
    raw = path.read_bytes(); digests[path.relative_to(root).as_posix()] = sha(raw)
    return raw
def snapshot(folder):
    data = json.loads(read(folder/'material.json'))
    with np.load(folder/'state.npz',allow_pickle=False) as saved:
        arrays = {name:np.array(saved[name],copy=True) for name in saved.files}
    read(folder/'state.npz'); read(folder/'checkpoint.bin')
    r = data['result']
    stations = tuple(NS(element_id=s['element_id'],cell=s['cell'],fibres=tuple(
        NS(plastic_increment=f['plastic_increment']) for f in s['fibres']))
        for s in r['beam_fibre_material'])
    return dict(result=NS(load_position=r['load_position'],beam_frames=arrays['beam_frames'],
        cell_frames=arrays['cell_frames'],beam_fibre_material=stations),
        shell_frames=arrays['shell_frames'],raw_result=r)
def sequence(label):
    folders = sorted(case.glob(label+'-*'),key=lambda p:int(p.name.split('-')[-1]))
    return [snapshot(p) for p in folders if p.is_dir()]
prefix = sequence('prefix')
before = json.loads(read(case/'before-rebase/material.json'))['result']
after = json.loads(read(case/'after-rebase/material.json'))['result']
restored = json.loads(read(case/'chart-restored/material.json'))['result']
assert after['generation'] == before['generation']+1 == restored['generation']
assert before['load_position'] == after['load_position'] == restored['load_position'] == 1.
assert test.has_flow(prefix[-1]['result'])
values = {}
reference_positions = None
for branch in ('control','reset','restored'):
    following = sequence(branch)
    path = prefix+following
    positions = [v['result'].load_position for v in path]
    if reference_positions is None: reference_positions = positions
    else: assert positions == reference_positions
    active = test.active_noncommuting_positions(path)
    assert active, branch
    measured = {field:test.coverage(path,field)
                for field in ('shell','beam','cell','fibre_nodes','fibre_cells')}
    assert all(v['rotation_rad']>=.05 and v['commutator_rad']>=1e-5 for v in measured.values())
    assert positions[-1] == 4.
    values[branch] = dict(coverage=measured, same_cell_active_positions=active, accepted_positions=positions)
proof = dict(scope='stricter matching-cell validation of exact retained installed numerical run',
    cross_cell_false_positive_rejected=True, wrong_member_false_positive_rejected=True,
    matching_positive_control_passed=True, actual_generation_increment=1,
    prefix_actual_flow=True, branches=values, input_sha256=sha(read(case/'input.json')),
    test_sha256=sha((repo/'tests/test_stiffened_shell_native_plastic_chart.py').read_bytes()),
    data_sha256=digests, no_mechanical_reevaluation=True)
(root/'saved-proof-v1.json').open('x').write(json.dumps(proof,indent=2)+'\n')
print(json.dumps(dict(branches=len(values), generation_increment=1,
                     same_cell_active_counts={k:len(v['same_cell_active_positions']) for k,v in values.items()})))
