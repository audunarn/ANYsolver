"""New N32 elastic equilibrium from a continuum guess; not a transplanted history."""
import argparse,os,sys,traceback
from pathlib import Path
from hashlib import sha256
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_spatial_ritz_worker import source,INPUTS

def sample(poly,x,segment=None):
    import numpy as np
    if not np.isfinite(x) or not -1<=x<=1:raise ValueError('bounded reference coordinate')
    if segment is None:segment=min(int((x+1)*2),3)
    if type(segment) is not int or not 0<=segment<4 or not -1+.5*segment<=x<=-.5+.5*segment:
        raise ValueError('one-sided registered reference segment')
    return poly(2*(x-(-1+.5*segment)))[13*segment:13*(segment+1)]

def guess_descriptor(physical,value):
    import numpy as np
    from docs.reference_cases.ge_beam3_spatial_next_reference import unpack
    from docs.reference_cases.ge_beam3_spatial_continuum import matrix
    if len(physical.node_ids)!=65 or len(physical.elements)!=32:raise ValueError('N32 guess only')
    poly=unpack(value['polynomial']);data=physical.initial.mechanical.descriptor()
    out={k:v.copy() for k,v in data.items()}
    for i,x in enumerate(np.linspace(-1.,1.,65)):
        y=sample(poly,float(x));out['positions'][i]=y[:3];out['nodal_frames'][i]=matrix(y[3:7])
    out['position_low'][:]=0.
    # Exact supports belong to the native model; roundoff in the BVP end values
    # is not allowed to perturb a fixed position or frame.
    for i in (0,64):
        out['positions'][i]=physical.reference_positions[i];out['nodal_frames'][i]=physical.reference_frames[i]
    for i,(_,element) in enumerate(physical.elements):
        ref=element.operator.reference
        for cell in (0,1):
            half=2*i+cell;lo=-1.+half/32;hi=lo+1/32;mid=(lo+hi)/2
            segment=min(int((mid+1)*2),3);y=sample(poly,mid,segment)
            u=matrix(y[3:7])@ref.frame(cell-.5).T
            out['cell_rotations'][i,cell]=u
            # Work-dual initial guesses: reference-global force and material
            # endpoint moment coefficients. Newton must solve all 18 values.
            out['resultants'][i,3*cell:3*cell+3]=u.T@y[7:10]
            for end,x in enumerate((lo,hi)):
                a=sample(poly,x,segment);slot=6+6*cell+3*end
                out['resultants'][i,slot:slot+3]=ref.nodal_triads[cell+end].T@u.T@a[10:13]
    return physical.make(out)

def run(revision,sign,output):
    guard(revision);value=source(sign)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    if value['sign']!=sign or value['reference']['amplitude']!=(.0065 if sign=='plus' else -.0065):
        raise ValueError('frozen endpoint amplitude')
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('fresh external output')
    root.mkdir(exist_ok=False);sys.path.insert(0,str(ROOT/'src'))
    from anysolver._ge_beam3_refinement_capacity import n32_refinement_capacity
    from anysolver._ge_beam3_precise_geometric_work import POLICY
    from anysolver._ge_beam3_retained_translation_control import Program,NodalDeadForces
    from anysolver._ge_beam3_p5_seeded.core import canonical
    from docs.reference_cases.ge_beam3_n32_controlled_case import model
    from docs.reference_cases.ge_beam3_spatial_equilibrium_probe import elastic_control,solve_guess,require_elastic
    def progress(row):print(row,flush=True)
    progress(dict(stage='n32-source-authority-complete',sign=sign))
    try:
        with n32_refinement_capacity():
            target=.0065 if sign=='plus' else -.0065
            program=Program((target,),17,(0.,0.,1.),NodalDeadForces(((33,0.,-1.,0.),)))
            context=elastic_control(model(32,arithmetic_policy=POLICY),program);p=context.physical
            progress(dict(stage='n32-virgin-context',full_coordinates=p.count,nodal=p.nodal_count))
            guess=guess_descriptor(p,value)
            write(root/'guess.json',dict(source_sha256=INPUTS[sign][1],mechanical=guess.descriptor(),
                load=value['reference']['load'],accepted_history_issued=False,production_qualified=False))
            result,load,details=solve_guess(context,guess,value['reference']['load'],target,progress)
            before=canonical(result);recovery=[]
            for i,(eid,e) in enumerate(p.elements):
                stations=e.operator.recover(result.cell_rotations[i],result.resultants[i],origin=p.initial.histories[i],check=context.guard)
                require_elastic(tuple(r['history'] for r in stations),p.initial.histories[i].stations)
                recovery.append(dict(element_id=eid,stations=stations))
            if canonical(result)!=before:raise ValueError('recovery changed new equilibrium')
            import numpy as np
            total=details['residual'][:p.nodal_count].reshape(-1,6).copy();total[32,1]-=load
            force=float(np.linalg.norm(np.sum(total[:,:3],axis=0)))
            moment=float(np.linalg.norm(np.sum(total[:,3:]+np.cross(result.positions,total[:,:3])+np.cross(result.position_low,total[:,:3]),axis=0)))
            if max(force,moment)>1e-11 or max(*details['metrics'],details['correction'])>1e-11:
                raise ValueError('native N32 equilibrium and complete balance')
            context.guard();guard(revision);source(sign)
            write(root/'equilibrium.json',dict(schema='GE_BEAM3_N32_PRECISE_ELASTIC_EQUILIBRIUM_V1',revision=revision,sign=sign,
                macros=32,nodes=65,full_retained_coordinates=1158,control_node=17,load_node=33,amplitude=target,
                source_sha256=INPUTS[sign][1],arithmetic_policy=POLICY,model_sha256=p.model_identity,
                operators=[e.operator.identity for _,e in p.elements],mechanical=result.descriptor(),load=load,
                convergence=details,recovery=recovery,force_balance=force,moment_balance=moment,
                elastic_origin_only=True,accepted_history_issued=False,old_chain_relabelled=False,
                physical_loading_path_from_rest=False,modal_comparison_passed=False,production_qualified=False))
            progress(dict(stage='n32-equilibrium-complete',sign=sign,load=load))
    except BaseException:
        write(root/'failure.json',dict(revision=revision,sign=sign,error=traceback.format_exc(),production_qualified=False))
        raise
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--sign',choices=('plus','minus'),required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.revision,a.sign,a.output)

