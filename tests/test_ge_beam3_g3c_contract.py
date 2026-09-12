"""Standard-library-only design checks; zero mechanical cases are executed."""
import ast
from fractions import Fraction
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('g3c_contract',ROOT/'scripts/audit_ge_beam3_g3c_contract.py')
a=importlib.util.module_from_spec(spec); spec.loader.exec_module(a)


class G3cContractTests(unittest.TestCase):
    def fixture(self): return a.strict(a.text(ROOT/a.FIXTURES))

    def test_complete_source_and_payload_authority(self):
        result=a.audit()
        self.assertEqual(result['status'],'CONTRACT_STATIC_ONLY_NOT_QUALIFICATION')
        self.assertEqual((result['graphs'],result['graph_variants']),(5,25))

    def test_strict_json_and_determinism(self):
        for raw in (b'{"a":1,"a":2}\n',b'{"a":NaN}\n',b'{"a":Infinity}\n',b'{"a":1}'):
            with self.subTest(raw=raw),self.assertRaises(ValueError): a.strict(raw)
        value=self.fixture()
        self.assertEqual(a.canonical(a.strict(a.canonical(value))),a.canonical(value))

    def test_fixture_mutations_reject(self):
        for kind in ('drop_graph','alias','midpoint','frame','adapter','qualification','history','normal','component','material_extra','program_extra','negative_omission','bool_modulus','bool_connectivity','bool_fixed','bool_load','bool_master','bool_slave','extra'):
            value=deepcopy(self.fixture()); g=value['graphs'][0]
            if kind=='drop_graph': value['graphs'].pop()
            elif kind=='alias': g['nodes'][1][0]=g['nodes'][0][0]
            elif kind=='midpoint': g['nodes'][1][1][0]=.25
            elif kind=='frame': g['joints'][0]['master_frame'][0][0]=-1
            elif kind=='adapter': g['joints'][0]['adapter']='G3C_NATIVE_Q4_POSE_V1'
            elif kind=='qualification': g['qualification']=True
            elif kind=='history': value['programs']['load_factors'].pop()
            elif kind=='normal': value['definitions']['shell']['reference_normal']=[0,0,-1]
            elif kind=='component': g['fixed_nodes']=[]
            elif kind=='material_extra': value['definitions']['native']['extra']=1
            elif kind=='program_extra': value['programs']['extra']=1
            elif kind=='negative_omission': value['negative_cases'].pop()
            elif kind=='bool_modulus': value['definitions']['native']['E']=True
            elif kind=='bool_connectivity': g['elements'][0]['nodes'][0]=True
            elif kind=='bool_fixed': g['fixed_nodes'][0]=True
            elif kind=='bool_load': g['load_node']=True
            elif kind=='bool_master': g['joints'][0]['master']=True
            elif kind=='bool_slave': g['joints'][0]['slave']=True
            else: g['unregistered']=True
            with self.subTest(kind=kind),self.assertRaises(ValueError): a.validate_fixtures(value)

    def test_source_auditor_is_inert(self):
        tree=ast.parse((ROOT/'scripts/audit_ge_beam3_g3c_contract.py').read_bytes())
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                self.assertTrue(all(v.name.split('.')[0] in sys.stdlib_module_names for v in node.names))
            elif isinstance(node,ast.ImportFrom):
                self.assertIn(node.module.split('.')[0],sys.stdlib_module_names)
            elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                self.assertNotIn(node.func.id,('eval','exec','__import__','compile'))

    def test_joint_incidence_and_eccentricity(self):
        for g in self.fixture()['graphs']:
            points=dict(g['nodes'])
            self.assertEqual(len(g['joints']),8 if g['id']=='J_MULTIFAMILY_LOOP' else 2)
            for j in g['joints']:
                self.assertNotEqual(points[j['master']],points[j['slave']])
                self.assertEqual(points[j['master']][2]-points[j['slave']][2],.125)
                if j['id']%2==0:
                    self.assertNotEqual(j['master_frame'],j['slave_frame'])

    def test_limits_and_separate_acceptance(self):
        self.assertEqual(a.LIMITS['child_seconds'],600)
        self.assertEqual(a.LIMITS['wave_seconds'],1800)
        self.assertEqual(a.LIMITS['max_workers'],3)
        self.assertFalse(a.LIMITS['automatic_retry'])
        for g in self.fixture()['graphs']:
            self.assertFalse(g['qualification'])
            self.assertFalse(g['reference_only'])

    def test_source_equation_principal_mean_counterexample(self):
        # Exact pi-unit source reconstruction, NOT production execution.
        delta=Fraction(1,10000)
        def principal(x): return (x+1)%2-1
        for angles in ((-delta,delta),(-2*delta,delta,delta)):
            self.assertEqual(sum(angles),0)
            self.assertLess(max(angles)-min(angles),Fraction(9,10))
            observed=sum(principal(1+x) for x in angles)/len(angles)
            self.assertNotEqual((observed-1)%2,0)
            self.assertEqual(observed,0 if len(angles)==2 else -Fraction(1,3))


if __name__=='__main__': unittest.main()
