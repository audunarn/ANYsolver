"""Two-load OpenSees shell-only discriminator for E01 secondary rotations.

The prescribed eight-cell geometry and root supports match the point-panel
screen. No beam or connection is present. This is development evidence only.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

from b3_e4_e01_opensees_point_canary import E, NU, SHELL_THICKNESS, _cross


INTERVALS = 8
LOAD_N = 1000.


def _geometry(transverse_intervals: int):
    def node_id(row, col):
        return 1 + row * (INTERVALS + 1) + col

    nodes = {node_id(row, col): (2. * col / INTERVALS,
                                -.5 + row / transverse_intervals, 0.)
             for row in range(transverse_intervals + 1)
             for col in range(INTERVALS + 1)}
    elements = tuple((1 + row * INTERVALS + col,
                      node_id(row, col), node_id(row, col + 1),
                      node_id(row + 1, col + 1), node_id(row + 1, col))
                     for row in range(transverse_intervals)
                     for col in range(INTERVALS))
    roots = tuple(node_id(row, 0)
                  for row in range(transverse_intervals + 1))
    return nodes, elements, roots, node_id(0, INTERVALS)


def solve(ops, axis: int | None, loads: dict[int, tuple[float, ...]] | None = None,
          transverse_intervals: int = 1):
    nodes, elements, roots, tip_node = _geometry(transverse_intervals)
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)
    for node, position in nodes.items():
        ops.node(node, *position)
    ops.section("ElasticMembranePlateSection", 1, E, NU,
                SHELL_THICKNESS, 7850.)
    for element in elements:
        ops.element("ASDShellQ4", *element, 1)
    for node in roots:
        ops.fix(node, 1, 1, 1, 1, 1, 1)
    if loads is None:
        assert axis is not None
        loads = {tip_node: tuple(LOAD_N if i == axis else 0.
                                 for i in range(6))}
    if (any(node not in nodes or len(row) != 6
            or not all(map(math.isfinite, row)) for node, row in loads.items())
            or any(any(loads.get(node, (0.,) * 6))
                   for node in roots)):
        raise ValueError("finite free-node shell load vectors required")
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    for node, row in loads.items():
        if any(row):
            ops.load(node, *row)
    ops.constraints("Plain")
    ops.numberer("RCM")
    ops.system("BandGeneral")
    ops.test("NormUnbalance", 1e-8, 20)
    ops.algorithm("Linear")
    ops.integrator("LoadControl", 1.)
    ops.analysis("Static")
    status = ops.analyze(1)
    if status != 0:
        raise RuntimeError(f"OpenSees analyze returned {status}")
    ops.reactions()
    disp = {node: tuple(float(v) for v in ops.nodeDisp(node))
            for node in nodes}
    support = {node: tuple(float(v) for v in ops.nodeReaction(node))
               for node in roots}
    if any(len(row) != 6 or not all(map(math.isfinite, row))
           for row in (*disp.values(), *support.values())):
        raise ValueError("finite six-component outputs required")
    force = tuple(sum(support[node][i] for node in support)
                  for i in range(3))
    moment = tuple(sum(support[node][i + 3]
                       + _cross(nodes[node], support[node][:3])[i]
                       for node in support) for i in range(3))
    load_force = tuple(sum(row[i] for row in loads.values())
                       for i in range(3))
    load_moment = tuple(sum(_cross(nodes[node], row[:3])[i] + row[i + 3]
                            for node, row in loads.items()) for i in range(3))
    force_error = max(abs(force[i] + load_force[i]) for i in range(3))
    moment_error = max(abs(moment[i] + load_moment[i]) for i in range(3))
    work = 0.
    for element, *element_nodes in elements:
        values = tuple(float(v) for v in ops.eleResponse(
            element, "globalForce"))
        if len(values) != 24:
            raise ValueError("24 shell resisting coordinates required")
        work += sum(disp[node][i] * values[6 * j + i]
                    for j, node in enumerate(element_nodes) for i in range(6))
    applied_work = sum(sum(disp[node][i] * row[i] for i in range(6))
                       for node, row in loads.items())
    work_error = abs(work - applied_work)
    if (force_error > 1e-5 or moment_error > 1e-5
            or work_error > 1e-8 * abs(applied_work)):
        raise ValueError(f"balance/work failed: {force_error=:.6g}, "
                         f"{moment_error=:.6g}, {work_error=:.6g}")
    return {"load_axis": axis, "node_displacements": disp,
            "support_reactions": support,
            "force_error_n": force_error,
            "moment_error_nm": moment_error,
            "work_error_j": work_error,
            "applied_work_j": applied_work}


def main(site: Path, output: Path, load_file: Path | None = None,
         transverse_intervals: int = 1):
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("pinned OpenSees binary requires Python 3.12")
    if transverse_intervals not in (1, 4):
        raise ValueError("bounded shell screen admits one or four width cells")
    if output.exists():
        raise FileExistsError("preserve earlier shell-only evidence")
    sys.path.insert(0, str(site))
    import openseespy.opensees as ops
    from openseespywin import opensees as core

    record = {
        "classification": "E01 shell-only discriminator; not acceptance",
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "point_screen_source_sha256": sha256(Path(
            __file__).with_name("b3_e4_e01_opensees_point_canary.py").read_bytes()).hexdigest(),
        "opensees_version": ops.version(), "python": sys.version.split()[0],
        "binary_sha256": sha256(Path(core.__file__).read_bytes()).hexdigest(),
        "shell_intervals": INTERVALS,
        "transverse_intervals": transverse_intervals,
        "cases": [], "failure": None,
    }
    loads = None
    if load_file is not None:
        raw = load_file.read_bytes()
        saved = json.loads(raw)
        if (saved["shell_intervals"] != INTERVALS
                or saved.get("transverse_intervals", 1) != transverse_intervals
                or saved["classification"] !=
                "E01 same-action shell covector; development only"):
            raise ValueError("incompatible native shell action")
        loads = {int(node): tuple(float(v) for v in row)
                 for node, row in saved["loads"].items()}
        record["load_file"] = str(load_file.resolve())
        record["load_sha256"] = sha256(raw).hexdigest()
    try:
        for axis in ((None,) if loads is not None else (1, 2)):
            record["cases"].append(solve(
                ops, axis, loads, transverse_intervals))
    except Exception as exc:
        record["failure"] = f"{type(exc).__name__}: {exc}"
    finally:
        ops.wipe()
        output.write_text(json.dumps(record, sort_keys=True, indent=2,
                                     allow_nan=False) + "\n", encoding="utf-8")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--load-file", type=Path)
    parser.add_argument("--transverse-intervals", type=int, default=1)
    args = parser.parse_args()
    result = main(args.site, args.output, args.load_file,
                  args.transverse_intervals)
    print(json.dumps({"failure": result["failure"],
                      "completed_cases": len(result["cases"])}))
    if result["failure"]:
        raise SystemExit(1)
