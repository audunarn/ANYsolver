"""Single-use, unregistered F03 continuum comparator screen; not acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess

import numpy
import scipy

from probe_b3_ge_e4_pl_g0_f03_resolved_continuum import self_check, solve


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).with_name('probe_b3_ge_e4_pl_g0_f03_resolved_continuum.py')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    manifest = dict(purpose='UNREGISTERED_F03_RESOLVED_COMPARATOR_SCREEN',
                    qualification=False, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    source_revision=revision, python=platform.python_version(),
                    numpy=numpy.__version__, scipy=scipy.__version__,
                    topology=('Q4', 'S3-V2D'), n_shell=(2, 4, 8, 16),
                    n_y=('fixed_2', 'joint_2n_shell'), n_beam='2n_shell',
                    loads=('smooth', 'sine'),
                    limitations=('classical rather than E4 Q4',
                                 'conventional rather than native retained beam',
                                 'station collocation rather than line mortar',
                                 'no fully converged continuum target'))
    (args.root/'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n',
                                           encoding='utf-8')
    self_check()
    count = 0
    with (args.root/'records.jsonl').open('x', encoding='utf-8') as stream:
        for topology in manifest['topology']:
            for n in manifest['n_shell']:
                for n_y in sorted({2, 2*n}):
                    for load in manifest['loads']:
                        result = solve(topology, n, 2*n, load, n_y)
                        stream.write(json.dumps(result, sort_keys=True, allow_nan=False)+'\n')
                        stream.flush()
                        count += 1
    digest = hashlib.sha256((args.root/'records.jsonl').read_bytes()).hexdigest()
    result = dict(records=count, records_sha256=digest, root=str(args.root),
                  status='EXPLORATORY_NOT_QUALIFIED')
    (args.root/'result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n',
                                         encoding='utf-8')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
