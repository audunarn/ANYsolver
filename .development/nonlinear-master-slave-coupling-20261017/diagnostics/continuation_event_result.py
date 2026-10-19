"""Summarize preserved terminal evidence without another solver invocation."""
import argparse,hashlib,json,pickle
from pathlib import Path

p=argparse.ArgumentParser(); p.add_argument('source'); p.add_argument('output'); a=p.parse_args()
rows=[]
for folder in sorted(Path(a.source).iterdir()):
    if not folder.is_dir(): continue
    terminal=folder/'terminal.pkl'
    if not terminal.exists(): continue
    data=pickle.loads(terminal.read_bytes()); accepted=sorted(folder.glob('accepted-*.pkl'))
    last=pickle.loads(accepted[-1].read_bytes()) if accepted else {}
    rows.append(dict(case=folder.name,status=data['status'],reason=data['stop_reason'],lam=data['load_factor'],control=last.get('control'),accepted=len(accepted),adaptation=data['info'].get('displacement_control_adaptation'),constraint_postcheck=data['info'].get('constraint_postcheck'),raw_files=[dict(name=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(folder.glob('*.pkl'))]))
Path(a.output).write_text(json.dumps(dict(solver_rerun=False,rows=rows),indent=2)); print(json.dumps(rows))
