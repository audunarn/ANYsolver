"""Elastic spatial-equilibrium initializer, NOT history/restart authority.

Use an authenticated planar solution as a numerical guess only. Every residual
uses virgin section origins. No accepted record is issued or rewritten.
"""
from hashlib import sha256
from pathlib import Path
import argparse, sys

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-fine-onset-formal-b-61ac5d8-20260909')
MANIFEST_SHA='da37ee1261b379c461de4b28f9740d54130dc8af4f4d2dc06dc0c5f97c2000c2'
SOURCE='runs/n20/point-2/stage-4/output/checkpoint.json'
SOURCE_SHA='f45e617c272aba490db5cd1ef93fc543462aaf5c104557cbd1c47defebe76d45'
SCHEMA='GE_BEAM3_ELASTIC_SPATIAL_EQUILIBRIUM_INITIALIZER_V1'

def source_bytes(archive=ARCHIVE):
    from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes
    manifest=(archive/'archive-manifest.json').read_bytes()
    if sha256(manifest).hexdigest()!=MANIFEST_SHA:raise ValueError('frozen onset archive manifest mismatch')
    inventory=strict_bytes(manifest)
    raw=(archive/SOURCE).read_bytes()
    if inventory[SOURCE]!=[432367,SOURCE_SHA.upper()] or len(raw)!=432367 or sha256(raw).hexdigest()!=SOURCE_SHA:
        raise ValueError('frozen planar guess hash mismatch')
    strict_bytes(raw);return raw

def amplitude(value):
    if type(value) is not float or value not in (-.006,-.003,.003,.006):
        raise ValueError('registered signed lateral displacement required')
    return value

def require_elastic(histories,virgin):
    from anysolver._ge_beam3_p5_seeded.core import canonical
    if canonical(histories)!=canonical(virgin):raise ValueError('spatial initializer cannot create material history')

def elastic_control(model,program):
    """Trial-only border; deliberately has no genesis, stage or checkpoint API.

    A lateral control under vertical load is singular at the symmetric virgin
    state. That is not a reason to weaken the normal history owner's genesis
    check. This separate initializer borrows only its algebraic trial methods.
    """
    import numpy as np
    from anysolver import _ge_beam3_retained_translation_control as control
    from anysolver._ge_beam3_retained_nodal_loading import Context as Physical,Program as ForceProgram
    from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
    from anysolver._ge_beam3_native_line_loading import LinePattern
    from anysolver._ge_beam3_p5_seeded.core import canonical
    from anysolver._native_reference_modal import _owned
    if type(program) is not control.Program:raise ValueError('exact initializer control programme')
    program.__post_init__()
    class TrialControl:
        value=control.Context.value
        project=control.Context.project
        assemble=control.Context.assemble
        correction_norm=control.Context.correction_norm
        step=control.Context.step
        def guard(self):
            self.physical.guard()
            if canonical(self.program)!=self.program_bytes or canonical(dict(node=self.node,row=self.row,column=self.column))!=self.maps:
                raise ValueError('elastic trial control authority changed')
    made=TrialControl();made.program=program;made.program_bytes=canonical(program)
    made.physical=Physical(model,ForceProgram((0.,),DistributedPattern(LinePattern(()),()),program.nodal_forces,
        program.max_iterations,program.max_backtracks))
    p=made.physical
    if program.control_node not in p.index:raise ValueError('initializer control node absent')
    made.node=p.index[program.control_node];slots=list(model.mesh.dof_manager.get_node_dofs(program.control_node)[:3])
    if slots!=list(range(6*made.node,6*made.node+3)) or any(s in p.fixed for s in slots):
        raise ValueError('initializer free physical translation map required')
    row=np.zeros(p.count);row[slots]=program.direction
    column=np.zeros(p.count);column[:p.nodal_count]=-p.nodal_external(1.)
    if not np.any(column[p.free]):raise ValueError('initializer free force pattern required')
    made.row,made.column=_owned(row),_owned(column)
    made.maps=canonical(dict(node=made.node,row=made.row,column=made.column));made.guard()
    return made

def lateral_seed(context,mechanical,parameter,target):
    """Approximate eigenvector for a guess only; not an inertia certificate."""
    import numpy as np
    p=context.physical
    _,j,metrics,responses,_=p.assemble(mechanical,parameter,p.initial.histories)
    require_elastic(tuple(a.history for a in responses),p.initial.histories)
    if max(metrics)>1e-11:raise ValueError('source is not elastic equilibrium under original load')
    kinematic=list(range(p.nodal_count));static=[]
    for i in range(len(p.elements)):
        first=p.nodal_count+24*i;kinematic.extend(range(first,first+6));static.extend(range(first+6,first+24))
    kk=j[np.ix_(kinematic,kinematic)];ss=j[np.ix_(static,static)];sk=j[np.ix_(static,kinematic)]
    reduced=kk-j[np.ix_(kinematic,static)]@np.linalg.solve(ss,sk)
    local={g:i for i,g in enumerate(kinematic)}
    lateral=[g for g in p.free if (g<p.nodal_count and g%6 in (2,3,4)) or
             (g>=p.nodal_count and (g-p.nodal_count)%24 in (0,1,3,4))]
    indices=[local[g] for g in lateral];block=reduced[np.ix_(indices,indices)]
    symmetry=float(np.linalg.norm(block-block.T)/max(1.,np.linalg.norm(block)))
    if symmetry>1e-11:raise ValueError('seed tangent symmetry')
    values,vectors=np.linalg.eigh((block+block.T)/2.)
    index=int(np.argmin(abs(values)));vector=vectors[:,index]
    error=float(np.linalg.norm(block@vector-values[index]*vector)/max(1.,np.linalg.norm(block)))
    if error>1e-11:raise ValueError('seed eigenpair residual')
    mode=np.zeros(p.count);mode[lateral]=vector
    mode[static]=-np.linalg.solve(ss,sk@mode[kinematic])
    control=float(context.row@mode)
    if abs(control)<1e-8*np.linalg.norm(mode[:p.nodal_count]):raise ValueError('registered control has no lateral seed amplitude')
    seed=context.project(p.advance(mechanical,mode*(target/control)),target)
    return seed,dict(approximate_seed_eigenvalue=float(values[index]),symmetry=symmetry,
        eigenpair_residual=error,control_component=control,stability_classification=False)

def solve_guess(context,guess,parameter,target,progress):
    import numpy as np
    p=context.physical;virgin=p.initial.histories
    initial_history=tuple(virgin);trial=context.project(guess,target)
    for iteration in range(context.program.max_iterations+1):
        progress(dict(stage='spatial-equilibrium-assembly',iteration=iteration))
        r,j,metrics,responses,work=context.assemble(trial,parameter,virgin,target)
        require_elastic(tuple(a.history for a in responses),virgin)
        step,delta,correction,matrix=context.step(trial,parameter,r,j,target)
        progress(dict(stage='spatial-equilibrium-correction',iteration=iteration,metrics=metrics,
                      correction=correction,load=parameter,control=context.value(trial)))
        if max(*metrics,correction)<=1e-11:
            require_elastic(virgin,initial_history)
            return trial,parameter,dict(iterations=iteration,metrics=metrics,correction=correction,
                                        residual=r,work=work)
        if iteration==context.program.max_iterations:raise RuntimeError('spatial initializer Newton limit')
        angular=[step[6*i+3:6*i+6] for i in range(len(p.node_ids))]
        angular.extend(step[p.nodal_count+24*i+3*c:p.nodal_count+24*i+3*c+3]
                       for i in range(len(p.elements)) for c in (0,1))
        fraction=min(1.,.45*np.pi/max(max(float(np.linalg.norm(v)) for v in angular),np.finfo(float).tiny))
        for cut in range(context.program.max_backtracks+1):
            amount=fraction*.5**cut;candidate=context.project(p.advance(trial,step*amount),target)
            next_parameter=float(parameter+delta*amount)
            changed,_,_,responses,_=context.assemble(candidate,next_parameter,virgin,target)
            require_elastic(tuple(a.history for a in responses),virgin)
            natural=np.linalg.solve(matrix,-np.r_[changed[p.free],context.value(candidate)-target])
            if not np.isfinite(natural).all():raise ValueError('nonfinite initializer natural merit')
            trial_step=np.zeros(p.count);trial_step[p.free]=natural[:-1]
            merit=context.correction_norm(trial,parameter,trial_step,float(natural[-1]))
            if merit<correction:trial,parameter=candidate,next_parameter;break
        else:raise RuntimeError('spatial initializer line search limit')

def run(revision,target,output):
    from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
    guard(revision);amplitude(target);raw=source_bytes()
    output=Path(output).resolve()
    if output.exists() or output.is_relative_to(ROOT):raise ValueError('fresh external diagnostic directory required')
    output.mkdir();sys.path.insert(0,str(ROOT/'src'))
    import numpy as np
    from anysolver import _ge_beam3_retained_translation_control as control
    from anysolver._ge_beam3_p5_seeded.core import canonical
    from docs.reference_cases import ge_beam3_refined_controlled_case as case
    def emit(row):print(row,flush=True)
    emit(dict(stage='validate-original-planar-prefix'))
    original=control.Context(case.model(20),case.program(20,.045075))
    source,records=original.restore(raw,expected_sha256=SOURCE_SHA)
    if original.checkpoint(records)!=raw:raise ValueError('original source replay differs')
    require_elastic(source.histories,original.physical.initial.histories)
    require_elastic(source.origins,original.physical.initial.histories)
    descriptor=source.mechanical.descriptor();parameter=source.parameter
    emit(dict(stage='original-prefix-authenticated',records=len(records)))
    # Left quarter-span control; no external lateral force is applied.
    programme=control.Program((target,),11,(0.,0.,1.),control.NodalDeadForces(((21,0.,-1.,0.),)))
    context=elastic_control(case.model(20),programme);p=context.physical
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
    total=details['residual'][:p.nodal_count].reshape(-1,6).copy();total[20,1]-=load
    force=float(np.linalg.norm(np.sum(total[:,:3],axis=0)))
    moment=float(np.linalg.norm(np.sum(total[:,3:]+np.cross(solution.positions,total[:,:3])+
        np.cross(solution.position_low,total[:,:3]),axis=0)))
    out_of_plane=float(np.max(abs(solution.positions[:,2]+solution.position_low[:,2])))
    if max(force,moment)>1e-11 or out_of_plane<abs(target)*.99:raise ValueError('spatial equilibrium balance/amplitude')
    result=dict(schema=SCHEMA,revision=revision,source_sha256=SOURCE_SHA,amplitude=target,control_node=11,
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
