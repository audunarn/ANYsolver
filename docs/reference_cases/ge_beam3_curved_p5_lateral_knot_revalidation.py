"""Revalidate saved continuum endpoints on explicit coefficient-knot grids.

Preserves original inputs; no base/root solve or discrete computation occurs.
New transfer records are successors, never byte-replacements of old evidence.
"""

import argparse
from pathlib import Path

from docs.reference_cases.ge_beam3_curved_p5_refinement_wave import load,sha,publish,canonical,RefinementError

SOURCES={1:(34293,'3cab47bfb275de3d9af26609f9f1291717420285be1ebb458815b5c7b4d08e20'),
         2:(34291,'fe310ec8836fdd0adb58b8c910a47f111d32ad4097fe6bd9534279323fb6a1da')}


def revalidate(path,stride):
    if type(stride) is not int or stride not in SOURCES: raise ValueError('registered integer stride required')
    data=Path(path).read_bytes();size,digest=SOURCES[stride]
    if len(data)!=size or sha(data)!=digest: raise RefinementError('legacy root byte/hash mismatch')
    legacy=load(path)
    import numpy as np
    from docs.reference_cases import ge_beam3_curved_p5_lateral_knot_diagnostic as knots
    from docs.reference_cases.ge_beam3_curved_p5_arch_reference import ArchReference
    from docs.reference_cases.ge_beam3_curved_p5_arch_lateral_reference import arch_generator,boundary_measure
    result={}
    for side in ('left','right'):
        old=legacy['result'][side];fields=dict(old['reference'])
        for key in ('force','parameter','fields'): fields[key]=np.asarray(fields[key])
        generator=arch_generator(ArchReference(**fields),stride=stride)
        coarse=knots.propagate(generator,np.eye(6))
        fine=knots.propagate(generator,np.eye(6),half_nodes=257)
        error=float(np.linalg.norm(coarse['endpoint']-fine['endpoint']))/max(1.,float(np.linalg.norm(fine['endpoint'])))
        if error>1e-11: raise RefinementError('knot-refinement consistency failed')
        result[side]={'reference':old['reference'],'displacement':old['displacement'],'load':old['load'],
                      'reference_stride':stride,'profile':'KNOT_IVP11_257','transfer':fine['endpoint'],
                      'coarse_transfer':coarse['endpoint'],'refinement_error':error,
                      'callbacks':[coarse['callbacks'],fine['callbacks']],**boundary_measure(fine['endpoint'])}
    if not (result['left']['normalized_determinant']>0>result['right']['normalized_determinant'] and
            0<result['right']['displacement']-result['left']['displacement']<=1e-8):
        raise RefinementError('preserved endpoint bracket not revalidated; no extension')
    return {'schema':'GE_BEAM3_P5_KNOT_RESOLVED_LATERAL_REFERENCE_V1',
            'source_legacy_root':{'bytes':size,'sha256':digest},
            'propagator_sha256':sha(Path(knots.__file__).read_bytes()),
            'revalidator_sha256':sha(Path(__file__).read_bytes()),'result':result,
            'production_qualified':False,'disposition':'NUMERICALLY_REVALIDATED_PRESERVED_ROOT_ENDPOINTS',
            'restriction':'NO_GO_PRODUCTION_RESTRICTION_UNCHANGED'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--stride',required=True,type=int,choices=(1,2));parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();output=args.output.resolve()
    if (output.exists() or output.is_relative_to(args.input.resolve().parent) or
            output.is_relative_to(Path(__file__).resolve().parents[2])):
        raise RefinementError('fresh external successor output required')
    result=revalidate(args.input,args.stride);binding=publish(output,result)
    print(canonical({'output':binding,'endpoints':{s:{k:result['result'][s][k] for k in
        ('displacement','normalized_determinant','refinement_error','callbacks')} for s in ('left','right')}}).decode(),end='')


if __name__=='__main__': main()
