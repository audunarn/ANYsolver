"""Read-only exact evidence aggregation; no numerical solve or adjudication."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
OLD=REPO/'.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1'
reuse={'ns16_b1_2':OLD/'ratios/whole_half/owner-v1',
       'ns16_b2':OLD/'ratios/whole_double/owner-v1',
       'ns32_b1':OLD/'joint32/installed-v2/owner'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
wheel='1bf7dabd8771e76ed09825fb66a89e3e48d513dbb0321989c41701096a679632'
out=dict(identity='PROJECTED_BL5_ENVELOPE_DEVELOPMENT_AGGREGATE_V1',
    source_parent='a7327da2', qualification=False, formal_f03_authority_consumed=False,
    limitation='Actual installed physical checks and scalar eligibility, not full native beta/stability/engineering convergence.',cases={})
source_snapshots={sha(p):str(p) for directory in ('sources-v1','sources-v2','sources-v3','sources-v4')
    for p in (ROOT/directory).glob('*.py')}
for nx in (16,32,64):
 for ratio in ('1_8','1_4','1_2','1','2','4','8'):
  name=f'ns{nx}_b{ratio}';version=2 if name in ('ns64_b4','ns64_b8') else 1
  reg=ROOT/'registrations'/name/f'registration-v{version}.json';r=json.loads(reg.read_text())
  assert r['status']=='REGISTERED_ENVELOPE_DEVELOPMENT_BOUND' and all(v is True for v in r['predicates'].values())
  assert r['arrays_sha256']==sha(reg.with_suffix('.npz')) and r['source_sha256'] in source_snapshots
  folder=reuse.get(name,ROOT/'owners'/name/'owner-v1');owner=json.loads((folder/'summary.json').read_text())
  assert owner['status']=='COMPLETED_INSTALLED_DEVELOPMENT_ONLY' and owner['fixture']==r['fixture']
  assert owner['wheel_sha256']==wheel and owner['matching_modules']==417
  assert owner['factorization_count']==1 and owner['accurate_refinements']==6
  assert owner['module_sha256']==json.loads((ROOT/'owners/ns16_b1_8/owner-v1/summary.json').read_text())['module_sha256']
  for filename,digest in owner['native_input_sha256'].items():assert sha(folder/'native'/filename)==digest
  # Archived owners keep their original binding. Reuse never rewrites a report.
  reg_binding=owner['registration'];oldreg=Path(reg_binding['json_path'])
  if name not in reuse:assert sha(oldreg)==reg_binding['json_sha256'] and sha(oldreg.with_suffix('.npz'))==reg_binding['arrays_sha256']
  maxcheck=max(max(case['physical_checks'].values()) for case in owner['cases'].values())
  assert maxcheck <= 1e-8
  row=dict(fixture=r['fixture'],counts=r['counts'],supported_kkt_count=r['supported_kkt_count'],
      scalar_json=str(reg),scalar_sha256=sha(reg),scalar_source=r['source_sha256'],
      scalar_reference_error=r['numerical']['reference_error'],scalar_safe_floor=r['safe_case_floor'],
      owner=str(folder),owner_summary_sha256=sha(folder/'summary.json'),
      owner_source_sha256=owner['source_sha256'],reused_unchanged_installed_owner=name in reuse,
      maximum_physical_check=maxcheck,work_J={load:owner['cases'][load]['work_J'] for load in ('fy','mx','mz')})
  if name not in reuse:
   assert owner['source_sha256'] in source_snapshots
   execution=ROOT/f'owner-{name}-v1/execution.json';run=json.loads(execution.read_text())
   row['resources']={key:run[key] for key in ('elapsed_seconds','sampled_peak_tree_bytes','sampled_numeric_or_unresolved_max')}
  out['cases'][name]=row
out['finest_relative_work_change_percent']={ratio:{load:100*(out['cases'][f'ns64_b{ratio}']['work_J'][load]/out['cases'][f'ns32_b{ratio}']['work_J'][load]-1)
    for load in ('fy','mx','mz')} for ratio in ('1_8','1_4','1_2','1','2','4','8')}
out['summary']=dict(cases=21,new_native=18,reused_native=3,
    max_physical_check=max(row['maximum_physical_check'] for row in out['cases'].values()),
    max_sampled_peak_bytes=max(row['resources']['sampled_peak_tree_bytes'] for row in out['cases'].values() if 'resources' in row),
    max_sampled_numeric_or_unresolved=max(row['resources']['sampled_numeric_or_unresolved_max'] for row in out['cases'].values() if 'resources' in row),
    max_elapsed_seconds=max(row['resources']['elapsed_seconds'] for row in out['cases'].values() if 'resources' in row))
with (ROOT/'aggregate-v1.json').open('x') as handle:json.dump(out,handle,indent=2,allow_nan=False)
print(json.dumps(out['summary']))
print(json.dumps(out['finest_relative_work_change_percent']))
