"""Bounded saved-F5 bond work on transverse face modes (development only).

The affine trace is fitted independently at every saved x station, so its
complement tests transverse content without imposing a coarse longitudinal
line space. It is not a B3 sided-port or full six-channel qualification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import read_deck, wrench
from scripts.b3_e4_f03_c3d20r_stress_force_recovery import integrate, read_stress
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


BASE = Path(".qualification/b3-ge-e4-pl")
STEM = BASE / "f03-c1-factor5-stiffener-ip-stress-dev-20260926-v1/solid-5-tip_mx"
MODEL = BASE / "f03-ccx-c1-preopen-combined-factor5-dev-20260926-v1/solid-5-tip_mx/model.json"
VALIDATED = BASE / "f03-c1-factor5-stress-force-recovery-dev-20260926-v1/result.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _transverse_projection(x: np.ndarray, displacement: np.ndarray,
                           seam: np.ndarray, order: int) -> tuple[np.ndarray, dict]:
    projected = np.zeros((len(seam), 3))
    weights = np.zeros(len(seam))
    stations = np.unique(np.round(x[seam, 0], 9))
    details = []
    for station in stations:
        local = np.flatnonzero(np.isclose(x[seam, 0], station, rtol=0, atol=1e-10))
        local = local[np.argsort(x[seam[local], 1])]
        yy = x[seam[local], 1]
        if len(yy) < 3 or abs(yy[0] + .05) > 1e-10 or abs(yy[-1] - .05) > 1e-10:
            raise ValueError("incomplete transverse saved face station")
        dy = np.diff(yy)
        if np.any(dy <= 0):
            raise ValueError("unordered transverse saved face station")
        ww = np.r_[dy[0] / 2, (dy[:-1] + dy[1:]) / 2, dy[-1] / 2]
        design = np.stack([yy**j for j in range(order + 1)], axis=1)
        weighted = np.sqrt(ww)[:, None]
        coeff, _, rank, _ = np.linalg.lstsq(weighted * design,
                                             weighted * displacement[seam[local]],
                                             rcond=None)
        if rank != order + 1:
            raise ArithmeticError("transverse projection lost rank")
        projected[local] = design @ coeff
        weights[local] = ww
        residual = displacement[seam[local]] - projected[local]
        orth = design.T @ (ww[:, None] * residual)
        details.append({"x_m": float(station), "nodes": len(local),
                        "max_residual_m": float(np.max(np.linalg.norm(residual, axis=1))),
                        "weighted_orthogonality_m2": float(np.max(np.abs(orth)))})
    residual = displacement[seam] - projected
    rms = float(np.sqrt(np.sum(weights[:, None] * residual**2) / (3 * np.sum(weights))))
    return projected, {"weighted_component_rms_m": rms,
                       "maximum_vector_residual_m": float(np.max(np.linalg.norm(residual, axis=1))),
                       "max_weighted_orthogonality_m2": max(d["weighted_orthogonality_m2"] for d in details),
                       "stations": details}


def evaluate() -> dict:
    inp, frd, dat = STEM.with_suffix(".inp"), STEM.with_suffix(".frd"), STEM.with_suffix(".dat")
    source = [inp, frd, dat, MODEL, VALIDATED]
    accepted = json.loads(VALIDATED.read_text())
    model = json.loads(MODEL.read_text())
    if accepted["validation"]["status"] != "PASSED_SAVED_STATE_AND_WEAK_FORCE_CHECKS":
        raise ValueError("validated saved F5 force recovery required")
    if (model["element_family"] != "C3D20R" or model["bond_policy"] != "terminal"
            or model["contact_policy"] != "none" or model["boundary_policy"] != "left_root"
            or model["bond_interval_m"] != [.9, 1.] or model["bar_clearance_um"] != 2):
        raise ValueError("saved F5 physical fixture changed")
    x, elements = read_deck(inp)
    vectors = _read_frd_u(frd)
    if set(vectors) != set(range(1, len(x))):
        raise ValueError("incomplete saved F5 displacement field")
    u = np.array([[0., 0., 0.]] + [vectors[i] for i in range(1, len(x))])
    load = np.zeros_like(x)
    for key, vector in model["applied_nodal_forces_N"].items():
        load[int(key)] = vector
    # Use the validated printed-stress route, including CalculiX Gauss-point
    # ordering. Reintegrating rounded FRD strains is a different force oracle.
    bar_stress = read_stress(dat, first_element=len(elements["Plate"]) + 1,
                             element_count=len(elements["Stiffener"]))
    bar_force, _ = integrate(x, elements["Stiffener"], bar_stress)
    seam = np.asarray(model["shared_interface_node_ids"], dtype=np.int32)
    if len(seam) != 181 or np.max(np.abs(x[seam, 2] - .0175)) > 1e-12:
        raise ValueError("saved F5 shared face layout changed")
    action = load[seam] - bar_force[seam]
    known = accepted["reconstruction"]
    seam_work = float(np.sum(action * u[seam]))
    seam_wrench = wrench(load - bar_force, x, seam)
    known_wrench = np.asarray(known["bar_on_plate_stress_wrench_N_Nm"])
    if (abs(seam_work - known["seam_work_on_saved_displacement_J"]) > 1e-9
            or np.max(np.abs(seam_wrench - known_wrench)) > 1e-6):
        raise ArithmeticError("bond action does not reproduce validated F5 recovery")
    outputs = {}
    for order, name in ((1, "transverse_affine"), (2, "transverse_quadratic")):
        projected, diagnostic = _transverse_projection(x, u, seam, order)
        omitted = u[seam] - projected
        projected_work = float(np.sum(action * projected))
        omitted_work = float(np.sum(action * omitted))
        if abs(projected_work + omitted_work - seam_work) > 1e-12:
            raise ArithmeticError("virtual work did not decompose")
        diagnostic.update({
            "projected_work_J": projected_work,
            "omitted_signed_work_J": omitted_work,
            "omitted_abs_nodal_work_J": float(np.sum(np.abs(action * omitted))),
            "omitted_over_total_abs_signed_work": abs(omitted_work) / max(abs(seam_work), 1e-30),
        })
        outputs[name] = diagnostic
    return {
        "classification": "bounded saved-F5 transverse virtual-work diagnostic; no G0B acceptance",
        "decision": "Does transverse face deformation outside the affine section trace carry material work on the validated F5 bond action?",
        "model": "pre-opened +100 Nm/-1000 N C1 35 mm plate, 100 mm square bar, 0.1 m terminal shared-node bond, no contact",
        "transverse_projection": "weighted least-squares in y independently at every saved x station; positive trapezoid weights; no longitudinal coarsening",
        "known_seam_work_J": seam_work,
        "known_seam_wrench_N_Nm": seam_wrench.tolist(),
        "saved_face_nodes": len(seam),
        "results": outputs,
        "limitations": ["affine/quadratic face traces do not encode the independent E4 director-pitch channel",
                        "saved 3D section is not the native retained B3 port",
                        "nodal interface action is a weak discrete functional, not a pointwise traction",
                        "one saved mesh and a combined pre-opened linear load; no law, multiplier, or stability selection"],
        "inputs_sha256": {str(path): sha(path) for path in source},
        "runner_sha256": sha(Path(__file__)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    brief = {name: {key: value for key, value in entry.items()
                    if key in ("weighted_component_rms_m", "maximum_vector_residual_m",
                               "omitted_signed_work_J", "omitted_over_total_abs_signed_work")}
             for name, entry in result["results"].items()}
    print(json.dumps({"seam_work_J": result["known_seam_work_J"], "results": brief}))


if __name__ == "__main__":
    main()
