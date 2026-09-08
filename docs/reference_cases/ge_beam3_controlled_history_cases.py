"""Frozen research specimens; no production import depends on this module."""
from fractions import Fraction
from math import cos, sin, sqrt
import numpy as np
from anysolver.fe_core import FEModel
from anysolver.boundary import BoundaryCondition
from anysolver._ge_beam3_native_generalized_element import NativeGeneralizedStaticElement
from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry
from anysolver._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
from anysolver._ge_beam3_retained_translation_control import Program

CASES = ('axial', 'curved', 'connected')

def pose(name):
    if name == 'base': return np.eye(3), np.zeros(3)
    if name == 'large-dyadic':
        return np.array([[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]]), np.array([2.**30, -2.**29, 2.**28])
    if name != 'general': raise ValueError('registered pose required')
    a = np.array([2., -3., 4.])/sqrt(29.)
    x, y, z = a; cross = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
    return cos(2.1)*np.eye(3)+(1-cos(2.1))*np.outer(a, a)+sin(2.1)*cross, np.array([16., -8., 4.])

def transformed_positions(high, low, rotation, translation):
    high_out = np.empty_like(high); low_out = np.empty_like(low)
    for node in range(len(high)):
        for i in range(3):
            value = Fraction(float(translation[i]))+sum([Fraction(float(rotation[i, j]))*
                (Fraction(float(high[node, j]))+Fraction(float(low[node, j]))) for j in range(3)], Fraction(0))
            h = float(value); l = float(value-Fraction(h))
            high_out[node, i], low_out[node, i] = h, l
    return high_out, low_out

def position_error(actual, base, rotation, translation):
    differences = []
    for node in range(len(base.positions)):
        for i in range(3):
            expected = Fraction(float(translation[i]))+sum([Fraction(float(rotation[i, j]))*
                (Fraction(float(base.positions[node, j]))+Fraction(float(base.position_low[node, j]))) for j in range(3)], Fraction(0))
            observed = Fraction(float(actual.positions[node, i]))+Fraction(float(actual.position_low[node, i]))
            differences.append(float(observed-expected))
    return float(np.linalg.norm(differences))/2.

def section(axial):
    if axial:
        return EllipsoidalGeneralizedSection(np.diag([1000., 400., 350., .8, 1., 1.2]), np.eye(6), .05, 10.)
    # Exact existing coupled section fixture, independently enumerated here.
    a = np.eye(6); a[0, 3] = .2; a[1, 4] = -.3; a[2, 5] = .25; a[0, 1] = .1
    b = np.eye(6); b[0, 5] = .2; b[1, 3] = -.15; b[2, 4] = .1
    return EllipsoidalGeneralizedSection(a.T@np.diag([4., 6., 8., 2., 3., 5.])@a,
        b.T@np.diag([1., .25, .5, 2., .75, 1.5])@b, .025, .6)

def make(case, pose_name='base'):
    if case not in CASES: raise ValueError('registered controlled-history specimen required')
    macros = 2 if case == 'connected' else 1; axial = case == 'axial'
    rotation, translation = pose(pose_name); points = []; frames = []
    for x in np.linspace(0., 2., 2*macros+1):
        point = np.array([x, 0. if axial else .25*(1-(x-1)**2), 0.])
        tangent = np.array([1., 0. if axial else .5*(1-x), 0.]); tangent /= np.linalg.norm(tangent)
        second = np.array([0., 0., 1.]); frame = np.column_stack((tangent, second, np.cross(tangent, second)))
        points.append(rotation@point+translation); frames.append(rotation@frame)
    model = FEModel('retained-controlled-history-'+case+'-'+pose_name); law = section(axial)
    for node, point in enumerate(points, 1): model.add_node(node, *point)
    for index in range(macros):
        ids = tuple(range(2*index+1, 2*index+4))
        reference = CenteredCurvedBeam3ReferenceGeometry(np.array(points[2*index:2*index+3]), np.array(frames[2*index:2*index+3]))
        element = NativeGeneralizedStaticElement(index+1, ids, reference, law, order=4)
        model.add_element(index+1, element); model.materials[element.material_name] = element.section
    model.add_boundary_condition(BoundaryCondition('clamped', [1], {k: 0. for k in ('ux','uy','uz','rx','ry','rz')}))
    force = np.array([1., 0., 0.] if axial else [1., -.3, .2]); direction = force/np.linalg.norm(force)
    targets = (.00005,.00015,.0005,.0002,0.,-.0005,0.) if axial else (.005,.02,.08,.03,0.,-.08,0.)
    force = rotation@force; direction = rotation@direction
    program = Program(targets, len(points), tuple(map(float, direction)),
                      NodalDeadForces(((len(points), *map(float, force)),)))
    return model, program

def axial_reference(targets):
    """Independent scalar primal return map, not a section-library call."""
    plastic = accumulated = 0.; rows = []
    for target in targets:
        strain = target/2.; trial = 1000.*(strain-plastic)
        excess = abs(trial)-(.05+10.*accumulated)
        increment = max(0., excess/1010.); sign = 1. if trial >= 0. else -1.
        stress = trial-1000.*increment*sign
        plastic += increment*sign; accumulated += increment
        rows.append(dict(strain=strain, stress=stress, plastic=plastic, accumulated=accumulated, increment=increment))
    return rows
