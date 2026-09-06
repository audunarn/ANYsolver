"""Hash-bound comparison of preserved continuum/discrete research modes."""

import argparse
from pathlib import Path

from docs.reference_cases.ge_beam3_curved_p5_refinement_wave import load,sha,canonical,publish,RefinementError


ROOTS={1:(34293,'3cab47bfb275de3d9af26609f9f1291717420285be1ebb458815b5c7b4d08e20'),
       2:(34291,'fe310ec8836fdd0adb58b8c910a47f111d32ad4097fe6bd9534279323fb6a1da')}
INSPECTION=(109306,'252ace01cabf4b11818657436f7d49b669325b9b97b7bfe21faf7c5679495e9f')
SCHEMA='GE_BEAM3_P5_LATERAL_STATIC_SHAPE_COMPARISON_V1'


def bound(path,binding):
    data=Path(path).read_bytes()
    if len(data)!=binding[0] or sha(data)!=binding[1]:
        raise RefinementError('registered mode-input byte/hash mismatch')
    return load(path)


def run(root_folder,inspection_file):
    # All historical inputs are fixed before importing numerical reconstruction.
    roots={stride:bound(Path(root_folder)/f'root-stride-{stride}.json',binding)
           for stride,binding in ROOTS.items()}
    inspected=bound(inspection_file,INSPECTION)
    if [r['step'] for r in inspected['records']]!=list(range(8)):
        raise RefinementError('eight ordered discrete states required')
    import numpy as np
    from docs.reference_cases import ge_beam3_curved_p5_arch_lateral_mode_reference as mode
    from docs.reference_cases.ge_beam3_curved_p5_arch_reference import ArchReference
    shapes={}
    for stride,root in roots.items():
        endpoint=root['result']['left']
        fields=dict(endpoint['reference'])
        for key in ('force','parameter','fields'): fields[key]=np.asarray(fields[key],dtype=float)
        reference=ArchReference(**fields)
        shapes[stride]=mode.shape(reference,endpoint,stride=stride)
    rows=[]
    for row in inspected['records']:
        metrics=mode.compare(shapes[1]['nodal_increment'],row['out_of_plane']['lowest_nodal_increment'],
                             shapes[1]['metric_weights'])
        rows.append({'step':row['step'],'displacement':row['crown_drop'],'load':row['load'],
                     'negative_count':row['out_of_plane']['negative'],
                     'lowest_coordinate_eigenvalue':row['out_of_plane']['values'][0],
                     'comparison':metrics,'source_raw_sha256':row['raw_sha256']})
    repeat=mode.compare(shapes[1]['nodal_increment'],shapes[2]['nodal_increment'],shapes[1]['metric_weights'])
    return {'schema':SCHEMA,'source_roots':{str(k):{'bytes':v[0],'sha256':v[1]} for k,v in ROOTS.items()},
            'source_inspection':{'bytes':INSPECTION[0],'sha256':INSPECTION[1]},
            'mode_reference_sha256':sha(Path(mode.__file__).read_bytes()),
            'comparison_sha256':sha(Path(__file__).read_bytes()),
            'shapes':{str(k):v for k,v in shapes.items()},'interpolation_shape_comparison':repeat,
            'discrete_comparisons':rows,'production_qualified':False,'qualification_gate':False,
            'restriction':'NO_GO_PRODUCTION_RESTRICTION_UNCHANGED',
            'metric':'REFERENCE_ARCLENGTH_TRAPEZOID_SPAN_SCALED_COORDINATES_NOT_MASS_MAC'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root-folder',required=True,type=Path)
    parser.add_argument('--inspection',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();output=args.output.resolve()
    if (output.exists() or output.is_relative_to(args.root_folder.resolve()) or
            output.is_relative_to(args.inspection.resolve().parent) or
            output.is_relative_to(Path(__file__).resolve().parents[2])):
        raise RefinementError('fresh external output outside preserved evidence/worktree required')
    record=run(args.root_folder,args.inspection)
    binding=publish(output,record)
    print(canonical({'output':binding,'last_comparison':record['discrete_comparisons'][-1],
                     'interpolation_shape_comparison':record['interpolation_shape_comparison'],
                     'production_qualified':False}).decode('ascii'),end='')


if __name__=='__main__': main()
