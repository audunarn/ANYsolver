"""Failure-only detached witness retention; no research wave execution."""

from dataclasses import asdict

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_displacement_control_probe import (
    DisplacementControlledAssemblyProbe, DisplacementControlError, ControlObservationError,
)
from docs.reference_cases.ge_beam3_curved_p5_arch_refinement_case import make_beam
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_refinement_wave import canonical


def driver():
    model, _ = make_beam(2)
    return DisplacementControlledAssemblyProbe(model, node=2)


def test_failure_snapshot_matches_actual_last_evaluation_and_is_not_committed():
    d=driver();before=digest(d.committed_model.committed);saved=[]
    with pytest.raises(DisplacementControlError):
        d.trial(.095,max_iterations=0,failure_observer=saved.append)
    assert len(saved)==1 and d._pending is None
    assert digest(d.committed_model.committed)==before
    raw=saved[0];model=d.committed_model
    actual=model.response_at(raw['positions'],raw['rotations'])
    assert digest(raw['response'])==digest(actual)
    assert raw['schema']=='GE_BEAM3_P5_FAILED_LAST_EVALUATION_V1'
    assert raw['disposition']=='UNCOMMITTED_DIAGNOSTIC_ONLY'
    assert raw['origin_epoch']==0 and raw['target']==.095
    assert model._norm(actual.residual-model._external(raw['forces']),raw['forces'])==raw['residual_norm']


def test_mutating_failure_snapshot_cannot_change_checkpoint():
    d=driver();before=digest(d.committed_model.committed)
    def sink(raw):
        raw['positions'].setflags(write=True);raw['positions'][:]=99
        raw['response'].residual.setflags(write=True);raw['response'].residual[:]=99
    with pytest.raises(DisplacementControlError):d.trial(.095,max_iterations=0,failure_observer=sink)
    assert digest(d.committed_model.committed)==before and d._pending is None


def test_success_does_not_emit_snapshot_or_change_bytes():
    saved=[];a=driver().trial(.095);b=driver().trial(.095,failure_observer=saved.append)
    assert not saved and canonical(asdict(a))==canonical(asdict(b))


def test_sink_failure_blocks_publication_and_no_initial_evaluation_fabricates_nothing():
    d=driver();before=digest(d.committed_model.committed)
    def deny(raw):raise OSError('disk unavailable')
    with pytest.raises(ControlObservationError):d.trial(.095,max_iterations=0,failure_observer=deny)
    assert digest(d.committed_model.committed)==before and d._pending is None
    saved=[]
    with pytest.raises(DisplacementControlError):d.trial(.095,max_mixed_evaluations=0,failure_observer=saved.append)
    assert not saved
    with pytest.raises(ValueError):driver().trial(.095,failure_observer=1)
