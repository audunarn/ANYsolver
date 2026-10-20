"""Seal one verified bundle; static artifact verification, no solver runs."""
import hashlib
import importlib.metadata
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import zipfile

HERE = Path(__file__).resolve().parent
SLICE = HERE.parent
TASK = SLICE.parents[1]
REPO = TASK.parents[1]
BUILD = Path('C:/ANYworkspaceWork/beam-shell-incremental-delivery-20261020/build-6fb907a1c-v2')
BUNDLE = BUILD / 'bundle'
load = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = load(BUNDLE / 'MANIFEST.json')
source = '6fb907a1ca9bedf7ea08b8b967dd264447d56437'
assert manifest['source_commit'] == source
assert manifest['omitted_features'] == []
spec = importlib.util.spec_from_file_location('installed_guard', BUNDLE / 'tests/conftest.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
runtime = guard.inspect_runtime()
records, nodes = {}, []
for label, expected in [('fast', 69), ('direct', 4), ('interpolated', 4)]:
    record = load(HERE / (label + '-runtime.json'))
    assert record['status'] == 'PASS' and record['exit_code'] == 0
    assert record['collected'] == expected and record['failed'] == 0
    assert record['outcomes'] == {'passed': expected}
    assert record['runtime']['jit_disabled'] and record['runtime']['numerical_threads'] == 1
    assert not record['runtime']['retired_programme']
    assert all(p['num_threads'] == 1 for p in record['runtime']['effective_pools'])
    records[label] = record
    nodes += record['node_ids']
assert len(nodes) == len(set(nodes)) == 77
smoke = load(HERE / 'smoke-result.json')
assert smoke['status'] == 'PASS' and len(smoke['cli_runs']) == 2
old = load(SLICE / 'DELIVERY.json')
assert sha(Path(old['bundle'])) == old['sha256'], 'preserve the earlier artifact'
# Independently tie the wheel, sdist and examples/tests to the requested Git source.
archive = subprocess.check_output(['git', '-C', str(REPO), 'archive', '--format=zip', source,
    '--', 'src/anysolver', 'examples/beam_shell_coupling.py', 'docs/BEAM_SHELL_CONNECTION.md',
    'tests/test_beam_shell_checkpoint_workflow.py', 'tests/test_beam_shell_workflow.py',
    'tests/test_beam_shell_connection_options.py', 'tests/test_director_integrated_trace.py',
    'tests/test_nonlinear_beam_shell_slice3_continuation.py'])
with zipfile.ZipFile(io.BytesIO(archive)) as frozen, zipfile.ZipFile(BUNDLE / 'wheelhouse' / manifest['solver_wheel']) as wheel:
    for relative, expected in manifest['source_files'].items():
        normalized = relative.replace('\\', '/')
        assert hashlib.sha256(frozen.read('src/' + normalized)).hexdigest() == expected
        assert hashlib.sha256(wheel.read(normalized)).hexdigest() == expected
    for name in frozen.namelist():
        if name.startswith(('examples/', 'docs/', 'tests/')) and not name.endswith('/'):
            assert (BUNDLE / name).read_bytes() == frozen.read(name), name
    with tarfile.open(BUNDLE / 'source-distribution' / manifest['sdist']) as distribution:
        contents = {member.name.partition('/')[2]: distribution.extractfile(member).read()
            for member in distribution.getmembers() if member.isfile()}
    for relative, expected in manifest['source_files'].items():
        assert hashlib.sha256(contents['src/' + relative.replace('\\', '/')]).hexdigest() == expected
    assert contents['examples/beam_shell_coupling.py'] == frozen.read('examples/beam_shell_coupling.py')
    assert ('version = "' + manifest['version'] + '"').encode() in contents['pyproject.toml']
verification = BUNDLE / 'verification'
verification.mkdir(exist_ok=False)
shutil.copyfile(BUNDLE / 'MANIFEST.json', verification / 'BUILD_MANIFEST.json')
for label in records:
    for suffix in ('-runtime.json', '-junit.xml'):
        shutil.copyfile(HERE / (label + suffix), verification / (label + suffix))
for filename in ('smoke-result.json', 'smoke-commands.json', 'install-commands.json',
                 'direct-preyield.stdout.json', 'interpolated-preyield.stdout.json'):
    shutil.copyfile(HERE / filename, verification / filename)
summaries = {}
for coupling in ('direct', 'interpolated'):
    folder = HERE / (coupling + '-temp') / ('checkpoint_' + coupling + '0')
    assert not (folder / 'reused-evidence.json').exists()
    shutil.copytree(folder, verification / ('checkpoint-' + coupling))
    summaries[coupling] = {}
    for phase in ('full', 'prefix', 'resumed'):
        command = load(folder / (phase + '.command.json'))
        assert command['exit_code'] == 0
        assert Path(command['command'][0]).resolve() == Path(runtime['executable']).resolve()
        assert Path(command['command'][1]).resolve() == (BUNDLE / 'examples/beam_shell_coupling.py').resolve()
        result = load(folder / (phase + '.stdout.txt'))
        assert result['completed'] and result['status'] == 'completed'
        assert result['checkpoint_written'] and result['control_error'] <= 1e-8
        assert result['constraint_postcheck']['status'] == 'passed'
        summaries[coupling][phase] = result
for name in ('refresh-build-6fb907a1c', 'refresh-install-6fb907a1c', 'refresh-installed-fast',
             'refresh-installed-preyield-cli', 'refresh-installed-checkpoint-direct',
             'refresh-installed-checkpoint-interpolated'):
    receipt = load(SLICE / 'evidence' / name / 'receipt.json')
    assert receipt['status'] == 'EXIT'
    target = verification / name
    target.mkdir()
    for filename in ('receipt.json', 'preflight.json', 'stdout.txt', 'stderr.txt'):
        path = SLICE / 'evidence' / name / filename
        if path.exists():
            shutil.copyfile(path, target / filename)
(verification / 'checkpoint-summary.json').write_text(json.dumps(summaries, indent=2) + '\n')
environment = {d.metadata['Name']: d.version for d in importlib.metadata.distributions() if d.metadata['Name']}
(BUNDLE / 'ENVIRONMENT.json').write_text(json.dumps(environment, indent=2, sort_keys=True) + '\n')
limitations = '''Registered development workflows only: S355 default direct/interpolated
coupling, completed-prefix restart to -11/60 m via -0.10 m. Original -0.20 m,
director continuation and analytical accuracy remain open. Three historical
director failures remain ordinary repository tests, unmodified and not part of
this installed selection. No full-suite, general accuracy or release claim.
Windows Python 3.12 only, disabled JIT, one effective numerical thread and retired
programme selection disabled. Wheel installed and tested; sdist built and its
complete solver/example contents checked against the same Git source, without
a separate source-install matrix. Numerical dependencies resolve from the
configured index; this bundle is not offline. Exact installed versions are in
ENVIRONMENT.json. The earlier pre-yield artifact is preserved with the same
private version and a different source/hash: use the explicit local wheel and
this bundle's SHA256 identity, never a version-only index selection.
'''
(verification / 'LIMITATIONS.txt').write_text(limitations)
with (BUNDLE / 'README.md').open('a', encoding='utf-8') as stream:
    stream.write('''
## Installed verification

77 unique focused tests passed (69 fast/compatibility, 4 direct checkpoint,
4 interpolated checkpoint), plus 2 standalone pre-yield CLIs and 6 separate
plastic full/prefix/resumed CLIs. All checkpoint processes used fresh models;
no prior solver-state fixture was reused. Target error <=1e-8 m, independent
relative reduced residual <=1e-7, material/restart, constraint/reaction,
cancellation, rejected-trial and failed-terminal refusal assertions passed at
the existing tolerances. These counts are not a passing full suite.

See verification/ for exact commands, source/input hashes, runtime/origin
receipts, counts, JSON outputs and copied accepted checkpoints. ENVIRONMENT.json
records every installed distribution. See verification/LIMITATIONS.txt.
The frozen source guide's private pre-yield-only artifact paragraph refers to
the earlier ab407246a build; this README/MANIFEST describe the refreshed 6fb907a1c
artifact, including both checkpoint workflows. No publication or release.
''')
manifest.update(status='VERIFIED_WINDOWS_PY312_REGISTERED_WORKFLOWS',
    verification=dict(unique_tests_passed=77, preyield_cli_passed=2, plastic_cli_passed=6,
        fresh_processes=True, payload_files_verified=runtime['payload_files_verified'],
        runtime=runtime, source_wheel_sdist_bytes_match=True, full_suite_claim=False),
    post_verification_metadata_changes=['README.md', 'MANIFEST.json', 'ENVIRONMENT.json', 'verification/'])
# No tested executable, test, wheel or source distribution is changed by sealing.
original = load(verification / 'BUILD_MANIFEST.json')
for name, expected in original['files'].items():
    if name != 'README.md':
        assert sha(BUNDLE / name) == expected, name
manifest['files'] = {str(p.relative_to(BUNDLE)): sha(p) for p in sorted(BUNDLE.rglob('*'))
    if p.is_file() and p != BUNDLE / 'MANIFEST.json'}
(BUNDLE / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
final = BUILD / ('ANYsolver-beam-shell-' + manifest['version'] + '-6fb907a1c-verified.zip')
assert not final.exists()
with zipfile.ZipFile(final, 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
    for path in sorted(BUNDLE.rglob('*')):
        if path.is_file():
            zipped.write(path, path.relative_to(BUNDLE))
delivery = dict(status=manifest['status'], source_commit=source, version=manifest['version'],
    bundle=str(final), sha256=sha(final), bytes=final.stat().st_size,
    installed_focused_passed=77, preyield_cli_passed=2, plastic_cli_passed=6,
    payload_files_verified=runtime['payload_files_verified'], installed_environment=runtime['prefix'],
    executable_payload_unchanged_after_checks=True, sdist_source_contents_verified=True,
    delivered_features=manifest['delivered_features'], omitted_workflows=[],
    scientific_clearance=False, full_suite_claim=False, old_artifact_preserved=old,
    budget_before_finalization=load(SLICE / 'budget.json'), published=False)
(HERE / 'DELIVERY.json').write_text(json.dumps(delivery, indent=2) + '\n')
print(json.dumps(dict(bundle=str(final), sha256=delivery['sha256'], passed=77)))
