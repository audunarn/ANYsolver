"""Bind certified comparisons to manufactured recovery; no equilibrium."""
from fractions import Fraction as F

import pytest

from scripts import _b3_e4_f03_action_enclosure as bound
from scripts import _b3_e4_f03_local_grid as grid
from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_local_recovery as rec
from scripts import _b3_e4_f03_spatial_contract as c

RB=rec.RecoveryBudget(assembly.AssemblyBudget(512,1,128*1024**2,8_000_000),
                     1024,128,8_000_000,256*1024**2,1_000_000_000)
AB=bound.ActionBudget(64,128,65536,200_000_000,2_000_000,256*1024**2)
BANDS=((F(0),F(1,4)),(F(1,4),F(1,2)),(F(1,2),F(3,4)),(F(3,4),F(1)),
       (F(0),F(1,32)),(F(1,32),F(1,16)),(F(15,16),F(31,32)),(F(31,32),F(1)))


@pytest.fixture(scope='module')
def manufactured():
    g=grid.compile_grid((F(-1,2),F(1,2),F(3,2)),(F(-1,2),F(0),F(1,2)),1)
    q=(F(1,10**6),)+(F(0),)*(g.free_dofs-1)
    value=rec.recover(g,q,(F(7),F(-11),F(13)),RB)
    return g,value


def test_all_fixed_band_saved_values_receive_certified_comparisons(manufactured):
    _,value=manufactured
    assert value.support_lift_actions is None
    actions=tuple(a for left,right in BANDS for a in rec.band(value,left,right))
    for action in actions:
        saved=float(action.decimal_value())
        result=bound.compare_saved(action,saved,c.F0,1e-10,budget=AB)
        assert result['status']=='PASSED'
        assert result['enclosure']['work']['quadrature_evaluations']==0
    action=actions[0];bad=float(action.decimal_value())+1.
    assert bound.compare_saved(action,bad,c.F0,1e-10,budget=AB)['status']=='FAILED'


def test_support_identities_do_not_hide_nonzero_admissible_shift(manufactured):
    from scripts import _b3_e4_f03_local_support_recovery as support
    g,value=manufactured
    sb=support.SupportBudget(RB,1024,128,1_000_000_000,80_000_000,512*1024**2)
    result=support.support_recovery(g,value,sb)
    assert value.support_lift_actions is None
    assert result.lift_family=='Q1_EDGE_ROTATION'
    for action in (*result.route_difference,*result.shift_binding_defects,
                   *result.force_balance_actual,result.represented_moment_identity):
        assert bound.compare_saved(action,0.,c.F0,1e-8,budget=AB)['status']=='PASSED'
    # Two correct work routes and global identities cannot establish equilibrium.
    assert bound.compare_saved(result.first_free_route1_residual,0.,c.F0,1e-8,
                               budget=AB)['status']=='FAILED'
    for action in result.route1:
        saved=float(action.decimal_value())
        assert bound.compare_saved(action,saved,c.F0,1e-8,budget=AB)['status']=='PASSED'
    force_difference=bound.enclose(result.load_actual_minus_nominal[0],budget=AB)
    assert force_difference['upper']<0
    physical=bound.enclose(result.physical_moment_defect,budget=AB)
    assert physical['lower']==physical['upper']!=0
    assert result.diagnostics['equilibrium_solves']==0
