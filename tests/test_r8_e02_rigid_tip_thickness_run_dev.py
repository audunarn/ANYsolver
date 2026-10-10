"""Source-only controls for the one-use E02 thickness supervisor."""

import copy

import pytest

from scripts import r8_e02_rigid_tip_thickness_run_dev as run


def test_prepared_thickness_inputs_match_archived_physics():
    old, metadata, execution = run.source_inputs()
    assert old["deck_sha256"] == run.EXPECTED[2]
    assert execution["exit_code"] == 0
    assert execution["elapsed_seconds"] > 0
    original_xy = {(p[0], p[1]) for p in metadata["physical_nodes"].values()}
    for nz in (4, 8):
        deck, variant = run.deck_inputs(metadata, nz)
        assert run.sha(deck) == run.EXPECTED[nz]
        assert {(p[0], p[1]) for p in variant["physical_nodes"].values()} == original_xy
        for name in ("patch", "root"):
            old_xy = {(metadata["physical_nodes"][n][0], metadata["physical_nodes"][n][1])
                      for n in metadata[name + "_nodes"]}
            new_xy = {(variant["physical_nodes"][n][0], variant["physical_nodes"][n][1])
                      for n in variant[name + "_nodes"]}
            assert new_xy == old_xy
        assert {p[2] for p in variant["physical_nodes"].values()} >= {-.01, .01}


def test_complete_physical_screen_refuses_missing_work_and_bad_mapping():
    old, _, _ = run.source_inputs()
    assert run.physical_checks(old)["complete_sections"]
    missing_work = copy.deepcopy(old)
    missing_work["conjugate_external_work_J"] = 0
    with pytest.raises(ValueError, match="work"):
        run.physical_checks(missing_work)
    bad_mapping = copy.deepcopy(old)
    bad_mapping["rigid_mapping"]["patch"]["max_gap_beyond_printed_rounding_m"] = 1e-9
    with pytest.raises(ValueError, match="mapping"):
        run.physical_checks(bad_mapping)
