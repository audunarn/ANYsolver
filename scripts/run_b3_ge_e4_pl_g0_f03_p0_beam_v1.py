"""Single-use unregistered P0-beam full retained-KKT physical screen."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
import warnings

import numpy
import scipy
from scipy.sparse import SparseEfficiencyWarning

from _b3_e4_f03_native_fixture import build
from _b3_e4_f03_shell_trace import make_shell
from probe_b3_ge_e4_pl_g0_f03_k1_rank import candidate_spaces
from probe_b3_ge_e4_pl_g0_f03_kkt import (
    assemble, candidate_rank_context, reference_consistency,
)
from probe_b3_ge_e4_pl_g0_f03_k2p import solve_candidate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    args=parser.parse_args()
    args.root.mkdir(parents=True,exist_ok=False)
    directory=Path(__file__).parent
    names=('_b3_e4_f03_native_fixture.py','_b3_e4_f03_shell_trace.py',
           'probe_b3_ge_e4_pl_g0_f03_k1_rank.py',
           'probe_b3_ge_e4_pl_g0_f03_kkt.py',
           'probe_b3_ge_e4_pl_g0_f03_k2p.py')
    cases=[(topology,n_shell) for topology in ('Q4','S3-V2D')
           for n_shell in (1,2,4,8,16,32,64)]
    manifest=dict(purpose='UNREGISTERED_F03_P0_BEAM_SPAN_PHYSICAL_FALSIFICATION',
                  qualification=False,
                  source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  source_sha256={name:hashlib.sha256((directory/name).read_bytes()).hexdigest()
                                 for name in names},
                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  python=platform.python_version(),numpy=numpy.__version__,
                  scipy=scipy.__version__,n_native_half_cells=8,
                  spaces=('p0-beam',),loads=('smooth','sine'),
                  cases=[dict(topology=t,n_beam=8,n_shell=ns) for t,ns in cases],
                  limitations=('planar three-channel small-strain fixture',
                               'sampled pointwise gap is a lower bound',
                               'no signed native inf-sup or converged physical target',
                               'not F03/G0B acceptance'))
    (args.root/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n',
                                           encoding='utf-8')
    started=time.perf_counter()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore',category=SparseEfficiencyWarning)
        with (args.root/'records.jsonl').open('x',encoding='utf-8') as stream:
            for topology,n_shell in cases:
                beam=build(8)
                shell=make_shell(n_shell,topology)
                space=next(s for s in candidate_spaces(beam,shell)
                           if s.name=='p0-beam')
                coupling=assemble(beam,shell,space)
                reference=reference_consistency(beam,shell,coupling)
                rank=candidate_rank_context(beam,shell,coupling)
                result=solve_candidate(beam,shell,space,coupling,reference,rank)
                stream.write(json.dumps(dict(topology=topology,n_beam=8,
                                             n_shell=n_shell,result=result),
                                        sort_keys=True,allow_nan=False)+'\n')
                stream.flush()
    summary=dict(status='EXPLORATORY_NOT_QUALIFIED',records=len(cases),
                 elapsed_seconds=time.perf_counter()-started,
                 records_sha256=hashlib.sha256((args.root/'records.jsonl').read_bytes()).hexdigest(),
                 root=str(args.root))
    (args.root/'result.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n',
                                         encoding='utf-8')
    print(json.dumps(summary,sort_keys=True))


if __name__=='__main__':
    main()
