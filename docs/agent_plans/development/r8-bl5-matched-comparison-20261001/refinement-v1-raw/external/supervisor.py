from pathlib import Path
import ctypes,hashlib,json,os,shutil,subprocess,sys,tempfile,time
from ctypes import wintypes
import psutil
r=Path(tempfile.gettempdir());root=r/'r8-bl5-external-p0-family-v1';root.mkdir(exist_ok=False)
src=Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/scripts')
files=['b3_e4_bl5_external_p0_refinement_dev.py','b3_e4_bl5_external_p0_enforcement_dev.py','b3_e4_bl5_matched_mz_reference_dev.py','b3_e4_bl5_matched_reference_actions.py','b3_e4_f03_bl5_opensees_line_reference.py']
identities={}
for name in files:
 shutil.copyfile(src/name,root/name);identities[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
assert identities[files[0]]=='0e5435e0d38952642662eb1aad7dd374c341c866c9d099c87d2e66ce135a21c0'
shutil.copyfile(__file__,root/'supervisor.py');identities['supervisor.py']=hashlib.sha256((root/'supervisor.py').read_bytes()).hexdigest()
shutil.copyfile(r/'r8-bl5-external-p0-family-prerun-review.md',root/'prerun-review.md')
shutil.copyfile(r/'r8-opensees-binary-thread-imports.json',root/'binary-thread-imports.json')
runtime=Path(r'C:/Users/AudunArnesenNyhus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
site=Path(r'C:/Python/Python314/Lib/site-packages');first=r/'r8-bl5-external-p0-enforcement-v2/case'
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
jobs=[(16,'mz',True)]+[(n,c,False) for n in (16,32,64) for c in ('fy','mx','mz') if (n,c)!=(16,'mz')]
commands=[]
for n,c,reuse in jobs:
 command=[str(runtime),'-u',str(root/files[0]),'--site',str(site),'--output-dir',str(root/f'n{n}/{c}'),'--completed-first-level-dir',str(first),'--nx',str(n),'--case',c]
 if reuse:command+=['--reuse-completed-first-level']
 commands.append(command)
manifest={'classification':'bounded matched growing-space development; formalF03 unconsumed','parent_source':'f887c32a03962fbd520f64fb67bfc1cd0935f1a6','sources':identities,'commands':commands,'jobs':jobs,'physical_cases':{'fy':[0,100,0,0,0,0],'mx':[0,0,0,10,0,0],'mz':[0,0,0,0,0,10]},'limits':{'rows':100000,'seconds_per_child':600,'process_tree_bytes':8*1024**3,'numerical_or_unresolved_thread_starts':8,'one_heavy_job':True},'criteria':'Frozen helper physical/work/gap1e-8/1e-9, derivative1e-6 and existing floors unchanged. Three prescribed levels only. Programme1% requires demonstrated converged matched quantities, not single coarse agreement. No automatic fourth grid or space selection.','outcome_actions':'Converging common work/fields/transfer advances envelope; persistent disagreement/nonconvergence identifies obstruction, no automatic extra grid.','thread_scope':'Single CPU set while process suspended before child code. Sampled OS support starts do not prove thread work/lifetime or effective library settings; no general resource-qualified claim.'}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
kernel=ctypes.WinDLL('kernel32',use_last_error=True);nt=ctypes.WinDLL('ntdll')
kernel.OpenThread.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenThread.restype=wintypes.HANDLE
kernel.CloseHandle.argtypes=[wintypes.HANDLE]
nt.NtQueryInformationThread.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.ULONG,ctypes.c_void_p];nt.NtQueryInformationThread.restype=ctypes.c_long
def threads(proc):
 maps=proc.memory_maps(grouped=False);records=[]
 for th in proc.threads():
  handle=kernel.OpenThread(0x40,False,th.id);address=ctypes.c_void_p();code=None
  if handle:
   try:code=nt.NtQueryInformationThread(handle,9,ctypes.byref(address),ctypes.sizeof(address),None)
   finally:kernel.CloseHandle(handle)
  module=None
  if code==0 and address.value:
   for m in maps:
    if int(m.addr,16)<=address.value<int(m.addr,16)+m.rss:module=m.path;break
  support=module is not None and Path(module).name.lower() in ('ntdll.dll','combase.dll')
  records.append({'pid':proc.pid,'id':th.id,'win32_start_address':address.value,'start_module':module,'query_status':code,'user_seconds':th.user_time,'system_seconds':th.system_time,'OS_support_start':support,'numeric_or_unresolved':not support})
 return records
results=[]
for (nx,case,reuse),command in zip(jobs,commands):
 start=time.monotonic();peak=0;max_os=0;max_numeric=0;failure=None;samples=[];tree=[];affinity=None
 logpath=root/f'n{nx}-{case}.log'
 with logpath.open('w') as log:
  child=subprocess.Popen(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=4)
  parent=psutil.Process(child.pid)
  try:
   selected=parent.cpu_affinity()[0];parent.cpu_affinity([selected]);affinity=parent.cpu_affinity();assert affinity==[selected]
   parent.resume()
   while child.poll() is None:
    try:
     tree=[parent]+parent.children(recursive=True);live=[p for p in tree if p.is_running()]
     peak=max(peak,sum(p.memory_info().rss for p in live));records=[v for p in live for v in threads(p)]
     total=len(records);numeric=sum(v['numeric_or_unresolved'] for v in records)
     max_os=max(max_os,total);max_numeric=max(max_numeric,numeric);samples.append({'seconds':time.monotonic()-start,'threads':records})
     if any(p.cpu_affinity()!=affinity for p in live):failure='CPU affinity changed'
     if numeric>8:failure='numerical or unresolved thread starts exceed8'
    except psutil.NoSuchProcess:pass
    if time.monotonic()-start>600 or peak>8*1024**3:failure='time/memory ceiling exceeded'
    if failure:break
    time.sleep(.01)
  except BaseException as error:failure=type(error).__name__+': '+str(error)
  finally:
   if failure and child.poll() is None:
    for p in reversed([parent]+parent.children(recursive=True)):
     try:p.kill()
     except psutil.NoSuchProcess:pass
   code=child.wait()
 entry={'nx':nx,'case':case,'reuse':reuse,'status':failure or ('passed' if code==0 else 'failed'),'exit_code':code,'elapsed_seconds':time.monotonic()-start,'sampled_process_tree_peak_rss_bytes':peak,'sampled_total_process_tree_max_OS_threads':max_os,'sampled_max_numerical_or_unresolved_starts':max_numeric,'verified_before_child_code_CPU_affinity':affinity,'sampling_seconds':.01,'command':command}
 (root/f'n{nx}-{case}-thread-samples.json').write_text(json.dumps(samples,indent=2)+'\n');results.append(entry)
 (root/'execution.json').write_text(json.dumps({'results':results,'status':'IN_PROGRESS' if len(results)<9 and entry['status']=='passed' else ('COMPLETED_DEVELOPMENT_ONLY' if len(results)==9 and all(e['status']=='passed' for e in results) else 'FAILED')},indent=2)+'\n')
 print(json.dumps({k:entry[k] for k in ('nx','case','reuse','status','elapsed_seconds','sampled_process_tree_peak_rss_bytes','sampled_total_process_tree_max_OS_threads')}),flush=True)
 if entry['status']!='passed':
  print('\n'.join(logpath.read_text().splitlines()[-15:]),flush=True);sys.exit(1)
print('Completed9cases,8newexternal solves; no convergence/qualification inference',flush=True)
