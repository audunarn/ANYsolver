"""Parse a bounded CalculiX B31/S4 compatibility canary response.

This does not interpret MPC nodal RF as physical support reactions and does
not compare against a native B3-GE/B2/E4-PL solution.
"""

from __future__ import annotations

import math
import re


_HEADER = re.compile(r"^\s*displacements \([^\n]*\) for set ALLNODES and time\s+([\d.Ee+-]+)\s*$", re.I)
_NODE = re.compile(r"^\s*(\d+)\s+((?:[+-]?\d+(?:\.\d*)?[Ee][+-]?\d+\s*)+)$")
_STEP = re.compile(r"^\s*1\s+1\s+1\s+\d+\s+([\d.Ee+-]+)\s+([\d.Ee+-]+)\s+([\d.Ee+-]+)\s*$")


def parse_completed_response(stdout: str, status: str, dat: str,
                             *, tip_node: int = 48) -> dict:
    """Require one complete linear step and 48 finite nodal translations.

    The printed values have about seven decimal digits. Any later balance,
    compatible station gap, or convergence comparison needs its own parser
    and acceptance contract, including rotational and MPC reaction meaning.
    """
    if stdout.count("Job finished") != 1 or re.search(
            r"(?i)\b(error|fatal|divergence|not converged)\b", stdout):
        raise ValueError("CalculiX job did not finish cleanly")
    status_rows = [line for line in status.splitlines()
                   if re.match(r"^\s*\d+\s+\d+\b", line)]
    matches = [_STEP.match(line) for line in status_rows]
    if (len(matches) != 1 or matches[0] is None or
            any(abs(float(x)-1.) > 1e-8 for x in matches[0].groups())):
        raise ValueError("one full accepted linear increment is required")
    lines = dat.splitlines()
    headers = [(i, m) for i, line in enumerate(lines)
               if (m := _HEADER.match(line))]
    if len(headers) != 1 or abs(float(headers[0][1].group(1))-1.) > 1e-8:
        raise ValueError("one full-step displacement block is required")
    nodes = {}
    rotations = {}
    for line in lines[headers[0][0]+1:]:
        if not line.strip():
            continue
        if re.match(r"^\s*(forces|stresses|displacements)\s*\(", line, re.I):
            break
        match = _NODE.match(line)
        if match is None:
            raise ValueError("malformed displacement row")
        node = int(match.group(1))
        values = tuple(float(s) for s in match.group(2).split())
        if (node in nodes or not 1 <= node <= 48 or len(values) not in (3, 6) or
                any(not math.isfinite(v) for v in values)):
            raise ValueError("invalid nodal displacement")
        nodes[node] = values[:3]
        if len(values) == 6:
            rotations[node] = values[3:]
    if set(nodes) != set(range(1, 49)) or tip_node != 48:
        raise ValueError("incomplete or unexpected displacement inventory")
    tip = nodes[tip_node]
    if not any(abs(v) > 1e-15 for v in tip):
        raise ValueError("zero tip response in loaded canary")
    return dict(accepted_steps=1, printed_nodes=48, tip_translation_m=tip,
                tip_rotation_rad=rotations.get(tip_node),
                printed_six_coordinate_nodes=sorted(rotations),
                output_precision="printed CalculiX DAT, about seven digits")
