"""Archive only this explicitly owned campaign; no historical secret sources."""
from pathlib import Path
import hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parent
REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
DEST=REPO/'.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1/envelope'
DOC=REPO/'docs/agent_plans/development/r8-bl5-projected-assessment-20261003'
FILES=('aggregate-v1.json','campaign-v1.json','consolidate-v1.py','consolidate-v2.py',
 'native-campaign-v1.json','reference-tail-design-review-v1.md','run-fine-v1.py','run-matched-v1.py',
 'run-next-v1.py','run-register-v1.py','run-test-v3.py','run-v1.py','run-v2.py','run-v3.py',
 'slice-runtime-review-v1.md','slice-source-review-v1.md','slice-source-review-v2.md',
 'slice-source-review-v3.md','sparse-envelope-next-seam-v1.md','archive-v1.py')
ids=[f'ns{nx}_b{ratio}' for nx in (16,32,64) for ratio in ('1_8','1_4','1_2','1','2','4','8')]
newowners=[name for name in ids if name not in ('ns16_b1_2','ns16_b2','ns32_b1')]
DIRS=('owners','registrations','sources-v1','sources-v2','sources-v3','sources-v4','test-v1','test-v2','test-v3',
 *(f'register-{name}-v1' for name in ids), 'register-ns64_b4-v2','register-ns64_b8-v2',
 *(f'owner-{name}-v1' for name in newowners))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not DEST.exists() and not (DOC/'raw-manifest-v8.json').exists()
owned=[]
for filename in FILES:
 p=ROOT/filename;assert p.is_file();owned.append(p)
for dirname in DIRS:
 p=ROOT/dirname;assert p.is_dir()
 for f in p.rglob('*'):
  if f.is_file():
   assert not f.is_symlink() and '__pycache__' not in f.parts
   owned.append(f)
DEST.mkdir()
for p in owned:
 target=DEST/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
 assert not target.exists();shutil.copyfile(p,target);assert sha(target)==sha(p)
# Preserve previous live note byte-for-byte before reducing the working record.
parent=subprocess.check_output(['git','-c','safe.directory='+str(REPO),'show','HEAD:docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md'],cwd=REPO)
(DEST/'active-state-parent.md').write_bytes(parent)
(DEST/'active-state-prospective.md').write_bytes((REPO/'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md').read_bytes())
(DEST/'consolidate-v1-failure.txt').write_text('Read-only aggregate v1 raised KeyError json_path for the first historical reused owner. Original v1 source retained; v2 restricts modern JSON path lookup to new owners. No numerical failure or native rerun.\n')
manifest=dict(identity='BL5_PROJECTED_ENVELOPE_DEVELOPMENT_RAW_V8',source_parent='a7327da2',
 previous_manifest_sha256=sha(DOC/'raw-manifest-v7.json'),
 supervisor_source=dict(path=str(ROOT.parent/'r8-bl5-affine-flexible-v1/run.py'),sha256=sha(ROOT.parent/'r8-bl5-affine-flexible-v1/run.py')),
 files=[dict(path=p.relative_to(REPO).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
        for p in sorted(DEST.rglob('*')) if p.is_file()],
 limitation='Owned immutable development evidence; original failed bounds retained, no F03/qualification/release.')
manifest['count']=len(manifest['files']);manifest['bytes']=sum(f['bytes'] for f in manifest['files'])
with (DOC/'raw-manifest-v8.json').open('x') as handle:json.dump(manifest,handle,indent=2)
print(json.dumps(dict(count=manifest['count'],bytes=manifest['bytes'],manifest_sha256=sha(DOC/'raw-manifest-v8.json'))))
