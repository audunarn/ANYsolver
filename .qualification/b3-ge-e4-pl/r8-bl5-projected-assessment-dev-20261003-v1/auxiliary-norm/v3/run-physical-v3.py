import importlib.util,pathlib,sys
root=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('bounded_supervisor',root.parent/'r8-bl5-affine-flexible-v1/run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=root
repo=pathlib.Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
m.ENV['PYTHONPATH']=str(root.parent/'r8-bl5-projected-integration-v1/site')+';'+str(repo)
m.supervise([sys.executable,'-u',str(root/'physical-v3.py'),'--root',str(root.parent/'r8-bl5-affine-flexible-v1'),
'--registration',str(root/'physical-registration.json'),'--output',str(root/'physical-v3.json'),'--wheel',str(root.parent/'r8-bl5-projected-integration-v1/dist/anysolver-0.4.7-py3-none-any.whl')], 'physical-v3-check',1024**3)


