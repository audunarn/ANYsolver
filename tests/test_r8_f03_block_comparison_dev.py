"""Independent bounded exact controls. PREPARED, NOT RUN under current slot hold."""
from fractions import Fraction as F
import hashlib
import json
from itertools import product
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import unittest
from scripts import r8_f03_block_comparison_dev as block
from scripts.r8_f03_finite_local_dev import ExactBudget,Unresolved


def sparse(matrix):
    return {(i,j):block.point(v)for i,row in enumerate(matrix)for j,v in enumerate(row)if v or i==j}


def direct(matrix,rhs):
    """Independent tiny oracle with elimination and back substitution; order<=6."""
    n=len(rhs)
    if n>6:raise ValueError('tiny independent oracle only')
    a=[list(row)+[rhs[i]]for i,row in enumerate(matrix)]
    for k in range(n):
        pivot=next(i for i in range(k,n)if a[i][k])
        a[k],a[pivot]=a[pivot],a[k]
        for i in range(k+1,n):
            factor=a[i][k]/a[k][k]
            for j in range(k,n+1):a[i][j]-=factor*a[k][j]
    x=[F()]*n
    for i in range(n-1,-1,-1):x[i]=(a[i][-1]-sum((a[i][j]*x[j]for j in range(i+1,n)),F()))/a[i][i]
    return x


def scalar_comparison(matrix,rhs,lower=True):
    n=len(rhs);x=[F()]*n
    for i in (range(n)if lower else range(n-1,-1,-1)):
        x[i]=(rhs[i]+sum((abs(v)*x[j]for j,v in enumerate(matrix[i])if j!=i),F()))/abs(matrix[i][i])
    return x


PROVENANCE={'pencil_identity':'exact small synthetic input','factor_identity':'exact signed original triangular factors',
            'residual_identity':'independent exact declared row magnitude','residual_coordinates':'Pr A Pc'}


class BlockControls(unittest.TestCase):
    def test_01_exact_three_coordinate_two_path_cancellation(self):
        l=[[F(1),F(),F()],[F(1),F(1),F()],[F(1),F(1),F(1)]];rhs=[F(1),F(),F()]
        actual=direct(l,rhs);scalar=scalar_comparison(l,rhs)
        self.assertEqual(actual,[F(1),F(-1),F()]);self.assertEqual(scalar,[F(1),F(1),F(2)])
        bound=block.block_triangular_bound(sparse(l),rhs,lower=True,width=3)
        self.assertEqual(bound['bound'],[F(1),F(1),F()])
        self.assertEqual(block.block_triangular_bound(sparse(l),rhs,lower=True,width=1)['bound'],scalar)

    def test_02_upper_two_path_cancellation(self):
        u=[[F(1),F(1),F(1)],[F(),F(1),F(1)],[F(),F(),F(1)]];rhs=[F(),F(),F(1)]
        self.assertEqual(direct(u,rhs),[F(),F(-1),F(1)])
        self.assertEqual(block.block_triangular_bound(sparse(u),rhs,lower=False,width=3)['bound'],[F(),F(1),F(1)])

    def test_03_asymmetric_negative_diagonals_and_fixed_permutations(self):
        l=[[F(-2),F(),F()],[F(1),F(3),F()],[F(-1),F(2),F(-4)]]
        u=[[F(2),F(-3),F(1)],[F(),F(-1),F(4)],[F(),F(),F(5)]]
        pr=[2,0,1];pc=[1,2,0];rhs=[F(1,32),F(1,64),F(1,16)]
        b=block.permuted_residual_rhs(rhs,pr,pc,block.exact_budget())
        r=block.lu_block_comparison(sparse(l),sparse(u),b,pr,pc,width=2,provenance=PROVENANCE)
        # Independent explicit original A with Pr A Pc=LU under these maps.
        a=[[F(1),F(-13),F(-2)],[F(6),F(-2),F(-4)],[F(-6),F(13),F(2)]]
        for signs in product((-1,1),repeat=3):
            original=[v*sign for v,sign in zip(rhs,signs)];permuted=[F()]*3
            for i,v in enumerate(original):permuted[pr[i]]=v
            y=direct(u,direct(l,permuted));x=[y[pc[i]]for i in range(3)]
            self.assertEqual(x,direct(a,original))
            for value,upper in zip(x,r['original_coordinate_bound']):self.assertLessEqual(abs(value),upper)
        self.assertGreaterEqual(F(r['q_upper']),r['q_exact'])
        for key in ('inertia','coercivity','physical_acceptance'):self.assertIsNone(r[key])
        self.assertFalse(r['qualification'])

    def test_04_interval_blocks_enclose_all_independent_corner_solves(self):
        center=[[F(2),F(),F()],[F(-1),F(3),F()],[F(2),F(-1),F(4)]]
        uncertain={(0,0):F(1,10),(1,0):F(1,20),(1,1):F(1,10),(2,0):F(1,20),(2,2):F(1,10)}
        entries=sparse(center)
        for key,r in uncertain.items():i,j=key;entries[key]=block.Band(center[i][j]-r,center[i][j]+r)
        rhs=[F(1,8),F(1,5),F(1,7)];r=block.block_triangular_bound(entries,rhs,lower=True,width=2)
        for choices in product((-1,1),repeat=len(uncertain)):
            actual=[list(row)for row in center]
            for ((i,j),radius),sign in zip(uncertain.items(),choices):actual[i][j]+=sign*radius
            for signs in product((-1,1),repeat=3):
                x=direct(actual,[v*sign for v,sign in zip(rhs,signs)])
                for value,upper in zip(x,r['bound']):self.assertLessEqual(abs(value),upper)
        self.assertTrue(any(d['diagonal_uncertainty_beta']>0 for d in r['diagnostics']))

    def test_05_missing_zero_singular_interval_singular_and_wrong_triangle_refuse(self):
        for entries in ({}, {(0,0):block.point(F())}, {(0,0):block.Band(F(-1),F(1))},
                        {(0,0):block.Band(F(),F(2))}):
            with self.assertRaises(Unresolved):block.block_triangular_bound(entries,[F(1)],lower=True)
        bad=sparse([[F(1),F(1)],[F(),F(1)]])
        with self.assertRaises(Unresolved):block.block_triangular_bound(bad,[F(1),F(1)],lower=True)
        with self.assertRaises(Unresolved):block.local_inverse([[F(1),F(1)],[F(1),F(1)]],[[F(),F()],[F(),F()]],block.exact_budget())

    def test_06_scalar_storage_rhs_and_local_shape_refuse(self):
        for value in (2**53+1,1,True,'1.0'):
            with self.assertRaises(Unresolved):block.binary64_point(value)
        for value in (float('inf'),float('nan'),1e-320):
            with self.assertRaises(Unresolved):block.binary64_point(value)
        for band in (block.Band(F(2),F(1)),block.Band(1.,1.)):
            with self.assertRaises(Unresolved):block.block_triangular_bound({(0,0):band},[F(1)],lower=True)
        for rhs in ([F(-1)],[1.],None):
            with self.assertRaises(Unresolved):block.block_triangular_bound({(0,0):block.point(F(1))},rhs,lower=True)
        with self.assertRaises(Unresolved):block.local_inverse([[F(1)]],[[F(-1)]],block.exact_budget())
        with self.assertRaises(Unresolved):block.local_inverse([[F(1),F()]],[[F()]],block.exact_budget())

    def test_07_dimension_block_fill_operation_and_bit_caps_refuse(self):
        for n,width in ((8001,1),(1,19),(0,1),(1,0),(True,1)):
            with self.assertRaises(Unresolved):block.partition(n,width)
        entries=sparse([[F(1)]])
        with patch.dict(block.CAPS,input_fill=0):
            with self.assertRaises(Unresolved):block.block_triangular_bound(entries,[F(1)],lower=True)
        with patch.dict(block.CAPS,block_row_fill=0):
            with self.assertRaises(Unresolved):block.block_triangular_bound(entries,[F(1)],lower=True)
        with self.assertRaises(Unresolved):block.block_triangular_bound(entries,[F(1)],lower=True,budget=ExactBudget(operation_cap=1))
        with self.assertRaises(Unresolved):block.block_triangular_bound({(0,0):block.point(F(2**100))},[F(1)],lower=True,budget=ExactBudget(bit_cap=32))
        for budget in (ExactBudget(operation_cap=block.CAPS['operations']+1),ExactBudget(bit_cap=block.CAPS['bits']+1)):
            with self.assertRaises(Unresolved):block.block_triangular_bound(entries,[F(1)],lower=True,budget=budget)

    def test_08_permutation_and_provenance_refusals(self):
        t=sparse([[F(1),F()],[F(),F(1)]]);rhs=[F(1),F(1)]
        for pr,pc in (([0,0],[0,1]),([0,1],[0]),([0.,1],[0,1])):
            with self.assertRaises(Unresolved):block.lu_block_comparison(t,t,rhs,pr,pc,provenance=PROVENANCE)
        for field in PROVENANCE:
            missing=dict(PROVENANCE);missing.pop(field)
            with self.assertRaises(Unresolved):block.lu_block_comparison(t,t,rhs,[0,1],[0,1],provenance=missing)
        wrong=dict(PROVENANCE,residual_coordinates='original A rows')
        with self.assertRaises(Unresolved):block.lu_block_comparison(t,t,rhs,[0,1],[0,1],provenance=wrong)

    def test_09_no_claim_that_coarse_blocks_always_improve(self):
        # Cancellation lies across the chosen block frontier, so both bounds coincide.
        t=[[F(1),F(),F()],[F(1),F(1),F()],[F(1),F(1),F(1)]];rhs=[F(1),F(),F()]
        coarse=block.block_triangular_bound(sparse(t),rhs,lower=True,width=2)['bound']
        self.assertEqual(coarse,scalar_comparison(t,rhs))
        r=block.lu_block_comparison(sparse(t),sparse([[F(1),F(),F()],[F(),F(1),F()],[F(),F(),F(1)]]),rhs,[0,1,2],[0,1,2],width=2,provenance=PROVENANCE)
        self.assertEqual(r['status'],'UNRESOLVED');self.assertEqual(r['q_exact'],F(2))

    def test_10_outward_underflow_overflow_and_zero_controls(self):
        unit=sparse([[F(1)]])
        for value in (F(2**2000),F(1,2**2000)):
            with self.assertRaises(Unresolved):block.lu_block_comparison(sparse([[value]]),unit,[F(1)],[0],[0],provenance=PROVENANCE)
        zero=block.lu_block_comparison(unit,unit,[F()],[0],[0],provenance=PROVENANCE)
        self.assertEqual(zero['q_exact'],0);self.assertEqual(zero['q_upper'],0.)
        r=block.lu_block_comparison(unit,unit,[F(1,10)],[0],[0],provenance=PROVENANCE)
        self.assertGreaterEqual(F(r['q_upper']),F(1,10))

    def test_11_hash_loader_binds_original_binary64_and_prior_flags(self):
        # Mock file bytes only; no saved809 loading and no source assessment.
        values={'assessment.json':{'dimension':1,'certificate':{'residual_row_bound':[1e-8],'contraction_upper':2.},
                 'kappa':'unchanged synthetic input','congruence':[1.],'raw_stored_inertia':None,'raw_stored_coercivity':None},
                'sparse-factors.json':{'shape':[1,1],'L':[[0,0,'1.0']],'U':[[0,0,'1.0']],'perm_r':[0],'perm_c':[0]},
                'halfpoint-box.json':{'dimension':1},'sparse-reference.json':{},'exact-targets.json':{},'sparse-stored.json':{},'binding.json':{}}
        def load(values,changed_hash=False):
            encoded={name:json.dumps(v).encode()for name,v in values.items()}
            hashes={name:hashlib.sha256(raw).hexdigest()for name,raw in encoded.items()}
            if changed_hash:hashes['sparse-factors.json']='0'*64
            with patch.object(Path,'read_bytes',lambda p:encoded[p.name]),patch.object(Path,'stat',lambda p:SimpleNamespace(st_size=len(encoded[p.name]))):
                return block.saved_candidate_inputs('unexecuted-synthetic-only',hashes)
        r=load(values);self.assertEqual(r['retained_prior_q'],2.);self.assertIsNone(r['retained_raw_target_flags']['raw_stored_inertia'])
        self.assertEqual(r['lower'][0,0],block.point(F(1)))
        with self.assertRaises(Unresolved):load(values,changed_hash=True)
        values['sparse-factors.json']['L']=[[0,0,'9007199254740993']]
        with self.assertRaises(Unresolved):load(values)
        values['sparse-factors.json']['L']=[[0,0,'1.0'],[0,0,'1.0']]
        with self.assertRaises(Unresolved):load(values)
        with self.assertRaises(Unresolved):block.saved_candidate_inputs('not-read',{})

    def test_12_signed_local_inverse_times_offdiagonal_edge_cancellation(self):
        l=[[F(1),F(),F(),F()],[F(),F(1),F(),F()],
           [F(1),F(),F(1),F()],[F(1),F(),F(1),F(1)]]
        rhs=[F(1),F(),F(),F()]
        self.assertEqual(direct(l,rhs),[F(1),F(),F(-1),F()])
        scalar=scalar_comparison(l,rhs);self.assertEqual(scalar[-1],F(2))
        bound=block.block_triangular_bound(sparse(l),rhs,lower=True,width=2)['bound']
        self.assertEqual(bound,[F(1),F(),F(1),F()])
