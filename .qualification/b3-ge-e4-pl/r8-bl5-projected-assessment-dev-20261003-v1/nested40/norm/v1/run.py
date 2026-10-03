import importlib.util,pathlib,sys
root=pathlib.Path(__file__).resolve().parent
repo=pathlib.Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
input_dir=repo/'.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1/auxiliary-norm/v3'
spec=importlib.util.spec_from_file_location('bounded_supervisor',root.parent/'r8-bl5-affine-flexible-v1/run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=root
m.ENV['PYTHONPATH']=str(root.parent/'r8-bl5-projected-integration-v1/site')+';'+str(repo)
stage=sys.argv[1]
cmd=[sys.executable,'-u',str(root/'norm.py'),stage,'--inputs',str(input_dir),'--output',str(root/(stage+'.json'))]
if stage=='assess':cmd+=['--registration',str(root/'register.json')]
m.supervise(cmd,stage+'-check',1024**3)
