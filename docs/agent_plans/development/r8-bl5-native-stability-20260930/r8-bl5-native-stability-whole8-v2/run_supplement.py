from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

root = Path.cwd()
original = root/'scalar.json'
table = json.loads(original.read_text())
original_hash = hashlib.sha256(original.read_bytes()).hexdigest()
# Reuse unchanged passed16x4; retry only failed32x8, then unexecuted64x16.
extra = [row for row in table['cases'] if row['nx'] != 16]
assert len(extra)==2
started = time.monotonic()
results = []
for case in extra:
    key = (case['nx'],case['ny'],case['beam_halfcells'])
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
        (root/'supplement-failure.json').write_text(json.dumps(dict(case=key,completed=len(results),
            exit_code=completed.returncode,elapsed_seconds=time.monotonic()-started),indent=2))
        raise SystemExit(completed.returncode)
    row = json.loads((directory/'result.json').read_text())
    assert row['rows']<=100000 and all(row['predicates'].values())
    results.append(row)
(root/'supplement-result.json').write_text(json.dumps(dict(status='COMPLETED_DEVELOPMENT_ONLY',
    cases=results,original_scalar_sha256=original_hash,elapsed_seconds=time.monotonic()-started),indent=2))
print(json.dumps(dict(status='COMPLETED_DEVELOPMENT_ONLY',cases=len(results))),flush=True)
