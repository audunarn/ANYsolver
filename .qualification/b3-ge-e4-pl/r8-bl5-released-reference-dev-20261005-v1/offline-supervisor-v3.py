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
                    if numeric > 1: failure = 'numeric/unresolved thread ceiling'
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
        seconds_limit=600, memory_limit_bytes=memory, numerical_threads_limit=1,
        environment={k:ENV[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS','NUMBA_DISABLE_JIT')},
        thread_scope='Sampled start modules/affinity; effective library-thread qualification not established; sampled source controls only',
        supervisor_sha256=sha(__file__))
    (folder/'execution.json').write_text(json.dumps(record, indent=2)+'\n')
    (folder/'thread-samples.json').write_text(json.dumps(samples, indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ('status','elapsed_seconds','sampled_peak_tree_bytes','sampled_numeric_or_unresolved_max')}), flush=True)
    if failure or code:
        raise RuntimeError('failed owned child '+str(folder))
