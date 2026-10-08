"""Independent complete Hermite path certificate and unsafe hidden-motion controls."""
import json,os
from pathlib import Path
from fractions import Fraction as F
import numpy as np
from examples.general_contact_beam_s3_loaded_path_reference import geometry_controls,certify,enclosure,RADIUS,MAX_VISITED,GAP_GATE,RIM,subtract_lower,lo
from examples.general_contact_beam_s3_transient_directional_loaded_impact import run,DT,END

def test_loaded_complete_paths_and_hidden_crossing(tmp_path):
    import math
    # Retained severe-cancellation counterexample to one final nextafter.
    A=1.;radius_upper=math.nextafter(1/128,math.inf);movement=.9921875
    exact=F(A)-F(radius_upper)-F(movement)
    old=lo(A-radius_upper-movement-0.)
    staged=subtract_lower(A,radius_upper,movement,0.)
    cancellation=dict(exact_numerator=exact.numerator,exact_denominator=exact.denominator,exact_float=float(exact),old_bound=old,staged_bound=staged)
    assert F(old)>exact and F(staged)<=exact
    rows=[]
    path=Path(os.environ.get('CONTACT_APP_RESULT_RECORD',str(tmp_path/'path_result.json')))
    trajectory_files=[]
    for dt in (DT,DT/2):
        model,result,_=run(dt=dt,end=END);segments=[]
        import hashlib
        trajectory_path=path.with_name('coarse_trajectory.npz' if dt==DT else 'fine_trajectory.npz')
        np.savez(trajectory_path,times=result.times,displacements=result.displacements,velocities=result.velocities,nominal_dt=np.array(dt))
        trajectory_files.append(dict(path=str(trajectory_path),sha256=hashlib.sha256(trajectory_path.read_bytes()).hexdigest()))
        assert result.cutbacks==0
        for i in range(len(result.times)-1):
            # This profile uses nominal dt (including operand-scale endpoint matching).
            control=geometry_controls(model,result.displacements[i],result.displacements[i+1],result.velocities[i],result.velocities[i+1],dt)
            segments.append(certify(control))
        rows.append(dict(dt=dt,states=len(result.times),segments=len(segments),all_certified=all(x['certified'] for x in segments),visited=sum(x['visited'] for x in segments),certificates=segments))
    # All four tensor-domain boundaries safe; only middle time/space controls bow.
    base=np.array([[F(0),F(0),RADIUS+F(1,128)+F(1,2**20)],[F(1,4),F(0),RADIUS+F(1,128)+F(1,2**20)],[F(1,2),F(0),RADIUS+F(1,128)+F(1,2**20)],[F(-1),F(-1),F(1,128)],[F(3),F(-1),F(1,128)],[F(-1),F(3),F(1,128)]],object)
    control=np.array([base.copy() for _ in range(4)],object)
    for k in (1,2):control[k,1,2]-=F(1,2**13)
    endpoint0=certify(np.array([control[0]]*4,object));endpoint1=certify(np.array([control[3]]*4,object));hidden=certify(control)
    midpoint_gap=F(1,2**20)-F(3,8)*F(1,2**13)
    spatial_boundaries=[]
    for side in (0,2):
        boundary=control.copy()
        for k in range(4):boundary[k,:3]=control[k,side]
        spatial_boundaries.append(certify(boundary))
    # Changing face controls can collapse/reverse orientation with safe endpoints.
    collapse=np.array([base.copy() for _ in range(4)],object)
    collapse[1,4,0]=F(-5);collapse[2,4,0]=F(-5)
    orientation=certify(collapse,budget=64)
    midpoint_target=(collapse[0,3:]+3*collapse[1,3:]+3*collapse[2,3:]+collapse[3,3:])/8
    midpoint_C=np.cross(midpoint_target[1]-midpoint_target[0],midpoint_target[2]-midpoint_target[0])
    reversed_face=np.array([base.copy() for _ in range(4)],object)
    reversed_face[:,4:6]=reversed_face[:,[5,4]]
    direct_orientation=enclosure(reversed_face)
    degenerate=np.array([base.copy() for _ in range(4)],object)
    degenerate[:,4]=degenerate[:,3]
    direct_degeneracy=enclosure(degenerate)
    exhausted=certify(control,budget=1)
    path=Path(os.environ.get('CONTACT_APP_RESULT_RECORD',str(tmp_path/'path_result.json')))
    path.write_text(json.dumps(dict(gap_gate_m=GAP_GATE,rim_m=RIM,arithmetic='EXACT_BINARY_ENDPOINT_CONTROL_CONSTRUCTION_DIRECTED_INTERVAL_HULLS',scope='REPRESENTED_HERMITE_NOT_DAE_LIFT',rows=rows,cancellation_regression=cancellation,trajectory_files=trajectory_files,spatial_boundaries_safe=spatial_boundaries,endpoint_safe=[endpoint0,endpoint1],hidden_crossing=hidden,exact_midpoint_gap_m=float(midpoint_gap),target_orientation=orientation,exact_target_midpoint_oriented_cross=float(midpoint_C[2]),direct_reversed_orientation=direct_orientation,direct_degeneracy=direct_degeneracy,budget_refusal=exhausted),indent=2))
    assert all(x['all_certified'] for x in rows)
    assert endpoint0['certified'] and endpoint1['certified'] and all(x['certified'] for x in spatial_boundaries) and midpoint_gap<-F(float(GAP_GATE)) and not hidden['certified']
    assert midpoint_C[2]<0 and not orientation['certified'] and not exhausted['certified']

    assert not direct_orientation['resolved'] and direct_orientation['reason']=='normal/orientation unresolved'
    assert not direct_degeneracy['resolved'] and direct_degeneracy['reason']=='anchor degeneracy'
