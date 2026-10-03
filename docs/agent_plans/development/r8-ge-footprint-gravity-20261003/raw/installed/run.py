from pathlib import Path
import ast,hashlib,importlib.util,json,shutil,sys,zipfile
ROOT=Path(__file__).resolve().parent
REPO=Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
OLD=ROOT.parent/'r8-bl5-affine-flexible-v1/run.py'
spec=importlib.util.spec_from_file_location('owned_supervisor',OLD)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=ROOT
m.ENV['PYTHONPATH']=str(ROOT/'site')
TESTS=('test_stiffened_shell_ge_footprint_gravity.py','test_stiffened_shell_ge_body_load.py',
 'test_stiffened_shell_ge_gravity_owner.py','test_stiffened_shell_footprint_increment_charts.py')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='build':
  m.supervise([sys.executable,'-m','build','--wheel','--no-isolation','--outdir',str(ROOT/'dist'),str(REPO)],'build-run-v2',1024**3)
 elif mode=='install':
  wheels=list((ROOT/'dist').glob('*.whl'));assert len(wheels)==1
  m.supervise([sys.executable,'-m','pip','install','--no-deps','--no-index','--target',str(ROOT/'site'),str(wheels[0])],'install-run',1024**3)
 elif mode=='stage':
  (ROOT/'fixtures').mkdir();pending=list(TESTS);done=set()
  while pending:
   name=pending.pop()
   if name in done:continue
   path=REPO/'tests'/name;tree=ast.parse(path.read_text(encoding='utf-8'))
   shutil.copyfile(path,ROOT/'fixtures'/name);done.add(name)
   for node in ast.walk(tree):
    if isinstance(node,ast.ImportFrom) and node.module and node.module.startswith('test_'):
     assert '.' not in node.module;pending.append(node.module+'.py')
  for name in ('stiffened_shell_ge_footprint_gravity.py','stiffened_shell_ge_gravity.py'):
   shutil.copyfile(REPO/'examples'/name,ROOT/'fixtures'/name)
  (ROOT/'pytest.ini').write_text('[pytest]\naddopts = -p no:cacheprovider\n')
  wheel=next((ROOT/'dist').glob('*.whl'));modules={}
  source={'anysolver/'+p.relative_to(REPO/'src/anysolver').as_posix():p for p in (REPO/'src/anysolver').rglob('*.py')}
  with zipfile.ZipFile(wheel) as z:
   names={n for n in z.namelist() if n.startswith('anysolver/') and n.endswith('.py')}
   assert names==set(source) and len(names)==417
   for name in sorted(names):
    data=z.read(name);assert data==(ROOT/'site'/name).read_bytes()==source[name].read_bytes()
    modules[name]=hashlib.sha256(data).hexdigest()
  (ROOT/'binding.json').write_text(json.dumps(dict(source_parent='16cec54f',wheel=str(wheel),wheel_sha256=sha(wheel),module_sha256=modules,
   fixtures={p.name:sha(p) for p in (ROOT/'fixtures').iterdir()},supervisor_sha256=sha(OLD),scope='installed native footprint gravity development, not final graph/platform qualification'),indent=2)+'\n')
 elif mode=='tests':
  m.supervise([sys.executable,'-u',str(ROOT/'check.py'),'tests'],'installed-tests-run',1024**3)
 elif mode=='affected':
  m.supervise([sys.executable,'-u',str(ROOT/'check-affected.py'),'tests'],'installed-affected-v2',1024**3)
 elif mode=='example':
  m.supervise([sys.executable,'-u',str(ROOT/'check.py'),'example'],'example-run',1024**3)
 else:raise ValueError('build/install/stage/tests/example')
