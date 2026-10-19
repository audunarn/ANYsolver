"""Slice 3 convergence study (reproduces the numbers in HANDOVER.md section 4).

Cantilever Q4 shell strip L=1.0, W=0.24, t=0.012, root clamped, centre-line
beam stiffener (10 x 40 mm rectangle) at eccentricity +0.04 z, coupled by
CoupledBeamShellElement (beam node on a shell node) or
InterpolatedBeamShellMPCElement (bilinear weights) otherwise.

Usage (from C:/Github/ANYsolver):
  python <this file> linear       # linear static: R1..R5, M1..M5, P1..P3
  python <this file> nl_small     # corotational 12 kN (~2.5 deg): R1..R3
  python <this file> nl_finite    # corotational 140 kN (~28 deg): M1..M3, P1..P3
"""
import sys
import time

import numpy as np
from scipy.sparse.linalg import spsolve

from anysolver import BoundaryCondition, FEModel, LoadCase, create_shell_element, solve_static_nonlinear
from anysolver.assembly import build_constraint_transformation
from anysolver.elements import BeamElement, CoupledBeamShellElement
from anysolver.matrix_assembly import assemble_load_vector, assemble_stiffness_matrix
from anysolver.mesh_gen import InterpolatedBeamShellMPCElement

CS = {"area": 0.01 * 0.04, "Iy": 0.01 * 0.04**3 / 12.0, "Iz": 0.04 * 0.01**3 / 12.0, "J": 1.0e-8}

MESHES = {
    # half-density beam (n_beam = nx/2): beam nodes coincide with every 2nd shell row
    "R1": (4, 1, 2), "R2": (8, 2, 4), "R3": (16, 4, 8), "R4": (32, 8, 16), "R5": (64, 16, 32),
    # equal density (n_beam = nx)
    "M1": (4, 1, 4), "M2": (8, 2, 8), "M3": (16, 4, 16), "M4": (32, 8, 32), "M5": (64, 16, 64),
    # non-matching (n_beam = 1.5 nx): genuinely interpolated couplings
    "P1": (6, 2, 9), "P2": (10, 3, 15), "P3": (16, 4, 24),
}


def build(nx, ny, n_beam, total_fz):
    L, W, t = 1.0, 0.24, 0.012
    r = np.array([0.0, 0.0, 0.04])
    m = FEModel(f"stiffened_{nx}x{ny}_b{n_beam}")
    m.add_material("steel", 2.1e11, 0.3, density=7850.0)
    grid, nid = {}, 1
    for ix, x in enumerate(np.linspace(0.0, L, nx + 1)):
        for iy, y in enumerate(np.linspace(-W / 2, W / 2, ny + 1)):
            m.add_node(nid, float(x), float(y), 0.0)
            grid[(ix, iy)] = nid
            nid += 1
    eid = 1
    for ix in range(nx):
        for iy in range(ny):
            m.add_element(eid, create_shell_element(
                eid, [grid[(ix, iy)], grid[(ix + 1, iy)], grid[(ix + 1, iy + 1)], grid[(ix, iy + 1)]],
                "steel", thickness=t))
            eid += 1
    beam_nodes = []
    for ib, xb in enumerate(np.linspace(0.0, L, n_beam + 1)):
        b = 10000 + ib
        m.add_node(b, float(xb), 0.0, float(r[2]))
        beam_nodes.append(b)
        sx = xb / (L / nx)
        ix = min(int(np.floor(sx)), nx - 1)
        xix = sx - ix
        sy = 0.5 * ny
        iy = min(int(np.floor(sy)), ny - 1)
        xiy = sy - iy
        cand = [(grid[(ix, iy)], (1 - xix) * (1 - xiy)), (grid[(ix + 1, iy)], xix * (1 - xiy)),
                (grid[(ix + 1, iy + 1)], xix * xiy), (grid[(ix, iy + 1)], (1 - xix) * xiy)]
        masters = [n for n, w in cand if w > 1e-12]
        weights = np.array([w for n, w in cand if w > 1e-12])
        mid = 20000 + ib
        if len(masters) == 1:
            m.add_element(mid, CoupledBeamShellElement(mid, b, masters[0], "steel", eccentricity=r))
        else:
            m.add_element(mid, InterpolatedBeamShellMPCElement(mid, b, masters, weights, eccentricity=r))
    for ib in range(n_beam):
        m.add_element(30000 + ib, BeamElement(30000 + ib, [beam_nodes[ib], beam_nodes[ib + 1]], "steel", dict(CS)))
    m.add_boundary_condition(BoundaryCondition(
        "root", [grid[(0, iy)] for iy in range(ny + 1)], {k: 0.0 for k in ("ux", "uy", "uz", "rx", "ry", "rz")}))
    m.apply_boundary_conditions()
    lc = LoadCase("tip")
    for iy in range(ny + 1):
        w = 0.5 if iy in (0, ny) else 1.0
        lc.add_nodal_load(grid[(nx, iy)], [0.0, 0.0, total_fz * w / ny, 0.0, 0.0, 0.0])
    m.add_load_case(lc)
    return m, lc, beam_nodes[-1]


def tip(m, u, node):
    d = m.mesh.dof_manager.get_node_dofs(node)
    return float(u[d[0]]), float(u[d[2]]), float(np.rad2deg(abs(u[d[4]])))


def linear(names):
    for name in names:
        m, lc, node = build(*MESHES[name], total_fz=-12000.0)
        K, _ = assemble_stiffness_matrix(m)
        F, _ = assemble_load_vector(m, lc)
        Kr, Fr, T, u0, _, _ = build_constraint_transformation(K, F, m)
        u = np.asarray(T @ spsolve(Kr.tocsc(), Fr) + u0).reshape(-1)
        ux, uz, ry = tip(m, u, node)
        print(f"{name}: uz={uz:.6f} ry_deg={ry:.6f}", flush=True)


def nonlinear(names, total_fz):
    for name in names:
        t0 = time.perf_counter()
        m, lc, node = build(*MESHES[name], total_fz=total_fz)
        res = solve_static_nonlinear(m, lc, kinematics="corotational", num_steps=4, max_iterations=25)
        ux, uz, ry = tip(m, res.displacements, node)
        print(f"{name}: conv={res.converged} uz={uz:.6f} ux={ux:.6f} ry_deg={ry:.4f} "
              f"dt={time.perf_counter() - t0:.2f}s", flush=True)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "linear"
    if mode == "linear":
        linear(["R1", "R2", "R3", "R4", "R5", "M1", "M2", "M3", "M4", "M5", "P1", "P2", "P3"])
    elif mode == "nl_small":
        nonlinear(["R1", "R2", "R3"], -12000.0)
    elif mode == "nl_finite":
        nonlinear(["M1", "M2", "M3", "P1", "P2", "P3"], -140000.0)
    else:
        raise SystemExit(f"unknown mode {mode!r}")
