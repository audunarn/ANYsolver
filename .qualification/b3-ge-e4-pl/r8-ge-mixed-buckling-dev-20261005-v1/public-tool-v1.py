"""Check new diagnostic output through the already verified installed artifact."""
from pathlib import Path
import hashlib, importlib.util, json, os, sys
RAW = Path(__file__).resolve().parent
REPO = RAW.parents[2]
BASE = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
binding = json.loads((RAW/'integration-binding-v1.json').read_text())
assert all(hashlib.sha256((REPO/name).read_bytes()).hexdigest() == digest for name, digest in binding['files'].items())
spec = importlib.util.spec_from_file_location('bounded_public_tool', BASE)
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
s.ROOT = RAW; s.ENV.pop('PYTHONOPTIMIZE', None)
s.ENV.update(NUMEXPR_NUM_THREADS='1', NUMBER_OF_CPUS='1')
s.ENV['PYTHONPATH'] = os.pathsep.join((str(RAW/'site-integration-v1'), str(REPO)))
s.supervise([sys.executable, str(REPO/'scripts/r8_ge_mixed_buckling_dev.py'),
    '--output', str(RAW/'installed-tool-output-v1')], 'installed-tool-v1', 2*1024**3)
record = json.loads((RAW/'installed-tool-output-v1/status.json').read_text())
assert record['status'] == 'COMPLETED_DEVELOPMENT'
assert Path(record['imports']['anysolver']).resolve().is_relative_to(RAW/'site-integration-v1')
print('Installed diagnostic output completed; checkpoint and sparse packets retained.')
