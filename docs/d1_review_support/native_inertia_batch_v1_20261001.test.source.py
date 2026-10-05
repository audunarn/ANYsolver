"""One bounded complete-kernel comparison; no native trajectory or dispatch."""
from dataclasses import asdict
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
from time import perf_counter
import traceback
import numpy as np
import pytest

from anysolver._ge_beam3_centered_batched_finite_inertia import evaluate_batched_finite_inertia as batch
from anysolver._ge_beam3_centered_finite_inertia import _CenteredFiniteKernel, _mixed, PHYSICAL_DOFS, ALGEBRAIC_DOFS
from anysolver._ge_beam3_p5.algebra import rotation
from anysolver._ge_beam3_p5_seeded.core import canonical
from test_ge_beam3_centered_finite_inertia import fixture


def scaled_difference(actual, expected):
    expected = np.asarray(expected)
    norm = float(np.linalg.norm(expected))
    if norm == 0.:
        assert np.count_nonzero(actual) == 0
        return 0.
    return float(np.linalg.norm(np.asarray(actual)-expected)/norm)


def independent_station_virtual_work(kernel, positions, cells, velocity, acceleration, virtual):
    """Literal spatial/body balance, contracted BEFORE generalized assembly."""
    total = 0.
    for cell, left, right, t, frame, offset, weight in kernel._stations:
        r = cells[cell]@frame
        d = cells[cell]@offset
        omega = velocity[18+3*cell:21+3*cell]
        alpha = acceleration[18+3*cell:21+3*cell]
        linear_v = (1-t)*velocity[6*left:6*left+3]+t*velocity[6*right:6*right+3]+np.cross(omega,d)
        linear_a = ((1-t)*acceleration[6*left:6*left+3]+t*acceleration[6*right:6*right+3]
            +np.cross(alpha,d)+np.cross(omega,np.cross(omega,d)))
        u, w = r.T@linear_v, r.T@omega
        du, dw = r.T@(linear_a-np.cross(omega,linear_v)), r.T@alpha
        p, h = np.split(kernel.section_mass@np.concatenate((u,w)),2)
        fp, hp = np.split(kernel.section_mass@np.concatenate((du,dw)),2)
        f = r@(fp+np.cross(w,p))
        n = r@(hp+np.cross(w,h)+np.cross(u,p))
        virtual_w = virtual[18+3*cell:21+3*cell]
        virtual_v = ((1-t)*virtual[6*left:6*left+3]+t*virtual[6*right:6*right+3]
            +np.cross(virtual_w,d))
        total += weight*(virtual_v@f+virtual_w@n)
    return float(total)


def test_complete_prepared_kernel_batch(record_property):
    spec = json.loads(Path(os.environ['NATIVE_INERTIA_BATCH_INPUTS']).read_bytes())
    output = Path(spec['raw_output'])
    assert not output.exists()
    for path, expected in spec['source_sha256'].items():
        assert sha256(Path(path).read_bytes()).hexdigest() == expected, path
    for key, expected in spec['environment'].items():
        assert os.environ.get(key) == expected,key
    assert Path(inspect.getsourcefile(batch)).resolve() == Path(spec['candidate_module']).resolve()
    started = perf_counter()
    evidence = dict(status='RUNNING',cases=[],directional=[],timings=[],criteria=spec['criteria'],
        actual_candidate_file=inspect.getsourcefile(batch),effective_environment=spec['environment'])
    def save(stage):
        evidence['last_stage'] = stage
        evidence['elapsed_seconds'] = perf_counter()-started
        output.write_bytes(canonical(evidence))
        print(json.dumps(dict(stage=stage,elapsed_seconds=evidence['elapsed_seconds'])),flush=True)
    try:
        data = fixture()  # Authentic existing geometry/section helper, no old tests.
        ref, section, positions, _, cells, velocity, acceleration = data
        kernel = _CenteredFiniteKernel(ref,section,order=24)
        assert np.linalg.norm(section[:3,3:]) > 0.
        evidence['prepared_inputs'] = dict(section_mass=kernel.section_mass.tolist(),
            stations=[dict(cell=c,left=l,right=r,t=t,frame=f.tolist(),offset=d.tolist(),measure=w)
                for c,l,r,t,f,d,w in kernel._stations])
        shift = np.array(((.012,-.007,.004),(-.008,.013,-.006),(.004,-.009,.011)))
        fast_cells = np.array((rotation((.38,-.2,.31)),rotation((-.29,.41,-.14))))
        fast_v = np.zeros(24)
        omega = np.array((35.,-25.,20.))
        for node,point in enumerate(positions+shift): fast_v[6*node:6*node+3]=np.cross(omega,point)
        fast_v[18:21] = fast_v[21:24] = omega
        rigid_v = np.zeros(24)
        for node in range(3): rigid_v[6*node:6*node+3] = (.31,-.2,.5)
        cases = (
            ('rest',positions,np.array((np.eye(3),np.eye(3))),np.zeros(24),np.zeros(24)),
            ('finite_off_axis',positions+shift,cells,velocity,acceleration),
            ('fast_finite_off_axis',positions+shift,fast_cells,fast_v,np.linspace(-120.,150.,24)),
            ('finite_attitude_translation',positions,fast_cells,rigid_v,np.zeros(24)))
        for name,x,r,v,a in cases:
            old = kernel.evaluate(x,r,v,a)
            new = batch(kernel.section_mass,kernel._stations,x,r,v,a)
            errors = {key:scaled_difference(value,asdict(old)[key]) for key,value in asdict(new).items()}
            row = dict(name=name,positions=x.tolist(),cells=r.tolist(),velocity=v.tolist(),acceleration=a.tolist(),
                old=json.loads(canonical(old)),new=json.loads(canonical(new)),scaled_errors=errors,gate_status='UNASSESSED')
            evidence['cases'].append(row); save(name+'_before_gates')
            assert max(errors.values()) <= spec['criteria']['parity_limit']
            for value in vars(new).values():
                if isinstance(value,np.ndarray):
                    assert not value.flags.writeable
                    with pytest.raises(ValueError): value.flat[0]=1.
            for key in ('mass','generalized_momentum','inertia','velocity_derivative','configuration_derivative'):
                extended = _mixed(getattr(new,key))
                assert np.count_nonzero(extended[list(ALGEBRAIC_DOFS)]) == 0
                if extended.ndim==2: assert np.count_nonzero(extended[:,list(ALGEBRAIC_DOFS)]) == 0
            assert scaled_difference(new.generalized_momentum,new.mass@v) <= 1e-13
            assert scaled_difference(new.kinetic_energy,.5*v@new.mass@v) <= 1e-13
            row['gate_status']='PASS'; save(name+'_pass')
        _,x,r,v,a=cases[2]
        base=batch(kernel.section_mass,kernel._stations,x,r,v,a)
        direction=np.sin(np.arange(24)+.4);direction/=np.linalg.norm(direction)
        eta=np.array(((.3,-.2,.4),(-.25,.35,.15)))
        virtual=direction.copy()
        reference_work=independent_station_virtual_work(kernel,x,r,v,a,virtual)
        work=float(virtual@base.inertia)
        evidence['virtual_work']=dict(generalized=work,independent_station=reference_work,
            relative_error=abs(work-reference_work)/max(abs(reference_work),1e-30))
        save('virtual_work_before_gate')
        assert evidence['virtual_work']['relative_error'] <= 1e-13
        for h in spec['criteria']['directional_intervals']:
            plus=batch(kernel.section_mass,kernel._stations,x,r,v+h*direction,a)
            minus=batch(kernel.section_mass,kernel._stations,x,r,v-h*direction,a)
            fd=(plus.inertia-minus.inertia)/(2*h)
            velocity_error=scaled_difference(fd,base.velocity_derivative@direction)
            plus_r=np.array([rotation(h*e)@u for e,u in zip(eta,r)])
            minus_r=np.array([rotation(-h*e)@u for e,u in zip(eta,r)])
            plus=batch(kernel.section_mass,kernel._stations,x,plus_r,v,a)
            minus=batch(kernel.section_mass,kernel._stations,x,minus_r,v,a)
            fd=(plus.inertia-minus.inertia)/(2*h)
            expected=base.configuration_derivative[:,18:24]@eta.flatten()
            configuration_error=scaled_difference(fd,expected)
            evidence['directional'].append(dict(interval=h,velocity_error=velocity_error,
                configuration_error=configuration_error,configuration_signal_norm=float(np.linalg.norm(expected))))
            save('directional_before_gate')
            assert max(velocity_error,configuration_error) <= spec['criteria']['directional_limit']
        invalid=[]
        bad_station=list(kernel._stations)
        bad=list(bad_station[0]);bad[-1]=-bad[-1];bad_station[0]=tuple(bad)
        with pytest.raises(ValueError): batch(kernel.section_mass,tuple(bad_station),x,r,v,a)
        invalid.append('negative_measure')
        bad=kernel.section_mass.copy();bad[0,0]=-1.
        with pytest.raises(ValueError): batch(bad,kernel._stations,x,r,v,a)
        invalid.append('nonpositive_section')
        bad=r.copy();bad[0,0,0]=2.
        with pytest.raises(ValueError): batch(kernel.section_mass,kernel._stations,x,bad,v,a)
        invalid.append('improper_frame')
        bad=v.copy();bad[0]=np.nan
        with pytest.raises(ValueError): batch(kernel.section_mass,kernel._stations,x,r,bad,a)
        invalid.append('nonfinite_velocity')
        evidence['negative_controls']=invalid
        # Balanced fixed four calls; prepared inputs unchanged, no temporal run.
        for name in spec['criteria']['timing_order']:
            mark=perf_counter()
            response=(kernel.evaluate(x,r,v,a) if name=='scalar' else batch(kernel.section_mass,kernel._stations,x,r,v,a))
            elapsed=perf_counter()-mark
            evidence['timings'].append(dict(kernel=name,elapsed_seconds=elapsed))
            assert scaled_difference(response.inertia,base.inertia) <= 1e-13
        evidence['status']='PASS'
        save('complete')
        record_property('candidate_module_sha256',spec['source_sha256'][spec['candidate_module']])
    except BaseException as exc:
        evidence['status']='NONPASS'
        evidence['failure']=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
        save('first_failure');raise
    finally:
        evidence['source_postverify']={path:sha256(Path(path).read_bytes()).hexdigest()==expected
            for path,expected in spec['source_sha256'].items()}
        save('final_preserved')
