from pathlib import Path
import ast, shutil

root = Path(__file__).resolve().parent
repo = root.parents[2]
old = root.parent / 'r8-distributing-cyclic-dev-20261004-v1'
for name in ('build-installed-v1.py', 'run-installed-v1.py'):
    shutil.copyfile(old / name, root / name)
text = (old / 'probe-installed-v1.py').read_text()
start = text.index('solver_names = (')
end = text.index('\ntests = ', start)
text = text[:start] + '''solver_names = (
    'test_stiffened_shell_distributing_native_material.py',
    'test_stiffened_shell_distributing_cyclic.py',
    'test_stiffened_shell_ge_distributing_material.py',
    'test_stiffened_shell_ge_distributing_finite_public.py',
    'test_stiffened_shell_ge_distributing_reference.py',
    'test_stiffened_shell_ge_physical_fibre_finite.py',
    'test_stiffened_shell_native_coupled_material.py',
    'test_stiffened_shell_native_fibre_energy.py',
    'test_stiffened_shell_physical_fibre_j2_history.py')
fem_names = (
    'test_stiffened_shell_ge_distributing_native_material_consumer.py',
    'test_stiffened_shell_ge_distributing_cyclic_consumer.py',
    'test_stiffened_shell_ge_distributing_material_consumer.py',
    'test_stiffened_shell_ge_finite_distributing_consumer.py',
    'test_stiffened_shell_ge_distributing_consumer.py')
''' + text[end:]
text = text.replace('installed cyclic development slice', 'installed native fibre development slice')
text = text.replace('stiffened_shell_ge_distributing_cyclic_consumer.py',
                    'stiffened_shell_ge_distributing_native_material_consumer.py')
text = text.replace('Installed cyclic consumer', 'Installed native fibre consumer')
ast.parse(text)
(root / 'probe-installed-v1.py').write_text(text, encoding='utf-8')
snapshot = root / 'source-v4'
snapshot.mkdir()
names = (
    'src/anysolver/_stiffened_shell_ge_experimental.py',
    'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
    'src/anysolver/_stiffened_shell_ge_checkpoint_binary.py',
    'src/anysolver/_stiffened_shell_ge_distributing_reference.py',
    'src/anysolver/stiffened_shell.py',
    'tests/test_stiffened_shell_distributing_native_material.py')
for name in names:
    target = snapshot / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(repo / name, target)
records = root / 'source-v4-runtime'
records.mkdir()
log = (root / 'source-v4.log').read_text(encoding='utf-8-sig')
line = next(line for line in log.splitlines() if line.startswith('[development]'))
runtime = Path(line.split('record=', 1)[1])
for p in runtime.glob('*.json'):
    shutil.copyfile(p, records / p.name)
print('Prepared versioned installed checks and preserved successful source/runtime inputs.')
