"""Compare saved native/OpenSees centered-rib responses without gate scoring."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


def _sha(path):
    return sha256(path.read_bytes()).hexdigest()


def _spread(row):
    mean = sum(row)/len(row)
    return (max(row)-min(row))/abs(mean) if mean else None


def main(native_file: Path, external_file: Path, output: Path):
    if output.exists():
        raise FileExistsError("preserve previous centered-rib comparison")
    native = json.loads(native_file.read_bytes())
    external = json.loads(external_file.read_bytes())
    if (native.get("classification") !=
            "V06 centered eccentric rib; development only" or
            external.get("classification") !=
            "V06 independent centered rib; development only" or
            native["geometry"] != external["geometry"] or
            external["failure"] is not None):
        raise ValueError("matched completed centered-rib models required")
    ext = {(case["shell_intervals"], case["offset_sign"],
            case["beam_tip_force_x_n"], case["beam_tip_moment_y_nm"]): case
           for case in external["cases"]}
    if len(ext) != 18:
        raise ValueError("complete distinct external case inventory required")
    rows = []
    for group in native["cases"]:
        if group["linear_factorizations"] != 1:
            raise ValueError("unchanged native operator must factor once")
        for case in group["cases"]:
            key = (group["shell_intervals"], group["offset_sign"],
                   case["beam_tip_force_x_n"],
                   case["beam_tip_moment_y_nm"])
            other = ext.pop(key)
            if (case["support_force_error_n"] > 1e-4 or
                    case["support_moment_error_nm"] > 1e-4 or
                    case["free_equilibrium_ratio"] > 1e-8 or
                    case["constraint_max"] > 1e-9 or
                    other["point_gap_max"] > 1e-10 or
                    other["support_force_error_n"] > 1e-4 or
                    other["support_moment_error_nm"] > 1e-4 or
                    other["work_error_j"] >
                    1e-8*max(abs(other["applied_work_j"]), 1e-12)):
                raise ValueError("unbalanced centered-rib source case")
            row = {"shell_intervals": key[0], "offset_sign": key[1],
                   "beam_tip_force_x_n": key[2],
                   "beam_tip_moment_y_nm": key[3]}
            for name in ("tip_x_m", "tip_ry_rad"):
                a, b = case[name], other[name]
                row[name] = {"native": a, "external": b,
                             "absolute_difference": abs(a-b),
                             "relative_where_nonzero": (abs(a-b)/abs(b)
                                 if abs(b) > 1e-12 else None)}
            nk = case["center_section_shell_curvature_by_row"]
            ek = other["center_section_shell_curvature_by_row"]
            if len(nk) != len(ek):
                raise ValueError("same shell width resolution required")
            row["native_center_curvature_spread_to_mean"] = _spread(nk)
            row["external_center_curvature_spread_to_mean"] = _spread(ek)
            row["center_curvature_max_difference_relative_to_external_peak"] = (
                max(abs(a-b) for a, b in zip(nk, ek))/
                max(abs(b) for b in ek))
            row["native_tip_ry_to_section_theory"] = (
                case["tip_ry_rad"]/case["reference"]["tip_ry_rad"]
                if abs(case["reference"]["tip_ry_rad"]) > 1e-12 else None)
            row["external_tip_ry_to_section_theory"] = (
                other["tip_ry_rad"]/case["reference"]["tip_ry_rad"]
                if abs(case["reference"]["tip_ry_rad"]) > 1e-12 else None)
            rows.append(row)
    if ext or len(rows) != 18:
        raise ValueError("complete native/external case pairing required")
    pure = [row for row in rows if (row["beam_tip_force_x_n"] == 0.) !=
            (row["beam_tip_moment_y_nm"] == 0.)]
    report = {
        "classification": "V06 centered native/external comparison; development only",
        "source_sha256": _sha(Path(__file__)),
        "native_sha256": _sha(native_file),
        "external_sha256": _sha(external_file),
        "geometry": native["geometry"],
        "cases": rows,
        "max_pure_tip_x_relative": max(
            row["tip_x_m"]["relative_where_nonzero"] for row in pure),
        "max_pure_tip_ry_relative": max(
            row["tip_ry_rad"]["relative_where_nonzero"] for row in pure),
        "max_all_tip_x_relative": max(
            row["tip_x_m"]["relative_where_nonzero"] for row in rows),
        "max_all_tip_ry_relative": max(
            row["tip_ry_rad"]["relative_where_nonzero"] for row in rows),
        "limit": ("Different shell formulations and a point-connected 2D "
                  "strip; the homogeneous 1D section formula is not an "
                  "exact comparator. No E01/V06 acceptance inference."),
    }
    output.write_text(json.dumps(report, indent=2, sort_keys=True,
                                 allow_nan=False)+"\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", required=True, type=Path)
    parser.add_argument("--external", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = main(args.native, args.external, args.output)
    print(json.dumps({key: result[key] for key in
                      ("max_pure_tip_x_relative", "max_pure_tip_ry_relative",
                       "max_all_tip_x_relative", "max_all_tip_ry_relative")}))
