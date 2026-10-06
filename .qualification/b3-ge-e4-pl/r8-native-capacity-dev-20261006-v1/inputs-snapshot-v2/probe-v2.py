"""Verify the actual failed-screen accepted prefix; never rerun its loading."""
from copy import deepcopy
from hashlib import sha256
import json
import numpy as np
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken, SolveCancelled
from examples import stiffened_shell_native_capacity as case

def save(folder,name,value):
    (folder/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def compare(actual,expected,path='recovery'):
    if isinstance(expected,dict):
        assert actual.keys()==expected.keys(),path
        for key in expected: compare(actual[key],expected[key],path+'.'+key)
    elif isinstance(expected,list):
        assert len(actual)==len(expected),path
        for i,(a,b) in enumerate(zip(actual,expected)): compare(a,b,path+f'[{i}]')
    elif isinstance(expected,(int,float)) and not isinstance(expected,bool):
        np.testing.assert_allclose(actual,expected,rtol=1e-10,atol=1e-12,err_msg=path)
    else:
        assert actual==expected,path

def run(folder):
    original=folder.parent/'installed-v1'
    report=json.loads((original/'screen-result.json').read_text())
    assert report['status']=='typed_failure' and report['failure']['phase']=='seed'
    observations=report['observations']
    assert len(observations)==3 and [o['state']['load_factor'] for o in observations]==[.1,.25,.5]
    entry=report['checkpoint_inventory'][-1]
    raw=(original/'checkpoint-0-g3.bin').read_bytes()
    assert len(raw)==entry['size_bytes'] and sha256(raw).hexdigest()==entry['sha256']
    seed=tuple(ss.NodalAction(row['domain'],row['node'],tuple(row['wrench'])) for row in report['seed_actions'])
    direction=tuple(ss.NodalAction(row['domain'],row['node'],tuple(row['wrench'])) for row in report['arc_direction'])
    specimen=case.Specimen()
    force_scale=1.12*specimen.estimate()['euler_clamped_free_n']
    rows=[]
    for observation in observations:
        state=observation['state']; wrench=np.asarray(observation['global_wrench_residual'])
        row=dict(generation=observation['generation'],equilibrium=state['free_equilibrium_ratio'],constraint=state['constraint_max'],force=float(np.linalg.norm(wrench[:3])/force_scale),moment=float(np.linalg.norm(wrench[3:])/(2*force_scale)))
        assert np.isfinite(list(row.values())).all()
        assert row['equilibrium']<=1e-8 and row['constraint']<=1e-9 and row['force']<=1e-8 and row['moment']<=1e-8
        rows.append(row)
    streamed=[json.loads(line) for line in (original/'accepted-observations.jsonl').read_text().splitlines()]
    assert streamed==observations
    save(folder,'accepted-mechanics.json',dict(force_scale_n=force_scale,moment_scale_nm=2*force_scale,observations=rows,rejected_attempt=report['failure']))
    owner=ss.create_analysis(definition=case.definition())
    bad=None
    checks=dict(checkpoint_sha256=sha256(raw).hexdigest(),generation=3,streamed_state_parity=True)
    try:
        owner.restore(raw)
        assert owner.checkpoint()==raw
        restored=case._plain(owner.recover())
        expected=deepcopy(observations[-1]['state'])
        # Reconstruction has zero solve iterations and explicit chart fields;
        # compare actual physical charts separately rather than their availability.
        operational=('iterations','shell_frames','shell_rotation_anchors','shell_chart_coordinates')
        checks['reconstruction_metadata']={key:dict(before=expected.pop(key),after=restored.pop(key)) for key in operational}
        compare(restored,expected)
        recovered=case.observe(owner.recover(),specimen,tuple(owner.preflight()['arc_metric_node_order']),seed_actions=seed,arc_direction=direction)
        for key in ('physical_positions_m','physical_applied_rows','shell_physical_frames','shell_chart_coordinates','shell_rotation_anchors','material_activity','applied_common_origin_wrench','root_common_origin_reaction_wrench'):
            compare(recovered[key],observations[-1][key],key)
        before=owner.checkpoint(); state_before=case._plain(owner.recover())
        token=CancellationToken(); token.cancel('before failed capacity seed continuation')
        try:
            owner.solve(seed,(.75,),cancellation_token=token)
        except SolveCancelled:
            pass
        else:
            raise AssertionError('pre-step cancellation did not propagate')
        assert owner.checkpoint()==before and case._plain(owner.recover())==state_before
        checks['precancel_complete_prefix_unchanged']=True
        damaged=bytearray(raw); damaged[-1]^=1
        bad=ss.create_analysis(definition=case.definition())
        try:
            bad.restore(bytes(damaged))
        except ValueError as error:
            checks['fresh_corrupt_refusal']=dict(type=type(error).__name__,message=str(error))
        else:
            raise AssertionError('corrupt checkpoint restored')
        try:
            bad.recover()
        except RuntimeError as error:
            assert 'no accepted' in str(error)
        else:
            raise AssertionError('failed fresh restore left accepted state')
        bad.restore(raw)
        assert bad.checkpoint()==raw and case._plain(bad.recover())==state_before
        checks['fresh_corrupt_atomicity_and_valid_restore']=True
        checks['snapshot_bytes_equal']=True
        checks['physical_recovery_equal_with_registered_tolerance']=True
        save(folder,'prefix-checks.json',checks)
    finally:
        owner.close()
        if bad is not None: bad.close()
    save(folder,'prefix-disposition.json',dict(status='ACCEPTED_PREFIX_VERIFIED',original_route='SEED_FAILED_NO_ARC',physical_route_retried=False,capacity_or_stability_proved=False,scientific_acceptance=False))
    return 0
