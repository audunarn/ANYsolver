from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time,tempfile
import psutil,ctypes
from ctypes import wintypes
src=Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/scripts')
root=Path(tempfile.gettempdir())/'r8-bl5-external-p0-enforcement-v2'
root.mkdir(exist_ok=False)
shutil.copyfile(Path(tempfile.gettempdir())/'r8-opensees-binary-thread-imports.json',root/'binary-thread-imports.json')
files=['b3_e4_bl5_external_p0_enforcement_dev.py','b3_e4_bl5_matched_mz_reference_dev.py','b3_e4_bl5_matched_reference_actions.py','b3_e4_f03_bl5_opensees_line_reference.py']
identities={}
for name in files:shutil.copyfile(src/name,root/name);identities[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
assert identities[files[0]]=='180e2c33d1df17239fbf30f66d9c6b400eebbfa9e5f961d83e7c9b68bdc5fdac'
shutil.copyfile(__file__,root/'supervisor.py');identities['supervisor.py']=hashlib.sha256((root/'supervisor.py').read_bytes()).hexdigest()
runtime=Path(r'C:/Users/AudunArnesenNyhus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe');site=Path(r'C:/Python/Python314/Lib/site-packages')
strong=Path(tempfile.gettempdir())/'r8-bl5-matched-mz-reference-v1/mz'
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
command=[str(runtime),'-u',str(root/files[0]),'--site',str(site),'--output-dir',str(root/'case'),'--strong-reference-dir',str(strong)]
(root/'manifest.json').write_text(json.dumps({'source_parent':'12278092177c4ca70f4a026ea8c2462fb72781f7','sources':identities,'command':command,'thread_scope':'Serial-route admission from exact binary imports/API observations plus single-CPU affinity. Numerical/unresolved starts capped8; OS ntdll/COM starts separately logged. No general numerical-library configuration/performance qualification.','timeout_seconds':600,'memory_limit_bytes':8*1024**3,'numerical_or_unresolved_thread_limit':8,'OS_support_start_modules':['ntdll.dll','combase.dll']},indent=2))
kernel=ctypes.WinDLL('kernel32',use_last_error=True);nt=ctypes.WinDLL('ntdll')
kernel.OpenThread.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenThread.restype=wintypes.HANDLE
kernel.CloseHandle.argtypes=[wintypes.HANDLE];nt.NtQueryInformationThread.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.ULONG,ctypes.c_void_p];nt.NtQueryInformationThread.restype=ctypes.c_long
def thread_record(proc):
 maps=proc.memory_maps(grouped=False);records=[]
 for th in proc.threads():
  handle=kernel.OpenThread(0x40,False,th.id);address=ctypes.c_void_p();code=None
  if handle:
   code=nt.NtQueryInformationThread(handle,9,ctypes.byref(address),ctypes.sizeof(address),None);kernel.CloseHandle(handle)
  module=None
  if code==0 and address.value:
   for m in maps:
    lo=int(m.addr,16)
    if lo<=address.value<lo+m.rss:module=m.path;break
  support=module is not None and Path(module).name.lower() in ('ntdll.dll','combase.dll')
  records.append({'pid':proc.pid,'id':th.id,'win32_start_address':address.value,'start_module':module,'query_status':code,'user_seconds':th.user_time,'system_seconds':th.system_time,'OS_support_start':support,'numeric_or_unresolved':not support})
 return records
start=time.monotonic();peak=0;max_threads=0;max_numeric=0;exceeded=None;affinity=None;tree=[];thread_samples=[]
with (root/'execution.log').open('w') as log:
 child=subprocess.Popen(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 parent=psutil.Process(child.pid)
 try:
  selected=parent.cpu_affinity()[0];parent.cpu_affinity([selected]);affinity=parent.cpu_affinity();assert affinity==[selected]
  while child.poll() is None:
   try:
    tree=[parent]+parent.children(recursive=True);live=[proc for proc in tree if proc.is_running()]
    peak=max(peak,sum(proc.memory_info().rss for proc in live));records=[item for proc in live for item in thread_record(proc)];threads=len(records);numeric=sum(item['numeric_or_unresolved'] for item in records);max_threads=max(max_threads,threads);max_numeric=max(max_numeric,numeric);thread_samples.append({'seconds':time.monotonic()-start,'threads':records})
    if any(proc.cpu_affinity()!=affinity for proc in live):exceeded='affinity changed'
    if numeric>8:exceeded='numerical or unresolved thread starts exceed8'
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
result={'status':exceeded or ('passed' if code==0 else 'failed'),'exit_code':code,'elapsed_seconds':time.monotonic()-start,'sampled_process_tree_peak_rss_bytes':peak,'sampled_total_process_tree_max_OS_threads':max_threads,'sampled_max_numerical_or_unresolved_starts':max_numeric,'verified_child_CPU_affinity':affinity,'sampling_seconds':.01,'thread_scope':'Recorded OS starts separately; declared serial route from exact binary/API observations, verified CPU affinity and capped numeric/unresolved starts. No general numerical-library thread-setting qualification.','command':command}
(root/'thread-samples.json').write_text(json.dumps(thread_samples,indent=2));(root/'execution.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
print('\n'.join((root/'execution.log').read_text().splitlines()[-6:]))
sys.exit(0 if result['status']=='passed' else 1)
