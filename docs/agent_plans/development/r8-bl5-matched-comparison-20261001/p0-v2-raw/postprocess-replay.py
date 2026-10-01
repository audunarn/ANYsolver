"""Read-only provenance replay; original native-comparison.json is unchanged."""
from pathlib import Path
import ast,hashlib,json,math,tempfile
import numpy as np
r=Path(tempfile.gettempdir())
out=r/'r8-bl5-external-p0-enforcement-v2/native-comparison-replay.json'
assert not out.exists()
src=Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/scripts/b3_e4_bl5_matched_mz_native_dev.py')
original=json.loads((r/'r8-bl5-external-p0-enforcement-v2/native-comparison.json').read_text())
assert hashlib.sha256(src.read_bytes()).hexdigest()==original['collector_source_sha256']
for p,h in original['bound_inputs'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
tree=ast.parse(src.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='field_errors')
scope={'np':np,'math':math,'LREF_M':1.}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(src),'exec'),scope)
with np.load(r/'r8-bl5-matched-mz-native-v1/mz/raw-state.npz') as z:
 q=z['q'][:708].reshape(118,6).copy();xyz=z['xyz_m'].copy();ids=z['external_ids'].copy()
data=json.loads((r/'r8-bl5-external-p0-enforcement-v2/case/recovered-actions.json').read_text())
model=json.loads((r/'r8-bl5-external-p0-enforcement-v2/case/inputs.json').read_text())['model']
external=np.array([data['full_q_node_poses'][str(n)] for n in ids])
index={int(n):i for i,n in enumerate(ids)}
fields={name:scope['field_errors'](q,external,[[index[n] for n in c] for c in model[name+'_cells']],xyz,beam=name=='beam') for name in ('shell','beam')}
for name in fields:
 for key,value in fields[name].items():assert np.array_equal(np.asarray(value),np.asarray(original['native_vs_external_P0_common_fields'][name][key]))
out.write_text(json.dumps({'classification':'read-only provenance replay, not another solve; exact field results match original', 'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'original_output_sha256':hashlib.sha256((out.parent/'native-comparison.json').read_bytes()).hexdigest(),'collector_sha256':original['collector_source_sha256'],'bound_inputs':original['bound_inputs'],'fields':fields,'product_imports':[]},indent=2)+'\n')
print('Read-only replay matches every common-field component; original retained')
