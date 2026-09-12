"""Registered authentic five-family smoke; reviewed bounded runner only."""
from hashlib import sha256
import json
import numpy as np
import pytest

import ge_beam3_g3c_history_owner as history

GRAPHS = ('J_B2_PAIR','J_B3_PAIR','J_Q4_PAIR','J_S3_PAIR','J_MULTIFAMILY_LOOP')


def command(stage):
    return dict(kind='LOAD_STAGE',root_stage=stage,load_factor=(0.,.5,1.,.25,0.)[stage],force_scale=.01)


def native_stage(previous, current, graph):
    old={r['element_id']:r['payload'] for r in previous['native_rows']}
    points={n:np.asarray(x) for n,x in graph['nodes']}
    elements={e['id']:e for e in graph['elements']}
    for row in current['native_rows']:
        payload=row['payload']; response=payload['response']
        assert payload['epoch']==current['epoch']
        assert payload['previous_state_sha256']==old[row['element_id']]['state_sha256']
        J=np.asarray(response['full']['jacobian']); r=np.asarray(response['full']['residual'])
        assert J.shape==(42,42) and r.shape==(42,)
        nodes=elements[row['element_id']]['nodes']
        length=np.linalg.norm(points[nodes[-1]]-points[nodes[0]])
        scale=np.r_[np.full(12,length),np.ones(12)]
        assert response['internal_error']<=1e-11 and np.linalg.norm(r[18:]/scale)<=1e-11
        lift=-np.linalg.solve(J[18:,18:],J[18:,:18])
        correction=-np.linalg.solve(J[18:,18:],r[18:])
        for actual,expected in ((response['lift'],lift),(response['correction'],correction),
                (response['tangent'],J[:18,:18]+J[:18,18:]@lift),
                (response['residual'],r[:18]+J[:18,18:]@correction)):
            actual=np.asarray(actual)
            assert np.linalg.norm(actual-expected)<=1e-11*max(1.,np.linalg.norm(expected))


@pytest.mark.parametrize('fixture',GRAPHS,ids=GRAPHS)
def test_family_two_stage_smoke(fixture):
    owner=history.HistoryOwner(fixture)
    _, source=history.packet.authorities()
    graph=source.expand(fixture)[1]['graph']
    before=json.loads(owner.checkpoint_bytes())['final_state']
    for stage in range(2):
        result=owner.solve(command(stage))
        raw=owner.checkpoint_bytes(); current=json.loads(raw)['final_state']
        assert result['epoch']==stage+1 and np.linalg.norm(result['residual'])<=1e-11
        assert current['previous_sha256']==history.packet.digest(before)
        native_stage(before,current,graph)
        # Actual next-origin validation in a real discarded same-pose trial.
        diagnostic=json.loads(owner.accepted_pose_diagnostic_bytes())
        assert diagnostic['state_committed'] is False
        assert diagnostic['origin_sha256']==history.packet.digest(current)
        assert np.linalg.norm(diagnostic['residual'])<=1e-11
        assert owner.checkpoint_bytes()==raw
        history.packet.preflight(raw,sha256(raw).hexdigest(),expected_runtime_sha256=history.runtime_identity())
        before=current


@pytest.mark.parametrize('prefix',(0,1,2),ids=('prefix0','prefix1','prefix2'))
def test_b2_authentic_prefix_replay_and_continuation(prefix):
    original=history.HistoryOwner('J_B2_PAIR'); checkpoints=[original.checkpoint_bytes()]
    for stage in range(2):
        original.solve(command(stage)); checkpoints.append(original.checkpoint_bytes())
    raw=checkpoints[prefix]
    restored=history.resume(raw,sha256(raw).hexdigest(),expected_runtime_sha256=history.runtime_identity())
    assert restored.checkpoint_bytes()==raw
    for stage in range(prefix,2): restored.solve(command(stage))
    assert restored.checkpoint_bytes()==checkpoints[-1]
