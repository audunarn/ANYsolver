"""Read saved arrays only. No product/reference imports, factorization or solve."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent
NATIVE = ROOT/"r8-bl5-native-p0-family-v1"
EXTERNAL = ROOT/"r8-bl5-external-p0-family-v1"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wrench(nodes, field, origin):
    force = np.sum([field[n][:3] for n in field], axis=0)
    moment = np.sum([field[n][3:]+np.cross(nodes[n]-origin, field[n][:3]) for n in field], axis=0)
    return np.r_[force, moment]


def projection(a, b):
    square = float(b@b)
    return None if square == 0. else float(a@b/square)


def norm(v):
    return float(np.sqrt(v@v))


distance = read(NATIVE/"fixed-distance-transfer.json")
result = {"classification": "saved-data root support decomposition, no new mechanics or qualification",
          "script_sha256": sha(__file__), "component_order": ["Fx_N", "Fy_N", "Fz_N", "Mx_Nm", "My_Nm", "Mz_Nm"],
          "difference_sign": "native minus external", "norm_scale": "Lref1m: forces and M/Lref in N",
          "root_equation": "R = mask*(G+C^Tlambda-L); root L=0; deltaR = deltaG+deltaC on fixed components",
          "projection_warning": "Signed projection fractions are algebraic attribution along deltaR, not causal percentages; cancellation can exceed100%.",
          "cases": [], "bound_inputs": {}}
for nx in (16, 32, 64):
    nr, er = NATIVE/f"n{nx}", EXTERNAL/f"n{nx}"
    layout = read(nr/"layout.json")
    inputs = read(nr/"inputs.json")
    typed = layout["typed_physical_nodes"]
    index = {(row["domain"], row["native_node"]): row["q_offset"] for row in typed}
    xyz = np.array(inputs["xyz_m"])
    ns = len(layout["shell_node_ids"])
    origin = xyz[ns]
    roots = {domain: sorted({node for d, node, c in layout["fixed_coordinates"] if d == domain})
             for domain in ("shell", "beam")}
    fixed = {(d, n, c) for d, n, c in layout["fixed_coordinates"]}
    with np.load(nr/"operators.npz", allow_pickle=False) as op:
        maps = {d: np.array(op[d+"_rigid_work_map"], copy=True) for d in ("shell", "beam")}
    for case in ("fy", "mx", "mz"):
        nc, ec = nr/case, er/case
        external = read(ec/"recovered-actions.json")
        raw = read(ec/"raw-inventory.json")
        actions = read(nc/"physical-actions.json")
        paths = [nr/"operators.npz", nr/"layout.json", nr/"inputs.json", nc/"raw-state.npz", nc/"physical-actions.json",
                 ec/"recovered-actions.json", ec/"raw-inventory.json", ec/"summary.json"]
        result["bound_inputs"].update({str(p): sha(p) for p in paths})
        with np.load(nc/"raw-state.npz", allow_pickle=False) as data:
            arrays = {k: np.array(data[k], copy=True) for k in ("q", "load", "Kq", "constraint_resisting", "reactions", "beam_retained", "beam_nodal_poses")}
        entry = {"nx": nx, "case": case, "domains": {}, "boundary_trace": {}, "rigid_domain_work": {}}
        for domain in ("shell", "beam"):
            nodal, fields = [], {side: {key: {} for key in ("G", "C", "L", "R")} for side in ("native", "external")}
            positions = {}
            for node in roots[domain]:
                slot = index[domain, node]
                external_node = node if domain == "shell" else 100001+node-101
                positions[node] = xyz[slot//6]
                if not np.allclose(positions[node], raw["nodes"][str(external_node)], rtol=0., atol=1e-13):
                    raise ValueError("typed root geometry mismatch")
                mask = np.array([int((domain, node, c) in fixed) for c in range(6)])
                actual_mask = np.array(raw["fixes"][str(external_node)])
                if not np.array_equal(mask, actual_mask):
                    raise ValueError("typed root support mask mismatch")
                nv = {"G": arrays["Kq"][slot:slot+6], "C": arrays["constraint_resisting"][slot:slot+6],
                      "L": arrays["load"][slot:slot+6], "R": arrays["reactions"][slot:slot+6]}
                ev = {"G": np.array(external[domain+"_domain_nodal_G"][str(external_node)]),
                      "C": np.array(external["connection_resisting_C_transpose_lambda"][str(external_node)]),
                      "L": np.array(external["applied_nodal_L"][str(external_node)]),
                      "R": np.array(external["actual_ground_exerted_loads"][str(external_node)])}
                if np.any(nv["L"]) or np.any(ev["L"]):
                    raise ValueError("root applied loads must be zero")
                delta = {key: nv[key]-ev[key] for key in nv}
                for side, values in (("native", nv), ("external", ev)):
                    for key, value in values.items():
                        fields[side][key][node] = value*mask
                nodal.append({"native_domain_node": (domain, node), "external_node": external_node, "fixed_mask": mask.tolist(),
                    "native_all6": {k: v.tolist() for k, v in nv.items()}, "external_all6": {k: v.tolist() for k, v in ev.items()},
                    "delta_all6": {k: v.tolist() for k, v in delta.items()},
                    "decomposition_fixed_error": (delta["R"]-mask*(delta["G"]+delta["C"])).tolist(),
                    "free_root_equilibrium_native": ((1-mask)*(nv["G"]+nv["C"])).tolist(),
                    "free_root_equilibrium_external": ((1-mask)*(ev["G"]+ev["C"])).tolist()})
            aggregates = {side: {key: wrench(positions, field, origin) for key, field in f.items()}
                          for side, f in fields.items()}
            delta = {key: aggregates["native"][key]-aggregates["external"][key] for key in ("G", "C", "L", "R")}
            entry["domains"][domain] = {"root_node_count": len(nodal), "root_all6_covectors": nodal,
                "common_origin_native": {k: v.tolist() for k, v in aggregates["native"].items()},
                "common_origin_external": {k: v.tolist() for k, v in aggregates["external"].items()},
                "delta_common_origin": {k: v.tolist() for k, v in delta.items()},
                "delta_R_minus_G_minus_C": (delta["R"]-delta["G"]-delta["C"]).tolist(),
                "norms_1m_force_equivalent": {k: norm(v) for k, v in delta.items()},
                "signed_projection_on_delta_R": {"internal_G": projection(delta["G"], delta["R"]),
                                                   "constraint_resisting_C": projection(delta["C"], delta["R"])}}
            full, nodal_only = {}, {}
            physical = layout["counts"]["physical_dofs"]
            for label, vector in (("internal_G", arrays["Kq"]), ("constraint_resisting", arrays["constraint_resisting"]),
                                  ("ground", arrays["reactions"]), ("applied", arrays["load"])):
                full[label] = maps[domain]@vector
                nodal_only[label] = maps[domain][:, :physical]@vector[:physical]
            entry["rigid_domain_work"][domain] = {"full_native": {k: v.tolist() for k, v in full.items()},
                "physical_nodal_only_native": {k: v.tolist() for k, v in nodal_only.items()},
                "retained_native_contribution": {k: (full[k]-nodal_only[k]).tolist() for k in full},
                "saved_domain_workmap_parity_max": max(float(np.max(np.abs(full[k]-np.array(actions["domain_wrenches"][{"internal_G":"internal", "constraint_resisting":"connection_exerted", "ground":"ground", "applied":"applied"}[k]][domain])*(-1 if k=="constraint_resisting" else 1)))) for k in full)}
        # Linearized exact native end-work map: p=(n0,n1,m0L,m0R,m1L,m1R).
        p = arrays["beam_retained"][0, 6:]
        root_slot = index["beam", 101]
        predicted_root_G = -np.r_[p[:3], p[6:9]]
        current_root_G = arrays["Kq"][root_slot:root_slot+6]
        cell_rot = arrays["beam_retained"][0, :3]
        ext_root = np.array(raw["poses"]["100001"])
        ext_next = np.array(raw["poses"]["100002"])
        entry["boundary_trace"] = {"native_root_nodal_pose": arrays["beam_nodal_poses"][0].tolist(),
            "external_root_nodal_pose": ext_root.tolist(), "native_first_cell_rotation": cell_rot.tolist(),
            "external_first_interval_center_P1_rotation": ((ext_root[3:]+ext_next[3:])/2.).tolist(),
            "native_cell_minus_root_nodal_rotation": (cell_rot-arrays["beam_nodal_poses"][0, 3:]).tolist(),
            "first_halfcell_length_m": 1./(2*nx), "native_first_cell_resultants_p18": p.tolist(),
            "native_root_G_independent_endpoint_prediction": predicted_root_G.tolist(),
            "native_root_G_minus_endpoint_prediction": (current_root_G-predicted_root_G).tolist(),
            "physical_trace_distinction": "Native line rotation uses retained cell Theta, not nodal theta; external line uses continuous nodal P1 theta."}
        whole = next(row for row in distance["cases"][case] if row["nx"] == nx)["whole_difference"]
        entry["whole_interface_difference_saved"] = whole
        entry["delta_beam_ground_plus_delta_interface"] = (np.array(entry["domains"]["beam"]["delta_common_origin"]["R"])+np.array(whole)).tolist()
        entry["total_root_ground_difference"] = (np.array(entry["domains"]["beam"]["delta_common_origin"]["R"])+
                                                 np.array(entry["domains"]["shell"]["delta_common_origin"]["R"])).tolist()
        result["cases"].append(entry)
result["bound_inputs"][str(NATIVE/"fixed-distance-transfer.json")] = sha(NATIVE/"fixed-distance-transfer.json")
destination = ROOT/"r8-bl5-endport-support-work.json"
if destination.exists():
    raise FileExistsError("preserve prior analysis")
destination.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
for row in result["cases"]:
    beam = row["domains"]["beam"]
    print(json.dumps({"nx": row["nx"], "case": row["case"], "delta_beam_ground": beam["delta_common_origin"]["R"],
                      "delta_beam_internal_G": beam["delta_common_origin"]["G"], "delta_beam_C": beam["delta_common_origin"]["C"],
                      "beam_signed_projection": beam["signed_projection_on_delta_R"]}))
print(json.dumps({"cases": len(result["cases"]), "output": str(destination), "no_product_imports": not any(n.split('.')[0] == "anysolver" for n in __import__('sys').modules)}))
