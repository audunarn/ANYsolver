"""Read-only discrete recovery audit; no production or continuum solver import.

Reconstruct work maps from the saved candidate equations, not from native
assembly. Independent algorithm, same authorship; not a qualification checker.
"""
import argparse
from hashlib import sha256
from math import fsum
from pathlib import Path
import numpy as np
from docs.reference_cases.ge_beam3_preserved_arch_load_comparison import canonical,parse

RESULT_SHA='8e128fc1bcefbbbf06735ff40894b1afc41fcc00b70d8674dca436d34f016b43'
ROOT=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-curved-moment-20260907-v1')


def skew(v):
    x,y,z=v
    return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def rotation_log_jacobian(q):
    q=np.asarray(q,dtype=float)
    if (q.shape!=(3,3) or not np.isfinite(q).all() or np.max(abs(q.T@q-np.eye(3)))>1e-11
            or abs(np.linalg.det(q)-1)>1e-11): raise ValueError('proper endpoint relative rotation required')
    axial=np.array([q[2,1]-q[1,2],q[0,2]-q[2,0],q[1,0]-q[0,1]])/2
    sine=float(np.linalg.norm(axial)); cosine=float((np.trace(q)-1)/2)
    angle=float(np.arctan2(sine,cosine))
    if angle>=.9*np.pi: raise ValueError('endpoint principal chart exceeded')
    ell=axial*(1+angle**2/6+7*angle**4/360 if angle<1e-5 else angle/sine)
    cross=skew(ell)
    coefficient=1/12+angle**2/720+angle**4/30240 if angle<1e-3 else (1-angle/(2*np.tan(angle/2)))/angle**2
    return ell,np.eye(3)-.5*cross+coefficient*(cross@cross)


def pair(row,key):
    return np.array([fsum((a,b)) for a,b in zip(row[key],row[key+'_low'])])


def best_constant_rotation(reference_frames,current_frames,weights):
    """Weighted SO(3) Procrustes lower bound, diagnostic only; never recovery."""
    r=np.asarray(reference_frames); q=np.asarray(current_frames); w=np.asarray(weights)
    if (r.shape!=q.shape or r.ndim!=3 or r.shape[1:]!=(3,3) or w.shape!=(len(r),)
            or not np.isfinite(r).all() or not np.isfinite(q).all() or not np.isfinite(w).all() or np.min(w)<=0):
        raise ValueError('complete finite weighted frames')
    cross=np.einsum('n,nij,nkj->ik',w,q,r)
    left,_,right=np.linalg.svd(cross)
    diagonal=np.eye(3); diagonal[-1,-1]=np.linalg.det(left@right)
    return left@diagonal@right


def inspect_record(macros,packet,rec,reference):
    """Check cell force, moment and curvature work, and assembled nodal work."""
    target=rec['target']; row=packet['records'][(.25,.5,1.).index(target)]
    mechanical=row['mechanical']; initial=packet['initial']['mechanical']
    x=np.asarray(mechanical['positions'])+np.asarray(mechanical['position_low'])
    q=np.asarray(mechanical['nodal_frames']); r0=np.asarray(initial['nodal_frames'])
    vertex=np.zeros((2*macros+1,6)); cells=[]
    parameters=np.asarray(reference['parameter']); reference_q=np.asarray(reference['frames'])
    for eid,element in enumerate(rec['fields']):
        p=np.asarray(mechanical['resultants'][eid]); rotations=np.asarray(mechanical['cell_rotations'][eid])
        for cell in (0,1):
            left=2*eid+cell; right=left+1; u=rotations[cell]
            a=p[3*cell:3*cell+3]; m=p[6+6*cell:12+6*cell].reshape(2,3)
            force=u@a; vertex[left,:3]-=force; vertex[right,:3]+=force
            endpoint=[]; ell=[]
            for node,sign,end_m in ((left,-1,m[0]),(right,1,m[1])):
                a_frame=u@r0[node]; angle,jinv=rotation_log_jacobian(a_frame.T@q[node])
                spatial=sign*a_frame@jinv.T@end_m
                vertex[node,3:]+=spatial; endpoint.append(spatial); ell.append(sign*angle)
            cell_residual=-np.cross(x[right]-x[left],force)-sum(endpoint)
            saved_cell=np.asarray(row['residual'])[6*(2*macros+1)+24*eid+3*cell:6*(2*macros+1)+24*eid+3*cell+3]
            force_integral=np.zeros(3); curvature=np.zeros((2,3)); moment_error=[]; frame_error=[]
            weights=[]; reference_frames=[]; expected_frames=[]; actual_frames=[]
            for station in element['stations']:
                if station['cell']!=cell: continue
                t=station['xi']-cell+1; measure=station['measure']
                # Local xi spans each macro; global t spans [-1,1].
                global_t=-1+(2*eid+station['xi']+1)/macros
                hits=np.flatnonzero(parameters==global_t)
                if len(hits)!=1:
                    # Reuse the exactly captured reference-position samples;
                    # arithmetic evaluation order must not invent interpolation.
                    location=rec['locations'][station['cell']*4+station['station']+eid*8]
                    hits=np.flatnonzero(parameters==location)
                if len(hits)!=1: raise ValueError('explicit continuum station absent')
                jacobian=np.sqrt(1+(.3*float(parameters[hits[0]]))**2)/macros
                frame=np.asarray(station['current_frame']); ref=np.asarray(station['reference_frame'])
                n=pair(station,'resultants'); strain=pair(station,'strain')
                force_integral+=measure/jacobian*(frame@n[:3])
                curvature+=measure*np.outer([1-t,t],strain[3:])
                moment_error.append(float(np.max(abs(n[3:]-np.array([1-t,t])@m))))
                frame_error.append(float(np.max(abs(frame-u@ref))))
                weights.append(measure); reference_frames.append(ref)
                expected_frames.append(reference_q[hits[0]]); actual_frames.append(frame)
            if len(weights)!=4: raise ValueError('four stations per cell required')
            optimal=best_constant_rotation(reference_frames,expected_frames,weights)
            def error(frames):
                return float(np.sqrt(np.sum(np.asarray(weights)[:,None,None]*(np.asarray(frames)-expected_frames)**2)/sum(weights)))
            native_error=error(actual_frames); floor=error(optimal@np.asarray(reference_frames))
            if native_error+1e-12<floor: raise ValueError('optimal projection bound violated')
            values=dict(element=eid+1,cell=cell,
                saved_frame_map_error=max(frame_error),
                station_moment_interpolation_error=max(moment_error),
                force_work_map_error=float(np.max(abs(force_integral-force))),
                curvature_endpoint_work_error=float(np.max(abs(curvature-np.asarray(ell)))),
                internal_cell_rotation_residual_error=float(np.max(abs(cell_residual-saved_cell))),
                native_frame_weighted_rms=native_error,best_constant_frame_weighted_rms=floor,
                native_to_best_rotation_norm=float(np.linalg.norm(u-optimal)),
                spatial_cell_force_norm=float(np.linalg.norm(force)))
            if max(values[k] for k in ('saved_frame_map_error','station_moment_interpolation_error',
                    'force_work_map_error','curvature_endpoint_work_error','internal_cell_rotation_residual_error'))>1e-11:
                raise ValueError('discrete recovered field/work identity failed')
            cells.append(values)
    vertex[-1,3:]-=np.asarray(reference['moment'])
    nodal_error=float(np.max(abs(vertex-np.asarray(row['residual'][:6*(2*macros+1)]).reshape(-1,6))))
    if nodal_error>1e-11: raise ValueError('independent nodal residual reconstruction failed')
    return dict(macros=macros,target=target,nodal_residual_reconstruction_error=nodal_error,cells=cells)


def build(root=ROOT):
    raw=(root/'comparison.json').read_bytes()
    if sha256(raw).hexdigest()!=RESULT_SHA: raise ValueError('frozen comparison hash')
    summary=parse(raw); packets={}
    for item in summary['artifacts']:
        data=(root/item['path']).read_bytes()
        if len(data)!=item['bytes'] or sha256(data).hexdigest()!=item['sha256']: raise ValueError('frozen artifact hash')
        packets[item['path']]=parse(data)
    detail=packets['fields-diagnostic.json']; rows=[]
    refs={(r['target'],r['value']['profile']):r['value'] for r in detail['references']}
    for rec in detail['recoveries']:
        rows.append(inspect_record(rec['macros'],packets[f"checkpoint-{rec['macros']}.json"],rec,refs[rec['target'],'IVP13']))
    return dict(schema='GE_BEAM3_DISCRETE_RECOVERY_WORK_AUDIT_V1',input_sha256=RESULT_SHA,rows=rows,
        status='DISCRETE_IDENTITIES_CHECKED_NOT_QUALIFICATION',production_qualified=False,independent_review='PENDING',
        native_solves=0,reference_solves=0,smoothing_applied=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); raw=canonical(build())
    with args.output.open('xb') as stream: stream.write(raw)


if __name__=='__main__': main()
