"""Source controls for the one-case signed-system development discriminator."""
import json
import numpy as np
import pytest

from scripts.r8_bl5_c2_signed_kkt_dev import guarded_run, prior_process_wall, relative, require
from scripts.b3_e4_bl5_coherent_aggregation_dev import model


def test_exact_matched_c2_policy_has_eight_complete_p0_supports():
    definition, policy = model(16,4,32,2)
    assert definition.lines[0].basis == 'p0'
    assert policy['span_halfcells'] == 4
    assert policy['support_membership'] == [list(range(4*i,4*i+4)) for i in range(8)]
    assert len(definition.fixed) == 35


def test_holds_unsupported_case_and_refuses_evidence_reuse(tmp_path):
    with pytest.raises(ValueError,match='unsupported'):
        require(False,'unsupported')
    assert relative(np.array([1.]),np.array([1.])) == 0.
    occupied=tmp_path/'occupied'
    occupied.mkdir()
    with pytest.raises(FileExistsError):
        guarded_run(occupied)


@pytest.mark.parametrize('numerical,source_control',[(12.,18.01),(75.,75.)])
def test_guard_refuses_insufficient_or_exhausted_shared_allowance(
        tmp_path,monkeypatch,numerical,source_control):
    attempt=tmp_path/'attempt1'
    attempt.mkdir()
    (attempt/'receipt.json').write_text(json.dumps({'process_wall_seconds':numerical}))
    (tmp_path/'source-receipt.json').write_text(
        json.dumps({'process_wall_seconds':source_control}))
    assert prior_process_wall(tmp_path)=={'numerical':numerical,'source_control':source_control}
    def unexpected_launch(*args,**kwargs):
        raise AssertionError('guard launched a process without allowance')
    monkeypatch.setattr('scripts.r8_bl5_c2_signed_kkt_dev.subprocess.Popen',unexpected_launch)
    new=tmp_path/'attempt2'
    with pytest.raises(ValueError,match='insufficient cumulative allowance'):
        guarded_run(new)
    assert not new.exists()


def test_guard_keeps_fixed_attempt_cap(tmp_path):
    with pytest.raises(ValueError,match='fixed 60s'):
        guarded_run(tmp_path/'attempt1',timeout=10.)
