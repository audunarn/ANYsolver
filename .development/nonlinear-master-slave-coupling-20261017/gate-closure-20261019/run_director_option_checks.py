"""Bounded disjoint candidate partitions with explicit34-module selection."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

PHASE=Path(__file__).resolve().parent
TASK=PHASE.parent
REPO=TASK.parents[1]
PYTHON=REPO/'.venv/Scripts/python.exe'
NEW='tests/test_nonlinear_beam_shell_slice3_director_continuation.py'
COMMON='tests/test_nonlinear_beam_shell_slice3_continuation.py'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name',required=True)
    parser.add_argument('--selection',choices=('source-focus','full-pilot','state-rest'),required=True)
    args=parser.parse_args()
    inherited=PHASE/'revised-endpoint-final-continuation-selection.json'
    old=json.loads(inherited.read_text(encoding='utf-8-sig'))
    all_targets=list(old['all_required_targets'])
    assert len(all_targets)==33 and NEW not in all_targets
    all_targets.append(NEW)
    if args.selection=='source-focus':
        targets=['tests/test_nonlinear_beam_shell_slice3.py']; outer=120
    elif args.selection=='full-pilot':
        targets=[NEW+'::test_director_full_target_plasticity_equilibrium_and_rhs_budget'];outer=300
    else:
        names=['test_director_preyield_matches_high_yield_control',
               'test_director_preyield_matches_distinct_linear_elastic_stored_stress',
               'test_director_restart_reproduces_full_physical_history',
               'test_director_cancelled_same_model_and_inputs_still_deliver',
               'test_director_incompatible_restart_refused_without_input_mutation',
               'test_director_stopped_negative_run_excludes_rejected_history']
        targets=[NEW+'::'+n for n in names];outer=600
    selection=PHASE/(args.name+'-selection.json')
    if selection.exists(): raise FileExistsError(selection)
    data=dict(historical_selection=old['historical_selection'],selection=args.selection,
        all_required_targets=all_targets,targets=targets,
        selected_file_sha256={t.partition('::')[0]:sha(REPO/t.partition('::')[0]) for t in targets},
        dependency_file_sha256={COMMON:sha(REPO/COMMON)},development_only=True,
        note='Historical559 results remain historical after source change; common helper dependency explicitly bound.')
    selection.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    files=[Path(__file__),selection,inherited,REPO/NEW,REPO/COMMON,
           PHASE/'director-option-scientific-candidate-authority.json',
           PHASE/'rejected-increment-seed-authority.json',
           REPO/'scripts/run_portable_ci.py',REPO/'scripts/development_test_runtime.py']
    command=[str(PYTHON),str(PHASE/'harness.py'),'--name',args.name,'--timeout',str(outer)]
    for file in files: command+=['--hash-input',str(file)]
    command+=['--',str(PYTHON),'scripts/run_portable_ci.py','--development',*targets,
              '--workers','1','--jit','off','--timeout-seconds',str(outer-10),'--memory-limit-mib','2048']
    env=dict(os.environ);env['RUNNER_TEMP']=str(PHASE/'portable-runs')
    raise SystemExit(subprocess.run(command,cwd=REPO,env=env,check=False).returncode)


if __name__=='__main__':main()
