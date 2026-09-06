"""Small axial semidiscrete temporal checks; no continuum qualification."""

import ast
import math
from pathlib import Path

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_axial_time_reference as exact
from docs.reference_cases.ge_beam3_curved_p5_implicit_dynamics_probe import ImplicitDynamicProbe
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from test_ge_beam3_curved_p5_algebra_probe import reference


def test_reference_has_no_beam_or_numerical_library_import():
    tree=ast.parse(Path(exact.__file__).read_text())
    imports=[n for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
    assert len(imports)==1 and isinstance(imports[0],ast.Import)
    assert [n.name for n in imports[0].names]==['math']


def test_closed_modes_and_time_response_satisfy_the_rod_equations():
    for sign in (-1,1):
        mode=np.array([1.,-sign*math.sqrt(2.)])
        value=6*exact.EA/(7*exact.RHO)*(5+sign*3*math.sqrt(2.))
        assert np.linalg.norm(np.array(exact.K)@mode-value*np.array(exact.M)@mode)<1e-11
    assert exact.step_response(0.)==((0.,0.),(0.,0.))
    for time in (.04,.12):
        x,v=exact.pulse_response(time);epsilon=1e-6
        plus=exact.pulse_response(time+epsilon);minus=exact.pulse_response(time-epsilon)
        acceleration=(np.array(plus[1])-minus[1])/(2*epsilon)
        derivative=(np.array(plus[0])-minus[0])/(2*epsilon)
        expected=np.array([0.,exact.FORCE if time<exact.DURATION/2 else 0.])
        assert np.linalg.norm(np.array(exact.M)@acceleration+np.array(exact.K)@x-expected)<1e-7
        assert np.linalg.norm(derivative-v)<1e-7


@pytest.mark.parametrize('method',['BACKWARD_EULER','MIDPOINT'])
def test_linear_work_identity_and_temporal_error_are_separate(method):
    errors=[]
    for steps in (4,8,16,32):
        result=exact.integrate(steps,method=method);rows=result['records'];errors.append(result['temporal_error'])
        scale=max(r['energy'] for r in rows)
        assert max(abs(r['balance_error']) for r in rows)<1e-11*scale
        assert abs(rows[-1]['energy']-result['work']+result['dissipation'])<1e-11*scale
        for left,right in zip(rows[steps//2-1:-1],rows[steps//2:]):
            if method=='MIDPOINT': assert abs(right['energy']-left['energy'])<1e-11*scale
            else: assert right['energy']<left['energy']
        assert result['production_qualified'] is False
    assert all(b<a for a,b in zip(errors,errors[1:]))
    observed=math.log2(errors[-2]/errors[-1])
    # Declared development check of expected temporal order, not a beam gate.
    assert .8<observed<1.1 if method=='BACKWARD_EULER' else 1.9<observed<2.1


def test_first_order_limitation_is_preserved_not_mislabeled_mechanics_failure():
    backward=exact.integrate(16);midpoint=exact.integrate(16,method='MIDPOINT')
    assert backward['temporal_error']>.15
    assert midpoint['temporal_error']<.01
    assert abs(backward['relative_energy_error'])>.20
    # Midpoint's energy differs from the exact pulse solution because of
    # time-discretized external work; free-phase conservation is tested above.
    assert midpoint['relative_energy_error']<0.


@pytest.mark.parametrize('steps',[4,8,16])
def test_actual_beam_matches_separate_axial_recurrence_and_dissipation(steps):
    ref=reference(0.)
    section=np.diag([exact.EA,60.,70.,10.,12.,14.]);inertia=np.diag([exact.RHO]*3+[.2,.1,.15])
    beam=ImplicitDynamicProbe(ref,section,inertia,order=8)
    expected=exact.integrate(steps);h=exact.DURATION/steps;previous_energy=0.
    for row in expected['records']:
        forces=np.zeros((3,3));forces[-1,0]=row['force'][1]
        trial=beam.trial(h,forces);beam.commit(trial)
        assert digest(beam.replay())==digest(trial.response)
        state=beam.committed
        assert np.linalg.norm(state.positions[1:,0]-ref.coordinates[1:,0]-row['positions'])<1e-11
        assert np.linalg.norm(state.nodal_velocity[1:,0]-row['velocities'])<1e-11
        energy=trial.response.elastic_energy+trial.response.kinetic_energy
        scale=max(energy,row['energy'],previous_energy,1e-30)
        assert abs(energy-row['energy'])<1e-11*scale
        actual_work=h*float(forces[-1]@state.nodal_velocity[-1])
        assert abs(energy-previous_energy-actual_work+row['dissipation'])<1e-11*scale
        assert trial.residual_norm<=1e-11
        previous_energy=energy
    measured=exact.temporal_error(tuple(state.positions[1:,0]-ref.coordinates[1:,0]),tuple(state.nodal_velocity[1:,0]))
    assert abs(measured-expected['temporal_error'])<1e-11


def test_invalid_reference_profiles_are_rejected():
    for time in (True,-1.,float('nan'),float('inf')):
        with pytest.raises(ValueError): exact.pulse_response(time)
    for count in (True,0,3,64):
        with pytest.raises(ValueError): exact.integrate(count)
    with pytest.raises(ValueError): exact.integrate(4,method='QUALIFIED')
