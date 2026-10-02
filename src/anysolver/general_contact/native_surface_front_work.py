"""Conservative work density bound near one contact-producing stationary front.

Caller supplies whole-angle/time proof of one simple stationary H=-A/B, nonzero
B and open captured endpoints. This bounds an integral, never a point history.
"""
import numpy as np
from .native_surface_path import material_path_pose
from .native_surface_support import _base


def open_front_strip_work_bound(field,cell,axial_width,*,segment_index=None):
    if segment_index is None and len(field.segments)!=1:
        raise ValueError('strip work enclosure currently requires one released-origin segment')
    if segment_index is None:segment_index=0
    if type(segment_index) is not int or not 0<=segment_index<len(field.segments):
        raise ValueError('strip work enclosure requires a valid explicit segment index')
    if not np.isfinite(axial_width) or axial_width<=0:
        raise ValueError('positive explicit strip width required')
    # The caller proves all other segments open on this entire strip using
    # their complete branch covers and every captured endpoint. Only this
    # segment then carries work. Its start includes the actual prefix motion,
    # including shell displacement and finite rotations.
    start=field.initial
    for prefix in field.segments[:segment_index]:
        start=material_path_pose(start,prefix.translations,prefix.angular,prefix.shell_increment,1.)
    motion=field.segments[segment_index];target=field.patch.target
    end=material_path_pose(start,motion.translations,motion.angular,motion.shell_increment,1.)
    poses=(start,end);corners=[target.adapter.current_positions(p.shell_displacement) for p in poses]
    velocities=np.asarray(target.adapter.work_map@motion.shell_increment).reshape(3,3)
    edges=[(y[1]-y[0],y[2]-y[0]) for y in corners]
    a,b=edges[0];c,d=edges[1];da,db=velocities[1]-velocities[0],velocities[2]-velocities[0]
    controls=(np.cross(a,b),.5*(np.cross(a,d)+np.cross(c,b)),np.cross(c,d))
    reference=target.adapter.reference_positions
    normal=np.cross(reference[1]-reference[0],reference[2]-reference[0]);normal/=np.linalg.norm(normal)
    coordinate_scale=max(1.,*(float(np.max(np.abs(y))) for y in corners),float(np.max(np.abs(reference))))
    coordinate_error=1024*np.finfo(float).eps*coordinate_scale
    edge_scale=max(np.linalg.norm(e) for pair_edges in edges for e in pair_edges)
    area_error=1024*np.finfo(float).eps*max(1.,edge_scale**2)+8*coordinate_error*edge_scale+16*coordinate_error**2
    area_lower=min(float(normal@v) for v in controls)-area_error
    edge_change=c-a
    # Reverse triangle inequality avoids an ill-conditioned minimizer division.
    edge_lower=max(np.linalg.norm(a),np.linalg.norm(c))-np.linalg.norm(edge_change)-8*coordinate_error
    if area_lower<=0 or edge_lower<=0:raise ValueError('strip full-frame motion unresolved')
    velocity_error=1024*np.finfo(float).eps*max(1.,float(np.max(np.abs(velocities))))
    numerator_error=1024*np.finfo(float).eps*max(1.,edge_scale*(np.linalg.norm(da)+np.linalg.norm(db)))
    numerator_error+=8*(coordinate_error*(np.linalg.norm(da)+np.linalg.norm(db))+velocity_error*edge_scale)
    normal_rate=(max(np.linalg.norm(np.cross(da,e2)+np.cross(e1,db)) for e1,e2 in edges)+numerator_error)/area_lower
    tangent_rate=(np.linalg.norm(da)+4*velocity_error)/edge_lower
    frame_rate=2*(normal_rate+tangent_rate)
    radius=field.patch.rule.definition['radius'];omega=np.linalg.norm(motion.angular[cell])
    xis=(float(cell-1),float(cell))
    chord=max(np.linalg.norm(_base(p,cell,xis[1],ys[0])-_base(p,cell,xis[0],ys[0])) for p,ys in zip(poses,corners))
    relative=max(np.linalg.norm(_base(p,cell,xi,y)) for p,ys in zip(poses,corners) for xi in xis for y in ys)+radius
    speed=max(np.linalg.norm(motion.translations[i]-v) for i in (cell,cell+1) for v in velocities)+omega*radius
    scale=max(1.,relative,speed,chord,frame_rate,*(float(np.max(np.abs(y))) for y in corners))
    padding=1024*np.finfo(float).eps*scale
    penetration=chord*axial_width+padding
    pair=field.patch.pairs[0];pressure=pair.normal_stiffness_Pa_per_m*penetration
    cap=pair.friction_coefficient*pressure;kt=pair.tangential_stiffness_Pa_per_m
    slip=speed+frame_rate*relative+padding
    dissipation=cap*(slip+2*pair.event_history_substeps*cap/kt)
    release=cap*cap/(2*kt)
    result=np.array((0.,dissipation,release,dissipation))
    if not np.all(np.isfinite(result)):raise ValueError('nonfinite strip work enclosure')
    return result
