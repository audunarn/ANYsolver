"""Installed development boundary for the mixed slice; no scientific campaign."""
from pathlib import Path
import hashlib, importlib.util, json, os, subprocess, sys

RAW = Path(__file__).resolve().parent
REPO = RAW.parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
BASE = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
assert sha(BASE) == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec = importlib.util.spec_from_file_location('bounded_integration', BASE)
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
s.ROOT = RAW; s.ENV.pop('PYTHONOPTIMIZE', None)
s.ENV.update(NUMEXPR_NUM_THREADS='1', NUMBER_OF_CPUS='1')
mode = sys.argv[1]
if mode == 'build':
    binding = {'source_parent': '8c827d1a', 'files': {}, 'scope': 'Installed development only, no qualification'}
    for root, dirs, files in os.walk(REPO/'src/anysolver'):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', 'us3-modal-canary')]
        for name in files:
            if name.endswith('.py'):
                p = Path(root)/name
                binding['files'][p.relative_to(REPO).as_posix()] = sha(p)
    for name in ('tests/test_stiffened_shell_ge_mixed_buckling.py', 'examples/stiffened_shell_ge_mixed_buckling.py',
                 'scripts/r8_ge_mixed_buckling_dev.py'):
        binding['files'][name] = sha(REPO/name)
    (RAW/'integration-binding-v1.json').write_text(json.dumps(binding, indent=2)+'\n')
    command = [sys.executable, str(__file__), 'build-child']
    s.ENV['PYTHONPATH'] = str(REPO)
elif mode == 'build-child':
    dist = RAW/'solver-dist-integration-v1'; dist.mkdir(exist_ok=False)
    commands = [[sys.executable, '-m', 'pip', 'wheel', str(REPO), '--no-index', '--no-deps',
                 '--no-build-isolation', '--no-cache-dir', '-w', str(dist)]]
    subprocess.run(commands[0], check=True, timeout=120)
    wheel, = dist.glob('*.whl')
    commands.append([sys.executable, '-m', 'pip', 'install', '--no-index', '--no-deps', '--no-cache-dir',
                     '--target', str(RAW/'site-integration-v1'), str(wheel)])
    subprocess.run(commands[1], check=True, timeout=120)
    (RAW/'artifact-integration-v1.json').write_text(json.dumps(dict(wheel=str(wheel), sha256=sha(wheel),
        commands=commands, source_binding=str(RAW/'integration-binding-v1.json')), indent=2)+'\n')
    raise SystemExit(0)
elif mode == 'installed':
    assert json.loads((RAW/'integration-build-v1/execution.json').read_text())['status'] == 'completed'
    binding = json.loads((RAW/'integration-binding-v1.json').read_text())
    assert all(sha(REPO/name) == digest for name, digest in binding['files'].items())
    s.ENV['PYTHONPATH'] = os.pathsep.join((str(RAW/'site-integration-v1'), str(REPO)))
    command = [sys.executable, str(__file__), 'installed-child']
elif mode == 'installed-child':
    import importlib.metadata as metadata
    import numpy, scipy, numba, psutil, pytest, anysolver
    from anysolver import stiffened_shell as public
    from threadpoolctl import threadpool_info
    site = RAW/'site-integration-v1'
    binding = json.loads((RAW/'integration-binding-v1.json').read_text())
    assert Path(anysolver.__file__).resolve().is_relative_to(site)
    assert Path(public.__file__).resolve().is_relative_to(site)
    for name, digest in binding['files'].items():
        if name.startswith('src/'):
            assert sha(site/name[4:]) == digest, name
    assert numba.config.DISABLE_JIT and not sys.flags.optimize
    assert len(psutil.Process().cpu_affinity()) == 1
    pools = threadpool_info(); assert pools and all(p['num_threads'] == 1 for p in pools)
    record = dict(status='IN_PROGRESS', solver_import=anysolver.__file__, public_import=public.__file__,
        package_files=sum(name.startswith('src/') for name in binding['files']), pools=pools,
        dependencies={name: metadata.version(name) for name in ('numpy','scipy','numba','anysolver','ANYmaterial')},
        qualified=False)
    save = lambda: (RAW/'installed-integration-result-v1.json').write_text(json.dumps(record, indent=2)+'\n')
    save()
    status = pytest.main(['-q', '-p', 'no:cacheprovider', '--basetemp', str(RAW/'pytest-temp-integration-v1'),
        '--junitxml='+str(RAW/'installed-integration-junit-v1.xml'),
        str(REPO/'tests/test_stiffened_shell_ge_mixed_buckling.py')])
    record.update(pytest_exit=int(status), status='FAILED_TESTS' if status else 'PASSED_INSTALLED_DEVELOPMENT')
    save()
    if status: raise SystemExit(int(status))
    from examples.stiffened_shell_ge_mixed_buckling import workflow
    result = workflow()
    assert result['status'] == 'completed' and result['accepted_checkpoint_unchanged']
    assert max(result['equation_residuals']) <= 1e-8 and max(result['constraint_residuals']) <= 1e-8
    record.update(example=result, status='PASSED_INSTALLED_PUBLIC_DEVELOPMENT')
    save()
    raise SystemExit(0)
else:
    raise ValueError('build/installed only')
s.supervise(command, 'integration-'+mode+'-v1', 2*1024**3)
