import importlib.util,pathlib,sys
root=pathlib.Path(__file__).resolve().parent
repo=pathlib.Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
spec=importlib.util.spec_from_file_location('bounded_supervisor',root.parent/'r8-bl5-affine-flexible-v1/run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=root
site=root.parent/'r8-bl5-projected-integration-v1/site'
m.ENV['PYTHONPATH']=str(site)+';'+str(repo)+';'+str(repo/'tests')
m.supervise([sys.executable,'-u',str(root/'owner.py'),'--site',str(site),
'--wheel',str(root.parent/'r8-bl5-projected-integration-v1/dist/anysolver-0.4.7-py3-none-any.whl'),
'--wheel-sha','a47e518fe36050e1a2d5a93d9d8c9802138e46c0cc9d8c1c840cc5efdd8650d3',
'--source',str(repo),'--old-root',str(root.parent/'r8-bl5-affine-flexible-v1'),
'--kernel',str(root/'kernel.json'),'--output',str(root/'owner.json')], 'owner-check',1024**3)
