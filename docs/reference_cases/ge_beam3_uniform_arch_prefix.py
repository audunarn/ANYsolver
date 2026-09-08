"""Replay a failed smoke's preserved accepted prefix; do not advance its path."""
import argparse
from hashlib import sha256
from pathlib import Path
import sys
import numpy as np


def inspect(checkpoint,expected_sha256):
    if type(checkpoint) is not bytes or sha256(checkpoint).hexdigest()!=expected_sha256:
        raise ValueError('explicit preserved checkpoint hash required before mechanics')
    root=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(root/'src'))
    import anysolver
    if Path(anysolver.__file__).resolve()!=root/'src'/'anysolver'/'__init__.py':
        raise ValueError('prefix replay must use this source checkout')
    from anysolver._ge_beam3_native_arc_restart import decode_checkpoint
    from anysolver._ge_beam3_native_arc import replay_direction,capture
    from docs.reference_cases.ge_beam3_uniform_arch_reference import solve
    sys.path.insert(0,str(root/'tests'))
    from test_ge_beam3_native_uniform_arch import make
    model,program=make();chain,records=decode_checkpoint(model,program,checkpoint,expected_sha256=expected_sha256)
    if len(records)!=3:raise ValueError('exact preserved three-step prefix required')
    rows=[];reference=None
    for state,record in zip(chain[1:],records):
        u=state['displacements'].reshape(5,6);drop=float(-u[2,1]);reference=solve(drop,previous=reference,profile='BVP9')
        tangent=replay_direction(model,program,state,record['parameter'],record['direction'])
        crown_direction=float(-tangent[13])
        if abs(crown_direction)<=1e-12:raise ValueError('unresolved crown path derivative')
        zero=all(not any(sum(v) for v in h.plastic) and sum(h.accumulated)==0.
            for s in state['states'].values() for h in s['response'].history.stations)
        if not zero:raise ValueError('elastic reference cannot qualify plastic history')
        rows.append(dict(step=record['index'],drop=drop,density=record['parameter'],reference_density=reference.density,
            relative_load_error=abs(record['parameter']/reference.density-1),native_load_slope=float(tangent[-1]/crown_direction),
            reference_load_slope=reference.slope,crown_direction=crown_direction,parameter_direction=float(tangent[-1]),
            reflection_error=float(max(np.max(np.abs(u[:,0]+u[::-1,0])),np.max(np.abs(u[:,1]-u[::-1,1])),np.max(np.abs(u[:,2])))),
            zero_plastic_history=True,reference_diagnostics=reference.diagnostics))
    return dict(schema='GE_BEAM3_UNIFORM_ARCH_PRESERVED_PREFIX_DIAGNOSTIC_V1',checkpoint_sha256=expected_sha256,
        rows=rows,accepted_prefix_replayed=True,path_advanced=False,failed_smoke_reclassified=False,
        production_qualified=False,full_spatial_stability=False,independent_review='PENDING')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--sha256',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    raw=args.checkpoint.read_bytes();value=inspect(raw,args.sha256)
    from docs.reference_cases.ge_beam3_preserved_arch_load_comparison import canonical,parse
    encoded=canonical(value);parse(encoded)
    if args.checkpoint.read_bytes()!=raw:raise ValueError('preserved checkpoint changed')
    args.output.parent.mkdir(parents=True,exist_ok=False)
    with args.output.open('xb') as stream:stream.write(encoded)
    print(encoded.decode(),end='')


if __name__=='__main__':main()
