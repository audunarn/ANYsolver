"""Bounded ordinary-force and split-restart development discriminator."""
import hashlib, json, sys, time, traceback
from pathlib import Path
import numpy as np
from anysolver import BoundaryCondition, solve_static_nonlinear
from anysolver.boundary import LoadCase
import anysolver.nonlinear_static as driver
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from docs.d1_review_support.d2_projected_penalty_shell_dev import fixture, represented_gap

output = Path(sys.argv[1])
if output.exists(): raise RuntimeError("output already exists")
reference_path = Path("docs/d1_review_support/d2_projected_penalty_shell_v2_20260930.json")
reference = json.loads(reference_path.read_text(encoding="utf-8"))["rows"][0]
record = {"accepted": False, "released": False, "kind": "ordinary_force_restart_development",
          "reference": str(reference_path), "reference_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
          "matrix_classes": [], "source": {}, "checks": {}}
for name in ("nonlinear_static.py", "general_contact/core.py", "general_contact/s3_patch_static.py", "general_contact/static_path.py"):
 p = Path("src/anysolver")/name
 record["source"][name] = hashlib.sha256(p.read_bytes()).hexdigest()
record["imported_driver"] = driver.__file__
original = driver.factorize

def traced(matrix, matrix_class, *args, **kwargs):
 record["matrix_classes"].append(str(matrix_class))
 return original(matrix, matrix_class, *args, **kwargs)

def case():
 m, d, s, _ = fixture(1e7)
 # Preserve both zero-valued pilot controls as prescribed BCs.
 m.add_boundary_condition(BoundaryCondition("former_zero_controls", (2,), {"ux": 0., "uy": 0.}))
 load = LoadCase("same_half_newton_press")
 for node in (3, 6): load.add_nodal_load(node, forces=np.array([0., 0., -.25]))
 return m, d, s, load

started = time.perf_counter()
try:
 driver.factorize = traced
 m, d, s, load = case()
 prefix = solve_static_nonlinear(m, load_case=load, contact=d, contact_settings=s,
     num_steps=2, max_load_factor=.5, max_iterations=18, tolerance=1e-8,
     emit_restart_checkpoint=True, record_increment_snapshots=True)
 record["prefix"] = {"status": prefix.status, "failure": prefix.failure_reason,
     "load_factor": prefix.load_factor, "checkpoint": prefix.restart_checkpoint,
     "displacements": prefix.displacements.tolist(), "info": prefix.info}
 if prefix.status != "completed" or prefix.restart_checkpoint is None:
  raise RuntimeError("ordinary prefix did not complete with checkpoint")
 m, d, s, load = case()
 result = solve_static_nonlinear(m, load_case=load, contact=d, contact_settings=s,
     num_steps=2, max_iterations=18, tolerance=1e-8,
     restart_checkpoint=prefix.restart_checkpoint, emit_restart_checkpoint=True,
     record_increment_snapshots=True)
 record["resumed"] = {"status": result.status, "failure": result.failure_reason,
     "load_factor": result.load_factor, "checkpoint": result.restart_checkpoint,
     "displacements": result.displacements.tolist(), "info": result.info}
 if result.status != "completed": raise RuntimeError("ordinary resumed press failed")
 manager = GeneralS3PatchManager(m, d, s)
 certificate = manager.evaluate(result.displacements, tangent=False)[2]
 record["certificate"] = certificate.to_dict()
 record["independent_gap"] = represented_gap(m, result.displacements)
 uref = np.asarray(reference["final_displacements"])
 error = np.linalg.norm(result.displacements-uref)/np.linalg.norm(uref)
 pressure = np.asarray(reference["poses"][-1]["certificate"]["numerical_pressure_pa"])
 p_error = np.linalg.norm(np.asarray(certificate.numerical_pressure_pa)-pressure)/np.linalg.norm(pressure)
 record["comparison"] = {"relative_displacement": float(error), "relative_pressure": float(p_error)}
 summaries = [value for key, value in result.info.items() if isinstance(value, dict) and "normal_law" in value]
 record["reported_laws"] = [value["normal_law"] for value in summaries]
 record["checks"] = {"displacement_match": bool(error <= 1e-6),
     "pressure_match": bool(p_error <= 1e-6), "gap_budget": bool(record["independent_gap"]["minimum_gap_m"] >= -5e-5),
     "general_matrix": bool(record["matrix_classes"] and all("GENERAL" in mode for mode in record["matrix_classes"])),
     "law_reporting": bool(record["reported_laws"] == ["projected_penalty"]),
     "restart_completed": result.load_factor == 1.0,
     "zero_multipliers": bool(np.all(manager.normal_multipliers == 0))}
 record["development_checks_met"] = all(record["checks"].values())
except Exception as exc:
 record["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
 record["development_checks_met"] = False
finally:
 driver.factorize = original
 record["elapsed_seconds"] = time.perf_counter()-started
 def scalar(value):
  if isinstance(value, np.generic): return value.item()
  if isinstance(value, np.ndarray): return value.tolist()
  raise TypeError(type(value).__name__)
 output.write_text(json.dumps(record, indent=2, default=scalar)+"\n", encoding="utf-8")
 print(json.dumps({key: record[key] for key in ("development_checks_met", "elapsed_seconds", "checks")}), flush=True)
 if "error" in record: print(record["error"]["message"], flush=True)
raise SystemExit(0 if record["development_checks_met"] else 1)
