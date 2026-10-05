"""Sample same-deformed-XY face order in an already executed reverse-Fz solid.

This is a bounded no-contact admissibility screen, not a continuous gap
certificate, contact solution, or beam-shell connection qualification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c1_split_unbonded_gap import _same_xy_plate_gap
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    _quad8_shape, digest, parse_nodal_vectors,
)
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_deck_nodes


BASE = (Path(__file__).resolve().parents[1] / ".qualification" / "b3-ge-e4-pl" /
        "f03-ccx-half-plate-quadratic-face-reverse-fz-dev-20260925-v1")
CASE = "solid-4-tip_fz"


def sample_matching_faces(faces, coordinates, displacement, *, roots=None,
                          face_indices=None):
    """Return interior sampled face order; unmatched same-face points stay unknown."""
    if roots is None:
        roots = np.polynomial.legendre.leggauss(9)[0]
    roots = np.asarray(roots, dtype=float)
    if roots.ndim != 1 or not len(roots) or not np.isfinite(roots).all() or np.max(np.abs(roots)) >= 1:
        raise ValueError("finite interior sample roots required")
    count = projected = negative = 0
    minimum = float("inf")
    maximum_xy_defect = 0.0
    minimum_sample = None
    if face_indices is None:
        face_indices = range(len(faces))
    if len(face_indices) != len(faces):
        raise ValueError("face identity inventory changed")
    for face_index, pairs in zip(face_indices, faces):
        if len(pairs) != 8:
            raise ValueError("eight paired Q8 face nodes required")
        plate = np.array([coordinates[int(p)] + displacement[int(p)]
                          for p, _ in pairs], dtype=float)
        bar = np.array([coordinates[int(b)] + displacement[int(b)]
                        for _, b in pairs], dtype=float)
        if plate.shape != (8, 3) or bar.shape != (8, 3) or not (np.isfinite(plate).all() and np.isfinite(bar).all()):
            raise ValueError("finite Q8 face positions required")
        for xi in roots:
            for eta in roots:
                count += 1
                bar_point = _quad8_shape(float(xi), float(eta)) @ bar
                matched = _same_xy_plate_gap(plate, bar_point, float(xi), float(eta))
                if matched is None:
                    continue
                gap, plate_parameters, xy_defect = matched
                projected += 1
                negative += gap < 0.
                maximum_xy_defect = max(maximum_xy_defect, xy_defect)
                if gap < minimum:
                    minimum = gap
                    minimum_sample = {
                        "face_index": face_index, "bar_parameters": [float(xi), float(eta)],
                        "plate_parameters": plate_parameters.tolist(),
                        "bar_point_m": bar_point.tolist(), "xy_defect_m": xy_defect,
                    }
    return {
        "sample_count": count,
        "same_face_projected_count": projected,
        "unprojected_count": count - projected,
        "negative_same_xy_count": negative,
        "minimum_same_xy_gap_m": minimum if projected else None,
        "minimum_sample": minimum_sample,
        "maximum_projected_xy_defect_m": maximum_xy_defect if projected else None,
        "meaning": "interior bar-face Q8 samples projected to the same deformed XY in their paired plate face; negative values witness surface-order overlap, while nonnegative samples do not certify continuous separation or adjacent-face contact",
    }


def evaluate():
    root = BASE / CASE
    manifest = json.loads((BASE / "result.json").read_text())
    record = next((item for item in manifest if item.get("case") == CASE), None)
    if record is None or record.get("exit_code") != 0:
        raise ValueError("completed saved reverse-Fz case required")
    model_path = root / "model.json"
    meta = json.loads(model_path.read_text())
    faces = meta.get("unbonded_face_pairs", [])
    if (meta.get("factor") != 4 or meta.get("reverse_tip_fz") is not True or
            meta.get("contact_policy") != "none" or len(faces) != 128 or
            meta.get("shear") != "tip_fz"):
        raise ValueError("saved factor-4 detached reverse-Fz geometry required")
    deck = root / f"{CASE}.inp"
    dat = root / f"{CASE}.dat"
    expected = record["files_sha256"]
    for path in (model_path, deck, dat):
        if digest(path) != expected[path.name]:
            raise ValueError(f"saved field identity changed: {path.name}")
    coordinates = _read_deck_nodes(deck)
    face_nodes = {int(node) for face in faces for pair in face for node in pair}
    interface_nodes = {int(node) for pair in meta["unbonded_interface_pairs"]
                       for node in pair}
    displacement = parse_nodal_vectors(dat.read_text(), interface_nodes,
                                       "displacements", "UNBONDEDINTERFACE")
    unavailable = face_nodes - interface_nodes
    if (len(coordinates) != meta["node_count"] or
            not interface_nodes <= set(coordinates) or
            any(int(plate) != int(bar) for face in faces for plate, bar in face
                if int(plate) in unavailable or int(bar) in unavailable)):
        raise ValueError("incomplete saved displacement field")
    available = [(index, face) for index, face in enumerate(faces)
                 if all(int(plate) in displacement and int(bar) in displacement
                        for plate, bar in face)]
    available_faces = [face for _, face in available]
    if any(abs(coordinates[int(bar)][2] - coordinates[int(plate)][2]) > 1e-12
           for face in available_faces for plate, bar in face):
        raise ValueError("reference face gap changed")
    result = sample_matching_faces(available_faces, coordinates, displacement,
                                   face_indices=[index for index, _ in available])
    return {
        "status": "EXPLORATORY_COMPLETE", "case": CASE,
        "saved_field_sha256": {path.name: digest(path) for path in (model_path, deck, dat)},
        "source_sha256": digest(Path(__file__)),
        "saved_face_count": len(faces), "sampled_face_count": len(available_faces),
        "omitted_seam_face_count": len(faces) - len(available_faces),
        "omitted_original_face_indices": [index for index, face in enumerate(faces)
                                          if any(int(plate) not in displacement or
                                                 int(bar) not in displacement
                                                 for plate, bar in face)],
        "unavailable_shared_seam_nodes": len(unavailable),
        "result": result,
        "limitations": ["only interior samples on each face", "same paired face only",
                        "seam-adjacent faces omitted because saved output lacks shared seam displacements",
                        "no continuous deformed-surface separation certificate",
                        "reverse-Fz opening is not a torque/shear reference",
                        "no F03 or G0B acceptance"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous saved-field evidence")
    result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result["result"], sort_keys=True))


if __name__ == "__main__":
    main()
