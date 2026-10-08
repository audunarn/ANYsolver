from pathlib import Path
import tempfile,subprocess,json,time,psutil,ctypes
from ctypes import wintypes
p=Path(tempfile.gettempdir());root=p/'r8-opensees-thread-metadata-v1';root.mkdir(exist_ok=False)
exe=r'C:/Users/AudunArnesenNyhus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
child=subprocess.Popen([exe,str(p/'r8-opensees-thread-metadata-child.py'),str(root/'api.json')],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
proc=psutil.Process(child.pid);proc.cpu_affinity([proc.cpu_affinity()[0]])
kernel=ctypes.WinDLL('kernel32',use_last_error=True);nt=ctypes.WinDLL('ntdll')
kernel.OpenThread.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenThread.restype=wintypes.HANDLE
kernel.CloseHandle.argtypes=[wintypes.HANDLE];nt.NtQueryInformationThread.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.ULONG,ctypes.c_void_p];nt.NtQueryInformationThread.restype=ctypes.c_long
samples=[];start=time.monotonic()
while child.poll() is None:
 try:
  entries=[];maps=proc.memory_maps(grouped=False)
  for th in proc.threads():
   handle=kernel.OpenThread(0x40,False,th.id);address=ctypes.c_void_p();code=None
   if handle:
    code=nt.NtQueryInformationThread(handle,9,ctypes.byref(address),ctypes.sizeof(address),None);kernel.CloseHandle(handle)
   module=None;offset=None
   if code==0 and address.value:
    for m in maps:
     lo,hi=[int(x,16) for x in m.addr.split('-')]
     if lo<=address.value<hi:module=m.path;offset=address.value-lo;break
   entries.append({'id':th.id,'user_seconds':th.user_time,'system_seconds':th.system_time,'start_module':module,'module_offset':offset,'query_status':code})
  samples.append({'seconds':time.monotonic()-start,'threads':entries})
 except psutil.NoSuchProcess:break
 time.sleep(.05)
code=child.wait();log=child.stdout.read().decode(errors='replace');(root/'stdout.log').write_text(log)
(root/'samples.json').write_text(json.dumps(samples,indent=2));print(json.dumps({'exit':code,'maximum_OS_threads':max(len(s['threads']) for s in samples),'latest':samples[-1],'api':json.loads((root/'api.json').read_text())},indent=2))
