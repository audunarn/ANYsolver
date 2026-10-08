from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent
REPO=Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
DEST=REPO/'.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1'
REPORT=REPO/'docs/agent_plans/development/r8-bl5-projected-assessment-20261003'
DEST.mkdir(parents=True,exist_ok=False);REPORT.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
files={}
def add(src,name):
 src=Path(src);assert src.is_file();assert name not in files
 dst=DEST/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
 assert dst.read_bytes()==src.read_bytes();files[name]=dict(bytes=dst.stat().st_size,sha256=sha(dst))
def logs(root,prefix,names):
 for name in names:
  for leaf in ('execution.json','stdout.log','stderr.log','thread-samples.json'):
   path=root/name/leaf
   if path.is_file():add(path,prefix+'/'+name+'/'+leaf)
def top(root,prefix,suffixes=('.py','.json','.ini','.npz')):
 for path in sorted(root.iterdir()):
  if path.is_file() and path.suffix in suffixes:add(path,prefix+'/'+path.name)
worker=ROOT.parent/'r8-bl5-projected-compiler-source-v1'
top(worker,'compiler');logs(worker,'compiler',('focused-run','restart-retry-run'))
mixed=ROOT.parent/'r8-bl5-projected-mixed-v1'
top(mixed,'mixed-initial');logs(mixed,'mixed-initial',('mixed-run','mixed-run-v2','mixed-run-v3'))
common=ROOT.parent/'r8-bl5-projected-common-action-v1'
top(common,'common-initial');logs(common,'common-initial',('focused-run','common-work-run'))
top(ROOT,'integration');logs(ROOT,'integration',('math-tests','mixed-check','common-check','build','install','installed-tests','installed-affected','native-helper-check','native-helper-affected','native-hardening'))
add(ROOT/'stage-v1-failure.txt','integration/stage-v1-failure.txt')
for path in sorted((ROOT/'fixtures').rglob('*.py')):
 if '__pycache__' not in path.parts:add(path,'integration/fixtures/'+path.relative_to(ROOT/'fixtures').as_posix())
wheel=next((ROOT/'dist').glob('*.whl'));add(wheel,'artifact/'+wheel.name)
matched=ROOT.parent/'r8-bl5-projected-matched-v1'
top(matched,'matched');logs(matched,'matched',('external-fy','external-mx','external-mz','native-run','interpretation'))
for branch in ('fixtures','external','native'):
 for path in sorted((matched/branch).rglob('*')):
  if path.is_file() and path.suffix in ('.py','.json','.npz') and '__pycache__' not in path.parts:
   add(path,'matched/'+branch+'/'+path.relative_to(matched/branch).as_posix())
# Explicit old source inputs required to replay the bounded saved checks;
# these directories contain only the already reviewed native development fixture.
for root,prefix in ((ROOT.parent/'r8-bl5-affine-flexible-v1','inputs/coarse'),(ROOT.parent/'r8-bl5-growing-affine-fine-v1','inputs/growing-fine')):
 for name in ('inputs.json','operators.npz'):add(root/'native'/name,prefix+'/'+name)
 if prefix.endswith('coarse'):
  for case in ('fy','mx','mz'):
   for name in ('raw-state.npz','comparison.json'):add(root/'native'/case/name,prefix+'/'+case+'/'+name)
for name in ('r8_bl5_projected_density_patch_dev.py','r8_bl5_projected_mixed_system_dev.py','r8_bl5_projected_reference_action_dev.py',
             'r8_bl5_external_affine_reference_dev.py','r8_bl5_affine_flexible_native_dev.py'):
 add(REPO/'scripts'/name,'final-source/scripts/'+name)
for name in ('test_stiffened_shell_bl5_projected_density.py','test_r8_bl5_projected_reference_action_dev.py','test_r8_bl5_affine_flexible_native_dev.py'):
 add(REPO/'tests'/name,'final-source/tests/'+name)
add(REPO/'src/anysolver/_stiffened_shell_l1_assembly_experimental.py','final-source/compiler.py')
add(REPO/'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md','prior-active-state.md')
add(ROOT.parent/'r8-bl5-affine-flexible-v1/run.py','supervisor.py')
manifest=dict(scope='Explicit safe new projected-assessment inputs/source/artifact/failures/results; no F03/canary/history sweep',
 archive_root=str(DEST),entries=files,total_bytes=sum(v['bytes'] for v in files.values()))
(REPORT/'raw-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(files=len(files),bytes=manifest['total_bytes'],manifest_sha256=sha(REPORT/'raw-manifest.json'))))
