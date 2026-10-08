from pathlib import Path
import ast,hashlib,importlib.util,json,os,shutil,sys,zipfile
ROOT=Path(__file__).resolve().parent
REPO=Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
spec=importlib.util.spec_from_file_location('owned_supervisor',ROOT.parent/'r8-bl5-affine-flexible-v1/run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=ROOT
m.ENV['PYTHONPATH']=os.pathsep.join((str(ROOT.parent/'r8-ge-footprint-gravity-installed-v1/site'),str(REPO)))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
mode=sys.argv[1]
if mode=='math':
 (ROOT/'pytest.ini').write_text('[pytest]\naddopts = -p no:cacheprovider\n')
 (ROOT/'fixtures').mkdir()
 for name in ('test_r8_bl5_projected_reference_action_dev.py','test_r8_bl5_external_affine_reference_dev.py'):
  shutil.copyfile(REPO/'tests'/name,ROOT/'fixtures'/name)
 m.supervise([sys.executable,'-u',str(ROOT/'check-math.py')],'math-tests',1024**3)
elif mode=='mixed':
 m.supervise([sys.executable,'-u',str(REPO/'scripts/r8_bl5_projected_mixed_system_dev.py'),'--input',str(ROOT.parent/'r8-bl5-affine-flexible-v1'),'--output',str(ROOT/'mixed.json')],'mixed-check',1024**3)
elif mode=='common':
 m.supervise([sys.executable,'-u',str(REPO/'scripts/r8_bl5_projected_reference_action_dev.py'),'--coarse',str(ROOT.parent/'r8-bl5-affine-flexible-v1'),'--fine',str(ROOT.parent/'r8-bl5-growing-affine-fine-v1'),'--output',str(ROOT/'common.json')],'common-check',1024**3)
elif mode=='build':
 m.supervise([sys.executable,'-m','build','--wheel','--no-isolation','--outdir',str(ROOT/'dist'),str(REPO)],'build',1024**3)
elif mode=='install':
 wheel=next((ROOT/'dist').glob('*.whl'))
 m.supervise([sys.executable,'-m','pip','install','--no-deps','--no-index','--target',str(ROOT/'site'),str(wheel)],'install',1024**3)
elif mode=='stage-installed':
 pending=['test_stiffened_shell_bl5_projected_density.py','test_stiffened_shell_bl5_affine_supports.py'];done=set()
 while pending:
  name=pending.pop()
  if name in done:continue
  path=REPO/'tests'/name;tree=ast.parse(path.read_text(encoding='utf-8'))
  shutil.copyfile(path,ROOT/'fixtures'/name);done.add(name)
  for node in ast.walk(tree):
   if isinstance(node,ast.ImportFrom) and node.module and node.module.startswith('test_'):
    assert '.' not in node.module;pending.append(node.module+'.py')
 wheel=next((ROOT/'dist').glob('*.whl'));modules={}
 source={'anysolver/'+p.relative_to(REPO/'src/anysolver').as_posix():p for p in (REPO/'src/anysolver').rglob('*.py')}
 with zipfile.ZipFile(wheel) as z:
  names={n for n in z.namelist() if n.startswith('anysolver/') and n.endswith('.py')}
  assert names==set(source)
  for name in sorted(names):
   data=z.read(name);assert data==(ROOT/'site'/name).read_bytes()==source[name].read_bytes()
   modules[name]=hashlib.sha256(data).hexdigest()
 (ROOT/'binding.json').write_text(json.dumps(dict(source_parent='d5653ec69d62a19ddf2aa1194ae8a1872de2aab5',wheel_sha256=sha(wheel),modules=modules,fixtures={p.name:sha(p) for p in (ROOT/'fixtures').iterdir()},scope='experimental projected-density development only'),indent=2)+'\n')
elif mode=='installed':
 m.ENV['PYTHONPATH']=str(ROOT/'site')
 m.supervise([sys.executable,'-u',str(ROOT/'check-installed.py')],'installed-tests',1024**3)
else:raise ValueError(mode)
