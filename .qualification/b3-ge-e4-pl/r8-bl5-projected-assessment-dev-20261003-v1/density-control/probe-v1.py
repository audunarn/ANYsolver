"""ONE fixed-beam/shell density-subspace development control; no owner solve."""
from pathlib import Path
from fractions import Fraction as Q
import sys,json,hashlib,time,zipfile
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_info
from scripts.r8_bl5_density_subspace_dev import density_subspace_embedding,flat_reference_jacobian
from scripts._b3_e4_f03_sparse_certificate import SparseBudget
from scripts.r8_bl5_sparse_kernel_saved_dev import saved_csr
from scripts.r8_bl5_affine_flexible_native_dev import exact_transfer_moments

REPO=Path(r'C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
ROOT=Path(__file__).resolve().parent
GROUP=REPO/'docs/agent_plans/development/r8-bl5-projected-assessment-20261003'
RAW=REPO/'.qualification/b3-ge-e4-pl/r8-bl5-projected-assessment-dev-20261003-v1'
OWNER=RAW/'envelope/owners/ns64_b1_8/owner-v1'
BUDGET=SparseBudget(6924,4_000_000,1,512*1024**2)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(v,m):
 if not v:raise ValueError(m)
def store(arrays,name,value):
 value=value.tocsr();arrays.update({name+'_data':value.data.copy(),name+'_indices':value.indices.copy(),
  name+'_indptr':value.indptr.copy(),name+'_shape':np.array(value.shape,dtype=np.int64)})
def maximum(value):return float(np.max(np.abs(value.data),initial=0.))
def load_npz(p):
 with zipfile.ZipFile(p) as z:require(sum(e.file_size for e in z.infolist())<128*1024**2,'bounded saved arrays required')
 return np.load(p,allow_pickle=False)
require(not sys.flags.optimize,'explicit unoptimized guards required')
require(sha(REPO/'scripts/r8_bl5_density_subspace_dev.py')=='f049024905421c6773cce2d44fe75eb575ca2b97b74e300fe644973bb1209d05','frozen helper required')
dependencies={'r8_bl5_sparse_kernel_saved_dev.py':'064a0d8d36dca6db916d9a8eb2563620cf8c72cb82920bd4dc0c7182b6d1c138',
 '_b3_e4_f03_sparse_certificate.py':'2a4786d2990281d953ec58e65c2583f4de932b3bb4d10697df319c5432dfcfe2',
 'r8_bl5_sparse_kernel_interval_dev.py':'0f5b199822bfbdc52bdb95166008e4de59ce89e5c6a8d985727b574c2f5d2ab0'}
for name,digest in dependencies.items():require(sha(REPO/'scripts'/name)==digest,'frozen saved-loader dependency required: '+name)
manifest=GROUP/'raw-manifest-v8.json'
require(sha(manifest)=='4c6ffe7a94e0553b83b67a4f420d11599ed05c1e89b99e5093388a0ad4b0f73a','frozen owner manifest required')
records={r['path']:r['sha256'] for r in json.loads(manifest.read_text())['files']}
inputs=(OWNER/'summary.json',OWNER/'native/inputs.json',OWNER/'native/operators.npz',
 OWNER/'native/mz/raw-state.json',OWNER/'native/mz/raw-state.npz',OWNER/'native/mz/physical-actions.json')
for p in inputs:require(sha(p)==records[p.relative_to(REPO).as_posix()],'frozen input differs: '+p.name)
summary=json.loads(inputs[0].read_text());metadata=json.loads(inputs[1].read_text())
require(summary['status']=='COMPLETED_INSTALLED_DEVELOPMENT_ONLY' and summary['matching_modules']==417,'complete installed baseline required')
require(summary['wheel_sha256']=='1bf7dabd8771e76ed09825fb66a89e3e48d513dbb0321989c41701096a679632','same product wheel required')
require(sha(REPO/'scripts/r8_bl5_affine_flexible_native_dev.py')==summary['helper_sha256']['r8_bl5_affine_flexible_native_dev.py'],'same moment recovery source required')
require(metadata['fixture_case']=='ns64_b1_8' and metadata['policy']['span_halfcells']==4 and metadata['policy']['basis']=='discontinuous_p1_cell_average','exact frozen density required')
pools=threadpool_info();require(pools and all(p['num_threads']==1 for p in pools),'nonempty pools1 required')
mode=sys.argv[1];require(mode in ('prepare','case'),'declared stage required')
out=ROOT/('prepared-v1.json' if mode=='prepare' else 'control-v1.json')
require(not out.exists() and not out.with_suffix('.npz').exists(),'fresh paired outputs required')
started=time.monotonic();arrays={}
report=dict(identity='BL5_FIXED_NS64_H16_DENSITY_SUBSPACE_CONTROL_DEV_V1',stage=mode,status='STARTED',
 formal_f03_authority_consumed=False,qualification=False,source_sha256=sha(__file__),
 helper_sha256=sha(REPO/'scripts/r8_bl5_density_subspace_dev.py'),effective_pools=pools,
 dependencies=dependencies,
 inputs={p.relative_to(REPO).as_posix():sha(p) for p in inputs},
 limitation='Connection-only diagnostic outside candidateH4 rule; no kernel sign/nativebeta/norm/accuracy/qualification/release.')
def save():
 report['elapsed_seconds']=time.monotonic()-started
 np.savez_compressed(out.with_suffix('.npz'),**arrays)
 report['arrays_sha256']=sha(out.with_suffix('.npz'))
 out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
def build_c(blocks):
 row,col,val=[],[],[]
 for rows,basis,j,slots,weight in blocks:
  local=weight*(basis.T@j)
  for i,r in enumerate(rows):
   for k,c in enumerate(slots):
    if local[i,k]!=0.:row.append(r);col.append(c);val.append(float(local[i,k]))
 value=sparse.coo_matrix((val,(row,col)),shape=(max(max(b[0]) for b in blocks)+1,6924)).tocsr()
 value.eliminate_zeros();value.sort_indices();return value
def physical_recovery(q,fine_lam,local_js,local_slots):
 records_child=[];recovered=np.zeros(6924)
 beam_xyz=np.array(metadata['xyz_m'])[1105:];root=beam_xyz[0]
 for index,s in enumerate(metadata['station_traces']):
  rows=np.array(s['multiplier_rows']);density=np.array(s['density_basis'])@fine_lam[rows]
  p=s['beam_port'];d=np.array(s['reference_director']);b=np.array(s['director_basis']);arm=np.array(s['reference_arm_m']);lift=np.array(p['lift_m'])
  fb=density[:3];couple=np.cross(d,b.T@density[3:]);mb=np.cross(arm,fb)+couple
  ms=np.cross(.5*s['thickness_m']*d,-fb)-couple;alpha=s['shell_alpha'];w=p['weight']
  pullback=np.r_[(1-alpha)*(-fb),(1-alpha)*ms,alpha*(-fb),alpha*ms,(1-w)*fb,w*fb,mb+np.cross(lift,fb)]
  slots=local_slots[index];np.add.at(recovered,slots,s['measure_m']*pullback)
  require(np.max(np.abs(pullback+local_js[index].T@density))<=1e-8,'independent local physical work pullback required')
  xb=(1-w)*beam_xyz[p['node_indices'][0]]+w*beam_xyz[p['node_indices'][1]]+lift
  xs=(1-alpha)*np.array(s['shell_reference_m'])[0]+alpha*np.array(s['shell_reference_m'])[1]
  records_child.append(dict(x_m=float(xs[0]),measure_m=s['measure_m'],beam_wrench_about_root_density=np.r_[fb,mb+np.cross(xb-root,fb)].tolist(),
   five_channel_gap=(local_js[index]@q[slots]).tolist()))
 exact=exact_transfer_moments(records_child);region=exact_transfer_moments(records_child,(.25,.75))[0]
 return recovered,records_child,exact,region
try:
 if mode=='prepare':
  with load_npz(inputs[2]) as data:
   k=saved_csr(data,'K',sparse_budget=BUDGET);c=saved_csr(data,'C',False,sparse_budget=BUDGET)
   for name in ('free','fixed','coordinate_scale','constraint_scale','shell_rigid_work_map','beam_rigid_work_map'):
    arrays[name]=data[name].copy()
  with load_npz(inputs[4]) as data:
   for old,new in (('q','parent_q'),('multipliers','parent_lambda'),('load','load')):arrays[new]=data[old].copy()
  require(k.shape==(6924,6924) and c.shape==(40,6924),'same complete native operator required')
  require(metadata['layout']['counts']['physical_dofs']==6732 and metadata['layout']['counts']['retained_dofs']==192,'native roles preserved')
  require(np.array_equal(np.sort(np.r_[arrays['free'],arrays['fixed']]),np.arange(6924)),'complete support partition required')
  embedding=density_subspace_embedding();fineblocks=[];coarseblocks=[];js=[];slots_all=[]
  for s in metadata['station_traces']:
   p=s['beam_port'];require(np.array_equal(p['frame'],np.eye(3)),'flat identity reference frames only')
   cell=2*p['member_index']+p['native_cell'];require(0<=cell<16 and s['compiler_extra'][0]==cell,'physical halfcell identity required')
   fine_support=cell//4;coarse_support=cell//8
   rows=np.array(s['multiplier_rows'],dtype=int);slots=np.array(s['full_slots'],dtype=int)
   require(rows.tolist()==[2*(ch*4+fine_support)+mode for ch in range(5) for mode in range(2)],'actual channel-major fine rows required')
   require(slots.shape==(21,) and np.all((slots>=0)&(slots<6924)),'complete local physical/retained slots required')
   require(slots[12:].tolist()==[6630+6*n+axis for n in p['node_indices'] for axis in range(3)]+
    [6630+102+24*p['member_index']+3*p['native_cell']+axis for axis in range(3)],'native station variables preserved')
   j=flat_reference_jacobian(s['shell_alpha'],s['thickness_m'],s['reference_director'],s['director_basis'],s['reference_arm_m'],p['lift_m'],p['weight'])
   old=np.array(s['density_basis']);new=np.zeros((5,10));mean=float(Q(2*(cell%8)+1-8,8))
   expected=np.zeros((5,10));fine_mean=float(Q(2*(cell%4)+1-4,4))
   for ch in range(5):new[ch,2*ch:2*ch+2]=(1.,mean);expected[ch,2*ch:2*ch+2]=(1.,fine_mean)
   require(np.array_equal(old,expected),'reference fine halfcell mean required')
   coarse_rows=np.array([2*(ch*2+coarse_support)+m for ch in range(5) for m in range(2)])
   global_coarse=np.zeros((5,20));global_coarse[:,coarse_rows]=new
   require(np.array_equal(old@embedding[:,rows].T.toarray(),global_coarse),'exact per-station density subspace required')
   fineblocks.append((rows,old,j,slots,s['measure_m']));coarseblocks.append((coarse_rows,new,j,slots,s['measure_m']))
   js.append(j);slots_all.append(slots)
  require(len(js)==128 and sum(s['measure_m'] for s in metadata['station_traces'])==1.,'same reference segmentation/measure required')
  independent=build_c(fineblocks);direct=build_c(coarseblocks);child=(embedding@c).tocsr();child.sort_indices()
  original_error=maximum(independent-c)/max(maximum(c),np.finfo(float).tiny)
  subspace_error=maximum(direct-child)/max(maximum(child),np.finfo(float).tiny)
  report.update(original_constraint_relative_error=original_error,direct_child_relative_error=subspace_error,
   fine_rows=40,child_rows=20,order=6924,trace_count=128,load='Mz10Nm',definition_change='S4->S2 only, H4->H8 diagnostic')
  for name,value in (('K',k),('fine_C',c),('child_C',child),('direct_child_C',direct),('E',embedding)):store(arrays,name,value)
  arrays['local_J']=np.array(js);arrays['local_slots']=np.array(slots_all)
  arrays['child_constraint_scale']=np.asarray(abs(child)@arrays['coordinate_scale']).reshape(-1)
  # Bounded selected20-column exact-binary64 minor, not a global dense SVD,
  # inverse/nullspace or mixed-system stability certificate. Columns follow
  # actual compiled trace slots, never coordinate-based node-ID inference.
  components=(0,1,2,4,3);columns=[]
  for component in components:
   for edge_end in (4,20,36,52):
    columns.append(metadata['station_traces'][2*(edge_end-1)]['full_slots'][6+component])
  require(len(set(columns))==20 and set(columns)<=set(arrays['free'].tolist()),'independent supported minor columns required')
  minor=child[:,columns].toarray();table=[[Q(float(v)) for v in row] for row in minor];pivots=[]
  for column in range(20):
   candidates=[row for row in range(column,20) if table[row][column]!=0]
   require(candidates,'actual coarse constraint minor is rank-deficient')
   pivot=candidates[0];table[column],table[pivot]=table[pivot],table[column]
   diagonal=table[column][column];pivots.append(diagonal)
   for row in range(column+1,20):
    if table[row][column]:
     factor=table[row][column]/diagonal
     for col in range(column,20):table[row][col]-=factor*table[column][col]
  arrays['rank_minor_columns']=np.array(columns);arrays['rank_minor']=minor
  report['actual_coarse_row_rank']=20
  report['rational_minor_pivots']=[str(v) for v in pivots]
  report['rank_limitations']='Exact stored selected20-column minor only; no inf-sup, condition number or stability claim.'
  recovered,parent_records,parent_moments,parent_region=physical_recovery(arrays['parent_q'],arrays['parent_lambda'],arrays['local_J'],arrays['local_slots'])
  parent_action=json.loads(inputs[5].read_text())
  baseline_checks=dict(assembled_workmap=float(np.max(np.abs(recovered+c.T@arrays['parent_lambda'])))/10.,
   regional_wrench=float(np.max(np.abs(np.array(parent_region)-parent_action['exact_region_wrench'])))/10.,
   polynomial_moments=float(np.max(np.abs(np.array(parent_moments)-parent_action['exact_transfer_moments'])))/10.)
  report['baseline_recovery_checks']=baseline_checks
  require(all(v<=1e-8 for v in baseline_checks.values()),'independent frozen parent recovery must match before solving')
  report['status']='PREPARED_DEVELOPMENT_CONTROL'
  save()
  require(original_error<=1e-10 and subspace_error<=1e-10,'unchanged small-case operator parity required before solving')
  require(np.all(arrays['child_constraint_scale']>0),'physical child row scales required')
 else:
  prepath=ROOT/'prepared-v1.json';pre=json.loads(prepath.read_text())
  require(pre['status']=='PREPARED_DEVELOPMENT_CONTROL' and pre['source_sha256']==sha(__file__) and pre['helper_sha256']==report['helper_sha256'],'same prepared source required')
  require(pre['inputs']==report['inputs'] and pre['dependencies']==report['dependencies'],'same prepared input and loader maps required')
  require(pre['arrays_sha256']==sha(prepath.with_suffix('.npz')) and pre['original_constraint_relative_error']<=1e-10 and pre['direct_child_relative_error']<=1e-10,'successful bound preparation required')
  report['predecessor_json_sha256']=sha(prepath);report['predecessor_arrays_sha256']=pre['arrays_sha256']
  with load_npz(prepath.with_suffix('.npz')) as data:
   k=saved_csr(data,'K',sparse_budget=BUDGET);c=saved_csr(data,'child_C',False,sparse_budget=BUDGET)
   parent_c=saved_csr(data,'fine_C',False,sparse_budget=BUDGET);e=saved_csr(data,'E',False,sparse_budget=BUDGET)
   for name in ('free','fixed','coordinate_scale','child_constraint_scale','parent_q','parent_lambda','load',
    'local_J','local_slots','shell_rigid_work_map','beam_rigid_work_map'):arrays[name]=data[name].copy()
  site=Path(summary['site']);wheel=Path(summary['wheel']);require(sha(wheel)==summary['wheel_sha256'],'same installed wheel required')
  for name,digest in summary['module_sha256'].items():require(sha(site/name)==digest and sha(REPO/'src'/name)==digest,'source/site identity differs: '+name)
  sys.path.insert(0,str(site))
  import anysolver,numba
  from anysolver._b2_physical_linear_batch_dev import _accurate_sparse_residual
  from anysolver._stiffened_shell_ge_experimental import _linear_equilibrium,_scaled_constraint_gap
  require(Path(anysolver.__file__).is_relative_to(site) and numba.config.DISABLE_JIT,'bound installed utilities/JIToff required')
  report.update(imported_anysolver=anysolver.__file__,matching_modules=417,wheel_sha256=sha(wheel))
  free,fixed=arrays['free'],arrays['fixed'];load=arrays['load'];rhs=np.r_[load[free],np.zeros(20)]
  a=sparse.bmat([[k[free][:,free],c[:,free].T],[c[:,free],None]],format='csc')
  require(a.shape==(6837,6837) and a.nnz<4_000_000,'bounded sparse complete mixed system required')
  factor=sparse.linalg.splu(a);solution=factor.solve(rhs)
  for _ in range(2):solution+=factor.solve(-_accurate_sparse_residual(a,solution[:,None],rhs[:,None])[:,0])
  q=np.zeros(6924);q[free]=solution[:len(free)];lam=solution[len(free):];fine_lam=e.T@lam
  ct=c.T@lam;gradient=k@q;residual=gradient+ct-load;reaction=np.zeros(6924);reaction[fixed]=residual[fixed]
  weak=c@q;work=float(q@load);parentwork=float(arrays['parent_q']@load)
  arrays.update(q=q,lambda_coarse=lam,lambda_fine_lifted=fine_lam,reactions=reaction,equilibrium=residual,weak_gap=weak,
   omitted_fine_gap=parent_c@q,interface_resisting=ct)
  recovered,records_child,exact,region=physical_recovery(q,fine_lam,arrays['local_J'],arrays['local_slots'])
  maps={d:arrays[d+'_rigid_work_map'] for d in ('shell','beam')}
  applied={d:(m@load) for d,m in maps.items()};exerted={d:(m@(-ct)) for d,m in maps.items()};ground={d:m@reaction for d,m in maps.items()}
  loadscale=10.;workscale=max(abs(work),1e-12)
  checks=dict(equilibrium_ratio=_linear_equilibrium(residual[free],load[free],arrays['coordinate_scale'][free]),
   weak_gap=_scaled_constraint_gap(weak,arrays['child_constraint_scale']),energy_work=abs(float(q@gradient)-work)/workscale,
   compatible_work=abs(float(q@ct))/workscale,ground_work=abs(float(q@reaction))/workscale,
   local_and_assembled_workmap=float(np.max(np.abs(recovered+ct)))/loadscale,
   domain_cuts=max(float(np.max(np.abs(applied[d]+exerted[d]+ground[d])))/loadscale for d in maps),
   global_balance=float(np.max(np.abs(sum(ground.values())+sum(applied.values()))))/loadscale,
   beam_physical_workmap_scaled=float(np.max(np.abs(exerted['beam']-np.array(exact[0]))))/loadscale,
   shell_physical_workmap_scaled=float(np.max(np.abs(exerted['shell']+np.array(exact[0]))))/loadscale)
  report.update(status='COMPLETED_SAVED_OPERATOR_CONTROL_DEVELOPMENT_ONLY',physical_checks=checks,work_J=work,parent_work_J=parentwork,
   relative_work_change_percent=100*(work-parentwork)/parentwork,exact_transfer_moments=exact,exact_region_wrench=region,
   domain_wrenches={kind:{d:v.tolist() for d,v in values.items()} for kind,values in (('applied',applied),('connection_exerted',exerted),('ground',ground))},
   station_records=records_child,physical_nodal_scaled_change=float(np.linalg.norm((q[:6732]-arrays['parent_q'][:6732])/arrays['coordinate_scale'][:6732])/np.linalg.norm(arrays['parent_q'][:6732]/arrays['coordinate_scale'][:6732])),
   factorization_count=1,accurate_corrections=2,kkt_order=a.shape[0],kkt_nnz=a.nnz,positive_work_observed=work>0)
  save()
  for name,value in checks.items():require(np.isfinite(value) and value<=(1e-9 if name=='weak_gap' else 1e-8),'unchanged physical check failed: '+name)
 save()
 print(json.dumps({k:report.get(k) for k in ('status','original_constraint_relative_error','direct_child_relative_error','relative_work_change_percent','elapsed_seconds')}))
except BaseException as error:
 report.update(status='FAILED_DEVELOPMENT_CONTROL',failure=dict(type=type(error).__name__,message=str(error)))
 try:save()
 except BaseException as recording_error:error.add_note('Recording failed: '+repr(recording_error))
 raise
