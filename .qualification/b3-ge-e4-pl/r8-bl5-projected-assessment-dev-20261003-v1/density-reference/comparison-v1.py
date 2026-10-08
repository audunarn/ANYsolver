"""Read-only physical comparison of ONE same-geometry S4/S2 reference pair."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
from threadpoolctl import threadpool_info
FIELD=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001/scripts/r8_bl5_projected_ratio_comparison_dev.py')
if hashlib.sha256(FIELD.read_bytes()).hexdigest()!='a50a92d4f23c0d7419909a1edefbf91e75c060f9f04ec8dbba95aa79351d2c6c':
    raise ValueError('frozen field and physical-check helper required before import')
sys.path.insert(0,r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
from scripts.r8_bl5_projected_ratio_comparison_dev import field_errors, EXTERNAL_CHECKS

REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
ROOT=Path(__file__).resolve().parent
RAW=REPO/'.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1'
GROUP=REPO/'docs/agent_plans/development/r8-bl5-projected-assessment-20261003'
OWNER=RAW/'envelope/owners/ns64_b1_8/owner-v1'
CONTROL=RAW/'density-control'
def require(value,message):
    if not value: raise ValueError(message)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())

require(not sys.flags.optimize,'unoptimized guards required')
pools=threadpool_info();require(pools and all(p['num_threads']==1 for p in pools),'effective pools1 required')
out=ROOT/'comparison-v1.json';require(not out.exists(),'fresh comparison required')
bound={}
for name,pin in (('raw-manifest-v8.json','4c6ffe7a94e0553b83b67a4f420d11599ed05c1e89b99e5093388a0ad4b0f73a'),
                 ('raw-manifest-v11.json','c7223ba94c6ab964b977aaa39d783d616ab3c7f16f157125be5799fe882d4f01')):
    path=GROUP/name;require(sha(path)==pin,'frozen input manifest required')
    bound.update({REPO/row['path']:row['sha256'] for row in read(path)['files']})
used=[OWNER/'native/inputs.json',CONTROL/'prepared-v1.json',CONTROL/'prepared-v1.npz',
      CONTROL/'control-v1.json',CONTROL/'control-v1.npz',OWNER/'native/mz/physical-actions.json']
for path in used:require(sha(path)==bound[path],'bound original/child input required')
inputs=read(used[0]);control=read(CONTROL/'control-v1.json')
require(inputs['fixture_case']=='ns64_b1_8','fixed original model required')
xyz=np.array(inputs['xyz_m']);require(xyz.shape==(1122,3),'same physical nodes required')
with np.load(CONTROL/'prepared-v1.npz',allow_pickle=False) as data:
    parent=data['parent_q'].copy();load=data['load'].copy();fixed_indices=data['fixed'].copy()
with np.load(CONTROL/'control-v1.npz',allow_pickle=False) as data:child=data['q'].copy()
require(parent.shape==child.shape==load.shape==(6924,),'unchanged retained inventory required')
expected_load=np.zeros(6924);expected_load[6731]=10.
require(np.array_equal(load,expected_load),'same sole tipMz10Nm load required')
shell_ids=inputs['layout']['shell_node_ids'];index={node:i for i,node in enumerate(shell_ids)}
require(shell_ids==list(range(1,1106)) and inputs['layout']['beam_node_ids']==list(range(101,118)),
        'same physical ID/row mapping required')
cells=[tuple(index[node] for node in cell) for cell in inputs['shell_definition']['q4_elements']]
ids=list(range(1,1106))+list(range(100001,100018))
fixed={(d,n if d=='shell' else 100001+n-101,c) for d,n,c in inputs['layout']['fixed_coordinates']}
require(len(fixed)==107,'same fixed inventory required')
actual_fixed=sorted(6*((n-1) if d=='shell' else (1105+n-100001))+c for d,n,c in fixed)
require(np.array_equal(fixed_indices,np.array(actual_fixed)), 'same actual fixed columns required')
body_values={'E_PA':210e9,'NU':.3,'G_PA':210e9/2.6,'SHELL_THICKNESS_M':.035,
             'BEAM_AREA_M2':.01,'BEAM_TORSION_M4':1.6666666666666667e-5,
             'BEAM_BENDING_M4':8.333333333333333e-6,'BEAM_SHEAR_AREA_M2':.008}
report=dict(identity='BL5_FIXED_DENSITY_REFERENCE_PAIR_COMPARISON_DEV_V1',
            source_sha256=sha(Path(__file__)),inputs={str(p.relative_to(REPO)):sha(p) for p in used},
            field_source_sha256=sha(REPO/'scripts/r8_bl5_projected_ratio_comparison_dev.py'),
            effective_pools=pools,solve_count=0,qualification=False,formal_f03_authority_consumed=False,
            cases={},limitation='Supplementary OpenSees ASDShellQ4/classic beam bodies differ from native '
            'retained operators. No convergence, positivity, law selection or mandatory CalculiX acceptance.')
for supports,q in ((4,parent),(2,child)):
    folder=ROOT/f's{supports}-v1'
    records={name:read(folder/name) for name in ('summary.json','inputs.json','raw-inventory.json',
        'recovered-actions.json','inventory-predicates.json','preparation-controls.json')}
    summary,external,raw,actions=(records[name] for name in ('summary.json','inputs.json','raw-inventory.json','recovered-actions.json'))
    require(summary['status']=='completed' and summary['supports']==supports,'successful exact support case required')
    require(summary['source_sha256']=='87a76f7ecd69133da5a955c7a59b1c8b8467be26c23f9b84cf619f9a3a45554b'
            and sha(ROOT/'caller-v1.py')==summary['source_sha256'],'same archived actual external caller required')
    require(summary['binary_sha256']=='25ba42e1672526137d765d9c3631d1403e091f54f5afcdb9242f9243c63c3a96',
            'same bound external binary required')
    expected=external['expected_inventory'];predicates=records['inventory-predicates.json']
    require(set(expected)=={'nodes','elements','fixes','loads','model_commands','equations'}
            and set(predicates)==set(expected)|{'all_primary_poses','all_element_covectors'}
            and all(type(value) is bool and value for value in predicates.values()),'complete nonempty boolean inventory required')
    require(all(raw[key]==expected[key] for key in expected)
            and set(raw['poses'])==set(expected['nodes'])
            and set(raw['element_global_covectors'])==set(expected['elements']), 'independent raw inventory agreement required')
    checks=actions['checks']
    require(set(checks)==EXTERNAL_CHECKS and all(type(value) in (int,float)
            and np.isfinite(value) and 0<=value<=(1e-9 if name in
            ('average_five_channel_gap_scaled','emitted_coordinate_gap_scaled') else 1e-8)
            for name,value in checks.items()),'complete finite physical predicates required')
    execution=read(ROOT/f's{supports}-case-v1/execution.json')
    require(execution['status']=='completed' and execution['exit_code']==0,'terminal successful supervised case required')
    model=external['model']
    require((model['nx'],model['ny'],model['beam_intervals'],model['support_count'])==(64,16,16,supports),
            'same exact shell/beam geometry and density resolution required')
    external_xyz=np.array([model['nodes'][str(n)] for n in ids])
    require(external_xyz.shape==xyz.shape and np.max(np.abs(xyz-external_xyz))<=1e-13,'same reference physical coordinates required')
    efixed={('beam' if int(n)>=100001 else 'shell',int(n),c)
            for n,flags in model['fixes'].items() for c,flag in enumerate(flags) if flag}
    require(fixed==efixed,'same physical support/release law required')
    require(external['load']==[0.,0.,0.,0.,0.,10.],'same declared sole load required')
    load_commands=[args for name,args in external['command_recipe'] if name=='load']
    require(load_commands==[[model['beam_tip'],0.,0.,0.,0.,0.,10.]],'same actual sole load command required')
    for name,value in body_values.items():
        require(abs(external['sections'][name]-value)<=1e-13*max(abs(value),1e-12),'matched material/section required: '+name)
    poses=np.array([raw['poses'][str(n)] for n in ids]);nodal=q[:6732].reshape(1122,6)
    require(poses.shape==nodal.shape and np.isfinite(poses).all(),'complete finite physical poses required')
    moments=actions['continuous_density_measures']['polynomial_x_moments']
    region=actions['continuous_density_measures']['fixed_region_025_075']['open']
    parent_actions=read(OWNER/'native/mz/physical-actions.json') if supports==4 else control
    nw=float(q@load);ew=actions['work_J']['applied'];require(np.isfinite(ew) and ew>0,'finite positive observed external work required')
    report['cases'][str(supports)]=dict(native_work_J=nw,external_work_J=ew,
        work_difference_percent=100*(nw-ew)/ew,
        native_region_wrench=parent_actions['exact_region_wrench'],external_region_wrench=region,
        region_difference=(np.array(parent_actions['exact_region_wrench'])-np.array(region)).tolist(),
        native_integrated_beam_force=parent_actions['exact_transfer_moments'][0][:3],
        external_integrated_beam_force=moments['0'][:3],
        fields=dict(shell=field_errors(nodal[:1105],poses[:1105],cells,xyz[:1105]),
                    beam=field_errors(nodal[1105:],poses[1105:],[(i,i+1) for i in range(16)],xyz[1105:],True)),
        physical_checks=actions['checks'],
        external_inputs={name:sha(folder/name) for name in records})
four,two=(report['cases'][str(s)] for s in (4,2))
report['contrast']=dict(native_work_change_percent=100*(two['native_work_J']-four['native_work_J'])/four['native_work_J'],
    external_work_change_percent=100*(two['external_work_J']-four['external_work_J'])/four['external_work_J'],
    native_region_Mz_change=two['native_region_wrench'][5]-four['native_region_wrench'][5],
    external_region_Mz_change=two['external_region_wrench'][5]-four['external_region_wrench'][5])
report['status']='COMPLETED_DEVELOPMENT_COMPARISON'
out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({'status':report['status'],'contrast':report['contrast'],
                  'work_difference_percent':{s:item['work_difference_percent'] for s,item in report['cases'].items()}}))
