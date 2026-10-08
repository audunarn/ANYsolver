"""Small deck-contract checks for the BL5 development external comparison."""
import json

import numpy as np
import pytest

from scripts import r8_bl5_ccx_weak_p0_dev as reference


@pytest.mark.parametrize("case,expected",[("fy",(0.,100.,0.,0.,0.,0.)),
                                         ("mx",(0.,0.,0.,10.,0.,0.))])
def test_weak_deck_has_unique_ccx_pivots_and_declared_wrench(case,expected):
    data,metadata=reference.deck(case)
    assert json.loads(json.dumps(metadata,allow_nan=False))["case"]==case
    assert metadata["equation_check"]["physical_rows"]==20
    assert metadata["equation_check"]["pivot_error"]==0.
    assert metadata["equation_check"]["row_relative_error"]<1e-11
    lines=data.decode("ascii").splitlines()
    equations=[]
    for i,line in enumerate(lines):
        if line!="*EQUATION":
            continue
        count=int(lines[i+1]); tokens=[]; j=i+2
        while len(tokens)<3*count:
            tokens.extend(lines[j].split(",")); j+=1
        assert len(tokens)==3*count
        equations.append([(int(tokens[3*k]),int(tokens[3*k+1]),
                           float(tokens[3*k+2])) for k in range(count)])
    assert len(equations)==20
    pivots=[tuple(pair) for pair in metadata["dependent_pivots"]]
    assert len(set(pivots))==20
    for row,pivot in zip(equations,pivots):
        assert row[0]==(*pivot,1.)
        assert all((node,axis) not in pivots for node,axis,_ in row[1:])
    observed=np.r_[metadata["tip_load_check"]["force_N"],
                    metadata["tip_load_check"]["moment_about_beam_tip_Nm"]]
    assert np.allclose(observed,expected,rtol=0.,atol=1e-10)


def test_weak_deck_rejects_undeclared_load():
    with pytest.raises(ValueError,match="admitted Fy or Mx"):
        reference.deck("follower")
