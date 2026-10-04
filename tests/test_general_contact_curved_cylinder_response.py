"""Guided curved B3 response checked against independently integrated work.

The scalar structural law is derived from quadratic Timoshenko/von Karman
strain energy. The contact oracle integrates explicit Lagrange polynomials;
it does not call the production contact or element-response kernels.
This is bounded code verification, not an unrestricted beam qualification.
"""
from dataclasses import replace
import json
import os
from pathlib import Path

import numpy as np
import pytest
from numpy.polynomial import Polynomial
from scipy.optimize import brentq

from anysolver import BoundaryCondition, LoadCase, solve_static_nonlinear
from anysolver.general_contact.beam_hemisphere_cylinder import HemisphereCylinderManager
from test_general_contact_hemisphere_cylinder_static import _support_case, _line_reference
from test_general_contact_hemisphere_cylinder_work import _reference

L = .2
EA = 1.
GA = 1000. / (2. * 1.3) * .001 * (5. / 6.)
SHEAR = 16. * GA / (3. * L)
CUBIC = 25.6 * EA / L**3
FORCE = .01
RADIUS = .11
LINE = 1e8


def fixture(moving):
    model, definition, settings = _support_case(True, 1e5)
    model.add_boundary_condition(BoundaryCondition('left', (1,),
        {key: 0. for key in ('ux','uy','uz','rx','ry','rz')}))
    model.add_boundary_condition(BoundaryCondition('right', (3,),
        {key: 0. for key in ('ux','uy','uz','rx','ry','rz')}))
    model.add_boundary_condition(BoundaryCondition('mid_guide', (2,),
        {key: 0. for key in ('ux','uz','rx','ry','rz')}))
    body = replace(definition.rigid_bodies[0], point=(.117, -.111 if moving else -.110005, 0.),
        path_translation=(0., .000995, 0.) if moving else None)
    definition = replace(definition, rigid_bodies=(body,), interactions=(
        replace(definition.interactions[0], line_stiffness=LINE, gap_tolerance=1e-5),))
    settings = replace(settings, beam_end_cap_work=(
        'hemisphere_coupled_tool_dev' if moving else 'hemisphere_support_dev'))
    load = LoadCase('guided quadratic transverse force')
    load.add_nodal_load(2, forces=(0., -FORCE, 0.))
    return model, definition, settings, load


def reference(factor, moving):
    point = np.array((.117, -.111 + .000995*factor if moving else -.110005, 0.))
    def evaluate(q):
        positions = np.array(((.112, 0., 0.), (.212, q, 0.), (.312, 0., 0.)))
        energy, gradients = _line_reference(positions, RADIUS, point,
            np.array((0., 0., 1.)), LINE, L)
        return positions, energy, gradients
    def balance(q):
        return SHEAR*q + CUBIC*q**3 + evaluate(q)[2][1, 1] + FORCE*factor
    q = brentq(balance, -FORCE*factor/SHEAR, 0., xtol=1e-16)
    return q, point, evaluate(q)


def independent_gap(positions, point):
    # The squared radial distance is quartic. Its extrema include all
    # interior minima of the actual curved centreline, not just the nodes.
    lanes = [Polynomial((positions[0,j]-point[j],
        4*positions[1,j]-3*positions[0,j]-positions[2,j],
        2*positions[0,j]-4*positions[1,j]+2*positions[2,j])) for j in (0,1)]
    distance = sum((lane*lane for lane in lanes), Polynomial((0.,)))
    sites = [0.,1.] + [float(x.real) for x in distance.deriv().roots()
        if abs(x.imag)<1e-12 and 0.<x.real<1.]
    gaps = [(float(np.sqrt(distance(s))-RADIUS), s) for s in sites]
    return min(gaps), gaps


@pytest.mark.parametrize('moving', (False, True))
def test_guided_curved_response_and_wrench(moving):
    model, definition, settings, load = fixture(moving)
    result = solve_static_nonlinear(model, load, contact=definition, contact_settings=settings,
        num_steps=4, max_iterations=20, tolerance=1e-10)
    assert result.status == 'completed', result.failure_reason
    q, point, (positions, energy, gradients) = reference(1., moving)
    actual = result.displacements[model.mesh.dof_manager.get_node_dofs(2)[1]]
    assert actual == pytest.approx(q, rel=1e-6, abs=1e-11)
    info = result.info['general_contact']
    assert info['active_line_length'] > 0 and info['active_endpoints'] == 0
    assert info['line_contact_energy'] == pytest.approx(energy, rel=1e-4, abs=1e-14)
    np.testing.assert_allclose(info['beam_force'], -gradients.sum(axis=0), rtol=1e-6, atol=1e-10)
    np.testing.assert_allclose(info['beam_moment'], -np.cross(positions, gradients).sum(axis=0),
        rtol=1e-6, atol=1e-10)
    actual_positions = positions.copy(); actual_positions[1,1] = actual
    (gap, location), extrema = independent_gap(actual_positions, point)
    assert 0. < location < 1. and -1e-5 <= gap < 0.
    assert all(np.linalg.norm(p[:2]-point[:2])-RADIUS > 0. for p in actual_positions)
    cap_gaps = [_reference(actual_positions, end, sign, .01, point, np.array((0.,0.,1.)), .1)[0]
        for end, sign in ((0,-1),(2,1))]
    assert min(cap_gaps) > 0.
    # Reported value is a conservative enclosure, not an exact minimum.
    assert info['minimum_gap'] <= gap + 1e-12
    assert gap-info['minimum_gap'] <= info['gap_enclosure_accuracy_m'] + 1e-12
    assert info['gap_tolerance_met']
    force = np.array((0., -FORCE, 0.)) + np.asarray(info['beam_force'])
    moment = np.cross(actual_positions[1], (0.,-FORCE,0.)) + np.asarray(info['beam_moment'])
    for name, node in (('left',1),('mid_guide',2),('right',3)):
        reaction = np.asarray(result.steps[-1].support_reactions[name])
        force += reaction[:3]
        moment += reaction[3:] + np.cross(actual_positions[node-1], reaction[:3])
    assert np.linalg.norm(force)/FORCE <= 1e-6
    assert np.linalg.norm(moment)/(FORCE*L) <= 1e-6
    history_checks = []
    for row in result.info['force_displacement_history']:
        expected_q, _, _ = reference(row['load_factor'], moving)
        # Exactly one free coordinate, negative under the declared load;
        # the public full displacement norm therefore equals -q.
        actual_q = -row['displacement_norm']
        assert actual_q == pytest.approx(expected_q, rel=1e-6, abs=1e-11)
        history_checks.append(dict(factor=row['load_factor'], q=actual_q, reference_q=expected_q))
    record = os.environ.get('CONTACT_APP_RESULT_RECORD')
    if record:
        Path(record).with_name('curved_'+('moving' if moving else 'fixed')+'.json').write_text(
            json.dumps(dict(reference_q=q, actual_q=actual, independent_gap=gap,
                extremal_gaps=extrema, cap_gaps=cap_gaps, force_balance=force.tolist(),
                moment_balance=moment.tolist(), info=info,
                states=len(result.info['force_displacement_history']),
                iterations=result.info['total_newton_iterations'], history_checks=history_checks),
                indent=2), encoding='utf-8')


def test_initial_open_interior_minimum_has_nonpenetration_certificate(monkeypatch):
    from anysolver.general_contact import beam_hemisphere_cylinder as geometry
    model, definition, settings, _ = fixture(False)
    bounds = []
    original = geometry.curve_gap_lower
    def record(*args, **kwargs):
        bound = original(*args, **kwargs)
        bounds.append((kwargs.get('admit_above'), bound))
        return bound
    monkeypatch.setattr(geometry, 'curve_gap_lower', record)
    manager = HemisphereCylinderManager(model, definition, settings)
    assert bounds and bounds[0][0] == 0. and bounds[0][1] >= 0.
    cell = manager.cells[0]
    positions = np.array([model.mesh.nodes[n].coords() for n in cell.node_ids])
    (_, bound) = manager._geometry(cell, positions)
    (exact, location), _ = independent_gap(positions, np.array(definition.rigid_bodies[0].point))
    assert 0. < location < 1. and 0. <= bound <= exact
    assert bounds[0][1] <= exact


@pytest.mark.parametrize('hidden', (False, True))
def test_initial_penetration_never_becomes_admitted_by_open_certificate(hidden):
    model, definition, settings, _ = fixture(False)
    initial = np.zeros(model.mesh.dof_manager.total_dofs)
    if hidden:
        initial[model.mesh.dof_manager.get_node_dofs(2)[1]] = -.0001
    else:
        definition = replace(definition, rigid_bodies=(
            replace(definition.rigid_bodies[0], point=(.117,-.10999,0.)),))
    positions = np.array([model.mesh.nodes[n].coords()+initial[
        model.mesh.dof_manager.get_node_dofs(n)[:3]] for n in (1,2,3)])
    point = np.array(definition.rigid_bodies[0].point)
    assert independent_gap(positions,point)[0][0] < 0.
    if hidden:
        assert all(np.linalg.norm(p[:2]-point[:2])-RADIUS>0. for p in positions)
    # Unresolved roundoff classification is explicit failure, never admission.
    with pytest.raises((ValueError,MemoryError), match='penetration|enclosure budget'):
        HemisphereCylinderManager(model, definition, settings, initial)
