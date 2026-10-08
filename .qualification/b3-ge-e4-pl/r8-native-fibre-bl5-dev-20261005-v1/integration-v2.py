from pathlib import Path
import hashlib,importlib.util,json,os,sys
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
BASE=Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(BASE)=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec=importlib.util.spec_from_file_location('bounded',BASE);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.ROOT=ROOT;s.ENV.pop('PYTHONOPTIMIZE',None);s.ENV.pop('OPENBLAS_CORETYPE',None)
s.ENV.update(NUMEXPR_NUM_THREADS='1',NUMBER_OF_CPUS='1')
CI=ROOT.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
SITE=ROOT/'installed-v1'
binding=json.loads((ROOT/'installed-binding-v1.json').read_text())
assert binding['source']=={name:sha(REPO/name) for name in binding['source']}
assert sha(ROOT/'wheel-v1'/binding['wheel'])==binding['wheel_sha256']
binding.update(runner_sha256=sha(__file__),entry_sha256=sha(ROOT/'installed-entry-v2.py'),
 changed_input_reason='Append repository namespace after installed+CI sites for examples collection; same wheel/product')
(ROOT/'installed-binding-v2.json').write_text(json.dumps(binding,indent=2)+'\n')
s.ENV['PYTHONPATH']=os.pathsep.join((str(SITE),str(CI),str(REPO)))
s.supervise([sys.executable,str(ROOT/'installed-entry-v2.py')],'installed-example-v2',2*1024**3)
