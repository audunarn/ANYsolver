"""Inert folded-shell flat-web/T CalculiX supplementary comparator.

Neither root option is a same-law F03 oracle.  The clamped option fixes six
shell DOFs to compare response work with a fixed B3 root, but the verified
CalculiX 2.23 RF print contains translational forces only.  Its force-lever
moment is therefore partial; the hinged option fixes translations only.
The plate/web and web/flange midsurface seams share nodes and shell rotations.
No internal interface traction is inferred from the shared seam.  Each printed
FRD face pair recovers the midsurface translation conjugate to an original
shell CLOAD; DAT RF at translation-only supports gives the total wrench.
No solver is launched by this module.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import isfinite, pi, tanh
from pathlib import Path
import re


E_PA = 210_000_000_000.
NU = .3
PLATE_T_M = .035
WEB_T_M = .01
WEB_H_M = .2
FLANGE_T_M = .01
FLANGE_W_M = .1
FY_N = 100.
TORQUE_NM = 10.
CASES = ("plate_fy", "web_fy", "web_mx")
VARIANTS = ("flat", "t")
_FRD_NUMBER = re.compile(r"[+-]?\d\.\d{5}E[+-]\d{2,3}", re.I)


def _number(value: float) -> str:
    return f"{value:.17g}"


def _wrench(nodes: dict[str, list[float]], terms: list[list[float]]) -> dict:
    force = [0., 0., 0.]
    moment = [0., 0., 0.]
    for node, axis, amount in terms:
        xyz = nodes[str(node)]
        f = [0., 0., 0.]
        f[int(axis)-1] = float(amount)
        for j in range(3):
            force[j] += f[j]
        moment[0] += xyz[1]*f[2]-xyz[2]*f[1]
        moment[1] += xyz[2]*f[0]-xyz[0]*f[2]
        moment[2] += xyz[0]*f[1]-xyz[1]*f[0]
    return {"force_n": force, "moment_nm_about_origin": moment}


def _section(variant: str) -> dict:
    # Web thickness points along y; height points along z.  Iy is about y.
    aw = WEB_T_M*WEB_H_M
    iyw = WEB_T_M*WEB_H_M**3/12.
    izw = WEB_H_M*WEB_T_M**3/12.
    if variant == "flat":
        # Saint-Venant rectangle series, with a=height and b=thickness.
        # This is a geometric B3 target, not a proof of S4 torsion agreement.
        odd_sum = sum(tanh(n*pi*WEB_H_M/(2*WEB_T_M))/n**5
                      for n in range(1, 200, 2))
        j = (WEB_H_M*WEB_T_M**3/3 *
             (1-192*WEB_T_M*odd_sum/(pi**5*WEB_H_M)))
        return {"area_m2": aw, "centroid_y_m": 0.,
                "centroid_z_m": WEB_H_M/2, "Iy_m4": iyw, "Iz_m4": izw,
                "Iyz_m4": 0., "J_rect_m4": j,
                "nominal_shear_area_m2": 5*aw/6,
                "scope": "web_only_b3_section_geometry"}
    af = FLANGE_W_M*FLANGE_T_M
    z = (aw*WEB_H_M/2+af*WEB_H_M)/(aw+af)
    iy = (iyw+aw*(WEB_H_M/2-z)**2+
          FLANGE_W_M*FLANGE_T_M**3/12+af*(WEB_H_M-z)**2)
    iz = izw+FLANGE_T_M*FLANGE_W_M**3/12
    return {"area_m2": aw+af, "centroid_y_m": 0.,
            "centroid_z_m": z, "Iy_m4": iy, "Iz_m4": iz,
            "Iyz_m4": 0., "J_rect_m4": None,
            "nominal_shear_area_m2": None,
            "scope": "t_section_not_web_only_b3"}


def build_bundle(variant: str = "flat", case: str = "web_fy",
                 nx: int = 4, root: str = "clamped") -> tuple[str, dict]:
    """Build one small S4 deck and its exact original-node action inventory."""
    if (variant not in VARIANTS or case not in CASES or
            type(nx) is not int or nx not in (4, 8, 16) or
            root not in ("hinged", "clamped")):
        raise ValueError("bounded flat/T variant, action and x mesh required")
    points: dict[tuple[float, float, float], int] = {}
    nodes: dict[str, list[float]] = {}

    def node(x: float, y: float, z: float) -> int:
        key = tuple(round(v, 12) for v in (x, y, z))
        if key not in points:
            index = len(points)+1
            points[key] = index
            nodes[str(index)] = list(key)
        return points[key]

    plate = [[node(i/nx, -.5+j/4, 0.) for j in range(5)]
             for i in range(nx+1)]
    web = [[node(i/nx, 0., k*WEB_H_M/4) for k in range(5)]
           for i in range(nx+1)]
    flange = ([[node(i/nx, -.05+j*FLANGE_W_M/2, WEB_H_M)
                for j in range(3)] for i in range(nx+1)]
              if variant == "t" else None)

    def cells(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
        return [(grid[i][j], grid[i+1][j], grid[i+1][j+1], grid[i][j+1])
                for i in range(nx) for j in range(len(grid[0])-1)]

    plate_cells, web_cells = cells(plate), cells(web)
    flange_cells = cells(flange) if flange is not None else []
    plate_root = plate[0]
    web_root = web[0]
    flange_root = flange[0] if flange is not None else []
    supports = sorted(set(plate_root+web_root+flange_root))
    loaded = {"plate": plate[-1][3], "web_low": web[-1][1],
              "web_center": web[-1][2], "web_high": web[-1][3]}
    # Low +Fy and high -Fy give +Mx because Mx = -z Fy.
    actions = {
        "plate_fy": [[loaded["plate"], 2, FY_N]],
        "web_fy": [[loaded["web_center"], 2, FY_N]],
        "web_mx": [[loaded["web_low"], 2, TORQUE_NM/.1],
                   [loaded["web_high"], 2, -TORQUE_NM/.1]],
    }
    loaded_sides = {"plate": "plate", "web_low": "web",
                    "web_center": "web", "web_high": "web"}
    lines = ["** INERT S4 FOLDED-SHELL FLAT/T COMPARATOR; NO F03 ACCEPTANCE",
             "** x longitudinal, y plate transverse, z web height; metres/N/Pa",
             "** shared midsurface seams; no separately recoverable interface RF",
             "*NODE,NSET=AllNodes"]
    lines += [f"{n},{','.join(_number(v) for v in nodes[str(n)])}"
              for n in range(1, len(nodes)+1)]
    element = 1
    for name, group in (("Plate", plate_cells), ("Web", web_cells),
                        ("Flange", flange_cells)):
        if not group:
            continue
        lines.append(f"*ELEMENT,TYPE=S4,ELSET={name}")
        for cell in group:
            lines.append(f"{element},{','.join(map(str, cell))}")
            element += 1
    lines += ["*NSET,NSET=Root", ",".join(map(str, supports)),
              "*NSET,NSET=Supports", ",".join(map(str, supports)),
              "*MATERIAL,NAME=Steel", "*ELASTIC", f"{_number(E_PA)},{_number(NU)}"]
    for name, thickness in (("Plate", PLATE_T_M), ("Web", WEB_T_M),
                            ("Flange", FLANGE_T_M)):
        if name == "Flange" and variant == "flat":
            continue
        lines += [f"*SHELL SECTION,ELSET={name},MATERIAL=Steel",
                  _number(thickness)]
    lines += ["*STEP", "*STATIC", "*BOUNDARY",
              "Root,1,6,0" if root == "clamped" else "Root,1,3,0",
              "*CLOAD"]
    lines += [f"{n},{axis},{_number(value)}" for n, axis, value in actions[case]]
    lines += ["*NODE FILE,OUTPUT=3D", "U", "*NODE PRINT,NSET=Supports",
              "RF", "*END STEP"]
    deck = "\n".join(lines)+"\n"
    manifest = {
        "schema": "B3_E4_F03_CCX_MATCHED_FOLDED_SHELL_DEV_V1",
        "classification": ("clamped_root_engineering_work_comparator"
                           if root == "clamped" else
                           "unmatched_supplementary_hinged_root_comparator"),
        "variant": variant, "case": case, "nx": nx, "root": root,
        "nodes_m": nodes, "supports": supports, "plate_root": plate_root,
        "web_root": web_root, "flange_root": flange_root,
        "support_law": ("all x=0 shell nodes: DOFs 1..6 fixed" if root == "clamped"
                        else "all x=0 shell nodes: translations 1..3 fixed; shell rotations free"),
        "six_dof_b3_root_match": root == "clamped",
        "rotational_support_reaction_available": False,
        "loaded_nodes": loaded,
        "loaded_sides": loaded_sides, "actions": actions,
        "action_wrenches": {name: _wrench(nodes, terms)
                            for name, terms in actions.items()},
        "section": _section(variant), "web_only_section": _section("flat"),
        "section_measure": "sum of nominal shell-wall sections; folded-knot overlap not subtracted",
        "section_axes": {"x": "longitudinal", "y": "plate_transverse",
                         "z": "web_height", "Iy": "about_y", "Iz": "about_z"},
        "geometry_m": {"plate_mid_surface": {"x": [0., 1.],
                                               "y": [-.5, .5], "z": 0.},
                       "web_mid_surface": {"x": [0., 1.], "y": 0.,
                                           "z": [0., WEB_H_M]},
                       "flange_mid_surface": ({"x": [0., 1.],
                                               "y": [-FLANGE_W_M/2, FLANGE_W_M/2],
                                               "z": WEB_H_M}
                                              if variant == "t" else None)},
        "web_centroid_offset_from_plate_midplane_m": [0., 0., WEB_H_M/2],
        "plate_thickness_m": PLATE_T_M, "web_thickness_m": WEB_T_M,
        "flange_thickness_m": FLANGE_T_M if variant == "t" else None,
        "shell_elements": {"plate": len(plate_cells), "web": len(web_cells),
                           "flange": len(flange_cells)},
        "node_count": len(nodes), "element_count": element-1,
        "deck_sha256": sha256(deck.encode("ascii")).hexdigest(),
        "limitations": ["shared fold seam; internal sided interface forces unavailable",
                        "S4 finite-thickness shell is not native E4/B3 discretization",
                        "web-only B3 needs these section constants; existing square B3 fixture is different",
                        "rectangle J and nominal shear area do not prove S4/B3 torsion or shear equivalence",
                        "T torsion constant is unresolved; T section is not a B3 target",
                        "hinged option is not a six-DOF B3 root clamp",
                        "clamped option RF excludes unknown rotational support reaction; moment balance is partial",
                        "T flange changes web-only section and centroid",
                        "one linear elastic level is not a converged reference"],
    }
    return deck, manifest


def _frd_vector(line: str) -> tuple[int, tuple[float, float, float]]:
    if not line.startswith(" -1"):
        raise ValueError("invalid ASCII FRD node row")
    node = int(line[3:13])
    values = _FRD_NUMBER.findall(line[13:])
    if node < 1 or len(values) != 3:
        raise ValueError("invalid ASCII FRD vector")
    triple = tuple(float(value) for value in values)
    if not all(isfinite(value) for value in triple):
        raise ValueError("nonfinite ASCII FRD vector")
    return node, triple


def _frd_fields(frd: str) -> tuple[dict[int, tuple], dict[int, tuple]]:
    if type(frd) is not str or len(frd) > 64*1024*1024:
        raise ValueError("bounded ASCII FRD required")
    fields = ("    2C", " -4  DISP")
    result = []
    lines = frd.splitlines()
    for marker in fields:
        starts = [i for i, line in enumerate(lines) if line.startswith(marker)]
        if len(starts) != 1:
            raise ValueError("one FRD mesh and one DISP block required")
        values = {}
        terminated = False
        for line in lines[starts[0]+1:]:
            if line.startswith(" -3"):
                terminated = True
                break
            if line.startswith(" -1"):
                node, vector = _frd_vector(line)
                if node in values:
                    raise ValueError("duplicate FRD node vector")
                values[node] = vector
        if not terminated or not values:
            raise ValueError("incomplete FRD field")
        result.append(values)
    return result[0], result[1]


def _support_forces(dat: str, supports: set[int],
                    node_set: str = "SUPPORTS") -> dict[int, tuple]:
    if type(dat) is not str or len(dat) > 8*1024*1024:
        raise ValueError("bounded CalculiX DAT required")
    lines = dat.splitlines()
    starts = [i for i, line in enumerate(lines)
              if re.search(r"^\s*forces\s*\(fx,fy,fz\)\s*for set "+
                           re.escape(node_set)+r"\b", line, re.I)]
    if len(starts) != 1:
        raise ValueError(f"one {node_set} RF block required")
    result = {}
    for line in lines[starts[0]+1:]:
        parts = line.split()
        if len(parts) == 4 and parts[0].isdigit():
            node = int(parts[0])
            values = tuple(float(v.replace("D", "E")) for v in parts[1:])
            if node in result or not all(isfinite(v) for v in values):
                raise ValueError("invalid or repeated support reaction")
            result[node] = values
        elif result:
            break
    if set(result) != supports:
        raise ValueError("incomplete support reaction inventory")
    return result


def _translation(xyz: list[float], normal: int, thickness: float,
                 coordinates: dict[int, tuple], displacement: dict[int, tuple]
                 ) -> tuple[float, float, float]:
    def at(target):
        return [n for n, value in coordinates.items()
                if max(abs(a-b) for a, b in zip(value, target)) <= 1e-6]
    centre = at(xyz)
    if len(centre) == 1:
        mapped = (centre[0],)
    elif not centre:
        low, high = list(xyz), list(xyz)
        low[normal] -= thickness/2
        high[normal] += thickness/2
        below, above = at(low), at(high)
        if len(below) != 1 or len(above) != 1 or below[0] == above[0]:
            raise ValueError("ambiguous expanded shell face pair")
        mapped = (below[0], above[0])
    else:
        raise ValueError("ambiguous expanded shell centre")
    if any(n not in displacement for n in mapped):
        raise ValueError("loaded shell displacement missing")
    return tuple(sum(displacement[n][axis] for n in mapped)/len(mapped)
                 for axis in range(3))


def parse_outputs(manifest: dict, frd: str, dat: str) -> dict:
    """Recover applied sided work and total support wrench, never seam traction."""
    if type(manifest) is not dict or any(k not in manifest for k in
                                            ("variant", "case", "nx", "root")):
        raise ValueError("generated reference manifest required")
    _, expected = build_bundle(manifest["variant"], manifest["case"],
                               manifest["nx"], manifest["root"])
    if manifest != expected:
        raise ValueError("reference manifest identity changed")
    coordinates, displacement = _frd_fields(frd)
    u = {}
    for name, node in manifest["loaded_nodes"].items():
        side = manifest["loaded_sides"][name]
        u[node] = _translation(manifest["nodes_m"][str(node)],
                               2 if side == "plate" else 1,
                               PLATE_T_M if side == "plate" else WEB_T_M,
                               coordinates, displacement)
    works = {name: sum(value*u[node][axis-1] for node, axis, value in terms)
             for name, terms in manifest["actions"].items()}
    if not all(isfinite(v) for v in works.values()):
        raise ValueError("nonfinite action work")
    reactions = _support_forces(dat, set(manifest["supports"]))
    reaction_terms = [[node, axis, value]
                      for node, vector in reactions.items()
                      for axis, value in enumerate(vector, 1)]
    support = _wrench(manifest["nodes_m"], reaction_terms)
    applied = manifest["action_wrenches"][manifest["case"]]
    balance = {"force_n": [a+b for a, b in zip(
        applied["force_n"], support["force_n"])],
        "moment_nm_about_origin": (None if manifest["root"] == "clamped" else
                                   [a+b for a, b in zip(
                                       applied["moment_nm_about_origin"],
                                       support["moment_nm_about_origin"])])}
    return {"schema": manifest["schema"], "variant": manifest["variant"],
            "case": manifest["case"], "root": manifest["root"],
            "deck_sha256": manifest["deck_sha256"],
            "classification": manifest["classification"],
            "six_dof_b3_root_match": manifest["six_dof_b3_root_match"],
            "action_work_j": works,
            "loaded_case_work_j": works[manifest["case"]],
            "linear_half_work_j": .5*works[manifest["case"]],
            "applied_wrench": applied,
            "support_force_lever_wrench": support,
            "rotational_support_reaction_available": False,
            "support_wrench_complete": manifest["root"] == "hinged",
            "wrench_balance": balance,
            "interpretation": ("applied plate/web action work, not seam interface work; "
                               "clamped-root force-lever moment excludes rotational reactions"
                               if manifest["root"] == "clamped" else
                               "applied plate/web action work, not seam interface work; "
                               "complete support wrench for hinged shell root")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate", help="write inert .inp and .json")
    generate.add_argument("--variant", choices=VARIANTS, default="flat")
    generate.add_argument("--case", choices=CASES, default="web_fy")
    generate.add_argument("--nx", type=int, choices=(4, 8, 16), default=4)
    generate.add_argument("--root", choices=("hinged", "clamped"), default="clamped")
    generate.add_argument("--stem", required=True, type=Path)
    parse = sub.add_parser("parse", help="read existing CalculiX .frd/.dat")
    parse.add_argument("--stem", required=True, type=Path)
    args = parser.parse_args()
    stem = args.stem
    if args.command == "generate":
        deck, manifest = build_bundle(args.variant, args.case, args.nx, args.root)
        # Keep the on-disk deck identical to the bytes hashed in the manifest.
        # Text-mode writes translate LF to CRLF on Windows.
        with stem.with_suffix(".inp").open("xb") as output:
            output.write(deck.encode("ascii"))
        stem.with_suffix(".json").open("x", encoding="utf-8").write(
            json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False)+"\n")
        print(json.dumps({"deck": str(stem.with_suffix(".inp")),
                          "manifest": str(stem.with_suffix(".json")),
                          "deck_sha256": manifest["deck_sha256"]}, sort_keys=True))
    else:
        manifest = json.loads(stem.with_suffix(".json").read_text(encoding="utf-8"))
        deck = stem.with_suffix(".inp").read_bytes()
        if sha256(deck).hexdigest() != manifest.get("deck_sha256"):
            raise ValueError("saved deck identity changed")
        result = parse_outputs(
            manifest, stem.with_suffix(".frd").read_text(errors="replace"),
            stem.with_suffix(".dat").read_text(errors="replace"))
        stem.with_suffix(".result.json").open("x", encoding="utf-8").write(
            json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n")
        print(json.dumps({"result": str(stem.with_suffix(".result.json")),
                          "loaded_case_work_j": result["loaded_case_work_j"],
                          "wrench_balance": result["wrench_balance"]}, sort_keys=True))


if __name__ == "__main__":
    main()
