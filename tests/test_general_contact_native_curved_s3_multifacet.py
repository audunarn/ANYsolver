"""Curved material contact with two connected deformable target facets."""
from hashlib import sha256
from pathlib import Path
import json,os
from math import acos,atan2,ceil,floor,pi
import numpy as np
from numpy.polynomial.legendre import leggauss
from test_general_contact_native_curved_s3_static import _analysis
from test_general_contact_native_surface_bounds import _independent_point
from test_general_contact_native_curved_s3_work import _corners
from native_s3_fixture_replay import restore_native_s3_fixture


def test_curved_multifacet_extension_preserves_single_facet_restart_identity():
    path=Path(__file__).parent/'data/general_contact_native_curved_s3_v2_active.checkpoint'
    owner=_analysis()
    accepted,records,raw=restore_native_s3_fixture(owner,path)
    assert accepted.completed_targets==1 and owner._checkpoint(records)==raw


def test_curved_multifacet_coupled_retained_reactions_and_shared_target():
    owner=_analysis(targets=(1.,),two_facets=True);run=owner.solve()
    output=os.environ.get('CONTACT_APP_RESULT_RECORD')
    if output:
        Path(output+'-multifacet.json').write_text(json.dumps(dict(status=run.status,
            failure=run.failure,completed_targets=run.accepted.completed_targets,
            candidate_evaluations=owner.candidate_evaluations,pair_evaluations=owner.pair_evaluations,
            trial_failures=owner.curved_trial_failures,
            contact=json.loads(run.checkpoint)['records'][-1]['contact'] if run.accepted.completed_targets else None),indent=2))
        Path(output+'-multifacet.checkpoint').write_bytes(run.checkpoint)
    assert run.status=='completed',run.failure
    _verify_coupled_state(owner,run.accepted)
    restored,records=_analysis(targets=(1.,),two_facets=True)._restore(run.checkpoint,run.checkpoint_sha256)
    assert restored.completed_targets==1 and owner._checkpoint(records)==run.checkpoint


def _verify_coupled_state(owner,state):
    assert state.completed_targets==1 and len(owner.pairs)==2
    assert {p.work.shell.element_id for p in owner.pairs}=={21,22}
    assert len(owner.initial.shell_displacement)==24
    contact=state.contact
    assert np.linalg.norm(state.shell_displacement)>0.
    for pair,result in contact.pairs:
        assert result.contact.minimum_gap_m>=-pair.gap_tolerance_m
        assert result.contact.minimum_rim_clearance_m>pair.work.contact.rim_clearance
        if pair.work.shell.element_id==21:
            assert result.contact.minimum_gap_m>0. and result.contact.potential_j==0.
            np.testing.assert_array_equal(result.contact.beam_force_n,0.)
            assert result.tangent.nnz==0
        else:
            assert result.contact.beam_force_n[2]>0.
            assert result.tangent[:42,42:].nnz and result.tangent[42:,:42].nnz
        np.testing.assert_allclose(result.contact.beam_force_n+result.contact.shell_force_n,0.,atol=1e-10)
        np.testing.assert_allclose(result.contact.beam_moment_nm+result.contact.shell_moment_nm,0.,atol=1e-10)
    # Reuse the exact accepted contact candidate. Repeating its quadrature here
    # adds no independent evidence; structural reactions are recovered afresh.
    residual,tangent,_=owner._assemble_structural(state.mechanical,state.shell_displacement,1.,state.native_histories)
    residual+=contact.residual;tangent+=contact.tangent.toarray()
    scaled=residual[:42]/owner.context.scale
    metrics=(np.linalg.norm(scaled[owner.context.equilibrium]),
             np.linalg.norm(scaled[owner.context.compatibility]),np.linalg.norm(residual[42+owner.shell_free]))
    assert tangent.shape==(66,66) and max(metrics)<=owner.equilibrium_tolerance
    # Reactions on all prescribed coordinates must balance the applied tip load.
    sr=residual[42:].reshape(4,6)
    shell_positions=np.array([node.coords() for _,node in sorted(owner.shell_model.mesh.nodes.items())])
    shell_positions+=state.shell_displacement.reshape(4,6)[:,:3]
    root,_,tip=owner.context.nodes[0];load=np.array((0.,0.,-.005))
    force=sr[:,:3].sum(axis=0)+residual[6*root:6*root+3]+load
    moment=np.cross(shell_positions,sr[:,:3]).sum(axis=0)+sr[:,3:].sum(axis=0)
    moment+=np.cross(state.mechanical.positions[root],residual[6*root:6*root+3])+residual[6*root+3:6*root+6]
    moment+=np.cross(state.mechanical.positions[tip],load)
    assert np.linalg.norm(force)/.005<=1e-6
    assert np.linalg.norm(moment)/.010<=1e-6
    # Both local facet blocks map to the same free target vertex. Contact is
    # assembled before solving the retained coupled system, never per-pair solves.
    shared=42+owner.shell_model.mesh.dof_manager.get_node_dofs(5)[2]
    assert np.count_nonzero(tangent[:42,shared]) and np.count_nonzero(tangent[shared,:42])


def test_curved_multifacet_saved_completed_state_reactions_and_exact_restart():
    # Actual completed installed solve retained before a test-only dtype failure.
    # This checks the remaining gates without regrading or repeating that batch.
    path=Path(__file__).parent/'data/general_contact_native_curved_s3_multifacet_v1.checkpoint'
    owner=_analysis(targets=(1.,),two_facets=True)
    accepted,records,raw=restore_native_s3_fixture(owner,path)
    _verify_coupled_state(owner,accepted)
    assert owner._checkpoint(records)==raw


def _independent_material_integral(work,p,low,rotations,u,order=24):
    # Analytic parabola with e2=z, e3=-planar-normal. No production station,
    # surface integration or gap kernel. The reference area is held fixed.
    corners=_corners(work,u)
    normal=np.cross(corners[1]-corners[0],corners[2]-corners[0]);normal/=np.linalg.norm(normal)
    x,w=leggauss(order);lo,hi=work.contact.rule.definition['xi_range']
    al,ar=work.contact.rule.definition['angle_range'];radius=work.contact.radius
    energy=0.;force=np.zeros(3);moment=np.zeros(3)
    for v,weight in zip(x,w):
        xi=(lo+hi)/2+(hi-lo)*v/2;j=np.sqrt(1+.16*xi*xi)
        point=lambda angle:_independent_point(xi,angle+pi/2,radius,p,low,rotations,False)
        p0,pp,ph=point(0.),point(pi),point(pi/2)
        centre=(p0+pp)/2;co=(p0-pp)/2;si=ph-centre
        A=normal@(centre-corners[0]);B=normal@co;C=normal@si
        amplitude=np.hypot(B,C);cuts=[al,ar]
        if amplitude>0. and abs(A)<amplitude:
            phase=atan2(C,B);root=acos(-A/amplitude)
            for initial in (phase-root,phase+root):
                for turn in range(ceil((al-initial)/(2*pi)),floor((ar-initial)/(2*pi))+1):
                    angle=initial+turn*2*pi
                    if al<angle<ar:cuts.append(angle)
        cuts=sorted(cuts)
        for left,right in zip(cuts[:-1],cuts[1:]):
            if normal@(point((left+right)/2)-corners[0])>=0.:continue
            for a,aw in zip(x,w):
                angle=(left+right)/2+(right-left)*a/2
                position=point(angle);gap=normal@(position-corners[0])
                measure=weight*aw*(hi-lo)*(right-left)/4*radius*(j-.4*radius*np.sin(angle)/j**2)
                reaction=work.contact.stiffness*max(0.,-gap)*measure*normal
                energy+=.5*work.contact.stiffness*min(gap,0.)**2*measure
                force+=reaction;moment+=np.cross(position,reaction)
    return energy,force,moment


def test_curved_multifacet_complete_shared_map_and_independent_material_work():
    owner=_analysis(targets=(1.,),two_facets=True)
    pose=owner.initial.mechanical
    u=owner.initial.shell_displacement.copy()
    u[2::6]=.00012
    shared_shell=owner.shell_model.mesh.dof_manager.get_node_dofs(5)[2]
    u[shared_shell]+=1e-7;shared=42+shared_shell
    result=owner._contact(pose,u)
    expected_intervals={21:(-.9,-.1),22:(.1,.9)}
    for pair,row in result.pairs:
        assert pair.work.shell.body_id==7 and pair.work.shell.side=='top'
        assert tuple(pair.work.contact.rule.definition['xi_range'])==expected_intervals[pair.work.shell.element_id]
        assert shared_shell in pair.work.shell_translation_dofs[:,2]
        assert row.contact.beam_force_n[2]>0.
        assert row.contact.minimum_gap_m>=-pair.gap_tolerance_m
        assert row.tangent[:42,shared].nnz and row.tangent[shared,:42].nnz
        oracle=_independent_material_integral(pair.work,pose.positions,pose.position_low,pose.cell_rotations[0],u)
        np.testing.assert_allclose(row.contact.potential_j,oracle[0],rtol=1e-9,atol=1e-12)
        np.testing.assert_allclose(row.contact.beam_force_n,oracle[1],rtol=1e-9,atol=1e-9)
        np.testing.assert_allclose(row.contact.beam_moment_nm,oracle[2],rtol=1e-9,atol=1e-9)
    # Direct local sum is an independent assembly check for this one-beam ordering.
    expected_r=sum((row.residual for _,row in result.pairs),np.zeros(66))
    expected_k=sum((row.tangent.toarray() for _,row in result.pairs),np.zeros((66,66)))
    np.testing.assert_allclose(result.residual,expected_r,rtol=1e-13,atol=1e-13)
    np.testing.assert_allclose(result.tangent.toarray(),expected_k,rtol=1e-13,atol=1e-13)
    d=np.random.default_rng(524).normal(size=66)*.001;errors=[];work_errors=[]
    d[list(owner.context.fixed)]=0.
    for h in (1e-5,2e-6):
        states=[owner.context.advance(pose,sign*h*d[:42]) for sign in (1,-1)]
        values=[owner._contact(s,u+sign*h*d[42:]) for sign,s in zip((1,-1),states)]
        fd=(values[0].residual-values[1].residual)/(2*h)
        error=float(np.linalg.norm(result.tangent@d-fd)/np.linalg.norm(fd));errors.append(error)
        assert error<=1e-5
        energies=[sum(_independent_material_integral(pair.work,s.positions,s.position_low,
            s.cell_rotations[0],u+sign*h*d[42:])[0] for pair in owner.pairs)
            for sign,s in zip((1,-1),states)]
        derivative=(energies[0]-energies[1])/(2*h)
        work_error=float(abs(result.residual@d-derivative)/max(abs(derivative),1e-12))
        work_errors.append(work_error);assert work_error<=1e-5
    # The manufactured compressed pose is local code verification, not an
    # equilibrium state or an admission override of the owner30um gap gate.
    output=os.environ.get('CONTACT_APP_RESULT_RECORD')
    if output:Path(output+'-multifacet-local.json').write_text(json.dumps(dict(
        directional_errors=errors,independent_virtual_work_errors=work_errors,
        pair_force_z=[row.contact.beam_force_n[2] for _,row in result.pairs],
        energy_j=result.contact.potential_j),indent=2))
