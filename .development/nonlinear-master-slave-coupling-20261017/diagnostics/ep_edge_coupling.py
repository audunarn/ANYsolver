"""Slice 3 deliverable 3: direct vs interpolated edge coupling, EP geometry.

Existing EP isolation geometry and repository S355 curve (ep_isolation.py):
L=1.0, W=0.24, t=0.012, shell 2x1, stiffener 10x40 mm at e=+0.04,
fiber plasticity. Direct coupling: beam with 2 elements (nodes on shell
edge nodes). Interpolated counterpart: beam with 3 elements (middle nodes
genuinely interpolated on the edge).

Stages (streamed as JSON, one per line, flush immediately):
  preyield                 -2 kN/node force control, plastic vs elastic,
                            direct and interpolated: lambda=1, zero plastic
                            strain, plastic == elastic control.
  dc_full DIRECT|INTERP    uninterrupted DC uz=-0.20 at the original tip
                            probe (num_steps=12, max_iterations=40,
                            tolerance=1e-8): completion, target error,
                            positive plastic strain, independent reduced
                            residual, constraint postcheck, reactions.
  dc_split DIRECT|INTERP  split at uz=-0.10, resume to -0.20, compare
                            u/lambda/history with the uninterrupted run
                            (same tolerances, no relaxation).
  dc_cancel DIRECT         cancellation during a resumed run: caller restart
                            input deep-unchanged, accepted snapshots only
                            from committed steps, checkpoint still resumes.
"""
from __future__ import annotations

import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from ep_isolation import CS, L, NX, NY, R, W, material, t  # noqa: E402
from anysolver import (  # noqa: E402
    BoundaryCondition,
    FEModel,
    LoadCase,
    create_shell_element,
    solve_static_nonlinear,
)
from anysolver.assembly import build_constraint_transformation  # noqa: E402
from anysolver.control import CancellationToken  # noqa: E402
from anysolver.elements import BeamElement, CoupledBeamShellElement  # noqa: E402
from anysolver.matrix_assembly import (  # noqa: E402
    assemble_load_vector,
    assemble_stiffness_matrix,
)
from anysolver.mesh_gen import InterpolatedBeamShellMPCElement  # noqa: E402
from anysolver.nonlinear_static import (  # noqa: E402
    DisplacementControl,
    _assemble_nonlinear_system,
)

try:  # absent on clean HEAD; corotational candidate uses the rotating map
    from anysolver.corotational import build_nonlinear_rotating_mpc_map  # noqa: E402
except ImportError:  # pragma: no cover - clean-HEAD attribution runs
    build_nonlinear_rotating_mpc_map = None

DC_PARAMS = {"num_steps": 12, "max_iterations": 40, "tolerance": 1.0e-8}
FC_PARAMS = {"num_steps": 6, "max_iterations": 30}


def build_model(coupling: str, scale: float):
    """EP isolation geometry; coupling in {'direct','interp','none'}."""
    m = FEModel(f"ep_edge_{coupling}")
    material(m, scale)
    grid, nid = {}, 1
    for ix, x in enumerate(np.linspace(0.0, L, NX + 1)):
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
    if coupling == "none":
        m.add_boundary_condition(BoundaryCondition(
            "root", [grid[(0, iy)] for iy in range(NY + 1)],
            {k: 0.0 for k in ("ux", "uy", "uz", "rx", "ry", "rz")}))
        m.apply_boundary_conditions()
        lc = LoadCase("tip")
        return m, lc, grid[(NX, 0)]
    n_beam = 2 if coupling == "direct" else 3
    beam_nodes = []
    for ib, xb in enumerate(np.linspace(0.0, L, n_beam + 1)):
        b = 100 + ib
        m.add_node(b, float(xb), -W / 2.0, float(R[2]))
        beam_nodes.append(b)
        sx = xb / (L / NX)
        ix = min(int(np.floor(sx)), NX - 1)
        xi = sx - ix
        masters = [(grid[(ix, 0)], 1.0 - xi), (grid[(ix + 1, 0)], xi)]
        masters = [(n, w) for n, w in masters if w > 1e-12]
        mid = 200 + ib
        if len(masters) == 1:
            m.add_element(mid, CoupledBeamShellElement(mid, b, masters[0][0], "steel", eccentricity=R))
        else:
            weights = np.array([w for _, w in masters])
            m.add_element(mid, InterpolatedBeamShellMPCElement(
                mid, b, [n for n, _ in masters], weights, eccentricity=R))
    for ib in range(n_beam):
        m.add_element(300 + ib, BeamElement(300 + ib, [beam_nodes[ib], beam_nodes[ib + 1]], "steel", dict(CS)))
    m.add_boundary_condition(BoundaryCondition(
        "root", [grid[(0, iy)] for iy in range(NY + 1)],
        {k: 0.0 for k in ("ux", "uy", "uz", "rx", "ry", "rz")}))
    m.apply_boundary_conditions()
    lc = LoadCase("tip")
    probe = grid[(NX, 0)]
    return m, lc, probe


def add_tip_load(m, lc, fz_per_node):
    for iy in range(NY + 1):
        lc.add_nodal_load(grid_node(m, NX, iy), [0, 0, fz_per_node, 0, 0, 0])
    m.add_load_case(lc)


def grid_node(m, ix, iy):
    # nodes were added in the same order as build_model; recover by coordinates
    for node in m.mesh.nodes.values():
        if (abs(node.x - ix * L / NX) < 1e-12 and abs(node.y + W / 2 - iy * W / NY) < 1e-12
                and abs(node.z) < 1e-12):
            return node.id
    raise KeyError((ix, iy))


def alpha_max(states):
    vals = [float(np.max(np.abs(s.get("alpha", 0.0)))) for s in states.values() if isinstance(s, dict)]
    return max(vals, default=0.0)


def independent_residual(model, load_case, u, states, kinematics="corotational"):
    K0, _ = assemble_stiffness_matrix(model)
    F_prop, _ = assemble_load_vector(model, load_case)
    _, _, T, u0, _, _ = build_constraint_transformation(K0, F_prop, model)
    mpc_map = build_nonlinear_rotating_mpc_map(model, T) if kinematics == "corotational" else None
    states_copy = copy.deepcopy(states)
    F_int, _, _ = _assemble_nonlinear_system(
        model, u, states_copy, 5, tangent=False, kinematics=kinematics,
        corotational_tangent="work_conjugate" if kinematics == "corotational" else "auto",
    )
    lam_force = lambda lam: (mpc_map.reduce_force(u, lam * F_prop - F_int) if mpc_map is not None
                             else np.asarray(T.T @ (lam * F_prop - F_int)).reshape(-1))
    ref = (mpc_map.reduce_force(u, F_prop) if mpc_map is not None
           else np.asarray(T.T @ F_prop).reshape(-1))
    ref_norm = max(float(np.linalg.norm(ref)), 1.0)
    return ref_norm, float(np.linalg.norm(lam_force(1.0)))


def uz_of(model, u, probe):
    return float(u[model.mesh.dof_manager.get_node_dofs(probe)[2]])


def stage_preyield():
    out = {"stage": "preyield", "cases": []}
    for coupling in ("direct", "interp"):
        row = {"coupling": coupling}
        for label, scale in (("plastic", 1.0), ("elastic", 1.0e4)):
            m, lc, probe = build_model(coupling, scale)
            add_tip_load(m, lc, -2000.0)
            res = solve_static_nonlinear(m, lc, kinematics="corotational", **FC_PARAMS)
            row[label] = {
                "status": res.status,
                "load_factor": res.load_factor,
                "uz_probe": uz_of(m, res.displacements, probe),
                "alpha_max": alpha_max(res.element_states),
                "max_eq_plastic_strain": [s.max_equivalent_plastic_strain for s in res.steps],
            }
        row["uz_abs_difference"] = abs(row["plastic"]["uz_probe"] - row["elastic"]["uz_probe"])
        out["cases"].append(row)
        print(json.dumps(row), flush=True)
    print(json.dumps(out), flush=True)


def dc_solve(coupling, target, num_steps, **extra):
    m, lc, probe = build_model(coupling, 1.0)
    add_tip_load(m, lc, -2000.0)
    control = DisplacementControl(node_id=probe, dof="uz", target_displacement=target)
    res = solve_static_nonlinear(
        m, lc, control="displacement", displacement_control=control,
        kinematics="corotational", num_steps=num_steps,
        max_iterations=DC_PARAMS["max_iterations"], tolerance=DC_PARAMS["tolerance"],
        emit_restart_checkpoint=True, record_increment_snapshots=True, **extra,
    )
    return m, lc, probe, res


def dc_summary(m, lc, probe, res):
    uz = uz_of(m, res.displacements, probe)
    ref_norm, resid = independent_residual(m, lc, res.displacements, res.element_states)
    reactions = res.steps[-1].support_reactions if res.steps else {}
    return {
        "status": res.status,
        "stop_reason": res.stop_reason,
        "load_factor": res.load_factor,
        "uz_probe": uz,
        "target_error_m": abs(uz - (-0.20)),
        "alpha_max": alpha_max(res.element_states),
        "steps": [s.to_dict() for s in res.steps],
        "snapshot_count": len(res.snapshots),
        "snapshot_control_values": [s.control_value for s in res.snapshots],
        "snapshots_match_steps": (
            [s.control_value for s in res.snapshots] == [s.control_value for s in res.steps]
            and len(res.snapshots) == len(res.steps)
        ),
        "independent_residual_relative": resid / ref_norm,
        "constraint_postcheck": res.info.get("constraint_postcheck", {}),
        "support_reactions": {k: list(v) for k, v in reactions.items()},
        "has_restart_checkpoint": res.restart_checkpoint is not None,
    }


def stage_dc_full(coupling):
    m, lc, probe, res = dc_solve(coupling, -0.20, 12)
    summary = {"stage": "dc_full", "coupling": coupling, **dc_summary(m, lc, probe, res)}
    print(json.dumps(summary), flush=True)


def stage_dc_split(coupling):
    m1, lc1, p1, res1 = dc_solve(coupling, -0.10, 6)
    half = {
        "status": res1.status, "load_factor": res1.load_factor,
        "uz_probe": uz_of(m1, res1.displacements, p1),
        "restart_checkpoint_bytes": len(res1.restart_checkpoint_bytes()),
    }
    print(json.dumps({"stage": "dc_split_half", "coupling": coupling, **half}), flush=True)

    m2, lc2, p2, res2 = dc_solve(coupling, -0.20, 6, restart_checkpoint=res1.restart_checkpoint_bytes())
    m3, lc3, p3, res3 = dc_solve(coupling, -0.20, 12)
    compare = {
        "stage": "dc_split_compare", "coupling": coupling,
        "resumed": {"status": res2.status, "load_factor": res2.load_factor,
                    "uz_probe": uz_of(m2, res2.displacements, p2)},
        "uninterrupted": {"status": res3.status, "load_factor": res3.load_factor,
                          "uz_probe": uz_of(m3, res3.displacements, p3)},
        "displacements_max_abs_diff": float(np.max(np.abs(res2.displacements - res3.displacements))),
        "displacements_exact": bool(np.array_equal(res2.displacements, res3.displacements)),
        "steps_equal": [s.to_dict() for s in res2.steps] == [s.to_dict() for s in res3.steps],
        "load_factor_history_resumed": [s.load_factor for s in res2.steps],
        "load_factor_history_uninterrupted": [s.load_factor for s in res3.steps],
        "restart_bytes_equal": res2.restart_checkpoint_bytes() == res3.restart_checkpoint_bytes(),
    }
    print(json.dumps(compare), flush=True)


def stage_dc_cancel(coupling):
    m1, lc1, p1, res1 = dc_solve(coupling, -0.10, 6)
    ckpt_bytes = res1.restart_checkpoint_bytes()
    ckpt_input = json.loads(ckpt_bytes.decode("utf-8"))
    ckpt_snapshot = copy.deepcopy(ckpt_input)

    token = CancellationToken()
    state = {"steps": 0}

    def cancel_after_two(status):
        state["steps"] += 1
        if state["steps"] >= 2:
            token.cancel("diagnostic cancellation after two status callbacks")

    cancelled = False
    try:
        dc_solve(coupling, -0.20, 6, restart_checkpoint=ckpt_input,
                 cancellation_token=token, status_callback=cancel_after_two)
    except Exception as exc:  # noqa: BLE001
        cancelled = type(exc).__name__ == "SolveCancelled"
        if not cancelled:
            raise
    report = {
        "stage": "dc_cancel", "coupling": coupling,
        "cancelled_raised": cancelled,
        "caller_restart_input_unchanged": _deep_equal_json(ckpt_input, ckpt_snapshot),
    }
    # The same checkpoint must still resume cleanly after the cancelled run.
    m2, lc2, p2, res2 = dc_solve(coupling, -0.20, 6, restart_checkpoint=ckpt_bytes)
    report["checkpoint_still_resumes"] = res2.status
    report["resumed_load_factor"] = res2.load_factor
    report["caller_restart_input_still_unchanged"] = _deep_equal_json(ckpt_input, ckpt_snapshot)
    print(json.dumps(report), flush=True)


def _deep_equal_json(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def stage_ckpt_probe(coupling, control_name, scale, kin="corotational"):
    """Attribute the pre-existing checkpoint emission failure boundary."""
    m, lc, probe = build_model(coupling, float(scale))
    add_tip_load(m, lc, -2000.0)
    kwargs = dict(kinematics=kin, **FC_PARAMS, emit_restart_checkpoint=True)
    if control_name == "dc":
        kwargs.update(
            control="displacement",
            displacement_control=DisplacementControl(node_id=probe, dof="uz", target_displacement=-0.02),
            **{k: v for k, v in DC_PARAMS.items() if k != "num_steps"},
            num_steps=4,
        )
    try:
        res = solve_static_nonlinear(m, lc, **kwargs)
        report = {"stage": "ckpt_probe", "coupling": coupling, "control": control_name,
                  "scale": float(scale), "kin": kin, "status": res.status,
                  "checkpoint_emitted": res.restart_checkpoint is not None}
    except Exception as exc:  # noqa: BLE001
        report = {"stage": "ckpt_probe", "coupling": coupling, "control": control_name,
                  "scale": float(scale), "kin": kin,
                  "error": f"{type(exc).__name__}: {str(exc)[:200]}"}
    print(json.dumps(report), flush=True)


def main():
    stage = sys.argv[1]
    if stage == "preyield":
        stage_preyield()
    elif stage == "dc_full":
        stage_dc_full(sys.argv[2])
    elif stage == "dc_split":
        stage_dc_split(sys.argv[2])
    elif stage == "dc_cancel":
        stage_dc_cancel(sys.argv[2])
    elif stage == "ckpt_probe":
        stage_ckpt_probe(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else "corotational")
    else:
        raise SystemExit(f"unknown stage {stage!r}")


if __name__ == "__main__":
    main()
