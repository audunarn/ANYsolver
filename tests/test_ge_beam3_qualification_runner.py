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
        with self.assertRaises(ValueError):r.inventory('all')

    def test_strict_json(self):
        for raw in (b'{"x":1,"x":2}\n',b'{"x":NaN}\n',b'{"x":Infinity}\n'):
            with self.assertRaises(ValueError):r.environment.strict(raw)

    def test_review_hash_identity_and_inputs(self):
        candidate=dict(commit='a'*40,tree='b'*40);rows={'x':dict(bytes=1,sha256='c'*64)}
        value=dict(decision='ACCEPTED_GE_BEAM3_B2_CORE_FOR_BOUNDED_EXECUTION',findings=[],
            reviewer=dict(independent=True),subject_commit=candidate['commit'],scope=dict(scope_id=r.SCOPE,
            subject_tree=candidate['tree'],inputs_sha256=sha256(r.canonical(rows)).hexdigest(),contract_sha256=r.CONTRACT_SHA))
        raw=r.canonical(value);h=sha256(raw).hexdigest();r.verify_review(raw,h,candidate,rows)
        with self.assertRaises(ValueError):r.verify_review(raw,'0'*64,candidate,rows)
        with self.assertRaises(ValueError):r.verify_review(raw,h,candidate,{})
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

if __name__=='__main__':unittest.main()
