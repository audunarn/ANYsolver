"""Postprocess frozen arch tangents; no assembly, continuation or mechanics import.

This reports numerical inertia of sampled conservative tangents, not natural
frequencies, exact rank or a continuum buckling certificate. Reflection uses
polar translations and axial spatial rotation increments. No negative mode is
deleted. The nonlinear proof input is immutable and hash-checked before NumPy.
"""

import argparse
from pathlib import Path
import time

from docs.reference_cases.ge_beam3_curved_p5_arch_refinement_wave import (
    canonical,sha,load,publish,inspect_worker,RefinementError,
)


SCHEMA='GE_BEAM3_P5_ARCH_SAMPLED_SPATIAL_INERTIA_V1'
AGGREGATE_SHA='a53d7baa8ad6a21ca892dba2f10968458171ce8a87da6770a418545477f1bc8e'
WORKER_SHA='49e71f90d144963d8739918e5851d35a81d78579d93db2c877b7681461d2c182'
FROZEN_COMMIT='cc8f4b7ddea2deee6b29c9446a9b6269ef9b8d1b'
FROZEN_TREE='55afb09201ad7dc130fb5fa46c88be130d4057ef'
LIMIT=1e-11


def snapshot(root):
    """Fail closed on different/rehashed scientific inputs before numerics."""
    root=Path(root)
    for path,size,digest in ((root/'aggregate.json',924,AGGREGATE_SHA),
                             (root/'arch16/complete.json',6499,WORKER_SHA)):
        data=path.read_bytes()
        if len(data)!=size or sha(data)!=digest:
            raise RefinementError('registered arch input hash mismatch')
    aggregate=load(root/'aggregate.json')
    authority=aggregate['authority']
    if authority['commit']!=FROZEN_COMMIT or authority['tree']!=FROZEN_TREE:
        raise RefinementError('registered arch source identity mismatch')
    packet=inspect_worker(root/'arch16',authority,aggregate['request_id'],aggregate['request_sha256'])
    return [(row,load(root/'arch16'/row['raw']['name'])) for row in packet['records']]


def spectral(matrix, *, extent='REFINEMENT16'):
    """Backward-error diagnostics; uncertainty band is not a rigorous interval."""
    import numpy as np
    if extent not in ('REFINEMENT16','ARCH_ONSET32'):
        raise RefinementError('registered spectral extent required')
    maximum=378 if extent=='ARCH_ONSET32' else 186
    a=np.asarray(matrix,dtype=float)
    if a.ndim!=2 or a.shape[0]!=a.shape[1] or not 1<=len(a)<=maximum or not np.isfinite(a).all():
        raise RefinementError('bounded finite square tangent required')
    norm=max(1.,float(np.linalg.norm(a)))
    symmetry=float(np.linalg.norm(a-a.T))/norm
    if symmetry>LIMIT:
        raise RefinementError('conservative symmetry failure')
    # Do not symmetrize the input to hide a failure. eigh uses its lower triangle;
    # residual and reconstruction below are checked against the complete input.
    values,vectors=np.linalg.eigh(a)
    residual=float(np.linalg.norm(a@vectors-vectors*values))
    orthogonality=float(np.linalg.norm(vectors.T@vectors-np.eye(len(a))))
    reconstruction=float(np.linalg.norm(a-(vectors*values)@vectors.T))/norm
    if max(residual/norm,orthogonality,reconstruction)>LIMIT:
        raise RefinementError('eigensystem reconstruction failure')
    uncertainty=residual+norm*orthogonality+64*np.finfo(float).eps*len(a)*norm
    lowest=vectors[:,0].copy()
    if lowest[np.argmax(np.abs(lowest))]<0: lowest=-lowest
    return {'values':values,'lowest_vector':lowest,'uncertainty_band':float(uncertainty),
            'positive':int(np.count_nonzero(values>uncertainty)),
            'negative':int(np.count_nonzero(values < -uncertainty)),
            'unresolved':int(np.count_nonzero(np.abs(values)<=uncertainty)),
            'symmetry_error':symmetry,'eigen_residual':residual/norm,
            'orthogonality_error':orthogonality,'reconstruction_error':reconstruction}


def classify_matrix(matrix,*,nodes,span=2.,extent='REFINEMENT16'):
    """Clamped end nodes; only reflection-invariant planar conservative states.

    For S=diag(1,1,-1), delta r transforms with S but spatial delta theta
    transforms with det(S)S. Even DOFs: ux,uy,rz; odd: uz,rx,ry. Rotations are
    scaled by reference span using a positive congruence, not an invented mass.
    """
    import numpy as np
    if extent not in ('REFINEMENT16','ARCH_ONSET32'):
        raise RefinementError('registered nodal spectral extent required')
    maximum=65 if extent=='ARCH_ONSET32' else 33
    if type(nodes) is not int or not 3<=nodes<=maximum or not np.isfinite(span) or span<=0:
        raise RefinementError('bounded clamped node count and positive span required')
    matrix=np.asarray(matrix,dtype=float)
    if matrix.shape!=(6*nodes,6*nodes) or not np.isfinite(matrix).all():
        raise RefinementError('complete finite nodal tangent required')
    free=np.arange(6,6*(nodes-1))
    scale=np.tile([1.,1.,1.,span,span,span],nodes-2)
    a=matrix[np.ix_(free,free)]/np.outer(scale,scale)
    signs=np.tile([1,1,-1,-1,-1,1],nodes-2)
    even=np.flatnonzero(signs==1);odd=np.flatnonzero(signs==-1)
    norm=max(1.,float(np.linalg.norm(a)))
    reflection=float(np.linalg.norm(a-signs[:,None]*a*signs[None,:]))/norm
    if reflection>LIMIT:
        raise RefinementError('planar reflection coupling failure')
    full=spectral(a,extent=extent);in_plane=spectral(a[np.ix_(even,even)],extent=extent);out_of_plane=spectral(a[np.ix_(odd,odd)],extent=extent)
    union=np.sort(np.concatenate((in_plane['values'],out_of_plane['values'])))
    union_error=float(np.linalg.norm(union-full['values']))/norm
    if union_error>LIMIT:
        raise RefinementError('reflection spectra do not recover full tangent')
    # A small nonzero cross-block cannot be ignored merely because it passed a
    # normalized gate: include its absolute norm in block sign uncertainty.
    coupling=float(np.linalg.norm(a[np.ix_(even,odd)]))
    for block in (in_plane,out_of_plane):
        band=block['uncertainty_band']+coupling
        block.update(uncertainty_band=band,positive=int(np.count_nonzero(block['values']>band)),
                     negative=int(np.count_nonzero(block['values'] < -band)),
                     unresolved=int(np.count_nonzero(np.abs(block['values'])<=band)))
    for block,indices in ((in_plane,even),(out_of_plane,odd)):
        mode=np.zeros(6*nodes)
        mode[free[indices]]=block.pop('lowest_vector')/scale[indices]
        block['lowest_nodal_increment']=mode.reshape(nodes,6)
    full.pop('lowest_vector')
    return {'free_dimension':len(free),'in_plane_dimension':len(even),'out_of_plane_dimension':len(odd),
            'reflection_error':reflection,'coupling_norm':coupling,'spectral_union_error':union_error,
            'coordinate_scale_span':span,'full':full,'in_plane':in_plane,'out_of_plane':out_of_plane}


def inspect_state(row,raw):
    import numpy as np
    trial=raw['trial']['assembly_trial'];x=np.asarray(trial['positions']);q=np.asarray(trial['rotations'])
    response=trial['response'];r=np.asarray(response['residual']).reshape(33,6)
    force=np.asarray(trial['forces']);expected_force=np.zeros((33,3));expected_force[16,1]=-row['load']
    if x.shape!=(33,3) or q.shape!=(33,3,3) or not np.isfinite(x).all() or not np.isfinite(q).all():
        raise RefinementError('finite registered state required')
    s=np.diag([1.,1.,-1.])
    residual=r.copy();residual[:,:3]-=force
    errors={'position_planarity':float(np.max(np.abs(x[:,2]))),
            'rotation_planarity':float(np.max(np.abs(q-s@q@s))),
            'rotation_orthogonality':float(np.max(np.abs(q.transpose(0,2,1)@q-np.eye(3)))),
            'rotation_determinant':float(np.max(np.abs(np.linalg.det(q)-1))),
            'fixed_positions':float(np.max(np.abs(x[[0,32]]-[[-1.,0.,0.],[1.,0.,0.]]))),
            'fixed_rotations':float(np.max(np.abs(q[[0,32]]-np.eye(3)))),
            'free_equilibrium':float(np.max(np.abs(residual[1:32]))),
            'load_pattern':float(np.max(np.abs(force-expected_force)))}
    if any(not np.isfinite(v) or v>LIMIT for v in errors.values()):
        raise RefinementError('planar dead-load equilibrium/constraint mismatch')
    result=classify_matrix(response['tangent'],nodes=33)
    result.update(step=row['step'],crown_drop=row['crown_drop'],load=row['load'],
                  current_load_slope=row['current_load_slope'],state_errors=errors,
                  raw_sha256=row['raw']['sha256'])
    return result


def summarize(records):
    if len(records)!=8 or [r['step'] for r in records]!=list(range(8)):
        raise RefinementError('eight ordered sampled states required')
    def first(kind):
        return next((r['step'] for r in records if r[kind]['negative']),None)
    uncertain=any(r[k]['unresolved'] for r in records for k in ('full','in_plane','out_of_plane'))
    lateral=first('out_of_plane');planar=first('in_plane')
    return {'first_in_plane_negative_step':planar,'first_out_of_plane_negative_step':lateral,
            'disposition':'UNRESOLVED_SAMPLED_NUMERICAL_INERTIA' if uncertain else
              ('SAMPLED_OUT_OF_PLANE_INSTABILITY_PRESENT' if lateral is not None else
               'NO_NEGATIVE_OUT_OF_PLANE_MODE_AT_SAMPLED_STATES'),
            'production_qualified':False,'restriction':'NO_GO_PRODUCTION_RESTRICTION_UNCHANGED',
            'continuum_buckling_qualified':False,'natural_frequencies_computed':False}


def inspect(root,*,max_seconds=30.):
    start=time.monotonic()
    def deadline():
        if not 0<max_seconds<=30 or time.monotonic()-start>=max_seconds:
            raise RefinementError('bounded inspection deadline')
    deadline();inputs=snapshot(root);deadline()
    records=[]
    for row,raw in inputs:
        deadline();records.append(inspect_state(row,raw));deadline()
    return {'schema':SCHEMA,'source_aggregate_sha256':AGGREGATE_SHA,'source_worker_sha256':WORKER_SHA,
            'source_commit':FROZEN_COMMIT,'source_tree':FROZEN_TREE,
            'inspector_sha256':sha(Path(__file__).read_bytes()),
            'summary':summarize(records),'records':records}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    # Validate path before inspection; never write into the saved proof tree.
    output=args.output.resolve();root=args.input.resolve()
    if output.exists() or output.is_relative_to(root) or output.is_relative_to(Path(__file__).resolve().parents[2]):
        raise RefinementError('fresh external inspection output required')
    result=inspect(root)
    binding=publish(output,result)
    print(canonical({'output':binding,'summary':result['summary']}).decode('ascii'),end='')


if __name__=='__main__': main()
