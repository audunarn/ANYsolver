"""N24 spatial seed successor; unchanged trial equations and original onset replay."""
from hashlib import sha256
from pathlib import Path
import argparse,sys
from docs.reference_cases.ge_beam3_spatial_equilibrium_probe import (
    amplitude,require_elastic,elastic_control,lateral_seed,solve_guess)
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,read
ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-fine-onset-formal-b-61ac5d8-20260909')
MANIFEST_SHA='da37ee1261b379c461de4b28f9740d54130dc8af4f4d2dc06dc0c5f97c2000c2'
SOURCE='runs/n24/point-2/stage-4/output/checkpoint.json'
SOURCE_SHA='dd7271775f79640f53cb142125b2c3cd20b850caa7c6ffb804a8c237940880c1'
SCHEMA='GE_BEAM3_N24_ELASTIC_SPATIAL_EQUILIBRIUM_SEED_V1'

def source_bytes(archive=ARCHIVE):
    manifest=read(archive/'archive-manifest.json')
    if sha256(manifest).hexdigest()!=MANIFEST_SHA:raise ValueError('N24 onset manifest')
    inventory=strict_bytes(manifest);raw=read(archive/SOURCE)
    if inventory[SOURCE]!=[518339,SOURCE_SHA.upper()] or len(raw)!=518339 or sha256(raw).hexdigest()!=SOURCE_SHA:
        raise ValueError('N24 original onset bytes')
    strict_bytes(raw);return raw

def run(revision,target,output):
    from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
    guard(revision);amplitude(target)
    if target not in (-.003,.003):raise ValueError('N24 small signed seed only')
    raw=source_bytes()
    output=Path(output).resolve()
    if output.exists() or output.is_relative_to(ROOT):raise ValueError('fresh external diagnostic directory required')
    output.mkdir();sys.path.insert(0,str(ROOT/'src'))
    import numpy as np
    from anysolver import _ge_beam3_retained_translation_control as control
    from anysolver._ge_beam3_p5_seeded.core import canonical
    from docs.reference_cases import ge_beam3_refined_controlled_case as case
    def emit(row):print(row,flush=True)
    emit(dict(stage='validate-original-planar-prefix'))
    original=control.Context(case.model(24),case.program(24,.045225))
    source,records=original.restore(raw,expected_sha256=SOURCE_SHA)
    if original.checkpoint(records)!=raw:raise ValueError('original source replay differs')
    require_elastic(source.histories,original.physical.initial.histories)
    require_elastic(source.origins,original.physical.initial.histories)
    descriptor=source.mechanical.descriptor();parameter=source.parameter
    emit(dict(stage='original-prefix-authenticated',records=len(records)))
    # Left quarter-span control; no external lateral force is applied.
    programme=control.Program((target,),13,(0.,0.,1.),control.NodalDeadForces(((25,0.,-1.,0.),)))
    context=elastic_control(case.model(24),programme);p=context.physical
    mechanical=p.make(descriptor)
    seed,diagnostic=lateral_seed(context,mechanical,parameter,target)
    emit(dict(stage='lateral-seed-constructed',**diagnostic))
    solution,load,details=solve_guess(context,seed,parameter,target,emit)
    before=canonical(solution);recovery=[]
    for i,(eid,element) in enumerate(p.elements):
        rows=element.operator.recover(solution.cell_rotations[i],solution.resultants[i],origin=p.initial.histories[i],check=context.guard)
        require_elastic(tuple(r['history'] for r in rows),p.initial.histories[i].stations)
        recovery.append(dict(element_id=eid,stations=rows))
    if canonical(solution)!=before:raise ValueError('recovery changed initializer')
    total=details['residual'][:p.nodal_count].reshape(-1,6).copy();total[24,1]-=load
    force=float(np.linalg.norm(np.sum(total[:,:3],axis=0)))
    moment=float(np.linalg.norm(np.sum(total[:,3:]+np.cross(solution.positions,total[:,:3])+
        np.cross(solution.position_low,total[:,:3]),axis=0)))
    out_of_plane=float(np.max(abs(solution.positions[:,2]+solution.position_low[:,2])))
    if max(force,moment)>1e-11 or out_of_plane<abs(target)*.99:raise ValueError('spatial equilibrium balance/amplitude')
    result=dict(schema=SCHEMA,macros=24,revision=revision,source_sha256=SOURCE_SHA,amplitude=target,control_node=13,
        control_value=context.value(solution),load=load,mechanical=solution.descriptor(),recovery=recovery,
        convergence=details,seed=diagnostic,force_balance=force,moment_balance=moment,out_of_plane=out_of_plane,
        external_lateral_force=False,elastic_origin_only=True,accepted_history_issued=False,
        physical_loading_path_proved=False,postbuckled_branch_qualified=False,production_qualified=False,
        independent_review='PENDING',production_restriction='NO_GO_PRODUCTION_RESTRICTION_UNCHANGED')
    context.guard();guard(revision)
    if source_bytes()!=raw:raise ValueError('source changed')
    with (output/'equilibrium.json').open('xb') as f:f.write(canonical(result))
    emit(dict(stage='spatial-equilibrium-complete',load=load,amplitude=target,out_of_plane=out_of_plane))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True)
    parser.add_argument('--amplitude',type=float,required=True);parser.add_argument('--output',required=True)
    a=parser.parse_args();run(a.revision,a.amplitude,a.output)
if __name__=='__main__':main()
