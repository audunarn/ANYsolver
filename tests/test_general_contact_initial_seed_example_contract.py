"""Static public-example contract: model, route and seed wiring.

The end-to-end execution of the example (one real coupled half solve)
cannot fit this scope's remaining guard allowance: one half solve of
this fixture measures 167 s (default-none, attempt-05) and the seeded
run was still executing at the 180 s cap (attempt-06). This module
verifies the example's static public contract on the same immutable
snapshot instead: the built model/settings/program are the fixture's
D1 overlap-local route, the default-none selector keeps the legacy
shape, and the enabled selector is admitted by real validation on the
example's own model. No solve is executed and no trajectory claim is
made.
"""
import importlib.util
import os
from dataclasses import asdict, replace

from anysolver import validate_general_contact
from anysolver.general_contact.core import _contact_settings_contract

_EXAMPLE_NAME = "general_contact_initial_contact_seed_dev.py"


def _load_example():
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(repo, "examples", _EXAMPLE_NAME)
    assert os.path.isfile(path), path
    spec = importlib.util.spec_from_file_location(
        "initial_contact_seed_dev_example", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_example_builds_the_valid_d1_route_with_seed_wiring():
    example = _load_example()
    model, definition, settings, program = example.build_model()
    # The example's own settings carry the D1 reference-linear fine-Q1
    # monolithic Q4/S3 overlap-local route with the joint certificate.
    assert settings.initial_contact_seed == "none"
    assert settings.q4_source_gap_certificate == "overlap_local_dev"
    assert settings.q4_source_overlap_dual_dev is True
    assert settings.general_s3_differentiation == "jet2_q4_s3_dev"
    assert settings.enforcement_solver == "monolithic_active_set"
    assert settings.d1_interior_profile is True
    # Default-none keeps the exact legacy serialized contract shape.
    contract = _contact_settings_contract(settings)
    assert "initial_contact_seed" not in contract
    # The enabled selector is admitted by real validation on the
    # example's own model, program and settings.
    seeded = replace(settings, initial_contact_seed="linearized_kkt_dev")
    report = validate_general_contact(model, definition, seeded,
                                      analysis_control="contact_path")
    assert report.valid, report.issues
    enabled_contract = _contact_settings_contract(seeded)
    assert enabled_contract["initial_contact_seed"] == "linearized_kkt_dev"
    # The program is the fixture's two-step 0.04 N ramp with two
    # controls; the settings serialize the mandated route fields.
    record = asdict(seeded)
    assert record["complementarity_force_scale_n"] == 0.04
    assert program.steps_per_segment == 2
    assert len(program.controls) == 2
    assert len(program.nodal_forces) == 1
