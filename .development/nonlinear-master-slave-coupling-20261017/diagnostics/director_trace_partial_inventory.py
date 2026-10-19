"""Read-only raw snapshot inventory, no FE solve or acceptance reconstruction."""
import argparse, hashlib, json, pickle
from pathlib import Path
import numpy as np


def main():
    p=argparse.ArgumentParser(); p.add_argument("directory"); p.add_argument("output"); a=p.parse_args()
    rows=[]
    for path in sorted(Path(a.directory).glob("accepted-*.pkl")):
        raw=path.read_bytes(); value=pickle.loads(raw)
        rows.append(dict(path=str(path.resolve()),sha256=hashlib.sha256(raw).hexdigest(),
            lam=float(value["lam"]),control=value["control"],
            displacement_finite=bool(np.all(np.isfinite(value["u"]))),
            state_elements=sorted(value["states"])))
    record=dict(accepted_count=len(rows),snapshots=rows,terminal_result_exists=(Path(a.directory)/"result.json").exists(),
                equilibrium_or_accuracy_claim=False,iteration_or_deadline_residual_unmeasured=True)
    with Path(a.output).open("x",encoding="utf-8") as stream: json.dump(record,stream,indent=2)
    print(json.dumps(record))


if __name__=="__main__": main()
