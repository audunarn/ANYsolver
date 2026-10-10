"""Bounded C1-shaped detached solid mesh feasibility; no equilibrium solve.

This probes whether the existing C3D20R geometry builder can supply separate
plate/bar ownership under the diagnostic size cap. It does not establish a
five-channel law or reuse the historical shared-node weld as a reference.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from scripts import b3_e4_f03_ccx_solid_bond_screen as solid


def digest(path:Path)->str:
    return sha256(path.read_bytes()).hexdigest()


def evaluate()->dict:
    deck,meta=solid.build(2,"tip_mx",boundary_policy="left_root",
        bond_policy="detached",contact_policy="none",element_family="C3D20R",
        plate_thickness_mm=35,tip_load_map="quadratic_face",
        full_displacement_output=False,bar_clearance_um=0,
        bar_reference_profile="legacy_linear")
    count=int(meta["node_count"])
    applied={int(n):np.asarray(v,dtype=float) for n,v in meta["applied_nodal_forces_N"].items()}
    coordinates={int(n):np.asarray(v,dtype=float) for n,v in meta["probe_coordinates_m"].items()}
    if not set(applied)<=set(coordinates):
        raise ValueError("complete physical tip-load coordinates required")
    wrench=np.zeros(6)
    for n,force in applied.items():
        wrench[:3]+=force
        wrench[3:]+=np.cross(coordinates[n],force)
    if (meta["bond_policy"]!="detached" or meta["shared_interface_nodes"]!=0 or
            meta["plate_thickness_m"]!=.035 or
            abs(meta["bar_tip_axis_z_m"]-.0675)>1e-12 or
            meta["boundary_policy"]!="left_root" or
            not meta["beam_root_node_ids"] or count*3>100_000):
        raise ValueError("detached C1-shaped physical envelope or size cap failed")
    return {"identity":"R8_BL5_C1_DETACHED_FACTOR2_FEASIBILITY_DEV_V1",
        "status":"GEOMETRY_FEASIBILITY_NOT_QUALIFIED",
        "builder_sha256":digest(Path(solid.__file__)),
        "factor":2,"node_count":count,"physical_displacement_rows":3*count,
        "plate_elements":meta["plate_elements"],"bar_elements":meta["bar_elements"],
        "shared_interface_nodes":meta["shared_interface_nodes"],
        "detached_interface_nodes":meta["detached_interface_nodes"],
        "boundary_nodes":meta["boundary_nodes"],
        "beam_root_nodes":len(meta["beam_root_node_ids"]),
        "plate_thickness_m":meta["plate_thickness_m"],
        "bar_axis_z_m":meta["bar_tip_axis_z_m"],
        "tip_wrench_about_origin":wrench.tolist(),
        "deck_sha256":sha256(deck.encode("utf-8")).hexdigest(),
        "limitations":"straight legacy reference axis, no 2 um C1 tangent profile; detached terminal gap/trace equations not yet constructed; no solve"}


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve earlier geometry preflight")
    result=evaluate()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({key:result[key] for key in (
        "status","node_count","physical_displacement_rows",
        "plate_elements","bar_elements","shared_interface_nodes",
        "tip_wrench_about_origin")}))


if __name__=="__main__":
    main()
