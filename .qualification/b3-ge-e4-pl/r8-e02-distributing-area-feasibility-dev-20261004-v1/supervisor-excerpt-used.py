"""Owned bounded sequential affine-reference development supervisor."""
from pathlib import Path
import ctypes, hashlib, json, os, shutil, subprocess, sys, time
from ctypes import wintypes
import psutil

ROOT = Path(__file__).resolve().parent
REPO = Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
PREVIOUS = ROOT.parent/'r8-bl5-affine-installed-v1'
RUNTIME = Path('C:/Users/AudunArnesenNyhus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
EXTERNAL_SITE = Path('C:/Python/Python314/Lib/site-packages')
ENV = os.environ.copy()
ENV.update(OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', OMP_NUM_THREADS='1', NUMBA_NUM_THREADS='1',
           NUMBA_DISABLE_JIT='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
nt = ctypes.WinDLL('ntdll')
kernel.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel.OpenThread.restype = wintypes.HANDLE
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
nt.NtQueryInformationThread.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.ULONG, ctypes.c_void_p]
nt.NtQueryInformationThread.restype = ctypes.c_long


def threads(proc):
    maps, records = proc.memory_maps(grouped=False), []
    for th in proc.threads():
        handle = kernel.OpenThread(0x40, False, th.id)
        address, code = ctypes.c_void_p(), None
        if handle:
            try:
                code = nt.NtQueryInformationThread(handle, 9, ctypes.byref(address), ctypes.sizeof(address), None)
            finally:
                kernel.CloseHandle(handle)
        module = None
        if code == 0 and address.value:
            for m in maps:
                if int(m.addr, 16) <= address.value < int(m.addr, 16)+m.rss:
                    module = m.path; break
        support = module is not None and Path(module).name.lower() in ('ntdll.dll', 'combase.dll')
        records.append(dict(pid=proc.pid, id=th.id, start_module=module, query_status=code,
                            numeric_or_unresolved=not support))
    return records


def supervise(command, name, memory):
    folder = ROOT/name; folder.mkdir(exist_ok=False)
    started, peak, maximum, failure, samples = time.monotonic(), 0, 0, None, []
    with (folder/'stdout.log').open('x') as out, (folder/'stderr.log').open('x') as err:
        child = subprocess.Popen(command, cwd=ROOT, env=ENV, stdout=out, stderr=err, creationflags=4)
        parent = psutil.Process(child.pid); tree = [parent]; affinity = None
        try:
            selected = parent.cpu_affinity()[0]
            parent.cpu_affinity([selected]); affinity = parent.cpu_affinity()
            if affinity != [selected]: raise RuntimeError('before-execution affinity mismatch')
            parent.resume()
            while child.poll() is None:
                try:
                    tree = [parent]+parent.children(recursive=True)
                    live = [p for p in tree if p.is_running()]
                    peak = max(peak, sum(p.memory_info().rss for p in live))
                    records = [r for p in live for r in threads(p)]
                    numeric = sum(r['numeric_or_unresolved'] for r in records)
                    maximum = max(maximum, numeric)
                    samples.append({'seconds': time.monotonic()-started, 'threads': records})
                    if numeric > 8: failure = 'numeric/unresolved thread ceiling'
                    if any(p.cpu_affinity() != affinity for p in live): failure = 'affinity changed'
                except psutil.NoSuchProcess:
                    pass
                if time.monotonic()-started > 600: failure = 'time ceiling'
                if peak > memory: failure = 'memory ceiling'
                if failure: break
                time.sleep(.02)
        except BaseException as error:
            failure = type(error).__name__+': '+str(error)
        finally:
            if child.poll() is None:
                for p in reversed(tree):
                    try: p.kill()
                    except psutil.NoSuchProcess: pass
            code = child.wait(timeout=20)
    record = dict(status=failure or ('completed' if code == 0 else 'failed'), exit_code=code, command=command,
        elapsed_seconds=time.monotonic()-started, sampled_peak_tree_bytes=peak,
        sampled_numeric_or_unresolved_max=maximum, affinity_before_child_code=affinity,
        seconds_limit=600, memory_limit_bytes=memory, numerical_threads_limit=8,
        environment={k:ENV[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS','NUMBA_DISABLE_JIT')},
        thread_scope='Sampled start modules/affinity; effective OpenSees library-thread qualification unresolved',
        supervisor_sha256=sha(__file__))
    (folder/'execution.json').write_text(json.dumps(record, indent=2)+'\n')
    (folder/'thread-samples.json').write_text(json.dumps(samples, indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ('status','elapsed_seconds','sampled_peak_tree_bytes','sampled_numeric_or_unresolved_max')}), flush=True)
    if failure or code:
        raise RuntimeError('failed owned child '+str(folder))


