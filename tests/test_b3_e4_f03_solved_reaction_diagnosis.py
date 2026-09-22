"""Bounded physical partition of solved classical F03 support reactions.

These are signed KKT and virtual-work checks, not continuum agreement claims.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest
from scipy import sparse
from scipy.sparse.linalg import splu

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling
import _b3_e4_f03_loaded_preflight as loaded


def _shell_wrench(dual, points):
    return np.array((np.sum(dual[::2]), np.sum(dual[1::2]),
                     points[:,0]@dual[1::2]-points[:,1]@dual[::2]))


@pytest.mark.parametrize("topology", ("Q4", "CST-CB"))
@pytest.mark.parametrize("ns", (2,4))
def test_signed_solved_reaction_and_port_partition(topology,ns):
    ny, nb, nm = 8, 8, 4
    model = shell.panel(ns, ny, topology)
    ks = shell.stiffness(model)
    kb = beam.assembled_stiffness(nb)
    cs, cb, _ = line.coupling(model, nb, nm, "P1")
    k = sparse.block_diag((ks, kb), format="csr")
    c = sparse.hstack((-cs, cb), format="csr")
    f = np.r_[np.zeros(model.dof_count), beam.assembled_load(nb, "smooth")]
    supported = np.r_[model.supported, model.dof_count+beam.root_dofs(nb)]
    free = np.setdiff1d(np.arange(k.shape[0]), supported)
    scaled = scaling.build(k, c, f, free, model.dof_count, nb, nm, "P1")
    qfree, lam = scaled.recover(splu(scaled.matrix).solve(scaled.rhs))
    q = np.zeros(k.shape[0]); q[free] = qfree
    qs, qb = q[:model.dof_count], q[model.dof_count:]

    # The separately assembled elastic, port and external terms recover the
    # signed supported covector. Neither a shell slope nor a free beam slope
    # contributes to the prescribed-support wrench.
    shell_elastic = ks@qs
    shell_port = -(cs.T@lam)
    beam_elastic = kb@qb
    beam_port = cb.T@lam
    beam_external = f[model.dof_count:]
    shell_reaction = shell_elastic+shell_port
    beam_reaction = beam_elastic+beam_port-beam_external
    full = k@q+c.T@lam-f
    np.testing.assert_allclose(np.r_[shell_reaction, beam_reaction], full,
                               rtol=5e-12, atol=1e-5)
    assert max(abs(lam)) > 1 and max(abs(shell_port)) > 1
    assert max(abs(beam_port)) > 1
    if ns == 4:
        # Here the four physical sample columns lie strictly away from
        # supported x edges, as they do on the loaded Ns128 panel.
        np.testing.assert_allclose(shell_port[model.supported], 0., atol=1e-9)
        np.testing.assert_allclose(shell_reaction[model.supported],
                                   shell_elastic[model.supported],atol=1e-9)

    # Independent scalar virtual-work difference with a *supported-only*
    # perturbation: the resulting covector must be the reaction, including
    # signed port and applied-load terms.
    support_mode = np.zeros_like(q)
    support_mode[model.supported] = np.linspace(-.3,.4,len(model.supported))
    support_mode[model.dof_count+beam.root_dofs(nb)] = (.2,-.4,.17)
    delta = 1e-7
    def scalar_work(state):
        return float(.5*state@(k@state)+lam@(c@state)-f@state)
    numerical = (scalar_work(q+delta*support_mode)-
                 scalar_work(q-delta*support_mode))/(2*delta)
    np.testing.assert_allclose(numerical,full@support_mode,
                               rtol=5e-7,atol=2e-4)

    nx = 2*ns
    left = np.array([j*(nx+1) for j in range(ny+1)])
    right = left+nx
    grouped = []
    for nodes in (left, right):
        dofs = np.ravel(np.column_stack((2*nodes, 2*nodes+1)))
        grouped.append(_shell_wrench(shell_reaction[dofs], model.nodes[nodes]))
        # Resolve the reaction over two fixed physical y bands, including
        # each nodal force's moment arm about the common global origin.
        lower = model.nodes[nodes,1] < 0
        halves = []
        for mask in (lower, ~lower):
            ids = nodes[mask]
            sub = np.ravel(np.column_stack((2*ids, 2*ids+1)))
            halves.append(_shell_wrench(shell_reaction[sub], model.nodes[ids]))
        np.testing.assert_allclose(np.sum(halves,axis=0),grouped[-1],
                                   rtol=2e-12,atol=1e-5)
        # A prescribed rigid virtual displacement confined to this edge
        # gives its signed resultant and moment about the chosen origin.
        boundary_mode = np.zeros(model.dof_count)
        tx,ty,omega = .12,-.28,.37
        boundary_mode[2*nodes] = tx-omega*model.nodes[nodes,1]
        boundary_mode[2*nodes+1] = ty+omega*model.nodes[nodes,0]
        np.testing.assert_allclose(shell_reaction@boundary_mode,
                                   grouped[-1]@np.array((tx,ty,omega)),
                                   rtol=2e-12,atol=1e-5)
    root = beam.root_dofs(nb)
    grouped.append(beam_reaction[root])

    observed = loaded.recover_solved(model,nb,nm,"P1",4,
                                     ks,kb,cs,cb,k,c,f,free,qfree,lam)
    np.testing.assert_allclose(grouped,observed.support_wrenches,
                               rtol=5e-12,atol=1e-5)
    np.testing.assert_allclose(np.sum(grouped,axis=0)+observed.applied_resultant,
                               0.,atol=1e-5)
    np.testing.assert_allclose(observed.global_balance_scaled,0.,atol=1e-10)

    # Physical port work and nodal adjoints are independent signed views of
    # the same Lagrange term, before any normalized absolute comparison.
    np.testing.assert_allclose(shell_port@qs, -lam@(cs@qs),
                               rtol=5e-12,atol=1e-8)
    np.testing.assert_allclose(beam_port@qb, lam@(cb@qb),
                               rtol=5e-12,atol=1e-8)
    np.testing.assert_allclose(shell_port@qs+beam_port@qb,
                               observed.interface_work_joule,rtol=5e-12,atol=1e-8)
    assert observed.free_force_scaled_max < 1e-8
    assert observed.weak_gap_scaled_max < 1e-9
