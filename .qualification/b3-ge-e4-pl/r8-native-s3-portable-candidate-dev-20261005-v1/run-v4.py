"""Changed receiver/predecessor certificate controls; preserve v1 failure."""
from pathlib import Path
import hashlib, importlib.util, json, os, shutil, sys
ROOT = Path(__file__).resolve().parent;REPO = ROOT.parents[2]
BASE = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(BASE) == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec = importlib.util.spec_from_file_location('bounded', BASE)
s = importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.ROOT = ROOT;s.ENV.pop('PYTHONOPTIMIZE', None)
SITE = ROOT.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
s.ENV.update(NUMEXPR_NUM_THREADS='1', NUMBER_OF_CPUS='1', OPENBLAS_CORETYPE='Haswell')
s.ENV['PYTHONPATH'] = os.pathsep.join((str(SITE), str(REPO/'src'), str(REPO)))
previous = json.loads((ROOT/'binding-v1.json').read_text())
files = {name:sha(REPO/name) for name in previous['files']}
record = dict(files=files, runner_sha256=sha(__file__), entry_sha256=sha(ROOT/'entry-v4.py'),
    supervisor_sha256=sha(BASE), wheels=previous['wheels'],
    changed_input_reason='Error witness only; single unchanged old-seed physical/local association discriminator')
(ROOT/'binding-v4.json').write_text(json.dumps(record, indent=2)+'\n')
snapshot = ROOT/'executed-source-v4';snapshot.mkdir(exist_ok=False)
for name, expected in files.items():
    if name.endswith('.py'):
        destination = snapshot/name;destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO/name, destination);assert sha(destination) == expected
s.supervise([sys.executable, str(ROOT/'entry-v4.py')], 'focused-v4', 2*1024**3)


