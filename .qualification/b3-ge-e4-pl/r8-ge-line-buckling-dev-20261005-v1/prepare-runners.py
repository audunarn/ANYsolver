"""Reuse the previous bounded source/build/install harness, without running it."""
from pathlib import Path
import hashlib, json

root = Path(__file__).resolve().parent
previous = root.parent/'r8-ge-point-buckling-dev-20261005-v1'
run = (previous/'run-v1.py').read_text()
start = run.index('    files = [')
end = run.index("    folder = ROOT/'executed-source-v1'", start)
files = ['src/anysolver/_stiffened_shell_ge_point_buckling.py',
    'src/anysolver/_stiffened_shell_ge_experimental.py', 'src/anysolver/stiffened_shell.py',
    'src/anysolver/_stiffened_shell_q4_algorithmic_pullback.py',
    'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
    'src/anysolver/_stiffened_shell_bl5_local_experimental.py',
    'src/anysolver/_stiffened_shell_l1_local_experimental.py',
    'tests/test_stiffened_shell_ge_point_buckling.py',
    'tests/test_stiffened_shell_ge_line_buckling.py',
    'tests/test_stiffened_shell_l1_assembly_experimental.py',
    'tests/test_stiffened_shell_bl5_finite.py',
    'tests/test_stiffened_shell_ge_experimental.py',
    'scripts/r8_ge_line_buckling_dev.py']
run = run[:start]+'    files = '+repr(files)+'\n'+run[end:]
run = run.replace("source_parent='20a09c21'", "source_parent='a4ee8a66'")
run = run.replace("tests = [name for name in files if name.startswith('tests/')]",
    "tests = ['tests/test_stiffened_shell_ge_point_buckling.py', 'tests/test_stiffened_shell_ge_line_buckling.py']")
build = (previous/'build-v1.py').read_text().replace("source_parent='20a09c21'", "source_parent='a4ee8a66'")
installed = (previous/'installed-v1.py').read_text().replace(
    'tests/test_stiffened_shell_q4_algorithmic_pullback.py', 'tests/test_stiffened_shell_ge_line_buckling.py')
for name, code in (('run-v1.py', run), ('build-v1.py', build), ('installed-v1.py', installed)):
    compile(code, name, 'exec')
    with (root/name).open('x', encoding='utf-8') as handle:
        handle.write(code)
(root/'harness-origin-v1.json').write_text(json.dumps(dict(previous=str(previous),
    source_harness_hashes={name: hashlib.sha256((previous/name).read_bytes()).hexdigest()
        for name in ('run-v1.py', 'build-v1.py', 'installed-v1.py')},
    scope='Reused supervision, new line and regression point tests; no execution during preparation'), indent=2)+'\n')
print('Prepared three source-bound serial runners; no numerical work launched.')
