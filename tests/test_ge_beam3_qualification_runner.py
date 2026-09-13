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
            candidate=dict(commit='a'*40,tree='b'*40),inputs={},review_sha256='c'*64,selected=selected)
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
        lease=dict(run_id=str(uuid.uuid4()),gate='q4-affine-numerical',lane='core',candidate={},inputs={},
                   selected=['fixture.py::'+name for name in r.NUMERICAL_TESTS])
        values=[]
        for i in range(15):
            a=r.numerical_assignment(lease,i);digest=sha256(r.canonical(a)).hexdigest()
            value=dict(schema='GE_BEAM3_REGISTERED_NUMERICAL_NODE_V1',node=a['node'],index=i,candidate={},
                inputs_sha256=a['inputs_sha256'],whole_inventory_sha256=a['whole_inventory_sha256'],lane='core',
                records=[dict(test=r.NUMERICAL_TESTS[i].removeprefix('test_affine_recovery_'),
                    tables={key:[{'id':identity} for identity in ids] for key,ids in r.NUMERICAL_TABLE_IDS[i].items()},
                    full_g3c_qualified=False,production_qualified=False)],contradictions=[],status='PASSED',
                physical_recovery_scope='REGISTERED_AFFINE_LOCAL_ONLY',full_g3c_qualified=False,production_qualified=False)
            raw=r.canonical(value);completion=dict(assignment_sha256=digest,node=a['node'],scientific=r.fingerprint(raw))
            self.assertEqual(r.validate_numerical_result(raw,completion,lease,i,digest),value);values.append(value)
            for key,bad_value in (('index',True),('records',[]),('status','CONTRADICTION'),('production_qualified',True)):
                bad=dict(value,**{key:bad_value});bad_raw=r.canonical(bad)
                with self.assertRaises(ValueError):r.validate_numerical_result(bad_raw,
                    dict(completion,scientific=r.fingerprint(bad_raw)),lease,i,digest)
        self.assertEqual(r.numerical_union(lease,values)['terminal'],'PROVISIONAL_GO_G3C_Q4_AFFINE_LOCAL_PHYSICAL_RECOVERY_ONLY')
        for bad in (values[:-1],values[::-1],values+values[:1]):
            with self.assertRaises(ValueError):r.numerical_union(lease,bad)
        values[3]['contradictions']=[dict(payload={'inert':True},verification={'accepted':True})]
        values[3]['status']='CONTRADICTION'
        self.assertEqual(r.numerical_union(lease,values)['terminal'],'NO_GO_G3C_Q4_AFFINE_RECOVERY_VARIATIONAL_OR_STATE')

    def test_numerical_ordered_table_identity_not_only_count(self):
        for i,name in enumerate(r.NUMERICAL_TESTS):
            value=dict(test=name.removeprefix('test_affine_recovery_'),tables={
                key:[{'id':identity} for identity in ids] for key,ids in r.NUMERICAL_TABLE_IDS[i].items()},
                full_g3c_qualified=False,production_qualified=False)
            r.validate_numerical_tables('fixture.py::'+name,[value])
            for key in value['tables']:
                bad=copy.deepcopy(value);bad['tables'][key][0]['id']='substituted-but-unique'
                with self.assertRaises(ValueError):r.validate_numerical_tables('fixture.py::'+name,[bad])
                if len(value['tables'][key])>1:
                    bad=copy.deepcopy(value);bad['tables'][key]=bad['tables'][key][::-1]
                    with self.assertRaises(ValueError):r.validate_numerical_tables('fixture.py::'+name,[bad])

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
