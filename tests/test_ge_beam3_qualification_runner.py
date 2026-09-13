"""Inert runner guard tests: fake jobs only, never import mechanics."""
import copy
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_ge_beam3_qualification as r

class Clock:
    def __init__(self):self.value=0
    def __call__(self):return self.value
    def sleep(self,value):self.value+=value

class Job:
    def __init__(self,memory=0):self.active=1;self.mem=0;self.killed=False;self.closed=False;self.code=None;self.cpu=0
    def accounting(self):return self.cpu,self.active,self.mem
    def terminate(self):self.killed=True;self.active=0;self.code=124;return True
    def close(self):self.closed=True
    def poll(self):return self.code
    def launch(self,*a,**kw):return self


def inert_zeros(shape):
    return [inert_zeros(shape[1:]) for _ in range(shape[0])] if shape else 0.


def inert_row(table,identity):
    """Schema fixtures only: deliberately NOT mechanics or accepted evidence."""
    row={'id':identity};digest=lambda shape:r.numeric_array(inert_zeros(shape),shape)
    if table in r.PHYSICAL_TABLES:
        state=dict(construction_id=r.row_construction(table,identity),coordinates=inert_zeros([4,3]),q=inert_zeros([24]),
            accepted=inert_zeros([4,3,3]),normal=[0.,0.,1.],material_direction=[1.,0.,0.],director_polarity=-1 if identity.endswith('::DIRECTOR:-1') else 1)
        row.update(state=state,state_sha256=sha256(r.canonical(state)).hexdigest(),physical_checks={})
        checks=dict(symmetry=0.,spatial_force=0.,spatial_tangent=0.)
        mapping={'energy':'physical_energy','force':'physical_force','hessian':'physical_hessian'}
        if table=='work' and not identity.endswith('::ZERO'):
            mapping.update(source_energy='source_physical_energy',source_force='source_physical_force',source_hessian='source_physical_hessian')
        for key,predicate in mapping.items():
            check=dict(relative_error=0.,passed=True,actual=digest(r.PHYSICAL_SHAPES[predicate]))
            checks[key]=check;row['physical_checks'][predicate]=check
        row['checks']=checks
    if table=='definitions':row.update(recipe_sha256='0'*64,descriptor_sha256='0'*64)
    elif table=='source_graph':row['hashes']=dict(r.NUMERICAL_SOURCE_HASHES)
    elif table=='extension_lemma':row.update(lemma_sha256='156d33ae5a621b953b5d04050218618f6416bac1042f94d3d3fc5c305c9f8762',review_sha256='e28f184023ce1bba825a89079bcd2f9af99cf7861d701d7d918e2d30492b073e')
    elif table=='station_join':row.update(station_association_id=r.STATION_ASSOCIATION_ID,verified=True,rejections=4)
    elif table=='chart_authority':row.update(chart_numerics_id=r.CHART_ID,addendum_sha256=r.CHART_ADDENDUM_SHA,
        review_sha256=r.CHART_REVIEW_SHA,increment_addendum_sha256=r.INCREMENT_ADDENDUM_SHA,
        increment_review_sha256=r.INCREMENT_REVIEW_SHA,sources=dict(r.CHART_SOURCES),verified=True)
    elif table=='fingerprint':row.update(distinct_fingerprints=20,nonfinite_rejections=5,evidence_sha256='0'*64,verified=True)
    elif table=='station':row.update(checks={key:0. for key in ('d','D','D2','R','Q','x')},energy=0.,stations=4)
    elif table=='independent':row['stations']=[{key:0. for key in ('M','strain','resultant','frame','constitutive')} for _ in range(4)]
    elif table=='schur':row.update(schur=digest([24,24]),full_internal_dimension=64)
    elif table=='work':row['chart_image_sentinels']=True
    elif table=='directional':row.update(work=0.,tangent=0.)
    elif table=='rigid':row.update(rigid_columns=6,total_positive_modes=18,eigenvalues=digest([24]))
    elif table in ('common_motion','passive','rebase','tiny'):row['energy']=1.
    elif table=='d4':
        k=int(identity.rsplit(':',1)[1]);row['station_map']=[(i+k%4)%4 for i in ((0,1,2,3) if k<4 else (0,3,2,1))]
    elif table=='director':row['physical_polarity']=int(identity.rsplit(':',1)[1])
    elif table=='graph':
        ids=[101,102,103,104] if identity.startswith('J_Q4_PAIR::') else [301,302,303,304]
        element=11 if identity.startswith('J_Q4_PAIR::') else 13
        if '::RENUMBERED::' in identity:ids=[10000+7*i for i in ids];element=20000+5*element
        if '::CONNECTIVITY_REVERSED::' in identity:ids=[ids[i] for i in (0,3,2,1)]
        row.update(node_ids=ids,element_id=element,recipe_sha256='0'*64)
    elif table=='channels':row.update(physical=0.,numerical=[dict(name=n,energy=0.) for n in ('NUMERICAL_PL','NUMERICAL_HOURGLASS')])
    elif table=='races':row['rejected_before_family']=True
    elif table=='immutability':
        row.update(verified=True,prior_arrays_sha256='0'*64)
        if identity=='all_detached_arrays':row['array_count']=31
        if identity=='reentry':row['rejections']=2
        if identity=='nested_candidate_bytes':row['fingerprint_sha256']='0'*64
    elif table=='rejections':
        if identity in ('before_work','before_publication','invalid_callback'):
            row.update(callbacks=2 if identity=='before_publication' else 1,family_entries=1 if identity=='before_publication' else 0,published=False)
        else:row['rejected_before_family']=True
    elif table=='eigen_derivatives':row.update(derivative_coordinates=24,derivative_pairs=576,
        derivative_residuals={key:0. for key in ('first_normalization','second_normalization','first_stationarity','second_stationarity','second_symmetry')})
    elif table=='chart_mutations':
        compared=identity in ('missing_delta_covariance','naive_reference_subtraction','omitted_delta_derivatives')
        row['rejection']=('INDEPENDENT_CHART_COMPARISON' if compared else 'BRANCH_REJECTION' if identity in ('wrong_davenport_branch','wrong_polar_branch')
            else 'DERIVATIVE_IDENTITY_REJECTION' if identity in ('eigen_first_derivative','eigen_second_derivative') else 'NONCONVERGENCE_REJECTION')
        if compared:row['relative_error']=1e-8
    elif table=='mutations':
        mutation=identity.split('::',1)[1]
        row['rejection']=('INDEPENDENT_HESSIAN' if mutation in ('force_weighted_Hessian','chart_second') else
            'STATION_EQUILIBRIUM' if mutation=='coupling_sign' else 'STATION_INVERSE' if mutation=='inverse' else
            'MATERIAL_ENERGY' if mutation=='numerical_energy_leak' else 'INDEPENDENT_STATION_COMPARISON')
    if table=='tiny':row['chart']={key:0. for key in ('d','D','D2','R','Q','x')}
    return row


def inert_records(index):
    return [dict(test=r.NUMERICAL_TESTS[index].removeprefix('test_affine_recovery_'),
        tables={table:[inert_row(table,identity) for identity in ids] for table,ids in r.NUMERICAL_TABLE_IDS[index].items()},
        full_g3c_qualified=False,production_qualified=False)]


def inert_observations(node,records):
    return {(node,table,row['id']):row['state_sha256'] for table,rows in records[0]['tables'].items()
            if table in r.PHYSICAL_TABLES for row in rows}


def inert_contradiction(node,table,row,lease,predicate='physical_energy'):
    """Protocol-only synthetic witness, never passed to the physics checker."""
    state=row['state'];actual=inert_zeros(r.PHYSICAL_SHAPES[predicate])
    error=.5;fingerprint=r.numeric_array(actual,r.PHYSICAL_SHAPES[predicate])
    check=dict(relative_error=error,passed=False,actual=fingerprint)
    row['physical_checks'][predicate]=check
    key={'physical_energy':'energy','physical_force':'force','physical_hessian':'hessian',
         'source_physical_energy':'source_energy','source_physical_force':'source_force','source_physical_hessian':'source_hessian'}[predicate]
    row['checks'][key]=check
    if predicate.startswith('source_'):row['chart_image_sentinels']=False
    payload=dict(schema='Q4_AFFINE_NUMERICAL_CONTRADICTION_V1',predicate=predicate,actual=actual,tolerance=1e-11,
        scale_mode='REFERENCE_EDGE_NONDIMENSIONAL_V1',source_identity=sha256(r.canonical(lease['inputs'])).hexdigest(),
        candidate_identity=lease['candidate']['commit'],fixture_identity=state['construction_id'],
        node=node,table=table,row_id=row['id'],state_sha256=row['state_sha256'],
        **{key:state[key] for key in ('coordinates','q','accepted','normal','material_direction','director_polarity')})
    verification=dict(accepted=True,predicate=predicate,relative_error=error,node=node,table=table,row_id=row['id'],
        fixture_identity=state['construction_id'],payload_sha256=sha256(r.canonical(payload)).hexdigest(),
        state_sha256=row['state_sha256'],actual=fingerprint,expected=dict(fingerprint,sha256='1'*64))
    return dict(payload=payload,verification=verification)

class GuardTests(unittest.TestCase):
    def test_registered_inventory(self):
        self.assertEqual(len(r.inventory('core')),8);self.assertEqual(len(r.inventory('smoke')),2)
        self.assertEqual(len(r.inventory('core','b2-adapter')),3)
        self.assertEqual(len(r.inventory('smoke','b2-adapter')),1)
        self.assertEqual(len(r.inventory('core','q4-audit')),5)
        self.assertEqual(len(r.inventory('smoke','q4-audit')),2)
        self.assertEqual(len(r.inventory('core','q4-affine-exact')),6)
        self.assertEqual(len(r.inventory('smoke','q4-affine-exact')),2)
        self.assertEqual(len(r.inventory('core','q4-affine-numerical')),15)
        self.assertEqual([p.split('::')[-1] for p in r.inventory('smoke','q4-affine-numerical')],
                         [r.NUMERICAL_TESTS[0],r.NUMERICAL_SMOKE])
        with self.assertRaises(ValueError):r.inventory('all')

    def test_strict_json(self):
        for raw in (b'{"x":1,"x":2}\n',b'{"x":NaN}\n',b'{"x":Infinity}\n'):
            with self.assertRaises(ValueError):r.environment.strict(raw)

    def test_review_hash_identity_and_inputs(self):
        candidate=dict(commit='a'*40,tree='b'*40);rows={'x':dict(bytes=1,sha256='c'*64)}
        value=dict(decision='ACCEPTED_GE_BEAM3_REGISTERED_GATE_FOR_BOUNDED_EXECUTION',findings=[],
            reviewer=dict(independent=True),subject_commit=candidate['commit'],scope=dict(scope_id=r.SCOPE,gate='b2-core',
            subject_tree=candidate['tree'],inputs_sha256=sha256(r.canonical(rows)).hexdigest(),contract_sha256=r.CONTRACT_SHA))
        raw=r.canonical(value);h=sha256(raw).hexdigest();r.verify_review(raw,h,candidate,rows)
        with self.assertRaises(ValueError):r.verify_review(raw,'0'*64,candidate,rows)
        with self.assertRaises(ValueError):r.verify_review(raw,h,candidate,{})
        with self.assertRaises(ValueError):r.verify_review(raw,h,candidate,rows,'b2-adapter')
        for key,v in (('subject_commit','d'*40),('findings',['defect']),('reviewer',dict(independent=False))):
            bad=dict(value,**{key:v});b=r.canonical(bad)
            with self.assertRaises(ValueError):r.verify_review(b,sha256(b).hexdigest(),candidate,rows)

    def test_lease_mismatch_before_construction(self):
        expected=({'commit':'a','tree':'b'},{},b'{}\n')
        lease=dict(schema=r.SCOPE,run_id=str(uuid.uuid4()),gate='b2-core',lane='smoke',
            candidate=expected[0],inputs={},review_sha256='c',selected=r.inventory('smoke'))
        r.validate_lease(lease,expected,'c','smoke',Path('.'))
        for key,v in (('gate','other'),('candidate',{}),('selected',[]),('inputs',{'altered':1}),('run_id','not-a-uuid')):
            bad=copy.deepcopy(lease);bad[key]=v
            with self.assertRaises(ValueError):r.validate_lease(bad,expected,'c','smoke',Path('.'))

    def test_exclusive_outputs_and_attempt_reuse(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);r.claim_attempt(root,'test')
            with self.assertRaises(FileExistsError):r.claim_attempt(root,'test')
            self.assertFalse((root/'scientific.json').exists())

    def test_inactivity_memory_and_timeout_drain(self):
        for mode in ('inactivity','memory','wall'):
            j=Job();c=Clock()
            if mode=='memory':j.mem=r.MEMORY+1
            def progress():
                if mode=='wall':j.cpu+=1
                return (0,0)
            result=r.monitor(j,j,progress,c,c.sleep)
            self.assertEqual(result['status'],'RESOURCE_BLOCKED');self.assertTrue(j.killed)
            self.assertEqual(result['active_processes'],0);self.assertLess(c.value,600)

    def test_exited_parent_does_not_release_live_tree(self):
        j=Job();j.code=0;c=Clock()
        result=r.monitor(j,j,lambda:(0,0),c,c.sleep)
        self.assertEqual(result['status'],'RESOURCE_BLOCKED');self.assertTrue(j.killed)
        for code,status in ((0,'PASSED'),(1,'FAILED')):
            j=Job();j.active=0;j.code=code
            self.assertEqual(r.monitor(j,j,lambda:(0,0),c,c.sleep)['status'],status)

    def test_exception_closes_and_drains_no_canonical_output(self):
        with tempfile.TemporaryDirectory() as d:
            j=Job();root=Path(d)
            expected=({'commit':'a','tree':'b'},{},b'{}\n')
            args=SimpleNamespace(review=root/'review-source',review_sha256='c',gate='b2-core',lane='smoke')
            with patch.object(r,'authority',return_value=expected),patch.object(r,'job_type',return_value=lambda n:j), \
                 patch.object(r.tempfile,'mkdtemp',return_value=d),patch.object(r,'monitor',side_effect=RuntimeError('injected')):
                with self.assertRaises(RuntimeError):r.execute(args)
            self.assertTrue(j.killed and j.closed);self.assertEqual(j.active,0)
            self.assertFalse((root/'scientific.json').exists());self.assertTrue((root/'process.json').exists())

    def test_no_mechanics_import_before_authority(self):
        self.assertNotIn('numpy',sys.modules);self.assertNotIn('anysolver',sys.modules)

    def test_checker_gate_and_replica_before_import(self):
        with self.assertRaises(ValueError):r.q4_checker(Path('.'),'wrong','1','bad')
        with self.assertRaises(ValueError):r.q4_checker(Path('.'),r.Q4_FIXTURES[0],'3','bad')
        with patch.object(r,'read',return_value=r.canonical({'gate':'b2-adapter','lane':'core'})), \
             patch.object(r,'authority',side_effect=AssertionError('wrong gate entered authority')):
            with self.assertRaises(ValueError):r.q4_checker(Path('.'),r.Q4_FIXTURES[0],'1','bad')
        self.assertNotIn('ge_beam3_q4_recovery_coefficient_checker',sys.modules)
        with self.assertRaises(ValueError):r.q4_checker(Path('.'),r.Q4_FIXTURES[0],'1','bad','q4-affine-exact')
        with patch.object(r,'read',return_value=r.canonical({'gate':'q4-audit','lane':'core'})), \
             patch.object(r,'authority',side_effect=AssertionError('cross gate entered authority')):
            with self.assertRaises(ValueError):r.q4_checker(Path('.'),r.AFFINE_FIXTURES[0],'1','bad','q4-affine-exact')
        self.assertNotIn('ge_beam3_q4_affine_recovery_checker',sys.modules)

    def test_affine_review_gate_binding(self):
        candidate=dict(commit='a'*40,tree='b'*40);rows={}
        value=dict(decision='ACCEPTED_GE_BEAM3_REGISTERED_GATE_FOR_BOUNDED_EXECUTION',findings=[],
            reviewer=dict(independent=True),subject_commit=candidate['commit'],scope=dict(scope_id=r.SCOPE,
            gate='q4-affine-exact',subject_tree=candidate['tree'],inputs_sha256=sha256(r.canonical(rows)).hexdigest(),
            contract_sha256=r.AFFINE_PLAN_SHA))
        raw=r.canonical(value);digest=sha256(raw).hexdigest()
        r.verify_review(raw,digest,candidate,rows,'q4-affine-exact')
        with self.assertRaises(ValueError):r.verify_review(raw,digest,candidate,rows,'q4-audit')

    def test_affine_terminal_inventory_and_first_witness(self):
        rows=[];zero={'coefficient':['0']*8}
        for fixture in r.AFFINE_FIXTURES:
            proof=dict(schema='GE_BEAM3_Q4_AFFINE_RECOVERY_EXACT_FIXTURE_V1',fixture_id=fixture,
                coefficient_records=[zero]*7125,coefficient_count=7125,degree_counts={'3':1140,'4':5985},
                nonzero_count=0,zero_count=7125,first_nonzero=None,physical_recovery_qualified=False,full_g3c_qualified=False)
            verification=dict(fixture_id=fixture,coefficient_count=7125,nonzero_count=0,first_nonzero=None,
                independently_verified=True,physical_recovery_qualified=False,full_g3c_qualified=False)
            rows.append(dict(test=fixture,proof=proof,verification=verification,checker_replicas_byte_identical=True))
        self.assertEqual(r.affine_adjudication(rows,'core')['coefficient_count'],21375)
        self.assertEqual(r.affine_adjudication(rows,'core')['terminal'],'UNCLASSIFIED_G3C_Q4_AFFINE_RECOVERY_EXACT_IDENTITIES_ONLY')
        witness={'coefficient':['1']+['0']*7}
        for row in reversed(rows):
            row['proof']['coefficient_records'][0]=witness
            row['proof'].update(first_nonzero=witness,nonzero_count=1,zero_count=7124)
            row['verification'].update(first_nonzero=witness,nonzero_count=1)
            self.assertEqual(r.affine_adjudication(rows,'core')['first_nonzero']['fixture_id'],row['test'])
        for wrong in (rows[::-1],rows[:-1],rows+rows[:1]):
            with self.assertRaises(ValueError):r.affine_adjudication(wrong,'core')
        self.assertEqual(r.affine_adjudication([],'smoke')['terminal'],'NOT_ADJUDICATED_SMOKE_ONLY')

    def test_q4_terminal_order_and_incomplete_rejection(self):
        # Inert decision-layer fixtures, not algebraic or scientific evidence.
        zero={'coefficient':['0']*8};rows=[]
        for fixture in r.Q4_FIXTURES:
            proof=dict(coefficient_records=[zero]*20150,coefficient_count=20150,
                       nonzero_count=0,zero_count=20150,first_nonzero=None)
            rows.append(dict(test=fixture,proof=proof,checker_replicas_byte_identical=True,
                verification=dict(first_nonzero=None,nonzero_count=0,independently_verified=True)))
        self.assertEqual(r.q4_adjudication(rows,'core')['terminal'],'UNCLASSIFIED_G3C_Q4_TWO_FIXTURE_COEFFICIENT_IDENTITIES')
        nonzero={'coefficient':['1']+['0']*7}
        for row in reversed(rows):
            row['proof']['coefficient_records'][0]=nonzero
            row['proof'].update(first_nonzero=nonzero,nonzero_count=1,zero_count=20149)
            row['verification'].update(first_nonzero=nonzero,nonzero_count=1)
            result=r.q4_adjudication(rows,'core')
            self.assertEqual(result['terminal'],'NO_GO_G3C_Q4_NATURAL_RETAINED_SPACE_FINITE_IDENTITY')
            self.assertEqual(result['first_nonzero']['fixture_id'],row['test'])
        with self.assertRaises(ValueError):r.q4_adjudication(rows[::-1],'core')
        with self.assertRaises(ValueError):r.q4_adjudication(rows[:1],'core')
        self.assertEqual(r.q4_adjudication([],'smoke')['terminal'],'NOT_ADJUDICATED_SMOKE_ONLY')

    def test_whole_invocation_watchdog(self):
        timers=[];exits=[]
        class Timer:
            def __init__(self,delay,callback):
                self.delay=delay;self.callback=callback;self.started=False;self.cancelled=False;timers.append(self)
            def start(self):self.started=True
            def cancel(self):self.cancelled=True
        w=r.WaveWatchdog(timer=Timer,exit_process=exits.append)
        self.assertEqual([t.delay for t in timers],[1780,1800])
        self.assertTrue(all(t.started and t.daemon for t in timers))
        def blocked_authority(*args):
            timers[0].callback()  # deadline before a job exists
            return ({},{},b'{}\n')
        with patch.object(r,'WaveWatchdog',return_value=w),patch.object(r,'authority',side_effect=blocked_authority):
            with self.assertRaises(TimeoutError):r.execute(SimpleNamespace(review=None,review_sha256=None,gate='b2-core'))
        self.assertEqual(exits,[124]);self.assertTrue(all(t.cancelled for t in timers))
        w=r.WaveWatchdog(timer=Timer,exit_process=exits.append);j=Job();w.attach(j)
        w.expire();self.assertTrue(j.killed)
        with self.assertRaises(TimeoutError):w.check()  # no publication after expiration
        w.hard_exit();self.assertEqual(exits,[124,124,124]);w.close()

    def test_numerical_assignment_binds_single_node_and_whole_inventory(self):
        selected=['test.py::n'+str(i) for i in range(15)]
        lease=dict(schema=r.SCOPE,run_id=str(uuid.uuid4()),gate='q4-affine-numerical',lane='core',
            candidate=dict(commit='a'*40,tree='b'*40),inputs={},review_sha256='c'*64,selected=selected,
            observation_manifest_sha256='f'*64)
        assignment=r.numerical_assignment(lease,4);r.validate_assignment(assignment,lease,4)
        for key,value in (('index',5),('node',selected[5]),('lane','smoke'),('parent_lease_sha256','0'*64),
                          ('whole_inventory_sha256','0'*64),('inputs_sha256','0'*64),('run_id',str(uuid.uuid4()))):
            bad=dict(assignment,**{key:value})
            with self.assertRaises(ValueError):r.validate_assignment(bad,lease,4)
        for wrong in (-1,15,True,'1'):
            with self.assertRaises(ValueError):r.numerical_assignment(lease,wrong)
        with self.assertRaises(ValueError):r.numerical_assignment(dict(lease,gate='q4-affine-exact'),0)

    def test_numerical_batch_independent_limits_and_worker_cap(self):
        class Watch:
            def check(self):pass
        for failure in ('inactivity','memory','wall'):
            clock=Clock();entries=[]
            for i in range(3):
                job=Job()
                if failure=='memory' and i==0:job.mem=r.MEMORY+1
                def progress(j=job,index=i):
                    if index or failure=='wall':j.cpu+=1
                    return (0,0)
                entries.append(dict(job=job,process=job,start=0,progress=progress))
            r.monitor_batch(entries,Watch(),clock,clock.sleep)
            self.assertEqual(entries[0]['record']['status'],'RESOURCE_BLOCKED')
            self.assertTrue(all(e['job'].killed and e['record']['active_processes']==0 for e in entries))
            self.assertLess(clock.value,600)
        for count in (0,4):
            with self.assertRaises(ValueError):r.monitor_batch([{}]*count,Watch())

    def test_numerical_batch_does_not_accept_live_descendant(self):
        clock=Clock();job=Job();job.code=0
        entry=dict(job=job,process=job,start=0,progress=lambda:(0,0))
        r.monitor_batch([entry],SimpleNamespace(check=lambda:None),clock,clock.sleep)
        self.assertEqual(entry['record']['status'],'RESOURCE_BLOCKED')
        self.assertTrue(job.killed)

    def test_numerical_result_schema_and_union_completeness(self):
        lease=dict(run_id=str(uuid.uuid4()),gate='q4-affine-numerical',lane='core',candidate=dict(commit='a'*40,tree='b'*40),inputs={},
                   selected=['fixture.py::'+name for name in r.NUMERICAL_TESTS],observation_manifest_sha256='f'*64)
        values=[];observations={}
        for i in range(15):
            a=r.numerical_assignment(lease,i);digest=sha256(r.canonical(a)).hexdigest()
            value=dict(schema='GE_BEAM3_REGISTERED_NUMERICAL_NODE_V1',node=a['node'],index=i,candidate=lease['candidate'],
                inputs_sha256=a['inputs_sha256'],whole_inventory_sha256=a['whole_inventory_sha256'],lane='core',
                records=inert_records(i),contradictions=[],status='PASSED',
                physical_recovery_scope='REGISTERED_AFFINE_LOCAL_ONLY',full_g3c_qualified=False,production_qualified=False,
                observation_manifest_sha256=lease['observation_manifest_sha256'])
            observations.update(inert_observations(a['node'],value['records']))
            raw=r.canonical(value);completion=dict(assignment_sha256=digest,node=a['node'],scientific=r.fingerprint(raw))
            self.assertEqual(r.validate_numerical_result(raw,completion,lease,i,digest,observations),value);values.append(value)
            for key,bad_value in (('index',True),('records',[]),('status','CONTRADICTION'),('production_qualified',True)):
                bad=dict(value,**{key:bad_value});bad_raw=r.canonical(bad)
                with self.assertRaises(ValueError):r.validate_numerical_result(bad_raw,
                    dict(completion,scientific=r.fingerprint(bad_raw)),lease,i,digest,observations)
        self.assertEqual(r.numerical_union(lease,values,observations)['terminal'],'PROVISIONAL_GO_G3C_Q4_AFFINE_LOCAL_PHYSICAL_RECOVERY_ONLY')
        for bad in (values[:-1],values[::-1],values+values[:1]):
            with self.assertRaises(ValueError):r.numerical_union(lease,bad,observations)
        values[4]['contradictions']=[inert_contradiction(values[4]['node'],'work',values[4]['records'][0]['tables']['work'][1],lease)]
        values[4]['status']='CONTRADICTION'
        self.assertEqual(r.numerical_union(lease,values,observations)['terminal'],'NO_GO_G3C_Q4_AFFINE_RECOVERY_VARIATIONAL_OR_STATE')

    def test_numerical_ordered_table_identity_not_only_count(self):
        for i,name in enumerate(r.NUMERICAL_TESTS):
            value=inert_records(i)[0]
            r.validate_numerical_tables('fixture.py::'+name,[value])
            for key in value['tables']:
                bad=copy.deepcopy(value);bad['tables'][key][0]['id']='substituted-but-unique'
                with self.assertRaises(ValueError):r.validate_numerical_tables('fixture.py::'+name,[bad])
                if len(value['tables'][key])>1:
                    bad=copy.deepcopy(value);bad['tables'][key]=bad['tables'][key][::-1]
                    with self.assertRaises(ValueError):r.validate_numerical_tables('fixture.py::'+name,[bad])

    def test_every_numerical_row_rejects_missing_extra_and_wrong_types(self):
        def paths(value,path=()):
            if type(value)is dict:
                for key,item in value.items():
                    yield path+(key,),item
                    yield from paths(item,path+(key,))
            elif type(value)is list:
                for index,item in enumerate(value):yield from paths(item,path+(index,))
        def owner(value,path):
            for key in path[:-1]:value=value[key]
            return value,path[-1]
        checked=set()
        for tables in r.NUMERICAL_TABLE_IDS:
            for table,ids in tables.items():
                # Distinct schema branches include ZERO/nonzero, all negative
                # probe IDs, graph renumberings and both director polarities.
                selected=ids if table in ('immutability','rejections','graph','director','chart_mutations') else [ids[0],ids[-1]]
                for identity in selected:
                    if (table,identity) in checked:continue
                    checked.add((table,identity));row=inert_row(table,identity)
                    r.validate_numerical_row(table,row)
                    for path,item in paths(row):
                        if type(path[-1])is str:
                            bad=copy.deepcopy(row);target,key=owner(bad,path);del target[key]
                            with self.assertRaises(ValueError):r.validate_numerical_row(table,bad)
                        if type(item) in (float,int):
                            for wrong in (True,float('nan'),float('inf'),'0'):
                                bad=copy.deepcopy(row);target,key=owner(bad,path);target[key]=wrong
                                with self.assertRaises(ValueError):r.validate_numerical_row(table,bad)
                    bad=copy.deepcopy(row);bad['unregistered_summary']=True
                    with self.assertRaises(ValueError):r.validate_numerical_row(table,bad)
                    if table in r.PHYSICAL_TABLES:
                        bad=copy.deepcopy(row);bad['physical_checks']['physical_force']['actual']['shape']=[23]
                        with self.assertRaises(ValueError):r.validate_numerical_row(table,bad)

    def test_contradiction_receipt_bijection_and_frozen_observed_state(self):
        node='fixture.py::'+r.NUMERICAL_TESTS[4];records=inert_records(4)
        lease=dict(candidate={'commit':'a'*40},inputs={})
        observations=inert_observations(node,records)
        row=records[0]['tables']['work'][1];witness=inert_contradiction(node,'work',row,lease)
        r.validate_contradictions(node,records,[witness],lease,observations)
        for bad in ([],[witness,witness],[dict(payload=witness['payload'],verification={'accepted':True})]):
            with self.assertRaises(ValueError):r.validate_contradictions(node,records,bad,lease,observations)
        for part,key,value in (('payload','row_id',records[0]['tables']['work'][2]['id']),
            ('payload','node','other-node'),('payload','candidate_identity','c'*40),
            ('payload','actual',1.),('payload','state_sha256','d'*64),
            ('verification','payload_sha256','e'*64),('verification','relative_error',0.),
            ('verification','state_sha256','b'*64),('verification','expected',{'shape':[24],'sha256':'0'*64})):
            bad=copy.deepcopy(witness);bad[part][key]=value
            with self.assertRaises(ValueError):r.validate_contradictions(node,records,[bad],lease,observations)
        # Even a coherently rehashed row/payload/receipt cannot substitute an
        # unregistered reference or trial state after the parent pins authority.
        for field in ('coordinates','q','accepted'):
            bad_records=copy.deepcopy(records);bad_row=bad_records[0]['tables']['work'][1]
            if field=='coordinates':bad_row['state'][field][0][0]=.25
            elif field=='q':bad_row['state'][field][0]=.25
            else:bad_row['state'][field][0][0][0]=.25
            bad_row['state_sha256']=sha256(r.canonical(bad_row['state'])).hexdigest()
            bad_witness=inert_contradiction(node,'work',bad_row,lease)
            with self.assertRaises(ValueError):r.validate_contradictions(node,bad_records,[bad_witness],lease,observations)
        orphan_records=inert_records(4)
        with self.assertRaises(ValueError):r.validate_contradictions(node,orphan_records,[witness],lease,observations)

    def test_observation_manifest_is_canonical_pinned_and_ordered(self):
        expected=dict(source_bindings={},generator_bindings={},capsule_sha256='a'*64,
                      inventory_sha256=sha256(r.canonical(r.observation_specs())).hexdigest())
        value=dict(schema='GE_BEAM3_REGISTERED_OBSERVATION_HASHES_V1',**expected,
            observations=[dict(spec,state_sha256='b'*64) for spec in r.observation_specs()],
            fixture_data_only=True,numerical_qualification=False)
        raw=r.canonical(value);digest=sha256(raw).hexdigest()
        with patch.object(r,'read',return_value=raw),patch.object(r,'OBSERVATION_MANIFEST_SHA',digest), \
             patch.object(r,'observation_authority',return_value=expected):
            self.assertEqual(len(r.frozen_observations()),130)
        for mode in ('omitted','reordered','source','state_hash','wrong_id','duplicate'):
            bad=copy.deepcopy(value)
            if mode=='omitted':bad['observations'].pop()
            elif mode=='reordered':bad['observations'].reverse()
            elif mode=='source':bad['capsule_sha256']='c'*64
            elif mode=='state_hash':bad['observations'][0]['state_sha256']='not-a-digest'
            elif mode=='wrong_id':bad['observations'][0]['row_id']='foreign'
            else:bad['observations'][1]=copy.deepcopy(bad['observations'][0])
            bad_raw=r.canonical(bad)
            with patch.object(r,'read',return_value=bad_raw),patch.object(r,'OBSERVATION_MANIFEST_SHA',sha256(bad_raw).hexdigest()), \
                 patch.object(r,'observation_authority',return_value=expected):
                with self.assertRaises(ValueError):r.frozen_observations()
            with patch.object(r,'read',return_value=bad_raw),patch.object(r,'OBSERVATION_MANIFEST_SHA',digest):
                with self.assertRaises(ValueError):r.frozen_observations()

    def test_numerical_watchdog_drains_all_jobs(self):
        class Timer:
            def __init__(self,*args):pass
            def start(self):pass
            def cancel(self):pass
        exits=[];watch=r.WaveWatchdog(timer=Timer,exit_process=exits.append)
        jobs=[Job() for _ in range(3)]
        for job in jobs:watch.attach(job)
        watch.expire();self.assertEqual(exits,[124]);self.assertTrue(all(j.killed for j in jobs));watch.close()

if __name__=='__main__':unittest.main()
