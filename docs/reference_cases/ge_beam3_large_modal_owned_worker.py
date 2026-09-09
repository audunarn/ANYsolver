"""Actual N32 model-owned modal dispatch, replay only; no Newton campaign."""
import argparse,os,sys,time,traceback
from hashlib import sha256
from pathlib import Path
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,canonical
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_next_spatial_native import member
from docs.reference_cases.ge_beam3_n32_snapshot_capture import sources,PREFIX,GUARD_POLICY
from docs.reference_cases.ge_beam3_n32_owned_capture import POLICY
from docs.reference_cases.ge_beam3_n32_spectrum_worker import inputs,PACKETS

NUMERICAL=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-large-modal-e9a1baf-20260909')
MANIFEST='b43b9735da24dfc6cab4c9fd7117ad6b8e70222ca1ce2d1619c770f5ecaaf9e6'
MODES={'plus':'ceeb0f302dfb30b598e2c5de582430d88b0c449d81366ad265819da1c575842d',
       'minus':'8336b410243a6a2635e55746186ff9f8523086108542202b927d8a3b49cbe513'}


def run(revision,sign,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    supplied,v=sources(sign);saved,_=inputs(sign)
    expected=member(NUMERICAL,MANIFEST,'first/'+sign+'/output/modes.json',MODES[sign])
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('exclusive external output')
    root.mkdir(exist_ok=False);sys.path.insert(0,str(ROOT/'src'))
    from anysolver._ge_beam3_native_definition import NativeBeamDefinition
    from anysolver._ge_beam3_native_analysis import NativeBeamAnalysis
    from anysolver._ge_beam3_retained_translation_control import Program
    from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
    from anysolver._ge_beam3_p5_seeded.core import canonical as native
    from anysolver._native_modal_capacity import POLICY as MODAL_POLICY
    from anysolver.control import CancellationToken
    from docs.reference_cases.ge_beam3_n32_controlled_case import model
    from docs.reference_cases.ge_beam3_refined_controlled_case import masses
    class Progress(CancellationToken):
        def __init__(self):super().__init__();self.last=0.;self.stage=None
        def raise_if_cancelled(self,stage=''):
            super().raise_if_cancelled(stage);now=time.monotonic()
            if now-self.last>=10. or stage.startswith('compensated_spectrum.') and stage!=self.stage:
                print(dict(stage=stage,sign=sign),flush=True);self.last=now;self.stage=stage
    try:
        source=model(32,arithmetic_policy=POLICY);inertias=masses(source)
        definitions=tuple(NativeBeamDefinition.capture(e,inertias[i]) for i,e in sorted(source.mesh.elements.items()))
        made=NativeBeamAnalysis(definitions,tuple(source.boundary_conditions),retained_refinement=True)
        p=Program((v['amplitude'],),17,(0.,0.,1.),NodalDeadForces(((33,0.,-1.,0.),)))
        kw=dict(seed=supplied['seed-input.json'],expected_seed_sha256=PREFIX[sign]['seed-input.json'])
        print(dict(stage='model-owned-definition-complete',sign=sign),flush=True)
        envelope=made.import_translation_checkpoint(p,supplied['checkpoint.json'],
            expected_sha256=PREFIX[sign]['checkpoint.json'],**kw)
        write(root/'checkpoint.json',envelope)
        result=made.translation_modes(p,envelope,expected_sha256=sha256(envelope).hexdigest(),
            bounds=(-1.,20.),num_modes=6,modal_policy=MODAL_POLICY,
            compliance_guard_policy=GUARD_POLICY,cancellation_token=Progress(),**kw)
        # Physical factors and state facts must match the accepted saved packet.
        actual=strict_bytes(native(result.packet))
        if set(actual)!=set(saved):raise ValueError('complete native packet field extent')
        fields=set(saved)-{'identity','model_sha256'}
        if canonical({k:actual[k] for k in fields})!=canonical({k:saved[k] for k in fields}):
            raise ValueError('model-owned physical factors differ from preserved packet')
        modes=native(result.modes);write(root/'modes.json',modes)
        if modes!=expected:raise ValueError('model-owned modes differ from saved-factor numerical verification')
        made._guard();guard(revision)
        if sources(sign)[0]!=supplied or canonical(inputs(sign)[0])!=canonical(saved):
            raise ValueError('preserved source inputs changed')
        write(root/'complete.json',dict(schema='GE_BEAM3_N32_MODEL_OWNED_MODAL_INTEGRATION_V1',revision=revision,
            sign=sign,definition_graph=made.identity,snapshot_sha256=result.snapshot_sha256,
            packet_sha256=sha256(native(result.packet)).hexdigest(),historical_packet_sha256=PACKETS[sign],
            checkpoint_sha256=sha256(envelope).hexdigest(),modes_sha256=MODES[sign],modal_policy=MODAL_POLICY,
            elements=32,nodes=65,modal_coordinates=582,physical_dimension=381,
            original_capture_deadline_unchanged=True,physical_factor_bytes_equal=True,
            numerical_mode_bytes_equal=True,accepted_state_replayed=True,newton_advance=False,
            production_qualified=False,independent_author_review=False))
        print(dict(stage='model-owned-N32-modal-complete',sign=sign),flush=True)
    except BaseException:
        write(root/'failure.json',dict(revision=revision,sign=sign,error=traceback.format_exc(),production_qualified=False));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True)
    p.add_argument('--sign',choices=('plus','minus'),required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.revision,a.sign,a.output)
