from pathlib import Path
import hashlib, json, subprocess

root = Path(__file__).resolve().parent
repo = root.parents[2]
expected = set((root/'stage-inputs-v1.txt').read_text().splitlines())
actual = set(filter(None,subprocess.check_output(
    ['git','diff','--cached','--name-only','-z'],cwd=repo).decode().split('\0')))
assert actual == expected, actual ^ expected
digests = {}
for name in sorted(actual):
    blob = subprocess.check_output(['git','show',':'+name],cwd=repo)
    assert blob == (repo/name).read_bytes(), name
    if name != (root/'staged-proof-v1.json').relative_to(repo).as_posix():
        digests[name] = hashlib.sha256(blob).hexdigest()
for stem,target in (
    ('report','docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md'),
    ('matrix','docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md')):
    assert (repo/target).read_bytes().startswith((root/(stem+'-before-final-v1.bin')).read_bytes())
subprocess.run(['git','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
    'diff','--cached','--check'],cwd=repo,check=True)
(root/'staged-proof-v1.json').write_text(json.dumps(dict(
    exact_scope_and_bytes=True, historical_report_matrix_prefixes_preserved=True,
    files=digests),indent=2)+'\n')
print(json.dumps(dict(staged_files=len(actual), bytes=sum((repo/p).stat().st_size for p in actual))))
