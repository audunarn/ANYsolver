"""Bounded, linearized two-sided pitch references on saved C1 solids.

The existing shared-node top-face bond is unchanged. One equation over the
whole terminal bond, or two equations over its halves, equate the area-mean
through-thickness x-motion gradients of bar and plate. These are external
diagnostics of a declared reduced two-sided joint, not native-line or G0
qualification results.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np
import psutil

from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    EXE, EXE_SHA, _quad8_shape, audit_unbonded_open, digest,
    parse_nodal_vectors, parse_probe_displacements, recover,
    unexpected_solver_diagnostics,
)
from scripts.b3_e4_f03_solid_bond_pose_projection import (
    _read_deck_nodes, _read_frd_u,
)


WORKTREE = Path(__file__).resolve().parents[1]
SOURCE_HASHES = {
    2: ("54eb26899e371bfa2a2bc8910ab6ffcc4b4cd61374980e3b9abd1bbb32676a3e",
        "9726e26e57f9f13bae15a2995f59e0c6f636486147ea14175021204ee77cff90"),
    4: ("e0143e59c05c2b9182fdbd2b4f4df75ff7224dddc8be32bf6bb14b00bfe3c9fd",
        "e06f4a4b9e7e35541f5e5de7afb4f4dd2f44bb9ed3cc8a16972aa37974883ecc"),
    5: ("a9d7ba21525f1177e4e75bc2b4c8a657806de4bfe0e993049999bfe580a8d28b",
        "bf41b8bd670243c59d1d63a73b137304f515a94e123e58d687bbd807ea39cf75"),
}
MEMORY_LIMIT_BYTES = 2 * 1024**3
TIME_LIMIT_SECONDS = 120


def _weights(coords: dict[int, np.ndarray], z: float,
             factor: int, interval: tuple[float, float] = (.9, 1.)) -> dict[int, float]:
    """Reference-area Q8 weights on one flat mesh-aligned surface."""
    lookup: dict[tuple[float, float, float], list[int]] = defaultdict(list)
    for node, xyz in coords.items():
        lookup[tuple(np.round(xyz, 9))].append(node)

    def node(x: float, y: float) -> int:
        ids = lookup.get(tuple(np.round((x, y, z), 9)), ())
        if len(ids) != 1:
            raise ValueError(f"ambiguous surface node at {(x, y, z)}: {len(ids)}")
        return ids[0]

    low, high = interval
    xs = (np.linspace(.9, 1., factor+1) if interval == (.9, 1.) else
          np.linspace(low, high, round(factor*(high-low)/.1)+1))
    ys = np.linspace(-.05, .05, 2*factor+1)
    roots, gauss = np.polynomial.legendre.leggauss(3)
    weights: dict[int, float] = defaultdict(float)
    for x0, x1 in zip(xs[:-1], xs[1:]):
        for y0, y1 in zip(ys[:-1], ys[1:]):
            xm, ym = (x0+x1)/2, (y0+y1)/2
            ids = (node(x0,y0), node(x1,y0), node(x1,y1), node(x0,y1),
                   node(xm,y0), node(x1,ym), node(xm,y1), node(x0,ym))
            area_fourfold = (.04 if interval == (.9, 1.) else
                             4*(high-low)*.1)
            scale = (x1-x0)*(y1-y0)/area_fourfold
            for xi, wx in zip(roots, gauss):
                for eta, wy in zip(roots, gauss):
                    shape = _quad8_shape(float(xi), float(eta))
                    for idx, value in zip(ids, scale*wx*wy*shape):
                        weights[idx] += float(value)
    if abs(sum(weights.values())-1.) > 1e-12:
        raise AssertionError("surface integration lost unit constant field")
    return dict(weights)


def _equation(coords: dict[int, np.ndarray], supports: set[int],
              factor: int, interval: tuple[float, float] = (.9, 1.),
              reserved: frozenset[int] = frozenset()
              ) -> tuple[list[tuple[int, float]], dict]:
    # theta_b - theta_s = (u_x^bar,top-u_x^bar,bottom)/.1
    #                  - (u_x^plate,top-u_x^plate,bottom)/.035.
    surfaces = (
        ("plate_bottom", -.0175, +1/.035),
        ("plate_top", +.0175, -1/.035),
        ("bar_bottom", +.0175, -1/.1),
        ("bar_top", +.1175, +1/.1),
    )
    coefficients: dict[int, float] = defaultdict(float)
    groups = {}
    for name, z, scale in surfaces:
        weights = _weights(coords, z, factor, interval)
        groups[name] = {node: scale*weight for node, weight in weights.items()}
        for node, value in groups[name].items():
            coefficients[node] += value
    if any(node in supports for node in coefficients):
        raise AssertionError("pitch equation touches a directly supported node")
    if interval == (.9, 1.) and not reserved:
        dependent = max(groups["plate_bottom"],
                        key=lambda node: abs(coefficients[node]))
    else:
        low, high = interval
        candidates = [node for node in groups["plate_bottom"]
                      if low+1e-12 < coords[node][0] < high-1e-12 and
                      node not in reserved and abs(coefficients[node]) > 1e-15]
        if not candidates:
            raise ValueError("sided interval lacks independent interior equation node")
        dependent = max(candidates, key=lambda node: abs(coefficients[node]))
    terms = [(dependent, coefficients.pop(dependent))] + sorted(
        ((node, value) for node, value in coefficients.items()
         if abs(value) > 1e-15))
    result = {"interval_m": list(interval),
              "translation_x": sum(c for _, c in terms),
              "rigid_y_rotation": sum(c*coords[n][2] for n,c in terms),
              "rigid_z_rotation": -sum(c*coords[n][1] for n,c in terms),
              "group_force_x": {name: sum(g.values())
                                for name,g in groups.items()},
              "group_moment_y": {name: sum(c*coords[n][2]
                                           for n,c in g.items())
                                 for name,g in groups.items()},
              "dependent_node": dependent,
              "term_count": len(terms),
              "meaning": "one unit equation multiplier gives opposite unit My on plate and bar; zero global force/moment"}
    if (max(abs(result[k]) for k in
            ("translation_x", "rigid_y_rotation", "rigid_z_rotation")) > 1e-11 or
            abs(sum(result["group_moment_y"].values())) > 1e-11 or
            abs(sum(result["group_force_x"].values())) > 1e-11):
        raise AssertionError("pitch equation violates rigid motion or wrench work")
    witness = sum(c*(-.035) for n,c in groups["plate_bottom"].items())
    if abs(witness+1.) > 1e-11:
        raise AssertionError("top-fixed director witness not detected")
    result["top_fixed_unit_pitch_witness"] = witness
    return terms, result


def _cards(terms: list[tuple[int, float]]) -> str:
    lines = ["*EQUATION", str(len(terms))]
    for start in range(0, len(terms), 4):
        lines.append(",".join(f"{node},1,{coeff:.17g}"
                              for node, coeff in terms[start:start+4]))
    return "\n".join(lines)+"\n"


def _run(stem: str, folder: Path) -> tuple[int | None, bytes, bytes, float, int, str | None]:
    environment = os.environ.copy()
    environment["OMP_NUM_THREADS"] = "1"
    start = time.perf_counter()
    proc = subprocess.Popen((str(EXE), "-i", stem), cwd=folder,
                            env=environment, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    monitor = psutil.Process(proc.pid)
    peak = 0
    failure = None
    while True:
        try:
            peak = max(peak, monitor.memory_info().rss)
        except psutil.NoSuchProcess:
            pass
        elapsed = time.perf_counter()-start
        if peak > MEMORY_LIMIT_BYTES:
            failure = "MEMORY_LIMIT_2_GIB"
        elif elapsed > TIME_LIMIT_SECONDS:
            failure = "TIMEOUT_120_SECONDS"
        if failure:
            proc.kill()
            stdout, stderr = proc.communicate()
            return None, stdout, stderr, elapsed, peak, failure
        try:
            stdout, stderr = proc.communicate(timeout=.5)
            return proc.returncode, stdout, stderr, time.perf_counter()-start, peak, None
        except subprocess.TimeoutExpired:
            continue


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--factor", type=int, choices=tuple(SOURCE_HASHES), required=True)
    parser.add_argument("--print-dependent-reaction", action="store_true")
    parser.add_argument("--pitch-intervals", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    if args.print_dependent_reaction and (args.factor,args.pitch_intervals) not in (
            (2, 1), (4, 2)):
        raise ValueError("bounded direct-reaction probe requires F2 single or F4 split")
    if args.pitch_intervals == 2 and args.factor != 4:
        raise ValueError("bounded two-interval sided diagnostic is F4 only")
    root = args.output_root.resolve()
    if root.exists():
        raise FileExistsError(root)
    factor = args.factor
    source = (WORKTREE / ".qualification/b3-ge-e4-pl/"
              f"f03-ccx-c1-preopen-combined-factor{factor}-dev-20260926-v1/"
              f"solid-{factor}-tip_mx")
    source_deck = source/f"solid-{factor}-tip_mx.inp"
    source_model = source/"model.json"
    deck_sha, model_sha = SOURCE_HASHES[factor]
    if (digest(source_deck) != deck_sha or
            digest(source_model) != model_sha or
            digest(EXE) != EXE_SHA):
        raise ValueError("saved F5 deck, model or solver identity changed")
    meta = json.loads(source_model.read_text())
    if (meta["factor"] != factor or meta["bond_policy"] != "terminal" or
            meta["plate_thickness_m"] != .035 or
            meta["bar_reference_profile"] != "C1_TWO_QUADRATIC_TANGENT_ALIGNED_V1"):
        raise ValueError("unexpected physical F5 model")
    coords = _read_deck_nodes(source_deck)
    intervals = (((.9, 1.),) if args.pitch_intervals == 1 else
                 ((.9, .95), (.95, 1.)))
    equations = []
    mechanics_list = []
    reserved = set()
    for interval in intervals:
        terms, mechanics = _equation(
            coords, set(meta["boundary_node_ids"]), factor, interval,
            frozenset(reserved))
        equations.append(terms)
        mechanics_list.append(mechanics)
        reserved.add(mechanics["dependent_node"])
    deck = source_deck.read_text()
    marker = "*MATERIAL,NAME=Isotropic"
    if deck.count(marker) != 1:
        raise ValueError("material insertion point changed")
    stem = (f"solid-{factor}-sided-pitch" if args.pitch_intervals == 1 else
            f"solid-{factor}-sided-pitch-two-intervals")
    inserted = "".join(_cards(terms) for terms in equations)+marker
    if args.print_dependent_reaction:
        names = (["PitchDependent"] if args.pitch_intervals == 1 else
                 [f"PitchDependent{i+1}" for i in range(len(equations))])
        inserted = "".join(
            f"*NSET,NSET={name}\n{mechanics['dependent_node']}\n"
            for name,mechanics in zip(names,mechanics_list))+inserted
        if deck.count("*END STEP") != 1:
            raise ValueError("output insertion point changed")
        deck = deck.replace("*END STEP",
                            "".join(f"*NODE PRINT,NSET={name}\nRF\n"
                                    for name in names)+"*END STEP")
    root.mkdir(parents=True)
    (root/(stem+".inp")).write_text(deck.replace(marker, inserted))
    (root/"model.json").write_text(json.dumps(meta, sort_keys=True, indent=2)+"\n")
    code, stdout, stderr, elapsed, peak, failure = _run(stem, root)
    (root/"stdout.log").write_bytes(stdout)
    (root/"stderr.log").write_bytes(stderr)
    response = None
    if failure is None and code != 0:
        failure = f"CALCULIX_EXIT_{code}"
    if failure is None:
        try:
            out = stdout.decode(errors="replace")
            err = stderr.decode(errors="replace")
            cvg = (root/(stem+".cvg")).read_text(errors="replace")
            diagnostics = unexpected_solver_diagnostics(out+err+cvg,
                                                        c1_penalty=False)
            if out.count("Job finished") != 1 or diagnostics:
                raise ValueError(f"solver incomplete or diagnostics: {diagnostics[:5]}")
            dat = (root/(stem+".dat")).read_text()
            probes = parse_probe_displacements(dat,set(meta["probe_node_ids"]))
            reactions = parse_nodal_vectors(dat,set(meta["boundary_node_ids"]),
                                            "forces",meta["support_set"])
            response = recover(meta,probes,reactions)
            expected = {node for pair in meta["unbonded_interface_pairs"]
                        for node in pair}
            interface = parse_nodal_vectors(dat, expected,"displacements",
                                            "UNBONDEDINTERFACE")
            response["unbonded_open_audit"] = audit_unbonded_open(meta,interface)
            field = _read_frd_u(root/(stem+".frd"))
            if set(field) != set(coords):
                raise ValueError("incomplete full-field displacement")
            gaps = [sum(c*field[node][0] for node,c in terms)
                    for terms in equations]
            if args.pitch_intervals == 1:
                response["sided_pitch_equation_rad"] = gaps[0]
            else:
                response["sided_pitch_equations_rad"] = gaps
            if args.print_dependent_reaction:
                printed = [parse_nodal_vectors(
                    dat,{mechanics["dependent_node"]},"forces",name.upper())[
                        mechanics["dependent_node"]].tolist()
                    for name,mechanics in zip(names,mechanics_list)]
                if args.pitch_intervals == 1:
                    response["dependent_node_printed_force_N"] = printed[0]
                    response["dependent_node_coefficient_per_m"] = equations[0][0][1]
                else:
                    response["dependent_node_printed_forces_N"] = printed
                    response["dependent_node_coefficients_per_m"] = [
                        terms[0][1] for terms in equations]
        except (OSError, ValueError, KeyError) as exc:
            failure = f"PARSE_{type(exc).__name__}: {exc}"
    result = {
        "classification": "bounded physically explicit two-sided linear pitch external diagnostic; not G0B acceptance",
        "status": "EXPLORATORY_COMPLETE" if failure is None else "EXPLORATORY_FAILURE",
        "failure": failure, "exit_code": code, "seconds": elapsed,
        "peak_solver_rss_bytes": peak,
        "source_head": subprocess.check_output(("git","rev-parse","HEAD"),
                                               cwd=WORKTREE,text=True).strip(),
        "source_hashes": {str(path.relative_to(WORKTREE)):digest(path)
                          for path in (Path(__file__),source_deck,source_model)},
        "solver_sha256": digest(EXE),
        "mechanics_preflight": (mechanics_list[0] if args.pitch_intervals == 1
                                else mechanics_list),
        "dependent_reaction_probe": args.print_dependent_reaction,
        "equation_node_x_coefficients": (
            [[node,c] for node,c in equations[0]] if args.pitch_intervals == 1
            else [[[node,c] for node,c in terms] for terms in equations]),
        "pitch_intervals_m": [list(interval) for interval in intervals],
        "response": response,
        "limitations": ["linearized area-average pitch, not finite-rotation native pose",
                        f"shared top-face nodes plus {args.pitch_intervals} additional weak two-sided constraint(s)",
                        "solid section deformation and inferred shell director are not native B3/E4 states",
                        "contact and mesh convergence are not qualified"],
    }
    (root/"result.json").write_text(json.dumps(result,sort_keys=True,
                                                indent=2,allow_nan=False)+"\n")
    print(json.dumps({"status":result["status"],"failure":failure,
                      "seconds":elapsed,"peak_solver_rss_bytes":peak,
                      "pitch_equation_rad":None if response is None else
                      (response["sided_pitch_equation_rad"]
                       if args.pitch_intervals == 1 else
                       response["sided_pitch_equations_rad"])}),flush=True)
    return 0 if failure is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
