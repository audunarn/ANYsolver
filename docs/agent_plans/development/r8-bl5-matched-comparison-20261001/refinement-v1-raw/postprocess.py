"""Read-only complete matched-family/convergence summary; no product imports/solve."""
from pathlib import Path
import ast,hashlib,json,math,tempfile
import numpy as np
r=Path(tempfile.gettempdir());native=r/'r8-bl5-native-p0-family-v1';external=r/'r8-bl5-external-p0-family-v1'
out=native/'matched-family-summary.json';assert not out.exists()
helper=native/'b3_e4_bl5_matched_mz_native_dev.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest()=='92fa4515f1c61008f24bafe932e8fa2c50ea298903f2a1e5499e5be6c7dfaefb'
tree=ast.parse(helper.read_text());fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='field_errors')
scope={'np':np,'math':math,'LREF_M':1.};exec(compile(ast.Module(body=[fun],type_ignores=[]),str(helper),'exec'),scope)
bindings={}
def read(p):
 bindings[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
def arrays(p):
 bindings[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 with np.load(p,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def fields(which,nx,case):
 if which=='native':
  a=arrays(native/f'n{nx}/{case}/raw-state.npz')
  return a['shell_poses'],a['beam_nodal_poses'],a['shell_xyz_m'],a['beam_xyz_m']
 raw=read(external/f'n{nx}/{case}/raw-inventory.json');model=read(external/f'n{nx}/{case}/inputs.json')['model']
 ids=(model['shell_node_ids'],model['beam_node_ids'])
 return (*(np.array([raw['poses'][str(n)] for n in ns]) for ns in ids),*(np.array([raw['nodes'][str(n)] for n in ns]) for ns in ids))
def prolong(shell,beam,coarse,fine):
 assert fine==2*coarse and shell.shape==((coarse+1)*(coarse//4+1),6) and beam.shape==(2*coarse+1,6)
 grid=shell.reshape(coarse//4+1,coarse+1,6);result=[]
 for j in range(fine//4+1):
  y=j/2.;iy=min(int(y),coarse//4-1);dy=y-iy
  for i in range(fine+1):
   x=i/2.;ix=min(int(x),coarse-1);dx=x-ix
   result.append((1-dx)*(1-dy)*grid[iy,ix]+dx*(1-dy)*grid[iy,ix+1]+dx*dy*grid[iy+1,ix+1]+(1-dx)*dy*grid[iy+1,ix])
 trace=[]
 for i in range(2*fine+1):
  t=i/2.;k=min(int(t),2*coarse-1);a=t-k;trace.append((1-a)*beam[k]+a*beam[k+1])
 return np.array(result),np.array(trace)
def compare_fields(coarse_data,fine_data,coarse,fine):
 s,b=prolong(*coarse_data[:2],coarse,fine);fs,fb,xyzs,xyzb=fine_data
 cells=[(j*(fine+1)+i,j*(fine+1)+i+1,(j+1)*(fine+1)+i+1,(j+1)*(fine+1)+i) for j in range(fine//4) for i in range(fine)]
 return {'shell':scope['field_errors'](s,fs,cells,xyzs),'beam':scope['field_errors'](b,fb,[(i,i+1) for i in range(2*fine)],xyzb,True)}
report={'classification':'complete read-only matched three-level development summary; no F03/space/1% adjudication','levels':[16,32,64],'loads':{'fy100N':'fy','mx10Nm':'mx','mz10Nm':'mz'},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':{},'convergence_scope':'Successive common nodal Q1/P1 fields use exact dyadic prolongation then the existing two-Gauss L2, all6components/1m scale/1e-24 squared floor. Cell rotations remain separate. Work qTF is twice elastic strain energy. All raw transfer components retained; small-reference percent alone is not acceptance.'}
for case in ('fy','mx','mz'):
 levels=[]
 for nx in (16,32,64):
  summary=read(native/f'n{nx}/summary.json');result=read(native/f'n{nx}/{case}/result.json');extsummary=read(external/f'n{nx}/{case}/summary.json')
  assert summary['status']==result['status']==extsummary['status']=='completed'
  assert summary['final_preflight']['reference_linear_factorizations']==1
  cross=read(native/f'n{nx}/{case}/external-comparison.json');transfer=read(native/f'n{nx}/{case}/physical-transfer.json');windows=read(native/f'n{nx}/{case}/fixed-windows.json')
  ext=read(external/f'n{nx}/{case}/recovered-actions.json')
  levels.append({'nx':nx,'native_work_J':result['applied_work_J'],'external_work_J':ext['work_J']['applied'],'same_level_comparison':cross,'native_transfer':{'polynomial_x_moments':transfer['polynomial_transfer_moments'],'fixed_region_025_075':windows},'external_transfer':ext['continuous_density_measures'],'native_check_max':max(result['physical_checks'].values()),'external_check_max':max(ext['checks'].values()),'factorizations':1})
 successive=[]
 for i,(coarse,fine) in enumerate(((16,32),(32,64))):
  item={'coarse':coarse,'fine':fine}
  for name in ('native','external'):
   a,b=levels[i][name+'_work_J'],levels[i+1][name+'_work_J']
   item[name]={'work_signed_relative':(b-a)/max(abs(a),1e-12),'common_field_change':compare_fields(fields(name,coarse,case),fields(name,fine,case),coarse,fine)}
  successive.append(item)
 report['cases'][case]={'levels':levels,'successive':successive}
report['old16_mz_parity']=read(native/'n16/mz/old16-mz-raw-parity.json')
report['bound_inputs']=bindings
out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
for case,values in report['cases'].items():
 print(json.dumps({'case':case,'cross_work_percent':[100*x['same_level_comparison']['work_relative_signed'] for x in values['levels']],'cross_shell_L2_percent':[100*x['same_level_comparison']['field_errors']['shell']['combined_1m_relative_l2'] for x in values['levels']],'cross_beam_L2_percent':[100*x['same_level_comparison']['field_errors']['beam']['combined_1m_relative_l2'] for x in values['levels']],'last_work_change_percent':{n:100*values['successive'][-1][n]['work_signed_relative'] for n in ('native','external')}}))
