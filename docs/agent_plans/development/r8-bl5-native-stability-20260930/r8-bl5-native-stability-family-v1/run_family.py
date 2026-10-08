from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time
import math

root = Path.cwd()
table = json.loads((root/'scalar.json').read_text())
pilot_path = root/'pilot_result.json'
pilot = json.loads(pilot_path.read_text())
assert all(pilot['predicates'].values())
results = [pilot]
started = time.monotonic()
for case in table['cases']:
    key = (case['nx'], case['ny'], case['beam_halfcells'])
    if key == (pilot['nx'], pilot['ny'], pilot['beam_halfcells']):
        continue
    directory = root/f'nx{key[0]}-ny{key[1]}-half{key[2]}'
    directory.mkdir()
    for name in ('scripts','fixtures'):
        shutil.copytree(root/name,directory/name,ignore=shutil.ignore_patterns('__pycache__'))
    for name in ('run_case.py','run_bounded.py','run_installed.py','scalar.json'):
        shutil.copyfile(root/name,directory/name)
    (directory/'case.json').write_text(json.dumps(case,indent=2))
    completed = subprocess.run([sys.executable,'run_bounded.py'],cwd=directory,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (directory/'coordinator-output.txt').write_text(completed.stdout)
    print(json.dumps(dict(case=key,exit_code=completed.returncode)),flush=True)
    if completed.returncode:
        (root/'family-failure.json').write_text(json.dumps(dict(case=key,completed=len(results),
            exit_code=completed.returncode,elapsed_seconds=time.monotonic()-started),indent=2))
        raise SystemExit(completed.returncode)
    row = json.loads((directory/'result.json').read_text())
    assert row['rows'] <= 100000 and all(row['predicates'].values())
    results.append(row)
ordered = sorted(results,key=lambda r:(r['beam_halfcells']/r['nx'],r['nx']))
deterioration = []
for coarse,fine in zip(ordered[:-1],ordered[1:]):
    if coarse['beam_halfcells']/coarse['nx'] != fine['beam_halfcells']/fine['nx']:
        continue
    p = math.log(coarse['beta']/fine['beta'])/math.log(2)
    ceiling = math.log((1+1e-6)/fine['safe_case_floor'])/math.log(2)
    deterioration.append(dict(ratio=coarse['beam_halfcells']/coarse['nx'],
        coarse_nx=coarse['nx'],fine_nx=fine['nx'],raw_p=p,noncollapse_ceiling=ceiling,
        passed=p <= ceiling+1e-6))
assert len(results)==21 and len(deterioration)==14
assert all(r['passed'] for r in deterioration)
summary=dict(status='COMPLETED_DEVELOPMENT_ONLY',cases=ordered,
    deterioration=deterioration,elapsed_seconds=time.monotonic()-started,
    reused_pilot_sha256=hashlib.sha256(pilot_path.read_bytes()).hexdigest(),
    scope='frozen c2 finite reference inf-sup; no KKT/locking/accuracy/F03 acceptance')
(root/'family-result.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(dict(status=summary['status'],cases=21,
    beta_min=min(r['beta'] for r in ordered),beta_max=max(r['beta'] for r in ordered))),flush=True)
