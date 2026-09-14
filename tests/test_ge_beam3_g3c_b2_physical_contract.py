"""Independent exact source-equation audit; no production/numerical imports."""
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'docs/reference_cases/ge_beam3_g3c_b2_physical_contract_v1.json'

def canonical(v):
    return (json.dumps(v,sort_keys=True,separators=(',', ':'),allow_nan=False)+'\n').encode()

def strict(raw):
    def pairs(p):
        if len(dict(p))!=len(p): raise ValueError('duplicate')
        return dict(p)
    def reject(v): raise ValueError('nonfinite')
    v=json.loads(raw,object_pairs_hook=pairs,parse_constant=reject)
    if canonical(v)!=raw: raise ValueError('noncanonical')
    return v

def fixtures():
    return [{k:F(v) if k!='id' else v for k,v in x.items()} for x in strict(PATH.read_bytes())['fixtures']]

def mm(a,b):
    return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]

def tr(a): return list(map(list,zip(*a)))
def eye(n): return [[F(i==j) for j in range(n)] for i in range(n)]

def blocks(L,EI,S):
    # Independently integrate M1=t-1, M2=t and constant V=1/L over t=[0,1].
    flex=[[L/(3*EI)+1/(S*L),-L/(6*EI)+1/(S*L)],
          [-L/(6*EI)+1/(S*L),L/(3*EI)+1/(S*L)]]
    p=L/(6*EI)+2/(S*L); m=L/(2*EI)
    inv=[[(1/p+1/m)/2,(1/p-1/m)/2],[(1/p-1/m)/2,(1/p+1/m)/2]]
    return flex,inv,p,m

def basic(L):
    B=[[F(0) for j in range(12)] for i in range(6)]
    B[0][0],B[0][6]=-F(1),F(1);B[1][3],B[1][9]=-F(1),F(1)
    for row,rot in ((2,4),(3,10)):
        B[row][2],B[row][8],B[row][rot]=-1/L,1/L,F(1)
    for row,rot in ((4,5),(5,11)):
        B[row][1],B[row][7],B[row][rot]=1/L,-1/L,F(1)
    return B

class ContractTests(unittest.TestCase):
    def test_contract_authority(self):
        c=strict(PATH.read_bytes())
        for key in ('source','proposal'):
            b=(ROOT/c[key]['path']).read_bytes().replace(b'\r\n',b'\n')
            self.assertEqual(sha256(b).hexdigest(),c[key]['sha256'])
        self.assertFalse(c['boundary']['full_g3c_qualified'])
        self.assertEqual(c['limits']['child_seconds'],600)

    def test_exact_flexibility_integrals(self):
        # Exact monomial integrals independently reconstruct both polynomial entries.
        integ=lambda p:sum(v/F(i+1) for i,v in enumerate(p))
        for x in fixtures():
            L=x['L'];G=x['E']/(2*(1+x['nu']))
            for inertia,k in ((x['Iy'],x['kz']),(x['Iz'],x['ky'])):
                EI=x['E']*inertia;S=G*x['A']*k;f,_,_,_=blocks(L,EI,S)
                self.assertEqual(f[0][0],L/EI*integ([1,-2,1])+1/(S*L))
                self.assertEqual(f[0][1],L/EI*integ([0,-1,1])+1/(S*L))

    def test_two_sided_inverse_and_positive_blocks(self):
        for x in fixtures():
            G=x['E']/(2*(1+x['nu']))
            for i,k in ((x['Iy'],x['kz']),(x['Iz'],x['ky'])):
                f,b,p,m=blocks(x['L'],x['E']*i,G*x['A']*k)
                self.assertGreater(p,0); self.assertGreater(m,0)
                self.assertEqual(mm(f,b),eye(2));self.assertEqual(mm(b,f),eye(2))

    def test_clamp_physical_energy_and_legacy_distinction(self):
        for x in fixtures()[:3]:
            L=x['L'];EI=x['E']*x['Iz'];S=x['E']/(2*(1+x['nu']))*x['A']*x['ky']
            f,k,_,_=blocks(L,EI,S);v=[[-F(1,100)/L],[-F(1,100)/L]]
            q=mm(k,v);U=mm(tr(v),q)[0][0]/2
            self.assertEqual(mm(mm(tr(q),f),q)[0][0]/2,U)
            old=6*EI*F(1,100)**2/(L**3*(1+12*EI/max(S*L**2,F('1e-12'))))
            if x['id']=='CLAMP': self.assertNotEqual(U,old)
            else: self.assertEqual(U,old)

    def test_reference_rank_and_rigid_modes(self):
        for x in fixtures():
            B=basic(x['L']); a=[r[:] for r in B]; rank=0
            for col in range(12):
                pivot=next((i for i in range(rank,6) if a[i][col]),None)
                if pivot is None:continue
                a[rank],a[pivot]=a[pivot],a[rank];p=a[rank][col];a[rank]=[v/p for v in a[rank]]
                for i in range(6):
                    if i!=rank:
                        s=a[i][col];a[i]=[v-s*w for v,w in zip(a[i],a[rank])]
                rank+=1
            self.assertEqual(rank,6)
            R=[[F(0) for j in range(6)] for i in range(12)]
            for n in (0,1):
                for j in range(3):R[6*n+j][j]=1;R[6*n+j+3][j+3]=1
            R[7][5]=x['L'];R[8][4]=-x['L']
            self.assertEqual(mm(B,R),[[0]*6 for _ in range(6)])

    def test_units_and_range(self):
        c=strict(PATH.read_bytes());x=fixtures()[0];L=x['L'];EI=x['E']*x['Iz'];S=x['E']/(2*(1+x['nu']))*x['A']
        f,k,_,_=blocks(L,EI,S)
        for exponent in c['range']['rigidity_power_two_exponents']:
            scale=F(2)**exponent;fs,ks,_,_=blocks(L,EI*scale,S*scale)
            self.assertEqual(fs,[[v/scale for v in r] for r in f])
            self.assertEqual(ks,[[v*scale for v in r] for r in k])
        for unit in map(F,c['range']['unit_length_factors']):
            for force in map(F,c['range']['unit_force_factors']):
                fs,ks,_,_=blocks(L*unit,EI*force*unit**2,S*force)
                self.assertEqual(ks,[[v*force*unit for v in r] for r in k])

    def test_canonical_duplicate_and_nonfinite_rejection(self):
        for raw in (b'{"a":1,"a":2}\n',b'{"a":NaN}\n',b'{"a":Infinity}\n',b'{ "a":1}\n'):
            with self.assertRaises(ValueError):strict(raw)

if __name__=='__main__': unittest.main()
