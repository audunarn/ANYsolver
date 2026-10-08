import importlib.util,pathlib,sys
root=pathlib.Path(__file__).resolve().parent
repo=pathlib.Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
spec=importlib.util.spec_from_file_location('bounded_supervisor',root.parent/'r8-bl5-affine-flexible-v1/run.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=root
m.ENV['PYTHONPATH']=str(root.parent/'r8-bl5-projected-integration-v1/site')+';'+str(repo)
m.supervise([sys.executable,'-u',str(root/'r8_bl5_nested_projected_kernel_dev.py'),'--prior',
str(root.parent/'r8-bl5-projected-integration-v1/mixed.json'),'--input',str(root.parent/'r8-bl5-affine-flexible-v1'),
'--output',str(root/'kernel.json')], 'kernel-check',1024**3)
