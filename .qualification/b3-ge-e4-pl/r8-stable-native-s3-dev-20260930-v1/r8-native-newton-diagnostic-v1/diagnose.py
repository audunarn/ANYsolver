"""Fixed-fixture/fixed-predecessor diagnosis; no acceptance or controller edits."""
from pathlib import Path
from dataclasses import replace
from decimal import Decimal,localcontext
import hashlib,json,sys,time
import numpy as np
from scipy import sparse
from scipy.sparse import linalg as spla
import numba,threadpoolctl

root=Path.cwd()
fixture=Path('C:/Users/AudunArnesenNyhus/AppData/Local/Temp/r8-ge-native-energy-coupled-installed-v1')
site=(fixture/'site').resolve()
sys.path.insert(0,str(fixture/'tests'));sys.path.insert(0,str(fixture))
import anysolver
from anysolver import b3_ge
from anysolver._stiffened_shell_ge_experimental import NodalAction
from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver
from test_stiffened_shell_ge_physical_fibre_linear import _definition
from test_stiffened_shell_ge_physical_fibre_finite import _yielding_definition

assert Path(anysolver.__file__).resolve().is_relative_to(site)
pools=threadpoolctl.threadpool_info()
assert pools and all(pool['num_threads']==1 for pool in pools)
assert numba.config.DISABLE_JIT and numba.config.NUMBA_NUM_THREADS==1
started=time.monotonic()
assembly=FinitePointDriver._assemble;advance=FinitePointDriver._advance
linear=spla.spsolve

def branch(origins,candidates):
    with localcontext() as context:
        context.prec=80
        signs=[]
        for origin,candidate in zip(origins,candidates):
            for old,new in zip(origin.stations,candidate.stations):
                for a,b in zip(old.fibres,new.fibres):
                    delta=sum(map(Decimal.from_float,b[:2]))-sum(map(Decimal.from_float,a[:2]))
                    signs.append(0 if delta==0 else (1 if delta>0 else -1))
        return {'signature':hashlib.sha256(json.dumps(signs).encode()).hexdigest(),
                'elastic':signs.count(0),'positive':signs.count(1),'negative':signs.count(-1)}

def strong_definition():
    definition=_definition()
    beams=[]
    for native in definition.beams:
        element,inertia=native.instantiate();reference=element.operator.reference
        section=b3_ge.PhysicalFibreSection(tuple(replace(fibre,
            curve=b3_ge.FlowCurve((0.,),(1e5,),1e9)) for fibre in element.section.fibres),
            element.section.background_factor)
        beams.append(b3_ge.define_beam('b3-ge',element.element_id,element.node_ids,
            reference.coordinates,reference.nodal_triads,section,inertia,
            quadrature=element.operator.order))
    return replace(definition,beams=tuple(beams))

def run(name,definition):
    owner=anysolver.stiffened_shell.create_analysis(definition=definition)
    records=[];newton=[];pending={};latest={};work={'assemblies':0,'linear_solves':0,'advances':0}
    def assembled(driver,state,factor,shell_origins,beam_origins,**kwargs):
        result=assembly(driver,state,factor,shell_origins,beam_origins,**kwargs)
        work['assemblies']+=1
        item={'evaluation':work['assemblies'],'factor':float(factor),
              'relative':float(result[2]),'gap':float(result[3])}
        if pending.get('state') is state:
            item.update(kind='candidate',alpha=pending['alpha'])
            pending.clear()
        else:
            item.update(kind='newton')
            latest.update(driver=driver,state=state,factor=factor,
                shell_origins=shell_origins,beam_origins=beam_origins,
                pattern=kwargs.get('pattern'),result=result)
            newton.append(item)
        records.append(item)
        return result
    def advanced(driver,state,increment,amount):
        candidate=advance(driver,state,increment,amount)
        work['advances']+=1
        pending.update(state=candidate,alpha=float(amount))
        return candidate
    def solved(matrix,rhs,**kwargs):
        value=linear(matrix,rhs,**kwargs);work['linear_solves']+=1
        return value
    FinitePointDriver._assemble=assembled;FinitePointDriver._advance=advanced;spla.spsolve=solved
    status='completed';failure=None
    try:
        owner.solve((NodalAction('beam',105,(0.,0.,1000.,0.,0.,0.)),),targets=(.5,1.))
    except RuntimeError as error:
        if str(error) not in ('finite mixed backtrack budget exhausted','finite mixed Newton iteration limit'):
            raise
        status='nonconverged';failure=str(error)
    finally:
        FinitePointDriver._assemble=assembly;FinitePointDriver._advance=advance;spla.spsolve=linear
    count=owner._K.shape[0];driver=latest['driver'];state=latest['state']
    residual,matrix,relative,gap,shell_next,beam_next=latest['result']
    free=np.r_[owner._free,np.arange(count,matrix.shape[0])]
    a=matrix[free,:][:,free].tocsc();rhs=-residual[free]
    raw=linear(a,rhs)
    scaled=a.copy();left=np.ones(len(free));right=left.copy()
    for _ in range(4):
        rows=np.asarray(abs(scaled).max(axis=1).toarray()).ravel()
        row=np.divide(1.,rows,out=np.ones_like(rows),where=rows>0.)
        scaled=sparse.diags(row)@scaled;left*=row
        cols=np.asarray(abs(scaled).max(axis=0).toarray()).ravel()
        col=np.divide(1.,cols,out=np.ones_like(cols),where=cols>0.)
        scaled=(scaled@sparse.diags(col)).tocsc();right*=col
    lu=spla.splu(scaled)
    refined=right*lu.solve(left*rhs)
    refinements=[]
    for _ in range(8):
        error=rhs-a@refined
        refinements.append(float(np.max(np.abs(error),initial=0.)))
        correction=right*lu.solve(left*error)
        if np.array_equal(refined+correction,refined):break
        refined+=correction
    full_scale=np.r_[owner._coordinate_scale,1./owner._constraint_scale]
    weights=full_scale[free]
    def label(index):
        if index<owner._shell_count:
            return f'shell:{owner._shell_ids[index//6]}:dof{index%6}'
        i=index-owner._shell_count
        if i<6*len(owner._beam_ids):return f'beam:{owner._beam_ids[i//6]}:dof{i%6}'
        if index<count:
            i-=6*len(owner._beam_ids)
            return f'beam-element:{owner._beam_parts[i//24][0].element_id}:retained{i%24}'
        return f'point-constraint:{(index-count)//6}:row{(index-count)%6}'
    def dominant(value):
        weighted=np.abs(value*weights);order=np.argsort(weighted)[-8:][::-1]
        return [{'row':int(free[i]),'label':label(int(free[i])),
                 'value':float(value[i]),'weighted':float(weighted[i])} for i in order]
    def backward(step):
        error=a@step-rhs
        denominator=np.asarray(abs(a)@abs(step)).ravel()+abs(rhs)
        return {'componentwise':float(np.max(np.divide(abs(error),denominator,
            out=np.zeros_like(error),where=denominator>0.),initial=0.)),
            'weighted_max':float(np.max(abs(error*weights),initial=0.)),
            'dominant':dominant(error)}
    probes={}
    parent_branch=branch(latest['beam_origins'],beam_next)
    for method,delta in (('raw',raw),('equilibrated_refined',refined)):
        full=np.zeros(matrix.shape[0]);full[free]=delta
        rows=[]
        for alpha in (1.,.5,.25):
            candidate=advance(driver,state,full,alpha)
            response=assembly(driver,candidate,latest['factor'],latest['shell_origins'],
                latest['beam_origins'],pattern=latest['pattern'])
            predicted=residual+alpha*(matrix@full)
            error=(response[0]-predicted)[free]
            denominator=float(np.max(abs((alpha*(matrix@full))[free]*weights),initial=0.))
            represented=np.r_[candidate.q-state.q,
                (candidate.frames-state.frames).ravel(),
                (candidate.cells-state.cells).ravel(),candidate.resultants.ravel()-state.resultants.ravel()]
            rows.append({'alpha':alpha,'relative':float(response[2]),'gap':float(response[3]),
                'derivative_relative':float(np.max(abs(error*weights),initial=0.))/max(denominator,np.finfo(float).tiny),
                'derivative_error_dominant':dominant(error),
                'changed_state_values':int(np.count_nonzero(represented)),
                'beam_branch':branch(latest['beam_origins'],response[5])})
        probes[method]={'linear_backward':backward(delta),'trials':rows}
    full=np.zeros(matrix.shape[0]);full[free]=raw
    measure=float(np.max(abs(full[:count]/owner._coordinate_scale),initial=0.))
    smooth=[]
    if measure>0.:
        direction=full*(1e-6/measure)
        for h in (.125,.0625,.03125):
            plus=assembly(driver,advance(driver,state,direction,h),latest['factor'],
                latest['shell_origins'],latest['beam_origins'],pattern=latest['pattern'])
            minus=assembly(driver,advance(driver,state,direction,-h),latest['factor'],
                latest['shell_origins'],latest['beam_origins'],pattern=latest['pattern'])
            actual=(plus[0]-minus[0])/(2*h);predicted=matrix@direction
            error=(actual-predicted)[free]
            smooth.append({'h':h,'relative':float(np.linalg.norm(error*weights)/max(
                np.linalg.norm(predicted[free]*weights),np.finfo(float).tiny)),
                'plus_branch':branch(latest['beam_origins'],plus[5]),
                'minus_branch':branch(latest['beam_origins'],minus[5])})
    prefix=() if owner._finite_driver is None else owner.recover().accepted_factors
    snapshot=None if owner._finite_driver is None else hashlib.sha256(owner.checkpoint()).hexdigest()
    np.savez_compressed(root/(name+'.npz'),q=state.q,frames=state.frames,cells=state.cells,
        resultants=state.resultants,multipliers=state.multipliers,residual=residual,
        sparse_data=matrix.data,sparse_indices=matrix.indices,sparse_indptr=matrix.indptr,
        sparse_shape=matrix.shape,free=free,raw_correction=raw,refined_correction=refined,
        coordinate_scale=owner._coordinate_scale,constraint_scale=owner._constraint_scale)
    report={'name':name,'status':status,'failure':failure,'model':owner._identity,
        'geometry_load_history':'frozen existing fixture;1000Nz;targets(.5,1);default12iterations/8backtracks',
        'physical_rows':count,'mixed_rows':matrix.shape[0],'nnz':matrix.nnz,
        'accepted_factors':prefix,'accepted_checkpoint_sha256':snapshot,'work':work,
        'trace':records,'dominant_parent_residual':dominant(residual[free]),
        'parent_branch':parent_branch,'raw_correction_scaled_max':measure,
        'refinement_backward_raw_max_history':refinements,'probes':probes,'directional':smooth}
    (root/(name+'.json')).write_text(json.dumps(report,indent=2,allow_nan=False))
    owner.close()
    print(json.dumps({'name':name,'status':status,'prefix':prefix,'last_relative':relative,
        'raw_backward':probes['raw']['linear_backward']['componentwise'],
        'equilibrated_backward':probes['equilibrated_refined']['linear_backward']['componentwise'],
        'raw_full_relative':probes['raw']['trials'][0]['relative'],
        'equilibrated_full_relative':probes['equilibrated_refined']['trials'][0]['relative']}),flush=True)

for name,definition in (('s3_elastic_pure_fibre',_definition(False,True)),
                        ('s3_partial_fibre_yield',_yielding_definition(False,True)),
                        ('q4_full_fibre_yield',strong_definition())):
    run(name,definition)
loaded={name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items())
    if name.split('.')[0]=='anysolver' and getattr(module,'__file__',None)}
assert all(Path(path).is_relative_to(site) for path in loaded.values())
(root/'imports.json').write_text(json.dumps(loaded,indent=2))
(root/'environment.json').write_text(json.dumps({'python':sys.version,'threads':pools,
    'jit_disabled':bool(numba.config.DISABLE_JIT),'elapsed':time.monotonic()-started},indent=2))
