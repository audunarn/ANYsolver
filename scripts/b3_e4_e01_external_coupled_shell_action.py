"""Recover the missing external coupled-shell action on the saved E01 8x4 model.

Reuses the existing OpenSees point-model generator without changing its mesh,
loads, section or link law. This is development evidence, not E01 acceptance.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

from scripts.b3_e4_e01_opensees_point_canary import solve


INTERVALS = 8
TRANSVERSE = 4
SHELL_ELEMENTS = INTERVALS*TRANSVERSE


def _sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


class CaptureShellForces:
    def __init__(self, ops):
        self.ops = ops
        self.shell_forces = {}

    def __getattr__(self, name):
        return getattr(self.ops, name)

    def eleResponse(self, tag, response):
        value = self.ops.eleResponse(tag, response)
        if response == "globalForce" and 1 <= tag <= SHELL_ELEMENTS:
            if tag in self.shell_forces:
                raise ValueError("duplicate shell element-force recovery")
            row = tuple(float(v) for v in value)
            if len(row) != 24 or not all(map(math.isfinite, row)):
                raise ValueError("finite 24-coordinate shell force required")
            self.shell_forces[tag] = row
        return value


def _node(row, column):
    return 1+row*(INTERVALS+1)+column


def _position(row, column):
    return (2.*column/INTERVALS, -.5+row/TRANSVERSE, 0.)


def _assemble(captured):
    if set(captured) != set(range(1, SHELL_ELEMENTS+1)):
        raise ValueError("complete external shell element-force inventory required")
    action = {_node(row, column): [0.]*6
              for row in range(TRANSVERSE+1)
              for column in range(INTERVALS+1)}
    for row in range(TRANSVERSE):
        for column in range(INTERVALS):
            tag = 1+row*INTERVALS+column
            corners = (_node(row, column), _node(row, column+1),
                       _node(row+1, column+1), _node(row+1, column))
            forces = captured[tag]
            for local, node in enumerate(corners):
                for axis in range(6):
                    action[node][axis] += forces[6*local+axis]
    return action


def _resultant(action):
    force = [sum(row[d] for row in action.values()) for d in range(3)]
    moment = [0.]*3
    for node, row in action.items():
        index = node-1
        position = _position(index//(INTERVALS+1), index%(INTERVALS+1))
        arm = _cross(position, row[:3])
        for axis in range(3):
            moment[axis] += row[axis+3]+arm[axis]
    return force, moment


def main(site, native_file, action_file, report_file):
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("the pinned OpenSees binary requires Python 3.12")
    if action_file.exists() or report_file.exists():
        raise FileExistsError("preserve earlier E01 action evidence")
    sys.path.insert(0, str(site))
    import openseespy.opensees as ops
    from openseespywin import opensees as core

    native_bytes = native_file.read_bytes()
    native = json.loads(native_bytes)
    if (native.get("classification") !=
            "E01 same-action shell covector; development only" or
            native.get("shell_intervals") != INTERVALS or
            native.get("transverse_intervals") != TRANSVERSE):
        raise ValueError("incompatible native coupled shell action")
    proxy = CaptureShellForces(ops)
    try:
        coupled = solve(proxy, +1, INTERVALS, TRANSVERSE)
    finally:
        ops.wipe()
    shell_action = _assemble(proxy.shell_forces)
    displacement = {int(k): v for k, v in coupled["node_displacements"].items()}
    if set(shell_action) != set(map(int, native["loads"])):
        raise ValueError("external/native shell-node identities differ")
    work = sum(sum(force[d]*displacement[node][d] for d in range(6))
               for node, force in shell_action.items())
    if not math.isfinite(work) or work < 0. or work > coupled[
            "element_internal_virtual_work_j"]*(1.+1e-8):
        raise ValueError("external coupled shell work inventory inconsistent")
    root_nodes = {_node(row, 0) for row in range(TRANSVERSE+1)}
    free_action = {node: ([0.]*6 if node in root_nodes else row)
                   for node, row in shell_action.items()}
    free_work = sum(sum(force[d]*displacement[node][d] for d in range(6))
                    for node, force in free_action.items())
    if abs(free_work-work) > 1e-12*max(abs(work), 1.):
        raise ValueError("external root displacement should do no shell work")
    native_action = {int(k): v for k, v in native["loads"].items()}
    delta = {node: [free_action[node][d]-native_action[node][d]
                    for d in range(6)] for node in free_action}
    external_force, external_moment = _resultant(free_action)
    native_force, native_moment = _resultant(native_action)
    action_record = {
        "classification": "E01 same-action shell covector; development only",
        "source_sha256": _sha(__file__),
        "load_source": "external OpenSees coupled +1000 N beam-tip x, 8x4",
        "shell_intervals": INTERVALS,
        "transverse_intervals": TRANSVERSE,
        "loads": {str(node): row for node, row in free_action.items()},
        "external_coupled_shell_displacements": {
            str(node): displacement[node] for node in free_action},
    }
    report = {
        "classification": "E01 external coupled shell-action development only",
        "source_sha256": _sha(__file__),
        "point_runner_sha256": _sha(Path(__file__).with_name(
            "b3_e4_e01_opensees_point_canary.py")),
        "native_action_sha256": sha256(native_bytes).hexdigest(),
        "opensees_version": ops.version(),
        "binary_sha256": _sha(core.__file__),
        "python": sys.version.split()[0],
        "shell_internal_work_j": work,
        "coupled_element_work_j": coupled["element_internal_virtual_work_j"],
        "coupled_applied_work_j": coupled["applied_virtual_work_j"],
        "coupled_max_link_gap": coupled["maximum_link_gap"],
        "coupled_support_force_error_n": coupled["support_force_residual_n"],
        "coupled_support_moment_error_nm": coupled["support_moment_residual_nm"],
        "external_free_shell_force_n": external_force,
        "external_free_shell_moment_nm": external_moment,
        "native_free_shell_force_n": native_force,
        "native_free_shell_moment_nm": native_moment,
        "max_abs_action_difference_by_channel": [
            max(abs(row[d]) for row in delta.values()) for d in range(6)],
        "external_bond_action": {
            str(_node(0, column)): free_action[_node(0, column)]
            for column in range(INTERVALS+1)},
        "native_bond_action": {
            str(_node(0, column)): native_action[_node(0, column)]
            for column in range(INTERVALS+1)},
        "limit": ("Same external 8x4 point model and positive offset; action "
                  "recovery still requires independent shell-only replay "
                  "before causal interpretation. Different shell formulations."),
    }
    action_file.write_text(json.dumps(action_record, indent=2,
                                      sort_keys=True, allow_nan=False)+"\n")
    report_file.write_text(json.dumps(report, indent=2,
                                      sort_keys=True, allow_nan=False)+"\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True, type=Path)
    parser.add_argument("--native-action", required=True, type=Path)
    parser.add_argument("--action-output", required=True, type=Path)
    parser.add_argument("--report-output", required=True, type=Path)
    args = parser.parse_args()
    result = main(args.site, args.native_action, args.action_output,
                  args.report_output)
    print(json.dumps({"shell_work_j": result["shell_internal_work_j"],
                      "max_abs_action_difference_by_channel":
                      result["max_abs_action_difference_by_channel"]}))
