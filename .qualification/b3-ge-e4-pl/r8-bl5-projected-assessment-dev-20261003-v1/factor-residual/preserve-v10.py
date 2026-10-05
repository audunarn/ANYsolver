"""Exact newly-owned whitelist; no other historical TEMP/raw tree inspected."""
from pathlib import Path
import json,hashlib,subprocess,shutil

ROOT=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
TEMP=Path(__file__).resolve().parent
RAW=ROOT/'.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1/factor-residual'
GROUP=ROOT/'docs/agent_plans/development/r8-bl5-projected-assessment-20261003'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(value,message):
 if not value:raise ValueError(message)
previous=GROUP/'raw-manifest-v9.json'
require(digest(previous)=='5af39a3e686138941bfc7ccd02cbba65f74a22c5b99de363a77f04c408ec96f8','frozen prior manifest differs')
require(not RAW.exists() and not (GROUP/'raw-manifest-v10.json').exists(),'fresh immutable extension required')
files={}
for name in ('factor-v1.json','factor-v1.npz','factor-v2.json','factor-v2.npz','factor-v3.json','factor-v3.npz',
 'probe-v1.py','probe-v2.py','probe-v3.py','run-v1.py','run-v2.py','run-v3.py','preserve-v10.py',
 'design-review-v1.md','driver-review-v1.md','integration-review-v1.md','integration-review-v2.md',
 'block-design-review-v1.md','block-integration-review-v1.md','block-integration-review-v2.md'):
 files[name]=TEMP/name
for directory in ('test-v1','test-block-v1','test-block-v2','ns16_b8-v1','ns16_b8-v2','ns16_b8-v3'):
 for name in ('execution.json','stdout.log','stderr.log','thread-samples.json'):
  files[directory+'/'+name]=TEMP/directory/name
for directory in ('sources-v1','sources-block-v1','sources-block-v2'):
 for name in ('helper.py','tests.py','probe.py','run.py'):
  files[directory+'/'+name]=TEMP/directory/name
for name in ('probe-v2.py','run-v2.py'):
 files['sources-v2/'+name]=TEMP/'sources-v2'/name
for name in ('r8_bl5_sparse_factor_residual_dev.py','r8_bl5_sparse_factor_block_dev.py',
 'r8_bl5_sparse_envelope_kernel_dev.py','r8_bl5_sparse_kernel_saved_dev.py','r8_bl5_sparse_kernel_interval_dev.py',
 '_b3_e4_f03_sparse_certificate.py'):
 files['sources-final/'+name]=ROOT/'scripts'/name
for name in ('test_r8_bl5_sparse_factor_residual_dev.py','test_r8_bl5_sparse_factor_block_dev.py'):
 files['sources-final/'+name]=ROOT/'tests'/name
supervisor=TEMP.parent/'r8-bl5-affine-flexible-v1/run.py'
require(digest(supervisor)=='ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec','supervisor differs')
files['supervisor.py']=supervisor
for target,source in files.items():require(source.is_file(),'missing exact owned evidence: '+str(source))
RAW.mkdir(parents=True)
for target,source in files.items():
 dest=RAW/target;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 require(digest(dest)==digest(source),'copy changed exact bytes')
note='docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md'
parent=subprocess.check_output(['git','-c','safe.directory='+str(ROOT),'show','HEAD:'+note],cwd=ROOT)
(RAW/'active-state-parent.md').write_bytes(parent)
(RAW/'active-state-prospective.md').write_bytes((ROOT/note).read_bytes())
entries=[dict(path=p.relative_to(ROOT).as_posix(),sha256=digest(p),bytes=p.stat().st_size)
 for p in sorted(RAW.rglob('*')) if p.is_file()]
manifest=dict(identity='BL5_SAVED_FACTOR_RESIDUAL_DEVELOPMENT_RAW_V10',source_parent='3f43e9ebd6fb25bb6a2cc9b43de892208fd27d9f',
 previous_manifest='raw-manifest-v9.json',previous_manifest_sha256=digest(previous),formal_f03_authority_consumed=False,
 qualification_claim=False,files=entries)
out=GROUP/'raw-manifest-v10.json';out.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(files=len(entries),bytes=sum(x['bytes'] for x in entries),manifest_sha256=digest(out))))
