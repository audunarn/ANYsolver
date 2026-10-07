"""Strict reader for this programme's pinned CCX 2.23 x64 DOUBLE U/RF fixture.

This is an evidence reader, not a general FRD importer or a qualification
adjudicator. Only one linear step, C3D20 geometry and the two declared nodal
datasets are admitted. Binary payloads are consumed by counts, never searched
for text delimiters. Executable identity and completed execution remain the
caller's responsibility. No solver is launched here.
"""
from __future__ import annotations

import math
import struct
from dataclasses import asdict

from scripts.r8_e02_rigid_tip_reference import ReferenceParseError

_VECTOR = struct.Struct("<i3d")
_ELEMENT = struct.Struct("<24i")
# CCX/Abaqus -> FRD he20: bottom edges, vertical edges, then top edges.
_FRD_ORDER = tuple(range(12)) + tuple(range(16, 20)) + tuple(range(12, 16))
MAX_BYTES = 64 * 1024 * 1024
MAX_ROWS = 100_000


def read_double_output(data: bytes, metadata: dict):
    """Return owned U/RF dictionaries after exact geometry/dataset validation."""
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_BYTES:
        raise ReferenceParseError("bounded binary FRD bytes required")
    try:
        nodes = {int(n): tuple(p) for n, p in metadata["physical_nodes"].items()}
        elements = {int(e): tuple(ids) for e, ids in metadata["elements"].items()}
        root = set(metadata["root_nodes"])
        if not (0 < len(nodes) <= MAX_ROWS and 0 < len(elements) <= MAX_ROWS
                and root and root <= nodes.keys()):
            raise ValueError("count or support")
        if any(n <= 0 or len(p) != 3 or not all(math.isfinite(v) for v in p)
               for n, p in nodes.items()):
            raise ValueError("node")
        if any(e <= 0 or len(ids) != 20 or len(set(ids)) != 20
               or not set(ids) <= nodes.keys() for e, ids in elements.items()):
            raise ValueError("element")
        # Reject conversion collisions in caller metadata.
        if len(nodes) != len(metadata["physical_nodes"]) or len(elements) != len(metadata["elements"]):
            raise ValueError("identity")
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ReferenceParseError("invalid expected geometry") from exc

    cursor = 0

    def line():
        nonlocal cursor
        end = data.find(b"\n", cursor, min(len(data), cursor + 257))
        if end < 0:
            raise ReferenceParseError("truncated or oversized ASCII header")
        try:
            value = data[cursor:end].decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise ReferenceParseError("non-ASCII header") from exc
        cursor = end + 1
        return value

    def payload(record, count):
        nonlocal cursor
        end = cursor + record.size * count
        if end > len(data):
            raise ReferenceParseError("truncated binary payload")
        result = list(record.iter_unpack(data[cursor:end]))
        cursor = end
        return result

    def vectors(count, expected):
        values = {}
        for n, *v in payload(_VECTOR, count):
            if n not in expected or n in values or not all(math.isfinite(x) for x in v):
                raise ReferenceParseError("unexpected, duplicate or nonfinite binary node")
            values[n] = tuple(v)
        if values.keys() != expected:
            raise ReferenceParseError("missing binary node")
        return values

    if line() != "1C":
        raise ReferenceParseError("missing FRD header")
    headers = []
    for _ in range(24):
        header = line()
        if header.startswith("2C"):
            break
        if not header.startswith("1U"):
            raise ReferenceParseError("unexpected geometry header")
        headers.append(header)
    else:
        raise ReferenceParseError("missing coordinate block")
    if (sum(h == "1UPGM               CalculiX" for h in headers) != 1
            or sum(h == "1UVERSION           Version 2.23" for h in headers) != 1
            or header.split() != ["2C", str(len(nodes)), "3"]):
        raise ReferenceParseError("wrong version, coordinate count or binary64 format")
    coordinates = vectors(len(nodes), nodes.keys())
    # CalculiX reconstructs some midside coordinates (a few binary64 ulps).
    # This is only a framing/geometry identity check, not a mechanics tolerance.
    coordinate_floor = 8 * math.ulp(max(abs(x) for p in nodes.values() for x in p))
    if any(abs(a - b) > coordinate_floor for n, p in nodes.items()
           for a, b in zip(coordinates[n], p)):
        raise ReferenceParseError("changed binary reference coordinates")
    if line().split() != ["3C", str(len(elements)), "2"]:
        raise ReferenceParseError("wrong element count or binary integer format")
    seen = set()
    for e, kind, group, material, *ids in payload(_ELEMENT, len(elements)):
        if (e in seen or e not in elements or (kind, group, material) != (4, 0, 1)
                or tuple(ids) != tuple(elements[e][j] for j in _FRD_ORDER)):
            raise ReferenceParseError("changed element identity, type or connectivity")
        seen.add(e)
    if seen != elements.keys():
        raise ReferenceParseError("missing binary element")

    datasets = []
    for step, (name, components, expected) in enumerate((
            ("DISP", "D", nodes.keys()), ("FORC", "F", root)), 1):
        if line().split() != ["1PSTEP", str(step), "1", "1"]:
            raise ReferenceParseError("unexpected dataset step")
        h = line().split()
        if (len(h) != 7 or h[:2] != ["100CL", "101"]
                or h[2] != "1.000000000" or h[3:] != [str(len(expected)), "0", "1", "3"]):
            raise ReferenceParseError("unexpected time, count or binary64 dataset format")
        if line().split() != ["-4", name, "4", "1"]:
            raise ReferenceParseError("unexpected vector label")
        for j in range(1, 4):
            if line().split() != ["-5", components + str(j), "1", "2", str(j), "0"]:
                raise ReferenceParseError("unexpected vector component")
        # ALL is a computed magnitude; it has no fourth stored binary value.
        if line().split() != ["-5", "ALL", "1", "2", "0", "0", "1ALL"]:
            raise ReferenceParseError("unexpected computed magnitude")
        datasets.append(vectors(len(expected), expected))
    if line() != "9999" or cursor != len(data):
        raise ReferenceParseError("unexpected footer or trailing data")
    return tuple(datasets)


def compare_double_with_print(data, dat, stdout, metadata, area):
    """Cross-check printed observations and report raw physical balance/work.

    Caller must bind metadata/area to the executed deck. No acceptance status
    or convergence claim is assigned. Positions for moments come from the
    original input, not reconstructed FRD midside coordinates.
    """
    from scripts.r8_e02_distributing_feasibility import _parse_observed
    from scripts.r8_e02_rigid_tip_reference import _HEADER, _printed_number

    expected = dict(metadata)
    expected["physical_nodes"] = {int(n): tuple(p) for n, p in metadata["physical_nodes"].items()}
    u, rf = read_double_output(data, metadata)
    printed = _parse_observed(dat, stdout, expected, area)
    headers = list(_HEADER.finditer(dat))
    max_fraction = {}
    by_key = {("displacements", "ALL"): u, ("forces", "ROOT"): rf}
    for i, h in enumerate(headers):
        values = by_key[h[1].lower(), h[2].upper()]
        end = headers[i+1].start() if i+1 < len(headers) else len(dat)
        fractions = []
        for row in dat[h.end():end].splitlines():
            if not row.strip():
                continue
            fields = row.split()
            for actual, text in zip(values[int(fields[0])], fields[1:]):
                center, bound, _ = _printed_number(text)
                delta = abs(actual - center)
                # Binary conversion of a decimal half-ulp bound is inexact.
                if delta > bound + 4 * max(math.ulp(actual), math.ulp(center)):
                    raise ReferenceParseError("binary output outside printed resolution bound")
                fractions.append(delta / bound)
        max_fraction[h[1]] = max(fractions)

    def cross(a, b):
        return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

    moments = [cross(expected["physical_nodes"][n], f) for n, f in rf.items()]
    root_wrench = tuple(math.fsum(f[j] for f in rf.values()) for j in range(3)) + tuple(
        math.fsum(m[j] for m in moments) for j in range(3))
    force = tuple(metadata["applied_wrench"][:3])
    couple = tuple(metadata["applied_wrench"][3:])
    lever = cross(metadata["port_m"], force)
    applied = force + tuple(couple[j] + lever[j] for j in range(3))
    error = tuple(a+b for a, b in zip(root_wrench, applied))
    action = area.action(force, couple)
    return dict(status="PARSED_DEVELOPMENT_ONLY", binary_format="little-endian int32/float64",
        displacement_count=len(u), reaction_count=len(rf),
        printed_bound_max_fraction=max_fraction,
        observable=asdict(area.recover(u)), external_final_pairing_J=action.work(u),
        root_wrench_about_origin=root_wrench, root_wrench_error=error,
        root_displacement_max=max(abs(v) for n in metadata["root_nodes"] for v in u[n]),
        printed_comparison=printed,
        scope="output precision and raw balance only; no acceptance or discretization claim")
