"""Deferred root-launched follow-up entry; outer supervisor owns time accounting."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import zipfile

RAW = Path(__file__).resolve().parent
REPO = RAW.parents[3]
mode, attempt, phase_attempt = sys.argv[1:4]
folder = RAW/attempt
manifest = json.loads((RAW/'inputs-manifest-followup-v1.json').read_text())
authority = json.loads((RAW/'authority-followup-v1.json').read_text())
assert authority['status'] == 'APPROVED' and authority['approval_evidence']
sys.path[:0] = [manifest['installed_provider_root'], manifest['ci_site'], str(REPO)]
import psutil


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, value):
    target = folder/name
    temporary = target.with_suffix(target.suffix+'.part')
    with temporary.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, target)


process = psutil.Process()
process.cpu_affinity([0])
stop = threading.Event()
samples, observations = [], []
owned = {}
owned_lock = threading.RLock()


def register(child):
    with owned_lock:
        created = child.create_time()
        if child.pid in owned:
            if owned[child.pid][1] != created: raise RuntimeError('owned PID creation identity changed')
        else:
            owned[child.pid] = (child, created)
        write('owned-processes.json', [dict(pid=pid, creation_time=created) for pid, (_, created) in owned.items()])


def terminate_fatal(reason):
    write('resource-failure.json', dict(reason=reason))
    with owned_lock:
        try:
            registry = dict(owned)
            followup.fatal_monitor_cleanup(process, registry)
        except Exception as error:
            write('cleanup-failure.json', dict(reason=str(error)))
            process.kill()  # Outer supervisor must verify recorded descendants.


def monitor():
    while not stop.is_set():
        try:
            tree = [process]+process.children(recursive=True)
            for child in tree[1:]: register(child)
            rss = sum(child.memory_info().rss for child in tree if child.is_running())
            samples.append(dict(rss=rss, monotonic=time.perf_counter()))
            if len(samples) % 50 == 0: write('rss-partial.json', samples)
            for child in tree:
                if child.name().lower() == 'ccx.exe':
                    observations.append(dict(pid=child.pid, affinity=child.cpu_affinity(), os_threads=child.num_threads()))
                if child.cpu_affinity() != [0] and child.name().lower() != 'conhost.exe':
                    write('resource-failure.json', dict(reason='observed CPU0 inheritance failure', pid=child.pid))
                    terminate_fatal('observed CPU0 inheritance failure')
            if rss > 2147483648:
                write('resource-failure.json', dict(reason='treeRSS2GiB exceeded', rss=rss))
                terminate_fatal('treeRSS2GiB exceeded')
        except psutil.NoSuchProcess:
            pass
        except Exception as error:
            write('monitor-failure.json', dict(reason=str(error)))
            terminate_fatal('generic monitor failure')
        stop.wait(.02)


thread = threading.Thread(target=monitor, daemon=True); thread.start()
try:
    # Hash frozen inputs before importing the candidate/helper modules.
    assert sha(__file__) == manifest['entry_sha256']
    assert sha(RAW/'supervise-followup-v1.ps1') == manifest['supervisor_sha256']
    for path, digest in manifest['inputs'].items():
        assert sha(path) == digest == sha(RAW/'input-snapshots-followup-v1'/manifest['snapshot_paths'][path])
    from scripts import r8_e03_force_observability_followup as followup
    from scripts import r8_e03_equation_force_audit as audit
    from scripts import r8_e03_curved_reference as reference
    import numpy, scipy, numba, llvmlite, anysolver, anymaterial
    from threadpoolctl import threadpool_info
    followup.validate_authority(authority, json.loads((RAW/'ledger-followup-v1.json').read_text()), mode)

    def identities():
        assert sha(__file__) == manifest['entry_sha256']
        assert sha(RAW/'supervise-followup-v1.ps1') == manifest['supervisor_sha256']
        for path, digest in manifest['inputs'].items():
            assert sha(path) == digest == sha(RAW/'input-snapshots-followup-v1'/manifest['snapshot_paths'][path])
        assert sha(manifest['wheel_path']) == manifest['reused_wheel_sha256']
        provider = Path(manifest['installed_provider_root'])
        with zipfile.ZipFile(manifest['wheel_path']) as wheel:
            payload = {name:followup.sha(wheel.read(name)) for name in wheel.namelist() if name.startswith('anysolver/') and name.endswith('.py')}
        assert payload == manifest['source_modules'] and len(payload) == 431
        for name, digest in payload.items():
            assert sha(REPO/'src'/name) == digest == sha(provider/name)
        assert Path(anysolver.__file__).resolve() == (provider/'anysolver/__init__.py').resolve()
        assert sha(anysolver.__file__) == payload['anysolver/__init__.py']
        assert Path(anymaterial.__file__).resolve() == Path(manifest['anymaterial_source']).resolve()
        assert sha(anymaterial.__file__) == manifest['anymaterial_sha256']
        assert sha(manifest['binary_path']) == audit.CCX_SHA256
        assert sha(manifest['source_archive_path']) == manifest['source_archive_sha256']

    def runtime():
        value = dict(affinity=process.cpu_affinity(), environment={key:os.environ.get(key) for key in manifest['thread_environment']},
            numba_threads=numba.get_num_threads(), jit_off=bool(numba.config.DISABLE_JIT), pools=threadpool_info(),
            versions={m.__name__:m.__version__ for m in (numpy, scipy, numba, llvmlite)}, executable=sys.executable,
            origins={m.__name__:dict(path=m.__file__, sha256=sha(m.__file__)) for m in (numpy, scipy, numba, llvmlite, anysolver, anymaterial)})
        assert value['affinity'] == [0] and value['environment'] == manifest['thread_environment']
        followup.validate_thread_environment(value['environment'])
        assert not any(k.startswith('CCX_NPROC_') and k not in manifest['thread_environment'] for k in os.environ)
        assert value['numba_threads'] == 1 and value['jit_off'] and all(p['num_threads'] == 1 for p in value['pools'])
        assert value['versions'] == manifest['runtime_versions'] and os.environ.get('OPENBLAS_CORETYPE') is None
        for m in (numpy, scipy, numba, llvmlite): assert Path(m.__file__).resolve().is_relative_to(Path(manifest['ci_site']).resolve())
        return value

    identities(); write('runtime-before.json', runtime()); write('python-launch.json', dict(command=list(sys.orig_argv), cwd=str(Path.cwd())))
    proposal = json.loads((RAW/'proposal-v3.json').read_text())
    result = None; code = 0
    if mode == 'controls':
        import pytest
        class Reports:
            def pytest_runtest_logreport(self, report):
                with (folder/'case-reports.jsonl').open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome, duration=report.duration, detail=str(report.longrepr) if report.failed else None))+'\n')
        snapshots = RAW/'input-snapshots-followup-v1'
        args = ['-q','-c',str(snapshots/'pyproject.toml'),'-o','pythonpath=', '--basetemp',str(folder/'temp'), '--junitxml='+str(folder/'junit.xml'),str(snapshots/'tests/test_stiffened_shell_e03_force_observability_followup.py')]
        write('pytest-command.json', args); code = pytest.main(args, plugins=[Reports()])
    elif mode in ('analytic','external'):
        if mode == 'external':
            analytic_bindings = json.loads((RAW/authority['analytic_finalization_attempt']/'analytic-bindings.json').read_text())
            followup.validate_confirmation(json.loads((RAW/'semantics-confirmation-v1.json').read_text()), analytic_bindings)
        definition = proposal[mode]
        phase = folder/'phase'; phase.mkdir()
        deck = RAW/definition['deck']; assert sha(deck) == definition['sha256']
        (phase/definition['deck']).write_bytes(deck.read_bytes())
        command = [manifest['binary_path']]+definition['command'][1:]
        write('phase-context.json', dict(mode=mode, command=command, phase=str(phase), deck_sha256=sha(deck), python_command=list(sys.orig_argv)))
        child = None; start = time.perf_counter()
        with (folder/'ccx-stdout.log').open('wb') as out, (folder/'ccx-stderr.log').open('wb') as err:
            try:
                # Launch and identity registration are indivisible with fatal
                # cleanup. RLock permits register's nested acquisition.
                with owned_lock:
                    child = subprocess.Popen(command, cwd=phase, env=os.environ.copy(), stdout=out, stderr=err)
                    try:
                        actual = psutil.Process(child.pid)
                        register(actual)
                        write('ccx-launch.json', dict(pid=child.pid, creation_time=owned[child.pid][1], command=command, cwd=str(phase), affinity=actual.cpu_affinity(), environment={k:os.environ.get(k) for k in manifest['thread_environment']}))
                        assert actual.cpu_affinity() == [0]
                    except Exception as registration_error:
                        # Popen retains the actual owned Windows process handle;
                        # no guessed PID is opened when capture/registration fails.
                        try:
                            if child.poll() is None: child.kill()
                            child.wait(timeout=2.)
                        except Exception as cleanup_error:
                            write('cleanup-failure.json', dict(reason=str(cleanup_error), registration_failure=str(registration_error)))
                            raise
                        write('ccx-registration-failure.json', dict(reason=str(registration_error), owned_child_exit_code=child.poll()))
                        raise
                child_code = child.wait()
            finally:
                write('ccx-process.json', dict(command=command, cwd=str(phase), exit_code=child.poll() if child else None, process_wall_seconds=time.perf_counter()-start, executable_sha256=sha(manifest['binary_path'])))
        if child_code != 0: raise followup.FollowupError('CCX failed')
    else:
        physical = mode.removeprefix('finalize-'); prior = RAW/phase_attempt
        outer = json.loads((prior/'execution.json').read_text()); context = json.loads((prior/'phase-context.json').read_text())
        # Preserve the prior raw attempt; refuse resources/provenance before success.
        assert outer['mode'] == physical and outer['status'] == 'completed' and outer['exit_code'] == 0 and outer['owned_child_exited']
        assert outer['input_manifest_sha256'] == sha(RAW/'inputs-manifest-followup-v1.json')
        assert outer['entry_sha256'] == sha(__file__) and outer['supervisor_sha256'] == manifest['supervisor_sha256']
        assert outer['authority_sha256'] == sha(RAW/'authority-followup-v1.json') and outer['command'] == context['python_command']
        assert outer['process_wall_seconds'] <= outer['seconds_limit']
        for name in ('resource-failure.json','monitor-failure.json','cleanup-failure.json'): assert not (prior/name).exists()
        resources = json.loads((prior/'resource-summary.json').read_text())
        assert resources['samples'] > 0 and 0 < resources['peak_tree_rss'] <= 2147483648
        launch = json.loads((prior/'ccx-launch.json').read_text()); observed = json.loads((prior/'ccx-observations.json').read_text())
        assert launch['affinity'] == [0] and launch['environment'] == manifest['thread_environment']
        assert observed and all(row['affinity'] == [0] and row['pid'] == launch['pid'] for row in observed)
        for name in ('runtime-before.json','runtime-after.json'):
            old = json.loads((prior/name).read_text()); now = runtime()
            assert old == now
        loaded = json.loads((prior/'loaded-modules.json').read_text())
        for row in loaded.values(): assert sha(row['path']) == row['sha256']
        inner = json.loads((prior/'ccx-process.json').read_text()); definition = proposal[physical]
        command = [manifest['binary_path']]+definition['command'][1:]
        assert inner['command'] == context['command'] == command and inner['exit_code'] == 0 and inner['executable_sha256'] == audit.CCX_SHA256
        phase = prior/'phase'; assert Path(inner['cwd']).resolve() == phase.resolve()
        assert sha(phase/definition['deck']) == context['deck_sha256'] == definition['sha256']
        stem = definition['command'][-1]
        def raw(path): return path.read_bytes() if path.is_file() else b''
        output = dict(sta=raw(phase/(stem+'.sta')), stdout=raw(prior/'ccx-stdout.log'), stderr=raw(prior/'ccx-stderr.log'))
        output['dat' if physical == 'analytic' else 'frd'] = raw(phase/(stem+('.dat' if physical == 'analytic' else '.frd')))
        receipt = dict(inner, deck_sha256=context['deck_sha256'], timed_out=False, resource_receipt_sha256=sha(prior/'execution.json'),
            **{name+'_sha256':followup.sha(data) for name,data in output.items()})
        if physical == 'analytic':
            result = followup.analytic_candidate(**output, receipt=receipt, deck_sha256=definition['sha256'], command=command)
        else:
            analytic_bindings = json.loads((RAW/authority['analytic_finalization_attempt']/'analytic-bindings.json').read_text())
            provenance = followup.validate_confirmation(json.loads((RAW/'semantics-confirmation-v1.json').read_text()), analytic_bindings)
            case = reference.build_case(0,1); original_deck, metadata = reference.build_deck(case)
            new_deck, prepared = audit.prepare_complete_force_output(original_deck, metadata)
            assert followup.sha(new_deck) == definition['sha256']
            write('case.json', case); write('prepared-metadata.json', prepared)
            result = followup.external_diagnostic(case, prepared, **output, receipt=receipt, command=command, provenance=provenance)
    identities()
    loaded = {name:dict(path=m.__file__, sha256=sha(m.__file__)) for name,m in sys.modules.items() if getattr(m,'__file__',None) and Path(m.__file__).is_file() and name.startswith(('anysolver','anymaterial','numpy','scipy','numba','llvmlite','scripts.r8_e03','scripts.r8_e02','test_stiffened_shell'))}
    for name,row in loaded.items():
        if name.startswith('anysolver'):
            relative = Path(row['path']).resolve().relative_to(Path(manifest['installed_provider_root']).resolve()).as_posix()
            assert row['sha256'] == manifest['source_modules'][relative]
        elif name.startswith('scripts.'):
            assert row['sha256'] == manifest['inputs'][str(Path(row['path']).resolve()).replace('\\','/')]
        elif name.startswith('test_stiffened_shell'):
            path = Path(row['path']).resolve()
            relative = path.relative_to((RAW/'input-snapshots-followup-v1').resolve()).as_posix()
            assert row['sha256'] == manifest['inputs'][str((REPO/relative).resolve()).replace('\\','/')]
    write('loaded-modules.json', loaded); write('runtime-after.json', runtime())
    if result is not None:
        write('finalization.json', result)
        if mode == 'finalize-analytic':
            write('analytic-bindings.json', dict(candidate_sha256=sha(folder/'finalization.json'), deck_sha256=proposal['analytic']['sha256'],
                source_archive_sha256=proposal['source_archive_sha256'], executable_sha256=audit.CCX_SHA256,
                outer_receipt_sha256=sha(RAW/phase_attempt/'execution.json'), input_manifest_sha256=sha(RAW/'inputs-manifest-followup-v1.json'),
                **{key+'_sha256':followup.sha(value) for key,value in output.items()}))
    raise SystemExit(code)
except Exception as error:
    write('entry-failure.json', dict(type=type(error).__name__, reason=str(error)))
    if mode.startswith('finalize-'): write('finalization-failure.json', dict(reason=str(error), raw_preserved_at=str(RAW/phase_attempt), production_qualified=False))
    raise
finally:
    stop.set(); thread.join(timeout=1)
    write('rss-samples.json', samples); write('ccx-observations.json', observations)
    write('resource-summary.json', dict(samples=len(samples), peak_tree_rss=max((row['rss'] for row in samples), default=0)))
