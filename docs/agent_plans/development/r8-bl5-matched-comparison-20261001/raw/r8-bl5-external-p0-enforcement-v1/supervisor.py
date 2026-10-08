from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time,tempfile
import psutil
src=Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/scripts')
root=Path(tempfile.gettempdir())/'r8-bl5-external-p0-enforcement-v1'
root.mkdir(exist_ok=False)
files=['b3_e4_bl5_external_p0_enforcement_dev.py','b3_e4_bl5_matched_mz_reference_dev.py','b3_e4_bl5_matched_reference_actions.py','b3_e4_f03_bl5_opensees_line_reference.py']
identities={}
for name in files:shutil.copyfile(src/name,root/name);identities[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
assert identities[files[0]]=='180e2c33d1df17239fbf30f66d9c6b400eebbfa9e5f961d83e7c9b68bdc5fdac'
shutil.copyfile(__file__,root/'supervisor.py');identities['supervisor.py']=hashlib.sha256((root/'supervisor.py').read_bytes()).hexdigest()
runtime=Path(r'C:/Users/AudunArnesenNyhus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe');site=Path(r'C:/Python/Python314/Lib/site-packages')
strong=Path(tempfile.gettempdir())/'r8-bl5-matched-mz-reference-v1/mz'
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
command=[str(runtime),'-u',str(root/files[0]),'--site',str(site),'--output-dir',str(root/'case'),'--strong-reference-dir',str(strong)]
(root/'manifest.json').write_text(json.dumps({'source_parent':'12278092177c4ca70f4a026ea8c2462fb72781f7','sources':identities,'command':command,'thread_scope':'Library settings unavailable; stricter total process-tree OS-thread ceiling8 monitored and single-CPU affinity verified. Observations, not library-thread configuration or performance qualification.','timeout_seconds':600,'memory_limit_bytes':8*1024**3,'total_process_tree_thread_limit':8},indent=2))
start=time.monotonic();peak=0;max_threads=0;exceeded=None;affinity=None;tree=[]
with (root/'execution.log').open('w') as log:
 child=subprocess.Popen(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 parent=psutil.Process(child.pid)
 try:
  selected=parent.cpu_affinity()[0];parent.cpu_affinity([selected]);affinity=parent.cpu_affinity();assert affinity==[selected]
  while child.poll() is None:
   try:
    tree=[parent]+parent.children(recursive=True);live=[proc for proc in tree if proc.is_running()]
    peak=max(peak,sum(proc.memory_info().rss for proc in live));threads=sum(proc.num_threads() for proc in live);max_threads=max(max_threads,threads)
    if any(proc.cpu_affinity()!=affinity for proc in live):exceeded='affinity changed'
    if threads>8:exceeded='total process-tree OS threads exceed8'
   except psutil.NoSuchProcess:pass
   if time.monotonic()-start>600 or peak>8*1024**3:exceeded='time/memory ceiling exceeded'
   if exceeded:
    for proc in reversed(tree):
     try:proc.kill()
     except psutil.NoSuchProcess:pass
    break
   time.sleep(.01)
 except BaseException as error:
  exceeded=type(error).__name__+': '+str(error)
  if child.poll() is None:child.kill()
 code=child.wait()
result={'status':exceeded or ('passed' if code==0 else 'failed'),'exit_code':code,'elapsed_seconds':time.monotonic()-start,'sampled_process_tree_peak_rss_bytes':peak,'sampled_total_process_tree_max_OS_threads':max_threads,'verified_child_CPU_affinity':affinity,'sampling_seconds':.01,'thread_scope':'No numerical library-thread setting claim; observed bounded total OS threads and verified CPU affinity.','command':command}
(root/'execution.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
print('\n'.join((root/'execution.log').read_text().splitlines()[-6:]))
sys.exit(0 if result['status']=='passed' else 1)
