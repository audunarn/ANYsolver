"""Prepare one owned saved-data driver; never runs a numerical experiment."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
PREVIOUS = ROOT.parent/'factor-residual'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
bindings = {str(p.relative_to(REPO)).replace('\\', '/'): sha(p) for p in (
    PREVIOUS/'factor-v2.json', PREVIOUS/'factor-v2.npz',
    REPO/'scripts/r8_bl5_sparse_gram_margin_dev.py',
    REPO/'scripts/r8_bl5_sparse_factor_residual_dev.py',
    REPO/'docs/agent_plans/development/r8-bl5-projected-assessment-20261003/raw-manifest-v10.json',
)}
source = (PREVIOUS/'probe-v2.py').read_text()
source = source.replace('from scripts.r8_bl5_sparse_factor_residual_dev import certify_factor_residual',
    'from scripts.r8_bl5_sparse_gram_margin_dev import certify_gram_margin')
source = source.replace("require(family.sha(family.ROOT/'scripts/r8_bl5_sparse_factor_residual_dev.py')=='cd56272435d4df22de7a08ff27362faf453c35ac1f97f138976d1f3aa70359f1','reviewed candidate helper source required')",
    "BINDINGS="+repr(bindings)+"\nfor name,expected in BINDINGS.items():require(family.sha(family.ROOT/name)==expected,'pinned extra-shift dependency differs')\n"+
    "old=family.RAW/'factor-residual/factor-v2.json'\noldproof=json.loads(old.read_text())\nrequire(family.sha(old.with_suffix('.npz'))==oldproof['arrays_sha256'],'saved rho arrays differ')\n"+
    "oldmanifest=json.loads((GROUP/'raw-manifest-v10.json').read_text())\noldrecords={r['path']:r['sha256'] for r in oldmanifest['files']}\n"+
    "for p in (old,old.with_suffix('.npz')):require(family.sha(p)==oldrecords[p.relative_to(family.ROOT).as_posix()],'saved rho manifest differs')\n"+
    "rho_saved=oldproof['factor_residual_proof']['rho_upper']\nrequire(oldproof['predecessor_arrays_sha256']==family.sha(archive) and oldproof['fixed_shift']==pre['fixed_shift'] and rho_saved==3.799961133131045e-11,'same frozen target and rho required')\n"+
    "tau=float(up(pre['fixed_shift']+float(up(2*rho_saved))))")
source = source.replace("out=ROOT/'factor-v2.json'", "out=ROOT/'gram-v1.json'")
source = source.replace('BL5_SAVED_SHIFTED_FACTOR_RESIDUAL_DISCRIMINATOR_DEV_V1', 'BL5_SAVED_FIXED_SHIFT_GRAM_MARGIN_DEV_V1')
source = source.replace("'r8_bl5_sparse_factor_residual_dev.py','r8_bl5_sparse_kernel_saved_dev.py'",
    "'r8_bl5_sparse_gram_margin_dev.py','r8_bl5_sparse_factor_residual_dev.py','r8_bl5_sparse_kernel_saved_dev.py'")
source = source.replace("len(order)==2745", "len(order)==2745 and set(order)==set(range(2745))")
source = source.replace("bhat=a[order][:,order].tocsr();bhat.setdiag(bhat.diagonal()-pre['fixed_shift'])",
    "report.update(saved_rho_upper=rho_saved,producer_shift=tau,saved_rho_json_sha256=family.sha(old),design_sha256=family.sha(ROOT/'design.md'))\n bhat=a[order][:,order].tocsr();bhat.setdiag(bhat.diagonal()-tau)")
source = source.replace("proof=certify_factor_residual(a,f,order,shift=pre['fixed_shift'],",
    "proof=certify_gram_margin(a,f,order,target_shift=pre['fixed_shift'],producer_shift=tau,")
source = source.replace("report['factor_residual_proof']", "report['gram_margin_proof']")
source = source.replace("proof['status']=='POSITIVE_SHIFTED_FACTOR_RESIDUAL'",
    "proof['status']=='POSITIVE_FIXED_SHIFT_GRAM_MARGIN' and proof['positive'] and proof['margin_lower']>0")
if 'certify_factor_residual' in source or "diagonal()-pre['fixed_shift']" in source:
    raise ValueError('old producer/proof not completely replaced')
(ROOT/'probe-v1.py').write_text(source, newline='\n')
wrapper = (PREVIOUS/'run-v2.py').read_text().replace("ROOT=Path(__file__).resolve().parent", "ROOT=Path(__file__).resolve().parent")
wrapper = wrapper.replace('test_r8_bl5_sparse_factor_residual_dev.py', 'test_r8_bl5_sparse_gram_margin_dev.py')
wrapper = wrapper.replace("ROOT/'probe-v2.py'", "ROOT/'probe-v1.py'").replace("'ns16_b8-v2'", "'ns16_b8-v1'")
wrapper = wrapper.replace("elif sys.argv[1]=='case':", "elif sys.argv[1]=='case':\n if hashlib.sha256((ROOT/'probe-v1.py').read_bytes()).hexdigest()!="+repr(sha(ROOT/'probe-v1.py'))+":raise ValueError('reviewed driver source differs')")
(ROOT/'run-v1.py').write_text(wrapper, newline='\n')
print(json.dumps({'driver_sha256':sha(ROOT/'probe-v1.py'),'wrapper_sha256':sha(ROOT/'run-v1.py'), 'bindings':bindings}, indent=2))
