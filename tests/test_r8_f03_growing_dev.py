"""Registered source/proof controls; actual compiler assessment ONLY level16."""
from copy import deepcopy
from fractions import Fraction as F
import unittest
from scripts import r8_f03_growing_dev as growing
from scripts import r8_f03_growing_halfpoint_dev as half
from scripts.r8_f03_finite_local_dev import ExactBudget,Unresolved
from scripts.r8_f03_finite_sparse_dev import Caps

ASSESSMENT=None
MEASUREMENTS={}

class GrowingControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global ASSESSMENT
        ASSESSMENT=half.assess(16);cls.r=ASSESSMENT

    def test_01_actual_roles_source_and_distinct_claims(self):
        r=self.r;ref=r['reference']
        self.assertEqual((ref['nx'],ref['np'],ref['m'],ref['dim']),(625,144,40,809))
        self.assertEqual(r['stored']['adapter'],'UNCHANGED_ACTUAL_GROWING_LOCAL_COMPILERS')
        self.assertEqual((r['stored']['shell_cells'],r['stored']['members']),(64,8))
        self.assertEqual(r['stored']['source_native_local_shape'],(42,42))
        self.assertEqual((r['stored']['owner_factorizations'],r['stored']['owner_solves']),(0,0))
        self.assertIn(r['status'],('CERTIFIED_GROWING_LEVEL16_HALFPOINT_BOX','UNRESOLVED'))
        for name in ('raw_stored_inertia','raw_stored_coercivity','scientific_floor_comparison','physical_acceptance'):self.assertIsNone(r[name])
        self.assertFalse(r['qualification'])
        MEASUREMENTS.update(status=r['status'],certificate=r['certificate'],kappa=str(ref['kappa']),Cgeom=str(ref['Cgeom']))

    def test_02_all_source_rows_and_force_equivalent_permutation(self):
        ref=self.r['reference'];stored=self.r['stored'];nx,np=ref['nx'],ref['np']
        permutation=stored['P0_channel_to_member_row_permutation']
        self.assertEqual(sorted(permutation.values()),list(range(ref['m'])))
        for raw,logical in permutation.items():self.assertEqual(logical,5*(raw%8)+raw//8)
        maximum=0.
        for row in range(ref['m']):
            keys={k for k in ref['ideal'] if k[0]==nx+np+row}|{k for k in stored['entries'] if k[0]==nx+np+row}
            scale=max(abs(float(ref['ideal'].get(k,F()))) for k in keys)
            error=max(abs(float(ref['ideal'].get(k,F()))-stored['entries'].get(k,0.)) for k in keys)/scale
            maximum=max(maximum,error);self.assertLess(error,2e-12)
            # Exact source row pairing is retained by the transpose scatter.
            for i,j in keys:self.assertEqual(stored['entries'].get((i,j),0.),stored['entries'].get((j,i),0.))
        MEASUREMENTS['all40_P0_row_relative_error']=maximum

    def test_03_native_B_D_and_stationary_shell_source_parity(self):
        ref=self.r['reference'];s=self.r['stored']['entries'];nx,np=ref['nx'],ref['np'];errors={}
        for name,predicate in (('shell',lambda i,j:i<nx and j<nx),('B',lambda i,j:nx<=i<nx+np and j<nx),('negative_D',lambda i,j:nx<=i<nx+np and nx<=j<nx+np)):
            keys={k for k in set(ref['ideal'])|set(s) if predicate(*k)}
            scale=max(abs(float(ref['ideal'].get(k,F()))) for k in keys)
            error=max(abs(float(ref['ideal'].get(k,F()))-s.get(k,0.)) for k in keys)/scale
            errors[name]=error;self.assertLess(error,2e-10)
        self.assertTrue(ref['proof']['native_local']['B_minor_identity'])
        MEASUREMENTS['source_block_max_relative_errors']=errors

    def test_04_independent_frozen_shell_H1_map(self):
        import numpy as np
        from scripts.r8_bl5_mixed_shell_h1_dev import scalar_mixed_h1
        ref=self.r['reference'];n,ny=ref['n'],ref['ny']
        xyz=np.array([(i/n,j/(5*ny)) for j in range(ny+1) for i in range(n+1)])
        cells=[(j*(n+1)+i,j*(n+1)+i+1,(j+1)*(n+1)+i+1,(j+1)*(n+1)+i) for j in range(ny) for i in range(n)]
        scalar,area=scalar_mixed_h1(xyz,cells,float(growing.ELL));self.assertAlmostEqual(area,.2)
        co=scalar.tocoo();idx=ref['index'];maximum=0.
        for i,j,value in zip(co.row,co.col,co.data):
            oldi,oldj=6*int(i)+2,6*int(j)+2
            if oldi in idx and oldj in idx:
                exact=ref['G'][idx[oldi],idx[oldj]]
                maximum=max(maximum,abs(float(exact)-float(value)))
        self.assertLess(maximum,2e-12);MEASUREMENTS['independent_H1_max_absolute_error']=maximum

    def test_05_global_L2_reconstruction_and_exact_yaw(self):
        ref=self.r['reference'];maps=ref['maps'];n,ny=ref['n'],ref['ny'];z=[F()]*ref['nx_full'];energy=F()
        # Arbitrary nonrigid shell interior field, zero bottom trace: actual C z=0.
        for row in range(1,ny+1):
            for col in range(1,n+1):
                for axis in range(6):z[6*(row*(n+1)+col)+axis]=F(((row+3*col+axis)%7)-3,13)
        rows=ref['shell_work']['rows_z']
        for row in range(ny):
            for col in range(n):
                nodes=(row*(n+1)+col,row*(n+1)+col+1,(row+1)*(n+1)+col+1,(row+1)*(n+1)+col)
                local=[z[6*node+axis] for node in nodes for axis in range(6)]
                energy+=sum((sum((v*x for v,x in zip(r,local)),F())**2 for r in rows),F())
        for action in maps['actions']:self.assertEqual(sum((v*z[i] for i,v in action.items()),F()),0)
        for i,value in enumerate(z):self.assertLessEqual(value**2,maps['bounds'][i]**2*energy)
        self.assertEqual(maps['yaw_action'],-F(1,2))
        self.assertIn('common',maps['multiplicity'])
        MEASUREMENTS['global_squared_L2_coordinates_checked']=len(z)

    def test_06_complete_native_norm_and_coupled_chain_bound(self):
        ref=self.r['reference'];sc=ref['shell_count'];phibase=sc+ref['nodal'];n=ref['n'];h=F(1,n);ell=growing.ELL
        z=[F()]*ref['nx_full']
        for node in range(1,n+1):
            for axis in range(6):z[sc+6*node+axis]=F((node+axis)%5-2,11)
        for cell in range(n):
            for axis in range(3):z[phibase+3*cell+axis]=F((cell+axis)%7-3,17)
        energy=F();norm=F()
        for cell in range(n):
            left=z[sc+6*cell:sc+6*cell+6];right=z[sc+6*(cell+1):sc+6*(cell+1)+6];phi=z[phibase+3*cell:phibase+3*cell+3]
            eta=[right[0]-left[0],right[1]-left[1]-h/ell*phi[2],right[2]-left[2]+h/ell*phi[1]]
            y=eta+[right[3+i]-left[3+i] for i in range(3)]+[(right[3+i]+left[3+i])/2-phi[i] for i in range(3)]
            energy+=sum((v*v for v in y),F())
            norm+=sum((h*(left[i]**2+left[i]*right[i]+right[i]**2)/3+ell**2/h*(right[i]-left[i])**2 for i in range(6)),F())
            arm=growing.ARM;width=growing.WIDTH
            norm+=h*sum((phi[i]**2*(1+((arm**2 if i in (0,1) else 0)+(width**2/12 if i in (0,2) else 0))/ell**2) for i in range(3)),F())
            norm+=h/ell*arm*(-phi[0]*(left[1]+right[1])+phi[1]*(left[0]+right[0]))
        for i in range(sc,len(z)):self.assertLessEqual(z[i]**2,ref['maps']['unclosed_bounds'][i]**2*energy)
        supported={ref['index'][i]:v for i,v in enumerate(z) if i in ref['index'] and v}
        assembled=sum((v*supported.get(i,F())*supported.get(j,F()) for (i,j),v in ref['G'].items()),F())
        self.assertEqual(assembled,norm);MEASUREMENTS['native_exact_norm_identity']=True

    def test_07_higher_levels_exact_proof_only(self):
        data=[]
        for level,dimension in ((32,2385),(64,7841)):
            ref=growing.exact_reference(level)
            self.assertEqual(ref['dim'],dimension);self.assertEqual(ref['proof']['full_C_rank'],ref['m'])
            self.assertEqual(ref['maps']['yaw_action'],-F(1,2));self.assertGreater(ref['kappa'],0)
            self.assertEqual(len(ref['maps']['P0_minors']),ref['members'])
            with self.assertRaises(Unresolved):growing.source_stored(ref)
            data.append({'level':level,'dimension':dimension,'C_rank':ref['m'],'kappa':str(ref['kappa']),'exact_operations':ref['exact_operations'],'source_assessment':False})
        MEASUREMENTS['higher_exact_proofs']=data

    def test_08_targets_structure_and_refusals(self):
        r=self.r;nx=r['reference']['nx'];np=r['reference']['np']
        for entries in r['targets']['entries'].values():half.assert_enclosed(entries,r['box'])
        self.assertTrue(half.admit_symmetric_target(r['targets']['entries']['ideal_half'],r['box'],r['family']))
        self.assertEqual(len(r['family']['D_row_lower_bounds']),np);self.assertGreater(r['family']['D_min_lower_bound'],0)
        for key in ((nx,nx+np),(nx+np,nx+np),(nx,nx+18)):
            box=deepcopy(r['box']);box['center_entries'][key]=1e-30
            with self.assertRaises(Unresolved):half.signed_family_certificate(r['reference'],r['congruence'],box,ExactBudget())
        box=deepcopy(r['box']);box['center_entries'][nx,nx]=abs(box['center_entries'][nx,nx])
        with self.assertRaises(Unresolved):half.signed_family_certificate(r['reference'],r['congruence'],box,ExactBudget())
        targets=deepcopy(r['targets']);targets['provenance'].pop('raw_stored_exact_shift')
        with self.assertRaises(Unresolved):half.target_box(targets,r['box']['center_entries'],ExactBudget(),Caps())
        for level in (8,16.,128):
            with self.assertRaises(Unresolved):growing.layout(level)
        box=deepcopy(r['box']);box['center_entries'][0,0]=2**53+1
        with self.assertRaises(Unresolved):half.validate_box_storage(box)
        box=deepcopy(r['box']);box['dimension']=8001
        with self.assertRaises(Unresolved):half.validate_box_storage(box)
        MEASUREMENTS['refusal_controls']=9
