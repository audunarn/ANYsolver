"""Refusal controls for the source-only detached E01 port admission."""

import json
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import b3_e4_e01_native_point_refinement_screen as native
from scripts import r8_e01_resolved_port_reference_dev as reference
from scripts.r8_e01_resolved_port_admission_dev import (
    SourceRefusal, _native_declared_tip_load, _records, audit, native_definition_controls,
    refuse_sided_claim, section_and_output_decision, source_controls,
    square_st_venant_j,
)


def _check(deck, info, sign=1, load="fy"):
    return source_controls(deck, info, sign, load)


def test_four_source_cases_pass_but_physical_admission_refused():
    result = audit()
    assert result["source_controls"] == "PASS"
    assert {(x["sign"], x["load"]) for x in result["cases"]} == {
        (1, "fy"), (1, "mx"), (-1, "fy"), (-1, "mx")}
    assert all(x["equations"] == 18 and x["complete_oriented_cuts"] == 8
               for x in result["cases"])
    assert not result["section_and_output"]["physical_admission"]
    assert not result["section_and_output"]["sided_action_admission"]
    assert result["numerical_children"] == 0


@pytest.mark.parametrize("sign", (1, -1))
def test_signed_row_and_six_work_fields(sign):
    deck, info = reference.build(sign, "fy")
    assert _check(deck, info, sign)["status"] == "SOURCE_CONTROLS_PASS"
    sr, rot = info["port_reference_nodes"]["shell_1000"]
    old = f"{rot},2,{-sign*.1:.17g}"
    new = f"{rot},2,{sign*.1:.17g}"
    assert old in deck
    with pytest.raises(SourceRefusal, match="signed six-row"):
        _check(deck.replace(old, new, 1), info, sign)


def test_wrong_station_and_root_refused():
    deck, info = reference.build(1, "fy")
    ref, _ = info["port_reference_nodes"]["beam_1000"]
    old = f"{ref},1,-0.5,0.10000000000000001"
    assert old in deck
    with pytest.raises(SourceRefusal, match="port station/frame"):
        _check(deck.replace(old, old.replace("1,-0.5", "1.01,-0.5"), 1), info)
    with pytest.raises(SourceRefusal, match="root constraint"):
        _check(deck.replace("PlateRootFree,1,3", "PlateRootFree,1,2", 1), info)


def test_wrong_tip_load_and_material_refused():
    deck, info = reference.build(1, "fy")
    tip, _ = info["port_reference_nodes"]["beam_2000"]
    with pytest.raises(SourceRefusal, match="tip load"):
        _check(deck.replace(f"{tip},2,1000", f"{tip},1,1000", 1), info)
    material = f"{reference.E:.17g},{reference.NU:.17g}"
    with pytest.raises(SourceRefusal, match="material"):
        _check(deck.replace(material, f"{reference.E:.17g},0.29", 1), info)
    with pytest.raises(SourceRefusal, match="material"):
        _check(deck.replace("*SOLID SECTION,ELSET=BeamSolid,MATERIAL=Isotropic",
                            "*SOLID SECTION,ELSET=BeamSolid,MATERIAL=Other", 1), info)


def test_missing_or_reversed_constituent_cut_refused():
    deck, info = reference.build(1, "fy")
    model = _records(deck)
    entry = model["surfaces"]["Plate1000LeftCut"][0]
    marker = "*SURFACE,NAME=Plate1000LeftCut,TYPE=ELEMENT\n"
    before, after = deck.split(marker, 1)
    assert after.startswith(f"{entry[0]},S4\n")
    with pytest.raises(SourceRefusal, match="wrong cut side"):
        _check(before+marker+after.replace(f"{entry[0]},S4\n",
                                            f"{entry[0]},S6\n", 1), info)
    with pytest.raises(SourceRefusal, match="incomplete cut"):
        _check(before+marker+after.replace(f"{entry[0]},S4\n", "", 1), info)


def test_missing_output_and_cancelled_pair_claim_refused():
    deck, info = reference.build(1, "fy")
    with pytest.raises(SourceRefusal, match="missing cut output"):
        _check(deck.replace("*SECTION PRINT,SURFACE=Beam1000RightCut,NAME=Beam1000RightCut\nSOF\n",
                            "", 1), info)
    for basis in ("adjacent SOF pair cancels", "rounded FRD displacement weak force"):
        with pytest.raises(SourceRefusal, match="independent sided"):
            refuse_sided_claim(basis)


def test_native_section_and_frame_are_bound_to_current_definition(monkeypatch):
    assert native_definition_controls(-1)["beam_tip_node"] == 105
    original = native.definition

    def changed(intervals, sign):
        model, tip = original(intervals, sign)
        beam = model.beams[0]
        data = json.loads(beam.raw)
        data["section"]["elastic"][3][3] *= 1.01
        altered = SimpleNamespace(raw=json.dumps(data).encode("ascii"))
        return SimpleNamespace(shell=model.shell, points=model.points,
                               fixed=model.fixed, beams=(altered, model.beams[1])), tip

    monkeypatch.setattr(native, "definition", changed)
    with pytest.raises(SourceRefusal, match="native six-resultant section drift"):
        native_definition_controls(1)


def _wrong_native_solve():
    return NodalAction("beam", tip_node, (0., 1000., 0., 0., 0., 0.))


def test_native_tip_load_mutation_refused(monkeypatch):
    monkeypatch.setattr(native, "solve", _wrong_native_solve)
    with pytest.raises(SourceRefusal, match="native tip action measure"):
        _native_declared_tip_load()


def test_square_torsion_is_not_polar_and_shear_remains_unmeasured():
    d = section_and_output_decision()
    assert np.isclose(d["solid_geometry"]["polar_J_m4"], 1.6666666666666667e-5)
    assert np.isclose(square_st_venant_j(.1), 1.4057701497e-5, rtol=1e-9)
    assert .84 < d["solid_geometry"]["Saint_Venant_to_native_J_ratio"] < .85
    assert d["solid_geometry"]["effective_shear_area_m2"] == "unverified"
    assert not d["physical_admission"]
