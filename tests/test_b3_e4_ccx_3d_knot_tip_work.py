"""Inert input contract for expanded-node B31 tip-work probe."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import generate_b3_e4_ccx_3d_knot_patch as knot
import generate_b3_e4_ccx_3d_knot_tip_work as work
import generate_b3_e4_ccx_3d_reciprocity_influences as old


@pytest.mark.parametrize("sign",(-1,1))
def test_only_root_y_motion_tip_load_and_expanded_output_are_added(sign):
    delta=sign*old.DELTA
    deck=work.build_tip_work_deck(delta)
    assert deck.count("*NODE FILE,OUTPUT=3D\nU\n")==1
    assert deck.count("*NODE PRINT,NSET=AllNodes\nU\nRF\n")==1
    assert deck.count("*EQUATION\n")==12
    assert deck.count("*CLOAD\n48,2,1000\n")==1
    support=deck.split("*BOUNDARY\n",1)[1].split("*CLOAD\n",1)[0]
    rows=[line.split(",") for line in support.splitlines()]
    expected=old.support_motion("beam",1,delta)
    assert len(rows)==len(expected)==36
    assert {(int(a),int(b)) for a,b,c,d in rows}==set(expected)
    assert all(b==c and len(d)<=20 and
               float(d)==expected[(int(a),int(b))] for a,b,c,d in rows)
    assert sum(float(d)!=0 for a,b,c,d in rows)==1
    assert f"46,2,2,{delta:.12g}" in support
    source=knot.build_knot_rigid_deck(1,delta)
    old_support=source.split("*BOUNDARY\n",1)[1].split("*NODE PRINT",1)[0]
    restored=deck.replace(support,old_support).replace(
        "*CLOAD\n48,2,1000\n","").replace(
        "*NODE FILE,OUTPUT=3D\nU\n","")
    assert restored==source


def test_rejects_unregistered_motion_amplitude():
    with pytest.raises(ValueError,match="frozen"):
        work.build_tip_work_deck(2*old.DELTA)
