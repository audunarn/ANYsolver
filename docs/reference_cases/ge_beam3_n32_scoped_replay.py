"""Same frozen replay diagnostic under the explicit local-validation policy."""
import argparse
from pathlib import Path
import sys
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard, ROOT
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.ge_beam3_n32_replay_profile import run as profile

def run(revision,output):
    guard(revision)
    sys.path.insert(0,str(ROOT/'src'))
    from anysolver._ge_beam3_operator_validation_scope import operator_validation_scope,POLICY
    with operator_validation_scope():
        profile(revision,'observed',output)
    write(Path(output)/'policy.json',dict(revision=revision,policy=POLICY,
        default_changed=False,mechanics_changed=False,qualification_evidence=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.revision,a.output)
