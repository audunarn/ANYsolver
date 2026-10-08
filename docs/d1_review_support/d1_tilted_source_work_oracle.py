"""Independent planar-Q1 source-ry work calculation for a saved tilted press."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--saved", type=Path, required=True)
parser.add_argument("--screen", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error("output already exists")
saved_bytes = args.saved.read_bytes()
screen_bytes = args.screen.read_bytes()
saved = json.loads(saved_bytes)
screen = json.loads(screen_bytes)
if (saved["status"], saved["columns"], saved["accepted_steps"],
        saved["target_reference_slope"], saved["target_right_x_m"],
        saved["load_profile"]) != (
        "completed", 8, 3, 1.0e-5, 1.3, "distributed"):
    raise ValueError("saved case is not the registered tilted planar fixture")
if (screen["active_pressure_modes"] != 6
        or screen["pressure_replay_max_error_pa"] != 0.0
        or screen["source_node_ids"] != list(range(1, 19))):
    raise ValueError("source-work screen did not replay the expected state")

# Exact reference overlap: Q4 source x=[0.1,1.1] in eight equal cells;
# y=[0.1,1.1], clipped by target at y=1.0. Target x=[0,1.3].
x_width = 1.0/8.0
x_integrals = np.array([x_width/2.0]+[x_width]*7+[x_width/2.0])
overlap_y = 0.9
y_upper_integral = overlap_y**2/2.0
y_lower_integral = overlap_y-y_upper_integral
reference_support = np.outer(
    [y_lower_integral, y_upper_integral], x_integrals).reshape(-1)
reported_support = np.asarray(
    saved["contact"]["reference_support_m2"], dtype=float)
pressure = np.asarray(saved["contact"]["numerical_pressure_pa"], dtype=float)
if pressure.size != 18 or reported_support.size != 18:
    raise ValueError("unexpected source pressure space")
normal_resultant = float(pressure @ reference_support)
# Consistent Q1 pressure-to-node work, assembled from exact 1D polynomial
# products. This resolves every source-ry row rather than only their sum.
mass_x = np.zeros((9, 9))
local_x = x_width*np.array([[1.0/3.0, 1.0/6.0],
                            [1.0/6.0, 1.0/3.0]])
for cell in range(8):
    mass_x[cell:cell+2, cell:cell+2] += local_x
length_y = overlap_y
mass_y_00 = length_y-length_y**2+length_y**3/3.0
mass_y_01 = length_y**2/2.0-length_y**3/3.0
mass_y_11 = length_y**3/3.0
mass_y = np.array([[mass_y_00, mass_y_01],
                   [mass_y_01, mass_y_11]])
pressure_mass = np.kron(mass_y, mass_x)
slope = float(saved["target_reference_slope"])
normal = np.array([-slope, 0.0, 1.0])/np.sqrt(1.0+slope*slope)
predicted_force = normal_resultant*normal
# Source bottom skin has -25 mm reference-director offset. Its uniform
# positive global-ry variation moves every skin point -25 mm in x per rad.
# The contact residual is opposite to physical virtual work.
predicted_contact_ry = -0.025*slope/np.sqrt(1.0+slope*slope)*normal_resultant
predicted_nodal_ry = (-0.025*slope/np.sqrt(1.0+slope*slope)
                      *(pressure_mass@pressure))
observed_nodal_ry = np.asarray(
    screen["source_contact_ry_moments_nm"], dtype=float)
observed_contact_ry = float(screen["sum_source_contact_ry_moment_nm"])
observed_force = np.asarray(screen["integration_force_n"], dtype=float)
predicted_reaction = (float(screen["sum_source_internal_ry_moment_nm"])
                      +predicted_contact_ry)
reported_reaction = float(screen["saved_source_guide_ry_reaction_nm"])

record = {
    "status": "development_independent_source_virtual_work",
    "oracle_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "saved_sha256": hashlib.sha256(saved_bytes).hexdigest(),
    "screen_sha256": hashlib.sha256(screen_bytes).hexdigest(),
    "reference_geometry": {
        "source_x_m": [0.1, 1.1], "source_y_m": [0.1, 1.1],
        "target_x_m": [0.0, 1.3], "target_y_m": [0.0, 1.0],
        "source_columns": 8, "source_bottom_offset_m": -0.025,
        "target_slope_dz_dx": slope,
    },
    "analytical_reference_support_m2": reference_support.tolist(),
    "support_relative_error": float(np.linalg.norm(
        reference_support-reported_support)/np.linalg.norm(reference_support)),
    "normal_resultant_n": normal_resultant,
    "predicted_source_force_n": predicted_force.tolist(),
    "source_force_relative_error": float(np.linalg.norm(
        predicted_force-observed_force)/np.linalg.norm(observed_force)),
    "predicted_source_contact_ry_nm": predicted_contact_ry,
    "predicted_source_nodal_ry_nm": predicted_nodal_ry.tolist(),
    "source_nodal_ry_relative_error": float(np.linalg.norm(
        predicted_nodal_ry-observed_nodal_ry)/np.linalg.norm(observed_nodal_ry)),
    "source_nodal_ry_max_abs_error_nm": float(np.max(np.abs(
        predicted_nodal_ry-observed_nodal_ry))),
    "pressure_mass_row_sum_error_m2": float(np.max(np.abs(
        pressure_mass.sum(axis=1)-reference_support))),
    "observed_source_contact_ry_nm": observed_contact_ry,
    "contact_ry_relative_error": abs(predicted_contact_ry-observed_contact_ry)/abs(
        observed_contact_ry),
    "predicted_source_guide_ry_reaction_nm": predicted_reaction,
    "reported_source_guide_ry_reaction_nm": reported_reaction,
    "reaction_absolute_error_nm": abs(predicted_reaction-reported_reaction),
}
args.output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
print(json.dumps({key: record[key] for key in (
    "support_relative_error", "source_force_relative_error",
    "contact_ry_relative_error", "source_nodal_ry_relative_error",
    "reaction_absolute_error_nm")}, indent=2))
