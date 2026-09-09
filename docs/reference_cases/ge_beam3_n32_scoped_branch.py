"""Original branch targets/lifecycle with explicit local-validation scheduling."""
import argparse
from pathlib import Path
import sys
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_n32_branch_continuation import run as branch,OPS
from docs.reference_cases.ge_beam3_retained_prestress_wave import write

def run(revision,sign,operation,step,output,checkpoint=None,expected_sha256=None):
    guard(revision)
    sys.path.insert(0,str(ROOT/'src'))
    from anysolver._ge_beam3_operator_validation_scope import operator_validation_scope,POLICY
    with operator_validation_scope():
        branch(revision,sign,operation,step,output,checkpoint,expected_sha256)
    write(Path(output)/'policy.json',dict(revision=revision,policy=POLICY,
        default_changed=False,mechanics_changed=False,production_qualified=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--sign',choices=('plus','minus'),required=True)
    p.add_argument('--operation',choices=OPS,required=True);p.add_argument('--step',type=int,required=True);p.add_argument('--output',required=True)
    p.add_argument('--checkpoint');p.add_argument('--expected-sha256');a=p.parse_args()
    run(a.revision,a.sign,a.operation,a.step,a.output,a.checkpoint,a.expected_sha256)
