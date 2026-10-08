"""Lean saved-output adjudication. No solver/provider initialization in data modes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
import uuid

HOME = Path(__file__).resolve().parent
RAW = HOME.parent
REPO = RAW.parents[3]
mode, attempt, deadline_text = sys.argv[1:]
if mode not in ('analytic-adjudication', 'external', 'external-adjudication'):
    raise ValueError('unknown mode')
folder = HOME / attempt
deadline = float(deadline_text)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write(name, value):
    target = folder / name
    temporary = target.with_suffix(target.suffix + '.' + uuid.uuid4().hex + '.part')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    for index in range(8):
        try:
            temporary.replace(target)
            break
        except PermissionError:
            if index == 7:
                raise
            time.sleep(.01)

def need(condition, reason):
    if not condition:
        raise ValueError(reason)

manifest = read(HOME / 'manifest.json')
proposal = read(HOME / 'proposal.json')
need(attempt == proposal['next_attempts'][mode], 'explicit unique prospective attempt required')
authority = read(HOME / 'authority.json')
ledger = read(HOME / 'ledger.json')
need(authority['status'] == 'APPROVED' and authority['manifest_sha256'] == sha(HOME / 'manifest.json') and authority['proposal_sha256'] == sha(HOME / 'proposal.json'), 'matching approved authority required')
need(ledger['authority_sha256'] == sha(HOME / 'authority.json') and ledger['remaining_seconds'] is None and ledger['consumed'][mode] is True and ledger['in_flight']['mode'] == mode and Path(ledger['in_flight']['path']).resolve() == folder.resolve(), 'supervised durable consumed attempt required')
sys.path.insert(0, manifest['ci_site'])
sys.path.insert(0, str(REPO))
import psutil
from threadpoolctl import threadpool_info

process = psutil.Process()
process.cpu_affinity([0])
write('entry-root-process.json', {'pid': process.pid, 'creation_time': process.create_time(), 'affinity': process.cpu_affinity()})
stop = threading.Event()
lock = threading.RLock()
owned = {}
samples = []
observations = []
fatal = []

def console(child):
    return Path(child.exe()).resolve() == Path(os.environ['SystemRoot'], 'System32', 'conhost.exe').resolve()

def register(child):
    with lock:
        if child.pid in owned:
            need(child.create_time() == owned[child.pid][1], 'descendant PID reuse')
            return
        is_console = console(child)
        initial_affinity = child.cpu_affinity()
        if is_console:
            child.cpu_affinity([0])
        owned[child.pid] = (child, child.create_time(), is_console)
        write('owned-processes.json', [{'pid': pid, 'creation_time': row[1], 'console': row[2], 'owner_pid': process.pid, 'owner_creation_time': process.create_time()} for pid, row in owned.items()])
        if is_console:
            write('console-pin.json', {'pid': child.pid, 'creation_time': child.create_time(), 'executable': child.exe(), 'initial_affinity': initial_affinity, 'actual_affinity': child.cpu_affinity()})

def cleanup():
    # Kill only captured creation-bound descendants, before this owner exits.
    uncertain = []
    with lock:
        for pid, (child, creation, is_console) in list(owned.items()):
            if is_console:
                continue  # parent creation-bound cleanup owns console termination
            try:
                if child.create_time() == creation and child.is_running():
                    child.kill()
            except psutil.NoSuchProcess:
                pass
            except Exception as error:
                uncertain.append(str(error))
        _, alive = psutil.wait_procs([row[0] for row in owned.values() if not row[2]], timeout=max(0., min(1., deadline-time.perf_counter())))
        if alive:
            uncertain.append('owned descendants remain alive')
    if uncertain:
        write('cleanup-failure.json', {'uncertainty': uncertain})
    return uncertain

def monitor():
    try:
        while not stop.is_set():
            with lock:
                children = process.children(recursive=True)
                for child in children:
                    register(child)
                rss = process.memory_info().rss
                for child, creation, is_console in owned.values():
                    try:
                        if child.create_time() == creation and child.is_running():
                            rss += child.memory_info().rss
                            affinity = child.cpu_affinity()
                            if not is_console:
                                observations.append({'pid': child.pid, 'affinity': affinity, 'os_threads': child.num_threads()})
                            need(affinity == [0], 'descendant affinity')
                    except psutil.NoSuchProcess:
                        pass
                samples.append({'rss': rss, 'qpc': time.perf_counter()})
                need(process.cpu_affinity() == [0], 'owner affinity')
                need(rss <= 2147483648, 'process-tree memory limit')
                need(time.perf_counter() < deadline, 'absolute deadline')
            stop.wait(.02)
    except Exception as error:
        fatal.append(str(error))
        write('resource-failure.json', {'reason': str(error)})
        cleanup()

thread = threading.Thread(target=monitor, daemon=True)
thread.start()

def identities():
    for path, digest in manifest['frozen'].items():
        need(sha(path) == digest, 'frozen identity: ' + path)
    need(sha(__file__) == manifest['entry_sha256'], 'entry identity')
    need(sha(HOME / 'supervise.ps1') == manifest['supervisor_sha256'], 'supervisor identity')
    prior = read(RAW / 'inputs-manifest-followup-v2.json')
    for path, digest in prior['inputs'].items():
        need(sha(path) == digest, 'unchanged tested input: ' + path)
    loaded = read(RAW / 'analytic-v4/loaded-modules.json')
    need(len(loaded) == manifest['prior_loaded_rows'], 'complete original loaded identity inventory')
    for path, digest in {(row['path'], row['sha256']) for row in loaded.values()}:
        need(sha(path) == digest, 'original loaded identity: ' + path)
    write('identity-validation.json', {'prior_loaded_rows': len(loaded), 'tested_inputs': len(prior['inputs']), 'old_manifest_sha256': sha(RAW / 'inputs-manifest-followup-v2.json')})

def runtime():
    import numpy as np
    need(np.__version__ == '2.5.3', 'NumPy version')
    origin = Path(np.__file__).resolve()
    need(origin.is_relative_to(Path(manifest['ci_site']).resolve()), 'NumPy origin')
    loaded = read(RAW / 'analytic-v4/loaded-modules.json')
    need(origin == Path(loaded['numpy']['path']).resolve() and sha(origin) == loaded['numpy']['sha256'], 'current NumPy identity')
    for key, version in (('psutil', '7.2.2'), ('threadpoolctl', '3.6.0')):
        module = sys.modules[key]
        need(module.__version__ == version, 'current support dependency version: ' + key)
    for key, module in list(sys.modules.items()):
        if key == 'threadpoolctl' or key == 'psutil' or key.startswith('psutil.'):
            path = str(Path(module.__file__).resolve()).replace('\\', '/')
            need(path in manifest['support_dependencies'] and sha(path) == manifest['support_dependencies'][path], 'support dependency origin/hash: ' + key)
    pools = threadpool_info()
    need(bool(pools) and all(row['num_threads'] == 1 for row in pools), 'current numerical pools')
    env = {key: os.environ.get(key) for key in manifest['thread_environment']}
    need(env == manifest['thread_environment'] and os.environ.get('NUMBA_DISABLE_JIT') == '1', 'current environment')
    need(process.cpu_affinity() == [0], 'current CPU0')
    provider = any(key == 'anysolver' or key.startswith('anysolver.') or key == 'numba' or key.startswith('numba.') or key == 'anymaterial' or key.startswith('anymaterial.') for key in sys.modules)
    need(not provider, 'unused provider initialization')
    return {'affinity': [0], 'environment': env, 'jit_off_environment': True, 'numpy_version': np.__version__, 'numpy_origin': str(origin), 'pools': pools, 'provider_modules_initialized': provider}

def completed_outer(prior, old=False):
    outer = read(prior / 'execution.json')
    need(outer['status'] == 'completed' and type(outer['exit_code']) is int and outer['exit_code'] == 0 and outer['owned_child_exited'], 'saved execution not successful')
    need(0 < outer['process_wall_seconds'] <= outer['seconds_limit'], 'saved process wall/cap')
    if old:
        old_manifest = read(RAW / 'inputs-manifest-followup-v2.json')
        need(outer['input_manifest_sha256'] == sha(RAW / 'inputs-manifest-followup-v2.json'), 'old manifest binding')
        need(outer['entry_sha256'] == old_manifest['entry_sha256'] and outer['supervisor_sha256'] == old_manifest['supervisor_sha256'], 'old executable bindings')
        need(outer['authority_sha256'] == sha(RAW / 'authority-followup-v2.json'), 'old approval binding')
    else:
        need(outer['input_manifest_sha256'] == sha(HOME / 'manifest.json') and outer['authority_sha256'] == sha(HOME / 'authority.json'), 'new execution bindings')
        need(outer['entry_sha256'] == manifest['entry_sha256'] and outer['supervisor_sha256'] == manifest['supervisor_sha256'], 'new executable bindings')
    for name in ('resource-failure.json', 'monitor-failure.json', 'cleanup-failure.json', 'entry-failure.json'):
        need(not (prior / name).exists(), 'saved failure: ' + name)
    resources = read(prior / 'resource-summary.json')
    need(resources['samples'] > 0 and 0 < resources['peak_tree_rss'] <= 2147483648, 'saved resources')
    return outer

def adopted():
    analytic_attempt = HOME / proposal['next_attempts']['analytic-adjudication']
    completed_outer(analytic_attempt)
    bindings = read(analytic_attempt / 'analytic-bindings.json')
    need(bindings['candidate_sha256'] == sha(analytic_attempt / 'candidate.json'), 'candidate binding')
    return followup.validate_confirmation(read(HOME / 'semantics-confirmation.json'), bindings)

try:
    identities()
    write('runtime-before.json', runtime())
    from scripts import r8_e03_force_observability_followup as followup
    from scripts import r8_e03_equation_force_audit as audit
    completed_outer(RAW / 'controls-followup-v2', old=True)
    junit = ET.parse(RAW / 'controls-followup-v2/junit.xml').getroot()
    suites = [junit] if junit.tag == 'testsuite' else list(junit.findall('testsuite'))
    need(sum(int(row.attrib['tests']) for row in suites) == 62 and all(int(row.attrib.get(key, 0)) == 0 for row in suites for key in ('failures', 'errors', 'skipped')), 'exact 62 source-control pass')
    need(len(junit.findall('.//testcase')) == 62, 'complete source-control cases')
    write('source-controls-reuse.json', {'passed': 62, 'executed_again': False, 'junit_sha256': sha(RAW / 'controls-followup-v2/junit.xml'), 'receipt_sha256': sha(RAW / 'controls-followup-v2/execution.json'), 'tested_input_manifest_sha256': sha(RAW / 'inputs-manifest-followup-v2.json')})
    if mode == 'external':
        adopted()
        phase = folder / 'phase'
        phase.mkdir()
        deck = phase / 'e03.inp'
        deck.write_bytes((RAW / 'e03.inp').read_bytes())
        need(sha(deck) == proposal['external']['sha256'], 'unchanged external deck')
        command = [manifest['binary_path'], '-i', 'e03']
        write('phase-context.json', {'mode': 'external', 'command': command, 'phase': str(phase), 'deck_sha256': sha(deck), 'python_command': list(sys.orig_argv)})
        child = None
        start = time.perf_counter()
        with (folder / 'ccx-stdout.log').open('wb') as out, (folder / 'ccx-stderr.log').open('wb') as err:
            try:
                with lock:
                    need(not fatal and time.perf_counter() < deadline, 'launch resource/deadline')
                    child = subprocess.Popen(command, cwd=phase, env=os.environ.copy(), stdout=out, stderr=err)
                    try:
                        actual = psutil.Process(child.pid)
                        register(actual)
                        write('ccx-launch.json', {'pid': child.pid, 'creation_time': actual.create_time(), 'command': command, 'cwd': str(phase), 'affinity': actual.cpu_affinity(), 'environment': manifest['thread_environment']})
                        need(actual.cpu_affinity() == [0], 'direct external CPU0')
                    except Exception:
                        child.kill()
                        child.wait(timeout=max(.001, min(1., deadline-time.perf_counter())))
                        raise
                child.wait(timeout=max(.001, deadline-time.perf_counter()))
                need(child.returncode == 0, 'external exit code')
            finally:
                write('ccx-process.json', {'command': command, 'cwd': str(phase), 'exit_code': child.poll() if child else None, 'process_wall_seconds': time.perf_counter()-start, 'executable_sha256': sha(manifest['binary_path'])})
    else:
        analytic = mode == 'analytic-adjudication'
        prior = RAW / 'analytic-v4' if analytic else HOME / 'external-v1'
        definition = proposal['analytic' if analytic else 'external']
        outer = completed_outer(prior, old=analytic)
        need(outer['mode'] == ('analytic' if analytic else 'external'), 'saved physical mode')
        context = read(prior / 'phase-context.json')
        need(outer['command'] == context['python_command'], 'saved launch command')
        launch = read(prior / 'ccx-launch.json')
        write('physical-observation-validation.json', followup.validate_ccx_observations(launch, read(prior / 'ccx-observations.json')))
        before, after = read(prior / 'runtime-before.json'), read(prior / 'runtime-after.json')
        need(before == after and before['affinity'] == [0] and before['environment'] == manifest['thread_environment'], 'saved runtime stability')
        need(all(row['num_threads'] == 1 for row in before['pools']), 'saved thread pools')
        if analytic:
            need(before['jit_off'] is True and before['numba_threads'] == 1 and before['versions'] == manifest['runtime_versions'], 'original full runtime')
        else:
            need(before['jit_off_environment'] is True and not before['provider_modules_initialized'], 'lean external runtime')
        inner = read(prior / 'ccx-process.json')
        command = [manifest['binary_path']] + definition['command'][1:]
        phase = prior / 'phase'
        need(inner['command'] == context['command'] == launch['command'] == command, 'actual CCX commands')
        need(Path(inner['cwd']).resolve() == Path(launch['cwd']).resolve() == phase.resolve(), 'CCX physical directory')
        need(inner['executable_sha256'] == audit.CCX_SHA256 and type(inner['exit_code']) is int and inner['exit_code'] == 0, 'CCX identity/exit')
        need(sha(phase / definition['deck']) == context['deck_sha256'] == definition['sha256'], 'physical deck identity')
        stem = definition['command'][-1]
        output = {name: (prior / filename).read_bytes() for name, filename in [('stdout', 'ccx-stdout.log'), ('stderr', 'ccx-stderr.log')]}
        output['sta'] = (phase / (stem + '.sta')).read_bytes()
        output['dat' if analytic else 'frd'] = (phase / (stem + ('.dat' if analytic else '.frd'))).read_bytes()
        receipt = dict(inner, deck_sha256=definition['sha256'], timed_out=False, resource_receipt_sha256=sha(prior / 'execution.json'), **{key + '_sha256': followup.sha(value) for key, value in output.items()})
        if analytic:
            result = followup.zero_support_analytic_candidate(**output, receipt=receipt, deck_sha256=definition['sha256'], command=command)
        else:
            provenance = adopted()
            from scripts import r8_e03_curved_reference as reference
            case = reference.build_case(0, 1)
            original, metadata = reference.build_deck(case)
            deck, prepared = audit.prepare_complete_force_output(original, metadata)
            need(followup.sha(deck) == definition['sha256'], 'complete output reconstruction')
            result = followup.external_diagnostic(case, prepared, **output, receipt=receipt, command=command, provenance=provenance)
        identities()
        need(not fatal, 'current resource monitor refusal')
        write('candidate.json', result)
        if analytic:
            write('analytic-bindings.json', dict(candidate_sha256=sha(folder / 'candidate.json'), deck_sha256=definition['sha256'], source_archive_sha256=proposal['source_archive_sha256'], executable_sha256=audit.CCX_SHA256, outer_receipt_sha256=sha(prior / 'execution.json'), input_manifest_sha256=sha(HOME / 'manifest.json'), **{key + '_sha256': followup.sha(value) for key, value in output.items()}))
    write('runtime-after.json', runtime())
    need(not fatal, 'resource failure')
except BaseException as error:
    write('entry-failure.json', {'type': type(error).__name__, 'reason': str(error), 'production_qualified': False})
    raise
finally:
    stop.set()
    thread.join(timeout=max(0., min(1., deadline-time.perf_counter())))
    uncertainty = cleanup()
    write('rss-samples.json', samples)
    write('ccx-observations.json', observations)
    write('resource-summary.json', {'samples': len(samples), 'peak_tree_rss': max((row['rss'] for row in samples), default=0), 'cleanup_uncertainty': bool(uncertainty)})
    if fatal or uncertainty or thread.is_alive():
        raise RuntimeError('resource/cleanup uncertainty refuses completion')
