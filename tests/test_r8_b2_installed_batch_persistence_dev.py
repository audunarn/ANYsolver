"""Focused stdlib-only controls for changed installed batch harness contracts."""
import importlib.util
import ast
import json
from pathlib import Path
import sys
import unittest

path=Path(__file__).resolve().parents[1]/'scripts/r8_b2_installed_batch_persistence_dev.py'
spec=importlib.util.spec_from_file_location('batch_persistence_control',path)
h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h)


class Controls(unittest.TestCase):
    def test_original_gate_is_stricter_than_absolute_product_floor(self):
        result=h.work_predicate(1e-6+5e-13,1e-6)
        self.assertFalse(result['original_work_pass']);self.assertTrue(result['product_work_pass'])

    def test_original_gate_true_and_zero_work_has_no_new_floor(self):
        self.assertTrue(h.work_predicate(1.+5e-9,1.)['original_work_pass'])
        self.assertFalse(h.work_predicate(1e-20,0.)['original_work_pass'])
        self.assertTrue(h.work_predicate(0.,0.)['original_work_pass'])

    def test_nonfinite_failure_remains_serializable(self):
        result=h.work_predicate(float('inf'),1.)
        self.assertFalse(result['original_work_pass'])
        json.dumps(h.json_safe(result),allow_nan=False)
        self.assertEqual(h.json_safe({'gap':[float('nan')]}),{'gap':['nan']})

    def test_counts_and_reuse(self):
        self.assertTrue(h.counter_predicate(1,111,111,111,True))
        for args in [(2,111,0,111,True),(1,110,0,111,True),(1,111,112,111,True),
                     (1,111,-1,111,True),(1,111,0,111,False)]:
            self.assertFalse(h.counter_predicate(*args))

    def test_governing_case_and_first_tie(self):
        low,high=h.extrema([('case-1',0.),('case-2',-2.),('case-3',-2.),('case-4',3.)])
        self.assertEqual(low,('case-2',-2.));self.assertEqual(high,('case-4',3.))
        self.assertEqual(h.extrema([('first',0.),('second',0.)]),(('first',0.),('first',0.)))

    def test_refuse_nonfinite_and_empty_envelopes(self):
        for values in [[],[('bad',float('nan'))],[('bad',float('inf'))]]:
            with self.assertRaises(RuntimeError):h.extrema(values)

    def test_public_canonical_payload_bytes_and_text(self):
        payload=b'{"schema":"experimental"}'
        self.assertIs(h.payload_bytes(payload),payload)
        self.assertEqual(h.payload_bytes(payload.decode('utf-8')),payload)
        for invalid in [None,bytearray(payload),{},17]:
            with self.assertRaises(RuntimeError):h.payload_bytes(invalid)

    def test_beam_rich_uses_registered_subdivision_builder(self):
        self.assertEqual(h.builder_path('full'),h.BUILDER)
        self.assertEqual(h.builder_path('beam'),h.BEAM_BUILDER)
        tree=ast.parse(h.BEAM_BUILDER.read_text())
        settings=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='settings')
        self.assertIn("'beam_rich'",ast.unparse(settings))
        self.assertIn('beam_segments_per_shell=5',ast.unparse(settings))
        # Execute ONLY this source-derived stdlib metadata function; no module
        # imports, material/operator evaluation, assembly or solve occurs.
        namespace={};exec(compile(ast.Module(body=[settings],type_ignores=[]),str(h.BEAM_BUILDER),'exec'),namespace)
        config=namespace['settings']('beam_rich',100)
        self.assertEqual(config,dict(nx=20,ny=20,line_rows=tuple(range(0,20,2)),
            patch_x=tuple(range(1,20,2)),beam_segments_per_shell=5,cases=100))
        frozen=ast.parse(h.BUILDER.read_text())
        old=next(n for n in frozen.body if isinstance(n,ast.FunctionDef) and n.name=='settings')
        namespace={};exec(compile(ast.Module(body=[old],type_ignores=[]),str(h.BUILDER),'exec'),namespace)
        full=namespace['settings']('large',100)
        self.assertEqual((full['nx'],full['ny'],full['cases']),(100,100,100))
        with self.assertRaises(RuntimeError):h.builder_path('other')


if __name__=='__main__':unittest.main()
