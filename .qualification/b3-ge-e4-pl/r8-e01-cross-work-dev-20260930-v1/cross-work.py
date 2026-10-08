"""Saved-field cross-work allocation; no solver, matrix or parameter changes."""
from pathlib import Path
from hashlib import sha256
import json, math

root=Path('C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
source=root/'.qualification/b3-ge-e4-pl/r8-e01-pure-torque-dev-20260929-v4'
paths=[source/'native-shell-action.json',source/'external-shell-action.json']
n,e=[json.loads(p.read_text()) for p in paths]
sn=n['native_coupled_shell_displacements']
se=e['external_coupled_shell_displacements']
an,ae=n['loads'],e['loads']
ids=sorted(set(sn)|set(se)|set(an)|set(ae),key=int)
assert set(sn)==set(se) and len(ids)==45
for field in [sn,se,an,ae]:
    assert all(len(row)==6 and all(math.isfinite(v) for v in row) for row in field.values())
zero=[0.]*6
columns=[math.fsum(an.get(i,zero)[j]*se[i][j]-ae.get(i,zero)[j]*sn[i][j]
                   for i in ids) for j in range(6)]
total=math.fsum(columns)
expected=100.*(se['9'][3]-sn['9'][3])
membrane=math.fsum(columns[j] for j in [0,1,5])
plate=math.fsum(columns[j] for j in [2,3,4])
rootids=[str(1+9*j) for j in range(5)]
assert all(max(abs(v) for v in sn[i]+se[i])<1e-12 for i in rootids)
record={'classification':'E01 saved-field work discriminator; development only',
        'inputs':{str(p.relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in paths},
        'runner_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
        'shell_nodes':len(ids),'torque_nm':100.,'root_nodes':rootids,
        'columns':['ux','uy','uz','rx','ry','rz'],
        'cross_work_j':columns,'total_j':total,'expected_tip_cross_work_j':expected,
        'closure_relative':abs(total-expected)/max(abs(total),abs(expected),1e-12),
        'membrane_drill_j':membrane,'plate_j':plate,
        'membrane_signed_fraction':membrane/total,'plate_signed_fraction':plate/total,
        'note':'Signed reciprocal cross-work; neither positive energies nor F03 norms.'}
out=Path('C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-e01-cross-work-v1.json')
if out.exists(): raise FileExistsError(out)
out.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:record[k] for k in ['total_j','expected_tip_cross_work_j',
       'closure_relative','membrane_drill_j','plate_j','membrane_signed_fraction']}))
