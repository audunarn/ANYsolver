from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile,time
import psutil
r=Path(tempfile.gettempdir());root=r/'r8-bl5-native-p0-family-v1';root.mkdir(exist_ok=False)
src=Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/scripts')
names=['b3_e4_bl5_matched_p0_native_refinement_dev.py','b3_e4_bl5_matched_mz_native_dev.py','b3_e4_bl5_coherent_aggregation_dev.py','b3_e4_bl5_matched_mz_reference_dev.py','b3_e4_bl5_matched_reference_actions.py','b3_e4_f03_bl5_opensees_line_reference.py']
bindings={}
for name in names:
 shutil.copyfile(src/name,root/name);bindings[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
assert bindings[names[0]]=='143297217ec7a4851fb79f83155d23adce7d38971bc82760e94c82a5a1f83fd7'
shutil.copyfile(__file__,root/'supervisor.py');bindings['supervisor.py']=hashlib.sha256((root/'supervisor.py').read_bytes()).hexdigest()
review=r/'r8-bl5-native-p0-family-prerun-review.md';assert review.exists();shutil.copyfile(review,root/'prerun-review.md')
site=r/'r8-staged-load-installed-v1/site';fixtures=r/'r8-staged-load-installed-v1/fixtures'
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',NUMBA_DISABLE_JIT='1',PYTHONNOUSERSITE='1',PYTHONPATH=os.pathsep.join((str(site),str(fixtures))))
commands=[[sys.executable,'-u',str(root/names[0]),'--site',str(site),'--output-dir',str(root/f'n{nx}'),'--nx',str(nx),'--external-level-dir',str(r/f'r8-bl5-external-p0-family-v1/n{nx}'),'--prior-16-mz-dir',str(r/'r8-bl5-matched-mz-native-v1/mz')] for nx in (16,32,64)]
manifest={'classification':'installed native matched growing-space development; formalF03 unconsumed','sources':bindings,'commands':commands,'wheel_sha256':'0c45666609355e654cb726a0e4e0780d386bccfaafef1209ffd994bdd3b9d09c','levels':[16,32,64],'cases':['fy100N','mx10Nm','mz10Nm'],'rows':[40,80,160],'limits':{'rows':100000,'seconds_per_child':600,'process_tree_bytes':8*1024**3,'numerical_threads':8,'one_heavy_job':True},'scope':'New full raw three-RHS collection where earlier screens lacked complete fields; one eligible factorization per geometry. Same16Mz raw parity checked in postprocessing. No production mechanics/criteria changes or automatic fourth level.'}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
results=[]
for nx,command in zip((16,32,64),commands):
 start=time.monotonic();peak=0;failure=None;tree=[]
 with (root/f'n{nx}.log').open('w') as log:
  child=subprocess.Popen(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
  parent=psutil.Process(child.pid)
  try:
   while child.poll() is None:
    try:
     tree=[parent]+parent.children(recursive=True);peak=max(peak,sum(p.memory_info().rss for p in tree if p.is_running()))
    except psutil.NoSuchProcess:pass
    if time.monotonic()-start>600 or peak>8*1024**3:failure='time/memory ceiling exceeded';break
    time.sleep(.05)
  except BaseException as error:failure=type(error).__name__+': '+str(error)
  finally:
   if failure and child.poll() is None:
    for p in reversed([parent]+parent.children(recursive=True)):
     try:p.kill()
     except psutil.NoSuchProcess:pass
   code=child.wait()
 entry={'nx':nx,'status':failure or ('passed' if code==0 else 'failed'),'exit_code':code,'elapsed_seconds':time.monotonic()-start,'sampled_process_tree_peak_rss_bytes':peak,'command':command}
 results.append(entry);(root/'execution.json').write_text(json.dumps({'results':results,'status':'COMPLETED_DEVELOPMENT_ONLY' if len(results)==3 and all(x['status']=='passed' for x in results) else ('IN_PROGRESS' if entry['status']=='passed' else 'FAILED')},indent=2)+'\n')
 print(json.dumps({k:entry[k] for k in ('nx','status','elapsed_seconds','sampled_process_tree_peak_rss_bytes')}),flush=True)
 if entry['status']!='passed':print('\n'.join((root/f'n{nx}.log').read_text().splitlines()[-18:]));sys.exit(1)
print('Three installed geometries/nine full-state cases complete; no converged acceptance inference',flush=True)
