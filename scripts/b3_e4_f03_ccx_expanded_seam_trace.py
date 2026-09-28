"""Reconstruct bounded flat-web side traces from CalculiX expanded S4 faces.

This is a kinematic development diagnostic, not an interface-force or F03
assessment. In particular, it does not reconstruct the shell drilling DOF.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_ccx_matched_t_reference import (
    PLATE_T_M, WEB_T_M, _frd_fields,
)


def _unit(value: np.ndarray, label: str) -> np.ndarray:
    norm = np.linalg.norm(value)
    if not np.isfinite(norm) or norm <= 1e-12:
        raise ValueError(f"degenerate {label}")
    return value / norm


def reconstruct(manifest: dict, coordinates: dict, displacement: dict) -> dict:
    """Recover material-line/director triads at the native flat-web seam."""
    if (manifest.get("profile") != "native_line_geometry" or
            manifest.get("variant") != "flat" or
            manifest.get("domain", "coupled") != "coupled" or
            manifest.get("nx") not in (4, 8, 16)):
        raise ValueError("coupled native-line flat-web manifest required")
    nx = manifest["nx"]
    if set(coordinates) != set(displacement):
        raise ValueError("complete expanded displacement field required")
    points = {int(n): np.asarray(x, dtype=float) for n, x in coordinates.items()}
    moved = {int(n): points[int(n)]+np.asarray(u, dtype=float)
             for n, u in displacement.items()}
    if any(x.shape != (3,) or not np.isfinite(x).all()
           for values in (points, moved) for x in values.values()):
        raise ValueError("finite three-dimensional fields required")

    def pair(x: float, y: float, z: float) -> tuple[np.ndarray, np.ndarray]:
        ids = [n for n, p in points.items()
               if np.max(np.abs(p-np.array((x, y, z)))) <= 1e-7]
        if len(ids) != 1:
            raise ValueError("unique expanded shell face node required")
        n = ids[0]
        return points[n], moved[n]

    reference = []
    current = []
    for i in range(nx+1):
        x = i/nx
        plate_low = pair(x, 0., -PLATE_T_M/2)
        plate_top = pair(x, 0., PLATE_T_M/2)
        web_low = pair(x, -WEB_T_M/2, PLATE_T_M/2)
        web_high = pair(x, WEB_T_M/2, PLATE_T_M/2)
        for slot, target in ((reference, 0), (current, 1)):
            pl, pt, wl, wh = (v[target] for v in
                              (plate_low, plate_top, web_low, web_high))
            slot.append((pt, _unit(pt-pl, "plate director"),
                         (wl+wh)/2, _unit(wh-wl, "web director")))

    def frames(rows: list[tuple], i: int) -> tuple[np.ndarray, np.ndarray]:
        before, after = ((0, 1) if i == 0 else
                         (nx-1, nx) if i == nx else (i-1, i+1))
        result = []
        for position, director in ((0, 1), (2, 3)):
            normal = rows[i][director]
            raw = rows[after][position]-rows[before][position]
            tangent = _unit(raw-normal*(normal@raw), "material-line tangent")
            result.append(np.column_stack((tangent,
                                           np.cross(normal, tangent), normal)))
        return result[0], result[1]

    samples = []
    for i in range(nx+1):
        plate_ref, web_ref = frames(reference, i)
        plate_cur, web_cur = frames(current, i)
        relative_ref = plate_ref.T@web_ref
        relative_cur = plate_cur.T@web_cur
        samples.append({
            "x_m": i/nx,
            "reference_seam_gap_m": float(np.linalg.norm(
                reference[i][0]-reference[i][2])),
            "current_seam_gap_m": float(np.linalg.norm(
                current[i][0]-current[i][2])),
            "relative_triads_frobenius": float(np.linalg.norm(
                relative_ref.T@relative_cur-np.eye(3))),
        })
    return {
        "classification": "expanded_face_kinematic_diagnostic_not_sided_work",
        "profile": manifest["profile"],
        "nx": nx,
        "sample_count": len(samples),
        "max_reference_seam_gap_m": max(s["reference_seam_gap_m"]
                                        for s in samples),
        "max_current_seam_gap_m": max(s["current_seam_gap_m"]
                                      for s in samples),
        "max_relative_triads_frobenius": max(s["relative_triads_frobenius"]
                                           for s in samples),
        "samples": samples,
        "limitations": [
            "Face-pair directors and finite-difference line tangents are not original shell rotation coordinates.",
            "No sided interface force, moment, virtual work or drilling response is recovered.",
            "Endpoint tangents are one-sided; this diagnostic does not interpolate at L1 Gauss stations.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--frd", type=Path, required=True)
    args = parser.parse_args()
    coordinates, displacement = _frd_fields(args.frd.read_text())
    result = reconstruct(json.loads(args.manifest.read_text()),
                         coordinates, displacement)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
