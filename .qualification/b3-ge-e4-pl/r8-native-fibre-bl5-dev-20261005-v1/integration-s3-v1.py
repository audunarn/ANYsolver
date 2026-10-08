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
s.ENV['PYTHONPATH']=str(CI)
binding=json.loads((ROOT/'binding-s3-v1.json').read_text())
assert binding['files']=={name:sha(REPO/name) for name in binding['files']}
package={str(p.relative_to(REPO/'src')):sha(p) for p in (REPO/'src/anysolver').rglob('*.py')}
(ROOT/'source-package-modules-s3-v1.json').write_text(json.dumps(package,indent=2)+'\n')
wheel_dir=ROOT/'wheel-s3-v1';wheel_dir.mkdir(exist_ok=False)
s.supervise([sys.executable,'-m','pip','wheel',str(REPO),'--no-deps','--no-build-isolation','--no-index','--wheel-dir',str(wheel_dir)],'build-s3-v1',2*1024**3)
wheels=list(wheel_dir.glob('*.whl'));assert len(wheels)==1,wheels
SITE=ROOT/'installed-s3-v1';assert not SITE.exists()
s.supervise([sys.executable,'-m','pip','install','--no-deps','--no-index','--target',str(SITE),str(wheels[0])],'install-s3-v1',2*1024**3)
(ROOT/'installed-binding-s3-v1.json').write_text(json.dumps(dict(source=binding['files'],wheel=wheels[0].name,wheel_sha256=sha(wheels[0]),
 runner_sha256=sha(__file__),entry_sha256=sha(ROOT/'installed-entry-s3-v1.py'),package_manifest_sha256=sha(ROOT/'source-package-modules-s3-v1.json')),indent=2)+'\n')
s.ENV['PYTHONPATH']=os.pathsep.join((str(SITE),str(CI),str(REPO)))
s.supervise([sys.executable,str(ROOT/'installed-entry-s3-v1.py')],'installed-example-s3-v1',2*1024**3)
