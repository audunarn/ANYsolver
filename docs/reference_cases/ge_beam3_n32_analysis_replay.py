"""Replay the passed N32 branch through reconstructible model-owned dispatch."""
import argparse,os,sys,traceback
from hashlib import sha256
from pathlib import Path
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical,strict_bytes
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_next_spatial_native import member
from docs.reference_cases.ge_beam3_n32_snapshot_capture import sources,PREFIX
from docs.reference_cases.ge_beam3_n32_owned_capture import POLICY

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-n32-scoped-branch-221b4fe-20260909')
MANIFEST='ea2f8dab163225f4c2b96b9e849ba50ca0048779f7f7b2abc396dd55f4a00ed5'
FINAL='16bf63f2cb7041236e6bc255b90edecfa901e3b766154eb2e7e2dfb17ff49bf0'
FIRST='6d6d4790cff22761f2c04f0fcc9172630eebbf49f386f4b540047984e223b226'

def run(revision,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    raw=member(ARCHIVE,MANIFEST,'wave/plus-a-advance-3/output/checkpoint.json',FINAL)
    first=member(ARCHIVE,MANIFEST,'wave/plus-a-advance-1/output/checkpoint.json',FIRST)
    value=strict_bytes(raw);recovery_digest=value['records'][-1]['recovery_sha256']
    recovery=member(ARCHIVE,MANIFEST,'wave/plus-a-replay-3/output/recovery.json',recovery_digest)
    inputs,_=sources('plus');seed=inputs['seed-input.json']
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('external output required')
    root.mkdir(exist_ok=False);print(dict(stage='analysis-replay-authority-complete'),flush=True)
    sys.path.insert(0,str(ROOT/'src'))
    from anysolver._ge_beam3_native_definition import NativeBeamDefinition
    from anysolver._ge_beam3_native_analysis import NativeBeamAnalysis
    from anysolver._ge_beam3_retained_translation_control import Program
    from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
    from anysolver._ge_beam3_p5_seeded.core import canonical as native
    from docs.reference_cases.ge_beam3_n32_controlled_case import model
    from docs.reference_cases.ge_beam3_refined_controlled_case import masses
    try:
        source=model(32,arithmetic_policy=POLICY);inertias=masses(source)
        definitions=tuple(NativeBeamDefinition.capture(e,inertias[i]) for i,e in sorted(source.mesh.elements.items()))
        made=NativeBeamAnalysis(definitions,tuple(source.boundary_conditions),retained_refinement=True)
        if any(e.operator.arithmetic_policy!=POLICY for e in made.model.mesh.elements.values()):raise ValueError('arithmetic policy lost')
        program=Program((.0075,.010,.015),17,(0.,0.,1.),NodalDeadForces(((33,0.,-1.,0.),)))
        kw=dict(seed=seed,expected_seed_sha256=PREFIX['plus']['seed-input.json'])
        print(dict(stage='analysis-model-reconstructed',elements=32,nodes=65),flush=True)
        envelope=made.import_translation_checkpoint(program,raw,expected_sha256=FINAL,**kw)
        if strict_bytes(envelope)['backend'].encode('ascii')!=raw:raise ValueError('adoption changed backend')
        write(root/'checkpoint.json',envelope);print(dict(stage='analysis-native-adoption-complete'),flush=True)
        fields=made.recover_translation(program,envelope,expected_sha256=sha256(envelope).hexdigest(),**kw)
        if native(fields)!=recovery:raise ValueError('actual physical recovery changed')
        write(root/'recovery.json',native(fields));print(dict(stage='analysis-native-recovery-complete'),flush=True)
        prefix=made.translation_checkpoint_prefix(program,envelope,1,expected_sha256=sha256(envelope).hexdigest(),**kw)
        if strict_bytes(prefix)['backend'].encode('ascii')!=first:raise ValueError('native original prefix changed')
        write(root/'prefix.json',prefix)
        write(root/'definitions.json',[strict_bytes(d.raw) for d in definitions])
        guard(revision);made._guard()
        if member(ARCHIVE,MANIFEST,'wave/plus-a-advance-3/output/checkpoint.json',FINAL)!=raw or sources('plus')[0]!=inputs:
            raise ValueError('immutable input changed')
        files={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p.read_bytes()).hexdigest()) for p in sorted(root.iterdir())}
        write(root/'complete.json',dict(schema='GE_BEAM3_N32_MODEL_OWNED_REPLAY_V1',revision=revision,
            source_manifest=MANIFEST,definition_graph=made.identity,elements=32,nodes=65,external_dofs=390,
            completed_targets=3,files=files,adopted_backend_sha256=FINAL,retained_prefix_sha256=FIRST,
            recovery_sha256=recovery_digest,advances_run=False,production_qualified=False,independent_review=False))
        print(dict(stage='analysis-replay-complete'),flush=True)
    except BaseException:
        write(root/'failure.json',dict(error=traceback.format_exc(),revision=revision,production_qualified=False));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.revision,a.output)
