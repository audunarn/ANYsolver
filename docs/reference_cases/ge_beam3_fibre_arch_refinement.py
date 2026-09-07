"""Frozen small-model family for a separately authorized refinement probe.

Same private physical-fibre section, exact parabola, clamped ends and crown
force/control as the preserved two-macro fixture. No formulation change,
automatic retry, public selector or qualification authority.
"""
import numpy as np


TARGETS = (.01, .025, .04, .055)


def model(macros):
    if type(macros) is not int or macros not in (2, 4, 6, 12):
        raise ValueError('registered 2/4/6/12-macro arch within native allocation bound')
    from anysolver.fe_core import FEModel
    from anysolver.boundary import BoundaryCondition
    from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as Reference
    from anysolver._ge_beam3_retained_fibre_element import NativeRetainedFibreElement
    from anysolver._ge_beam3_fibre_section import PhysicalFibreSection, Fibre, FlowCurve
    made = FEModel('small-physical-fibre-shallow-arch'); frames = []
    for node, x in enumerate(np.linspace(-1., 1., 2*macros+1), 1):
        made.add_node(node, float(x), float(.1*(1-x*x)), 0.)
        tangent = np.array([1., -.2*x, 0.]); tangent /= np.linalg.norm(tangent)
        second = np.array([0., 0., 1.])
        frames.append(np.column_stack((tangent, second, np.cross(tangent, second))))
    fibres = tuple(Fibre(str(i), y, z, .25, 1.e6, FlowCurve.linear(1.e6, 100.))
        for i, (y, z) in enumerate([(-.01, -.01), (-.01, .01), (.01, -.01), (.01, .01)]))
    factor = np.zeros((3, 6))
    factor[0, 1] = np.sqrt(4.e5); factor[1, 2] = np.sqrt(4.e5); factor[2, 3] = np.sqrt(80.)
    section = PhysicalFibreSection(fibres, factor)
    for eid in range(1, macros+1):
        nodes = (2*eid-1, 2*eid, 2*eid+1)
        reference = Reference(np.array([made.mesh.nodes[n].coords() for n in nodes]),
            np.array([frames[n-1] for n in nodes]))
        element = NativeRetainedFibreElement(eid, nodes, reference, section, order=4)
        made.add_element(eid, element); made.materials[element.material_name] = section
    made.add_boundary_condition(BoundaryCondition('ends', [1, 2*macros+1],
        {key: 0. for key in ('ux', 'uy', 'uz', 'rx', 'ry', 'rz')}))
    return made


def program(macros):
    if type(macros) is not int or macros not in (2, 4, 6, 12): raise ValueError('registered arch count')
    from anysolver._ge_beam3_seeded_fibre_control import TranslationProgram
    crown = macros+1
    return TranslationProgram(TARGETS, crown, (0., -1., 0.), ((crown, 0., -1., 0.),))
