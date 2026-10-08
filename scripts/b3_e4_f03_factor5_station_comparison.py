"""Compare saved F5 torque face and section motions at matched native stations.

Pure torque is a linear influence of the pre-opened C1 case, not an
admissible standalone contact reference. No solver or external process runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import read_deck
from scripts.b3_e4_f03_saved_six_gap_replay import (
    GRID, _lookup, _ports, _solid_face_sample)
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


STATIONS = (.9,.95,1.)
Y = np.array((-.05,-.025,0.,.025,.05))
WEIGHTS = np.array((.125,.25,.25,.25,.125))
FAMILIES = ("line_hybrid_p0_weighted", "line_hybrid_p1_weighted",
            "line_hybrid_dual_p1_weighted")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _section_rotation_at(x: float, rotations: np.ndarray) -> float:
    j = min(4,max(0,int(np.floor((x-.9)/.02+1e-8))))
    f = float(np.clip((x-GRID[j])/(GRID[j+1]-GRID[j]),0.,1.))
    return float((1.-f)*rotations[j,0]+f*rotations[j+1,0])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root",type=Path,required=True)
    args = parser.parse_args()
    root = args.evidence_root.resolve()
    if root.exists():
        raise FileExistsError(root)
    base = root.parent
    solid_stem = base/"f03-ccx-c1-factor5-torque-influence-dev-20260926-v1/solid-5-tip_mx/solid-5-tip_mx"
    solid_result_path = base/"f03-ccx-c1-factor5-torque-influence-dev-20260926-v1/result.json"
    native_root = base/"f03-c1-factor5-matched-tip-ports-dev-20260926-v2"
    native_path = native_root/"native-loaded.json"
    native_manifest_path = native_root/"manifest.json"
    x,elements = read_deck(solid_stem.with_suffix(".inp"))
    u = _read_frd_u(solid_stem.with_suffix(".frd"))
    if set(u)!=set(range(1,len(x))):
        raise ValueError("complete saved solid field required")
    solid = json.loads(solid_result_path.read_text())[0]
    model = solid["model"]
    if (solid["status"]!="EXPLORATORY_COMPLETE" or
            model["factor"]!=5 or model["plate_thickness_m"]!=.035 or
            model["bond_interval_m"]!=[.9,1.] or
            model["boundary_policy"]!="left_root" or
            model["bond_policy"]!="terminal" or
            model["contact_policy"]!="none" or
            model["bar_reference_profile"]!=
            "C1_TWO_QUADRATIC_TANGENT_ALIGNED_V1" or
            model["tip_load_map"]!="quadratic_face" or
            model["bar_clearance_um"]!=2 or
            model["element_family"]!="C3D20R" or
            np.max(np.abs(np.asarray(solid["response"]["applied_wrench_N_Nm"])-
                          np.array((0.,0.,0.,100.,0.,0.))))>1e-9):
        raise ValueError("unmatched C1 F5 solid torque influence")
    native = json.loads(native_path.read_text())
    manifest = json.loads(native_manifest_path.read_text())
    if (native["beam_half_cells"]!=12 or native["bond_x_cells"]!=2 or
            native["bond_y_cells"]!=4 or
            native["plate_thickness_m"]!=.035 or
            manifest["source_git"]!="ea5e2c46167ade41d795d602ed940ec414766b06"):
        raise ValueError("unmatched saved native station fixture")
    coords = {i:x[i] for i in range(1,len(x))}
    node = _lookup(coords)
    fits = {}
    for kind in ("area","nonbond"):
        _,rotations,rms = _ports(coords,u,elements,method=kind)
        fits[kind] = {"section_rx_at_stations_rad":{
            str(round(station*1000)):_section_rotation_at(station,rotations)
            for station in STATIONS},
            "section_vector_rms_fit_m":rms.tolist(),
            "station_950_is_linear_interpolation_between_940_and_960":True}
    stations = {}
    for station in STATIONS:
        key = str(round(station*1000))
        face = np.array([_solid_face_sample(node,u,station,float(y),.0175)
                         for y in Y])
        solid_mean = np.average(face,axis=0,weights=WEIGHTS)
        solid_slope = float((face[-1,2]-face[0,2])/.1)
        area_rx = fits["area"]["section_rx_at_stations_rad"][key]
        nonbond_rx = fits["nonbond"]["section_rx_at_stations_rad"][key]
        families = {}
        for family in FAMILIES:
            case = native["results"][family]["cases"]["tip_mx"]
            trace = case["terminal_station_kinematics"][key]
            if not np.allclose(trace["shell_top_edge_sample_y_m"],Y,
                               rtol=0.,atol=1e-14):
                raise ValueError("native shell-edge sampling changed")
            nmean = np.array(trace["shell_top_edge_mean_translation_m"])
            nslope = float(trace["shell_top_slope_z_y_rad"])
            nrx = float(trace["beam_nodal_rx_rad"])
            families[family] = {
                "native_face_mean_translation_m":nmean.tolist(),
                "native_face_endpoint_slope_z_y_rad":nslope,
                "native_beam_nodal_rx_rad":nrx,
                "native_minus_solid_face_mean_translation_m":(
                    nmean-solid_mean).tolist(),
                "native_minus_solid_face_slope_rad":nslope-solid_slope,
                "native_minus_solid_area_section_rx_rad":nrx-area_rx,
                "native_minus_solid_nonbond_section_rx_rad":nrx-nonbond_rx,
                "native_section_minus_face_slope_rad":nrx-nslope,
            }
        stations[key] = {
            "x_m":station,
            "solid_face_mean_translation_m":solid_mean.tolist(),
            "solid_face_endpoint_slope_z_y_rad":solid_slope,
            "solid_area_section_rx_rad":area_rx,
            "solid_nonbond_section_rx_rad":nonbond_rx,
            "solid_area_section_minus_face_slope_rad":area_rx-solid_slope,
            "solid_nonbond_section_minus_face_slope_rad":nonbond_rx-solid_slope,
            "native_families":families}
    paths = [solid_stem.with_suffix(suffix) for suffix in (".inp",".frd")]
    paths += [solid_result_path,native_path,native_manifest_path]
    result = {
        "classification":"bounded saved F5/native matched-station diagnostic; no G0B acceptance",
        "question":"Does native torque response differ first in the physical plate face or the reduced B3 section at the same bond stations?",
        "outcome_rule":"Face agreement with larger section divergence prioritizes section/end-port idealization; material face divergence keeps shell trace equally suspect. A station match alone cannot select a multiplier or prove causation.",
        "case":"same C1 35 mm plate, 100 mm square bar, terminal 0.1 m bond, +100 Nm tip torque linear influence, left shell and beam-root supports",
        "solid_face_measure":"five y samples -0.05,-0.025,0,0.025,0.05 m; trapezoidal weights 0.125,0.25,0.25,0.25,0.125 for mean; endpoint z-displacement secant over 0.1 m for slope, matching saved native recovery",
        "solid_section_measure":"area or independent nonbond rigid-section fit to saved F5 bar displacement; x=.95 m interpolated from fitted x=.94/.96 m sections",
        "section_fit_sensitivity":fits,
        "stations":stations,
        "limits":["pure torque closes sampled unbonded faces and is only a linear influence of the pre-opened combined case",
                  "solid face Q20 and native Q4/discrete director remain different idealizations",
                  "beam section fit is not the native retained B3 port",
                  "matched tip resultant and supported geometry do not make the 3D and reduced sections identical",
                  "none of these scalar station differences ranks P0/P1/dual or establishes cause"],
        "inputs_sha256":{str(path.relative_to(base)):_sha(path) for path in paths},
        "runner_sha256":_sha(Path(__file__))}
    root.mkdir(parents=True)
    (root/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    for key,value in stations.items():
        print(key,"solid face slope µrad",round(1e6*value["solid_face_endpoint_slope_z_y_rad"],3),
              "solid section µrad",round(1e6*value["solid_area_section_rx_rad"],3))


if __name__=="__main__":
    main()
