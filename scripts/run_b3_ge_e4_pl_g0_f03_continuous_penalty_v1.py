"""Single-use unregistered continuous spring sensitivity, not F03 mortar."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy
import scipy

from probe_b3_ge_e4_pl_g0_f03_continuous_penalty import self_check_penalty, solve


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    args=parser.parse_args()
    args.root.mkdir(parents=True,exist_ok=False)
    directory=Path(__file__).parent
    sources=(directory/'probe_b3_ge_e4_pl_g0_f03_continuous_penalty.py',
             directory/'probe_b3_ge_e4_pl_g0_f03_resolved_continuum.py',
             directory/'probe_b3_ge_e4_pl_g0_f03_independent_membrane.py')
    cases=[(t,l,n,k) for t in ('Q4','S3-V2D') for l in ('smooth','sine')
           for n in (8,16,32) for k in (1e11,1e12,1e13,1e14)]
    manifest=dict(purpose='UNREGISTERED_F03_CONTINUOUS_SPRING_SENSITIVITY',
                  qualification=False,
                  source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  python=platform.python_version(),numpy=numpy.__version__,scipy=scipy.__version__,
                  cases=[dict(topology=t,load=l,n_shell=n,n_y=n,n_beam=n,
                              penalty_translation_n_per_m2=k)
                         for t,l,n,k in cases],
                  limitations=('finite spring law, never exact multiplier acceptance',
                               'classical Q4/CST and conventional beam, not native E4/B3',
                               'large stiffness at fixed mesh can lock',
                               'sampled off-station gap is a lower bound'))
    (args.root/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n',
                                           encoding='utf-8')
    self_check_penalty()
    started=time.perf_counter()
    with (args.root/'records.jsonl').open('x',encoding='utf-8') as out:
        for topology,load,n,k in cases:
            item=solve(topology,n,n,n,load,k)
            out.write(json.dumps(item,sort_keys=True,allow_nan=False)+'\n')
            out.flush()
    result=dict(status='EXPLORATORY_NOT_QUALIFIED',records=len(cases),
                elapsed_seconds=time.perf_counter()-started,
                records_sha256=hashlib.sha256((args.root/'records.jsonl').read_bytes()).hexdigest(),
                root=str(args.root))
    (args.root/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',
                                         encoding='utf-8')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
