"""Prepared synthetic gradient/constraint controls; no physical solver or RF import."""
import copy
import struct

import pytest

from scripts import r8_e03_equation_force_audit as audit


@pytest.fixture
def coupled():
    # Two independently specified coupled rows. Known lambda=(2,-1),
    # C.T lambda=(-1,0,1) along x. Loads on BOTH pivots must be subtracted.
    return dict(coordinates={1:[0.,0.,0.], 2:[1.,0.,0.], 3:[2.,0.,0.]},
        equations=[[(1,1,1.), (2,1,2.), (3,1,-3.)],
                   [(1,1,3.), (2,1,4.), (3,1,-7.)]],
        pivots=[(1,1), (2,1)], support_dofs=[(3,1)],
        applied_forces={1:[5.,0.,0.], 2:[-2.,0.,0.], 3:[0.,0.,0.]},
        element_forces={1:[4.,0.,0.], 2:[-2.,0.,0.], 3:[-2.,0.,0.]})


def provenance(inputs):
    return dict(producer="synthetic", version="synthetic-v1", field="synthetic-element-gradient",
        semantics=audit.SEMANTICS, **audit.input_identity(**inputs))


def run(inputs, record=None):
    return audit.audit_equation_forces(**inputs, provenance=provenance(inputs) if record is None else record)


def vector(result, key, node):
    # Detached JSON output has canonical JSON object keys.
    return result[key][str(node)]


def test_full_coupled_transpose_and_loaded_pivots(coupled):
    result = run(coupled)
    assert result["multipliers_by_equation"] == pytest.approx([2., -1.])
    assert vector(result, "spc_reactions_n", 3) == pytest.approx([-3., 0., 0.])
    assert result["free_residual_max_abs_n"] < 1e-13
    assert result["rigid_work_wrenches"]["external_balance"] == pytest.approx([0.]*6, abs=1e-13)
    assert result["local_solve"]["dimension"] == 2


def test_constraint_action_and_spc_sign():
    inputs = dict(coordinates={1:[1.,0.,0.], 2:[0.,0.,0.]},
        equations=[[(1,1,1.), (2,1,-1.)]], pivots=[(1,1)], support_dofs=[(2,1)],
        applied_forces={1:[3.,0.,0.], 2:[0.,0.,0.]},
        element_forces={1:[5.,0.,0.], 2:[-5.,0.,0.]})
    result = run(inputs)
    assert result["multipliers_by_equation"] == [2.]
    assert vector(result, "equation_actions_n", 2) == [-2.,0.,0.]
    assert vector(result, "spc_reactions_n", 2) == [-3.,0.,0.]


def test_offset_common_origin_moment_and_rigid_work():
    inputs = dict(coordinates={1:[0.,0.,0.], 2:[1.,0.,0.], 3:[0.,1.,0.]},
        equations=[[(1,1,-1.), (1,2,-1.), (2,2,1.), (3,1,1.)]],
        pivots=[(2,2)], support_dofs=[(1,1),(1,2),(3,1)],
        applied_forces={1:[0.,0.,0.], 2:[0.,3.,0.], 3:[0.,0.,0.]},
        element_forces={1:[-5.,-5.,0.], 2:[0.,5.,0.], 3:[5.,0.,0.]})
    result = run(inputs)
    assert result["multipliers_by_equation"] == [2.]
    work = result["rigid_work_wrenches"]
    assert work["applied"] == [0.,3.,0.,0.,0.,3.]
    assert work["spc_reaction"] == [0.,-3.,0.,0.,0.,-3.]
    assert work["equation_action"] == [0.]*6
    assert result["equation_rigid_work"][0]["coefficients_of_rigid_work"] == [0.]*6


def test_free_residual_is_reported_not_fitted(coupled):
    coupled["element_forces"][1][2] = .25
    result = run(coupled)
    assert vector(result, "free_residual_n", 1)[2] == .25
    assert result["multipliers_by_equation"] == pytest.approx([2., -1.])
    assert result["free_residual_max_abs_n"] == pytest.approx(.25)
    assert result["status"] == "DIAGNOSTIC_ONLY_NOT_QUALIFIED"
    assert not result["production_qualified"] and not result["e03_accepted"] and not result["accuracy_scored"]


@pytest.mark.parametrize("kind", ["missing-g", "foreign-g", "missing-p", "nonfinite-g", "nonfinite-coordinate"])
def test_complete_finite_all_node_inputs_required(coupled, kind):
    if kind == "missing-g":
        del coupled["element_forces"][3]
    elif kind == "foreign-g":
        coupled["element_forces"][4] = [0.,0.,0.]
    elif kind == "missing-p":
        del coupled["applied_forces"][2]
    elif kind == "nonfinite-g":
        coupled["element_forces"][1][0] = float("nan")
    else:
        coupled["coordinates"][1][0] = float("inf")
    with pytest.raises(audit.EquationForceAuditError):
        run(coupled)


@pytest.mark.parametrize("kind", ["duplicate", "supported", "absent", "foreign", "bool-component"])
def test_invalid_pivots_refused(coupled, kind):
    if kind == "duplicate":
        coupled["pivots"] = [(1,1),(1,1)]
    elif kind == "supported":
        coupled["pivots"][0] = (3,1)
    elif kind == "absent":
        coupled["pivots"][0] = (1,2)
    elif kind == "foreign":
        coupled["pivots"][0] = (4,1)
    else:
        coupled["pivots"][0] = (1,True)
    with pytest.raises(audit.EquationForceAuditError):
        run(coupled)


@pytest.mark.parametrize("kind", ["singular", "duplicate-term", "zero-term", "nonfinite-term", "over48"])
def test_equation_system_refusals(coupled, kind):
    if kind == "singular":
        coupled["equations"][1] = copy.deepcopy(coupled["equations"][0])
    elif kind == "duplicate-term":
        coupled["equations"][0].append(coupled["equations"][0][0])
    elif kind == "zero-term":
        coupled["equations"][0][0] = (1,1,0.)
    elif kind == "nonfinite-term":
        coupled["equations"][0][0] = (1,1,float("inf"))
    else:
        coupled["equations"] *= 25
    with pytest.raises(audit.EquationForceAuditError):
        run(coupled)


@pytest.mark.parametrize("key,value", [("producer","unknown"), ("version","master"),
    ("field","RF/FORC"), ("semantics","SPC_REACTION"), ("model_sha256","wrong"),
    ("element_forces_sha256","wrong"), ("extra",float("nan"))])
def test_dishonest_or_unsupported_provenance_refused(coupled, key, value):
    record = provenance(coupled)
    record[key] = value
    with pytest.raises(audit.EquationForceAuditError):
        run(coupled, record)


@pytest.mark.parametrize("kind", ["no-review", "master-review", "no-binary-correspondence"])
def test_pinned_rf_cannot_be_admitted_by_version_label(coupled, kind):
    record = provenance(coupled)
    record.update(producer="CalculiX", version="2.23", field="RF/FORC", executable_sha256=audit.CCX_SHA256)
    if kind != "no-review":
        record["independent_semantics_confirmation"] = dict(status="CONFIRMED_BY_INDEPENDENT_REVIEW",
            version="master" if kind == "master-review" else "2.23", executable_sha256=audit.CCX_SHA256,
            semantics=audit.SEMANTICS)
    with pytest.raises(audit.EquationForceAuditError):
        run(coupled, record)


def test_output_and_input_mutations_are_detached(coupled):
    record = provenance(coupled)
    original = copy.deepcopy(coupled)
    result = run(coupled, record)
    assert coupled == original
    record["producer"] = "changed"
    coupled["coordinates"][1][0] = 99.
    assert result["provenance"]["producer"] == "synthetic"
    result["equation_actions_n"]["1"][0] = 99.
    assert coupled["element_forces"][1][0] == 4.


def test_input_identity_rejects_post_binding_mutation(coupled):
    record = provenance(coupled)
    coupled["element_forces"][1][0] += .01
    with pytest.raises(audit.EquationForceAuditError, match="identities"):
        run(coupled, record)


@pytest.mark.parametrize("kind", ["moment-overflow", "force-sum-overflow", "dependent-subtraction-overflow"])
def test_finite_extreme_inputs_refuse_intermediate_overflow(coupled, kind):
    if kind == "moment-overflow":
        coupled["coordinates"][1][1] = 1e308
        coupled["element_forces"][1][2] = 1e308
    elif kind == "force-sum-overflow":
        for node in coupled["element_forces"]:
            coupled["element_forces"][node][2] = 1e308
    else:
        coupled["element_forces"][1][0] = 1e308
        coupled["applied_forces"][1][0] = -1e308
    with pytest.raises(audit.EquationForceAuditError, match="finite"):
        run(coupled)


@pytest.fixture
def complete_output():
    from scripts import r8_e03_curved_reference as reference
    case = reference.build_case(0, 1)
    deck, metadata = reference.build_deck(case)
    modified, prepared = audit.prepare_complete_force_output(deck, metadata)
    return case, deck, metadata, modified, prepared


def synthetic_frd(metadata, *, force_nodes=None):
    # Synthetic binary fixture only: exact DOUBLE framing with zero U/g.
    nodes = metadata["physical_nodes"]
    elements = metadata["elements"]
    force_nodes = list(nodes) if force_nodes is None else force_nodes
    pieces = [b"1C\n1UPGM               CalculiX\n1UVERSION           Version 2.23\n",
        f"2C {len(nodes)} 3\n".encode()]
    pieces.extend(struct.pack("<i3d", node, *point) for node, point in nodes.items())
    pieces.append(f"3C {len(elements)} 2\n".encode())
    order = tuple(range(12))+tuple(range(16,20))+tuple(range(12,16))
    pieces.extend(struct.pack("<24i", element, 4, 0, 1, *(ids[j] for j in order)) for element, ids in elements.items())
    for step, name, component, selected in ((1,"DISP","D",list(nodes)), (2,"FORC","F",force_nodes)):
        pieces.append((f"1PSTEP {step} 1 1\n100CL 101 1.000000000 {len(selected)} 0 1 3\n"
            f"-4 {name} 4 1\n").encode())
        pieces.extend(f"-5 {component}{j} 1 2 {j} 0\n".encode() for j in range(1,4))
        pieces.append(b"-5 ALL 1 2 0 0 1ALL\n")
        pieces.extend(struct.pack("<i3d", node, 0., 0., 0.) for node in selected)
    pieces.append(b"9999\n")
    return b"".join(pieces)


def fictional_confirmed_record(case, metadata):
    # Entirely fictional control record; this is not review/build evidence.
    inputs = audit.e03_inputs(case, metadata)
    identity = audit.input_identity(**inputs, element_forces={node:[0.,0.,0.] for node in inputs["coordinates"]})
    return dict(producer="CalculiX", version="2.23", field="RF/FORC", semantics=audit.SEMANTICS,
        executable_sha256=audit.CCX_SHA256, **identity,
        independent_semantics_confirmation=dict(status="CONFIRMED_BY_INDEPENDENT_REVIEW", version="2.23",
            executable_sha256=audit.CCX_SHA256, semantics=audit.SEMANTICS,
            runtime_binary_correspondence="INDEPENDENTLY_CONFIRMED", exact_release_source_sha256="1"*64,
            source_files_sha256=audit.CCX_SOURCE_FILES_SHA256,
            correspondence_method="independent_analytic_spc_mpc_observable_control", control_evidence_sha256="3"*64,
            evidence_sha256="2"*64, review_id="fictional-synthetic-control", independent_reviewer_id="fictional",
            evidence_reference="synthetic fixture; not acceptance evidence"))


def test_output_change_is_exactly_one_card_and_metadata_detached(complete_output):
    case, deck, original, modified, prepared = complete_output
    old = b"*NODE OUTPUT,DOUBLE,NSET=ROOT\nRF\n"
    new = b"*NODE OUTPUT,DOUBLE,NSET=PHYSICAL\nRF\n"
    assert modified.replace(new, old, 1) == deck.encode("ascii")
    assert modified.count(new) == 1 and old not in modified
    assert len(prepared["force_output_nodes"]) == 333 and len(prepared["physical_support_nodes"]) == 49
    assert len(original["root_nodes"]) == 49
    prepared["original_metadata"]["root_nodes"].clear()
    assert len(original["root_nodes"]) == 49


@pytest.mark.parametrize("kind", ["changed-load", "missing-card", "duplicate-card"])
def test_output_preparation_refuses_changed_original(complete_output, kind):
    _, deck, metadata, _, _ = complete_output
    if kind == "changed-load":
        deck = deck.replace("*CLOAD", "*CLOAD,OP=NEW", 1)
    elif kind == "missing-card":
        deck = deck.replace("NSET=ROOT\nRF", "NSET=PHYSICAL\nRF")
    else:
        deck += "*NODE OUTPUT,DOUBLE,NSET=ROOT\nRF\n"
    with pytest.raises(audit.EquationForceAuditError):
        audit.prepare_complete_force_output(deck, metadata)


def test_strict_saved_output_projection_retains_real_supports(complete_output):
    case, _, metadata, _, prepared = complete_output
    original = copy.deepcopy(prepared)
    result = audit.audit_saved_complete_force_output(case, prepared, synthetic_frd(metadata),
        provenance=fictional_confirmed_record(case, metadata))
    assert prepared == original
    assert result["saved_output"]["output_nodes"] == 333
    assert result["saved_output"]["physical_support_nodes"] == 49
    assert not result["e03_accepted"] and result["free_residual_max_abs_n"] > 0


def test_saved_support_only_forces_are_refused(complete_output):
    from scripts.r8_e02_rigid_tip_reference import ReferenceParseError
    case, _, metadata, _, prepared = complete_output
    with pytest.raises(ReferenceParseError):
        audit.audit_saved_complete_force_output(case, prepared,
            synthetic_frd(metadata, force_nodes=metadata["root_nodes"]),
            provenance=fictional_confirmed_record(case, metadata))


@pytest.mark.parametrize("kind", ["supports", "output-inventory", "output-deck-sha"])
def test_saved_output_metadata_mutation_refused(complete_output, kind):
    case, _, metadata, _, prepared = complete_output
    if kind == "supports":
        prepared["physical_support_nodes"] = prepared["force_output_nodes"]
    elif kind == "output-inventory":
        prepared["force_output_nodes"].pop()
    else:
        prepared["output_deck_sha256"] = "wrong"
    with pytest.raises(audit.EquationForceAuditError):
        audit.audit_saved_complete_force_output(case, prepared, synthetic_frd(metadata),
            provenance=fictional_confirmed_record(case, metadata))


def test_saved_artifact_rejects_synthetic_producer_before_reader(complete_output):
    case, _, metadata, _, prepared = complete_output
    inputs = audit.e03_inputs(case, metadata)
    inputs["element_forces"] = {node:[0.,0.,0.] for node in inputs["coordinates"]}
    with pytest.raises(audit.EquationForceAuditError, match="CalculiX provenance"):
        audit.audit_saved_complete_force_output(case, prepared, b"not read", provenance=provenance(inputs))


@pytest.mark.parametrize("kind", ["missing-method", "missing-control-evidence", "foreign-source-file"])
def test_source_label_alone_does_not_confirm_actual_binary(complete_output, kind):
    case, _, metadata, _, prepared = complete_output
    record = fictional_confirmed_record(case, metadata)
    review = record["independent_semantics_confirmation"]
    if kind == "missing-method":
        del review["correspondence_method"]
    elif kind == "missing-control-evidence":
        del review["control_evidence_sha256"]
    else:
        review["source_files_sha256"] = {"resultsforc.c":"master"}
    with pytest.raises(audit.EquationForceAuditError):
        audit.audit_saved_complete_force_output(case, prepared, b"not read", provenance=record)
