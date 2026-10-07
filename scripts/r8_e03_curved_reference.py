"""Unexecuted, profile-specific E03 solid/fitted-port reference candidate.

No process is launched here. B2 fitted-port work and continuum accuracy are
separate questions. GE's independent shell rotation/drill reference is missing.
"""
from __future__ import annotations

import hashlib
import json
import math
import re

import numpy as np

from scripts.r8_e02_double_output import read_double_output
from scripts.r8_e02_rigid_tip_reference import CCX_VERSION, CCX_SHA256, ReferenceParseError


CASE_SCHEMA = "E03_POLYGONAL_ROOF_FITTED_PORT_CANDIDATE_V1"
LEVELS = ((4, 6, 1), (8, 10, 2), (16, 18, 3))
B2 = "B2_E4_PL_FAST_LINEAR_V1"
GE = "B3_GE_E4_PL_STIFFENED_SHELL_V1"
FLOORS = dict(displacement_m=1e-12, external_work_j=1e-12,
              force_n=1e-9, moment_nm=1e-10)
LINEAR_LIMIT = .01
BALANCE_LIMIT = 1e-8


def digest(value):
    value = json.loads(json.dumps(value, allow_nan=False))
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode("ascii")).hexdigest()


def balance_measure(case, force, moment):
    fref = len(case["ribs"])*float(np.linalg.norm(case["tip_force_each_n"]))
    lref = case["length_m"]
    if fref <= 0 or lref <= 0:
        raise ReferenceParseError("positive declared physical force and length scales required")
    return float(max(np.max(np.abs(force))/fref, np.max(np.abs(moment))/(fref*lref)))


def ccx_number(value):
    """Highest available significant precision within CCX's 20-character field."""
    number = float(value)
    if not math.isfinite(number):
        raise ReferenceParseError("finite CCX numeric field required")
    for digits in range(17, 11, -1):
        token = format(number, "."+str(digits)+"g")
        if len(token) <= 20:
            return token
    raise ReferenceParseError("CCX field cannot preserve the bounded numeric representation")


def _detached_receipt(receipt):
    """Retain only bounded finite JSON receipt data, with no nested aliases."""
    active, count = set(), [0]

    def validate(value, depth):
        count[0] += 1
        if count[0] > 4096 or depth > 16:
            raise ReferenceParseError("bounded receipt node count and depth required")
        if value is None or type(value) is bool:
            return
        if type(value) is str:
            if len(value) > 4096:
                raise ReferenceParseError("bounded receipt strings required")
            return
        if type(value) is int:
            if abs(value) > 10**20:
                raise ReferenceParseError("bounded receipt integers required")
            return
        if type(value) is float:
            if not math.isfinite(value):
                raise ReferenceParseError("finite receipt numbers required")
            return
        if type(value) not in (dict, list):
            raise ReferenceParseError("receipt values must be JSON primitives")
        identity = id(value)
        if identity in active:
            raise ReferenceParseError("cyclic receipt refused")
        active.add(identity)
        try:
            if type(value) is dict:
                for key, item in value.items():
                    if type(key) is not str or len(key) > 256:
                        raise ReferenceParseError("bounded string receipt keys required")
                    validate(item, depth+1)
            else:
                for item in value:
                    validate(item, depth+1)
        finally:
            active.remove(identity)

    if type(receipt) is not dict:
        raise ReferenceParseError("JSON object process receipt required")
    validate(receipt, 0)
    encoded = json.dumps(receipt, allow_nan=False, separators=(",", ":"))
    if len(encoded.encode("ascii")) > 65536:
        raise ReferenceParseError("bounded receipt serialization required")
    return json.loads(encoded)


def skew(vector):
    x, y, z = vector
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def translation_pose_fit(points):
    """Independent equal-weight left inverse; leaves non-rigid local modes free."""
    points = np.asarray(points, dtype=float)
    if points.shape != (4, 3) or not np.isfinite(points).all():
        raise ReferenceParseError("four finite physical port vertices required")
    origin = points.mean(axis=0)
    h = np.concatenate([np.column_stack((np.eye(3), -skew(p-origin)))
                        for p in points], axis=0)
    if np.linalg.matrix_rank(h) != 6:
        raise ReferenceParseError("noncollinear six-role fitted port required")
    return origin, np.linalg.solve(h.T @ h, h.T), h


def transport(offset):
    made = np.eye(6)
    made[:3, 3:] = -skew(offset)
    return made


def fitted_connection(shell_points, beam_points):
    """c=q_b-E(r)q_s, lambda=(force,moment) at the beam centroid."""
    xs, ps, _ = translation_pose_fit(shell_points)
    xb, pb, _ = translation_pose_fit(beam_points)
    e = transport(xb-xs)
    return dict(shell_origin=xs, beam_origin=xb, shell_fit=ps, beam_fit=pb,
                transport=e, constraint=np.column_stack((-e @ ps, pb)))


def connection_actions(connection, multiplier):
    lam = np.asarray(multiplier, dtype=float)
    if lam.shape != (6,) or not np.isfinite(lam).all():
        raise ReferenceParseError("finite world force/moment multiplier required")
    c = connection["constraint"]
    return (c[:, :12].T @ lam).reshape(4, 3), (c[:, 12:].T @ lam).reshape(4, 3)


def build_case(level=0, offset_sign=1):
    if type(level) is not int or level not in range(3) or type(offset_sign) is not int or offset_sign not in (-1, 1):
        raise ValueError("one of three frozen levels and an explicit eccentric sign required")
    nx, ny, through = LEVELS[level]
    length, radius, angle = .508, 2.540, .1
    thickness, width, height, young, poisson = .0127, .00635, .0254, 3.10275e9, .3
    theta = [-angle+2*angle*j/ny for j in range(ny+1)]
    boundaries = [(radius*math.sin(t), radius*(math.cos(t)-math.cos(angle))) for t in theta]

    def surface(i, j, refinement):
        x = -length/2+length*i/(refinement*nx)
        cell = min(j//refinement, ny-1)
        fraction = j/refinement-cell
        a, b = boundaries[cell], boundaries[cell+1]
        return [x, a[0]+fraction*(b[0]-a[0]), a[1]+fraction*(b[1]-a[1])]

    grids = {}
    for name, factor in (("b2", 1), ("ge", 2)):
        width_nodes = factor*ny+1
        nodes = [surface(i, j, factor) for i in range(factor*nx+1)
                 for j in range(factor*ny+1)]
        quads = [[i*width_nodes+j+1, (i+1)*width_nodes+j+1,
                  (i+1)*width_nodes+j+2, i*width_nodes+j+2]
                 for i in range(factor*nx) for j in range(factor*ny)]
        grids[name] = dict(nodes=nodes, quads=quads,
                          root_nodes=list(range(1, width_nodes+1)))
    ribs = []
    for rib, j in enumerate(((ny-2)//4, (3*ny-2)//4)):
        t = (theta[j]+theta[j+1])/2
        normal = [0., math.sin(t), math.cos(t)]
        tangent = [0., math.cos(t), -math.sin(t)]
        base = surface(0, 2*j+1, 2)
        offset = offset_sign*(thickness+height)/2
        center = [base[k]+offset*normal[k] for k in range(3)]
        frame = [[1., 0., 0.], [0., tangent[1], normal[1]],
                 [0., tangent[2], normal[2]]]
        ribs.append(dict(strip=j, normal=normal, tangent=tangent,
                         root_center=center, offset_m=offset, frame=frame,
                         ge_ids=list(range(100001+rib*(2*nx+1), 100001+(rib+1)*(2*nx+1))),
                         b2_ids=list(range(200001+rib*(nx+1), 200001+(rib+1)*(nx+1)))))
    odd = range(1, 512, 2)
    torsion = height*width**3/3*(1-192*width/(math.pi**5*height)*
        sum(math.tanh(k*math.pi*height/(2*width))/k**5 for k in odd))
    case = dict(schema=CASE_SCHEMA, level=level, offset_sign=offset_sign,
        nx=nx, ny=ny, through=through, length_m=length, radius_m=radius,
        half_angle_rad=angle, thickness_m=thickness, young_pa=young, poisson=poisson,
        section=dict(width_m=width, height_m=height, area_m2=width*height,
                     Iy_m4=width*height**3/12, Iz_m4=height*width**3/12,
                     J_m4=torsion, shear_y=5/6, shear_z=5/6,
                     torsion_definition="rectangular Saint-Venant odd series through 511"),
        grids=grids, ribs=ribs, tip_force_each_n=[0., 0., -.5],
        supports="all translations/rotations at native root; all solid root translations",
        profile_laws={B2: "equal-vertex translation-fitted shell pose and physical B2 station pose",
                      GE: "subdivided-facet shell nodal translation/independent rotation and native B3 nodal pose"},
        ge_reference="REFUSED_UNRESOLVED_INDEPENDENT_SHELL_ROTATION_DRILL_MAP",
        production_qualified=False)
    case["case_id"] = digest(case)
    return case


def validate_case(case):
    if type(case) is not dict or case != build_case(case.get("level"), case.get("offset_sign")):
        raise ReferenceParseError("immutable declared E03 case identity required")


_CORNERS = ((0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0),
            (0, 0, 2), (2, 0, 2), (2, 2, 2), (0, 2, 2))
_EDGES = ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6),
          (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7))
_OFFSETS = _CORNERS+tuple(tuple((a+b)//2 for a, b in zip(_CORNERS[i], _CORNERS[j]))
                          for i, j in _EDGES)


def _equation_rows(constraint, beam_ids, shell_ids):
    # Put independent beam-section columns first: each station owns its pivot DOFs.
    a = np.column_stack((constraint[:, 12:], constraint[:, :12])).copy()
    roles = [(node, component) for node in (*beam_ids, *shell_ids)
             for component in (1, 2, 3)]
    pivots = []
    for row in range(6):
        candidates = [column for column in range(12) if column not in pivots]
        column = max(candidates, key=lambda col: abs(a[row, col]))
        if abs(a[row, column]) <= 1e-12*np.max(abs(a[row])):
            raise ReferenceParseError("independent beam-section equation pivot required")
        a[row] /= a[row, column]
        for other in range(6):
            if other != row:
                a[other] -= a[other, column]*a[row]
                a[other, column] = 0.
        a[row, column] = 1.
        pivots.append(column)
    rows = []
    for row, pivot in zip(a, pivots):
        columns = [pivot]+[j for j in range(24) if j != pivot and row[j] != 0.]
        rows.append([(roles[j][0], roles[j][1], float(row[j])) for j in columns])
    return rows


def build_deck(case):
    """Independent solid continuum plus six fitted-pose equations; no rigid knots."""
    validate_case(case)
    nx, ny, nt = case["nx"], case["ny"], case["through"]
    nodes, elements, lookup = {}, {}, {}
    root, ports, loads, tips = [], [], {}, []
    length, radius, alpha, thick = (case[k] for k in
        ("length_m", "radius_m", "half_angle_rad", "thickness_m"))

    def mesh(domain, counts, coordinate):
        for i in range(counts[0]):
            for j in range(counts[1]):
                for k in range(counts[2]):
                    ids = []
                    for a, b, c in _OFFSETS:
                        key = (domain, 2*i+a, 2*j+b, 2*k+c)
                        if key not in lookup:
                            node = len(nodes)+1
                            lookup[key] = node
                            nodes[node] = tuple(float(v) for v in coordinate(key[1:]))
                            if key[1] == 0:
                                root.append(node)
                        ids.append(lookup[key])
                    elements[len(elements)+1] = tuple(ids)

    def shell_coordinate(indices):
        i, j, k = indices
        cell = min(j//2, ny-1)
        fraction = j/2-cell
        t0, t1 = -alpha+2*alpha*cell/ny, -alpha+2*alpha*(cell+1)/ny
        w = -thick/2+thick*k/(2*nt)
        y = (radius+w)*((1-fraction)*math.sin(t0)+fraction*math.sin(t1))
        z = (radius+w)*((1-fraction)*math.cos(t0)+fraction*math.cos(t1))-radius*math.cos(alpha)
        return (-length/2+length*i/(2*nx), y, z)

    mesh("shell", (nx, ny, nt), shell_coordinate)
    for rib_index, rib in enumerate(case["ribs"]):
        domain = "rib"+str(rib_index)
        b, h = case["section"]["width_m"], case["section"]["height_m"]

        def rib_coordinate(indices):
            i, j, k = indices
            y, z = -b/2+b*j/(2*nt), -h/2+h*k/(2*nt)
            return [rib["root_center"][axis]+(length*i/(2*nx) if axis == 0 else 0.)+
                    y*rib["tangent"][axis]+z*rib["normal"][axis] for axis in range(3)]

        mesh(domain, (nx, nt, nt), rib_coordinate)
        for i in range(nx):
            j = rib["strip"]
            shell_ids = [lookup[("shell", x, y, nt)] for x, y in
                         ((2*i, 2*j), (2*i+2, 2*j), (2*i+2, 2*j+2), (2*i, 2*j+2))]
            beam_ids = [lookup[(domain, 2*i+1, y, z)] for y, z in
                        ((0, 0), (2*nt, 0), (2*nt, 2*nt), (0, 2*nt))]
            ports.append(dict(point_id=f"rib{rib_index}-point{i}", shell_nodes=shell_ids,
                              beam_nodes=beam_ids))
        tip = [lookup[(domain, 2*nx, y, z)] for y, z in
               ((0, 0), (2*nt, 0), (2*nt, 2*nt), (0, 2*nt))]
        _, fit, _ = translation_pose_fit([nodes[n] for n in tip])
        forces = (fit.T @ np.array((*case["tip_force_each_n"], 0., 0., 0.))).reshape(4, 3)
        for node, force in zip(tip, forces):
            loads[node] = tuple(float(v) for v in force)
        tips.append(dict(rib_index=rib_index, nodes=tip))
    source_nodes = nodes
    nodes = {n: tuple(float(ccx_number(v)) for v in p) for n, p in source_nodes.items()}
    # Rebuild loads and equations from actual rounded geometry, retaining source
    # coordinates and pre-output row coefficients in the evidence metadata.
    loads = {}
    for tip in tips:
        _, fit, _ = translation_pose_fit([nodes[n] for n in tip["nodes"]])
        forces = (fit.T @ np.array((*case["tip_force_each_n"], 0., 0., 0.))).reshape(4, 3)
        for node, force in zip(tip["nodes"], forces):
            loads[node] = tuple(float(ccx_number(v)) for v in force)
    equations = []
    for port in ports:
        connection = fitted_connection([nodes[n] for n in port["shell_nodes"]],
                                       [nodes[n] for n in port["beam_nodes"]])
        equations.extend(_equation_rows(connection["constraint"], port["beam_nodes"], port["shell_nodes"]))
    lines = ["*HEADING", "E03 unqualified B2 fitted-port solid candidate", "*NODE"]
    lines += [str(n)+","+",".join(ccx_number(v) for v in p) for n, p in nodes.items()]
    lines += ["*ELEMENT,TYPE=C3D20R,ELSET=SOLID"]
    for element, ids in elements.items():
        lines += [str(element)+","+",".join(map(str, ids[:15])), ",".join(map(str, ids[15:]))]
    lines += ["*NSET,NSET=ROOT"]
    lines += [",".join(map(str, root[i:i+16])) for i in range(0, len(root), 16)]
    lines += ["*NSET,NSET=PHYSICAL"]
    all_ids = list(nodes)
    lines += [",".join(map(str, all_ids[i:i+16])) for i in range(0, len(all_ids), 16)]
    for row in equations:
        lines += ["*EQUATION", str(len(row))]
        for i in range(0, len(row), 4):
            lines.append(",".join(f"{n},{d},{ccx_number(v)}" for n, d, v in row[i:i+4]))
    lines += ["*MATERIAL,NAME=ELASTIC", "*ELASTIC", ccx_number(case["young_pa"])+","+ccx_number(case["poisson"]),
              "*SOLID SECTION,ELSET=SOLID,MATERIAL=ELASTIC", "*BOUNDARY", "ROOT,1,3,0.",
              "*STEP", "*STATIC", "1.,1.,1.,1.", "*CLOAD"]
    lines += [f"{n},{d},{ccx_number(v)}" for n, force in loads.items()
              for d, v in enumerate(force, 1) if v != 0.]
    lines += ["*NODE OUTPUT,DOUBLE,NSET=PHYSICAL", "U",
              "*NODE OUTPUT,DOUBLE,NSET=ROOT", "RF", "*END STEP"]
    text = "\n".join(lines)+"\n"
    metadata = dict(case_id=case["case_id"], level=case["level"], offset_sign=case["offset_sign"],
        profile=B2, status="UNEXECUTED_B2_FITTED_PORT_CANDIDATE", physical_nodes=nodes,
        source_nodes=source_nodes, source_equations=equations,
        deck_equations=[[(n, d, float(ccx_number(v))) for n, d, v in row] for row in equations],
        maximum_coordinate_rounding_m=max(abs(nodes[n][axis]-p[axis])
            for n, p in source_nodes.items() for axis in range(3)),
        elements=elements, root_nodes=root, ports=ports, tips=tips, nodal_loads=loads,
        deck_sha256=hashlib.sha256(text.encode("ascii")).hexdigest(),
        output_contract="prior pinned CCX2.23 DOUBLE U(all)/RF(root) syntax; E03 deck unexecuted",
        production_qualified=False)
    metadata["metadata_id"] = digest(metadata)
    return text, metadata


def parse_result(case, metadata, frd, sta, stdout, stderr, receipt):
    """Require exact input/output provenance and one complete step before quantities."""
    validate_case(case)
    _, expected = build_deck(case)
    if digest(metadata) != digest(expected) or type(receipt) is not dict:
        raise ReferenceParseError("exact declared metadata and process receipt required")
    metadata = expected  # Rehydrate integer IDs after a saved JSON round-trip.
    receipt = _detached_receipt(receipt)
    if type(receipt.get("exit_code")) is not int or receipt["exit_code"] != 0 or receipt.get("timed_out") is not False:
        raise ReferenceParseError("completed process required")
    if receipt.get("executable_sha256") != CCX_SHA256 or receipt.get("version") != CCX_VERSION:
        raise ReferenceParseError("pinned external executable identity required")
    for field, data in (("frd", frd), ("sta", sta), ("stdout", stdout), ("stderr", stderr)):
        if type(data) is not bytes or receipt.get(field+"_sha256") != hashlib.sha256(data).hexdigest():
            raise ReferenceParseError("exact output bytes and hashes required")
    if len(sta) > 65536 or len(stdout)+len(stderr) > 8*1024*1024:
        raise ReferenceParseError("bounded step inventory and diagnostics required")
    if receipt.get("case_id") != case["case_id"] or receipt.get("deck_sha256") != metadata["deck_sha256"]:
        raise ReferenceParseError("execution input identity mismatch")
    wall = receipt.get("process_wall_seconds")
    if type(wall) not in (int, float) or not math.isfinite(wall) or wall < 0 or not receipt.get("execution_scope"):
        raise ReferenceParseError("actual process-wall accounting and fresh execution scope required")
    if re.search(rb"\*ERROR|\*WARNING|not converg|divergen|incomplete", stdout+stderr, re.I):
        raise ReferenceParseError("diagnosed external output refused")
    try:
        rows = [line.split() for line in sta.decode("ascii").splitlines()
                if re.match(r"^\s*\d", line)]
        if len(rows) != 1 or len(rows[0]) != 7 or rows[0][:3] != ["1", "1", "1"] or any(float(v) != 1. for v in rows[0][4:]):
            raise ValueError("one completed unit-time static increment required")
    except (UnicodeDecodeError, ValueError) as error:
        raise ReferenceParseError("complete unambiguous STA inventory required") from error
    displacement, reaction = read_double_output(frd, metadata)
    gaps = []
    for port in metadata["ports"]:
        shell_ids, beam_ids = port["shell_nodes"], port["beam_nodes"]
        connection = fitted_connection([metadata["physical_nodes"][n] for n in shell_ids],
                                       [metadata["physical_nodes"][n] for n in beam_ids])
        u = np.array([displacement[n] for n in (*shell_ids, *beam_ids)]).ravel()
        gap = connection["constraint"] @ u
        if np.max(abs(gap[:3])) > 1e-10*case["length_m"] or np.max(abs(gap[3:])) > 1e-10:
            raise ReferenceParseError("actual fitted-port compatibility failed")
        gaps.append(dict(point_id=port["point_id"], world_gap=gap.tolist()))
    applied = np.sum(list(metadata["nodal_loads"].values()), axis=0)
    rf = np.sum(list(reaction.values()), axis=0)
    moment = np.zeros(3)
    root_moment = np.zeros(3)
    for n, force in reaction.items():
        root_moment += np.cross(metadata["physical_nodes"][n], force)
    for forces in (metadata["nodal_loads"], reaction):
        for n, force in forces.items():
            moment += np.cross(metadata["physical_nodes"][n], force)
    scaled_balance = balance_measure(case, rf+applied, moment)
    if scaled_balance > BALANCE_LIMIT:
        raise ReferenceParseError("physical common-origin force/moment balance failed")
    work = sum(float(np.dot(force, displacement[n])) for n, force in metadata["nodal_loads"].items())
    if not math.isfinite(work) or work <= 0.:
        raise ReferenceParseError("positive finite applied-force work required")
    tip_poses = []
    for tip in metadata["tips"]:
        _, fit, _ = translation_pose_fit([metadata["physical_nodes"][n] for n in tip["nodes"]])
        pose = fit @ np.array([displacement[n] for n in tip["nodes"]]).ravel()
        tip_poses.append(dict(rib_index=tip["rib_index"], world_pose=pose.tolist()))
    return dict(status="PARSED_UNQUALIFIED_B2_CANDIDATE", profile=B2, case_id=case["case_id"],
        level=case["level"], offset_sign=case["offset_sign"], external_work_j=work,
        force_balance_n=(rf+applied).tolist(), moment_balance_nm=moment.tolist(),
        scaled_balance=scaled_balance,
        point_gaps=gaps, tip_poses=tip_poses,
        root_reaction_wrench_world_origin=np.r_[rf, root_moment].tolist(),
        receipt=receipt, production_qualified=False)


def comparison_candidate(native, external, *, mapping_review_id):
    if native.get("profile") == GE or external.get("profile") == GE:
        raise ReferenceParseError("GE independent shell rotation/drill reference remains unresolved")
    if not isinstance(mapping_review_id, str) or not mapping_review_id.strip():
        raise ReferenceParseError("root-adopted B2 mapping review identity required")
    if native.get("profile") != B2 or external.get("profile") != B2 or native.get("case_id") != external.get("case_id"):
        raise ReferenceParseError("same profile and exact case identity required")
    if native.get("status") != "COMPLETED_UNQUALIFIED_B2_CANDIDATE" or external.get("status") != "PARSED_UNQUALIFIED_B2_CANDIDATE":
        raise ReferenceParseError("completed parsed routes required")
    a, b = native["external_work_j"], external["external_work_j"]
    if not all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in (a, b)):
        raise ReferenceParseError("finite positive work quantities required")
    difference = abs(a-b)
    try:
        def declared_tips(record):
            tips = record["tip_poses"]
            if type(tips) is not list or len(tips) != 2:
                raise ValueError("exactly two declared rib tip identities required")
            by_id = {}
            for tip in tips:
                if type(tip) is not dict or type(tip.get("rib_index")) is not int:
                    raise ValueError("explicit integer rib identity required")
                rib = tip["rib_index"]
                if rib not in (0, 1) or rib in by_id:
                    raise ValueError("distinct declared rib identities 0 and 1 required")
                by_id[rib] = tip["world_pose"]
            if set(by_id) != {0, 1}:
                raise ValueError("both declared rib identities required")
            return np.array([by_id[rib] for rib in (0, 1)], dtype=float)

        native_tips = declared_tips(native)
        external_tips = declared_tips(external)
        if native_tips.shape != (2, 6) or external_tips.shape != (2, 6):
            raise ValueError("two declared tip sections required")
        nr = np.asarray(native["root_reaction_wrench_world_origin"], dtype=float)
        er = np.asarray(external["root_reaction_wrench_world_origin"], dtype=float)
        if nr.shape != (6,) or er.shape != (6,) or not all(np.isfinite(v).all() for v in (native_tips, external_tips, nr, er)):
            raise ValueError("finite physical observations required")
    except (KeyError, TypeError, ValueError) as error:
        raise ReferenceParseError("complete tip displacement and physical root wrench required") from error
    displacement_difference = np.abs(native_tips[:, :3]-external_tips[:, :3])
    displacement_scale = np.maximum(np.abs(native_tips[:, :3]), np.abs(external_tips[:, :3]))
    wrench_difference = np.abs(nr-er)
    wrench_limit = np.maximum(np.array([FLOORS["force_n"]]*3+[FLOORS["moment_nm"]]*3),
                              LINEAR_LIMIT*np.maximum(np.abs(nr), np.abs(er)))
    return dict(status="B2_WORK_COMPARISON_CANDIDATE_ONLY", case_id=native["case_id"],
        level=native["level"], offset_sign=native["offset_sign"], mapping_review_id=mapping_review_id,
        relative_work_difference=difference/max(abs(a), abs(b), FLOORS["external_work_j"]),
        tip_translation_difference_m=displacement_difference.tolist(),
        root_wrench_difference=wrench_difference.tolist(),
        within_prepared_displacement_limit=bool(np.all(displacement_difference <=
            np.maximum(FLOORS["displacement_m"], LINEAR_LIMIT*displacement_scale))),
        within_prepared_wrench_limit=bool(np.all(wrench_difference <= wrench_limit)),
        within_prepared_one_percent_limit=difference <= max(FLOORS["external_work_j"], LINEAR_LIMIT*max(abs(a), abs(b))),
        convergence="requires all three declared levels; unassessed", production_qualified=False,
        full_e03_verdict="REFUSED_GE_ROTATION_DRILL_AND_PHYSICAL_ACCEPTANCE_OPEN")


def convergence_candidate(native_levels, external_levels, *, mapping_review_id):
    """Prepared three-level work question; never promote it to E03 acceptance."""
    if len(native_levels) != 3 or len(external_levels) != 3:
        raise ReferenceParseError("all three ordered declared levels required")
    sign = native_levels[0].get("offset_sign")
    comparisons = []
    for level, (native, external) in enumerate(zip(native_levels, external_levels)):
        expected = build_case(level, sign)
        if any(record.get("level") != level or record.get("offset_sign") != sign or
               record.get("case_id") != expected["case_id"] for record in (native, external)):
            raise ReferenceParseError("same eccentric sign and ordered exact level identities required")
        comparisons.append(comparison_candidate(native, external, mapping_review_id=mapping_review_id))
    movements = {}
    for name, records in (("native", native_levels), ("external", external_levels)):
        a, b = records[1]["external_work_j"], records[2]["external_work_j"]
        movements[name] = abs(a-b)/max(abs(a), abs(b), FLOORS["external_work_j"])
    return dict(status="UNQUALIFIED_THREE_LEVEL_WORK_CANDIDATE", comparisons=comparisons,
        last_pair_relative_movement=movements,
        within_prepared_limits=(comparisons[-1]["within_prepared_one_percent_limit"] and
                                comparisons[-1]["within_prepared_displacement_limit"] and
                                comparisons[-1]["within_prepared_wrench_limit"] and
                                all(value <= LINEAR_LIMIT for value in movements.values())),
        production_qualified=False, ge_reference="REFUSED_UNRESOLVED_ROTATION_DRILL_MAP")
