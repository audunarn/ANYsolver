"""Screen unbonded-face separation in saved exact split-law solid fields.

The saved shared-node C1 reference supplies the 128 paired Q8 face topology;
each side is remapped by reference geometry to the *detached* solid's own
nodes. This is a sampled physical-admissibility discriminator, not contact
traction, deformed closest-point certification or G0 qualification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c1_solid_trace_residual import (
    BASE, SCALES, SOURCE, _bound_field,
)
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import _quad8_shape, digest
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_deck_nodes


SPLIT = (BASE / "f03-c1-split-six-channel-dev-20260927-v1/"
         "reconstruction_v2.json")
RESPONSES = SPLIT.parent
SHARED = (BASE / "f03-ccx-c1-tangent-terminal-torque-full-u-dev-20260925-v1/"
          "solid-4-tip_mx")


def _mapped_faces(coords, plate_nodes, bar_nodes):
    meta = json.loads((SHARED / "model.json").read_text())
    decks = list(SHARED.glob("*.inp"))
    if (len(decks) != 1 or meta["shared_interface_nodes"] != 121 or
            meta["bar_reference_profile"] !=
            "C1_TWO_QUADRATIC_TANGENT_ALIGNED_V1" or
            len(meta["unbonded_face_pairs"]) != 128):
        raise ValueError("matched historical C1 face topology unavailable")
    old = _read_deck_nodes(decks[0])

    def lookup(nodes):
        result = {}
        for node in nodes:
            key = tuple(np.round(coords[node], 9))
            if key in result:
                raise ValueError("ambiguous detached-side reference node")
            result[key] = node
        return result

    plate, bar = lookup(plate_nodes), lookup(bar_nodes)
    mapped = []
    cells = set()
    for face in meta["unbonded_face_pairs"]:
        pair = []
        for old_plate, old_bar in face:
            pk = tuple(np.round(old[int(old_plate)], 9))
            bk = tuple(np.round(old[int(old_bar)], 9))
            if pk not in plate or bk not in bar:
                raise ValueError("historical face cannot map to detached source")
            pair.append((plate[pk], bar[bk]))
        array = np.asarray(pair, dtype=int)
        ref = np.array([coords[node] for node in array[:, 0]])
        x0, x1 = float(ref[0, 0]), float(ref[1, 0])
        y0, y1 = float(ref[0, 1]), float(ref[3, 1])
        key = tuple(round(value, 10) for value in (x0,x1,y0,y1))
        if (key in cells or x1 <= x0 or y1 <= y0 or
                not 0. <= x0 < .9+1e-10 or x1 > .9+1e-10 or
                np.max(np.abs(ref[:, 2]-.0175)) > 1e-12):
            raise ValueError("mapped unbonded face geometry changed")
        cells.add(key)
        mapped.append(array)
    if len(cells) != 128:
        raise ValueError("mapped unbonded rectangle incomplete")
    return mapped, {"shared_deck_sha256": digest(decks[0]),
                    "shared_model_sha256": digest(SHARED / "model.json")}


def _sample_faces(coords, state, faces):
    roots, _ = np.polynomial.legendre.leggauss(9)
    minimum = (float("inf"), None)
    negative = 0
    reprojected_negative = 0
    reprojected_count = 0
    reprojected_minimum = (float("inf"), None)
    unprojected_negative = 0
    maximum_horizontal = 0.
    sample_count = 0
    for face_index, face in enumerate(faces):
        plate = np.array([coords[node]+state[node] for node in face[:, 0]])
        bar = np.array([coords[node]+state[node] for node in face[:, 1]])
        for xi in roots:
            for eta in roots:
                shape = _quad8_shape(float(xi), float(eta))
                plate_point = shape@plate
                bar_point = shape@bar
                gap = float(bar_point[2]-plate_point[2])
                horizontal = float(np.linalg.norm(bar_point[:2]-plate_point[:2]))
                sample_count += 1
                maximum_horizontal = max(maximum_horizontal, horizontal)
                negative += gap < 0.
                if gap < 0.:
                    matched = _same_xy_plate_gap(
                        plate, bar_point, float(xi), float(eta))
                    if matched is None:
                        unprojected_negative += 1
                    else:
                        physical_gap, parameters, xy_defect = matched
                        reprojected_count += 1
                        reprojected_negative += physical_gap < 0.
                        if physical_gap < reprojected_minimum[0]:
                            reprojected_minimum = (
                                physical_gap,
                                (face_index, float(xi), float(eta),
                                 parameters.tolist(), xy_defect,
                                 bar_point.tolist()))
                if gap < minimum[0]:
                    minimum = (gap, (face_index, float(xi), float(eta),
                                     plate_point.tolist(), bar_point.tolist(),
                                     horizontal))
    return {"sample_count": sample_count,
            "negative_vertical_gap_sample_count": negative,
            "minimum_paired_parametric_vertical_gap_m": minimum[0],
            "minimum_sample": minimum[1],
            "same_xy_projected_parametric_negative_count": reprojected_count,
            "same_xy_negative_among_projected_count": reprojected_negative,
            "same_xy_minimum_among_projected_m": reprojected_minimum[0]
                if reprojected_minimum[1] is not None else None,
            "same_xy_minimum_among_projected_sample": reprojected_minimum[1],
            "unprojected_negative_pair_count": unprojected_negative,
            "maximum_paired_horizontal_mismatch_m": maximum_horizontal,
            "meaning": "only initially negative paired-parametric bar Q8 samples are reprojected to the same deformed XY inside paired plate Q8 faces; negative same-XY values among that subset witness sampled surface-order overlap under retained face orientation, not contact traction or a global penetration certificate"}


def _same_xy_plate_gap(plate, bar_point, xi, eta):
    """Project a bar-face sample into one deformed plate face in XY."""
    parameters = np.array((xi, eta), dtype=float)
    h = 1e-6
    for _ in range(12):
        shape = _quad8_shape(*parameters)
        plate_point = shape@plate
        defect = bar_point[:2]-plate_point[:2]
        if np.linalg.norm(defect) < 1e-12:
            break
        derivatives = np.column_stack((
            ((_quad8_shape(parameters[0]+h, parameters[1])-
              _quad8_shape(parameters[0]-h, parameters[1]))/(2*h))@
            plate[:, :2],
            ((_quad8_shape(parameters[0], parameters[1]+h)-
              _quad8_shape(parameters[0], parameters[1]-h))/(2*h))@
            plate[:, :2],
        ))
        if np.linalg.cond(derivatives) > 1e8:
            return None
        parameters += np.linalg.solve(derivatives, defect)
        if np.max(np.abs(parameters)) > 1.01:
            return None
    shape = _quad8_shape(*parameters)
    plate_point = shape@plate
    xy_defect = float(np.linalg.norm(bar_point[:2]-plate_point[:2]))
    if xy_defect > 1e-11 or np.max(np.abs(parameters)) > 1.-1e-10:
        return None
    return float(bar_point[2]-plate_point[2]), parameters, xy_defect


def evaluate():
    recon = json.loads(SPLIT.read_text())
    if recon["status"] != "EXPLORATORY_COMPLETE":
        raise ValueError("complete split reconstruction required")
    deck, _, coords, _, _, _ = _source(SOURCE / "tip_mx")
    plate, bar = _element_domain_nodes(deck)
    faces, historical = _mapped_faces(coords, plate, bar)
    unit = [_bound_field(RESPONSES / f"channel-{j}",
                         recon["unit_records"][j]["frd_sha256"])
            for j in range(12)]
    if any(set(field) != set(coords) for field in unit):
        raise ValueError("unit field topology changed")
    scale = np.tile(SCALES, 2)
    cases = {}
    for label in ("tip_mx", "tip_fz"):
        decks = list((SOURCE / label).glob("*.inp"))
        if (len(decks) != 1 or digest(decks[0]) !=
                recon["cases"][label]["source_deck_sha256"]):
            raise ValueError("loaded source deck changed")
        base = _bound_field(SOURCE / label,
                            recon["cases"][label]["source_frd_sha256"])
        if set(base) != set(coords):
            raise ValueError("loaded source field topology changed")
        coefficient = np.asarray(recon["cases"][label]["dual_physical"])/scale
        state = {node: base[node]-sum(coefficient[j]*unit[j][node]
                                      for j in range(12))
                 for node in coords}
        cases[label] = _sample_faces(coords, state, faces)
    return {
        "classification": "mapped historical C1 unbonded Q8 face sampling on exact split-law solid fields; development only",
        "status": "EXPLORATORY_COMPLETE", "cases": cases,
        "face_count": len(faces), **historical,
        "inputs_sha256": {str(SPLIT): digest(SPLIT)},
        "source_sha256": digest(Path(__file__)),
        "limitations": ["paired-parametric samples are not closest-point gaps",
                        "negative vertical samples alone do not certify contact without XY overlap",
                        "same-XY counts and minimum cover only initially negative paired-parametric samples",
                        "face Jacobian orientation and full-volume topology are not certified",
                        "positive samples alone do not certify separation between samples",
                        "one linear no-contact grid; no F03/G0B acceptance"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior split face-gap result")
    report = evaluate()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n")
    print(json.dumps({key: {"negative": value["negative_vertical_gap_sample_count"],
                            "minimum_m": value["minimum_paired_parametric_vertical_gap_m"]}
                      for key, value in report["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
