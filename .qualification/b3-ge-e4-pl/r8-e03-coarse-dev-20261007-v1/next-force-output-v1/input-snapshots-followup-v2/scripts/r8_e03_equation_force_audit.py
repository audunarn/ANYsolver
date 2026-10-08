"""Bounded equation-force diagnostic; no RF reader, solver launch or scoring.

Convention: g = p + r_SPC + C.T lambda. Inputs must contain complete element
internal nodal forces g; a support-only RF inventory is insufficient.
"""
from __future__ import annotations

import hashlib
import json
import math
import copy

import numpy as np


MAX_NODES = 333
MAX_ROWS = 48
MAX_TERMS = 24
SEMANTICS = "UNCONDENSED_ELEMENT_INTERNAL_NODAL_FORCE_GRADIENT"
CCX_VERSION = "2.23"
CCX_SHA256 = "27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f"
CCX_SOURCE_FILES_SHA256 = {
    "resultsforc.c":"26d324920e8ad16a2db0c736d524a03781880863e0cd089c0a4ce22d7410c505",
    "results.c":"9113a4984342355ff15bb16a609c5bdb034183c951719b064037b3858eac24dd",
    "frd.c":"6439bca2ae53c813ab6887c3c560dd15db5947fd8cf9b9f01ada5753d5ed9915",
}


class EquationForceAuditError(ValueError):
    """Missing observability, unsupported semantics or inadmissible local system."""


def _refuse(message):
    raise EquationForceAuditError(message)


def _number(value):
    if type(value) not in (int, float):
        _refuse("finite real scalar required")
    try:
        value = float(value)
    except (OverflowError, ValueError) as error:
        raise EquationForceAuditError("finite binary64 scalar required") from error
    if not math.isfinite(value):
        _refuse("finite real scalar required")
    return value


def _vectors(value, nodes=None):
    if type(value) is not dict or not 0 < len(value) <= MAX_NODES:
        _refuse("bounded complete node-vector map required")
    result = {}
    for node, vector in value.items():
        if type(node) is not int or node <= 0 or type(vector) not in (tuple, list) or len(vector) != 3:
            _refuse("positive integer node identity and three components required")
        result[node] = tuple(_number(x) for x in vector)
    if nodes is not None and result.keys() != nodes:
        _refuse("complete all-node force inventory required; missing or foreign node")
    return result


def _dof(value, nodes):
    if type(value) not in (tuple, list) or len(value) != 2:
        _refuse("declared node/component DOF required")
    node, component = value
    if type(node) is not int or node not in nodes or type(component) is not int or component not in (1, 2, 3):
        _refuse("declared physical translation DOF required")
    return node, component


def _inputs(coordinates, equations, pivots, support_dofs, element_forces, applied_forces):
    xyz = _vectors(coordinates)
    nodes = xyz.keys()
    g, p = _vectors(element_forces, nodes), _vectors(applied_forces, nodes)
    if type(equations) not in (list, tuple) or not 0 < len(equations) <= MAX_ROWS:
        _refuse("one to48 declared equation rows required")
    if type(pivots) not in (list, tuple) or len(pivots) != len(equations):
        _refuse("one explicit dependent pivot per equation required")
    pivots = tuple(_dof(dof, nodes) for dof in pivots)
    if len(set(pivots)) != len(pivots):
        _refuse("distinct dependent pivots required")
    if type(support_dofs) not in (list, tuple):
        _refuse("explicit support DOF sequence required")
    supports = tuple(_dof(dof, nodes) for dof in support_dofs)
    if len(set(supports)) != len(supports) or set(supports) & set(pivots):
        _refuse("distinct supports and pivots outside supports required")
    rows = []
    for i, source in enumerate(equations):
        if type(source) not in (list, tuple) or not 0 < len(source) <= MAX_TERMS:
            _refuse("bounded nonempty physical equation row required")
        row = {}
        for term in source:
            if type(term) not in (list, tuple) or len(term) != 3:
                _refuse("node/component/coefficient equation term required")
            dof = _dof(term[:2], nodes)
            coefficient = _number(term[2])
            if dof in row or coefficient == 0.:
                _refuse("distinct nonzero equation terms required")
            row[dof] = coefficient
        if pivots[i] not in row:
            _refuse("each declared pivot must occur in its own equation")
        rows.append(row)
    return xyz, tuple(rows), pivots, supports, g, p


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")).hexdigest()


def _identity(data):
    xyz, rows, pivots, supports, g, p = data
    ordered = lambda vectors: [[node, *vectors[node]] for node in sorted(vectors)]
    model = dict(coordinates=ordered(xyz), equations=[[[*dof, row[dof]] for dof in sorted(row)] for row in rows],
        pivots=pivots, support_dofs=sorted(supports), applied_forces=ordered(p))
    return dict(model_sha256=_digest(model), element_forces_sha256=_digest(ordered(g)))


def input_identity(*, coordinates, equations, pivots, support_dofs, element_forces, applied_forces):
    """Bind complete declared inputs without a numerical solve or RF ingestion."""
    return _identity(_inputs(coordinates, equations, pivots, support_dofs, element_forces, applied_forces))


def _provenance(value, identity=None):
    # Confirmation evidence is root-reviewed caller authority, not established by
    # a flag in this diagnostic. Missing or cross-version claims fail closed.
    if type(value) is not dict:
        _refuse("explicit finite JSON provenance required")
    try:
        encoded = json.dumps(value, allow_nan=False)
        if len(encoded) > 32768:
            _refuse("bounded provenance required")
        value = json.loads(encoded)
    except (ValueError, TypeError, RecursionError) as error:
        raise EquationForceAuditError("bounded finite JSON provenance required") from error
    if value.get("semantics") != SEMANTICS or (identity is not None and any(value.get(key) != digest for key, digest in identity.items())):
        _refuse("declared g semantics and exact model/force identities required")
    producer = value.get("producer")
    if producer == "synthetic":
        if value.get("version") != "synthetic-v1" or value.get("field") != "synthetic-element-gradient":
            _refuse("honest synthetic producer/version/field required")
    elif producer == "CalculiX":
        if value.get("version") != CCX_VERSION or value.get("executable_sha256") != CCX_SHA256 or value.get("field") != "RF/FORC":
            _refuse("exact pinned CCX2.23 producer/version/binary/field required")
        confirmation = value.get("independent_semantics_confirmation")
        if type(confirmation) is not dict:
            _refuse("CCX RF/FORC ingestion refused: independent exact-release fn semantics confirmation required")
        expected = dict(status="CONFIRMED_BY_INDEPENDENT_REVIEW", version=CCX_VERSION,
            executable_sha256=CCX_SHA256, semantics=SEMANTICS,
            runtime_binary_correspondence="INDEPENDENTLY_CONFIRMED")
        if any(confirmation.get(key) != item for key, item in expected.items()):
            _refuse("independent confirmation must bind exact release/binary/g semantics")
        if confirmation.get("source_files_sha256") != CCX_SOURCE_FILES_SHA256:
            _refuse("exact independently inspected release source-file identities required")
        method = confirmation.get("correspondence_method")
        if method not in ("independent_analytic_spc_mpc_observable_control", "verified_source_build_identity"):
            _refuse("independent binary-correspondence method required")
        evidence_keys = ["exact_release_source_sha256", "evidence_sha256"]
        if method == "independent_analytic_spc_mpc_observable_control":
            evidence_keys.append("control_evidence_sha256")
        for key in evidence_keys:
            digest = confirmation.get(key)
            if type(digest) is not str or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                _refuse("independently reviewed source/evidence SHA256 identities required")
        for key in ("review_id", "independent_reviewer_id", "evidence_reference"):
            if type(confirmation.get(key)) is not str or not confirmation[key].strip():
                _refuse("concrete independent review and evidence references required")
    else:
        _refuse("unsupported force producer; no source-version assumption permitted")
    return value


def _wrench(vectors, coordinates):
    # Same world origin for every force and moment; no deficit-based adjustment.
    try:
        force = [math.fsum(v[j] for v in vectors.values()) for j in range(3)]
        moments = []
        for node, (fx, fy, fz) in vectors.items():
            x, y, z = coordinates[node]
            moment = (y*fz-z*fy, z*fx-x*fz, x*fy-y*fx)
            if not all(math.isfinite(value) for value in moment):
                _refuse("finite rigid-work moment arithmetic required")
            moments.append(moment)
        moment = [math.fsum(v[j] for v in moments) for j in range(3)]
    except (OverflowError, ValueError) as error:
        raise EquationForceAuditError("finite rigid-work force/moment arithmetic required") from error
    if not all(math.isfinite(value) for value in force+moment):
        _refuse("finite rigid-work wrench required")
    return force+moment


def audit_equation_forces(*, coordinates, equations, pivots, support_dofs,
        element_forces, applied_forces, provenance):
    """Recover equation actions from dependent equilibrium, never global deficit.

    Local dense solve dimension is at most48. No tolerance or accuracy verdict is
    applied to reported equilibrium observables. No external process is launched.
    """
    data = _inputs(coordinates, equations, pivots, support_dofs, element_forces, applied_forces)
    xyz, rows, pivots, supports, g, p = data
    identity = _identity(data)
    provenance = _provenance(provenance, identity)
    # Equation DOFs may be coupled: solve the complete transposed dependent block.
    matrix = np.array([[row.get(dof, 0.) for row in rows] for dof in pivots])
    rhs = np.array([g[node][component-1]-p[node][component-1] for node, component in pivots])
    if not np.isfinite(rhs).all():
        _refuse("finite dependent equilibrium arithmetic required")
    try:
        singular_values = np.linalg.svd(matrix, compute_uv=False)
    except np.linalg.LinAlgError as error:
        raise EquationForceAuditError("unresolved local equation-force rank") from error
    if not np.isfinite(singular_values).all():
        _refuse("finite local equation-force rank required")
    rank_floor = len(rows)*np.finfo(float).eps*singular_values[0]
    if singular_values[-1] <= rank_floor:
        _refuse("singular or numerically dependent local equation-force system")
    try:
        multipliers = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError as error:
        raise EquationForceAuditError("singular local equation-force system") from error
    if not np.isfinite(multipliers).all():
        _refuse("finite local equation-force solution required")
    contributions = {node:[[] for _ in range(3)] for node in xyz}
    row_rigid_work = []
    for index, (row, multiplier) in enumerate(zip(rows, multipliers)):
        row_vectors = {}
        for (node, component), coefficient in row.items():
            contributions[node][component-1].append(coefficient*float(multiplier))
            row_vectors.setdefault(node, [0., 0., 0.])[component-1] = coefficient
        row_rigid_work.append(dict(row=index, coefficients_of_rigid_work=_wrench(row_vectors, xyz)))
    try:
        action = {node:[math.fsum(values) for values in components] for node, components in contributions.items()}
    except (OverflowError, ValueError) as error:
        raise EquationForceAuditError("finite equation-action arithmetic required") from error
    if not all(math.isfinite(value) for vector in action.values() for value in vector):
        _refuse("finite equation-action arithmetic required")
    support_set = set(supports)
    recovered = {node:[g[node][j]-p[node][j]-action[node][j] for j in range(3)] for node in xyz}
    reactions = {node:[recovered[node][j] if (node, j+1) in support_set else 0. for j in range(3)] for node in xyz}
    free = {node:[0. if (node, j+1) in support_set else recovered[node][j] for j in range(3)] for node in xyz}
    result = dict(status="DIAGNOSTIC_ONLY_NOT_QUALIFIED", production_qualified=False, e03_accepted=False,
        accuracy_scored=False, semantics_confirmation_is_caller_evidence=True, provenance=provenance, identity=identity,
        convention="g=p+r_SPC+C^Tlambda", node_count=len(xyz), equation_count=len(rows),
        multipliers_by_equation=multipliers.tolist(), equation_actions_n=action, spc_reactions_n=reactions,
        free_residual_n=free, dependent_residual_n=[recovered[n][c-1] for n, c in pivots],
        free_residual_max_abs_n=max(abs(v) for vector in free.values() for v in vector),
        equation_rigid_work=row_rigid_work,
        rigid_work_wrenches=dict(element_internal=_wrench(g, xyz), applied=_wrench(p, xyz),
            equation_action=_wrench(action, xyz), spc_reaction=_wrench(reactions, xyz),
            free_residual=_wrench(free, xyz),
            external_balance=_wrench({node:[p[node][j]+reactions[node][j] for j in range(3)] for node in xyz}, xyz)),
        local_solve=dict(dimension=len(rows), rank_floor=float(rank_floor),
            condition_number=float(singular_values[0]/singular_values[-1])))
    try:
        return json.loads(json.dumps(result, allow_nan=False))
    except (ValueError, OverflowError) as error:
        raise EquationForceAuditError("finite diagnostic output required") from error


def e03_inputs(case, metadata):
    """Prepare exact frozen coarse model inputs, not forces or new physical runs."""
    from scripts.r8_e03_curved_reference import build_deck, digest, validate_case

    validate_case(case)
    if case["level"] != 0 or case["offset_sign"] != 1:
        _refuse("exact E03 coarse level0/+offset contract required")
    _, expected = build_deck(case)
    if digest(metadata) != digest(expected):
        _refuse("exact frozen E03 deck metadata required")
    xyz = expected["physical_nodes"]
    if len(xyz) != MAX_NODES or len(expected["deck_equations"]) != MAX_ROWS:
        _refuse("declared333-node/48-equation E03 contract required")
    return dict(coordinates=xyz, equations=expected["deck_equations"],
        pivots=[tuple(row[0][:2]) for row in expected["deck_equations"]],
        support_dofs=[(node, component) for node in expected["root_nodes"] for component in (1, 2, 3)],
        applied_forces={node:expected["nodal_loads"].get(node, (0., 0., 0.)) for node in xyz})


def prepare_complete_force_output(deck, metadata):
    """Only change RF output ROOT->PHYSICAL; retain real supports separately.

    This prepares bytes only. It does not authorize a physical execution.
    """
    from scripts.r8_e03_curved_reference import digest

    if type(deck) is str:
        try:
            deck = deck.encode("ascii")
        except UnicodeEncodeError as error:
            raise EquationForceAuditError("original ASCII deck required") from error
    if type(deck) is not bytes or type(metadata) is not dict:
        _refuse("original ASCII deck bytes and declared metadata required")
    try:
        original = json.loads(json.dumps(metadata, allow_nan=False))
        original_id = original.pop("metadata_id")
        if digest(original) != original_id:
            _refuse("original metadata identity mismatch")
        original["metadata_id"] = original_id
    except (KeyError, ValueError, TypeError) as error:
        raise EquationForceAuditError("finite original metadata identity required") from error
    original_sha = hashlib.sha256(deck).hexdigest()
    if original.get("deck_sha256") != original_sha:
        _refuse("exact original deck bytes required")
    old = b"*NODE OUTPUT,DOUBLE,NSET=ROOT\nRF\n"
    new = b"*NODE OUTPUT,DOUBLE,NSET=PHYSICAL\nRF\n"
    if deck.count(old) != 1 or deck.count(new) != 0 or not deck.endswith(old+b"*END STEP\n"):
        _refuse("exact one original ROOT/RF output card required")
    modified = deck.replace(old, new, 1)
    if modified.replace(new, old, 1) != deck:
        _refuse("output-only deck reversibility required")
    nodes = sorted(int(node) for node in original["physical_nodes"])
    if len(nodes) != MAX_NODES or len(set(nodes)) != MAX_NODES or len(original["root_nodes"]) != 49:
        _refuse("declared333 output nodes and49 physical supports required")
    prepared = dict(schema="E03_COMPLETE_ELEMENT_FORCE_OUTPUT_DIAGNOSTIC_V1",
        original_metadata=original, original_deck_sha256=original_sha,
        output_deck_sha256=hashlib.sha256(modified).hexdigest(),
        force_output_nodes=nodes, physical_support_nodes=copy.deepcopy(original["root_nodes"]),
        only_change="RF output NSET ROOT->PHYSICAL", production_qualified=False, e03_accepted=False)
    prepared["prepared_metadata_sha256"] = digest(prepared)
    return modified, prepared


def audit_saved_complete_force_output(case, prepared_metadata, frd, *, provenance):
    """Strict complete-output reader plus audit; unconfirmed CCX input is refused.

    A detached inventory projection changes read_double_output's expected FORC
    node IDs only. The actual SPC support set remains the original49 nodes.
    """
    from scripts.r8_e02_double_output import read_double_output
    from scripts.r8_e03_curved_reference import build_deck, digest

    if type(provenance) is not dict or provenance.get("producer") != "CalculiX":
        _refuse("saved CCX artifact ingestion requires independently confirmed CalculiX provenance")
    _provenance(provenance)  # Gate semantics/version/binary before parsing any RF.
    try:
        prepared = json.loads(json.dumps(prepared_metadata, allow_nan=False))
        prepared_id = prepared.pop("prepared_metadata_sha256")
        if digest(prepared) != prepared_id:
            _refuse("prepared output metadata changed")
        original = prepared["original_metadata"]
        original_deck, _ = build_deck(case)
        _, expected = prepare_complete_force_output(original_deck, original)
        if digest(prepared_metadata) != digest(expected):
            _refuse("exact output-only metadata and true supports required")
    except (KeyError, ValueError, TypeError) as error:
        raise EquationForceAuditError("finite exact complete-output metadata required") from error
    inputs = e03_inputs(case, original)
    projection = copy.deepcopy(original)
    projection["root_nodes"] = list(prepared["force_output_nodes"])
    # Pure binary inventory helper: root_nodes here declares FORC output IDs,
    # not an altered support boundary. Recovery consumes inputs.support_dofs.
    displacement, g = read_double_output(frd, projection)
    result = audit_equation_forces(**inputs, element_forces=g, provenance=provenance)
    result["saved_output"] = dict(frd_sha256=hashlib.sha256(frd).hexdigest(),
        output_nodes=len(g), displacement_nodes=len(displacement), physical_support_nodes=49,
        prepared_metadata_sha256=prepared_id, original_deck_sha256=prepared["original_deck_sha256"],
        output_deck_sha256=prepared["output_deck_sha256"])
    return result
