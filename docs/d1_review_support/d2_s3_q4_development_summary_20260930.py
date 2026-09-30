"""Retain current development identities and completed test dispositions."""
from pathlib import Path
import hashlib,json,sys,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[2]
raw=Path(__file__).resolve().parent
output=raw/'d2_s3_q4_development_summary_v1_20260930.json'
assert not output.exists()
names=['s3_q4_overlap_derivatives.py','s3_q4_swept.py','q4_s3_overlap_derivatives.py',
       'core.py','s3_patch_static.py','s3_patch_augmented.py','s3_patch_mortar_energy.py','static_path.py']
paths=[root/'src/anysolver/general_contact'/name for name in names]
paths.append(root/'tests/test_general_contact_s3_q4_static_dev.py')
identities={}
for path in paths:
    data=path.read_bytes()
    snapshot=raw/f'd2_s3_q4_final_20260930.{path.name}.snapshot'
    assert not snapshot.exists()
    snapshot.write_bytes(data)
    identities[str(path.relative_to(root))]={'sha256':hashlib.sha256(data).hexdigest(),
                                          'snapshot':str(snapshot.relative_to(root))}
runs={}
for stem in [f'd2_s3_q4_static_v{i}_20260930' for i in range(1,5)]+[
             f'd2_s3_q4_deforming_target_v{i}_20260930' for i in (1,2)]:
    resource=json.loads((raw/f'{stem}.resources.json').read_text())
    suites=ET.parse(raw/f'{stem}.xml').getroot().findall('testsuite')
    counts={k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
    runs[stem]={'resource':resource,'counts':counts,'files':{suffix:
        hashlib.sha256((raw/f'{stem}.{suffix}').read_bytes()).hexdigest()
        for suffix in ('resources.json','log','xml')}}
record={'status':'implemented_and_locally_tested','scientifically_accepted':False,'released':False,
 'scope':'two S3 source faces, one original Q4 target; elastic small rotation projected finite penalty',
 'source_identity_scope':'final current source; earlier development runs retain their historical differences',
 'identities':identities,'runs':runs,'python_executable':sys.executable,
 'distinct_integrated_checks':5,
 'limitations':['no installed promotion or broader spatial/warped/CCD admission',
 'pure rigid-source press with zero contact-free reaction predictor is rejected',
 'near-cancelled S3/Q4 scalar disagreement rejects; no shape3 roundoff proof generalized',
 'adaptive derivative controls are measured differences, not certified true quadrature error'],
 'retained_failures':{'static_v1':'path converged but test used nonexistent result accessor',
 'static_v2':'wrong public API keyword rejected before solve',
 'deforming_target_v1':'pure-displacement contact-free rigid-source force predictor exactly zero; admission rejection'},
 'reference':'independent simplex P1-Q1 polynomial moments and existing linear structural operator; 4-row KKT enumeration, small-motion discrepancy bounded by 1e-6 comparisons'}
output.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'output':str(output),'source_files':len(identities),'runs':len(runs),
                  'summary_sha256':hashlib.sha256(output.read_bytes()).hexdigest()}))
