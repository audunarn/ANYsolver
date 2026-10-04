"""Curved retained B3-GE / deformable S3 interior: static development example."""
import json
import argparse
from hashlib import sha256
from pathlib import Path
from math import pi
import numpy as np
from anysolver import create_shell_element
from anysolver.fe_core import FEModel
from anysolver.boundary import BoundaryCondition,FixedSupport
from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry
from anysolver._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
from anysolver._ge_beam3_native_definition import NativeBeamDefinition
from anysolver._ge_beam3_native_generalized_element import NativeGeneralizedStaticElement
from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
from anysolver._ge_beam3_native_line_loading import LinePattern
from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces,Program
from anysolver.general_contact.native_surface_quadrature import NativeRoundSurfaceRule
from anysolver.general_contact.native_surface_normal import StraightNormalIntegrationSettings
from anysolver.general_contact.native_material_s3 import NativeMaterialS3Patch
from anysolver.general_contact.native_curved_s3_work import NativeCurvedMaterialS3Work
from anysolver.general_contact.s3_skin_work import S3SkinWorkAdapter
from anysolver.general_contact import NativeS3ContactPair,create_native_contact_analysis


def analysis(targets=(1.,0.,1.),*,normal_stiffness_Pa_per_m=1e7):
    points=[];frames=[]
    for x in np.linspace(0.,2.,3):
        points.append((x,.2*(1-(x-1)**2),0.))
        tangent=np.array((1.,.4*(1-x),0.));tangent/=np.linalg.norm(tangent)
        second=np.array((0.,0.,1.));frames.append(np.column_stack((tangent,second,np.cross(tangent,second))))
    reference=CenteredCurvedBeam3ReferenceGeometry(np.array(points),np.array(frames))
    section=EllipsoidalGeneralizedSection(np.diag((1000.,400.,350.,.8,1.,1.2)),np.eye(6),1e6,1.)
    element=NativeGeneralizedStaticElement(1,(1,2,3),reference,section,order=4)
    definition=NativeBeamDefinition.capture(element,np.diag((2.,2.,2.,.07,.09,.11)))
    root=BoundaryCondition('clamped',[1],{name:0. for name in ('ux','uy','uz','rx','ry','rz')})
    program=Program(targets,DistributedPattern(LinePattern(()),()),NodalDeadForces(((3,0.,0.,-.005),)),max_iterations=24)
    shell=FEModel('curved material and deformable S3');shell.add_material('elastic',1e8,.3,density=1.)
    for node,xy in zip((4,5,6),((-5.,-5.),(5.,-5.),(0.,10.))):shell.add_node(node,*xy,-.0551)
    shell.add_element(21,create_shell_element(21,(4,5,6),'elastic',thickness=.05,
        formulation='e4-pl-s3-v2d',reference_normal=(0.,0.,1.),reference_surface_offset=0.))
    shell.add_boundary_condition(FixedSupport('edge',[4,6]))
    shell.add_boundary_condition(BoundaryCondition('moving vertex',[5],
        {name:0. for name in ('ux','uy','rx','ry','rz')}))
    skin=S3SkinWorkAdapter.from_model(shell,7,21,'top')
    rule=NativeRoundSurfaceRule(1,reference,.03,xi_range=(.1,.9),angle_range=(pi-.3,pi+.3),axial_order=1,angular_order=1)
    patch=NativeMaterialS3Patch(rule,(1,2,3),normal_stiffness_Pa_per_m=normal_stiffness_Pa_per_m,
        integration_settings=StraightNormalIntegrationSettings(1e-10,1e-8,1e-6,64,2.),
        geometry_tolerance_m=1e-10,rim_clearance_m=1e-6)
    pair=NativeS3ContactPair('curved material / top',NativeCurvedMaterialS3Work(patch,skin),3e-5,128)
    return create_native_contact_analysis((definition,),(root,),program,shell,(pair,),equilibrium_tolerance=1e-10)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--through-target',type=int,choices=(1,2,3),default=1)
    parser.add_argument('--restart',type=Path)
    parser.add_argument('--checkpoint-out',type=Path)
    args=parser.parse_args()
    raw=None if args.restart is None else args.restart.read_bytes()
    if args.through_target>1 and raw is None:
        parser.error('--restart is required for subsequent bounded stages')
    if raw is not None and json.loads(raw)['completed_targets']!=args.through_target-1:
        parser.error('restart must precede the requested target by exactly one stage')
    run=analysis().solve(checkpoint=raw,expected_sha256=None if raw is None else sha256(raw).hexdigest(),
        stop_after=args.through_target)
    if run.status not in ('paused','completed'):raise RuntimeError(run.failure)
    if args.checkpoint_out is not None:args.checkpoint_out.write_bytes(run.checkpoint)
    print(json.dumps(dict(status=run.status,profile=run.profile,completed_targets=run.accepted.completed_targets,
        qualification='development only; not independently accepted or released',
        targets=[dict(target=row['target'],contact=row['contact']) for row in json.loads(run.checkpoint)['records']],
        checkpoint_sha256=run.checkpoint_sha256),indent=2))


if __name__=='__main__':main()
