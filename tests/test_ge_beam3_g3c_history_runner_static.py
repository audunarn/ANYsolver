"""Inert runner tests; worker stubs never execute numerical mechanics."""
from hashlib import sha256
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import run_ge_beam3_g3c_history as runner


class RunnerStaticTests(unittest.TestCase):
    def test_exact_separate_inventories_and_review_scope(self):
        self.assertEqual(len(runner.SMOKES),5)
        self.assertEqual(len(runner.PREFIXES),3)
        self.assertTrue(all(len(nodes)==1 for nodes in runner.INVENTORIES.values()))
        candidate=dict(commit='1'*40,tree='2'*40); inputs={'a':dict(bytes=1,sha256='3'*64)}
        review=dict(decision='ACCEPTED_G3C_STABLE_IMPLEMENTATION_FOR_BOUNDED_DEVELOPMENT',findings=[],
            reviewer=dict(independent=True),subject_commit=candidate['commit'],
            scope=dict(subject_tree=candidate['tree'],source_map_sha256=runner.inherited.MAP_SHA,
                inputs_sha256=sha256(runner.canonical(inputs)).hexdigest(),scope_id=runner.SCOPE))
        raw=runner.canonical(review)
        runner.verify_review(raw,sha256(raw).hexdigest(),candidate,inputs)
        review['scope']['scope_id']='another_scope'; raw=runner.canonical(review)
        with self.assertRaises(ValueError): runner.verify_review(raw,sha256(raw).hexdigest(),candidate,inputs)

    def test_three_overlapping_workers_distinct_directories_no_retry(self):
        lock=threading.Lock(); barrier=threading.Barrier(3); live=0; maximum=0; names=[]; paths=[]
        first=set(list(runner.SMOKES)[:3])
        def child(out,lease,review,deadline):
            nonlocal live,maximum
            with lock:
                live+=1; maximum=max(maximum,live); names.append(lease['lane']); paths.append(out)
            if lease['lane'] in first: barrier.wait(timeout=5)
            with lock: live-=1
            return dict(status='PASSED')
        with patch.object(runner,'child',side_effect=child):
            result=runner.run_wave(Path('unused-inert-wave'),runner.SMOKES,{},b'')
        self.assertEqual(result['status'],'PASSED'); self.assertEqual(maximum,3)
        self.assertEqual(len(names),5); self.assertEqual(len(set(paths)),5)
        self.assertEqual(list(result['results']),list(runner.SMOKES))

    def test_failed_child_prevents_unstarted_work_without_retry(self):
        names=[]; hold=threading.Event()
        def child(out,lease,review,deadline):
            names.append(lease['lane'])
            if lease['lane']=='smoke-b2': return dict(status='FAILED')
            hold.wait(.2)
            return dict(status='PASSED')
        with patch.object(runner,'child',side_effect=child):
            result=runner.run_wave(Path('unused-inert-wave'),runner.SMOKES,{},b'')
        self.assertEqual(result['status'],'FAILED')
        self.assertEqual(len(names),3); self.assertEqual(len(set(names)),3)
        self.assertEqual(sum(r['status']=='NOT_LAUNCHED' for r in result['results'].values()),2)

    def test_inherited_cleanup_failure_always_closes_job(self):
        class Job:
            closed=False
            def accounting(self): return (0,1,1)
            def terminate(self): return False
            def close(self): self.closed=True
        job=Job(); failures=[]
        with self.assertRaises(RuntimeError): runner.inherited.close_tree(job,None,failures.append)
        self.assertTrue(job.closed); self.assertEqual(len(failures),1)
        self.assertFalse(failures[0]['terminal_zero_proven'])
        self.assertNotIn('numpy',sys.modules)
        self.assertNotIn('anysolver',sys.modules)


if __name__=='__main__': unittest.main()
