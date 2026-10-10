"""Supervise candidate imports using the existing accounted process harness."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/agent_plans/development/r8-ge-paired-adaptive-20261010/execution-v4'
ENTRY=ROOT/'scripts/r8_ge_paired_adaptive_dev.py'
sys.path.insert(0,str(ROOT))

def launch(stage):
    # Import only the established supervisor, never the candidate in this parent.
    # Candidate/module import failures therefore occur inside its timed child.
    from scripts.r8_f06_fibre_log_domain_dev import run,write
    authority_name='ADAPTIVE_'+{'source-controls':'SOURCE','wheel':'WHEEL','installed-cycle':'INSTALLED'}[stage]+'_AUTHORITY.json'
    authority=json.loads((DOC/authority_name).read_text())
    slot=json.loads((DOC/'ADAPTIVE_SLOT_TRANSFER.json').read_text())
    if authority.get('status')!='AUTHORIZED' or slot.get('status')!='TRANSFERRED' or slot.get('one_numerical_job') is not True:
        raise ValueError('fresh root authority and exclusive slot required')
    if list(DOC.glob('attempt-'+stage+'*')):raise ValueError('sole attempt already consumed')
    manifest=DOC/'ADAPTIVE_BOOTSTRAP_BINDINGS.json'
    if hashlib.sha256(manifest.read_bytes()).hexdigest()!=authority.get('bootstrap_bindings_sha256'):
        raise ValueError('exact root bootstrap binding adoption required')
    expected=json.loads(manifest.read_text())
    def bind():
        if len(set(Path(p).name for p in expected))!=len(expected):raise ValueError('snapshot basename collision')
        for rel,digest in expected.items():
            path=ROOT/rel
            if not path.resolve().is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
                raise ValueError('changed or out-of-workspace binding: '+rel)
        return expected
    bind()
    if (authority.get('budget_s'),authority.get('reserve_s'),authority.get('process_cap_s'))!=(900,120,{'source-controls':30,'wheel':60,'installed-cycle':600}[stage]):
        raise ValueError('fresh adopted resource envelope required')
    if stage!='source-controls':
        receipt=json.loads((DOC/'attempt-source-controls1/receipt.json').read_text())
        count=json.loads((DOC/'attempt-source-controls1/counts.json').read_text())
        if receipt.get('status')!='PASS' or count!=dict(tests=12,errors=0,failures=0,skipped=0):raise ValueError('exact12source PASS required')
    if stage=='installed-cycle' and json.loads((DOC/'attempt-wheel1/receipt.json').read_text()).get('status')!='PASS':
        raise ValueError('new installed artifact PASS required')
    captured_authority=(DOC/authority_name).read_bytes()
    code=run(stage,doc=DOC,entry=str(ENTRY),bind=bind,authority_file=authority_name)
    out=DOC/('attempt-'+stage+'1')
    (out/'used-authority.json').write_bytes(captured_authority)
    if hashlib.sha256(captured_authority).hexdigest()!=json.loads((out/'receipt.json').read_text())['authority_sha256']:
        raise ValueError('authority changed during supervised launch')
    if code or stage=='installed-cycle':
        path=DOC/'ledger.json';value=json.loads(path.read_text());value.update(status='CLOSED',unused_discarded_s=value['budget_s']-value['used_s']);write(path,value)
    return code

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=('source-controls','wheel','installed-cycle'),required=True)
    raise SystemExit(launch(parser.parse_args().stage))
