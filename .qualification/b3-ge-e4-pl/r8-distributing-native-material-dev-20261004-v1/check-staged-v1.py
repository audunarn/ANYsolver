from pathlib import Path
import hashlib, json, subprocess

root = Path(__file__).resolve().parent
repo = root.parents[2]
fem = Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
inputs = json.loads((root/'delivery-inputs-v1.json').read_text())
records = {}
for name, owner, expected in (('solver', repo,
        set((root/'stage-inputs-v1.txt').read_text().splitlines())),
        ('fem', fem, set(inputs['fem_files']))):
    command = ['git','-c',f'safe.directory={owner.as_posix()}']
    files = subprocess.check_output(command+['diff','--cached','--name-only','-z'], cwd=owner).decode().split('\0')
    files = [p for p in files if p]
    assert set(files) == expected, (name, set(files)^expected)
    digests = {}
    for p in files:
        blob = subprocess.check_output(command+['show', ':'+p], cwd=owner)
        assert blob == (owner/p).read_bytes(), (name, p)
        digests[p] = hashlib.sha256(blob).hexdigest()
    subprocess.run(command+['-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
        'diff','--cached','--check'], cwd=owner, check=True)
    records[name] = digests
for filename, stem in (
    ('docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md','report'),
    ('docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md','matrix')):
    current = (repo/filename).read_bytes()
    assert current.startswith((root/(stem+'-before-final-v1.bin')).read_bytes())
    earlier = root.parent/'r8-distributing-fy80-dev-20261004-v1'
    initial = 'report-before-v1.bin' if stem == 'report' else 'acceptance_matrix-before-v1.bin'
    assert current.startswith((earlier/initial).read_bytes())
record = dict(scope='exact staged byte/scope proof before local commits',
              files=records, historical_report_and_matrix_prefixes_preserved=True)
(root/'staged-proof-v1.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({name:len(files) for name,files in records.items()}))
