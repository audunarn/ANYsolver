"""Extract existing predictor raw indicators only; no FE assembly or solve."""
import argparse, json, pickle
from pathlib import Path
import numpy as np

p=argparse.ArgumentParser(); p.add_argument('folder'); p.add_argument('output'); a=p.parse_args()
folder=Path(a.folder); out=Path(a.output); out.mkdir(parents=True,exist_ok=False)
raw=pickle.loads((folder/'predictor-raw.pkl').read_bytes())
report=json.loads((folder/'predictor.json').read_text())
base=raw['accepted_H11']; eps=np.finfo(float).eps
metadata=[]
for eid,state in sorted(base['trial'].items()):
    if not isinstance(state,dict) or 'alpha' not in state: continue
    shape=np.asarray(state['alpha']).shape; size=np.asarray(state['alpha']).size
    for label in ('loading','hardening_y1','hardening_y2'):
        for flat in range(size):
            metadata.append(dict(element=int(eid),kind='beam' if 'fiber_strain' in state else 'shell',indicator=label,point_flat=flat,point_index=list(np.unravel_index(flat,shape))))
values=base['events'].values
assert len(values)==len(metadata)
results=[]
for record in report['branch_log']:
    i=record['index']; hk=record['machine_scale']; hp=record['probe_scale']
    machine=raw[f'direction-{i}-machine']; actual=raw[f'direction-{i}-selected']
    rates=(machine['events'].values-values)/hk
    near=np.asarray([m['indicator']=='loading' and abs(v+(1e-9 if m['kind']=='beam' else 1e-10)) <= (1e-8 if m['kind']=='beam' else 1e-10)+64*eps for m,v in zip(metadata,values)])
    uncertainty=64*eps*np.maximum(1.,np.maximum(abs(values),abs(machine['events'].values)))/hk
    selected=near & (abs(rates)>uncertainty)
    expected=values>0.; expected[selected]=rates[selected]>0.
    mismatch=np.flatnonzero(expected!=actual['events'].signature)
    entries=[]
    for j in mismatch:
        entries.append(dict(index=int(j),**metadata[j],base=float(values[j]),machine=float(machine['events'].values[j]),rate=float(rates[j]),rate_uncertainty=float(uncertainty[j]),selected=bool(selected[j]),linear_predicted_value=float(values[j]+hp*rates[j]),expected_positive=bool(expected[j]),actual=float(actual['events'].values[j]),actual_positive=bool(actual['events'].signature[j]),equation_64eps_bound=float(64*eps*max(1.,abs(values[j]),abs(actual['events'].values[j])))))
    d=(machine['q']-base['q'])/hk
    results.append(dict(direction=i,machine_scale=hk,probe_scale=hp,direction_inf=float(np.max(abs(d))),probe_q_delta_inf=float(np.max(abs(actual['q']-base['q']))),branch_changes_from_base=int(np.count_nonzero(actual['events'].signature!=base['events'].signature)),mismatches=entries))
result=dict(raw_extraction_only=True,no_force_assembly_or_linear_solve=True,directions=results)
(out/'result.json').write_text(json.dumps(result,indent=2,default=lambda x:int(x)))
print(json.dumps(result,default=lambda x:int(x)))
