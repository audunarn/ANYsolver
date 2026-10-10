"""Installed-only handoff for the immutable tested paired adaptive candidate."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/agent_plans/development/r8-ge-paired-adaptive-20261010/execution-v4'
ENTRY=ROOT/'scripts/r8_ge_paired_adaptive_dev.py'
sys.path.insert(0,str(ROOT))

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def launch():
    # Only the existing supervisor imports in the parent. Candidate imports,
    # artifact checks, pytest and the physical workflow stay in its timed child.
    from scripts.r8_f06_fibre_log_domain_dev import run,write
    authority_name='ADAPTIVE_INSTALLED_AUTHORITY.json'
    authority_path=DOC/authority_name
    captured=authority_path.read_bytes();authority=json.loads(captured)
    slot_path=DOC/'ADAPTIVE_INSTALLED_SLOT_TRANSFER.json'
    slot=json.loads(slot_path.read_text())
    if authority.get('status')!='AUTHORIZED' or slot.get('status')!='TRANSFERRED' or slot.get('one_numerical_job') is not True:
        raise ValueError('fresh installed authority and exclusive slot required')
    if sha(slot_path)!=authority.get('installed_slot_sha256') or sha(__file__)!=authority.get('installed_bootstrap_sha256'):
        raise ValueError('exact installed launcher and slot adoption required')
    if list(DOC.glob('attempt-installed-cycle*')):raise ValueError('sole installed attempt already consumed')
    manifest=DOC/'ADAPTIVE_INSTALLED_BINDINGS.json'
    if sha(manifest)!=authority.get('installed_bindings_sha256'):
        raise ValueError('exact installed artifact binding adoption required')
    expected=json.loads(manifest.read_text())
    def bind():
        if len(expected)!=34 or len({Path(p).name for p in expected})!=34:
            raise ValueError('exact34 unique child bindings required')
        for rel,digest in expected.items():
            path=ROOT/rel
            if not path.resolve().is_relative_to(ROOT) or sha(path)!=digest:
                raise ValueError('changed or out-of-workspace installed binding: '+rel)
        return expected
    bind()
    if (authority.get('budget_s'),authority.get('reserve_s'),authority.get('process_cap_s'))!=(900,120,600):
        raise ValueError('adopted installed resource envelope required')
    source=DOC/'attempt-source-controls1/receipt.json';wheel=DOC/'attempt-wheel1/receipt.json'
    count=json.loads((source.parent/'counts.json').read_text())
    if (json.loads(source.read_text()).get('status')!='PASS' or count!=dict(tests=12,errors=0,failures=0,skipped=0)
            or json.loads(wheel.read_text()).get('status')!='PASS'):
        raise ValueError('exact12 source PASS and fresh wheel PASS required')
    if sha(source)!=authority.get('source_receipt_sha256') or sha(wheel)!=authority.get('wheel_receipt_sha256'):
        raise ValueError('exact consumed source/build receipt adoption required')
    out=DOC/'attempt-installed-cycle1'
    try:
        code=run('installed-cycle',doc=DOC,entry=str(ENTRY),bind=bind,authority_file=authority_name)
        (out/'used-authority.json').write_bytes(captured)
        if hashlib.sha256(captured).hexdigest()!=json.loads((out/'receipt.json').read_text())['authority_sha256']:
            raise ValueError('installed authority changed during launch')
        return code
    finally:
        # Every consumed installed attempt is terminal, including supervisor
        # refusal or accounting failure. There is no retry or new direction.
        if out.exists():
            path=DOC/'ledger.json';value=json.loads(path.read_text())
            value.update(status='CLOSED',unused_discarded_s=value['budget_s']-value['used_s'])
            write(path,value)

if __name__=='__main__':raise SystemExit(launch())
