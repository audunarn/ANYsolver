"""Guided Q4/S3 partial-support response against an independent continuum ODE.

Development only. The finite mesh uses nodal weak-gap pressure, whereas the
continuum reference uses pointwise finite penalty. Their agreement is measured
under refinement, not assumed. This case does not replace radial failures.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import platform
import sys
import time
import traceback

import numpy as np
import scipy
import anysolver
from anysolver import (BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactSurface, create_shell_element, solve_static_nonlinear,
    validate_general_contact)
from anysolver.boundary import LoadCase
from anysolver.fe_core import FEModel
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.nonlinear_static import _assemble_nonlinear_system, _discard_nonlinear_state_candidate
from docs.d1_review_support.d2_projected_penalty_shell_dev import fixture, file_identity, json_default
from docs.d1_review_support.d1_guided_reaction_wrench import guided_wrench_diagnostics
from docs.d1_review_support.d2_guided_partial_foundation_reference import make_reference


INPUTS = dict(young_pa=1e5, poisson=.3, thickness_m=.05,
    shear_factor=5/6, width_m=1., length_m=1., supported_length_m=.9,
    physical_skin_gap_m=1e-4, downward_load_pa=.5,
    normal_regularization_pa_per_m=1e6, target_offset_m=.01,
    source_x_left_m=.1, source_y_left_m=.1, target_height_m=1.4,
    source_rotations_and_in_plane_fixed=True, source_y_row_normal_ties=True,
    force_scale_n=.5, moment_scale_nm=.5,
    response_relative_limit=.02, analytic_converged_relative_limit=.001,
    equilibrium_relative_limit=1e-6, dimensional_gap_limit_m=5e-5,
    max_iterations=18, tolerance=1e-9, num_steps=2)


def build(nx):
    model = FEModel(f"d2_guided_partial_foundation_{nx}")
    model.add_material("elastic", INPUTS["young_pa"], INPUTS["poisson"], density=1.)
    for j, y in enumerate((.1, 1.1)):
        for i in range(nx+1):
            model.add_node(1+j*(nx+1)+i, .1+i/nx, y, .0401)
    start = 2*(nx+1)+1
    for node, (x,y) in enumerate(((0.,0.),(1.,0.),(1.,1.4),(0.,1.4)), start):
        model.add_node(node,x,y,0.)
    source_ids=[]
    for i in range(nx):
        eid=i+1
        nodes=(i+1,i+2,nx+i+3,nx+i+2)
        source_ids.append(eid)
        model.add_element(eid,create_shell_element(eid,nodes,"elastic",thickness=.05,
            reference_normal=(0.,0.,1.)))
    target_ids=(nx+1,nx+2)
    for eid,nodes in zip(target_ids,((start,start+1,start+3),(start+1,start+2,start+3))):
        model.add_element(eid,create_shell_element(eid,nodes,"elastic",thickness=.05,
            formulation="e4-pl-s3-v2d",reference_normal=(0.,0.,1.),reference_surface_offset=.01))
    sources=tuple(range(1,start))
    model.add_boundary_condition(BoundaryCondition("source_guides",sources,
        {name:0. for name in ("ux","uy","rx","ry","rz")}))
    model.add_boundary_condition(BoundaryCondition("source_clamp",(1,nx+2),{"uz":0.}))
    model.add_boundary_condition(BoundaryCondition("fixed_target",tuple(range(start,start+4)),
        {name:0. for name in ("ux","uy","uz","rx","ry","rz")}))
    model.apply_boundary_conditions()
    ndof=model.mesh.dof_manager.total_dofs
    free=np.zeros((ndof,nx))
    for i in range(1,nx+1):
        bottom=i+1; top=nx+i+2
        lo=int(model.mesh.dof_manager.get_node_dofs(bottom)[2])
        hi=int(model.mesh.dof_manager.get_node_dofs(top)[2])
        model.add_constraint_equation(terms=((hi,1.),(lo,-1.)),source_id=f"row_tie_{i}")
        free[lo,i-1]=1.;free[hi,i-1]=1.
    load=LoadCase("uniform_half_pascal")
    external=np.zeros(ndof)
    for node in sources:
        i=(node-1)%(nx+1)
        value=-.5/nx*(.25 if i in (0,nx) else .5)
        load.add_nodal_load(node,forces=np.array((0.,0.,value)))
        external[model.mesh.dof_manager.get_node_dofs(node)[2]]=value
    definition=ContactDefinition(surfaces=(ContactSurface("q4_source",tuple(source_ids),"bottom"),
        ContactSurface("s3_fixed_target",target_ids,"top")),rigid_bodies=(),
        interactions=(ContactInteraction("pair","q4_source","s3_fixed_target",1e6,5e-5,
            normal_law="projected_penalty"),))
    settings=fixture(1e6)[2]
    return model,definition,settings,load,external,free


def pressure_integrals(nx,pressure,edges):
    """Exact Q1 physical-plane integration, independent of mortar quadrature."""
    average=(pressure[:nx+1]+pressure[nx+1:])/2
    force=[]
    for left,right in zip(edges[:-1],edges[1:]):
        value=0.
        for i in range(nx):
            a=i/nx;b=(i+1)/nx
            lo=max(a,left,0.);hi=min(b,right,.9)
            if hi>lo:
                slope=(average[i+1]-average[i])/(b-a)
                value+=average[i]*(hi-lo)+slope*((hi-a)**2-(lo-a)**2)/2
        force.append(value)
    return np.asarray(force)


def assess(model,definition,settings,result,nx,external,free,reference):
    u=np.asarray(result.displacements)
    manager=GeneralS3PatchManager(model,definition,settings)
    contact,_,cert=manager.evaluate(u,tangent=False)
    structural,_,trials=_assemble_nonlinear_system(model,u,result.element_states,5,
        tangent=False,kinematics="von_karman",require_full_coordinates=True)
    _discard_nonlinear_state_candidate(trials)
    _discard_nonlinear_state_candidate(result.element_states)
    contact=np.asarray(contact); structural=np.asarray(structural)
    residual=structural+contact-external
    q=np.array([u[model.mesh.dof_manager.get_node_dofs(i+1)[2]] for i in range(nx+1)])
    qtop=np.array([u[model.mesh.dof_manager.get_node_dofs(nx+i+2)[2]] for i in range(nx+1)])
    nodes=np.asarray(cert.source_pressure_node_ids,dtype=int)
    pressure=np.zeros(2*(nx+1))
    pressure[nodes-1]=np.asarray(cert.numerical_pressure_pa)
    support=np.asarray(cert.reference_support_m2)
    expected_positive={1+j*(nx+1)+i for j in (0,1)
        for i in range(int(np.floor(.9*nx))+2)}
    actual_positive=set(nodes[support>0.].tolist())
    edges=np.arange(11,dtype=float)/10
    bins=pressure_integrals(nx,pressure,edges)
    exact_bins=np.array([reference.force_between(a,b) for a,b in zip(edges[:-1],edges[1:])])
    s=np.linspace(0.,1.,1001)
    actual=np.interp(s,np.arange(nx+1)/nx,q)
    exact=np.asarray(reference.displacement(s))
    q_l2=float(np.linalg.norm(actual-exact)/np.linalg.norm(exact))
    total=float(np.sum(bins))
    expected=reference.force_between(0.,1.)
    force_error=abs(total-expected)/expected
    bin_l1=float(np.linalg.norm(bins-exact_bins,1)/np.linalg.norm(exact_bins,1))
    bin_l2=float(np.linalg.norm(bins-exact_bins)/np.linalg.norm(exact_bins))
    # Bilinear surface becomes a tied-row linear curve. Its minima over the
    # represented target overlap occur at nodes or the genuine support boundary.
    represented=np.r_[q[np.arange(nx+1)/nx<=.9],np.interp(.9,np.arange(nx+1)/nx,q)]
    gap_lower=float(1e-4+np.min(represented)-128*np.finfo(float).eps*max(1.,np.max(abs(u))))
    force_scale=.5
    source,target=manager._positions(u)
    work=manager.law.work(source,target,manager.normal_multipliers,tangent=False)
    physical=-np.asarray(work.residual).reshape(-1,3)
    bodies={};start=0
    for name,ids,positions in (("source",manager.law.source_node_ids,source),
                              ("target",manager.law.target_node_ids,target)):
        local=physical[start:start+len(ids)]
        bodies[name]=dict(node_ids=list(ids),physical_contact_force=local.sum(axis=0),
            physical_contact_moment=np.cross(positions,local).sum(axis=0))
        start+=len(ids)
    wrench=guided_wrench_diagnostics(model,u,structural,contact,external,free,
        physical_contact_force=sum((b["physical_contact_force"] for b in bodies.values()),np.zeros(3)),
        physical_contact_moment=sum((b["physical_contact_moment"] for b in bodies.values()),np.zeros(3)),
        origin=np.zeros(3),force_scale_n=force_scale,moment_scale_nm=.5,
        bodies=bodies)
    body_errors=[b[k] for b in wrench["bodies"].values() for k in
        ("balance_relative_force","balance_relative_moment","contact_conversion_max_scaled","structural_internal_max_scaled")]
    wrench_error=max(body_errors+[wrench[k] for k in
        ("constraint_reconstruction_relative_force","balance_relative_force","balance_relative_moment",
         "contact_conversion_max_scaled","structural_internal_max_scaled")])
    equilibrium=float(np.linalg.norm(free.T@residual)/force_scale)
    conversion=abs(total-float(cert.integration_force[2]))/force_scale
    samples=[dict(s_m=float(x),actual_uz_m=float(np.interp(x,np.arange(nx+1)/nx,q)),
        reference_uz_m=float(reference.displacement(x))) for x in (.25,.5,.8,.9,1.)]
    checks=dict(completed=result.status=="completed",finite_law_profile=cert.profile==
        "Q4_S3_PATCH_REFINED_PROJECTED_FINITE_PENALTY_STATIC_DEV_V0",
        displacement_response=q_l2<=.02,integrated_response=force_error<=.02,
        physical_bin_response=bin_l1<=.02 and bin_l2<=.02,
        gap_budget=gap_lower>=-5e-5,pressure_nonnegative=bool(np.all(pressure>=0.)),
        all_positive_support_retained=bool(actual_positive==expected_positive
            and np.all(support>=0.) and np.all(np.asarray(cert.numerical_pressure_pa)[support==0.] == 0.)),
        zero_multipliers=bool(np.all(manager.normal_multipliers==0.)),
        tie_consistency=float(np.max(abs(q-qtop)))<=1e-12,
        equilibrium=equilibrium<=1e-6,both_body_wrench=wrench_error<=1e-6,
        independent_force_conversion=conversion<=1e-6,empty_integrity_bin=abs(bins[-1])<=1e-14)
    return dict(checks=checks,development_checks_met=all(checks.values()),
        metrics=dict(normal_displacement_sampled_l2_relative=q_l2,integrated_contact_force_relative=force_error,
            physical_bin_l1_relative=bin_l1,physical_bin_l2_relative=bin_l2,
            independent_physical_gap_lower_m=gap_lower,equilibrium_relative=equilibrium,
            maximum_wrench_relative=wrench_error,physical_force_conversion_relative=conversion),
        analytic_response_diagnostics=dict(reaction_within_point_one_percent=force_error<=.001,
            sampled_displacement_within_point_one_percent=q_l2<=.001,
            acceptance_status="unassessed: requires meaningful refinement and reference/integration uncertainty enclosure"),
        positive_support_node_ids=sorted(actual_positive),
        displacement_samples=samples,physical_bin_edges_m=edges.tolist(),physical_bin_forces_n=bins.tolist(),
        reference_bin_forces_n=exact_bins.tolist(),wrench=wrench,certificate=cert.to_dict())


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument("--nx",type=int,choices=(79,159),required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    freeze=args.output.with_suffix(".inputs.json")
    snapshot=args.output.with_suffix(".runner.source.py")
    if any(p.exists() for p in (args.output,freeze,snapshot)):raise FileExistsError(args.output)
    model,definition,settings,load,external,free=build(args.nx)
    D=INPUTS["shear_factor"]*INPUTS["young_pa"]/(2*(1+INPUTS["poisson"]))*INPUTS["thickness_m"]
    reference=make_reference(D=D)
    k,_=assemble_stiffness_matrix(model)
    actual_k=free.T@(k@free)
    independent=np.zeros((args.nx,args.nx))
    for cell in range(args.nx):
        for a in (cell,cell+1):
            for b in (cell,cell+1):
                if a and b:independent[a-1,b-1]+=D*args.nx*(1. if a==b else -1.)
    operator_error=float(np.linalg.norm(actual_k-independent)/np.linalg.norm(independent))
    import docs.d1_review_support.d2_guided_partial_foundation_reference as oracle
    package=Path(anysolver.__file__).parent
    record=dict(accepted=False,released=False,nx=args.nx,inputs=INPUTS,
        resource_caps=dict(seconds=180,process_tree_bytes=1073741824),
        environment=dict(python=sys.version,executable=sys.executable,
            platform=platform.platform(),numpy=np.__version__,scipy=scipy.__version__,
            anysolver=str(Path(anysolver.__file__).resolve()),
            thread_controls={key:os.environ.get(key) for key in
                ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS")}),
        reference=reference.summary(),normal_operator_relative_error=operator_error,
        definition=asdict(definition),settings=asdict(settings),
        source={str(p):file_identity(p) for p in (Path(__file__),Path(oracle.__file__))},
        package={str(p.relative_to(package)):file_identity(p)["sha256"] for p in package.rglob("*.py")},
        limits="guided planar fixed-target development; continuum and finite weak-gap models differ; no radial regrade, moving/rim/CCD/general geometry acceptance")
    snapshot.write_bytes(Path(__file__).read_bytes())
    freeze.write_text(json.dumps(record,indent=2,default=json_default)+"\n",encoding="utf-8")
    started=time.perf_counter()
    try:
        if operator_error>1e-10:raise RuntimeError("guided structural operator differs from declared continuum D")
        report=validate_general_contact(model,definition,settings)
        if not report.valid:raise RuntimeError(f"contact admission failed: {report.issues}")
        record["capability_profile"]=report.profile
        result=solve_static_nonlinear(model,load_case=load,contact=definition,contact_settings=settings,
            num_steps=2,max_iterations=18,tolerance=1e-9)
        record.update(status=result.status,failure=result.failure_reason,info=result.info,
            displacements=result.displacements.tolist(),steps=[s.to_dict() for s in result.steps])
        if result.status!="completed":raise RuntimeError("partial-foundation coupled solve did not complete")
        record["assessment"]=assess(model,definition,settings,result,args.nx,external,free,reference)
        record["development_checks_met"]=record["assessment"]["development_checks_met"]
    except Exception as exc:
        record.update(development_checks_met=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    finally:
        record["elapsed_seconds"]=time.perf_counter()-started
        args.output.write_text(json.dumps(record,indent=2,default=json_default)+"\n",encoding="utf-8")
        print(json.dumps({k:record.get(k) for k in ("status","development_checks_met","elapsed_seconds","error")}),flush=True)
    raise SystemExit(0 if record["development_checks_met"] else 1)


if __name__=="__main__":main()
