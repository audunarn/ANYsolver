"""New native owner enrollment, exact replay and original-factor N32 capture."""
import argparse,os,sys,traceback
from hashlib import sha256
from pathlib import Path
from math import isfinite
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,canonical
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-n32-equilibrium-35a4101-20260909')
MANIFEST='5ff438e561ef29dcada8b33582152e89be2186705d2021459d07613ba0a40886'
INPUTS={'plus':'d2fc255825846a3fdafc21429cd9ff6e69f50658c1f09b965a3e1262205e4bd2',
        'minus':'e40d1bb0e1bd01ed6f9ae4adbb391286fb37f50d8d71403469ebb309526e3eec'}
POLICY='GE_BEAM3_RETAINED_GEOMETRIC_WORK_DECIMAL80_V1'

def validate_equilibrium(v,sign):
    if sign not in INPUTS or v['schema']!='GE_BEAM3_N32_PRECISE_ELASTIC_EQUILIBRIUM_V1' or v['revision']!='35a4101cddeade2ea06dea4fe7861470dd5dba40' or v['sign']!=sign:
        raise ValueError('registered N32 equilibrium authority')
    if v['arithmetic_policy']!=POLICY or v['macros']!=32 or v['nodes']!=65 or v['full_retained_coordinates']!=1158 or v['control_node']!=17 or v['load_node']!=33:
        raise ValueError('same native model/control/policy')
    if v['amplitude']!=(.0065 if sign=='plus' else -.0065) or max(*v['convergence']['metrics'],v['convergence']['correction'],v['force_balance'],v['moment_balance'])>1e-11:
        raise ValueError('actual converged endpoint')
    for k in ('accepted_history_issued','old_chain_relabelled','physical_loading_path_from_rest','modal_comparison_passed','production_qualified'):
        if v[k] is not False:raise ValueError('equilibrium not accepted history/qualification')
    if v['elastic_origin_only'] is not True or len(v['operators'])!=32 or len(v['recovery'])!=32:
        raise ValueError('virgin full model')
    for i,e in enumerate(v['recovery'],1):
        if e['element_id']!=i or [(r['cell'],r['station']) for r in e['stations']]!=[(c,j) for c in (0,1) for j in range(4)]:
            raise ValueError('full ordered station inventory')
        for row in e['stations']:
            h=row['history']
            if any(x!=0. for values in h['plastic'] for x in values) or any(x!=0. for x in h['accumulated']):
                raise ValueError('virgin material history required')

def source(sign,root=ARCHIVE):
    from docs.reference_cases.ge_beam3_next_spatial_native import member
    if sign not in INPUTS:raise ValueError('registered sign')
    raw=member(root,MANIFEST,'wave/'+sign+'-a/output/equilibrium.json',INPUTS[sign])
    v=strict_bytes(raw);validate_equilibrium(v,sign);return raw,v

def layout(p):
    expected_free=list(range(6,384))+list(range(390,582))
    algebraic=[6*i+j for i in range(1,64) for j in (3,4,5)]
    if p['free_dofs']!=expected_free or p['algebraic_dofs']!=algebraic:
        raise ValueError('physical end clamps only; control node remains free')
    if p['internal_layout']!=[[i+1,list(range(390+6*i,396+6*i))] for i in range(32)]:
        raise ValueError('64 actual internal rotations')
    return expected_free,algebraic

def validate_packet(p,sign,seed,checkpoint,parameter):
    from docs.reference_cases.ge_beam3_next_spatial_native import BODY
    if (p['seed_sha256']!=sha256(seed).hexdigest() or p['checkpoint_sha256']!=sha256(checkpoint).hexdigest()
            or type(p['completed_targets']) is not int or p['completed_targets']!=0
            or p['displacement_target']!=(.0065 if sign=='plus' else -.0065) or p['parameter']!=parameter
            or p['policy']!='GE_BEAM3_ELASTIC_SEED_OWNED_CURRENT_REST_FACTOR_CHAIN_V1'):
        raise ValueError('new genesis target/seed/checkpoint authority')
    for k in ('control_constraint_in_physical_stiffness','physical_loading_path_from_rest','production_qualified'):
        if p[k] is not False:raise ValueError('physical packet scope')
    if sha256(canonical(dict(policy=p['policy'],**{k:p[k] for k in BODY}))).hexdigest()!=p['identity']:
        raise ValueError('actual full factor identity')
    layout(p)
    for key,n,m in (('left',576,576),('right',576,582),('geometric',582,582),('stiffness',582,582),('mass',582,582),('kinetic',9216,582)):
        a=p[key]
        if len(a)!=n or any(len(row)!=m or any(type(x) is not float or not isfinite(x) for x in row) for row in a):
            raise ValueError('complete original factor: '+key)
    traces=[6*i+j for i in range(65) for j in (3,4,5)]
    if any(row[j]!=0. for row in p['kinetic'] for j in traces) or any(row[j]!=0. for row in p['mass'] for j in traces):
        raise ValueError('exact zero nodal trace inertia')
    if len(p['compliance_errors'])!=32 or max(p['compliance_errors'])>1e-11:
        raise ValueError('all positive material-compliance factors')

def run(revision,sign,output):
    guard(revision);raw,v=source(sign)
    if any(os.environ.get(k)!=x for k,x in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('exclusive external output')
    root.mkdir(exist_ok=False);sys.path.insert(0,str(ROOT/'src'))
    from anysolver import _ge_beam3_elastic_seed_continuation as owner
    from anysolver import _ge_beam3_elastic_seed_modal as modal
    from anysolver._ge_beam3_refinement_capacity import n32_refinement_capacity
    from anysolver._ge_beam3_native_generalized_program import retained_model_identity
    from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
    from anysolver._ge_beam3_p5_seeded.core import canonical as native
    from docs.reference_cases.ge_beam3_n32_controlled_case import model
    from docs.reference_cases.ge_beam3_refined_controlled_case import masses
    def progress(stage,**extra):print(dict(stage=stage,sign=sign,**extra),flush=True)
    def emit(path,value):
        data=native(value);strict_bytes(data);write(root/path,data);return data
    progress('n32-owned-source-authority')
    try:
        with n32_refinement_capacity():
            program=owner.Program((v['amplitude'],),17,(0.,0.,1.),NodalDeadForces(((33,0.,-1.,0.),)))
            made=model(32,arithmetic_policy=POLICY)
            if retained_model_identity(made)!=v['model_sha256'] or [e.operator.identity for _,e in sorted(made.mesh.elements.items())]!=v['operators']:
                raise ValueError('unchanged source model and actual operators')
            seed=emit('seed-input.json',dict(schema=owner.SEED_SCHEMA,model_sha256=v['model_sha256'],operators=v['operators'],
                control_node=17,direction=program.direction,nodal_forces=program.nodal_forces,
                mechanical=v['mechanical'],parameter=v['load'],displacement=v['amplitude'],source_sha256=sha256(raw).hexdigest()))
            digest=sha256(seed).hexdigest();progress('n32-native-enrollment-start')
            context=owner.Context(made,program,seed,expected_seed_sha256=digest)
            state=context.initial;before=native(state);checkpoint=context.checkpoint(())
            recovery=native(context.recover(state))
            if native(state)!=before or native(state.mechanical.descriptor())!=native(v['mechanical']) or state.parameter!=v['load'] or state.completed_targets!=0:
                raise ValueError('new owner changed source equilibrium')
            if strict_bytes(recovery)!=v['recovery']:raise ValueError('native enrolled recovery differs from source')
            write(root/'checkpoint.json',checkpoint);write(root/'recovery.json',recovery)
            progress('n32-genesis-issued',checkpoint_sha256=sha256(checkpoint).hexdigest())
            replay=owner.Context(model(32,arithmetic_policy=POLICY),program,seed,expected_seed_sha256=digest)
            restored,records=replay.restore(checkpoint,expected_sha256=sha256(checkpoint).hexdigest())
            if records!=() or replay.checkpoint(records)!=checkpoint or native(restored)!=before or native(replay.recover(restored))!=recovery:
                raise ValueError('fresh owner exact genesis/state/recovery replay')
            progress('n32-fresh-owner-replay-complete')
            capture_model=model(32,arithmetic_policy=POLICY)
            packet,check=modal.prepare(capture_model,program,seed,checkpoint,masses(capture_model),
                expected_seed_sha256=digest,expected_sha256=sha256(checkpoint).hexdigest())
            check();p=strict_bytes(native(packet));validate_packet(p,sign,seed,checkpoint,v['load'])
            progress('n32-original-factors-complete',coordinates=582,physical=381,algebraic=189)
            # Packet context is checked promptly, before expensive JSON/source audit.
            check();guard(revision)
            if source(sign)[0]!=raw:raise ValueError('original equilibrium changed')
            packet_bytes=emit('packet.json',dict(schema='GE_BEAM3_N32_OWNED_CURRENT_REST_FACTORS_V1',revision=revision,sign=sign,
                source_sha256=INPUTS[sign],arithmetic_policy=POLICY,packet=p,production_qualified=False))
            emit('complete.json',dict(schema='GE_BEAM3_N32_OWNED_CAPTURE_V1',revision=revision,sign=sign,source_sha256=INPUTS[sign],
                seed_sha256=digest,checkpoint_sha256=sha256(checkpoint).hexdigest(),recovery_sha256=sha256(recovery).hexdigest(),
                packet_sha256=sha256(packet_bytes).hexdigest(),new_genesis_issued=True,fresh_owner_replayed=True,
                original_source_unchanged=True,history_advanced=False,completed_targets=0,physical_loading_path_from_rest=False,
                modal_comparison_passed=False,production_qualified=False,independent_author_review=False))
            progress('n32-owned-capture-complete')
    except BaseException:
        write(root/'failure.json',dict(revision=revision,sign=sign,error=traceback.format_exc(),production_qualified=False))
        raise
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--sign',choices=('plus','minus'),required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.revision,a.sign,a.output)

