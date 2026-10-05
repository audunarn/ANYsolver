"""Serial isolated reference retention, with process-tree resource supervision."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, time
import psutil

source = Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/scripts')
root = Path(r'C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-bl5-matched-mz-native-v1')
runtime = Path(sys.executable)
site = p_site = Path(r'C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-staged-load-installed-v1/site')
external = Path(r'C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-bl5-matched-mz-reference-v1')
root.mkdir(exist_ok=False)
files = ['b3_e4_bl5_matched_mz_native_dev.py', 'b3_e4_bl5_coherent_aggregation_dev.py', 'b3_e4_bl5_matched_mz_reference_dev.py', 'b3_e4_bl5_matched_reference_actions.py', 'b3_e4_f03_bl5_opensees_line_reference.py']
identities = {}
for name in files:
    shutil.copyfile(source/name, root/name)
    identities[name] = hashlib.sha256((root/name).read_bytes()).hexdigest()
shutil.copyfile(__file__, root/'supervisor.py')
identities['supervisor.py'] = hashlib.sha256((root/'supervisor.py').read_bytes()).hexdigest()
(root/'manifest.json').write_text(json.dumps({'sources':identities,'runtime':str(runtime),
    'site':str(site),'case_order':['fy','mz'],'thread_scope':'target-process BLAS and Numba checks required', 'external_thread_scope':'unverified requests only', 'fixture_site':str(site.parent/'fixtures'), 'external':str(external),
    'source_parent':'5bee12f6e2f3c94ae07f028e691b4a1f97e9d79f'},indent=2))
env=os.environ.copy()
env.update(PYTHONPATH=os.pathsep.join([str(site),str(site.parent/'fixtures'),str(root)]), OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
           MKL_NUM_THREADS='1', NUMBA_NUM_THREADS='1', NUMBA_DISABLE_JIT='1')
results=[]
for case in ('fy','mz'):
    command=[str(runtime),'-u',str(root/files[0]),'--expected-site',str(site),'--external-dir',str(external/case),
             '--output-dir',str(root/case),'--case',case]
    start=time.monotonic(); peak=0; exceeded=None; tree=[]
    with (root/(case+'.log')).open('w') as log:
        child=subprocess.Popen(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
        parent=psutil.Process(child.pid)
        while child.poll() is None:
            try:
                tree=[parent]+parent.children(recursive=True)
                peak=max(peak,sum(p.memory_info().rss for p in tree if p.is_running()))
            except (psutil.NoSuchProcess,psutil.AccessDenied): pass
            if time.monotonic()-start>600 or peak>8*1024**3:
                exceeded='resource limit exceeded'
                for p in reversed(tree):
                    try:p.kill()
                    except psutil.NoSuchProcess:pass
                break
            time.sleep(.25)
        code=child.wait()
    result={'case':case,'command':command,'exit_code':code,'status':exceeded or
            ('passed' if code==0 else 'failed'),'elapsed_seconds':time.monotonic()-start,
            'sampled_process_tree_peak_rss_bytes':peak,'timeout_seconds':600,
            'memory_limit_bytes':8*1024**3}
    (root/(case+'-execution.json')).write_text(json.dumps(result,indent=2))
    results.append(result)
    print(json.dumps(result),flush=True)
    # Failure is retained; the independent other case has its own fresh process.
(root/'execution.json').write_text(json.dumps(results,indent=2))
sys.exit(0 if all(r['status']=='passed' for r in results) else 1)
