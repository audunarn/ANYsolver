"""Inspect staged chart scope and bytes without changing Git state."""
from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[3];RAW=Path(__file__).resolve().parent
expected=set((RAW/'stage-inputs-v1.txt').read_text().splitlines())
actual=set(subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT).decode().splitlines())
assert actual==expected,(actual-expected,expected-actual)
for name in expected:
    staged=subprocess.check_output(['git','show',':'+name],cwd=ROOT)
    assert staged==(ROOT/name).read_bytes(),name
for name,record in json.loads((RAW/'historical-prefixes-v1.json').read_bytes()).items():
    prefix=(ROOT/name).read_bytes()[:record['prefix_bytes']]
    assert hashlib.sha256(prefix).hexdigest()==record['prefix_sha256'],name
assert (RAW/'active-state-before-v1.md').read_bytes()==subprocess.check_output(
    ['git','show','HEAD:docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md'],cwd=ROOT)
subprocess.check_call(['git','-c','core.whitespace=cr-at-eol','diff','--cached','--check'],cwd=ROOT)
print(f'Verified {len(actual)} staged paths, exact working bytes, historical prefixes and prior-note archive.')
