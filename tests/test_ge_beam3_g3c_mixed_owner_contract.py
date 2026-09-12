"""Inert contract/schema tests, not tests of an implemented graph owner."""
import ast
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mixed_audit', ROOT/'scripts/audit_ge_beam3_g3c_mixed_owner.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

class MixedOwnerContractTests(unittest.TestCase):
    def test_full_source_payload_and_exact_extent(self):
        self.assertEqual(a.audit(), dict(status='DESIGN_ONLY', mechanics_executed=False,
            sources=len(a.SOURCES), graph_variants=25, physical_recovery_complete=False))

    def test_strict_duplicates_nonfinite_encoding_and_bounds(self):
        for raw in (b'{"x":1,"x":2}\n', b'{"x":NaN}\n', b'{"x":Infinity}\n',
                    b'{"x":1e999}\n', b'{ }\n', b'{}', b'{}\r\n', b'{}\n{}\n', b' '*(4*1024**2+1)):
            with self.subTest(raw=raw[:40]), self.assertRaises(ValueError):
                a.strict(raw)
        raw = a.read(a.CONTRACT)
        self.assertEqual(raw, a.canonical(a.strict(raw)))

    def test_every_frozen_policy_schema_and_scope_mutation(self):
        original = a.strict(a.read(a.CONTRACT))
        for key in a.fixed():
            c = deepcopy(original); c[key] = None
            with self.subTest(key=key), self.assertRaises(ValueError): a.validate(c)
        for object_name, fields in a.LAYOUTS.items():
            for field in fields:
                c = deepcopy(original); del c['layouts'][object_name][field]
                with self.subTest(obj=object_name, field=field), self.assertRaises(ValueError): a.validate(c)
        for key in a.ADMISSION:
            for bad in (True, 0, 0.0):
                c = deepcopy(original); c['admission'][key] = bad
                with self.subTest(flag=key, bad=bad), self.assertRaises(ValueError): a.validate(c)

    def test_hash_inventory_and_type_mutations(self):
        original = a.strict(a.read(a.CONTRACT))
        mutations = []
        c = deepcopy(original); c['sources'].pop(); mutations.append(c)
        c = deepcopy(original); c['sources'][0] = None; mutations.append(c)
        c = deepcopy(original); c['sources'][0]['bytes'] = True; mutations.append(c)
        c = deepcopy(original); c['sources'][0]['sha256'] = 'g'*64; mutations.append(c)
        c = deepcopy(original); c['sources'][0]['blob'] = '1'*39; mutations.append(c)
        c = deepcopy(original); c['payloads'].pop(a.PLAN); mutations.append(c)
        c = deepcopy(original); c['payloads'][a.PLAN]['bytes'] = 0; mutations.append(c)
        for c in mutations:
            with self.assertRaises(ValueError): a.validate(c)
        for path in (a.SOURCES[3], a.SOURCES[12], a.PLAN):
            original_read = a.read
            def mutated(name):
                return original_read(name)+(b' ' if name == path else b'')
            with self.subTest(path=path), patch.object(a, 'read', mutated), self.assertRaises(ValueError): a.audit()

    def test_independent_fixture_counts_and_nontrivial_port_authority(self):
        f = a.strict(a.read('docs/reference_cases/ge_beam3_g3c_fixtures_v1.json'))
        self.assertEqual([(len(g['elements']),len(g['nodes']),len(g['joints']),
            6*(len(g['fixed_nodes'])+len(g['joints']))) for g in f['graphs']],
            [(3,8,2,24),(3,9,2,24),(3,10,2,24),(3,9,2,24),(6,17,8,54)])
        self.assertEqual(f['variants'], ['BASE','SHUFFLED_INSERTION','RENUMBERED',
                                       'CONNECTIVITY_REVERSED','PROPER_GLOBAL_TRANSFORM'])
        for g in f['graphs']:
            for j in g['joints']:
                self.assertEqual(j['master_frame'] == j['slave_frame'], bool(j['id'] % 2))
        self.assertEqual(f['programs']['directional_steps'], [1e-4,1e-5,1e-6])
        self.assertEqual(f['programs']['force_scales'], [.01,1,10])
        self.assertEqual(f['programs']['load_factors'], [0,.5,1,.25,0])

    def test_no_cyclic_state_hash_or_token_serialization(self):
        self.assertNotIn('state_sha256', a.LAYOUTS['state'])
        self.assertNotIn('entry_sha256', a.LAYOUTS['entry'])
        self.assertNotIn('accepted_entry_sha256', a.LAYOUTS['state'])
        for fields in a.LAYOUTS.values():
            self.assertTrue(set(fields).isdisjoint({'token','owner','store','pickle','module','cache'}))
        self.assertEqual(a.LAYOUTS['native_full']['jacobian'], 'f64[42,42]')
        self.assertEqual(a.LAYOUTS['native_response']['lift'], 'f64[24,18]')

    def test_imports_are_stdlib_only_and_no_dynamic_execution(self):
        tree = ast.parse(a.read('scripts/audit_ge_beam3_g3c_mixed_owner.py'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue(all(v.name.split('.')[0] in sys.stdlib_module_names for v in node.names))
            if isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0)
                self.assertIn(node.module.split('.')[0], sys.stdlib_module_names)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {'eval','exec','__import__'})

if __name__ == '__main__':
    unittest.main()
