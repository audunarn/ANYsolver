"""Saved-output observability only; the original strict parser still adjudicates."""
from pathlib import Path
import hashlib, json, runpy, sys, threading, time
RAW=Path(__file__).resolve().parent
REPO=RAW.parents[2]
assert sys.argv[1]=='finalize-external' and sys.argv[3]=='external-v1'
manifest=json.loads((RAW/'inputs-manifest-v1.json').read_text())
sys.path[:0]=[manifest['ci_site'],str(REPO)]
import psutil
process=psutil.Process()
process.cpu_affinity([0])
probe_stop=threading.Event()
probe_samples=[]
def probe_monitor():
    while not probe_stop.is_set():
        try:
            tree=[process]+process.children(recursive=True)
            rss=sum(p.memory_info().rss for p in tree if p.is_running())
            probe_samples.append(rss)
            if rss>2147483648 or process.cpu_affinity()!=[0]:
                for p in reversed(tree): p.kill()
        except psutil.NoSuchProcess: pass
        probe_stop.wait(.02)
probe_thread=threading.Thread(target=probe_monitor,daemon=True)
probe_thread.start()
from scripts import r8_e03_curved_reference as reference
import numpy as np
from scripts import r8_e03_coarse_screen as screen
original=reference.parse_result

def observe(evidence_dir,*,receipt,raw):
    case=json.loads((Path(evidence_dir)/"case.json").read_text())
    metadata=json.loads((Path(evidence_dir)/"metadata.json").read_text())
    frd,sta,stdout,stderr=(raw[key] for key in ("frd","sta","stdout","stderr"))
    _,declared=reference.build_deck(case)
    assert reference.digest(metadata)==reference.digest(declared)
    assert hashlib.sha256((Path(evidence_dir)/"e03.inp").read_bytes()).hexdigest()==declared["deck_sha256"]
    displacements,reactions=reference.read_double_output(frd,declared)
    applied=np.sum(list(declared['nodal_loads'].values()),axis=0)
    force=np.sum(list(reactions.values()),axis=0)
    moment=np.zeros(3); root_moment=np.zeros(3)
    for node,value in reactions.items():
        root_moment+=np.cross(declared['physical_nodes'][node],value)
    moment+=root_moment
    for node,value in declared['nodal_loads'].items():
        moment+=np.cross(declared['physical_nodes'][node],value)
    work=sum(float(np.dot(value,displacements[node])) for node,value in declared['nodal_loads'].items())
    record=dict(status='DIAGNOSTIC_ONLY_NOT_ACCEPTED',force_balance_n=(force+applied).tolist(),
        moment_balance_nm=moment.tolist(),scaled_balance=reference.balance_measure(case,force+applied,moment),
        frozen_limit=reference.BALANCE_LIMIT,applied_force_n=applied.tolist(),reaction_force_n=force.tolist(),
        root_reaction_wrench=np.r_[force,root_moment].tolist(),external_work_j=work,
        reaction_nodes=len(reactions),loaded_nodes=len(declared['nodal_loads']),
        loaded_support_overlap=sorted(set(reactions)&set(declared['nodal_loads'])),
        raw_frd_sha256=hashlib.sha256(frd).hexdigest(),production_qualified=False,
        original_parser_called_unchanged=True)
    (RAW/sys.argv[2]/'saved-balance.json').write_text(json.dumps(record,indent=2,allow_nan=False)+'\n')
    original(case,metadata,frd,sta,stdout,stderr,receipt)
    raise RuntimeError("Saved-output diagnostic must not create a new finalization outcome")

screen.finish_screen=observe
try:
    runpy.run_path(str(RAW/'entry-v1.py'),run_name='__main__')
finally:
    probe_stop.set(); probe_thread.join(timeout=1)
    (RAW/sys.argv[2]/"probe-resource.json").write_text(json.dumps(dict(peak_tree_rss=max(probe_samples,default=0),samples=len(probe_samples))))