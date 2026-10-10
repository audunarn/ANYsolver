"""Discriminating source controls; saved observations are a separate child stage."""
import unittest
from fractions import Fraction
from scripts import r8_f03_common_density_response_dev as observer


class ResponseControls(unittest.TestCase):
    def test_mixed_density_source_receipt_refused(self):
        observer.density_receipt('archive','archive',[1,2],[1,2])
        with self.assertRaises(observer.ContractRefusal):
            observer.density_receipt('capture-inferred','archive',[1,2],[1,2])
        with self.assertRaises(observer.ContractRefusal):
            observer.density_receipt('archive','archive',[1,3],[1,2])

    def test_signed_density_inverse_detects_sign_and_permutation(self):
        from scripts import r8_f03_common_density_dev as common
        physical=list(range(1,41)); native=common.native_density(physical)
        self.assertEqual(observer.physical_density(native),physical)
        wrong=native.copy();wrong[0]=-wrong[0]
        self.assertNotEqual(observer.physical_density(wrong),physical)
        wrong=native.copy();wrong[24],wrong[32]=wrong[32],wrong[24]
        self.assertNotEqual(observer.physical_density(wrong),physical)

    def test_original_supports_refuse_added_yaw_gauge(self):
        fixed=list(range(35));free=[i for i in range(1092) if i not in fixed]
        observer.original_supports(fixed,free)
        wrong=fixed[:-1]+[515]
        with self.assertRaises(observer.ContractRefusal):
            observer.original_supports(wrong,[i for i in range(1092) if i not in wrong])
        with self.assertRaises(observer.ContractRefusal):
            observer.original_supports(fixed,[i for i in free if i!=515])

    def test_stale_operator_scale_or_geometry_refused(self):
        for label in ('C CSR','coordinate scale','typed geometry'):
            observer.same_contract([1,2,3],[1,2,3],label)
            with self.assertRaises(observer.ContractRefusal):
                observer.same_contract([1,2,4],[1,2,3],label)

    def test_regional_torque_contains_traction_arm_and_correct_measure(self):
        rho=[0]*40;rho[5*2+1]=8;rho[5*2+3]=2
        wrench=observer.regional_wrench(rho)
        self.assertEqual(wrench[1],-1)
        self.assertEqual(wrench[3],-Fraction(3,10))
        self.assertNotEqual(wrench[3],-Fraction(1,4)) # mx-only loses traction arm
        self.assertEqual(wrench[5],-Fraction(5,16))
        rho[1]=999 # support0 lies outside the regional measure
        self.assertEqual(observer.regional_wrench(rho),wrench)

    def test_non_symmetric_column_capture_exposes_transposition(self):
        # A=[[2,3],[-5,7]], raw column buffer. Known force at q=(11,13).
        raw = [2,-5,3,7]
        f = observer.storage_action(raw,2,[11,13],'F')
        c = observer.storage_action(raw,2,[11,13],'C')
        self.assertEqual(f,[61,36])
        self.assertEqual(c,[-43,124])
        self.assertEqual([a-b for a,b in zip(f,c)],[104,-88])
        # Quadratic work cannot detect this skew-action error.
        self.assertEqual(11*f[0]+13*f[1],11*c[0]+13*c[1])

    def test_physical_flexure_annihilates_yaw_but_polluted_map_refuses(self):
        # At x=0,1 a unit yaw has Uy=0,1 and theta_z=1,1.
        yaw = [1,1,0]
        row = [1,-1,0]  # tip Uy, root theta_z, root Uy
        observer.prove_annihilation({'flexure':row},[yaw])
        with self.assertRaises(observer.ContractRefusal):
            observer.prove_annihilation({'polluted':[1,0,0]},[yaw])
        with self.assertRaises(observer.ContractRefusal):
            observer.prove_annihilation({'truncated':row},[yaw+[1]])

    def test_complete_halfcell_map_not_nodal_only(self):
        expected = [[Fraction(0)]*12 for _ in range(6)]
        # Independent rotation: nodal rx and two cell rx all follow omega_x.
        for slot in (3,6,9): expected[3][slot]=1
        observer.validate_rigid_map(expected,expected)
        omitted = [r.copy() for r in expected]
        omitted[3][6]=omitted[3][9]=0
        with self.assertRaises(observer.ContractRefusal):
            observer.validate_rigid_map(omitted,expected)

    def test_missing_or_changed_affine_load_base_refused(self):
        observer.validate_base(observer.BASE.copy())
        for key in ('affine_force','prescribed_displacement','prestress','operator'):
            incomplete=observer.BASE.copy();incomplete.pop(key)
            with self.assertRaises(observer.ContractRefusal):observer.validate_base(incomplete)
        changed=observer.BASE.copy();changed['prestress']='unknown_loaded_state'
        with self.assertRaises(observer.ContractRefusal):observer.validate_base(changed)
