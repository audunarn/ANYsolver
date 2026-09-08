"""Actual retained arch continuation; separate continuum is comparison only."""
from fractions import Fraction
from math import fsum
import numpy as np
from anysolver import _ge_beam3_retained_arc as arc
from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as Reference
from anysolver._ge_beam3_native_generalized_element import NativeGeneralizedStaticElement
from anysolver._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
from anysolver._ge_beam3_p5_seeded.core import canonical
from anysolver.fe_core import FEModel
from anysolver.boundary import BoundaryCondition
from docs.reference_cases import ge_beam3_curved_p5_arch_reference as continuum
from docs.reference_cases.ge_beam3_fibre_arch_comparison import geometry_diagnostics, sampled_geometry

SECTION = np.array((1000., 400., 400., .02, .01, .02))
STEPS = (.01,)*12


def model(macros):
    if type(macros) is not int or macros not in (2, 4, 8, 12):
        raise ValueError('registered 2/4/8/12 macro arch required')
    made = FEModel('retained-full-spatial-crown-arch'); frames = []
    x = np.linspace(-1., 1., 2*macros+1)
    for node, t in enumerate(x, 1):
        made.add_node(node, float(t), float(.1*(1-t*t)), 0.)
        tangent = np.array((1., -.2*t, 0.)); tangent /= np.linalg.norm(tangent)
        second = np.array((0., 0., 1.))
        frames.append(np.column_stack((tangent, second, np.cross(tangent, second))))
    section = EllipsoidalGeneralizedSection(np.diag(SECTION), np.eye(6), 1e6, 1.)
    for i in range(macros):
        nodes = (2*i+1, 2*i+2, 2*i+3)
        reference = Reference(np.array([made.mesh.nodes[n].coords() for n in nodes]), np.array(frames[2*i:2*i+3]))
        element = NativeGeneralizedStaticElement(i+1, nodes, reference, section, order=4)
        made.add_element(i+1, element); made.materials[element.material_name] = section
    made.add_boundary_condition(BoundaryCondition('ends', [1, 2*macros+1],
        {key:0. for key in ('ux', 'uy', 'uz', 'rx', 'ry', 'rz')}))
    return made


def program(macros):
    if type(macros) is not int or macros not in (2, 4, 8, 12):
        raise ValueError('registered arch count')
    return arc.Program(STEPS, 2., arc.NodalDeadForces(((macros+1, 0., -1., 0.),)))


def drop(state, macros):
    return float(Fraction(.1)-Fraction(float(state.mechanical.positions[macros, 1]))
                 -Fraction(float(state.mechanical.position_low[macros, 1])))


def reference_fields(reference, locations):
    fields = []
    for location in locations:
        indices = np.flatnonzero(reference.parameter == -abs(location))
        if len(indices) != 1: raise ValueError('every reference station must be evaluated directly')
        _, _, angle, moment = reference.fields[:, indices[0]]
        side = 1. if location <= 0. else -1.
        angle *= side; fx, fy = reference.force[0], side*reference.force[1]
        n = fx*np.cos(angle)+fy*np.sin(angle); v = -fx*np.sin(angle)+fy*np.cos(angle)
        fields.append((n, 0., -v, 0., moment, 0.))
    return np.array(fields)


def compare(context, state, *, previous=None):
    """Recompute accepted-state slope, all station fields and physical work."""
    p = context.physical; macros = len(p.elements); crown = drop(state, macros)
    before = canonical(state); recovered = context.recover(state)
    locations, weights, stresses, strains = [], [], [], []
    for (_, element), recovered_element in zip(p.elements, recovered):
        for row in recovered_element['stations']:
            locations.append(float(element.operator.reference.position(row['xi'])[0])); weights.append(row['measure'])
            stresses.append(row['resultants']+row['resultants_low']); strains.append(row['strain']+row['strain_low'])
            if row['history'].accumulated != (0., 0.): raise ValueError('elastic arch acquired plastic history')
    locations, weights, stresses, strains = map(np.asarray, (locations, weights, stresses, strains))
    node_x = p.reference_positions[:, 0]
    samples = np.unique(np.r_[np.linspace(-1., 0., 129), -abs(node_x), -abs(locations)])
    reference = continuum.solve(crown, height=.1, axial=1000., shear=400., bending=.01,
        profile='BVP9', previous=previous, sample_parameters=samples)
    expected = reference_fields(reference, locations)
    def energy_norm_squared(values): return float(np.sum(weights[:, None]*values*values/SECTION))
    recovery_error = np.sqrt(energy_norm_squared(stresses-expected)/energy_norm_squared(expected))
    material_error = float(np.max(abs(strains*SECTION-stresses)))/max(1., float(np.max(abs(stresses))))
    energy = float(.5*np.sum(weights*np.sum(strains*stresses, axis=1)))
    energy_error = abs(energy-reference.strain_energy)/reference.strain_energy
    points, frames = sampled_geometry(reference, node_x)
    position_error = max(abs(fsum((float(h), float(l), -float(r)))) for h,l,r in
        zip(state.mechanical.positions.flat, state.mechanical.position_low.flat, points.flat))
    frame_error = float(np.max(abs(state.mechanical.nodal_frames-frames)))
    direction = context.predictor(state); crown_direction = -direction[6*macros+1]
    if crown_direction <= 1e-12: raise ValueError('crown does not orient this branch')
    slope = float(direction[-1]/crown_direction)
    raw = context._require_issued(state)
    import json
    accepted = json.loads(raw)
    residual = np.array(accepted['residual'][:p.nodal_count]).reshape(-1, 6)
    total = residual.copy(); total[macros, 1] -= state.parameter
    force_balance = np.linalg.norm(np.sum(total[:, :3], axis=0))
    moment_balance = np.linalg.norm(np.sum(total[:, 3:]+np.cross(state.mechanical.positions, total[:, :3])
                                        +np.cross(state.mechanical.position_low, total[:, :3]), axis=0))
    work_error = abs(accepted['work'][-1]-state.parameter*crown)
    if canonical(state) != before: raise ValueError('arch comparison changed accepted state')
    rows = dict(step=state.completed_steps, drop=crown, load=state.parameter, reference_load=reference.load,
        load_error=abs(state.parameter-reference.load)/abs(reference.load), slope=slope, reference_slope=reference.load_slope,
        crown_direction=float(crown_direction), parameter_direction=float(direction[-1]),
        recovery_error=float(recovery_error), energy=energy, energy_error=float(energy_error), material_error=material_error,
        position_error=position_error, frame_error=frame_error, force_balance=float(force_balance),
        moment_balance=float(moment_balance), work_error=float(work_error), stations=len(weights),
        geometry=geometry_diagnostics(state.mechanical.descriptor()),
        reference_errors=dict(boundary=reference.boundary_error, differential=reference.differential_error,
            sensitivity=reference.sensitivity_error, work=reference.work_error),
        metrics=accepted['metrics'], arc_gap=accepted['arc_gap'], correction=accepted['correction'])
    return rows, reference, recovered
