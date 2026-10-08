from pathlib import Path
import ast, hashlib, json

root = Path(__file__).resolve().parent
repo = root.parents[2]
fem = Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
installed = json.loads((root/'installed-runtime-v1.json').read_text())
for path, digest in installed['tests'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
example = fem/'examples/stiffened_shell_ge_distributing_native_material_consumer.py'
assert hashlib.sha256(example.read_bytes()).hexdigest() == installed['example_sha256']
for name, original in installed['sources'].items():
    owner = repo if name.startswith('anysolver/') else fem
    assert hashlib.sha256((owner/'src'/name).read_bytes()).hexdigest() == original, name
products = (
    '.gitattributes', 'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md',
    'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md',
    'docs/stiffened_shell_distributing_material_development.md',
    'src/anysolver/_stiffened_shell_ge_experimental.py',
    'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
    'src/anysolver/_stiffened_shell_ge_checkpoint_binary.py',
    'src/anysolver/_stiffened_shell_ge_distributing_reference.py',
    'src/anysolver/stiffened_shell.py',
    'tests/test_stiffened_shell_distributing_native_material.py')
fem_products = ('.gitattributes',
    'src/anyfem/solve/stiffened_shell_ge_distributing_material.py',
    'tests/test_stiffened_shell_ge_distributing_native_material_consumer.py',
    'examples/stiffened_shell_ge_distributing_native_material_consumer.py')
# Nonprotected live text is stored consistently. Matrix/report historical bytes
# are preserved exactly, using explicit binary Git attributes below.
for owner, names in ((repo, products), (fem, fem_products)):
    for name in names:
        p = owner/name
        if name == '.gitattributes' or (name.startswith('docs/agent_plans/') and
                not name.endswith('results.md') and not name.endswith('ACCEPTANCE_MATRIX.md')):
            p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n'))
        if p.suffix == '.py':
            ast.parse(p.read_text(encoding='utf-8-sig'))
attr = repo/'.gitattributes'
with attr.open('ab') as out:
    out.write(b'\ndocs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md -text\n')
review = root/'final-evidence-review-v1.md'
review.write_text('''Supporting read-only OpenAI review of executed inputs/results found no blocking
evidence mismatch:204PASS464.58s, example9.156s, whole476.189s/sample236797952B.
Initial shellalpha.001657/fibreaccumulated.007 and exact zero restart/continuation
supported. Relevant imported paths all site-v1. No reverse-plastic-flow,
converged connection, aggregate gate or release claim. Different-family
scientific and effective OpenSees thread qualification remain unresolved.
No jobs/imports/edits/Git by reviewer. Root integrated and checked source hashes.
''', encoding='utf-8')
files = list(products)
suffixes = {'.json', '.log', '.py', '.md', '.bin', '.txt', '.anyfem', '.checkpoint'}
for evidence in (root.parent/'r8-distributing-fy80-dev-20261004-v1', root):
    for p in evidence.rglob('*'):
        if not p.is_file() or p.suffix not in suffixes:
            continue
        relative = p.relative_to(evidence)
        if any(part in ('site-v1','solver-dist-v1','fem-dist-v1','pytest-v1','__pycache__')
               for part in relative.parts):
            continue
        assert p.resolve().is_relative_to(repo.resolve())
        files.append(p.relative_to(repo).as_posix())
files = sorted(set(files))
manifest = root/'delivery-inputs-v1.json'
manifest.write_text(json.dumps(dict(
    scope='scoped source/docs/development evidence; no Git history/main/publication',
    files={p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in files},
    fem_files={p:hashlib.sha256((fem/p).read_bytes()).hexdigest() for p in fem_products},
    verified_installed_sources=len(installed['sources']),
    historical_report_prefix=True, historical_matrix_prefix=True), indent=2)+'\n')
files.append(manifest.relative_to(repo).as_posix())
listing = root/'stage-inputs-v1.txt'
files.append(listing.relative_to(repo).as_posix())
listing.write_text('\n'.join(files)+'\n', encoding='utf-8')
print(json.dumps(dict(solver_stage_files=len(files), fem_stage_files=len(fem_products),
                     bytes=sum((repo/p).stat().st_size for p in files))))
