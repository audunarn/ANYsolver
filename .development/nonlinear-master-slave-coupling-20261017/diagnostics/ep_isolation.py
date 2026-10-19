"""Isolate the 'plastic stiffer than elastic' anomaly.

Matrix: {shell_only, coupled} x {corotational, von_karman} x {elastic(yield x1e4), plastic}
Plus beam-only fiber cantilever (no shell) to isolate the fiber section.
"""
import sys
import numpy as np
from anymaterial import DNVC208MaterialCurve
from anysolver import BoundaryCondition, FEModel, LoadCase, create_shell_element, solve_static_nonlinear
from anysolver.elements import BeamElement, CoupledBeamShellElement

L, W, t = 1.0, 0.24, 0.012
NX, NY = 2, 1
R = np.array([0.0, 0.0, 0.04])
CS = {"area": 4e-4, "Iy": 0.01 * 0.04**3 / 12, "Iz": 0.04 * 0.01**3 / 12,
      "J": 1e-8, "b": 0.01, "h": 0.04, "fiber_plasticity": True}


def material(model, scale):
    from anysolver.material_curves import DNVC208MaterialCurve as C, dnv_c208_steel_curve
    base = dnv_c208_steel_curve("S355", 0.012).as_dict()
    hc = C(base["sigma_prop"] * scale, base["sigma_yield"] * scale, base["sigma_yield_2"] * scale,
           base["eps_p_y1"], base["eps_p_y2"], base["K"] * scale, base["n"])
    model.add_material("steel", 2.1e11, 0.3, density=7850.0,
                       yield_stress=base["sigma_yield"] * scale, hardening_curve=hc)


def shell_model(scale, coupled, fz):
    m = FEModel("iso")
    material(m, scale)
    grid = {}
    nid = 1
    for ix, x in enumerate(np.linspace(0, L, NX + 1)):
        for iy, y in enumerate(np.linspace(-W / 2, W / 2, NY + 1)):
            m.add_node(nid, float(x), float(y), 0.0)
            grid[(ix, iy)] = nid
            nid += 1
    eid = 1
    for ix in range(NX):
        for iy in range(NY):
            m.add_element(eid, create_shell_element(
                eid, [grid[(ix, iy)], grid[(ix + 1, iy)], grid[(ix + 1, iy + 1)], grid[(ix, iy + 1)]],
                "steel", thickness=t))
            eid += 1
    probe = grid[(NX, 0)]
    if coupled:
        bn = []
        for ix in range(NX + 1):
            b = 100 + ix
            mid = grid[(ix, 0)]
            mn = m.mesh.get_node(mid)
            m.add_node(b, mn.x, mn.y, mn.z + R[2])
            bn.append(b)
            m.add_element(200 + ix, CoupledBeamShellElement(200 + ix, b, mid, "steel", eccentricity=R))
        for ix in range(NX):
            m.add_element(300 + ix, BeamElement(300 + ix, [bn[ix], bn[ix + 1]], "steel", dict(CS)))
    m.add_boundary_condition(BoundaryCondition(
        "root", [grid[(0, iy)] for iy in range(NY + 1)],
        {k: 0.0 for k in ("ux", "uy", "uz", "rx", "ry", "rz")}))
    m.apply_boundary_conditions()
    lc = LoadCase("tip")
    for iy in range(NY + 1):
        lc.add_nodal_load(grid[(NX, iy)], [0, 0, fz, 0, 0, 0])
    m.add_load_case(lc)
    return m, lc, probe


def beam_model(scale, fz):
    m = FEModel("beam")
    material(m, scale)
    n = 4
    for i in range(n + 1):
        m.add_node(1 + i, L * i / n, 0.0, 0.0)
    for i in range(n):
        m.add_element(10 + i, BeamElement(10 + i, [1 + i, 2 + i], "steel", dict(CS)))
    m.add_boundary_condition(BoundaryCondition(
        "root", [1], {k: 0.0 for k in ("ux", "uy", "uz", "rx", "ry", "rz")}))
    m.apply_boundary_conditions()
    lc = LoadCase("tip")
    lc.add_nodal_load(n + 1, [0, 0, fz, 0, 0, 0])
    m.add_load_case(lc)
    return m, lc, n + 1


def run(builder, kin, steps=4):
    m, lc, probe = builder()
    try:
        res = solve_static_nonlinear(m, lc, kinematics=kin, num_steps=steps, max_iterations=30)
    except Exception as exc:  # noqa: BLE001
        return f"ERROR {type(exc).__name__}: {str(exc)[:90]}"
    d = m.mesh.dof_manager.get_node_dofs(probe)
    amax = max((float(np.max(np.abs(s.get("alpha", 0.0)))) for s in res.element_states.values()
                if isinstance(s, dict)), default=0.0)
    return f"conv={res.converged} uz={res.displacements[d[2]]:+.5f} alpha_max={amax:.2e}"


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    cases = []
    if which in ("all", "beam"):
        for kin in ("von_karman", "corotational"):
            for lab, s in (("elastic", 1e4), ("plastic", 1.0)):
                cases.append((f"beam-only  {kin:12s} {lab}", lambda s=s: beam_model(s, -2500.0), kin))
    if which in ("all", "shell"):
        for kin in ("von_karman", "corotational"):
            for lab, s in (("elastic", 1e4), ("plastic", 1.0)):
                cases.append((f"shell-only {kin:12s} {lab}", lambda s=s: shell_model(s, False, -6000.0), kin))
    if which in ("all", "coupled"):
        for kin in ("von_karman", "corotational"):
            for lab, s in (("elastic", 1e4), ("plastic", 1.0)):
                cases.append((f"coupled    {kin:12s} {lab}", lambda s=s: shell_model(s, True, -35000.0), kin))
    for label, b, kin in cases:
        print(label, "->", run(b, kin), flush=True)
