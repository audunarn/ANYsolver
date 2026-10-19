"""Discriminating checks of independent references, not product acceptance."""
import json
import math
from pathlib import Path

import numpy as np
import pytest

from oracles import catenary, contact_response, morison_endpoint


C = json.loads((Path(__file__).parent/'contract.json').read_text())


@pytest.mark.parametrize('name', C['static_cases'])
def test_registered_reference_existence_and_global_balance(name):
    f = {**C['static'], **C['static_case_inputs'][name]}
    w = (f['mass_per_length']-f['water_density']*f['displaced_area'])*f['gravity']
    material = np.linspace(0., f['length'], 129)
    r = catenary(f['first'], f['last'], f['length'], f['EA'], w, material, grounded=name=='touchdown')
    np.testing.assert_allclose(r['positions'][0], f['first'], atol=1e-10)
    np.testing.assert_allclose(r['positions'][-1], f['last'], atol=1e-9)
    suspended = f['length']-r['grounded_length']
    np.testing.assert_allclose(r['first_force']+r['last_force'], [0, 0, -w*suspended], atol=1e-9)
    assert np.min(r['tensions']) > 0
    if name=='touchdown':
        assert 0 < r['grounded_length'] < f['length']
        assert np.min(r['positions'][:, 2]) >= f['first'][2]-1e-10


def test_reject_impossible_monotone_touchdown():
    with pytest.raises(ValueError, match='no admitted monotone'):
        catenary([0, 0, -2.95], [8, 0, -1.5], 10., 10000., 9.81, [0, 10], grounded=True)


@pytest.mark.parametrize('landing', [False, True])
@pytest.mark.parametrize('damping', [0., 40.])
def test_contact_reference_ode_and_clipping_power(landing, damping):
    m, k = 4., 40000.
    q0, v0 = (.0002, -.1) if landing else (-.001, 0.)
    times = np.linspace(0, .05, 2001)
    r = contact_response(times, q0, v0, m, k, damping)
    # Separate geometric and raw-force boundaries from smooth derivative checks.
    dt = 1e-8
    near = contact_response(times+dt, q0, v0, m, k, damping)
    far = contact_response(times-dt, q0, v0, m, k, damping)
    mask = (np.abs(times-r['landing']) > 1e-6)&(np.abs(times-r['raw_release']) > 1e-6)&(np.abs(times-r['geometric_release']) > 1e-6)&(times > dt)
    np.testing.assert_allclose(((near['q']-far['q'])/(2*dt))[mask], r['v'][mask], atol=1e-8)
    np.testing.assert_allclose((m*(near['v']-far['v'])/(2*dt))[mask], r['force'][mask], atol=1e-6)
    dU = (near['storage']-far['storage'])/(2*dt)
    np.testing.assert_allclose((r['force']*r['v']+dU+r['loss'])[mask], 0., atol=1e-8)
    assert np.min(r['force']) >= 0 and np.min(r['loss']) >= -1e-12
    if damping > 0:
        clipped = (times > r['raw_release'])&(times < r['geometric_release'])
        assert clipped.any() and np.all(r['storage'][clipped] > 0)
        assert np.all(r['force'][clipped] == 0) and np.all(r['loss'][clipped] > 0)


def test_prescribed_oracle_exercises_every_hydrodynamic_branch():
    f, k = C['harmonic'], C['prescribed_kinematics']
    p = np.linspace(*f['anchors'], 5)
    represented = np.full(5, .5)
    represented[[0, -1]] *= .5
    parts, mass = morison_endpoint(p, .4, f, k['heading_degrees'], np.tile(k['structure_velocity'], (5, 1)), np.tile(k['structure_acceleration'], (5, 1)), represented)
    assert np.max(np.abs(parts['drag_normal'][:, [0, 2]])) > 0
    assert np.max(np.abs(parts['drag_tangential'][:, 1])) > 0
    for name in ('fluid_inertia', 'added_mass'):
        assert np.max(np.abs(parts[name][:, 1])) > 0
        assert np.max(np.abs(parts[name][:, [0, 2]])) > 0
    assert np.min(mass) > 0
    assert max(f['phase_samples']*0+np.arange(f['phase_samples'])*2*math.pi/(f['phase_samples']*f['omega'])) < 2*math.pi/f['omega']


def test_strict_damping_switch_has_no_classical_newmark_root_in_boundary_interval():
    # This records a governing limitation, not a passed incoming-contact gate.
    m,k,c,dt,vp=4.,40000.,40.,.0005,-.1
    b,gamma_dt=.25*dt*dt,.5*dt
    epsilon=1e-8
    a_inactive=0.
    a_active=(k*epsilon-c*vp)/(m+k*b+c*gamma_dt)
    assert -epsilon+b*a_inactive < 0.   # contradicts inactive gap>=0
    assert -epsilon+b*a_active > 0.     # contradicts active gap<0
    threshold=b*(-c*vp)/(m+c*gamma_dt)
    assert 0 < epsilon <= threshold


@pytest.mark.parametrize('q0,v0',[(-.001,0.),(.0002,-.1)])
def test_continuous_zero_damping_trajectory_matches_exact_piecewise_reference(q0,v0):
    t=np.linspace(0.,.05,501)
    exact=contact_response(t,q0,v0,4.,40000.,0.)
    numerical=contact_response(t,q0,v0,4.,40000.,0.,activation_depth_m=1e-4)
    np.testing.assert_allclose(numerical['q'],exact['q'],atol=1e-11,rtol=1e-9)
    np.testing.assert_allclose(numerical['v'],exact['v'],atol=1e-9,rtol=1e-9)
    np.testing.assert_allclose(numerical['force'],exact['force'],atol=4e-7,rtol=1e-9)


@pytest.mark.parametrize('q0,v0,duration',[(-.001,0.,.04),(.0002,-.1,.05),(-5e-5,.2,.004)])
def test_continuous_independent_reference_energy_and_gated_events(q0,v0,duration):
    t=np.linspace(0.,duration,401)
    r=contact_response(t,q0,v0,4.,40000.,40.,activation_depth_m=1e-4)
    assert r['reference_energy_defect']<=1e-9
    assert np.min(r['force'])>=0 and np.min(r['loss'])>=-1e-12
    for crossing in r['events']['outgoing_clipping']:
        assert crossing>=0.
    if v0==.2:
        assert r['method']=='analytical_clipped_departure'
        np.testing.assert_allclose(r['q'],q0+v0*t,atol=1e-14)
        np.testing.assert_array_equal(r['force'],0.)
        assert np.max(r['loss'])>0 and r['storage'][0]>0
    else:
        assert r['method']=='independent_DOP853' and r['events']['ramp']
