"""Inert deck checks for the separately identified CalculiX knot diagnostic."""

import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import generate_b3_e4_ccx_3d_footprint_feasibility as base
import generate_b3_e4_ccx_3d_knot_patch as knot
import generate_b3_e4_ccx_3d_reciprocity_influences as old


def test_knot_patch_changes_only_sections_and_rigid_support_field():
    original = base.build_deck(1, "force_y")
    deck = knot.build_knot_rigid_x_deck()
    assert deck.count("*ELEMENT,TYPE=B31") == 2
    assert deck.count("*BEAM SECTION") == 2
    assert deck.count("*EQUATION\n") == 12
    assert "*CLOAD" not in deck
    assert deck.index("*STEP") < deck.index("*BOUNDARY")
    assert "33,46,47" in deck and "34,47,48" in deck
    expected = old.support_motion("shell",3,old.DELTA)
    expected[(old.BEAM_ROOT,2)] = -base.ECCENTRICITY*old.DELTA
    expected[(old.BEAM_ROOT,4)] = old.DELTA
    rows = [line.split(",") for line in deck.split("*BOUNDARY\n",1)[1]
            .split("*NODE PRINT",1)[0].splitlines()]
    assert len(rows) == len(expected) == 36
    assert {(int(a),int(b)) for a,b,c,d in rows} == set(expected)
    for a,b,c,d in rows:
        assert b == c and len(d) <= 20
        assert float(d) == pytest.approx(expected[(int(a),int(b))],rel=0,abs=1e-16)
    # Its support coordinates are a rigid rotation about the global origin.
    for node, xyz in old.support_coordinates().items():
        displacement = (0.,-xyz[2]*old.DELTA,xyz[1]*old.DELTA)
        for direction in range(3):
            if (node,direction+1) in expected:
                assert expected[(node,direction+1)] == pytest.approx(
                    displacement[direction],rel=0,abs=1e-16)
    assert expected[(46,4)] == old.DELTA
    # Recover the original card inventory exactly; no unnoticed model edit.
    reconstructed = deck.replace(
        "*ELEMENT,TYPE=B31,ELSET=BeamA\n33,46,47\n"
        "*ELEMENT,TYPE=B31,ELSET=BeamB\n34,47,48\n",
        "*ELEMENT,TYPE=B31,ELSET=Beam\n33,46,47\n34,47,48\n")
    section = base._number(base.BEAM_WIDTH)+","+base._number(base.BEAM_WIDTH)
    reconstructed = reconstructed.replace(
        "*BEAM SECTION,ELSET=BeamA,MATERIAL=Isotropic,SECTION=RECT\n"
        f"{section}\n0,1,0\n"
        "*BEAM SECTION,ELSET=BeamB,MATERIAL=Isotropic,SECTION=RECT\n"
        f"{section}\n0,0,1\n",
        "*BEAM SECTION,ELSET=Beam,MATERIAL=Isotropic,SECTION=RECT\n"
        f"{section}\n0,1,0\n")
    boundary = "\n".join(",".join(row) for row in rows)+"\n"
    reconstructed = reconstructed.replace("*STATIC\n*BOUNDARY\n"+boundary,
                                          "*STATIC\n*CLOAD\n48,2,1000\n")
    reconstructed = reconstructed.replace("*NSET,NSET=BeamRoot\n46\n",
                                          "*NSET,NSET=BeamRoot\n46\n"
                                          "*BOUNDARY\nPanelEnds,1,3\nBeamRoot,1,6\n")
    assert reconstructed == original
    assert hashlib.sha256(deck.encode("ascii")).hexdigest() == (
        "a599b9db8f6ba77a0a3c0e67620986aa46d1e2828c36c27664b1322344e3ca59")


@pytest.mark.parametrize("component", range(6))
@pytest.mark.parametrize("sign",(-1,1))
def test_all_rigid_support_modes_have_reference_spatial_field(component,sign):
    delta=sign*old.DELTA
    deck=knot.build_knot_rigid_deck(component,delta)
    rows=[line.split(",") for line in deck.split("*BOUNDARY\n",1)[1]
          .split("*NODE PRINT",1)[0].splitlines()]
    assert len(rows)==36
    values={(int(a),int(b)):float(d) for a,b,c,d in rows}
    assert len(values)==36
    assert all(b==c and len(d)<=20 for a,b,c,d in rows)
    assert deck.count("*BEAM SECTION")==2 and deck.count("*EQUATION\n")==12
    assert "*CLOAD" not in deck
    for node,xyz in old.support_coordinates().items():
        if component<3:
            u=tuple(delta*float(i==component) for i in range(3))
        else:
            axis=tuple(float(i==component-3) for i in range(3))
            u=tuple(delta*x for x in old._cross(axis,xyz))
        for direction in range(3):
            if (node,direction+1) in values:
                assert values[node,direction+1]==pytest.approx(u[direction],rel=0,abs=1e-16)
        if node==old.BEAM_ROOT:
            for direction in range(3,6):
                expected=delta if direction==component else 0.
                assert values[node,direction+1]==pytest.approx(expected,rel=0,abs=1e-16)
