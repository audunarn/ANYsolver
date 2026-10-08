import importlib.util, pathlib, sys
root=pathlib.Path(__file__).resolve().parent
old=root.parent/'r8-bl5-affine-flexible-v1/run.py'
spec=importlib.util.spec_from_file_location('bounded_supervisor',old)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.ROOT=root
repo=pathlib.Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
m.ENV['PYTHONPATH']=str(root.parent/'r8-bl5-projected-integration-v1/site')+';'+str(repo)
m.supervise([sys.executable,'-u',str(root/'scalar.py'),'--output',str(root/'scalar.json')], 'scalar-check',1024**3)
