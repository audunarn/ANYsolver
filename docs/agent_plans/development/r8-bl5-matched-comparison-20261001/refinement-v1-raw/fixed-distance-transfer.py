"""Existing raw work localization; no new solve or acceptance criterion."""
from pathlib import Path
import hashlib,json,tempfile
import numpy as np
r=Path(tempfile.gettempdir());native=r/'r8-bl5-native-p0-family-v1';external=r/'r8-bl5-external-p0-family-v1';out=native/'fixed-distance-transfer.json'
assert not out.exists();bindings={}
def read(p):
 bindings[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
bins=((0.,.125),(.125,.25),(.25,.5),(.5,.75),(.75,.875),(.875,1.))
report={'classification':'read-only fixed physical distance transfer allocation, no acceptance or new solve','bins_m':bins,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':{}}
for case in ('fy','mx','mz'):
 report['cases'][case]=[]
 for nx in (16,32,64):
  records=read(native/f'n{nx}/{case}/physical-transfer.json');data=read(external/f'n{nx}/{case}/recovered-actions.json');model=read(external/f'n{nx}/{case}/inputs.json')['model']
  origin=np.array(model['moment_origin_m']);beam=set(model['beam_node_ids']);nparts=[];eparts=[]
  for lo,hi in bins:
   n=sum((s['measure_m']*np.array(s['beam_wrench_about_root_density']) for s in records['station_records'] if lo<s['x_m']<hi),np.zeros(6))
   e=np.zeros(6)
   for s in data['support_records']:
    a,b=s['interval_m']
    assert not (a<lo<b or a<hi<b),'bins must not split support'
    if lo<=a and b<=hi:
     for node,load in s['independent_exerted_loads'].items():
      node=int(node)
      if node in beam:
       load=np.array(load);position=np.array(model['nodes'][str(node)])
       e+=np.r_[load[:3],load[3:]+np.cross(position-origin,load[:3])]
   nparts.append(n);eparts.append(e)
  ns=np.sum(nparts,axis=0);es=np.sum(eparts,axis=0)
  nref=np.array(records['polynomial_transfer_moments'][0]);eref=np.array(data['continuous_density_measures']['polynomial_x_moments']['0'])
  errors={'native_sum_max_abs':float(np.max(np.abs(ns-nref))),'external_sum_max_abs':float(np.max(np.abs(es-eref)))}
  assert max(errors.values())<=1e-8,'complete wrench partition must agree with retained degree-zero moments'
  item={'nx':nx,'native_bins':[v.tolist() for v in nparts],'external_bins':[v.tolist() for v in eparts],'bin_differences':[(a-b).tolist() for a,b in zip(nparts,eparts)],'whole_difference':(ns-es).tolist(),'sum_checks':errors}
  report['cases'][case].append(item)
report['bound_inputs']=bindings;out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
for case,values in report['cases'].items():
 v=values[-1];print(json.dumps({'case':case,'whole':v['whole_difference'],'root_0_0125':v['bin_differences'][0],'interior_0125_0875':np.sum(v['bin_differences'][1:-1],axis=0).tolist(),'tip_0875_1':v['bin_differences'][-1],'sum_checks':v['sum_checks']}))
