"""Development comparison of a saved coupled field with the independent oracle."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

from docs.d1_review_support import d1_rim_oracle as oracle


root = Path("reports")
nx = int(sys.argv[1]) if len(sys.argv) > 1 else 16
if nx not in (8, 12, 16):
    raise ValueError("this development comparison admits 8, 12 or 16 x cells")
run_tag = sys.argv[2] if len(sys.argv) > 2 else "block32"
if run_tag not in {"block32", "guarded_no_checkpoint"}:
    raise ValueError("unknown near-rim development run")
refine_source = len(sys.argv) == 4 and sys.argv[3] == "refine_source"
if len(sys.argv) > 4 or (len(sys.argv) == 4 and not refine_source):
    raise ValueError("optional third argument must be refine_source")
coupled_file = root / f"general_contact_d1_{nx}x8_near_rim_{run_tag}_dev_20260928.json"
stem = f"general_contact_d1_{nx}x8_near_rim_{run_tag}"
output = root / f"{stem}_{'source_refinement' if refine_source else 'comparison_identity'}_dev_20260928.json"
if output.exists():
    raise FileExistsError(output)
coupled_bytes = coupled_file.read_bytes()
coupled = json.loads(coupled_bytes)
expected = {
    "status": "completed", "source_y_profile": "near_rim8",
    "columns": nx, "source_rows": 8, "load_profile": "distributed",
    "total_downward_force_n": oracle.Q, "target_right_x_m": 1.3,
    "target_reference_slope": 0.0, "target_columns": 1,
    "full_width_target": False, "four_phase": False,
    "steps_per_segment": 2, "pressure_basis": "fine_nodal_q1",
    "enforcement_solver": "monolithic_active_set",
    "monolithic_linear_solver": "block_response_dev",
}
if any(coupled.get(key) != value for key, value in expected.items()):
    raise ValueError("saved coupled result is not the intended near-rim completion")
if run_tag == "guarded_no_checkpoint" and (
        coupled.get("checkpoint_requested") is not False
        or coupled.get("has_checkpoint") is not False):
    raise ValueError("guarded spatial run must omit checkpoint emission")
y = np.array((0.0, 0.2, 0.4, 0.6, 0.75, 0.825, 0.875, 0.895, 1.0))
if refine_source:
    saved_file = root / f"{stem}_comparison_identity_dev_20260928.json"
    saved = json.loads(saved_file.read_text(encoding="utf-8"))
    if (saved.get("coupled_sha256") != hashlib.sha256(coupled_bytes).hexdigest()
            or saved.get("oracle_sha256") != hashlib.sha256(
                Path(oracle.__file__).read_bytes()).hexdigest()
            or saved.get("mesh") != [nx, 8]
            or saved.get("source_y_knots_m") != y.tolist()):
        raise ValueError("saved comparison identities differ")
    reference_bins = np.asarray(saved["fv_bins_n"], dtype=float)
    coarse_bins = np.asarray(saved["source_only_bins_n"], dtype=float)
    if (reference_bins.shape != (10, 8) or coarse_bins.shape != (10, 8)
            or np.any(~np.isfinite(reference_bins))
            or np.any(~np.isfinite(coarse_bins))):
        raise ValueError("saved physical bins are invalid")
    refined_y = np.sort(np.r_[y, 0.5*(y[:-1]+y[1:])])
    refined = oracle.solve_q1(2*nx, 16, ynodes=refined_y)
    edges_x = np.linspace(0.0, 1.0, 9)
    edges_y = np.r_[np.linspace(0.0, 0.9, 10), 1.0]
    refined_bins = oracle.q1_bins(refined, edges_x, edges_y)
    reference = reference_bins[:9]
    denominator = np.linalg.norm(reference)
    record = {
        "status": "development_source_only_refinement",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "coarse_coupled_sha256": saved["coupled_sha256"],
        "oracle_sha256": saved["oracle_sha256"],
        "saved_comparison_sha256": hashlib.sha256(saved_file.read_bytes()).hexdigest(),
        "coarse_grid": [nx, 8],
        "refined_grid": [2*nx, 16],
        "refined_y_knots_m": refined_y.tolist(),
        "common_bins": [8, 9],
        "coarse_vs_fv_l2_relative": float(
            np.linalg.norm(coarse_bins[:9]-reference)/denominator),
        "refined_vs_fv_l2_relative": float(
            np.linalg.norm(refined_bins[:9]-reference)/denominator),
        "coarse_vs_refined_l2_relative": float(
            np.linalg.norm(coarse_bins[:9]-refined_bins[:9])
            / np.linalg.norm(refined_bins[:9])),
        "coarse_reaction_n": float(coarse_bins.sum()),
        "refined_reaction_n": float(refined["reaction"]),
        "refined_bin_reaction_n": float(refined_bins.sum()),
        "fv_bin_reaction_n": float(reference_bins.sum()),
        "refined_equilibrium_n": float(refined["eq"]),
        "refined_complementarity_pa_m": float(refined["comp"]),
        "refined_bins_n": refined_bins.tolist(),
    }
    if abs(record["refined_reaction_n"]-record["refined_bin_reaction_n"]) > 1e-11:
        raise AssertionError("refined physical bins lose integrated reaction")
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: record[key] for key in (
        "coarse_vs_fv_l2_relative", "refined_vs_fv_l2_relative",
        "coarse_vs_refined_l2_relative", "coarse_reaction_n",
        "refined_reaction_n", "fv_bin_reaction_n",
    )}, indent=2))
    raise SystemExit(0)
source = oracle.solve_q1(nx, 8, ynodes=y)
fv = oracle.solve_fv(256, 320)
contact = coupled["contact"]
if contact["source_pressure_node_ids"] != list(range(1, 9*(nx+1)+1)):
    raise ValueError("saved pressure node order is incompatible with Q1 oracle")
edges_x = np.linspace(0.0, 1.0, 9)
edges_y = np.r_[np.linspace(0.0, 0.9, 10), 1.0]
ix = oracle.bin_integrals_1d(nx, 8, nodes=source["xn"], edges=edges_x)
iy = oracle.bin_integrals_1d(8, 10, oracle.YR, y, edges_y)
expected_support = np.kron(iy.sum(axis=0), ix.sum(axis=0))
np.testing.assert_allclose(contact["reference_support_m2"], expected_support,
                           rtol=1e-10, atol=1e-13)
pressure = np.asarray(coupled["contact"]["numerical_pressure_pa"]).reshape(9, nx+1)
coupled_bins = oracle.q1_bins(dict(nx=nx, ny=8, xn=source["xn"], yn=y,
                                   p=pressure), edges_x, edges_y)
source_bins = oracle.q1_bins(source, edges_x, edges_y)
reference_bins = oracle.fv_bins(fv, edges_x, edges_y)
ref = reference_bins[:9]
def errors(field):
    difference = field[:9]-ref
    return {
        "l1_relative": float(np.sum(np.abs(difference))/np.sum(np.abs(ref))),
        "l2_relative": float(np.linalg.norm(difference)/np.linalg.norm(ref)),
        "rim_band_force_relative": float(abs(field[8].sum()-ref[8].sum())
                                         /abs(ref[8].sum())),
        "empty_row_force_n": float(field[9].sum()),
    }

record = {
    "status": "development_comparison_only",
    "source_commit": subprocess.check_output(
        ("git", "rev-parse", "HEAD"), text=True).strip(),
    "coupled_file": str(coupled_file),
    "coupled_sha256": hashlib.sha256(coupled_bytes).hexdigest(),
    "oracle_file": str(Path(oracle.__file__).resolve()),
    "oracle_sha256": hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest(),
    "validated_model_identity": expected,
    "validated_pressure_node_ids_and_support": True,
    "mesh": [nx, 8],
    "source_y_knots_m": y.tolist(),
    "coupled_vs_fv": errors(coupled_bins),
    "source_only_vs_fv": errors(source_bins),
    "coupled_vs_source_only": {
        "pressure_l2_relative": float(np.linalg.norm(pressure-source["p"])
                                      /np.linalg.norm(source["p"])),
        "bin_l2_relative": float(np.linalg.norm(coupled_bins-source_bins)
                                 /np.linalg.norm(source_bins)),
        "reaction_relative": float(abs(coupled["contact"]["integration_force"][2]
                                       -source["reaction"])/abs(source["reaction"])),
    },
    "coupled_reaction_n": float(coupled["contact"]["integration_force"][2]),
    "source_only_reaction_n": float(source["reaction"]),
    "fv_reaction_n": float(fv["reaction"]),
    "source_only_equilibrium_n": float(source["eq"]),
    "source_only_complementarity_pa_m": float(source["comp"]),
    "fv_equilibrium_n": float(fv["eq"]),
    "coupled_bins_n": coupled_bins.tolist(),
    "source_only_bins_n": source_bins.tolist(),
    "fv_bins_n": reference_bins.tolist(),
}
output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
print(json.dumps({key: record[key] for key in (
    "coupled_vs_fv", "source_only_vs_fv", "coupled_vs_source_only",
    "coupled_reaction_n", "source_only_reaction_n", "fv_reaction_n",
)}, indent=2))
