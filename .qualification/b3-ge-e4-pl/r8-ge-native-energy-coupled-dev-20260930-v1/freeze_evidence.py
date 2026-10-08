from pathlib import Path
import hashlib,json,shutil,xml.etree.ElementTree as ET
repo=Path('C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
temp=Path('C:/Users/AudunArnesenNyhus/AppData/Local/Temp')
installed=temp/'r8-ge-native-energy-coupled-installed-v1'
consumer=temp/'r8-ge-native-energy-coupled-consumer-v1'
evidence=repo/'.qualification/b3-ge-e4-pl/r8-ge-native-energy-coupled-dev-20260930-v1'
assert not evidence.exists(), 'evidence cannot be overwritten'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for root,expected in ((installed,124),(consumer,7)):
    execution=json.loads((root/'execution.json').read_text())
    assert execution['exit_code']==0 and execution['status']=='passed'
    suites=ET.parse(root/'inventory.xml').getroot().findall('testsuite')
    assert sum(int(row.attrib['tests']) for row in suites)==expected
    assert all(int(row.attrib[key])==0 for row in suites for key in ('failures','errors','skipped'))
    manifest=json.loads((root/'manifest.json').read_text())
    assert all(sha(root/path)==digest for path,digest in manifest['inputs'].items())
evidence.mkdir()
for root,destination in ((installed,'solver'),(consumer,'consumer')):
    target=evidence/destination;target.mkdir()
    manifest=json.loads((root/'manifest.json').read_text())
    paths=list(manifest['inputs'])+['manifest.json','installed.log','inventory.xml',
         'identity.json','imports.json','execution.json']
    if destination=='solver':
        paths+=['build.log','install.log','examples.json']
        paths+=['wheels/'+name for name in manifest['wheels']]
    for name in paths:
        (target/name).parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/name,target/name)
    if destination=='consumer':
        for path in (root/'pytest-tmp').rglob('*.anyfem-ge.json'):
            name=path.relative_to(root/'pytest-tmp')
            (target/'inputs'/name).parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target/'inputs'/name)
source=evidence/'source';source.mkdir()
for name in ('r8-ge-fibre-energy-source-v1.log','r8-ge-native-coupled-source-v1.log',
             'r8-ge-native-coupled-source-v2.log','r8-ge-native-energy-coupled-source-v3.log'):
    shutil.copyfile(temp/name,source/name)
for name in ('r8-ge-native-energy-coupled-prepare.py','r8-ge-native-energy-coupled-consumer-prepare.py'):
    shutil.copyfile(temp/name,evidence/name)
binding={'solver_product':'565685c1ea6fa1a42509f132a8bd4396977ca709',
 'consumer_runtime':'a615c4b299e603264f67d292c8a4415168b1b9c6',
 'consumer_tests_base':'268001efc9102b46ffeb6ea776472a26205b4152',
 'consumer_tests_sha256':sha(consumer/'tests/test_experimental_stiffened_shell_consumer.py'),
 'foreign_dirty_path_excluded':'scripts/b3_e4_f03_c1_fy_supported_reference.py',
 'classification':'Level-A experimental integration; no aggregate/scientific qualification gate closed',
 'early_source_probe_identity':'logs and known fixture changes retained; no exact full-source catalog claim for early probes'}
(evidence/'source-binding.json').write_text(json.dumps(binding,indent=2))
print(json.dumps({'evidence':str(evidence),'files':sum(p.is_file() for p in evidence.rglob('*'))}))
