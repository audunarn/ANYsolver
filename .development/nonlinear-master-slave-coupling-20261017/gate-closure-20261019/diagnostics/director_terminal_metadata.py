"""Read trusted saved arrays only; no material/force/solver evaluations."""
from __future__ import annotations
import argparse
from collections import Counter
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import pickle
import numpy as np


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def plain(value):
    if isinstance(value, Mapping): return {str(k):plain(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [plain(v) for v in value]
    if isinstance(value,np.ndarray):
        return dict(shape=list(value.shape),dtype=str(value.dtype),sha256=hashlib.sha256(value.tobytes()).hexdigest())
    if isinstance(value,np.generic): return plain(value.item())
    if isinstance(value,float): return value if np.isfinite(value) else str(value)
    if value is None or isinstance(value,(str,int,bool)): return value
    return dict(type=type(value).__name__,representation=repr(value)[:300])


def material_summary(states):
    out={}
    for eid,state in states.items():
        if not isinstance(state,Mapping): continue
        row=dict(stored_keys=sorted(state),alpha_positive_means_history_not_current_loading=True)
        if 'alpha' in state:
            a=np.asarray(state['alpha']); row.update(alpha_max=float(np.max(a)),alpha_positive_count=int(np.count_nonzero(a>0)))
        for key in state:
            if any(word in str(key).lower() for word in ('active','yield','flow','hardening','return')):
                row[key]=plain(state[key])
        for key in ('fiber_stress','layer_stress'):
            if key in state:
                s=np.asarray(state[key]); row[key]=dict(shape=list(s.shape),minimum=float(np.min(s)),maximum=float(np.max(s)))
        out[str(eid)]=row
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    files=sorted(args.source.glob('accepted-*.pkl'))+[args.source/'terminal.pkl']
    before={f.name:digest(f) for f in files}
    accepted=[]
    for f in files[:-1]:
        with f.open('rb') as stream: value=pickle.load(stream)
        accepted.append(dict(path=str(f),control=value['control'],load_factor=value['lam'],
            material_summary=material_summary(value['element_states']) if f in files[-3:-1] else None))
    with files[-1].open('rb') as stream: terminal=pickle.load(stream)
    adaptation=terminal['info'].get('displacement_control_adaptation',{})
    seeds=adaptation.get('uncommitted_seeds',[])
    rhs=terminal.get('rhs_per_attempt',{})
    origins=terminal.get('attempt_origins',{})
    provenance=[]
    for seed in seeds:
        if seed.get('activation_cause') != 'failed_control_interval': continue
        key=(seed['step_index'],seed['attempt_index']); previous=(key[0],key[1]-1)
        equal=key in origins and previous in origins and origins[key]==origins[previous]
        provenance.append(dict(attempt=key,prior_attempt=previous,
            cutbacks=seed['failed_interval_cutbacks'],prior_actual_rhs=rhs.get(previous),
            same_accepted_origin=equal,
            current_q_sha256=hashlib.sha256(origins[key][0]).hexdigest() if key in origins else None))
    row=dict(kind='existing_director_terminal_metadata',status=terminal['status'],stop_reason=terminal['stop_reason'],
        load_factor=terminal['load_factor'],accepted=accepted,terminal_material=material_summary(terminal['element_states']),
        adaptation=plain(adaptation),rhs_per_attempt=plain(rhs),rhs_max=max(rhs.values()) if rhs else None,
        seed_count=len(seeds),seed_statuses=dict(Counter(s.get('status','missing') for s in seeds)),
        rejected_origin_provenance=provenance,
        input_sha256=before,raw_inputs_unchanged=before=={f.name:digest(f) for f in files},
        force_material_evaluations=0,global_rhs_solves=0,
        interpretation='Stored alpha indicates past plasticity only; current loading/yield event cannot be reconstructed without new material evaluation.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(row,indent=2,allow_nan=False,default=lambda x:x.item())+'\n',encoding='utf-8')
    print(json.dumps({k:row[k] for k in ('status','stop_reason','load_factor','rhs_max','seed_count','seed_statuses','raw_inputs_unchanged')},indent=2))
    print(json.dumps(dict(accepted=[{k:v for k,v in a.items() if k!='material_summary'} for a in accepted],adaptation=plain(adaptation)),default=lambda x:x.item()))


if __name__=='__main__':main()
