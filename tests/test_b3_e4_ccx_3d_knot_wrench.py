"""Knot-based external reciprocity decks share one mechanical comparator."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import generate_b3_e4_ccx_3d_knot_wrench as wrench
import generate_b3_e4_ccx_3d_reciprocity_influences as old


def _inventory(deck):
    support=deck.split("*BOUNDARY\n",1)[1].split("*NODE PRINT",1)[0]
    if "*CLOAD\n" in support:
        support=support.split("*CLOAD\n",1)[0]
    rows=[line.split(",") for line in support.splitlines()]
    assert len(rows)==36
    assert all(b==c and len(d)<=20 for a,b,c,d in rows)
    return {(int(a),int(b)):float(d) for a,b,c,d in rows}


def _model_without_step_supports_and_load(deck):
    head,tail=deck.split("*BOUNDARY\n",1)
    body=tail.split("*NODE PRINT,NSET=AllNodes\n",1)[1]
    return head+"*NODE PRINT,NSET=AllNodes\n"+body


def test_loaded_baseline_has_same_knot_model_and_zero_supports():
    baseline=wrench.build_loaded_baseline()
    assert baseline.count("*CLOAD\n48,2,1000\n")==1
    assert set(_inventory(baseline))==set(old.support_motion("beam",0,old.DELTA))
    assert not any(_inventory(baseline).values())
    assert baseline.count("*EQUATION\n")==12
    assert baseline.count("*BEAM SECTION")==2
    assert baseline.count("*NODE FILE,OUTPUT=3D\nU\n")==1


@pytest.mark.parametrize("sign",(-1,1))
def test_tip_torque_keeps_exact_knot_footprint_and_support_model(sign):
    force=wrench.build_loaded_baseline()
    moment=wrench.build_loaded_tip_torque_x(sign)
    assert moment.count(f"*CLOAD\n48,4,{100*sign}\n")==1
    assert "*CLOAD\n48,2,1000\n" not in moment
    assert _inventory(moment)==_inventory(force)
    assert _model_without_step_supports_and_load(moment)==(
        _model_without_step_supports_and_load(force))
    assert moment.count("*EQUATION\n")==12
    assert moment.count("*BEAM SECTION")==2


def test_tip_torque_rejects_ambiguous_sign():
    with pytest.raises(ValueError,match="tip torque sign"):
        wrench.build_loaded_tip_torque_x(True)


@pytest.mark.parametrize("group",("shell","beam"))
@pytest.mark.parametrize("component",range(6))
@pytest.mark.parametrize("sign",(-1,1))
def test_each_unloaded_basis_has_exact_support_work_and_common_model(group,component,sign):
    delta=sign*old.DELTA
    deck=wrench.build_unloaded_influence(group,component,delta)
    assert _inventory(deck)==pytest.approx(old.support_motion(group,component,delta),
                                          rel=0,abs=1e-16)
    assert "*CLOAD" not in deck
    assert _model_without_step_supports_and_load(deck)==(
        _model_without_step_supports_and_load(wrench.build_loaded_baseline()))
    assert deck.count("*BEAM SECTION")==2 and deck.count("*EQUATION\n")==12
