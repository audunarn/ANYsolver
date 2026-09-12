"""Inert implementation checks; intentionally imports no anysolver/NumPy."""
import ast
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import ge_beam3_g3c_stable_map as mapping
import run_ge_beam3_g3c_stable as runner


class ImplementationTests(unittest.TestCase):
    def test_exact_generated_sources(self):
        contract = mapping.strict(mapping.normalized(ROOT/mapping.MAP))
        self.assertEqual(mapping.audit(contract, implemented=True)['copies'], 13)

    def test_no_numerical_imports_during_preflight(self):
        self.assertNotIn('numpy', sys.modules)
        self.assertNotIn('anysolver', sys.modules)
        for path in runner.EXTRA:
            if path.endswith('.py'):
                ast.parse(mapping.normalized(ROOT/path))

    def test_review_fail_closed(self):
        candidate = {'commit':'test', 'tree':'tree'}
        frozen = {'file': {'bytes':1, 'sha256':'0'*64}}
        review = dict(decision='ACCEPTED_G3C_STABLE_IMPLEMENTATION_FOR_BOUNDED_DEVELOPMENT',
            findings=[], reviewer={'independent':True}, subject_commit='test',
            scope=dict(subject_tree='tree', source_map_sha256=runner.MAP_SHA,
                       inputs_sha256=runner.sha256(runner.canonical(frozen)).hexdigest()))
        raw = runner.canonical(review)
        runner.verify_review(raw, runner.sha256(raw).hexdigest(), candidate, frozen)
        for key, value in (('findings', ['unresolved']), ('subject_commit', 'foreign'),
                           ('decision', 'UNREVIEWED')):
            changed = copy.deepcopy(review); changed[key] = value
            raw = runner.canonical(changed)
            with self.assertRaises(ValueError):
                runner.verify_review(raw, runner.sha256(raw).hexdigest(), candidate, frozen)
        with self.assertRaises(ValueError):
            runner.verify_review(runner.canonical(review), '0'*64, candidate, frozen)

    def test_closed_inventory_and_limits(self):
        tree = ast.parse(mapping.normalized(ROOT/runner.GUARD))
        tests = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
        self.assertEqual(len(tests), runner.EXPECTED_NODES['guard'])
        self.assertEqual(runner.EXPECTED_NODES, {'guard':10, 'diagnostic':1, 'bridge':18})
        text = mapping.normalized(ROOT/'scripts/run_ge_beam3_g3c_stable.py').decode()
        for limit in ('now-start >= 600', 'now-last >= 120', '24*1024**3'):
            self.assertIn(limit, text)


if __name__ == '__main__':
    unittest.main()
