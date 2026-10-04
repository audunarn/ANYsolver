"""Interior native round material patch against a deformable S3 physical skin.

Frictionless static development profile: one straight half-cell patch and one
small-rotation elastic S3. Caps, friction and dynamics remain unadmitted.
"""
import json
from math import pi

import numpy as np

from anysolver import create_shell_element
from anysolver.boundary import BoundaryCondition, FixedSupport
from anysolver.fe_core import FEModel
from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry
from anysolver._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
from anysolver._ge_beam3_native_definition import NativeBeamDefinition
from anysolver._ge_beam3_native_generalized_element import NativeGeneralizedStaticElement
from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
from anysolver._ge_beam3_native_line_loading import LinePattern
from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces, Program
from anysolver.general_contact.native_material_s3 import NativeMaterialS3Patch, NativeRetainedMaterialS3Work
from anysolver.general_contact.native_retained_s3_static import NativeRetainedRoundS3Analysis
from anysolver.general_contact.native_surface_normal import StraightNormalIntegrationSettings
from anysolver.general_contact.native_surface_quadrature import NativeRoundSurfaceRule
from anysolver.general_contact.s3_skin_work import S3SkinWorkAdapter


def analysis():
    points = np.array(((0., 0., 0.), (1., 0., 0.), (2., 0., 0.)))
    frame = np.array(((1., 0., 0.), (0., 0., -1.), (0., 1., 0.)))
    reference = CenteredCurvedBeam3ReferenceGeometry(points, np.tile(frame, (3, 1, 1)))
    section = EllipsoidalGeneralizedSection(np.diag((1000., 400., 350., .8, 1., 1.2)),
                                           np.eye(6), 1e6, 1.)
    element = NativeGeneralizedStaticElement(1, (1, 2, 3), reference, section, order=4)
    definition = NativeBeamDefinition.capture(element, np.diag((2., 2., 2., .07, .09, .11)))
    root = BoundaryCondition('clamped', [1],
                             {name: 0. for name in ('ux', 'uy', 'uz', 'rx', 'ry', 'rz')})
    program = Program((.5, 1., 0., .5, 1.), DistributedPattern(LinePattern(()), ()),
                      NodalDeadForces(((3, 0., 0., -.005),)), max_iterations=24)
    shell = FEModel('native material patch and deformable S3')
    shell.add_material('elastic', 1e8, .3, density=1.)
    for node, (x, y) in zip((4, 5, 6), ((-5., -5.), (5., -5.), (0., 10.))):
        shell.add_node(node, x, y, -.0751)
    shell.add_element(21, create_shell_element(21, (4, 5, 6), 'elastic', thickness=.05,
        formulation='e4-pl-s3-v2d', reference_normal=(0, 0, 1), reference_surface_offset=0.))
    shell.add_boundary_condition(FixedSupport('edge', [4, 6]))
    shell.add_boundary_condition(BoundaryCondition('moving vertex', [5],
                                 {name: 0. for name in ('ux', 'uy', 'rx', 'ry', 'rz')}))
    skin = S3SkinWorkAdapter.from_model(shell, 7, 21, 'top')
    rule = NativeRoundSurfaceRule(1, reference, .05, xi_range=(.1, .9),
        angle_range=(pi-.3, pi+.3), axial_order=1, angular_order=1)
    patch = NativeMaterialS3Patch(rule, (1, 2, 3), normal_stiffness_Pa_per_m=1e6,
        integration_settings=StraightNormalIntegrationSettings(1e-12, 1e-10, 1e-9, 64, 2.),
        geometry_tolerance_m=1e-10, rim_clearance_m=1e-6)
    return NativeRetainedRoundS3Analysis((definition,), (root,), program, shell,
        NativeRetainedMaterialS3Work(patch, skin), gap_tolerance_m=5e-5,
        equilibrium_tolerance=1e-10, maximum_swept_intervals=128)


def main():
    run = analysis().solve()
    if run.status != 'completed':
        raise RuntimeError(run.failure)
    contact = run.accepted.contact.contact
    print(json.dumps(dict(profile=run.profile, status=run.status,
        qualification='implemented/tested development; not engineering accepted',
        completed_targets=run.accepted.completed_targets,
        normal_stiffness_Pa_per_m=1e6, measure='fixed reference material area',
        minimum_gap_lower_bound_m=contact.minimum_gap_m,
        minimum_gap_estimate_m=contact.minimum_gap_estimate_m,
        beam_force_n=contact.beam_force_n.tolist(), shell_force_n=contact.shell_force_n.tolist(),
        beam_moment_nm=contact.beam_moment_nm.tolist(), shell_moment_nm=contact.shell_moment_nm.tolist(),
        wrench_origin_m=(0., 0., 0.), shell_displacement_norm_m=float(np.linalg.norm(run.accepted.shell_displacement)),
        normal_storage_j=contact.potential_j, checkpoint_sha256=run.checkpoint_sha256), indent=2))


if __name__ == '__main__':
    main()
