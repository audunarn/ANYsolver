"""Saved-output follow-up diagnostics. This module grants no launch authority."""
import copy
import hashlib
import json
import math
import re
import time

from scripts import r8_e03_equation_force_audit as audit

INSTRUMENT_LIMIT = 1e-6
MODES = ("controls", "analytic", "finalize-analytic", "external", "finalize-external")
THREAD_ENVIRONMENT = {name:"1" for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS", "NUMBA_NUM_THREADS", "NUMBER_OF_CPUS", "CCX_NPROC_CFD", "CCX_NPROC_RESULTS")}


class FollowupError(ValueError):
    pass


def terminate_owned_descendants(registry, *, timeout=2.):
    """Kill only captured process objects with unchanged creation identity.

    The caller records descendants while their owned parent is alive. A failed
    identity/termination check is uncertainty, never permission to kill a PID.
    """
    if type(registry) is not dict or len(registry) > 64 or timeout <= 0:
        raise FollowupError("bounded owned-process registry required")
    deadline = time.monotonic()+timeout
    try:
        targets = []
        for pid, (process, creation_time) in registry.items():
            if process.pid != pid or not math.isfinite(creation_time):
                raise FollowupError("owned process identity mismatch")
            if process.is_running():
                if process.create_time() != creation_time:
                    raise FollowupError("owned PID creation identity changed")
                targets.append(process)
        for process in reversed(targets): process.kill()
        for process in reversed(targets):
            process.wait(timeout=max(.001, deadline-time.monotonic()))
            if process.is_running(): raise FollowupError("owned descendant remains alive")
    except Exception as error:
        if isinstance(error, FollowupError): raise
        raise FollowupError("owned descendant cleanup unproven") from error


def fatal_monitor_cleanup(owner, registry):
    """All fatal monitor paths terminate observed descendants before owner."""
    terminate_owned_descendants(registry)
    owner.kill()


def validate_thread_environment(value):
    if value != THREAD_ENVIRONMENT:
        raise FollowupError("complete inherited numerical-thread1 override contract required")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def detached(value):
    try:
        text = json.dumps(value, allow_nan=False)
        if len(text) > 4*1024*1024:
            raise ValueError("oversized JSON")
        return json.loads(text)
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise FollowupError("bounded detached finite JSON required") from error


def validate_authority(authority, ledger, mode):
    authority, ledger = detached(authority), detached(ledger)
    if mode not in MODES or authority.get("status") != "APPROVED" or not authority.get("approval_evidence"):
        raise FollowupError("fresh approved human authority required")
    if ledger.get("status") != "APPROVED" or authority.get("total_seconds") != 150 or ledger.get("total_seconds") != 150:
        raise FollowupError("exact fresh150 accounting required")
    if authority.get("reserve_seconds") != 60 or authority.get("allowed_modes") != list(MODES):
        raise FollowupError("exact modes/reserve required")
    used = ledger.get("used_seconds")
    remaining = ledger.get("remaining_seconds")
    if type(used) not in (int, float) or type(remaining) not in (int, float) or not math.isfinite(used) or not math.isfinite(remaining) or used < 0 or remaining != 150-used or remaining < 0:
        raise FollowupError("known consistent process-wall remainder required")
    return authority, ledger


def read_analytic_dat(data):
    """Exact CCX2.23 printout.f labels; one ALL/time1 U and RF frame."""
    if type(data) is not bytes or not 0 < len(data) <= 65536:
        raise FollowupError("bounded original DAT bytes required")
    try:
        lines = [line.strip() for line in data.decode("ascii").splitlines() if line.strip()]
    except UnicodeDecodeError as error:
        raise FollowupError("ASCII DAT required") from error
    labels = ("displacements (vx,vy,vz)", "forces (fx,fy,fz)")
    if len(lines) != 10:
        raise FollowupError("exact two complete four-node DAT frames required")
    result = []
    for offset, label in zip((0, 5), labels):
        match = re.fullmatch(re.escape(label)+r" for set ALL and time\s+([+-]?\d*\.?\d+(?:[EeDd][+-]?\d+)?)", lines[offset])
        if not match or float(match[1].replace("D", "E").replace("d", "e")) != 1.:
            raise FollowupError("exact label/set/final-time header required")
        values = {}
        for line in lines[offset+1:offset+5]:
            fields = line.split()
            if len(fields) != 4 or not re.fullmatch(r"[1-4]", fields[0]):
                raise FollowupError("four nodes/three global components required")
            node = int(fields[0])
            if node in values:
                raise FollowupError("duplicate DAT node")
            try:
                vector = [float(v.replace("D", "E").replace("d", "e")) for v in fields[1:]]
            except ValueError as error:
                raise FollowupError("numeric DAT component required") from error
            if not all(math.isfinite(v) for v in vector):
                raise FollowupError("finite DAT components required")
            values[node] = vector
        if set(values) != {1, 2, 3, 4}:
            raise FollowupError("complete DAT inventory required")
        result.append(values)
    return tuple(result)


def completed_outputs(sta, stdout, stderr):
    if any(type(v) is not bytes for v in (sta, stdout, stderr)) or len(sta) > 65536 or len(stdout)+len(stderr) > 8*1024*1024:
        raise FollowupError("bounded original STA/stdout/stderr required")
    if re.search(rb"\*ERROR|\*WARNING|not converg|divergen|incomplete", stdout+stderr, re.I):
        raise FollowupError("diagnosed process output refused")
    if not re.search(rb"CalculiX\s+Version\s+2\.23\b", stdout) or not re.search(rb"Job finished", stdout, re.I):
        raise FollowupError("actual version2.23/completion stdout required")
    declarations = re.findall(rb"Using\s+up\s+to\s+(\d+)\s+cpu\(s\)", stdout, re.I)
    if not declarations or any(int(v) != 1 for v in declarations):
        raise FollowupError("actual numerical CPU declaration1 required")
    try:
        lines = [line.split() for line in sta.decode("ascii").splitlines() if line.strip()]
        if len(lines) != 3 or lines[0] != ["SUMMARY", "OF", "JOB", "INFORMATION"] or lines[1] != ["STEP", "INC", "ATT", "ITRS", "TOT", "TIME", "STEP", "TIME", "INC", "TIME"]:
            raise ValueError("STA headers")
        row = lines[2]
        if len(row) != 7 or row[:3] != ["1", "1", "1"] or not row[3].isdigit() or int(row[3]) < 1 or any(float(v) != 1. for v in row[4:]):
            raise ValueError("STA increment")
    except (UnicodeDecodeError, ValueError) as error:
        raise FollowupError("one complete unit-time static STA increment required") from error


def validate_process_receipt(receipt, raw, deck_sha256, command):
    receipt = detached(receipt)
    if receipt.get("exit_code") != 0 or type(receipt.get("exit_code")) is not int or receipt.get("timed_out") is not False:
        raise FollowupError("actual successful untimed-out process required")
    if receipt.get("executable_sha256") != audit.CCX_SHA256 or receipt.get("deck_sha256") != deck_sha256 or receipt.get("command") != command:
        raise FollowupError("exact binary/deck/command binding required")
    for key, value in raw.items():
        if type(value) is not bytes or receipt.get(key+"_sha256") != sha(value):
            raise FollowupError("exact original output hash binding required")
    return receipt


def analytic_candidate(dat, sta, stdout, stderr, *, receipt, deck_sha256, command):
    raw = dict(dat=dat, sta=sta, stdout=stdout, stderr=stderr)
    receipt = validate_process_receipt(receipt, raw, deck_sha256, command)
    completed_outputs(sta, stdout, stderr)
    u, g = read_analytic_dat(dat)
    expected_u, expected_g = (.1, 0., .1, .1), (1., -1., 0., 0.)
    if any(abs(values[n][j]-(expected[n-1] if j == 0 else 0.)) > INSTRUMENT_LIMIT
           for values, expected in ((u, expected_u), (g, expected_g)) for n in range(1, 5) for j in range(3)):
        raise FollowupError("independently derived displacement/element-gradient oracle failed")
    multiplier = g[1][0]-2.
    reaction = [g[2][0], g[3][0]+multiplier]
    if abs(multiplier+1.) > INSTRUMENT_LIMIT or any(abs(v+1.) > INSTRUMENT_LIMIT for v in reaction):
        raise FollowupError("declared-load physical multiplier/reaction oracle failed")
    return detached(dict(status="ANALYTIC_SEMANTICS_REVIEW_CANDIDATE", semantics_adopted=False,
        production_qualified=False, e03_accepted=False, instrumentation_limit=INSTRUMENT_LIMIT,
        u=u, element_gradient=g, physical_multiplier=multiplier, physical_spc_fx=reaction,
        internal_fmpc_is_not_physical_multiplier=True, receipt=receipt))


def validate_confirmation(confirmation, analytic_bindings):
    """Root must author this record after inspecting actual analytic evidence."""
    confirmation, analytic_bindings = detached(confirmation), detached(analytic_bindings)
    provenance = dict(producer="CalculiX", version="2.23", field="RF/FORC",
        executable_sha256=audit.CCX_SHA256, semantics=audit.SEMANTICS,
        independent_semantics_confirmation=confirmation)
    audit._provenance(provenance)
    if confirmation.get("correspondence_method") != "independent_analytic_spc_mpc_observable_control" or confirmation.get("control_bindings") != analytic_bindings:
        raise FollowupError("root-adopted exact observed analytic control bindings required")
    if confirmation.get("control_evidence_sha256") != analytic_bindings.get("candidate_sha256") or confirmation.get("exact_release_source_sha256") != analytic_bindings.get("source_archive_sha256"):
        raise FollowupError("actual candidate/source archive confirmation mismatch")
    return provenance


def external_diagnostic(case, prepared_metadata, frd, sta, stdout, stderr, *, receipt, command, provenance):
    """Same geometry/update/port guards; recovered balance remains diagnostic."""
    from scripts import r8_e03_curved_reference as reference
    from scripts.r8_e02_double_output import read_double_output
    import numpy as np

    if type(provenance) is not dict or provenance.get("producer") != "CalculiX":
        raise FollowupError("independently confirmed CalculiX saved-artifact provenance required")
    audit._provenance(provenance)
    prepared_metadata = detached(prepared_metadata)
    receipt = validate_process_receipt(receipt, dict(frd=frd, sta=sta, stdout=stdout, stderr=stderr), prepared_metadata["output_deck_sha256"], command)
    completed_outputs(sta, stdout, stderr)
    # Rebuild exact original integer-ID metadata; never convert true supports into output nodes.
    _, original = reference.build_deck(case)
    projection = copy.deepcopy(original)
    projection["root_nodes"] = list(prepared_metadata["force_output_nodes"])
    displacement, forces = read_double_output(frd, projection)
    inputs = audit.e03_inputs(case, original)
    provenance = detached(provenance)
    provenance.update(audit.input_identity(**inputs, element_forces=forces))
    result = audit.audit_saved_complete_force_output(case, prepared_metadata, frd, provenance=provenance)
    gaps, tips = [], []
    for port in original["ports"]:
        shell, beam = port["shell_nodes"], port["beam_nodes"]
        connection = reference.fitted_connection([original["physical_nodes"][n] for n in shell], [original["physical_nodes"][n] for n in beam])
        gap = connection["constraint"] @ np.array([displacement[n] for n in (*shell, *beam)]).ravel()
        if not np.isfinite(gap).all() or np.max(abs(gap[:3])) > 1e-10*case["length_m"] or np.max(abs(gap[3:])) > 1e-10:
            raise FollowupError("actual fitted-port compatibility failed")
        gaps.append(dict(point_id=port["point_id"], world_gap=gap.tolist()))
    work = sum(float(np.dot(force, displacement[n])) for n, force in original["nodal_loads"].items())
    if not math.isfinite(work) or work <= 0.:
        raise FollowupError("positive finite actual applied-force work required")
    for tip in original["tips"]:
        _, fit, _ = reference.translation_pose_fit([original["physical_nodes"][n] for n in tip["nodes"]])
        pose = fit @ np.array([displacement[n] for n in tip["nodes"]]).ravel()
        if not np.isfinite(pose).all():
            raise FollowupError("finite actual full6 tip pose required")
        tips.append(dict(rib_index=tip["rib_index"], world_pose=pose.tolist()))
    wrench = result["rigid_work_wrenches"]["external_balance"]
    result.update(point_gaps=gaps, tip_poses=tips, external_work_j=work, receipt=receipt,
        recovered_scaled_balance=reference.balance_measure(case, np.array(wrench[:3]), np.array(wrench[3:])),
        frozen_e03_balance_limit=reference.BALANCE_LIMIT, diagnostic_balance_is_not_acceptance=True)
    return detached(result)
