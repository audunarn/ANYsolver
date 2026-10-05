"""Physical point-footprint work and balance with retained native B3 state."""

import numpy as np
import pytest

from scripts.b3_e4_f04_native_rigid_footprint_comparator import assemble, solve
from scripts.generate_b3_e4_ccx_3d_footprint_feasibility import footprint_rows
from scripts._b3_e4_f03_shell_finite_pose_candidate import reference_nodes


def test_native_nodal_footprint_has_exact_external_reference_rows_and_chart():
    reference=assemble("Q4",4)
    shell_size=6*reference.shell.panel.node_count
    expected=np.zeros_like(reference.constraint_jacobian)
    beam_node=reference.beam.n_half_cells//2
    for i,row in enumerate(footprint_rows(+1)):
        for node,dof,coefficient in row:
            column=(6*(node-1)+dof-1 if node<=45 else
                    shell_size+6*beam_node+dof-1)
            expected[i,column]+=coefficient
    np.testing.assert_allclose(reference.constraint_jacobian,expected,
                               rtol=0,atol=1e-14)
    direction=np.zeros(reference.primal_tangent.shape[0])
    direction[6*reference.shell_nodes[0]:6*reference.shell_nodes[0]+3]=(
        .17,-.23,.31)
    direction[shell_size+6*beam_node:shell_size+6*beam_node+6]=(
        -.29,.13,-.07,.19,-.11,.37)
    state=reference.beam.context.initial.mechanical
    samples=reference_nodes(reference.shell.panel)[list(reference.shell_nodes)]

    def gap(sign):
        beam_step=sign*direction[shell_size:]
        moved=reference.beam.context.advance(state,beam_step)
        bh,bl,frame=reference.port.pose_pair(moved)
        shell_motion=sign*direction[:shell_size].reshape(-1,6)[
            list(reference.shell_nodes),:3]
        return np.concatenate([
            frame.T@(point+delta-bh-bl)-offset
            for point,delta,offset in zip(samples,shell_motion,
                                          reference.sample_offsets)])

    h=1e-6
    np.testing.assert_allclose((gap(h)-gap(-h))/(2*h),
                               reference.constraint_jacobian@direction,
                               rtol=1e-9,atol=2e-10)
    assert np.linalg.norm(gap(0.))<1e-14


@pytest.mark.parametrize("topology",("Q4","S3-V2D"))
def test_native_footprint_transfers_torque_and_preserves_balance(topology):
    result=solve(assemble(topology,4))
    assert result["tip_rx_rad"]>0.
    assert result["scaled_equation_residual"]<1e-10
    assert result["weak_gap_norm_m"]<1e-12
    np.testing.assert_allclose(result["total_force_n"],0.,rtol=0,atol=1e-8)
    np.testing.assert_allclose(result["total_moment_origin_nm"],
                               (-100.,0.,0.),rtol=0,atol=1e-8)
    assert result["external_work_j"]==pytest.approx(
        result["quadratic_internal_work_j"],rel=1e-9,abs=1e-10)
