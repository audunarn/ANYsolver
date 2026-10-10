"""Recover continuous five-channel gaps between executed hinge stations.

Saved-output development diagnostic only. Three-point Gauss integrates the
square of each quadratic C3D20 material trace exactly on each axial cell.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from scripts import r8_bl5_mx_matched_refinement_dev as matched
from scripts import r8_bl5_mx_coupled_shell_refinement_dev as shell_ref
from scripts import r8_bl5_mx_torsion_refinement_dev as beam_ref
from scripts import r8_bl5_weak_continuum_reference as continuum
from scripts.r8_e02_double_output import read_double_output


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / ".development/bl5-ccx-strong-hinge-20261008-v1"
LEVEL = (8,4,2)
METADATA_SHA = "afddce6112a1f38615d441e28ef8506acb56d2f3ff5f12cdb525dc0f6858b853"
FRD_SHA = {"fy":"ec79ba0b8d0efd9bcbab4e38782cd229fc56a00d0f17df7e836be77ce0142093",
           "mx":"6c4f8b45f5234743d4b3f6aa578874686e1ee89bad7b23de0bb873a039683367"}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def evaluate() -> dict:
    metadata_path = CASE/"metadata.json"
    if digest(metadata_path) != METADATA_SHA:
        raise ValueError("frozen executed geometry/row metadata changed")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if tuple(metadata["level"]) != LEVEL or metadata["equation_check"]["physical_rows"] != 45:
        raise ValueError("nine-station five-channel case required")
    shell_nodes,shell_elements = shell_ref._shell_mesh(*LEVEL)
    beam_nodes,beam_elements = beam_ref._mesh(*LEVEL)
    model = shell_ref._combined(shell_nodes,shell_elements,beam_nodes,beam_elements)
    order,index,_,_,_ = continuum.layout(model)
    if ({str(k):list(v) for k,v in model["physical_nodes"].items()} != metadata["physical_nodes"]
            or {str(k):list(v) for k,v in model["elements"].items()} != metadata["elements"]):
        raise ValueError("saved external geometry differs from physical trace reconstruction")
    faces = matched._face_index(model)
    gauss,weights = np.polynomial.legendre.leggauss(3)
    station_x = np.linspace(0.,1.,LEVEL[0]+1)
    station_rows = np.stack([matched._five_rows(model,index,faces,float(x)) for x in station_x])
    segment_rows = np.stack([
        np.stack([matched._five_rows(model,index,faces,(edge+(1.+float(g))/2.)/LEVEL[0])
                  for g in gauss]) for edge in range(LEVEL[0])])
    midpoint_rows = np.stack([matched._five_rows(model,index,faces,(edge+.5)/LEVEL[0])
                              for edge in range(LEVEL[0])])
    cases = {}
    for name in ("fy","mx"):
        frd = CASE/f"{name}.frd"
        if digest(frd) != FRD_SHA[name]:
            raise ValueError("frozen executed displacement file changed")
        observed,reactions = read_double_output(frd.read_bytes(),metadata)
        q = np.array([value for node in order for value in observed[node]])
        station = np.einsum("scd,d->sc",station_rows,q)
        samples = np.einsum("sgcd,d->sgc",segment_rows,q)
        midpoint = np.einsum("scd,d->sc",midpoint_rows,q)
        # The physical line is 1 m long; normalized integral equals the
        # weighted mean of all segment-local quadrature values.
        rms = np.sqrt(np.einsum("g,sgc->c",weights,samples*samples)/(2*LEVEL[0]))
        max_abs = np.max(abs(samples),axis=(0,1))
        mid_abs = np.max(abs(midpoint),axis=0)
        if np.max(abs(station)) > 1e-9:
            raise ValueError("executed physical station constraints do not close")
        cases[name] = {"station_max_abs":np.max(abs(station),axis=0).tolist(),
                       "interior_rms":rms.tolist(),
                       "interior_gauss_max_abs":max_abs.tolist(),
                       "midpoint_max_abs":mid_abs.tolist(),
                       "midpoint_values":midpoint.tolist(),
                       "gauss_values":samples.tolist(),
                       "frd_sha256":FRD_SHA[name],
                       "translations_unit":"m", "director_slope_unit":"rad (small-strain proxy)"}
    return {"identity":"R8_BL5_STRONG_HINGE_INTERIOR_GAP_DEV_V1",
            "status":"SAVED_OUTPUT_DIAGNOSTIC_NOT_QUALIFIED",
            "source_sha256":digest(Path(__file__)),"metadata_sha256":METADATA_SHA,
            "level":LEVEL,"stations":station_x.tolist(),"gauss_abscissae":gauss.tolist(),
            "gauss_weights":weights.tolist(),"cases":cases,
            "limitation":"fixed same-body C3D20 thickness-secant proxy; station closure is not continuous bond fidelity"}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior saved-output diagnostic")
    result=evaluate()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"cases":{
        name:{"station_max_abs":case["station_max_abs"],"interior_rms":case["interior_rms"],
              "interior_gauss_max_abs":case["interior_gauss_max_abs"]}
        for name,case in result["cases"].items()}}))


if __name__=="__main__":
    main()
