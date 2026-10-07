"""Matched E02 development reference deck and parser; never runs CalculiX.

The reference is an isotropic C3D20R solid with two rigid bodies.  The entire
physical x >= 0.8 m region is rigid through the thickness; there is no beam.
The corresponding native unloaded beam stub is only a pose/load port.  This
helper supplies development evidence, not E02 qualification or normal-spin
equivalence.  Sector decoupling must be checked from actual matched results.

The caller owns executable hash verification, process/exit/resource supervision,
stderr retention and completed-step checks against .sta.  Pass stderr together
with stdout to parse_result if it is nonempty.  No process is launched here.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from decimal import Decimal, InvalidOperation


CCX_VERSION = "2.23"
CCX_SHA256 = "27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f"
LEVELS = ((10, 4), (20, 8), (40, 16))
LOADS = {
    "Fz": ((0.0, 0.0, 10.0), (0.0, 0.0, 0.0)),
    "Mx": ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
    "My": ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
}
_CORNERS = ((0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0),
            (0, 0, 2), (2, 0, 2), (2, 2, 2), (0, 2, 2))
_EDGES = ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6),
          (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7))
_OFFSETS = _CORNERS + tuple(
    tuple((a + b) // 2 for a, b in zip(_CORNERS[i], _CORNERS[j]))
    for i, j in _EDGES
)


class ReferenceParseError(ValueError):
    """Incomplete, ambiguous, malformed or diagnosed reference output."""


def _hash(value):
    normalized = json.loads(json.dumps(value, allow_nan=False))
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _nset(name, ids):
    return ["*NSET,NSET=" + name] + [
        ",".join(str(node) for node in ids[i:i + 16])
        for i in range(0, len(ids), 16)
    ]


def _geometry_payload(metadata):
    # String keys give exactly the same digest before/after a JSON round trip.
    return {
        "physical_nodes": {str(k): v for k, v in metadata["physical_nodes"].items()},
        "elements": {str(k): v for k, v in metadata["elements"].items()},
        "control_nodes": {str(k): v for k, v in metadata["control_nodes"].items()},
        "controls": metadata["controls"],
        "patch_nodes": metadata["patch_nodes"],
        "root_nodes": metadata["root_nodes"],
        "nx": metadata["nx"], "ny": metadata["ny"], "nz": metadata["nz"],
        "sign": metadata["sign"],
    }


def build_deck(nx, ny, sign, load_name):
    """Return (ASCII deck text, JSON-serializable exact-geometry metadata).

    Only the explicit paired levels (10,4), (20,8), (40,16), nz=2 are supported.
    sign is +1 or -1 and load_name is Fz, Mx or My (case sensitive).
    """
    if (type(nx) is not int or type(ny) is not int or (nx, ny) not in LEVELS):
        raise ValueError("mesh must be one of (10,4), (20,8), (40,16)")
    if isinstance(sign, bool) or sign not in (-1, 1):
        raise ValueError("sign must be -1 or +1")
    if not isinstance(load_name, str) or load_name not in LOADS:
        raise ValueError("load_name must be Fz, Mx or My")
    sign = int(sign)
    nz = 2
    lattice_cells = []
    used = set()
    for ix in range(nx):
        for iy in range(ny):
            for iz in range(nz):
                cell = tuple((2 * ix + dx, 2 * iy + dy, 2 * iz + dz)
                             for dx, dy, dz in _OFFSETS)
                lattice_cells.append(cell)
                used.update(cell)
    lattice_ids = {key: i + 1 for i, key in enumerate(sorted(used))}
    physical = {
        node: (ix / (2 * nx), (iy - ny) / (10 * ny), (iz - nz) / (100 * nz))
        for (ix, iy, iz), node in lattice_ids.items()
    }
    elements = {i + 1: tuple(lattice_ids[key] for key in cell)
                for i, cell in enumerate(lattice_cells)}
    # Integer-lattice selection avoids floating comparison at the .8 boundary.
    patch = sorted(node for (ix, _, _), node in lattice_ids.items() if 5 * ix >= 8 * nx)
    root = sorted(node for (ix, _, _), node in lattice_ids.items() if ix == 0)
    last_physical = len(physical)
    controls = dict(root_ref=last_physical + 1, root_rot=last_physical + 2,
                    patch_ref=last_physical + 3, patch_rot=last_physical + 4)
    control_nodes = {
        controls["root_ref"]: (0.0, 0.0, 0.0),
        controls["root_rot"]: (3.0, 3.0, 3.0),
        controls["patch_ref"]: (0.9, 0.0, sign * 0.05),
        controls["patch_rot"]: (4.0, 4.0, 4.0),
    }
    force, moment = LOADS[load_name]
    arm = tuple(a - b for a, b in zip(control_nodes[controls["patch_ref"]],
                                     control_nodes[controls["root_ref"]]))
    arm_moment = _cross(arm, force)
    expected_force = tuple(-v for v in force)
    expected_moment = tuple(-a - b for a, b in zip(arm_moment, moment))
    metadata = {
        "schema": "R8_E02_RIGID_TIP_REFERENCE_V1",
        "scope": "matched E02 development discriminator only; no qualification claim",
        "ccx_version": CCX_VERSION, "ccx_executable_sha256": CCX_SHA256,
        "nx": nx, "ny": ny, "nz": nz, "sign": sign, "load_name": load_name,
        "geometry_m": {"length": 1.0, "y_min": -0.1, "y_max": 0.1,
                       "z_min": -0.01, "z_max": 0.01, "patch_x_min": 0.8},
        "material": {"E_Pa": 210e9, "nu": 0.3}, "element_type": "C3D20R",
        "physical_nodes": physical, "elements": elements,
        "control_nodes": control_nodes, "controls": controls,
        "patch_nodes": patch, "root_nodes": root,
        "physical_node_count": len(physical), "element_count": len(elements),
        "applied_force_N": force, "applied_moment_Nm": moment,
        "expected_root_force_N": expected_force,
        "expected_root_moment_Nm": expected_moment,
        "expected_output_time": 1.0,
        "output_sets": {"CONTROLS": sorted(control_nodes), "PATCH": patch, "ROOT": root},
        "normal_spin_equivalence_claimed": False,
        "sector_decoupling_requires_actual_verification": True,
    }
    metadata["geometry_sha256"] = _hash(_geometry_payload(metadata))
    deck = ["*HEADING", "R8 E02 matched rigid-tip solid: development only", "*NODE"]
    deck.extend(str(node) + "," + ",".join(format(v, ".17g") for v in xyz)
                for node, xyz in (physical | control_nodes).items())
    deck.append("*ELEMENT,TYPE=C3D20R,ELSET=SOLID")
    for element, ids in elements.items():
        # CCX's first line has the element ID plus 15 nodes; continuation has 5.
        deck.append(str(element) + "," + ",".join(map(str, ids[:15])))
        deck.append(",".join(map(str, ids[15:])))
    deck.extend(_nset("ROOT", root))
    deck.extend(_nset("PATCH", patch))
    deck.extend(_nset("CONTROLS", sorted(control_nodes)))
    deck.extend([
        f'*RIGID BODY,NSET=ROOT,REF NODE={controls["root_ref"]},ROT NODE={controls["root_rot"]}',
        f'*RIGID BODY,NSET=PATCH,REF NODE={controls["patch_ref"]},ROT NODE={controls["patch_rot"]}',
        "*MATERIAL,NAME=ELASTIC", "*ELASTIC", "210000000000.,0.3",
        "*SOLID SECTION,ELSET=SOLID,MATERIAL=ELASTIC", "*BOUNDARY",
        f'{controls["root_ref"]},1,3,0.', f'{controls["root_rot"]},1,3,0.',
        "*STEP", "*STATIC", "1.,1.,0.000001,1.", "*CLOAD",
    ])
    for role, load in (("patch_ref", force), ("patch_rot", moment)):
        for i, value in enumerate(load, 1):
            if value:
                deck.append(f"{controls[role]},{i},{value:.17g}")
    deck.extend(["*NODE PRINT,NSET=CONTROLS", "U,RF", "*NODE PRINT,NSET=PATCH", "U",
                 "*NODE PRINT,NSET=ROOT", "U", "*END STEP"])
    deck_text = "\n".join(deck) + "\n"
    metadata["deck_sha256"] = hashlib.sha256(deck_text.encode("ascii")).hexdigest()
    return deck_text, metadata


_HEADER = re.compile(
    r"^\s*(displacements|forces)\s+\([^\n]*\)\s+for set\s+([A-Za-z0-9_]+)"
    r"\s+and time\s+(\S+)\s*$", re.I | re.M)
_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?$")


def _printed_number(token):
    if not _NUMBER.fullmatch(token):
        raise ReferenceParseError("invalid numeric output token: " + token[:80])
    try:
        decimal = Decimal(token.replace("D", "E").replace("d", "E"))
        value = float(decimal)
        uncertainty = float(Decimal(5).scaleb(decimal.as_tuple().exponent - 1))
    except (InvalidOperation, OverflowError, ValueError) as exc:
        raise ReferenceParseError("invalid numeric output") from exc
    if not math.isfinite(value) or not math.isfinite(uncertainty) or uncertainty <= 0:
        raise ReferenceParseError("nonfinite/unrepresentable numeric output")
    mantissa = re.split("[EeDd]", token)[0]
    digits = mantissa.lstrip("+-").replace(".", "").lstrip("0")
    return value, uncertainty, len(digits) if digits else None


def _int_map(values, name):
    normalized = {}
    for key, value in values.items():
        if isinstance(key, bool) or not re.fullmatch(r"[1-9]\d*", str(key)):
            raise ReferenceParseError("invalid ID in metadata: " + name)
        node = int(key)
        if node in normalized:
            raise ReferenceParseError("duplicate ID in metadata: " + name)
        normalized[node] = value
    return normalized


def _validate_metadata(metadata):
    try:
        _, rebuilt = build_deck(metadata["nx"], metadata["ny"], metadata["sign"], metadata["load_name"])
        # Exact metadata checking detects replaced geometry, loads and ID lists.
        # JSON normalizes tuple/list and integer/string dictionary keys.
        if _hash(metadata) != _hash(json.loads(json.dumps(rebuilt))):
            raise ReferenceParseError("metadata differs from the exact generated deck manifest")
        physical = _int_map(metadata["physical_nodes"], "physical_nodes")
        control_nodes = _int_map(metadata["control_nodes"], "control_nodes")
        elements = _int_map(metadata["elements"], "elements")
        if set(physical) & set(control_nodes):
            raise ReferenceParseError("control/physical IDs overlap")
        if any(len(ids) != 20 or len(set(ids)) != 20 or not set(ids) <= set(physical)
               for ids in elements.values()):
            raise ReferenceParseError("invalid C3D20R connectivity")
    except ReferenceParseError:
        raise
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ReferenceParseError("invalid or incomplete reference metadata") from exc
    return physical, control_nodes


def parse_result(dattext, stdout, metadata):
    """Parse one completed linear-static result; return compact development evidence.

    Reject warnings/errors, wrong CCX version/thread reporting, duplicate/missing
    output IDs, multiple frames, changed metadata, malformed/nonfinite values and
    uncompleted jobs.  No displacement, convergence, decoupling, balance or E02
    acceptance threshold is inferred or relaxed here.

    Rounding bounds assume nearest rounding to the last printed decimal place,
    and conservatively give printed zero the same half-unit bound.  They are
    evidence resolution bounds, not solver-error estimates or certification.
    """
    if not isinstance(dattext, str) or not isinstance(stdout, str):
        raise ReferenceParseError("outputs must be text")
    physical, control_nodes = _validate_metadata(metadata)
    if re.search(r"\b(?:warnings?|errors?|fatal|failed|failure|nan|infinity)\b", dattext + "\n" + stdout, re.I):
        raise ReferenceParseError("solver diagnostic or nonfinite output")
    if len(re.findall(r"^\s*Job finished\s*$", stdout, re.M)) != 1:
        raise ReferenceParseError("expected exactly one completed job")
    versions = re.findall(r"CalculiX Version\s+(\S+)", stdout)
    if versions != [CCX_VERSION + ","] and versions != [CCX_VERSION]:
        raise ReferenceParseError("unexpected or missing CalculiX version")
    cpu_lines = [line.strip() for line in stdout.splitlines() if "cpu" in line.lower()]
    if not cpu_lines or any(re.findall(r"\b(\d+)\s+cpu", line, re.I) != ["1"] for line in cpu_lines):
        raise ReferenceParseError("missing or non-single-CPU solver reporting")
    headers = list(_HEADER.finditer(dattext))
    expected = {("displacements", "CONTROLS"), ("forces", "CONTROLS"),
                ("displacements", "PATCH"), ("displacements", "ROOT")}
    parsed, bounds, precisions = {}, {}, []
    zero_count = 0
    for index, header in enumerate(headers):
        key = (header.group(1).lower(), header.group(2).upper())
        if key not in expected or key in parsed:
            raise ReferenceParseError("unexpected or duplicate output section: " + repr(key))
        time_value, _, _ = _printed_number(header.group(3))
        if time_value != metadata["expected_output_time"]:
            raise ReferenceParseError("result is not at completed expected time")
        end = headers[index + 1].start() if index + 1 < len(headers) else len(dattext)
        rows, row_bounds = {}, {}
        for line in dattext[header.end():end].splitlines():
            if not line.strip():
                continue
            fields = line.split()
            if len(fields) != 4 or not re.fullmatch(r"[1-9]\d*", fields[0]):
                raise ReferenceParseError("malformed output row in " + repr(key))
            node = int(fields[0])
            if node in rows:
                raise ReferenceParseError("duplicate output node ID: " + str(node))
            numbers = [_printed_number(token) for token in fields[1:]]
            rows[node] = tuple(item[0] for item in numbers)
            row_bounds[node] = tuple(item[1] for item in numbers)
            precisions.extend(item[2] for item in numbers if item[2] is not None)
            zero_count += sum(item[0] == 0 for item in numbers)
        required_ids = set(metadata["output_sets"][key[1]])
        if set(rows) != required_ids:
            raise ReferenceParseError("missing/unexpected IDs in " + repr(key) +
                                      f": missing={len(required_ids - set(rows))}, extra={len(set(rows) - required_ids)}")
        parsed[key], bounds[key] = rows, row_bounds
    if set(parsed) != expected:
        raise ReferenceParseError("missing required output section")
    controls = metadata["controls"]
    u = parsed[("displacements", "CONTROLS")]
    ub = bounds[("displacements", "CONTROLS")]
    rf = parsed[("forces", "CONTROLS")]
    rfb = bounds[("forces", "CONTROLS")]
    actual_force, actual_moment = rf[controls["root_ref"]], rf[controls["root_rot"]]
    expected_force, expected_moment = metadata["expected_root_force_N"], metadata["expected_root_moment_Nm"]
    force_residual = tuple(a - b for a, b in zip(actual_force, expected_force))
    moment_residual = tuple(a - b for a, b in zip(actual_moment, expected_moment))
    mapping = {}
    for name in ("patch", "root"):
        ref, rot = controls[name + "_ref"], controls[name + "_rot"]
        observed = parsed[("displacements", name.upper())]
        observed_bounds = bounds[("displacements", name.upper())]
        maximum_gap, maximum_bound, gap_node, max_excess = 0.0, 0.0, None, 0.0
        for node in metadata[name + "_nodes"]:
            arm = tuple(a - b for a, b in zip(physical[node], control_nodes[ref]))
            spin = _cross(u[rot], arm)
            predicted = tuple(a + b for a, b in zip(u[ref], spin))
            gap = tuple(abs(a - b) for a, b in zip(observed[node], predicted))
            rb = ub[rot]
            spin_bounds = (abs(arm[2]) * rb[1] + abs(arm[1]) * rb[2],
                           abs(arm[0]) * rb[2] + abs(arm[2]) * rb[0],
                           abs(arm[1]) * rb[0] + abs(arm[0]) * rb[1])
            uncertainty = tuple(a + b + c for a, b, c in zip(observed_bounds[node], ub[ref], spin_bounds))
            if max(gap) > maximum_gap or gap_node is None:
                maximum_gap, gap_node = max(gap), node
            maximum_bound = max(maximum_bound, *uncertainty)
            max_excess = max(max_excess, *(max(0.0, a - b) for a, b in zip(gap, uncertainty)))
        mapping[name] = {"node_count": len(observed), "max_abs_printed_gap_m": maximum_gap,
                         "max_gap_node_id": gap_node, "max_rounding_bound_m": maximum_bound,
                         "max_gap_beyond_printed_rounding_m": max_excess}
    force, moment = metadata["applied_force_N"], metadata["applied_moment_Nm"]
    ref, rot = controls["patch_ref"], controls["patch_rot"]
    work = sum(a * b for a, b in zip(force, u[ref])) + sum(a * b for a, b in zip(moment, u[rot]))
    work_bound = sum(abs(a) * b for a, b in zip(force, ub[ref])) + sum(abs(a) * b for a, b in zip(moment, ub[rot]))
    return {
        "status": "PARSED_DEVELOPMENT_ONLY", "qualification_claim": False,
        "load_name": metadata["load_name"], "sign": metadata["sign"],
        "mesh": {"nx": metadata["nx"], "ny": metadata["ny"], "nz": metadata["nz"],
                 "physical_nodes": metadata["physical_node_count"], "elements": metadata["element_count"]},
        "geometry_sha256": metadata["geometry_sha256"], "deck_sha256": metadata["deck_sha256"],
        "controls": controls,
        "patch_ref_displacement_m": u[ref], "patch_rot_theta_rad": u[rot],
        "patch_ref_displacement_rounding_bound_m": ub[ref], "patch_rot_theta_rounding_bound_rad": ub[rot],
        "root_ref_displacement_m": u[controls["root_ref"]], "root_rot_theta_rad": u[controls["root_rot"]],
        "actual_root_force_N": actual_force, "actual_root_moment_Nm": actual_moment,
        "expected_root_force_N": expected_force, "expected_root_moment_Nm": expected_moment,
        "root_force_residual_N": force_residual, "root_moment_residual_Nm": moment_residual,
        "root_force_rounding_bound_N": rfb[controls["root_ref"]],
        "root_moment_rounding_bound_Nm": rfb[controls["root_rot"]],
        "patch_ref_force_N": rf[ref], "patch_rot_moment_Nm": rf[rot],
        "rigid_mapping": mapping, "conjugate_external_work_J": work,
        "conjugate_external_work_rounding_bound_J": work_bound,
        "printed_rounding": {
            "assumption": "nearest rounding; half last printed decimal unit; zero bound conservative",
            "nonzero_significant_digits_min": min(precisions) if precisions else None,
            "nonzero_significant_digits_max": max(precisions) if precisions else None,
            "printed_zero_component_count": zero_count,
            "can_certify_relative_balance_1e_minus_8": False,
            "reason": "CCX .dat seven-significant-digit evidence cannot certify 1e-8 balance",
        },
        "cpu_reporting_lines": cpu_lines,
        "normal_spin_equivalence_claimed": False,
        "sector_decoupling_requires_actual_verification": True,
        "supervisor_checks_required": ["pinned executable SHA256", "exit code and stderr", "resource limits", "completed .sta step"],
    }


def self_check():
    """Bounded deck/parser checks with constructed text; no scientific run."""
    counts = []
    for nx, ny in LEVELS:
        for sign in (-1, 1):
            for load_name in LOADS:
                deck, metadata = build_deck(nx, ny, sign, load_name)
                physical = metadata["physical_nodes"]
                ids = set(physical)
                expected_nodes = ((nx + 1) * (ny + 1) * 3 + nx * (ny + 1) * 3
                                  + (nx + 1) * ny * 3 + (nx + 1) * (ny + 1) * 2)
                assert len(physical) == expected_nodes and len(metadata["elements"]) == nx * ny * 2
                assert len(set(physical.values())) == len(physical)
                assert set(metadata["patch_nodes"]) == {node for node, xyz in physical.items() if xyz[0] >= 0.8}
                assert set(metadata["root_nodes"]) == {node for node, xyz in physical.items() if xyz[0] == 0.0}
                assert set(metadata["patch_nodes"]).isdisjoint(metadata["root_nodes"])
                assert min(metadata["control_nodes"]) > max(ids)
                assert set().union(*(set(conn) for conn in metadata["elements"].values())) == ids
                assert all(len(conn) == len(set(conn)) == 20 for conn in metadata["elements"].values())
                # Every corner/edge position has the required standard ordering.
                for conn in metadata["elements"].values():
                    corners = [physical[node] for node in conn[:8]]
                    a, b, c, d = corners[0], corners[1], corners[3], corners[4]
                    assert b[0] > a[0] and c[1] > a[1] and d[2] > a[2]
                    for offset, (left, right) in enumerate(_EDGES, 8):
                        midpoint = physical[conn[offset]]
                        assert all(math.isclose(v, (x + y) / 2, rel_tol=0, abs_tol=2e-16)
                                   for v, x, y in zip(midpoint, corners[left], corners[right]))
                assert all(len(line.split(",")) <= 16 for line in deck.splitlines() if line and line[0].isdigit())
                _validate_metadata(json.loads(json.dumps(metadata)))
        counts.append({"nx": nx, "ny": ny, "nodes": len(physical), "elements": len(metadata["elements"]),
                       "patch_nodes": len(metadata["patch_nodes"]), "root_nodes": len(metadata["root_nodes"])})
    _, metadata = build_deck(10, 4, 1, "Fz")
    controls = metadata["controls"]
    # Deliberately arbitrary poses test coordinate mapping, not material response.
    u = {node: (0.0, 0.0, 0.0) for node in metadata["control_nodes"]}
    u[controls["patch_ref"]] = (1e-7, -2e-7, 3e-7)
    u[controls["patch_rot"]] = (2e-6, -3e-6, 4e-6)
    rf = {node: (0.0, 0.0, 0.0) for node in u}
    rf[controls["root_ref"]] = metadata["expected_root_force_N"]
    rf[controls["root_rot"]] = metadata["expected_root_moment_Nm"]
    rf[controls["patch_ref"]] = metadata["applied_force_N"]
    rf[controls["patch_rot"]] = metadata["applied_moment_Nm"]
    sections = []
    for label, name in (("displacements", "CONTROLS"), ("forces", "CONTROLS"),
                        ("displacements", "PATCH"), ("displacements", "ROOT")):
        sections.append(f" {label} (x,y,z) for set {name} and time 0.1000000E+01\n")
        for node in metadata["output_sets"][name]:
            if name == "CONTROLS":
                values = (u if label == "displacements" else rf)[node]
            else:
                ref, rot = controls[name.lower() + "_ref"], controls[name.lower() + "_rot"]
                arm = tuple(a - b for a, b in zip(metadata["physical_nodes"][node], metadata["control_nodes"][ref]))
                values = tuple(a + b for a, b in zip(u[ref], _cross(u[rot], arm)))
            sections.append(str(node) + " " + " ".join(f"{v:.6E}" for v in values) + "\n")
        sections.append("\n")
    dat = "".join(sections)
    stdout = "CalculiX Version 2.23, Copyright(C)\n Using up to 1 cpu(s) for stress.\n Job finished\n"
    result = parse_result(dat, stdout, json.loads(json.dumps(metadata)))
    assert result["patch_ref_displacement_m"] == u[controls["patch_ref"]]
    assert result["patch_rot_theta_rad"] == u[controls["patch_rot"]]
    assert result["rigid_mapping"]["patch"]["max_gap_beyond_printed_rounding_m"] < 1e-18
    assert tuple(result["expected_root_moment_Nm"]) == (0.0, 9.0, 0.0)
    assert parse_result(dat, stdout, metadata)["status"] == "PARSED_DEVELOPMENT_ONLY"
    assert not result["printed_rounding"]["can_certify_relative_balance_1e_minus_8"]
    rejection_count = 0
    def reject(bad_dat=dat, bad_stdout=stdout, bad_metadata=metadata):
        nonlocal rejection_count
        try:
            parse_result(bad_dat, bad_stdout, bad_metadata)
        except ReferenceParseError:
            rejection_count += 1
        else:
            raise AssertionError("malformed output was accepted")
    reject(bad_stdout=stdout + "WARNING: test\n")
    reject(bad_stdout=stdout.replace("Job finished", "interrupted"))
    reject(bad_stdout=stdout.replace("1 cpu", "2 cpu"))
    reject(bad_stdout=stdout.replace("1 cpu", "2 cpu followed by 1 cpu"))
    reject(bad_stdout=stdout.replace("2.23", "2.22"))
    reject(bad_dat=dat + dat)
    reject(bad_dat=dat[:dat.index(" displacements (x,y,z) for set ROOT")])
    first_row = next(line for line in dat.splitlines() if line and line[0].isdigit())
    reject(bad_dat=dat.replace(first_row + "\n", first_row + "\n" + first_row + "\n", 1))
    reject(bad_dat=dat.replace("0.1000000E+01", "0.5000000E+00", 1))
    reject(bad_dat=dat.replace(first_row, first_row.rsplit(" ", 1)[0] + " NaN", 1))
    changed = json.loads(json.dumps(metadata))
    changed["patch_nodes"] = changed["patch_nodes"][:-1]
    reject(bad_metadata=changed)
    return {"status": "SELF_CHECK_PASSED_NO_SOLVER_RUN", "deck_cases": 18,
            "mesh_counts": counts, "parser_rejections": rejection_count}


if __name__ == "__main__":
    print(json.dumps(self_check(), sort_keys=True))
