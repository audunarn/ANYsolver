from pathlib import Path
from dataclasses import asdict, is_dataclass
from decimal import Decimal as D, localcontext
from unittest.mock import patch
import hashlib, json, traceback
import numpy as np
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken
import anysolver._stiffened_shell_ge_finite_experimental as fm
from anysolver._ge_beam3_fibre_cell import FibreCellConjugate
from anysolver._ge_beam3_generalized_cell import GeneralizedCellConjugate
from anysolver._ge_beam3_retained_fibre import RetainedFibreOperator
from anysolver._ge_beam3_retained_generalized import RetainedGeneralizedOperator
from examples.stiffened_shell_native_fibre_bl5_material import definition, ACTIONS, CONTROLS

def plain(x):
    if isinstance(x, np.ndarray): return x.tolist()
    if isinstance(x, np.generic): return x.item()
    if isinstance(x, D): return str(x)
    if isinstance(x, bytes): return dict(bytes_sha256=hashlib.sha256(x).hexdigest(),length=len(x))
    if is_dataclass(x): return plain(asdict(x))
    if isinstance(x, dict): return {str(k):plain(v) for k,v in x.items() if k!='_trial_state'}
    if isinstance(x, (list,tuple)): return [plain(v) for v in x]
    if x is None or isinstance(x,(str,int,float,bool)): return x
    raise TypeError('unsupported diagnostic value '+str(type(x)))
def encoded(x): return json.dumps(plain(x),sort_keys=True,allow_nan=False).encode()
def write(path,x): path.write_bytes(encoded(x))
def digest(x): return hashlib.sha256(encoded(x)).hexdigest()
def state_arrays(s):
    return {k:np.array(v,copy=True) for k,v in vars(s).items() if v is not None}
def pair(v): return D.from_float(float(v[0]))+D.from_float(float(v[1]))
def branches(cell,out,origin):
    rows=[]
    with localcontext() as c:
        c.prec=80
        for index,(row,old) in enumerate(zip(out['stations'],cell._origins(origin))):
            if type(cell) is FibreCellConjugate:
                fibres=[]
                for f,item,(z0,p0) in zip(cell.section.fibres,row['fibres'],old):
                    drive=D.from_float(f.young)*(pair(item.total_strain)-z0)
                    radius=f.curve._at(p0)[0];delta=pair(item.plastic_increment);a=p0+abs(delta)
                    knots=[D.from_float(float(v)) for v in f.curve.plastic_strain]
                    fibres.append(dict(id=f.fibre_id,branch=item.branch,drive=str(drive),margin=str(abs(drive)-radius),
                        radius=str(radius),accumulated=str(a),table_interval=sum(a>k for k in knots),
                        knot_distances=[str(a-k) for k in knots],algorithmic_modulus=item.algorithmic_modulus))
                rows.append(dict(station=index,fibres=fibres))
            else:
                values=[pair(v) for v in zip(*row['resultants'])];z0,p0=old;m=cell.section._m
                q=sum((values[i]*sum((m[i][j]*values[j] for j in range(6)),D(0)) for i in range(6)),D(0)).sqrt()
                radius=D.from_float(cell.section.yield_force)+D.from_float(cell.section.hardening)*p0
                rows.append(dict(station=index,branch=row['branch'],margin=str(q-radius),radius=str(radius)))
    return rows

def execute(folder,evidence):
    counts={};evaluations=[];failures=[];case='A';stage='compile';label=None;local=[];latest=None;group=None
    owner=None;amount=None;proposal=None;accepted=[];token=CancellationToken();fullstep=None
    def count(name): counts[(case,stage,name)]=counts.get((case,stage,name),0)+1
    def dump(name,item):
        arrays=item['arrays'];np.savez_compressed(folder/(name+'.npz'),**arrays);write(folder/(name+'.json'),{k:v for k,v in item.items() if k!='arrays'})
    originals={name:getattr(fm.FinitePointDriver,name) for name in ('_assemble','_advance','_solve_fixed','_native_boundary_amount')}
    original_solve=fm.spla.spsolve;original_q4=fm.q4_algorithmic_response
    def q4(model,element,u,origin,*args,**kw):
        count('q4_response');before=plain(origin);out=original_q4(model,element,u,origin,*args,**kw)
        material=model.get_material(element.material_name)
        local.append(dict(family='q4',element_id=element.element_id if hasattr(element,'element_id') else None,
            u=plain(u),origin=before,origin_id=id(origin),origin_sha256=digest(origin),E=material.elastic_modulus,nu=material.poisson_ratio,
            curve=plain(vars(material.hardening_curve)) if material.hardening_curve is not None else None,
            residual=plain(out[0]),tangent=plain(out[1]),candidate=plain(out[2]),stable_rotation=kw.get('stable_rotation')))
        assert plain(origin)==before
        return out
    def cell(family,original):
        def call(self,p,origin=None,**kw):
            count(family+'_cell');before=encoded(origin);out=original(self,p,origin=origin,**kw)
            row=dict(family=family,cell_identity=self.identity,resultants=plain(p),origin=plain(origin),origin_id=id(origin),
                origin_sha256=hashlib.sha256(before).hexdigest(),response=plain(out),labels=branches(self,out,origin))
            local.append(row);assert encoded(origin)==before
            return out
        return call
    def retained(family,original):
        def call(self,*a,**kw):
            count(family+'_retained');out=original(self,*a,**kw)
            local.append(dict(family=family+'_retained',inputs=plain(a),origin_sha256=digest(kw.get('origin')),
                residual=plain(out.residual),hessian=plain(out.hessian),hessian_low=plain(out.hessian_low),kinematics=plain(out.kinematics)))
            return out
        return call
    def assemble(self,state,factor,*a,**kw):
        nonlocal local,latest
        count('assemble');local=[];out=originals['_assemble'](self,state,factor,*a,**kw)
        row=dict(case=case,stage=stage,label=label,factor=float(factor),amount=amount,relative=float(out[2]),gap=float(out[3]),
            generation=self.owner._generation,origins_sha256=digest((a[0],a[1])),callbacks=local,
            shell_next=plain(out[4]),beam_next=plain(out[5]))
        k=out[1].tocsc();row['arrays']=dict(R=out[0].copy(),K_data=k.data.copy(),K_indices=k.indices.copy(),
            K_indptr=k.indptr.copy(),K_shape=np.array(k.shape),**state_arrays(state))
        latest=row
        evaluations.append({k:row[k] for k in ('case','stage','label','factor','amount','relative','gap','generation','origins_sha256')})
        if stage=='resume' and group is not None: group['candidates'].append(row)
        if stage=='tangent': dump('B-'+label,row)
        if stage=='failed-parent-tangent': dump('A-'+label,row)
        return out
    def advance(self,state,d,h):
        nonlocal amount
        count('advance');amount=float(h);return originals['_advance'](self,state,d,h)
    def solve(k,rhs,*a,**kw):
        nonlocal group,fullstep
        count('global_linear_solve');step=original_solve(k,rhs,*a,**kw)
        free=np.r_[owner._free,np.arange(owner._K.shape[0],owner._K.shape[0]+len(owner._finite_driver._state.multipliers))]
        fullstep=np.zeros(len(latest['arrays']['R']));fullstep[free]=step
        kk=k.tocsc();err=k@step-rhs
        group=dict(parent=latest,candidates=[],linear=dict(free=free.copy(),rhs=rhs.copy(),step=step.copy(),fullstep=fullstep.copy(),
            K_data=kk.data.copy(),K_indices=kk.indices.copy(),K_indptr=kk.indptr.copy(),K_shape=np.array(kk.shape),linear_residual=err.copy()))
        return step
    def boundary(self,*a,**kw):
        nonlocal proposal
        count('boundary_proposal');proposal=originals['_native_boundary_amount'](self,*a,**kw)
        if group is not None:group['proposal']=proposal
        return proposal
    def fixed(self,actions,targets,**kw):
        nonlocal group,amount
        assert case=='A' and stage=='resume';assert len(targets)==1 and any(abs(targets[0]-v)<1e-15 for v in (1.,.9375,.90625)),targets
        assert self.owner._generation==3 and self._load_factor==.875
        count('fixed_attempt');group=None;amount=None
        try:return originals['_solve_fixed'](self,actions,targets,**kw)
        except fm.FiniteIncrementFailure as error:
            number=len(failures)+1
            if group is not None:
                dump('A-failure-%d-parent'%number,group['parent'])
                for i,row in enumerate(group['candidates']):dump('A-failure-%d-candidate-%02d'%(number,i),row)
                np.savez_compressed(folder/('A-failure-%d-linear.npz'%number),**group['linear'])
            failures.append(dict(attempt=plain(error.attempt),proposal=group.get('proposal') if group else None,
                saved_candidates=len(group['candidates']) if group else 0))
            write(folder/'A-failures.json',failures);raise
    def observe(result):
        accepted.append(plain(result));(folder/'unexpected-accepted.bin').write_bytes(owner.checkpoint())
        token.cancel('stop immediately on unexpected accepted commit')
    controls=[patch.object(fm.FinitePointDriver,k,v) for k,v in (('_assemble',assemble),('_advance',advance),('_solve_fixed',fixed),('_native_boundary_amount',boundary))]
    controls += [patch.object(fm.spla,'spsolve',solve),patch.object(fm,'q4_algorithmic_response',q4),
        patch.object(FibreCellConjugate,'response',cell('physical',FibreCellConjugate.response)),
        patch.object(GeneralizedCellConjugate,'response',cell('generalized',GeneralizedCellConjugate.response)),
        patch.object(RetainedFibreOperator,'evaluate',retained('physical',RetainedFibreOperator.evaluate)),
        patch.object(RetainedGeneralizedOperator,'evaluate',retained('generalized',RetainedGeneralizedOperator.evaluate))]
    results={}
    for control in controls:control.start()
    try:
        raw=(evidence/'boundary-candidate-v5/cohort-v1/accepted-0005.bin').read_bytes()
        assert hashlib.sha256(raw).hexdigest()=='4147dcbac56980a0e39db89b89b1aba2d7a4296c6860ded6056dbf57f7ff9869'
        owner=ss.create_analysis(definition=definition());stage='restore';owner.restore(raw);driver=owner._finite_driver
        assert owner.checkpoint()==raw and owner._generation==3 and driver._load_factor==.875
        write(folder/'A-origin.json',dict(controller=plain(driver._adaptive_state),shell=plain(driver._shell_origins),beams=plain(driver._beam_origins),state={k:plain(v) for k,v in state_arrays(driver._state).items()}))
        stage='resume'
        try:owner.solve(ACTIONS,(.5,1.),on_accepted=observe,cancellation_token=token,**CONTROLS)
        except fm.AdaptiveIncrementExhausted as error:results['A']=dict(outcome=type(error).__name__,message=str(error),attempts=plain(error.attempts))
        except BaseException:
            if not accepted:raise
            results['A']=dict(outcome='unexpected_acceptance_cancelled',traceback=traceback.format_exc())
        else:raise AssertionError('unexpected normal continuation return')
        results['A'].update(accepted=accepted,generation=owner._generation,prefix_bytes_equal=owner.checkpoint()==raw,controller_after=plain(driver._adaptive_state))
        if accepted:
            write(folder/'result.json',results);return results
        if not accepted:assert owner.checkpoint()==raw and owner._generation==3
        assert group is not None and len(group['candidates'])==13
        parent=group['parent'];arrays=parent['arrays'];s=fm._State(**{k:arrays[k] for k in ('q','frames','cells','resultants','multipliers')},shell_anchors=arrays.get('shell_anchors'))
        d=group['linear']['fullstep'].copy();kdata=arrays
        k=fm.sparse.csc_matrix((kdata['K_data'],kdata['K_indices'],kdata['K_indptr']),shape=tuple(kdata['K_shape']))
        w=np.r_[owner._coordinate_scale,np.ones(owner._C.shape[0])];expected=k@d;errors=[]
        origins=(driver._shell_origins,driver._beam_origins);origin_digest=digest(origins);factor=parent['factor'];stage='failed-parent-tangent'
        np.savez_compressed(folder/'A-direction.npz',direction=d,weights=w,expected=expected,fixed=owner._fixed,free=owner._free)
        for h in (1e-4,1e-5,1e-6):
            label='plus-'+str(h);positive=driver._assemble(driver._advance(s,d,h),factor,*origins,pattern=driver._pattern)
            label='minus-'+str(h);negative=driver._assemble(driver._advance(s,d,-h),factor,*origins,pattern=driver._pattern)
            error=np.linalg.norm(((positive[0]-negative[0])/(2*h)-expected)*w)/max(np.linalg.norm(expected*w),1.)
            errors.append(dict(h=h,error=float(error)))
        assert digest(origins)==origin_digest and owner.checkpoint()==raw and owner._generation==3
        results['A']['directional_errors']=errors
        owner.close();owner=None
        case='B';stage='compile';raw=(evidence/'boundary-candidate-v5/cohort-v1/accepted-0002.bin').read_bytes()
        assert hashlib.sha256(raw).hexdigest()=='487db8581a5a93517fd8e4956c092cd48c7473302ddb626b2886d2c477c91f03'
        owner=ss.create_analysis(definition=definition(shell_material=False));stage='restore';owner.restore(raw);driver=owner._finite_driver
        assert owner.checkpoint()==raw and owner._generation==2 and driver._load_factor==1.
        state=driver._state;origins=(driver._shell_predecessors,driver._beam_predecessors);origin_digest=digest(origins)
        write(folder/'B-origin.json',dict(shell=plain(origins[0]),beams=plain(origins[1]),controller=plain(driver._adaptive_state)))
        stage='tangent';label='base';amount=None
        base=driver._assemble(state,1.,*origins,pattern=driver._pattern);r,k=base[:2]
        def activity(out):
            beam=[]
            for candidate,origin in zip(out[5],origins[1]):
                for after,before in zip(candidate.stations,origin.stations):
                    if hasattr(after,'rows'):beam.extend(float(row[2]+row[3])>float(old[2]+old[3]) for row,old in zip(after.rows,before.rows))
                    else:beam.append(sum(after.accumulated)>sum(before.accumulated))
            return tuple(beam)
        branch=activity(base);d=np.zeros(len(r));n=owner._shell_count
        d[:n:6]=np.linspace(0.,1e-4,len(owner._shell_ids));d[3:n:6]=np.linspace(0.,2e-4,len(owner._shell_ids));d[4:n:6]=np.linspace(0.,-3e-4,len(owner._shell_ids))
        for i in range(len(owner._beam_ids)):
            d[n+6*i+2]=.001*(i+1);d[n+6*i+3:n+6*i+6]=(2e-4,-1e-4,3e-4)
        retained=n+driver._beam_nodal
        for i in range(len(owner._beam_parts)):
            d[retained+24*i:retained+24*i+6]=(2e-4,-3e-4,1e-4,-2e-4,1e-4,3e-4)
            d[retained+24*i+6:retained+24*i+24]=owner._coordinate_scale[retained+24*i+6:retained+24*i+24]*1e-4
        d[len(state.q):]=np.linspace(1.,2.,len(state.multipliers));d[owner._fixed]=0.
        w=np.r_[owner._coordinate_scale,np.ones(owner._C.shape[0])];expected=k@d;errors=[]
        np.savez_compressed(folder/'B-direction.npz',direction=d,weights=w,expected=expected,fixed=owner._fixed,free=owner._free)
        for h in (1e-4,1e-5,1e-6):
            label='plus-'+str(h);positive=driver._assemble(driver._advance(state,d,h),1.,*origins,pattern=driver._pattern)
            label='minus-'+str(h);negative=driver._assemble(driver._advance(state,d,-h),1.,*origins,pattern=driver._pattern)
            error=np.linalg.norm(((positive[0]-negative[0])/(2*h)-expected)*w)/max(np.linalg.norm(expected*w),1.)
            errors.append(dict(h=h,error=float(error),activity_plus=activity(positive),activity_minus=activity(negative),activity_base=branch,
                activity_matches=activity(positive)==activity(negative)==branch))
        assert digest(origins)==origin_digest and owner.checkpoint()==raw and owner._generation==2
        results['B']=dict(errors=errors,prefix_bytes_equal=True,generation=2,origin_sha256=origin_digest,criterion=1e-5,
            scope='all original h evaluated; branch eligibility adjudicated independently from explicit saved labels')
        write(folder/'result.json',results)
        return results
    finally:
        for control in reversed(controls):control.stop()
        write(folder/'evaluations.json',evaluations);write(folder/'counts.json',[dict(case=c,stage=s,method=m,count=v) for (c,s,m),v in counts.items()])
        write(folder/'partial-result.json',results)
        if owner is not None:owner.close()
