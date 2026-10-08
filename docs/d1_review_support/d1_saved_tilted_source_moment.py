"""Screen the source director contact action at a saved coupled tilted press."""

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np

from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.core import suspend_contact
from anysolver.nonlinear_static import (
    _assemble_nonlinear_system, _prepare_initial_states,
)
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import build_case


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--saved", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error("output already exists")
started = time.perf_counter()
saved_bytes = args.saved.read_bytes()
saved = json.loads(saved_bytes)
if (saved["status"], saved["columns"], saved["accepted_steps"],
        saved["target_reference_slope"], saved["load_profile"]) != (
        "completed", 8, 3, 1.0e-5, "distributed"):
    raise ValueError("saved press identity does not match this source-work screen")
model, definition, settings, _program = build_case(
    saved["columns"], four_phase=saved["four_phase"],
    steps_per_segment=saved["steps_per_segment"],
    load_profile=saved["load_profile"],
    total_force_n=saved["total_downward_force_n"],
    target_right_x_m=saved["target_right_x_m"],
    target_reference_slope=saved["target_reference_slope"],
)
settings = replace(settings, augmentation_schur_maximum_pressure_pa=250,
                   augmentation_schur_maximum_step_pa=200)
manager = GeneralS3PatchManager(model, definition, settings)
pose = np.asarray(saved["final_displacements"], dtype=float)
multipliers = np.asarray(
    saved["contact"]["normal_multiplier_estimate_pa"], dtype=float)
manager.set_normal_multipliers(multipliers)
force, _tangent, result = manager.evaluate(pose, tangent=False)
source_ry = np.asarray([
    model.mesh.dof_manager.get_node_dofs(node)[4]
    for node in manager.law.source_node_ids], dtype=int)
moments = np.asarray(force)[source_ry]
with suspend_contact():
    states, _provenance = _prepare_initial_states(model, None, None, 5)
    internal, _stiffness, _states = _assemble_nonlinear_system(
        model, pose, states, 5, tangent=False, kinematics="von_karman",
        require_full_coordinates=True)
internal_source_ry = np.asarray(internal)[source_ry]
saved_source_guide_ry_reaction = float(
    saved["support_reactions"][-1]["source_guide"][4])
pressure_error = float(np.max(np.abs(np.asarray(result.numerical_pressure_pa)
                                   -np.asarray(saved["contact"]["numerical_pressure_pa"]))))
record = {
    "status": "development_saved_tilted_source_moment_screen",
    "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                             text=True).strip(),
    "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "saved_sha256": hashlib.sha256(saved_bytes).hexdigest(),
    "active_pressure_modes": result.active_pressure_dofs,
    "pressure_replay_max_error_pa": pressure_error,
    "source_node_ids": list(manager.law.source_node_ids),
    "source_contact_ry_moments_nm": moments.tolist(),
    "maximum_abs_source_contact_ry_moment_nm": float(np.max(np.abs(moments))),
    "sum_source_contact_ry_moment_nm": float(np.sum(moments)),
    "sum_source_internal_ry_moment_nm": float(np.sum(internal_source_ry)),
    "sum_source_total_ry_residual_nm": float(np.sum(
        internal_source_ry+moments)),
    "saved_source_guide_ry_reaction_nm": saved_source_guide_ry_reaction,
    "nominal_half_thickness_times_slope_force_nm": float(
        0.025*saved["target_reference_slope"]
        *np.linalg.norm(result.integration_force)),
    "integration_force_n": list(result.integration_force),
    "minimum_gap_m": result.minimum_gap,
    "elapsed_seconds": time.perf_counter()-started,
}
args.output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
print(json.dumps({key: record[key] for key in (
    "active_pressure_modes", "pressure_replay_max_error_pa",
    "maximum_abs_source_contact_ry_moment_nm",
    "nominal_half_thickness_times_slope_force_nm",
    "elapsed_seconds")}, indent=2))
