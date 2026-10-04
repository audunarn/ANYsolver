from pathlib import Path
import hashlib, json, subprocess
ROOT = Path(__file__).resolve().parent; REPO = ROOT.parents[2]
paths = (ROOT/'stage-list-v1.txt').read_text().splitlines()
exact = [p for p in paths if p.startswith(('.qualification/', 'scripts/', 'tests/'))]
proof = {}
for p in exact:
    actual = (REPO/p).read_bytes()
    staged = subprocess.check_output(['git', 'show', ':'+p], cwd=REPO)
    assert actual == staged, p
    proof[p] = hashlib.sha256(actual).hexdigest()
for p in ('docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md',
          'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md'):
    historical = subprocess.check_output(['git', 'show', 'HEAD:'+p], cwd=REPO).replace(b'\r\n', b'\n')
    current = (REPO/p).read_bytes().replace(b'\r\n', b'\n')
    assert current.startswith(historical), p
record = dict(exact_checked_count=len(proof), exact_files_sha256=proof,
    historical_report_matrix_prefix_preserved=True,
    living_document_newlines='intentional Git normalization; science/history preserved')
(ROOT/'staged-byte-proof-v1.json').write_text(json.dumps(record, indent=2)+'\n', encoding='ascii')
print(json.dumps({k:v for k,v in record.items() if k!='exact_files_sha256'}))
