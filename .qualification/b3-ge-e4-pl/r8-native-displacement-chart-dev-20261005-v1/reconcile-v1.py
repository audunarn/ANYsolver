"""Non-numerical evidence reconciliation; preserves original run records."""
from pathlib import Path
import hashlib,json,shutil,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
RAW=Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,value):
    path=RAW/name
    if path.exists():raise RuntimeError(f'preserved output already exists: {path}')
    path.write_bytes((json.dumps(value,indent=2)+'\n').encode('ascii'))
def counts(path):
    tree=ET.parse(path)
    cases=tree.findall('.//testcase')
    return dict(total=len(cases),failures=sum(c.find('failure') is not None for c in cases),
                errors=sum(c.find('error') is not None for c in cases),
                skipped=sum(c.find('skipped') is not None for c in cases))
execution=json.loads((RAW/'installed-v1/execution.json').read_bytes())
assert execution['status']=='failed' and execution['exit_code']==1
first=counts(RAW/'installed-junit-v1.xml')
last=counts(RAW/'installed-junit-v3.xml')
assert first==dict(total=27,failures=3,errors=0,skipped=0)
assert last==dict(total=6,failures=0,errors=0,skipped=0)
final=json.loads((RAW/'installed-result-v3.json').read_bytes())
assert final['status']=='PASSED_NATIVE_CHART_INSTALLED_NOT_QUALIFIED'
save('installed-result-v1-terminal.json',dict(
    status='FAILED_OBSOLETE_TEST_EXPECTATIONS',counts=first,
    execution=execution,original_result_sha256=digest(RAW/'installed-result-v1.json'),
    junit_sha256=digest(RAW/'installed-junit-v1.xml'),
    disposition='Three legacy error-message expectations corrected; original failed run retained. '
                'Six changed/new rows passed in installed v3 on the identical wheel. '
                'Together the runs cover 27 impacted cases; v1 itself remains failed.'))
source=Path('C:/Users/AudunArnesenNyhus/AppData/Local/Temp/anysolver-portable-ci-c8g8_k8t/P01')
target=RAW/'source-check-v1';target.mkdir(exist_ok=False)
for name in ('resource.json','runtime.json','selection.json'):shutil.copyfile(source/name,target/name)
files=[p for p in (ROOT/'src/anysolver').glob('_stiffened_shell*.py')]
files += [ROOT/'tests/test_stiffened_shell_native_displacement_chart.py',
          ROOT/'tests/test_stiffened_shell_native_point_displacement.py']
save('reconciled-source-inputs-v1.json',dict(
    status='RECONCILED_DEVELOPMENT_EVIDENCE_NOT_QUALIFICATION',
    installed_v1=first,installed_v3=last,
    source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in files},
    solver_wheel_sha256=final['artifacts']['solver']['sha256'],
    consumer_wheel_sha256=final['artifacts']['fem']['sha256']))
print('Terminal failed-run disposition preserved; source runtime records copied; installed coverage reconciled.')
