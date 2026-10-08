from pathlib import Path
import hashlib, importlib.util, json, os, shutil, sys
ROOT=Path(__file__).resolve().parent; REPO=ROOT.parents[2]
BASE=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(BASE)=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec=importlib.util.spec_from_file_location('bounded',BASE);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.ROOT=ROOT;s.ENV.pop('PYTHONOPTIMIZE',None);s.ENV.pop('OPENBLAS_CORETYPE',None)
SITE=ROOT.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
s.ENV.update(NUMEXPR_NUM_THREADS='1',NUMBER_OF_CPUS='1')
s.ENV['PYTHONPATH']=os.pathsep.join((str(SITE),str(REPO/'src'),str(REPO)))
names=('src/anysolver/_stiffened_shell_ge_experimental.py','src/anysolver/_stiffened_shell_ge_finite_experimental.py',
 'src/anysolver/_stiffened_shell_ge_point_buckling.py','src/anysolver/_stiffened_shell_bl5_native_elastic.py',
 'src/anysolver/stiffened_shell.py','examples/stiffened_shell_native_fibre_bl5.py','tests/test_stiffened_shell_native_fibre_bl5.py')
files={name:sha(REPO/name) for name in names}
previous=json.loads((ROOT.parent/'r8-native-s3-portable-candidate-dev-20261005-v1/binding-v5.json').read_text())
record=dict(files=files,runner_sha256=sha(__file__),entry_sha256=sha(ROOT/'entry-v2.py'),supervisor_sha256=sha(BASE),
 wheels=previous['wheels'],reason='Separate raw/published pencil identities; fresh corruption control; affected10 only, unchanged4 reused')
(ROOT/'binding-v2.json').write_text(json.dumps(record,indent=2)+'\n')
snapshot=ROOT/'executed-source-v2';snapshot.mkdir(exist_ok=False)
for name,expected in files.items():
 target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/name,target);assert sha(target)==expected
s.supervise([sys.executable,str(ROOT/'entry-v2.py')],'focused-v2',2*1024**3)

