"""Prepared stdlib fake-clock/refusal controls; execution requires fresh authority.

These verify harness semantics only, never mechanics or G5 acceptance.
"""
from dataclasses import dataclass,field
import importlib.util
from pathlib import Path
import sys
import unittest

PATH=Path(__file__).resolve().parents[1]/'scripts/r8_b2_g5_readiness_dev.py'
spec=importlib.util.spec_from_file_location('b2_g5_prepared_controls',PATH)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)


@dataclass
class Action:
    shell_force_N:tuple=(0.,0.,0.)
    shell_direct_couple_Nm:tuple=(0.,0.,0.)
    beam_force_N:tuple=(0.,0.,0.)
    beam_direct_couple_Nm:tuple=(0.,0.,0.)
    gap:tuple=(0.,0.,0.,0.,0.)


@dataclass
class Wrench:
    node_actions:tuple=field(default_factory=lambda:tuple(Action() for _ in range(4)))
    production_qualified:bool=False
    shell_force_N:tuple=(0.,0.,0.)
    shell_moment_Nm:tuple=(0.,0.,0.)
    beam_force_N:tuple=(0.,0.,0.)
    beam_moment_Nm:tuple=(0.,0.,0.)


@dataclass
class Case:
    case_id:str
    internal_strain_energy:float
    selected_displacements:tuple=(-1.,0.)
    selected_affine_reactions:tuple=(0.,0.)
    footprint_wrenches:tuple=field(default_factory=lambda:(Wrench(),))
    beam_resultants_local:tuple=(('b2-0-0',((0.,)*6,)*3),)


@dataclass
class Envelope:
    component:str
    station_index:int
    station_normalized:float
    minimum_case_id:str='case-1'
    maximum_case_id:str='case-1'
    minimum:float=0.
    maximum:float=0.
    member_id:str='b2-0-0'


@dataclass
class Batch:
    cases:tuple
    solve_count:int
    status:str='completed'
    production_qualified:bool=False
    factorization_count:int=1
    maximum_rhs_chunk:int=1
    member_resultant_envelopes:tuple=field(default_factory=lambda:tuple(Envelope(c,i,s)
        for i,s in enumerate((0.,.5,1.)) for c in ('N','Qy','Qz','Mx','My','Mz')))


class Handle:
    solve_count=0
    factorization_count=1


class Owner:
    def __init__(self,increment=2):self._handle=Handle();self.calls=[];self.increment=increment
    def solve_linear_many(self,cases,**kwargs):
        self.calls.append(len(cases));result=[]
        for name,force in cases:
            self._handle.solve_count+=self.increment;kwargs['on_case'](name)
            result.append(Case(name,-force/2))
        return Batch(tuple(result),self._handle.solve_count)


class Controls(unittest.TestCase):
    def test01_exact_registered_profiles_and_middle_action(self):
        configs=m.proposed_doubling_configs()
        self.assertEqual([m.inventory(x)['q4_shells'] for x in configs],[2500,5000,10000])
        self.assertEqual(configs[-1],m.source_settings('large'))
        middle=m.selected_input(configs[1])
        self.assertEqual((middle['loaded_node'],middle['loaded_dof'],middle['selected_dofs']),(2626,15752,[15752,15750]))
        self.assertEqual(m.inventory(configs[1])['free_dofs'],33630)
    def test02_fakeclock_six111_sequences_one_factor(self):
        owner=Owner();ticks=iter(range(36));events=[]
        result=m.cached_sequence_series(owner,[(f'case-{i+1}',-float(i+1)) for i in range(100)],
            dict(dofs=(1,2),footprints='fixed'),{'b2-0-0':(0.,.5,1.)},clock=lambda:next(ticks),emit=events.append)
        self.assertEqual(owner.calls,[1,10,100]*6)
        self.assertEqual(result['primary_count'],666)
        self.assertEqual(owner._handle.solve_count,1332)
        self.assertEqual(result['median_seconds'],3.)
        self.assertEqual(len(result['warm']),5)
        self.assertEqual(sum(x['kind']=='validated' for x in events),18)
        self.assertFalse(result['assembly_qualification'])
    def test03_thirdsolve_refused_and_raw_return_preserved(self):
        owner=Owner(3);events=[]
        with self.assertRaisesRegex(RuntimeError,'same-factor counts'):
            m.cached_sequence_series(owner,[(f'case-{i+1}',-float(i+1)) for i in range(100)],
                dict(dofs=(1,2),footprints='fixed'),{},emit=events.append)
        self.assertEqual(len(owner.calls),1)
        self.assertEqual(events[0]['kind'],'returned_before_assertions')
    def test04_original_relative_floor_cannot_hide_failure(self):
        batch=Batch((Case('case-1',1e-15),),1)
        with self.assertRaisesRegex(RuntimeError,'relative work'):
            m.validate_warm_reference(batch,[('case-1',-1e-15)])
    def test05_partial_and_wrong_order_refused(self):
        for batch in (Batch((),0,status='failed'),Batch((Case('wrong',.5),),1)):
            with self.assertRaises(RuntimeError):m.validate_warm_reference(batch,[('case-1',-1.)])
    def test06_missing_repetitions_and_envelope_tie_refused(self):
        with self.assertRaises(RuntimeError):m.cached_sequence_series(Owner(),[],{}, {},repetitions=4)
        batch=Batch((Case('case-1',.5),),1);batch.member_resultant_envelopes[0].minimum_case_id='case-2'
        with self.assertRaisesRegex(RuntimeError,'governance'):m.validate_warm_reference(batch,[('case-1',-1.)])
    def test07_authority_and_resources_fail_closed(self):
        a=dict(status='AUTHORIZED',numerical_slot_transferred=True,plan_sha256='x',scope='cached-public-111-warm5',
            allowance_seconds=600,reserve_seconds=60,memory_bytes=4*1024**3,controls_seconds=20,installed_seconds=360)
        m.execution_gate(a,'x')
        for key,value in (('numerical_slot_transferred',False),('plan_sha256','y'),('reserve_seconds',0),('installed_seconds',600)):
            with self.assertRaises(RuntimeError):m.execution_gate(dict(a,**{key:value}),'x')
        result=unittest.TestResult();result.testsRun=8
        self.assertEqual(m.adjudicate_controls(result)['status'],'PASS_CONTROLS')
        for executed,skips,errors,failures in ((0,0,0,0),(8,8,0,0),(7,0,0,0),(9,0,0,0),(8,0,1,0),(8,0,0,1)):
            result=unittest.TestResult();result.testsRun=executed
            result.skipped=[(None,'not run')]*skips;result.errors=[(None,'error')]*errors
            result.failures=[(None,'failure')]*failures
            verdict=m.adjudicate_controls(result)
            self.assertEqual(verdict['status'],'FAILED_CONTROLS')
            self.assertEqual((verdict['executed'],verdict['skips'],verdict['errors'],verdict['failures']),
                (executed,skips,errors,failures))
    def test08_phase_landmarks_not_assembly_subtraction(self):
        self.assertEqual(m.CONTROL_FILENAME,'test_r8_b2_g5_readiness_dev.py')
        suite=m.control_suite()
        self.assertEqual(suite.countTestCases(),8)
        def cases(group):
            for item in group:
                if isinstance(item,unittest.TestSuite):yield from cases(item)
                else:yield item
        self.assertTrue(all(c.__class__.__module__=='test_r8_b2_g5_readiness_dev' for c in cases(suite)))
        phase=m.constructor_phase_map()
        self.assertIn('NOT unprofiled assembly acceptance',phase['usage'])
        self.assertIn('eligible_factorization',{x['label'] for x in phase['landmarks']})
        self.assertLess((100.+4.)/(100.+1.),2.5)
        self.assertGreater(4./1.,2.5)


if __name__=='__main__':unittest.main()
