import copy
import pytest
from scripts import r8_e03_force_observability_followup as followup

DAT = b''' displacements (vx,vy,vz) for set ALL and time  0.1000000E+01

1 .1 0 0
2 0 0 0
3 .1 0 0
4 .1 0 0

 forces (fx,fy,fz) for set ALL and time  0.1000000E+01

1 1 0 0
2 -1 0 0
3 0 0 0
4 0 0 0
'''
STA = b'SUMMARY OF JOB INFORMATION\n STEP INC ATT ITRS TOT TIME STEP TIME INC TIME\n 1 1 1 1 1.0 1.0 1.0\n'
STDOUT = b'CalculiX Version 2.23\nUsing up to 1 cpu(s) for solve\nJob finished\n'
COMMAND = ['pinned/ccx.exe', '-i', 'mpc-support-v3']


def receipt():
    raw = dict(dat=DAT, sta=STA, stdout=STDOUT, stderr=b'')
    return dict(exit_code=0, timed_out=False, executable_sha256=followup.audit.CCX_SHA256,
        deck_sha256='a'*64, command=copy.deepcopy(COMMAND),
        **{name+'_sha256':followup.sha(data) for name, data in raw.items()})


def test_independent_printed_oracle_and_detachment():
    source = receipt()
    result = followup.analytic_candidate(DAT, STA, STDOUT, b'', receipt=source, deck_sha256='a'*64, command=COMMAND)
    assert result['physical_multiplier'] == -1
    assert result['physical_spc_fx'] == [-1, -1]
    assert result['semantics_adopted'] is False and result['e03_accepted'] is False
    source['command'][0] = 'changed'
    assert result['receipt']['command'][0] == 'pinned/ccx.exe'


@pytest.mark.parametrize('bad', [DAT[:-8], DAT+DAT, DAT.replace(b'vx,vy,vz', b'ux,uy,uz'),
    DAT.replace(b'set ALL', b'set ROOT', 1), DAT.replace(b'0.1000000E+01', b'0.2000000E+01', 1),
    DAT.replace(b'2 0 0 0', b'1 0 0 0'), DAT.replace(b'1 1 0 0', b'1 nan 0 0'),
    DAT.replace(b'1 1 0 0', b'1 1 0'), DAT+b'extra\n', DAT.replace(b'4 .1 0 0', b'5 .1 0 0')])
def test_strict_dat_refusal(bad):
    with pytest.raises(followup.FollowupError):
        followup.read_analytic_dat(bad)


@pytest.mark.parametrize('sta,stdout,stderr', [(STA+STA, STDOUT, b''),
    (STA.replace(b'INFORMATION', b'CHANGED'), STDOUT, b''),
    (STA.replace(b'1.0 1.0 1.0', b'1.0 .5 .5'), STDOUT, b''),
    (STA, STDOUT.replace(b'2.23', b'2.22'), b''), (STA, STDOUT.replace(b'Job finished', b''), b''),
    (STA, STDOUT.replace(b'1 cpu(s)', b'2 cpu(s)'), b''), (STA, STDOUT, b'*ERROR failure')])
def test_completion_refusal(sta, stdout, stderr):
    with pytest.raises(followup.FollowupError):
        followup.completed_outputs(sta, stdout, stderr)


@pytest.mark.parametrize('key,value', [('exit_code',1), ('timed_out',True),
    ('executable_sha256','b'*64), ('deck_sha256','b'*64), ('dat_sha256','b'*64), ('command',['ccx','-o','x'])])
def test_receipt_binding_refusal(key, value):
    source = receipt(); source[key] = value
    with pytest.raises(followup.FollowupError):
        followup.analytic_candidate(DAT, STA, STDOUT, b'', receipt=source, deck_sha256='a'*64, command=COMMAND)


def test_complete_wrong_force_oracle_refused_after_hash_binding():
    bad = DAT.replace(b'1 1 0 0', b'1 2 0 0')
    source = receipt(); source['dat_sha256'] = followup.sha(bad)
    with pytest.raises(followup.FollowupError, match='oracle'):
        followup.analytic_candidate(bad, STA, STDOUT, b'', receipt=source, deck_sha256='a'*64, command=COMMAND)


def authority():
    return dict(status='APPROVED', approval_evidence='human fresh150', total_seconds=150,
        reserve_seconds=60, allowed_modes=list(followup.MODES))


@pytest.mark.parametrize('change', ['pending', 'no-evidence', 'unknown-remainder', 'incorrect-remainder', 'bad-mode'])
def test_fresh_authority_refusal(change):
    grant = authority(); ledger = dict(status='APPROVED', total_seconds=150, used_seconds=0., remaining_seconds=150.)
    mode = 'controls'
    if change == 'pending': grant['status'] = 'PENDING'
    if change == 'no-evidence': grant['approval_evidence'] = None
    if change == 'unknown-remainder': ledger['remaining_seconds'] = None
    if change == 'incorrect-remainder': ledger['remaining_seconds'] = 149.
    if change == 'bad-mode': mode = 'native'
    with pytest.raises(followup.FollowupError): followup.validate_authority(grant, ledger, mode)


def test_authority_detaches_caller_and_does_not_adopt_semantics():
    grant = authority(); ledger = dict(status='APPROVED', total_seconds=150, used_seconds=0., remaining_seconds=150.)
    detached, _ = followup.validate_authority(grant, ledger, 'controls')
    grant['allowed_modes'].clear()
    assert detached['allowed_modes'] == list(followup.MODES)


@pytest.mark.parametrize('producer', ['synthetic', 'CalculiX', None])
def test_unadopted_confirmation_refused(producer):
    with pytest.raises((followup.FollowupError, followup.audit.EquationForceAuditError)):
        followup.validate_confirmation(dict(producer=producer), dict(candidate_sha256='a'*64))


def confirmed_fixture():
    bindings = dict(candidate_sha256='a'*64, source_archive_sha256='b'*64)
    record = dict(status='CONFIRMED_BY_INDEPENDENT_REVIEW', version='2.23', executable_sha256=followup.audit.CCX_SHA256,
        semantics=followup.audit.SEMANTICS, runtime_binary_correspondence='INDEPENDENTLY_CONFIRMED',
        source_files_sha256=followup.audit.CCX_SOURCE_FILES_SHA256,
        correspondence_method='independent_analytic_spc_mpc_observable_control', exact_release_source_sha256='b'*64,
        evidence_sha256='c'*64, control_evidence_sha256='a'*64, review_id='fictional-control-only',
        independent_reviewer_id='fictional', evidence_reference='synthetic test; not real evidence', control_bindings=bindings)
    return record, bindings


def test_confirmation_detaches_exact_fictional_bindings():
    record, bindings = confirmed_fixture()
    result = followup.validate_confirmation(record, bindings)
    bindings['candidate_sha256'] = 'd'*64
    assert result['independent_semantics_confirmation']['control_bindings']['candidate_sha256'] == 'a'*64


@pytest.mark.parametrize('change', ['candidate', 'archive', 'actual-bindings'])
def test_confirmation_actual_evidence_binding_mutation_refused(change):
    record, bindings = confirmed_fixture()
    if change == 'candidate': record['control_evidence_sha256'] = 'd'*64
    if change == 'archive': record['exact_release_source_sha256'] = 'd'*64
    if change == 'actual-bindings': bindings['candidate_sha256'] = 'd'*64
    with pytest.raises(followup.FollowupError): followup.validate_confirmation(record, bindings)


class FakeProcess:
    def __init__(self, pid, events, creation=10., alive=True, failure=False):
        self.pid=pid; self.events=events; self.creation=creation; self.alive=alive; self.failure=failure
    def create_time(self): return self.creation
    def is_running(self): return self.alive
    def kill(self): self.events.append(('kill',self.pid))
    def wait(self, timeout):
        if self.failure: raise RuntimeError('wait failure')
        self.alive=False; self.events.append(('wait',self.pid))


def test_generic_monitor_failure_kills_and_verifies_child_before_parent():
    events=[]; child=FakeProcess(2,events); parent=FakeProcess(1,events)
    followup.fatal_monitor_cleanup(parent,{2:(child,10.)})
    assert events == [('kill',2),('wait',2),('kill',1)]


@pytest.mark.parametrize('change', ['creation','pid','cleanup-failure','oversized'])
def test_cleanup_uncertainty_refuses_parent_kill(change):
    events=[]; child=FakeProcess(2,events); parent=FakeProcess(1,events); registry={2:(child,10.)}
    if change == 'creation': child.creation=11.
    if change == 'pid': registry={3:(child,10.)}
    if change == 'cleanup-failure': child.failure=True
    if change == 'oversized': registry={n:(FakeProcess(n,events),10.) for n in range(65)}
    with pytest.raises(followup.FollowupError): followup.fatal_monitor_cleanup(parent,registry)
    assert ('kill',1) not in events


def test_full_thread_override_contract():
    followup.validate_thread_environment(dict(followup.THREAD_ENVIRONMENT))


@pytest.mark.parametrize('change', ['override','unrecorded'])
def test_thread_override_refusal(change):
    value=dict(followup.THREAD_ENVIRONMENT)
    if change == 'override': value['NUMBER_OF_CPUS']='2'
    if change == 'unrecorded': value['CCX_NPROC_FOREIGN']='2'
    with pytest.raises(followup.FollowupError): followup.validate_thread_environment(value)


def test_actual_saved_wrong_response_refused_after_valid_preamble_and_hashes():
    from pathlib import Path
    raw = Path(followup.__file__).resolve().parents[1]/'.qualification/b3-ge-e4-pl/r8-e03-coarse-dev-20261007-v1/next-force-output-v1/analytic-v1'
    dat = (raw/'phase/mpc-support-v3.dat').read_bytes()
    sta = (raw/'phase/mpc-support-v3.sta').read_bytes()
    stdout = (raw/'ccx-stdout.log').read_bytes(); stderr = (raw/'ccx-stderr.log').read_bytes()
    u, g = followup.read_analytic_dat(dat)
    assert u[4][0] == 0 and [g[n][0] for n in range(1,5)] == [1,-1,2,-2]
    import json
    source=json.loads((raw/'ccx-process.json').read_text())
    source.update(timed_out=False,deck_sha256=followup.sha((raw/'phase/mpc-support-v3.inp').read_bytes()))
    source.update({key+'_sha256':followup.sha(value) for key,value in dict(dat=dat,sta=sta,stdout=stdout,stderr=stderr).items()})
    with pytest.raises(followup.FollowupError, match='oracle'):
        followup.analytic_candidate(dat, sta, stdout, stderr, receipt=source, deck_sha256=source['deck_sha256'], command=source['command'])


def test_exact_single_preamble_accepts_synthetic_oracle():
    u,g=followup.read_analytic_dat(b' S T E P 1\n INCREMENT 1\n'+DAT)
    assert u[4][0] == .1 and g[4] == [0,0,0]


def test_wrong_response_refused_with_valid_synthetic_preamble_and_hashes():
    # A coherent receipt and successful parsing cannot establish physical
    # agreement. Preserve this portable counterexample separately from the
    # exact saved failed-execution regression, whose evidence is not in Git.
    displacement,heading,forces=DAT.partition(b' forces ')
    dat = b' S T E P 1\n INCREMENT 1\n'+displacement.replace(b'.1 0 0',b'0 0 0')+heading+forces.replace(
        b'3 0 0 0\n4 0 0 0\n',b'3 2 0 0\n4 -2 0 0\n')
    u,g=followup.read_analytic_dat(dat)
    assert u[4][0]==0 and [g[n][0] for n in range(1,5)]==[1,-1,2,-2]
    source=receipt();source['dat_sha256']=followup.sha(dat)
    with pytest.raises(followup.FollowupError,match='oracle'):
        followup.analytic_candidate(dat,STA,STDOUT,b'',receipt=source,
                                    deck_sha256='a'*64,command=COMMAND)


@pytest.mark.parametrize('prefix', [b'S T E P 2\nINCREMENT 1\n',b'S T E P 1\nINCREMENT 2\n',
    b'STEP 1\nINCREMENT 1\n', b'S T E P 1\nINCREMENT 1\nS T E P 1\nINCREMENT 1\n'])
def test_wrong_or_repeated_preamble_refused(prefix):
    with pytest.raises(followup.FollowupError): followup.read_analytic_dat(prefix+DAT)


def direct_launch():
    return dict(pid=42,creation_time=10.,affinity=[0],environment=dict(followup.THREAD_ENVIRONMENT))


def test_short_run_direct_launch_without_periodic_rows_is_reported_honestly():
    value=followup.validate_ccx_observations(direct_launch(),[])
    assert value['direct_launch_observed'] is True
    assert value['periodic_sample_count'] == 0 and value['periodic_samples_observed'] is False


def test_existing_periodic_rows_still_validate():
    value=followup.validate_ccx_observations(direct_launch(),[dict(pid=42,affinity=[0],os_threads=2)])
    assert value['periodic_sample_count'] == 1 and value['os_thread_counts_are_diagnostic']


@pytest.mark.parametrize('change', ['missing-direct','wrong-direct','wrong-row','wrong-pid'])
def test_observation_refusal(change):
    launch=direct_launch(); rows=[]
    if change == 'missing-direct': launch.pop('affinity')
    if change == 'wrong-direct': launch['affinity']=[1]
    if change == 'wrong-row': rows=[dict(pid=42,affinity=[1])]
    if change == 'wrong-pid': rows=[dict(pid=43,affinity=[0])]
    with pytest.raises(followup.FollowupError): followup.validate_ccx_observations(launch,rows)


def v4_dat():
    text='S T E P 1\nINCREMENT 1\n'
    for label,values in [('displacements (vx,vy,vz)',[0,.1,0,0]),('forces (fx,fy,fz)',[-1,1,0,0])]:
        text+=label+' for set ALL and time 1.0\n'
        text+=''.join(f'{node} {value} 0 0\n' for node,value in enumerate(values,1))
    return text.encode('ascii')


def test_separate_fixed_v4_zero_support_oracle():
    dat=v4_dat(); source=receipt(); source['dat_sha256']=followup.sha(dat)
    value=followup.zero_support_analytic_candidate(dat,STA,STDOUT,b'',receipt=source,deck_sha256='a'*64,command=COMMAND)
    assert value['physical_multiplier'] == -3 and value['physical_spc_fx'] == [-3]
    assert value['free_equilibrium_fx'] == [0,0] and value['semantics_adopted'] is False


@pytest.mark.parametrize('bad', [DAT,v4_dat().replace(b'2 0.1 0 0',b'2 0 0 0'),v4_dat().replace(b'1 -1 0 0',b'1 1 0 0')])
def test_v4_cannot_accept_v3_or_fitted_response(bad):
    source=receipt(); source['dat_sha256']=followup.sha(bad)
    with pytest.raises(followup.FollowupError,match='v4'):
        followup.zero_support_analytic_candidate(bad,STA,STDOUT,b'',receipt=source,deck_sha256='a'*64,command=COMMAND)
