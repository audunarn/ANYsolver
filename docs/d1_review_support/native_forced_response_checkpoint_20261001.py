"""Record exact owned checkpoint paths; no broad staging or solver execution."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess

root=Path('C:/ANYworkspaceWork/ANYsolver-general-contact')
support=root/'docs/d1_review_support'
digest=lambda path:sha256(path.read_bytes()).hexdigest()
review=support/'D6_NATIVE_FREE_TEMPORAL_REVIEW_20260930.md'
note=support/'D6_NATIVE_MIDPOINT_DEVELOPMENT_20260930.md'
assert digest(review)=='e1077dd517d71daabd5b701796d428b7654317e85a1f55c020d104cd6a5d1392'
assert digest(note)=='be4ca7cb85e90e4f8cc39b5777972dd4e22faba2a1dd039f058003715f33f4db'
summary=support/'native_forced_response_v2_20261001.summary.json'
assert digest(summary)=='d2c84c48d2f910c374feefa9e683376526b02f6729893641bdb4d08e297f6d7d'
disposition=support/'native_forced_response_v2_20261001.disposition.json'
assert not disposition.exists()
disposition.write_text(json.dumps(dict(status='INDEPENDENTLY_REVIEWED_DEVELOPMENT_PASS',
    summary_sha256=digest(summary), review_path=str(review), review_sha256=digest(review),
    accepted_steps=20, complete_route_seconds=94.9816845000023,
    scope='Named small-motion driven temporal reference using authenticated shared spatial matrices',
    exclusions=['C7 scientific qualification','continuum reference','finite-angle torque-free trajectory',
        'native impact','installed scientific admission','release'],
    retained=['V1 import startup timeout','bounded cache startup probe NONPASS','earlier native mechanics failures'],
    next_decision='Source-only clamped driven response and support impulses; no rigid-rotor substitution'),indent=2)+'\n',encoding='utf-8')
paths=set(support.glob('native_forced_response*'))
paths.update(root/p for p in ['.gitattributes','GENERAL_CONTACT_PLAN.md','GENERAL_CONTACT_RESTART.md',
    'docs/GENERAL_CONTACT_CAPABILITIES.md','docs/GENERAL_CONTACT_NATIVE_DYNAMIC_DEVELOPMENT.md',
    'docs/d1_review_support/GENERAL_CONTACT_RESTART_HISTORY_20261001_PART29.md',
    'docs/d1_review_support/native_torque_free_design_20261001.md',
    'docs/d1_review_support/native_dynamic_restart_checkpoint_commit_20261001.log'])
paths.update((review,note))
git=['git','-c','safe.directory='+str(root),'-c','core.excludesfile=NUL','-C',str(root)]
assert subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()=='9050dbf3b312980b3b3e0e7caac2539a87b8a0a3'
assert not subprocess.check_output(git+['diff','--cached','--name-only'],text=True).strip()
status=subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all'],text=True)
manifest=support/'native_forced_response_checkpoint_owned_paths_20261001.json'
assert not manifest.exists()
relative=sorted(str(path.relative_to(root)).replace('\\','/') for path in paths)
manifest.write_text(json.dumps(dict(prior_head='9050dbf3b312980b3b3e0e7caac2539a87b8a0a3',
    owned_paths=[dict(path=path,sha256=digest(root/path)) for path in relative],
    include_manifest_itself=True, source_changes='none',
    active_exclusions='NEW native_clamped_response* and native_clamped_response_review* worker ownership',
    preserved_dirty_status=status.splitlines()),indent=2)+'\n',encoding='utf-8')
relative.append(str(manifest.relative_to(root)).replace('\\','/'))
pathspec=support/'native_forced_response_checkpoint_20261001.paths'
assert not pathspec.exists()
pathspec.write_bytes(b'\0'.join(path.encode('utf-8') for path in relative)+b'\0')
print(json.dumps({'owned_path_count':len(relative),'manifest':str(manifest),
    'pathspec':str(pathspec),'unrelated_dirty_entries_preserved':len(status.splitlines())}))
