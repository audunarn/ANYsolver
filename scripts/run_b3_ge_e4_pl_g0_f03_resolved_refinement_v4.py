"""One-shot unregistered joint/one-sided continuum refinement screen."""

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

from probe_b3_ge_e4_pl_g0_f03_resolved_continuum import self_check, solve


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=False)
    base = Path(__file__).parent
    source = base/'probe_b3_ge_e4_pl_g0_f03_resolved_continuum.py'
    cases = sorted(set(
        (topology, load, n, n, n)
        for topology in ('Q4', 'S3-V2D')
        for load in ('smooth', 'sine')
        for n in (16, 32, 64)
    ) | set(
        (topology, load, 64, n_y, n_beam)
        for topology in ('Q4', 'S3-V2D')
        for load in ('smooth', 'sine')
        for n_y in (2, 8, 32, 64)
        for n_beam in (8, 64)
    ))
    manifest = dict(purpose='UNREGISTERED_F03_CONTINUUM_JOINT_AND_FIXED_REFINEMENT',
                    qualification=False,
                    source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    python=platform.python_version(), numpy=numpy.__version__,
                    scipy=scipy.__version__,
                    cases=[dict(topology=t, load=l, n_shell=ns, n_y=ny, n_beam=nb)
                           for t, l, ns, ny, nb in cases],
                    limitations=('classical Q4 differs from E4-PL hybrid Q4',
                                 'native retained B3 differs from conventional Timoshenko',
                                 'finite station collocation differs from continuous line law',
                                 'gap extrema are floating-point estimates, not certified bounds',
                                 'no registered signed inf-sup or release acceptance'))
    (args.root/'manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2)+'\n',
                                           encoding='utf-8')
    self_check()
    started = time.perf_counter()
    with (args.root/'records.jsonl').open('x', encoding='utf-8') as stream:
        for topology, load, ns, ny, nb in cases:
            item = solve(topology, ns, nb, load, ny)
            stream.write(json.dumps(item, sort_keys=True, allow_nan=False)+'\n')
            stream.flush()
    result = dict(status='EXPLORATORY_NOT_QUALIFIED',
                  records=len(cases), seconds=time.perf_counter()-started,
                  records_sha256=hashlib.sha256((args.root/'records.jsonl').read_bytes()).hexdigest(),
                  root=str(args.root))
    (args.root/'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n',
                                         encoding='utf-8')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
