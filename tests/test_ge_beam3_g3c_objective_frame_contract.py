"""Inert direct-anchor equation tests, not production mechanics qualification."""
import ast
from copy import deepcopy
from fractions import Fraction as F
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('frame_audit',ROOT/'scripts/audit_ge_beam3_g3c_objective_frame.py')
a=importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
I=[[F(i==j) for j in range(3)] for i in range(3)]
def T(m): return [list(r) for r in zip(*m)]
def mm(a,b): return [[sum(x*y for x,y in zip(r,c)) for c in zip(*b)] for r in a]
def mv(m,v): return [sum(x*y for x,y in zip(r,v)) for r in m]
def sub(a,b): return [x-y for x,y in zip(a,b)]
def add(a,b): return [x+y for x,y in zip(a,b)]
def mean(rows): return [sum(v)/len(rows) for v in zip(*rows)]
def cross(a,b): return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def rx(c,s): return [[F(1),F(0),F(0)],[F(0),c,-s],[F(0),s,c]]
def ry(c,s): return [[c,F(0),s],[F(0),F(1),F(0)],[-s,F(0),c]]
W=mm(rx(F(3,5),F(4,5)),ry(F(5,13),F(12,13)))
V=rx(F(15,17),F(8,17))

def coordinates(ref,x,q,anchor):
    # Independently reconstruct VALUES only. Compare relative rotation
    # matrices; their unique admitted Logs inherit these exact equalities.
    rt=T(q[anchor]); rc,xc=mean(ref),mean(x)
    return ([sub(mv(rt,sub(v,xc)),sub(v0,rc)) for v0,v in zip(ref,x)],
            [mm(rt,qi) for qi in q])

def specimen(n):
    ref=[[F(i),F(0),F(0)] for i in range(n)]
    x=[[F(i)+F(1,10),F(i*i,50),F(-i,20)] for i in range(n)]
    q=[I,V] if n==2 else [V,I,W]
    return ref,x,q,0 if n==2 else 1

class DirectAnchorContractTests(unittest.TestCase):
    def test_complete_source_and_payload_authority(self):
        self.assertEqual(a.audit()['status'],'EQUATION_DESIGN_ONLY')

    def test_strict_canonical_bytes(self):
        for raw in (b'{"a":1,"a":2}\n',b'{"a":NaN}\n',b'{"a":Infinity}\n',b'{}'):
            with self.subTest(raw=raw),self.assertRaises(ValueError): a.strict(raw)
        value=a.strict(a.read(a.CONTRACT))
        self.assertEqual(a.canonical(value),a.read(a.CONTRACT))

    def test_mutated_authority_rejects(self):
        for kind in ('anchor','bool_anchor','limit','policy','admission','source','inventory'):
            c=deepcopy(a.strict(a.read(a.CONTRACT)))
            if kind=='anchor': c['anchors'][0][2]=102
            elif kind=='bool_anchor': c['anchors'][0][1]=True
            elif kind=='limit': c['limits']['child_seconds']=601
            elif kind=='policy': c['policy']='legacy'
            elif kind=='admission': c['admission']['G3_complete']=True
            elif kind=='source': c['sources'].pop()
            else: c['next_tests'].pop()
            with self.subTest(kind=kind),self.assertRaises(ValueError): a.validate(c)

    def test_exact_common_motion_equations(self):
        rotations=(I,W,rx(F(-1),F(0)),mm(W,rx(F(-1),F(0))))
        shift=[F(2),F(-3),F(1)]
        for n in (2,3):
            ref,x,q,anchor=specimen(n); expected=coordinates(ref,x,q,anchor)
            for rotation in rotations:
                moved=[add(mv(rotation,v),shift) for v in x]
                changed=[mm(rotation,qi) for qi in q]
                self.assertEqual(coordinates(ref,moved,changed,anchor),expected)
                rigid=[add(mv(rotation,v),shift) for v in ref]
                dt,dq=coordinates(ref,rigid,[rotation]*n,anchor)
                self.assertEqual(dt,[[F(0)]*3 for _ in ref]); self.assertEqual(dq,[I]*n)

    def test_exact_global_coordinate_reexpression(self):
        shift=[F(2),F(-3),F(1)]
        for n in (2,3):
            ref,x,q,anchor=specimen(n); dt,dq=coordinates(ref,x,q,anchor)
            change=lambda rows:[add(mv(W,v),shift) for v in rows]
            result=coordinates(change(ref),change(x),[mm(mm(W,qi),T(W)) for qi in q],anchor)
            self.assertEqual(result,([mv(W,v) for v in dt],[mm(mm(W,v),T(W)) for v in dq]))

    def test_exact_physical_anchor_reversal(self):
        for n in (2,3):
            ref,x,q,anchor=specimen(n); dt,dq=coordinates(ref,x,q,anchor)
            result=coordinates(ref[::-1],x[::-1],q[::-1],n-1-anchor)
            self.assertEqual(result,(dt[::-1],dq[::-1]))
        ref,x,q,anchor=specimen(2)
        self.assertNotEqual(coordinates(ref,x,q,0),coordinates(ref,x,q,1))

    def test_exact_infinitesimal_rigid_removal(self):
        shift=[F(1,3),F(-2,5),F(3,7)]; omega=[F(-1,5),F(2,7),F(1,4)]
        for n in (2,3):
            ref,_,_,anchor=specimen(n); rc=mean(ref)
            delta=[add(shift,cross(omega,p)) for p in ref]; dc=mean(delta)
            local=[sub(sub(u,dc),cross(omega,sub(p,rc))) for p,u in zip(ref,delta)]
            self.assertEqual(local,[[F(0)]*3 for _ in ref])
            self.assertEqual([sub(omega,omega) for _ in ref],[[F(0)]*3 for _ in ref])

    def test_auditor_has_only_standard_library_imports(self):
        for node in ast.walk(ast.parse(a.read('scripts/audit_ge_beam3_g3c_objective_frame.py'))):
            if isinstance(node,ast.Import):
                self.assertTrue(all(v.name.split('.')[0] in sys.stdlib_module_names for v in node.names))
            elif isinstance(node,ast.ImportFrom):
                self.assertIn(node.module.split('.')[0],sys.stdlib_module_names)
            elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                self.assertNotIn(node.func.id,('eval','exec','__import__','compile'))

if __name__=='__main__': unittest.main()
