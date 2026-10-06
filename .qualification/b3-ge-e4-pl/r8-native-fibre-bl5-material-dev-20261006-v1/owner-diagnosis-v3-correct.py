"""Correct role labels only; preserve reviewed original diagnosis bytes."""
from pathlib import Path
import copy, hashlib, json
ROOT=Path(__file__).resolve().parent
source=ROOT/'owner-diagnosis-v3.json'
data=json.loads(source.read_text());fixed=copy.deepcopy(data)
def role(j):
    if j<48:return 'shell_pose'
    if j<78:return 'beam_nodal_pose'
    if j<84:return 'beam1_cell_rotation'
    if j<102:return 'beam1_resultant'
    if j<108:return 'beam2_cell_rotation'
    if j<126:return 'beam2_resultant'
    return 'multiplier'
for step in fixed['derivatives']:
    for row in step['rows']:
        terms=row.pop('kinematic_terms')+row.pop('moment_or_force_step_terms')
        for term in terms:term['role']=role(term['column'])
        row['kinematic_terms']=[t for t in terms if t['role'] not in ('beam1_resultant','beam2_resultant','multiplier')]
        row['retained_material_terms']=[t for t in terms if t['role'] in ('beam1_resultant','beam2_resultant')]
        row['multiplier_terms']=[t for t in terms if t['role']=='multiplier']
        assert len(terms)==len(row['kinematic_terms'])+len(row['retained_material_terms'])+len(row['multiplier_terms'])
fixed['label_correction']=dict(original_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    original_preserved=str(source),reason='j<108 incorrectly included beam1resultants84:102 in kinematic label; total errors and row attribution unchanged',
    explicit_mapping='shell0:48,nodal48:78,beam1cells78:84/resultants84:102,beam2cells102:108/resultants108:126,multipliers126:146',
    ULP_limitation='ULP(.25) is a characteristic scalar scale, not a proven absolute-coordinate update floor; source uses compensated reference/displacement high/low pairs')
target=ROOT/'owner-diagnosis-v3-corrected.json';assert not target.exists();target.write_text(json.dumps(fixed,indent=2)+'\n')
print(json.dumps(dict(original_preserved=True,original_sha256=fixed['label_correction']['original_sha256'],corrected_rows=12)))
