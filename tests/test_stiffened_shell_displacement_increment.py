"""Signed cutback accounting and durable metadata consistency."""
import json
from copy import deepcopy
import pytest
from anysolver._stiffened_shell_displacement_increment import DisplacementIncrementState as State,DisplacementIncrementLimit
from anysolver._stiffened_shell_increment_control import AdaptiveIncrementControl


def record(state,accepted):
    return state.record(accepted,evaluations=3,linear_solves=1,rejected_trials=0)


def test_signed_cutback_restart_and_reversal():
    state=State(AdaptiveIncrementControl(2,12),(-2.,1.),-1.)
    assert state.next_target()==-2.
    state=record(state,False);assert state.next_target()==-1.5
    state=record(state,True);assert state.next_target()==-2.
    restored=State.from_payload(json.loads(json.dumps(state.payload())))
    assert restored==state
    state=record(restored,True);assert state.next_target()==1.
    state=record(state,False);assert state.next_target()==-.5
    state=record(state,True);assert state.next_target()==1.
    state=record(state,True);assert state.completed


def test_spent_budget_survives_restart():
    state=record(State(AdaptiveIncrementControl(0,1),(-2.,),-1.),False)
    restored=State.from_payload(state.payload())
    with pytest.raises(DisplacementIncrementLimit) as error:restored.next_target()
    assert error.value.state.attempts==state.attempts


@pytest.mark.parametrize("fault",("position","work","target","fields"))
def test_corrupt_attempt_rejected(fault):
    state=record(State(AdaptiveIncrementControl(),(-2.,),-1.),False)
    payload=deepcopy(state.payload());row=payload["attempts"][0]
    if fault=="position":row["accepted_from"]=0.
    if fault=="work":row["evaluations"]=-1
    if fault=="target":row["requested_target"]=-3.
    if fault=="fields":row["extra"]=1
    with pytest.raises(ValueError):State.from_payload(payload)


def test_domain_rejections_need_not_evaluate_residual():
    state=State(AdaptiveIncrementControl(),(-2.,),-1.)
    state=state.record(False,evaluations=1,linear_solves=1,rejected_trials=13)
    assert State.from_payload(state.payload())==state
