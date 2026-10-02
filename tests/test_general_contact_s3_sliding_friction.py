"""Independent material-convection, work and coupled facet-crossing checks."""
import copy
from dataclasses import replace

import numpy as np
import pytest
from scipy import sparse

from anysolver import BoundaryCondition, solve_static_nonlinear
from anysolver.general_contact import ContactPathControl, ContactPathProgram
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.s3_sliding_friction import (
    S3SlidingFrictionSettings, S3SlidingFrictionManager,
)
from test_general_contact_s3_friction_static import _case, _mode


def _manager():
    model, definition, settings, _fixed = _case()
    friction = S3SlidingFrictionSettings(.3, 1000., (2e-7,)*42, 100)
    normal = GeneralS3PatchManager(model, definition, settings)
    return model, definition, settings, friction, S3SlidingFrictionManager(model, normal, friction)


def _affine(model, matrix):
    """Independent nodal realization of an affine physical-skin motion."""
    u = np.zeros(model.mesh.dof_manager.total_dofs)
    # Explicit fixture coordinates, avoiding production geometry as an oracle.
    xy = ((.2,.2),(.6,.2),(.2,.6),(0,0),(1,0),(0,1),(1,1))
    for node, position in enumerate(xy, 1):
        dofs = model.mesh.dof_manager.get_node_dofs(node)
        u[dofs[:2]] = (matrix-np.eye(2))@position
    return u


def test_anchor_convection_stretch_shear_and_no_same_pose_commit_force_jump():
    model, _d, _s, _f, manager = _manager()
    z, x, y = (_mode(model,(1,2,3),axis) for axis in (2,0,1))
    pressed = -.02*z
    manager.commit(manager.prepare_commit(pressed))
    before = manager.checkpoint_state()
    for F in (np.diag((1.4, 1.2)), np.array(((1.2,.25),(.1,1.3)))):
        u = pressed+_affine(model,F)
        force, _states, records = manager._friction(u)
        np.testing.assert_allclose(force,0,atol=2e-13)
        assert all(np.linalg.norm(r["traction_pa"]) < 2e-12 for r in records)
        # A rigid-frame-only reprojected-anchor rule would add P(I-F)delta.
        assert np.linalg.norm((np.eye(2)-F)@np.array((.1,.04))) > .01
    assert manager.checkpoint_state() == before
    u = pressed+.0002*x+.0003*y
    force = manager._friction(u)[0]
    np.testing.assert_allclose(force@x,.08*1000*.0002,atol=1e-12)
    np.testing.assert_allclose(force@y,.08*1000*.0003,atol=1e-12)
    manager.commit(manager.prepare_commit(u))
    np.testing.assert_allclose(manager._friction(u)[0],force,atol=1e-12)
    # Nonzero retained elastic gap convects through actual target strain too.
    F = np.array(((1.1,.05),(.02,1.1)))
    transformed = pressed+_affine(model,F)+(.0002*F[:,0]+.0003*F[:,1])[0]*x \
                  +(.0002*F[:,0]+.0003*F[:,1])[1]*y
    records = manager._friction(transformed)[2]
    for r in records:
        np.testing.assert_allclose(r["traction_pa"][:2],-1000*(F@np.array((.0002,.0003))),atol=1e-11)


def test_anchor_facet_crossing_work_wrench_reversal_and_release():
    model, _d, _s, _f, manager = _manager()
    x,y,z = (_mode(model,(1,2,3),a) for a in (0,1,2))
    press = -.02*z
    manager.commit(manager.prepare_commit(press))
    u = press+.39*x+.02*y
    force, histories, records = manager._friction(u)
    assert {h.target_element for h in histories} == {2,3}
    assert {r["branch"] for r in records} == {"slip"}
    # Independent flat uniform normal gap p=1000*.005 and Coulomb cap=1.5 Pa.
    np.testing.assert_allclose(force@x,.08*1.5*.39/np.hypot(.39,.02),rtol=1e-10)
    assert sum(r["dissipation_increment_j"] for r in records) > 0
    for r in records:
        assert r["return_storage_drop_j"] == pytest.approx(
            r["dissipation_increment_j"]+r["return_projection_loss_j"],abs=1e-12)
    for axis in range(3):
        assert abs(force@_mode(model,range(1,8),axis)) < 1e-11
    # Rotate all current physical points; include shell offset in the independent
    # nodal translation. Full force map must do no common rigid-spin work.
    positions = ((.2+.39,.2+.02,.045),(.6+.39,.2+.02,.045),(.2+.39,.6+.02,.045),
                 (0,0,0),(1,0,0),(0,1,0),(1,1,0))
    for omega in np.eye(3):
        spin = np.zeros(42)
        for node, pos in enumerate(positions,1):
            dofs = model.mesh.dof_manager.get_node_dofs(node)
            spin[dofs[:3]] = np.cross(omega,pos)
            spin[dofs[3:6]] = omega
        assert abs(force@spin) < 1e-11
    manager.commit(manager.prepare_commit(u))
    np.testing.assert_allclose(manager._friction(u)[0],force,atol=3e-12)
    reverse = manager.prepare_commit(press+.385*x+.02*y)
    assert reverse[2]["dissipation_increment_j"] >= 0
    opened = manager.prepare_commit(.385*x+.02*y)
    assert set(opened[2]["branch"]) == {"open"}
    assert opened[2]["released_storage_j"] > 0
    manager.commit(opened)
    assert set(manager.prepare_commit(press+.385*x+.02*y)[2]["branch"]) == {"activation"}


def test_anchor_pressure_tangent_and_admitted_deformable_target_direction():
    model, _d, _s, _f, manager = _manager()
    x,y,z = (_mode(model,(1,2,3),a) for a in (0,1,2))
    press = -.02*z
    manager.commit(manager.prepare_commit(press))
    # Restrict derivative columns to the admitted planar deformation manifold.
    active = [model.mesh.dof_manager.get_node_dofs(n)[a] for n in range(1,8) for a in (0,1)]
    active += [model.mesh.dof_manager.get_node_dofs(n)[2] for n in (1,2,3)]
    T = sparse.coo_matrix((np.ones(len(active)),(active,range(len(active)))),shape=(42,len(active)))
    manager.restrict_tangent_to_reduced_variations(T)
    u = press+.39*x+.02*y
    force,K,_certificate = manager.evaluate(u)
    normal_K = manager.normal.evaluate(u)[1]
    assert float(x@((K-normal_K)@z)) == pytest.approx(
        -.08*.3*1000*.39/np.hypot(.39,.02),rel=2e-7)
    direction = .01*x+.003*z+.02*_affine(model,np.array(((1.1,.2),(.05,1.03))))
    for h in (1e-4,2e-5):
        fd = (manager.evaluate(u+h*direction,tangent=False)[0]
              -manager.evaluate(u-h*direction,tangent=False)[0])/(2*h)
        error = np.linalg.norm(K@direction-fd)/max(np.linalg.norm(fd),1e-12)
        assert error <= 1e-5
    assert np.all(np.isfinite(force))


def test_real_deformable_target_crossing_history_and_split_restart():
    model, definition, settings, friction, _manager_unused = _manager()
    model.add_boundary_condition(BoundaryCondition("target_plane",(4,5,6,7),
        {d:0 for d in ("uz","rx","ry","rz")}))
    model.add_boundary_condition(BoundaryCondition("target_origin",(4,),{"ux":0,"uy":0}))
    model.add_boundary_condition(BoundaryCondition("target_orientation",(5,),{"uy":0}))
    model.add_boundary_condition(BoundaryCondition("source_guide",(1,2,3),
        {d:0 for d in ("uy","rx","ry","rz")}))
    program = ContactPathProgram((ContactPathControl.node(1,"ux"),ContactPathControl.node(1,"uz")),
        ((0,0),(0,-.02),(.0002,-.02),(.39,-.02),(.385,-.02),(.385,0),(.385,-.02)),1)
    kwargs = dict(model=model,contact=definition,contact_settings=settings,contact_friction=friction,
        contact_path_program=program,max_iterations=18,tolerance=1e-8,
        emit_restart_checkpoint=True,record_increment_snapshots=True)
    full = solve_static_nonlinear(**kwargs)
    assert full.status == "completed", full.info
    history = full.info["force_displacement_history"]
    assert set(history[0]["friction"]["branch"]) == {"activation"}
    assert 3 in history[2]["friction"]["target_elements"]
    assert set(history[2]["friction"]["branch"]) == {"slip"}
    assert set(history[4]["friction"]["branch"]) == {"open"}
    assert set(history[5]["friction"]["branch"]) == {"activation"}
    assert all(r["friction"]["dissipation_increment_j"] >= 0 for r in history)
    moved = full.snapshots[2].displacements
    assert max(abs(moved[model.mesh.dof_manager.get_node_dofs(n)[0]]) for n in (5,6,7)) > 1e-8
    half = solve_static_nonlinear(max_load_factor=.5,**kwargs)
    resumed = solve_static_nonlinear(restart_checkpoint=half.to_restart_checkpoint(),**kwargs)
    assert resumed.status == "completed", resumed.info
    np.testing.assert_allclose(resumed.displacements,full.displacements,rtol=1e-7,atol=1e-9)
    assert resumed.info["force_displacement_history"] == history
    with pytest.raises(ValueError,match="contract|fingerprint|incompatible"):
        solve_static_nonlinear(restart_checkpoint=half.to_restart_checkpoint(),
            **{**kwargs,"contact_friction":replace(friction,friction_coefficient=.4)})


def test_invalid_coverage_and_checkpoint_restore_are_atomic():
    model, _d, _s, _f, manager = _manager()
    old = manager.checkpoint_state()
    with pytest.raises(ValueError,match="target patch"):
        manager.prepare_commit(2*_mode(model,(1,2,3),0))
    assert manager.checkpoint_state() == old
    u = -.02*_mode(model,(1,2,3),2)
    manager.commit(manager.prepare_commit(u))
    state = copy.deepcopy(manager.checkpoint_state())
    state["history"][0]["target_element"] = 77
    before = manager.checkpoint_state()
    with pytest.raises(ValueError,match="outside"):
        manager.restore(state,u)
    assert manager.checkpoint_state() == before
    state=copy.deepcopy(before)
    state["history"][0]["stored_energy_Pa_m"] = 1.
    with pytest.raises(ValueError,match="elastic storage"):
        manager.restore(state,u)
    assert manager.checkpoint_state() == before


def test_zero_pressure_retains_zero_gap_anchor_and_labels_projection_loss(monkeypatch):
    from types import SimpleNamespace
    model, _d, _s, _f, manager = _manager()
    x,z=(_mode(model,(1,2,3),a) for a in (0,2))
    press=-.02*z
    manager.commit(manager.prepare_commit(press))
    manager.commit(manager.prepare_commit(press+.0003*x))
    old=manager.checkpoint_state()
    # Independent limiting pressure fixture; production geometry/anchor mechanics
    # remain active. This checks p=0 history, not admission of a different normal law.
    monkeypatch.setattr(manager.normal.law,"evaluate",lambda *_a: SimpleNamespace(pressure=np.zeros(3)))
    force,states,records=manager._friction(press+.0003*x)
    np.testing.assert_allclose(force,0,atol=1e-13)
    assert all(s.target_element is not None and s.stored_energy_Pa_m < 1e-25 for s in states)
    assert all(r["branch"]=="slip" and r["dissipation_increment_j"]==0 for r in records)
    assert sum(r["return_projection_loss_j"] for r in records) == pytest.approx(.08*.5*1000*.0003**2)
    assert manager.checkpoint_state()==old


def test_retained_gap_co_stretch_effect_vanishes_with_regularization_refinement():
    # The spatial interacting-gap model can return under common affine stretch
    # of a *nonzero* penalty gap. This is not rigid objectivity failure; expose its
    # finite-regularization consequence instead of calling it physical slip truth.
    dissipation=[]
    for kt in (1000.,4000.):
        model,definition,settings,friction,_unused=_manager()
        manager=S3SlidingFrictionManager(model,GeneralS3PatchManager(model,definition,settings),
            replace(friction,tangential_stiffness_Pa_per_m=kt))
        x,z=(_mode(model,(1,2,3),a) for a in (0,2))
        press=-.02*z
        manager.commit(manager.prepare_commit(press))
        initial=.9*1.5/kt
        manager.commit(manager.prepare_commit(press+initial*x))
        F=np.diag((1.2,1.1))
        candidate=manager.prepare_commit(press+_affine(model,F)+1.2*initial*x)
        assert set(candidate[2]["branch"])=={"slip"}
        expected=.08*1.5*(1.2*.9-1)*1.5/kt
        assert candidate[2]["dissipation_increment_j"]==pytest.approx(expected,rel=1e-9)
        dissipation.append(candidate[2]["dissipation_increment_j"])
    assert dissipation[0]/dissipation[1]==pytest.approx(4.,rel=1e-9)


def test_seam_roundoff_ownership_wrench_and_one_sided_residual():
    model, _d, _s, _f, manager = _manager()
    x,z = (_mode(model,(1,2,3),a) for a in (0,2))
    press = -.02*z
    manager.commit(manager.prepare_commit(press))
    u = press+(1-11/15+.0015)*x  # Two quadrature return points lie on x+y=1.
    f0,_h,records = manager._friction(u)
    assert sum(r["sliding_seam"] for r in records) == 2
    assert all(r["target_element"]==2 for r in records)
    assert max(np.linalg.norm(r["traction_pa"]) for r in records) <= 1.5+1e-12
    with pytest.raises(ValueError,match="seam/rim generalized tangent"):
        manager.evaluate(u)
    # Independent moving-load shape derivative on either side of the diagonal:
    # force density is constant; nodal shape gradients change, the force does not jump.
    for side in (-1,1):
        slopes=[]
        for h in (1e-5,1e-6):
            slopes.append((manager._friction(u+side*h*x)[0]-f0)/(side*h))
        np.testing.assert_allclose(slopes[0],slopes[1],rtol=1e-7,atol=1e-8)
    # The normal work derivative is one global patch derivative at either facet,
    # including a virtual apex motion that leaves the planar admission manifold.
    corners,n,_frame,_origin = manager._patch(u)
    Dn = manager._normal_variation(corners,n)
    point = manager.points[1]
    for element,bary in ((2,(0.,.73,.27)),(3,(.73,0.,.27))):
        # Use identical coordinates on the shared material edge, without production lookup.
        e,De,_anchor = manager._work(point,u,element,bary,n,Dn)
        direction = np.zeros(42)
        direction[model.mesh.dof_manager.get_node_dofs(7)[2]] = 1
        h=1e-6
        def gap(delta):
            pose=u+delta*direction
            cs,ns,_fs,_os=manager._patch(pose,validate=False)
            xs=np.asarray(point.barycentric)@point.adapter.current_positions(pose)
            ys=np.asarray(bary)@cs[element]
            return (np.eye(3)-np.outer(ns,ns))@(xs-ys)
        np.testing.assert_allclose(De@direction,(gap(h)-gap(-h))/(2*h),rtol=1e-8,atol=1e-9)
