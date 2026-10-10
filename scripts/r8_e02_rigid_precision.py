"""E02 development-only rigid observability; never launches a solver.

The fixed-root-elimination variant changes the algebraic representation, not
the physical displacement space: the old grounded root rigid map is identically
zero. Its physical-node RF is a reaction only because there are direct global
SPCs, no root MPC, and no load on root nodes/elements. Detached control DOFs
remain print-only. ELSE is independently integrated internal energy, printed
with e13.6 precision; it is not a binary energy or a 1e-8 work certificate.
"""
from __future__ import annotations

import hashlib
import math
import re

import numpy as np

from scripts.r8_e02_double_output import read_double_output
from scripts.r8_e02_rigid_tip_reference import (
    ReferenceParseError, _HEADER, _cross, _hash, _nset, _printed_number,
    build_deck, parse_result,
)

ORIGINAL = "original-rigid-root"
ELIMINATED = "static-fixed-root-elimination"
_ENERGY = re.compile(
    r"^[ \t]{0,16}internal energy \(element, energy\) for set SOLID and time"
    r"[ \t]{1,8}(\S+)[ \t]{0,16}$", re.M)


def build_precision_deck(nx, ny, sign, load_name, *, nz=2, variant=ELIMINATED):
    """Preserve the old deck generator; return a separately bound new candidate."""
    if variant not in (ORIGINAL, ELIMINATED):
        raise ValueError("only the original or static fixed-zero-root variant is supported")
    original, base = build_deck(nx, ny, sign, load_name, nz=nz)
    controls = base["controls"]
    deck = original
    if variant == ELIMINATED:
        card = (f'*RIGID BODY,NSET=ROOT,REF NODE={controls["root_ref"]},'
                f'ROT NODE={controls["root_rot"]}\n')
        deck = deck.replace(card, "", 1)
        # Keep detached root control nodes fixed solely for paired DAT output.
        # Add direct global physical SPCs covering every original root node.
        deck = deck.replace("*STEP\n", "ROOT,1,3,0.\n*STEP\n", 1)
    deck = deck.replace("*STEP\n", "\n".join(_nset("ALL", sorted(base["physical_nodes"]))) + "\n*STEP\n", 1)
    deck = deck.replace("*END STEP\n", "*NODE OUTPUT,DOUBLE,NSET=ALL\nU\n"
                        "*NODE OUTPUT,DOUBLE,NSET=ROOT\nRF\n"
                        "*EL PRINT,ELSET=SOLID\nELSE\n*END STEP\n", 1)
    manifest = {"schema": "R8_E02_RIGID_PRECISION_DEV_V1", "variant": variant,
                "base": base, "deck_sha256": hashlib.sha256(deck.encode("ascii")).hexdigest(),
                "scope": "development only; no convergence or qualification",
                "binary_selector": "NODE OUTPUT,DOUBLE; ALL U then ROOT RF",
                "energy_source": "CCX 2.23 printoutelem.f weight*xsj*ener(1,jj,nelem), e13.6"}
    return deck, manifest


def _validate_candidate(deck, manifest):
    try:
        base = manifest["base"]
        rebuilt, expected = build_precision_deck(base["nx"], base["ny"], base["sign"],
            base["load_name"], nz=base["nz"], variant=manifest["variant"])
        if deck != rebuilt or _hash(expected) != _hash(manifest):
            raise ReferenceParseError("exact load/geometry/variant/deck candidate identity differs")
    except (KeyError, TypeError, ValueError) as exc:
        raise ReferenceParseError("incomplete or unsupported candidate") from exc
    return base


def root_elimination_proof(base):
    """Exact node coverage and grounded rigid-map row-space argument.

    At zero reference translation and rotation, every physical root row has
    u_i=0. Conversely direct u_i=0 admits the old map with v=theta=0. This
    proof applies only to the generated static, fixed-zero ground model.
    """
    original, expected = build_deck(base["nx"], base["ny"], base["sign"],
                                    base["load_name"], nz=base["nz"])
    if _hash(base) != _hash(expected):
        raise ReferenceParseError("root proof requires exact fixed-zero static base")
    base = expected
    root = set(base["root_nodes"])
    physical = base["physical_nodes"]
    actual = {n for n, x in physical.items() if x[0] == 0.0}
    if root != actual or root & set(base["patch_nodes"]):
        raise ReferenceParseError("root coverage overlap/gap")
    used = set().union(*(set(c) for c in base["elements"].values()))
    if not root <= used:
        raise ReferenceParseError("root contains detached node")
    return {"physical_root_nodes": len(root), "fixed_physical_dofs": 3*len(root),
            "admitted_displacement_space": "u_i=0 at every physical root node",
            "both_directions_proved": True,
            "original_deck_sha256": hashlib.sha256(original.encode("ascii")).hexdigest()}


def root_wrench(base, reactions):
    """Dual of u_i=v+theta cross (x_i-ref), with input geometry lever arms."""
    root_elimination_proof(base)
    physical = {int(n): p for n, p in base["physical_nodes"].items()}
    if set(reactions) != set(base["root_nodes"]):
        raise ReferenceParseError("missing/extra root reaction data")
    ref = base["control_nodes"].get(base["controls"]["root_ref"])
    if ref is None:
        ref = base["control_nodes"][str(base["controls"]["root_ref"])]
    forces, moments = [], []
    for n, f in reactions.items():
        if len(f) != 3 or not all(math.isfinite(v) for v in f):
            raise ReferenceParseError("invalid root reaction vector")
        forces.append(f)
        moments.append(_cross(tuple(a-b for a,b in zip(physical[n], ref)), f))
    return tuple(math.fsum(f[j] for f in forces) for j in range(3)) + tuple(
        math.fsum(m[j] for m in moments) for j in range(3))


def physical_pose_and_work(base, u):
    """Recover port pose and verify its independent discrete dual force/work map."""
    root_elimination_proof(base)
    physical = {int(n): p for n,p in base["physical_nodes"].items()}
    patch = base["patch_nodes"]
    if set(u) != set(physical):
        raise ReferenceParseError("missing/extra physical displacement data")
    p = np.array([physical[n] for n in patch], dtype=float)
    v = np.array([u[n] for n in patch], dtype=float)
    if v.shape != p.shape or not np.isfinite(v).all():
        raise ReferenceParseError("invalid physical displacement vectors")
    center, mean = p.mean(axis=0), v.mean(axis=0)
    arms = p-center
    inertia = np.eye(3)*np.sum(arms*arms)-arms.T@arms
    theta = np.linalg.solve(inertia, np.sum(np.cross(arms, v-mean), axis=0))
    control_nodes = {int(n): p for n,p in base["control_nodes"].items()}
    port = np.array(control_nodes[base["controls"]["patch_ref"]])
    translation = mean+np.cross(theta, port-center)
    predicted = mean+np.cross(theta, arms)
    gap = float(np.max(np.abs(predicted-v)))
    scale = float(np.max(np.abs(v)))
    limit = max(128*math.ulp(scale), 1e-8*scale)
    if gap > limit:
        raise ReferenceParseError("physical patch is not a rigid displacement map")
    force, couple = np.array(base["applied_force_N"]), np.array(base["applied_moment_Nm"])
    dual = np.linalg.solve(inertia, couple+np.cross(port-center, force))
    nodal_force = force/len(patch)+np.cross(dual, arms)
    resultant = nodal_force.sum(axis=0)
    moment = np.cross(p-port, nodal_force).sum(axis=0)
    pairing = math.fsum(float(a*b) for a,b in zip(nodal_force.flat, v.flat))
    port_work = float(force@translation+couple@theta)
    if (np.max(np.abs(resultant-force)) > 1e-12*max(1., np.linalg.norm(force))
            or np.max(np.abs(moment-couple)) > 1e-12*max(1., np.linalg.norm(couple))
            or abs(pairing-port_work) > 1e-12*max(abs(pairing), abs(port_work), 1e-100)):
        raise ReferenceParseError("force/moment/work dual map failed")
    return {"translation_m": translation.tolist(), "theta_rad": theta.tolist(),
            "rigid_mapping_max_gap_m": gap, "external_final_pairing_J": pairing,
            "port_pairing_J": port_work, "load_resultant_N": resultant.tolist(),
            "load_moment_about_port_Nm": moment.tolist()}


def parse_precision_result(data, dat, stdout, deck, manifest, *, paired_original_dat=None):
    """Strict candidate-bound binary and DAT evidence; never assign acceptance."""
    base = _validate_candidate(deck, manifest)
    proof = root_elimination_proof(base)
    headers = list(_ENERGY.finditer(dat))
    if len(headers) != 1:
        raise ReferenceParseError("missing/duplicate/unsupported integrated ELSE dataset")
    header = headers[0]
    if _printed_number(header[1])[0] != 1.0:
        raise ReferenceParseError("ELSE is not at completed load time")
    # CCX chooses print-group ordering; ELSE need not be the final dataset.
    # Delimit only by validated ASCII nodal headers, never by binary payload.
    following = [h.start() for h in _HEADER.finditer(dat) if h.start() >= header.end()]
    end = min(following, default=len(dat))
    rows = {}
    for row in dat[header.end():end].splitlines():
        if not row.strip():
            continue
        fields = row.split()
        if len(fields) != 2 or not re.fullmatch(r"[1-9]\d*", fields[0]):
            raise ReferenceParseError("unsupported or malformed ELSE row")
        e = int(fields[0])
        if e in rows:
            raise ReferenceParseError("duplicate ELSE element")
        value, bound, _ = _printed_number(fields[1])
        if value < 0:
            raise ReferenceParseError("negative elastic internal energy")
        rows[e] = (value, bound)
    if set(rows) != {int(e) for e in base["elements"]}:
        raise ReferenceParseError("incomplete/unexpected integrated energy elements")
    printed = parse_result(dat[:header.start()]+dat[end:], stdout, base)
    u, rf = read_double_output(data, base)
    pose = physical_pose_and_work(base, u)
    for key, observed, bound in (
        ("translation_m", printed["patch_ref_displacement_m"], printed["patch_ref_displacement_rounding_bound_m"]),
        ("theta_rad", printed["patch_rot_theta_rad"], printed["patch_rot_theta_rounding_bound_rad"]),
    ):
        if any(abs(a-b) > c+64*max(math.ulp(a),math.ulp(b)) for a,b,c in zip(pose[key], observed, bound)):
            raise ReferenceParseError("physical port differs from printed control rounding")
    wrench = root_wrench(base, rf)
    reaction_supported = manifest["variant"] == ELIMINATED
    expected = tuple(base["expected_root_force_N"])+tuple(base["expected_root_moment_Nm"])
    paired = None
    if paired_original_dat is not None:
        old = parse_result(paired_original_dat, stdout, base)
        actual = tuple(old["actual_root_force_N"])+tuple(old["actual_root_moment_Nm"])
        bounds = tuple(old["root_force_rounding_bound_N"])+tuple(old["root_moment_rounding_bound_Nm"])
        paired = all(abs(a-b) <= c+64*max(math.ulp(a),math.ulp(b))
                     for a,b,c in zip(wrench, actual, bounds))
    blockers = ["ELSE integrated energy is e13.6 print-limited; precise energy is not reported",
                "external result is development evidence; in-plane convergence and native comparison remain open"]
    if not reaction_supported:
        blockers.append("original rigid-root MPC field is not independently interpreted as support reaction by this variant")
    return {"status": "PARSED_DEVELOPMENT_ONLY", "acceptance": False,
        "variant": manifest["variant"], "candidate_sha256": manifest["deck_sha256"],
        "control_nodes_in_binary": False, "port": pose, "root_elimination_proof": proof,
        "printed_root_controls_are_inactive": reaction_supported,
        "root_displacement_max_m": max(abs(v) for n in base["root_nodes"] for v in u[n]),
        "root_binary_field_wrench": wrench, "root_binary_field_is_reaction": reaction_supported,
        "paired_original_DAT_root_wrench_within_rounding": paired,
        "root_wrench_residual": tuple(a-b for a,b in zip(wrench,expected)) if reaction_supported else None,
        "independent_integrated_internal_energy_J": math.fsum(v for v,b in rows.values()),
        "energy_print_rounding_bound_J": math.fsum(b for v,b in rows.values()),
        "linear_energy_minus_half_final_pairing_J": math.fsum(v for v,b in rows.values())-0.5*pose["external_final_pairing_J"],
        "can_certify_energy_work_1e_minus_8": False,
        "paired_printed_control_result": printed, "blockers": blockers}


def compare_precision_pair(original_inputs, eliminated_inputs):
    """Complete saved-output comparison, retaining every failed support check.

    Each input has data/dat/stdout/deck/manifest keys. No quantitative normalized
    acceptance/floor adjudicator exists for these development outputs; none is
    invented here.
    Binary original ROOT field agreement is a numeric observation only and does
    not confer MPC-reaction meaning. No qualification or pair pass is assigned.
    """
    old_base = _validate_candidate(original_inputs['deck'],original_inputs['manifest'])
    new_base = _validate_candidate(eliminated_inputs['deck'],eliminated_inputs['manifest'])
    if (original_inputs['manifest']['variant'] != ORIGINAL
            or eliminated_inputs['manifest']['variant'] != ELIMINATED
            or _hash(old_base) != _hash(new_base)):
        raise ReferenceParseError('paired cases must differ only in declared fixed-root representation')
    old = parse_precision_result(**original_inputs)
    # Isolate the already-validated original nodal print groups for the
    # supporting old-control comparison; keep the full original DAT unchanged.
    dat = original_inputs['dat']
    h = list(_ENERGY.finditer(dat))[0]
    end = min((x.start() for x in _HEADER.finditer(dat) if x.start() >= h.end()),default=len(dat))
    new = parse_precision_result(**eliminated_inputs,paired_original_dat=dat[:h.start()]+dat[end:])
    old_u,old_rf = read_double_output(original_inputs['data'],old_base)
    new_u,new_rf = read_double_output(eliminated_inputs['data'],new_base)
    control = old['paired_printed_control_result']
    centers = tuple(control['actual_root_force_N'])+tuple(control['actual_root_moment_Nm'])
    bounds = tuple(control['root_force_rounding_bound_N'])+tuple(control['root_moment_rounding_bound_Nm'])
    component_rows = []
    for label,actual,center,bound in zip(('Fx','Fy','Fz','Mx','My','Mz'),
            new['root_binary_field_wrench'],centers,bounds):
        allowance = bound+64*max(math.ulp(actual),math.ulp(center))
        gap = actual-center
        component_rows.append({'component':label,'new_physical_root_binary':actual,
            'old_control_DAT_center':center,'old_DAT_half_print_unit':bound,
            'existing_binary_conversion_allowance':allowance,
            'difference':gap,'difference_over_half_print_unit':abs(gap)/bound,
            'within_existing_print_comparison':abs(gap)<=allowance})
    pose_delta = {key:[a-b for a,b in zip(new['port'][key],old['port'][key])]
                  for key in ('translation_m','theta_rad')}
    pairing_delta = new['port']['external_final_pairing_J']-old['port']['external_final_pairing_J']
    pose_checks = {}
    for key,bound_key in (('translation_m','patch_ref_displacement_rounding_bound_m'),
                          ('theta_rad','patch_rot_theta_rounding_bound_rad')):
        limits = [a+b for a,b in zip(control[bound_key],new['paired_printed_control_result'][bound_key])]
        pose_checks[key] = {'combined_print_bounds':limits,
            'within_original_pair_criterion':all(abs(x)<=b+1e-20 for x,b in zip(pose_delta[key],limits))}
    work_bound = control['conjugate_external_work_rounding_bound_J']+new['paired_printed_control_result']['conjugate_external_work_rounding_bound_J']
    residual = new['root_wrench_residual']
    return {'status':'SAVED_PAIR_COMPARISON_DEVELOPMENT_ONLY','acceptance':False,
        'supporting_original_DAT_wrench_check_passed':new['paired_original_DAT_root_wrench_within_rounding'],
        'failed_support_components':[r['component'] for r in component_rows if not r['within_existing_print_comparison']],
        'supporting_wrench_components':component_rows,
        'physical_displacement_binary64_vectors_equal':old_u==new_u,
        'physical_displacement_node_count':len(old_u),
        'original_and_eliminated_binary_ROOT_fields_equal':old_rf==new_rf,
        'original_ROOT_field_reaction_interpretation_supported':False,
        'physical_pose_delta':pose_delta,'physical_pose_criteria':pose_checks,
        'final_pairing_delta_J':pairing_delta,'paired_work_print_bound_J':work_bound,
        'paired_work_within_original_criterion':abs(pairing_delta)<=work_bound,
        'new_direct_root_wrench_residual':residual,
        'new_direct_root_wrench_max_abs_residual':max(abs(x) for x in residual),
        'normalized_root_balance_acceptance':'NOT_EVALUATED',
        'normalized_acceptance_reason':'no executed quantitative normalized-floor adjudicator exists for this development reference; no floor invented',
        'binary_work_map_relative_gap':abs(new['port']['external_final_pairing_J']-new['port']['port_pairing_J'])/max(
            abs(new['port']['external_final_pairing_J']),abs(new['port']['port_pairing_J'])),
        'integrated_energy_delta_J':new['independent_integrated_internal_energy_J']-old['independent_integrated_internal_energy_J'],
        'energy_print_precision_only':True,
        'disposition':'supporting wrench print comparison failed; retain failure and all other component observations; E02 remains open'}
