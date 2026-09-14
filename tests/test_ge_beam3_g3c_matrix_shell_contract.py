"""Inert equation-authority tests. Not a shell mechanics result."""
import ast
from copy import deepcopy
from fractions import Fraction as F
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('shell_audit', ROOT/'scripts/audit_ge_beam3_g3c_matrix_shell.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)

def add(*polys):
    out = [F(0)] * max(map(len, polys))
    for poly in polys:
        for i, value in enumerate(poly):
            out[i] += value
    return trim(out)

def trim(poly):
    while len(poly) > 1 and not poly[-1]:
        poly.pop()
    return poly

def scale(poly, value):
    return trim([F(value)*x for x in poly])

def mul(p, q):
    out = [F(0)]*(len(p)+len(q)-1)
    for i, x in enumerate(p):
        for j, y in enumerate(q):
            out[i+j] += x*y
    return trim(out)

def derivative(poly):
    return trim([i*x for i, x in enumerate(poly)][1:] or [F(0)])

class MatrixShellContractTests(unittest.TestCase):
    def test_complete_source_and_payload_authority(self):
        self.assertEqual(a.audit(), dict(status='EQUATION_DESIGN_ONLY',
            mechanics_executed=False, source_count=len(a.SOURCES),
            physical_recovery_complete=False))

    def test_strict_canonical_json(self):
        for raw in (b'{"a":1,"a":2}\n', b'{"a":NaN}\n', b'{"a":1e999}\n',
                    b'{"a":Infinity}\n', b'{}', b'{ }\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                a.strict(raw)
        self.assertEqual(a.canonical(a.strict(a.read(a.CONTRACT))), a.read(a.CONTRACT))

    def test_frozen_channels_scope_inventory_and_limits(self):
        original = a.strict(a.read(a.CONTRACT))
        mutations = []
        for field in ('channels', 'next_tests', 'sources', 'extent'):
            changed = deepcopy(original); changed[field].pop(); mutations.append(changed)
        for flag in original['admission']:
            for value in (True, 0, 0.0):
                changed = deepcopy(original); changed['admission'][flag] = value; mutations.append(changed)
        for value in (1, True, -1.0):
            changed = deepcopy(original); changed['channels'][-1][1] = value; mutations.append(changed)
        changed = deepcopy(original); changed['limits']['child_seconds'] = 601; mutations.append(changed)
        changed = deepcopy(original); changed['environment_sha256'] = '0'*64; mutations.append(changed)
        changed = deepcopy(original); changed['sources'][0]['bytes'] = True; mutations.append(changed)
        changed = deepcopy(original); changed['sources'][0]['sha256'] = 'g'*64; mutations.append(changed)
        for i, changed in enumerate(mutations):
            with self.subTest(mutation=i), self.assertRaises(ValueError):
                a.validate(changed)

    def test_hash_mutations_fail_audit(self):
        original_read = a.read
        for path in (a.SOURCES[0], a.SOURCES[10], a.PLAN, a.ASSESSMENT):
            def changed(name):
                raw = original_read(name)
                return raw+b' ' if name == path else raw
            with self.subTest(path=path), patch.object(a, 'read', changed), self.assertRaises(ValueError):
                a.audit()

    def test_exact_signed_potential_first_second_variations(self):
        # Independent univariate polynomial algebra, no source mechanics/AD.
        # e(t)=Bm*y(t), p(t)=Gw*y(t), arbitrary affine paths.
        e = [[F(1,7), F(2,5)], [F(-2,9), F(3,7)], [F(1,3), F(-4,11)]]
        p = [[F(1,5), F(-3,8)], [F(-2,7), F(5,9)]]
        n = [scale(mul(p[0], p[0]), F(1,2)), scale(mul(p[1], p[1]), F(1,2)), mul(*p)]
        ev = [add(x, y) for x, y in zip(e, n)]
        C = [[F(4), F(1), F(0)], [F(1), F(3), F(0)], [F(0), F(0), F(2)]]
        matvec = lambda v: [add(*(scale(v[j], C[i][j]) for j in range(3))) for i in range(3)]
        Nv, Nl = matvec(ev), matvec(e)
        product = lambda x, y: add(*(mul(v, w) for v, w in zip(x, y)))
        energy = scale(add(product(ev, Nv), scale(product(e, Nl), -1)), F(1,2))
        force = add(product(list(map(derivative, ev)), Nv),
                    scale(product(list(map(derivative, e)), Nl), -1))
        tangent = add(product(list(map(derivative, ev)), matvec(list(map(derivative, ev)))),
                      scale(product(list(map(derivative, e)), matvec(list(map(derivative, e)))), -1),
                      product([derivative(derivative(v)) for v in ev], Nv))
        self.assertEqual(derivative(energy), force)
        self.assertEqual(derivative(force), tangent)
        self.assertNotEqual(product([derivative(derivative(v)) for v in ev], Nv), [F(0)])

    def test_exact_single_resultant_is_not_work_equivalent(self):
        # Algebraic counterexample to conflating mixed baseline with one Beff.
        # This is NOT a measured Q4 fixture or scientific NO-GO.
        Bm, Bnl, Nm, Nl, Nv = F(2), F(3), F(7), F(5), F(11)
        correct = Bm*Nm+(Bm+Bnl)*Nv-Bm*Nl
        conflated = (Bm+Bnl)*(Nm+Nv-Nl)
        self.assertEqual(conflated-correct, Bnl*(Nm-Nl))
        self.assertNotEqual(conflated, correct)

    def test_exact_linear_terms_cancel_without_changing_source(self):
        Kqualified, Klinear, Kother, d = F(17,3), F(4,7), F(5,11), F(2,13)
        vk_energy, vk_force, vk_tangent = F(3,5), F(7,11), F(9,13)
        correction = Kqualified-Klinear-Kother
        self.assertEqual(vk_energy+(Kother+correction)*d*d/2,
                         Kqualified*d*d/2+vk_energy-Klinear*d*d/2)
        self.assertEqual(vk_force+(Kother+correction)*d,
                         Kqualified*d+vk_force-Klinear*d)
        self.assertEqual(vk_tangent+Kother+correction,
                         Kqualified+vk_tangent-Klinear)

    def test_no_mechanics_imports_or_dynamic_execution(self):
        for node in ast.walk(ast.parse(a.read('scripts/audit_ge_beam3_g3c_matrix_shell.py'))):
            if isinstance(node, ast.Import):
                self.assertTrue(all(x.name.split('.')[0] in sys.stdlib_module_names for x in node.names))
            elif isinstance(node, ast.ImportFrom):
                self.assertIn(node.module.split('.')[0], sys.stdlib_module_names)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, ('eval', 'exec', '__import__', 'compile'))

if __name__ == '__main__':
    unittest.main()
