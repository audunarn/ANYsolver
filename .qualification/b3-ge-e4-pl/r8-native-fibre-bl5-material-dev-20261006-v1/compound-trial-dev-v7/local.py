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
    stage='compile';callbacks=[];counts={};owner=None;result={}
    def count(method,value=1):counts[(stage,method)]=counts.get((stage,method),0)+value
    original_q4=fm.q4_algorithmic_response;original_assemble=fm.FinitePointDriver._assemble
    def q4(*args,**kwargs):
        count('q4_response');out=original_q4(*args,**kwargs)
        model,element,u,origin=args[:4];material=model.get_material(element.material_name)
        callbacks.append(dict(family='q4',u=plain(u),origin=plain(origin),candidate=plain(out[2]),
            residual=plain(out[0]),tangent=plain(out[1]),E=material.elastic_modulus,nu=material.poisson_ratio,
            curve=plain(vars(material.hardening_curve)) if material.hardening_curve is not None else None))
        return out
    def response(family,original):
        def call(self,*args,**kwargs):
            count(family+'_response');out=original(self,*args,**kwargs)
            count(family+'_local_evaluations',out['evaluations']);count(family+'_local_iterations',out['iterations']);count(family+'_line_trials',out.get('line_trials',0))
            origin=kwargs.get('origin',args[1] if len(args)>1 else None)
            callbacks.append(dict(family=family,origin=plain(origin),origin_sha256=digest(origin),response=plain(out),labels=branches(self,out,origin)))
            return out
        return call
    def assemble(self,state,factor,*args,**kwargs):
        nonlocal callbacks
        count('assemble');callbacks=[];out=original_assemble(self,state,factor,*args,**kwargs)
        if stage in ('parent','full','event','compound'):
            k=out[1].tocsc()
            np.savez_compressed(folder/(stage+'.npz'),R=out[0].copy(),K_data=k.data.copy(),K_indices=k.indices.copy(),K_indptr=k.indptr.copy(),K_shape=k.shape,**state_arrays(state))
            write(folder/(stage+'.json'),dict(relative=float(out[2]),gap=float(out[3]),callbacks=callbacks,
                generation=owner._generation,origin_sha256=digest((args[0],args[1])),shell_next=plain(out[4]),beam_next=plain(out[5])))
        return out
    def forbidden(*args,**kwargs):raise AssertionError('global continuation/Newton forbidden in local discriminator')
    controls=[patch.object(fm,'q4_algorithmic_response',q4),patch.object(fm.FinitePointDriver,'_assemble',assemble),
        patch.object(fm.FinitePointDriver,'_solve_fixed',forbidden),patch.object(FibreCellConjugate,'response',response('physical',FibreCellConjugate.response)),
        patch.object(GeneralizedCellConjugate,'response',response('generalized',GeneralizedCellConjugate.response))]
    for control in controls:control.start()
    try:
        raw=(evidence/'boundary-candidate-v5/cohort-v1/accepted-0005.bin').read_bytes()
        assert hashlib.sha256(raw).hexdigest()=='4147dcbac56980a0e39db89b89b1aba2d7a4296c6860ded6056dbf57f7ff9869'
        owner=ss.create_analysis(definition=definition());stage='restore';owner.restore(raw);driver=owner._finite_driver
        assert owner.checkpoint()==raw and owner._generation==3 and driver._load_factor==.875
        origins=(driver._shell_origins,driver._beam_origins);origin_sha=digest(origins);controller=encoded(driver._adaptive_state)
        saved=evidence/'j2-unblock-dev-v6/candidate-screen-v1'
        with np.load(saved/'A-failure-3-parent.npz',allow_pickle=False) as z:
            arrays={k:z[k].copy() for k in z.files};parent=fm._State(**{k:arrays[k] for k in ('q','frames','cells','resultants','multipliers')},shell_anchors=arrays.get('shell_anchors'))
        with np.load(saved/'A-failure-3-linear.npz',allow_pickle=False) as z:d=z['fullstep'].copy();saved_free=z['free'].copy()
        factor=.90625;stage='parent';base=driver._assemble(parent,factor,*origins,pattern=driver._pattern)
        np.testing.assert_array_equal(base[0],arrays['R']);np.testing.assert_array_equal(base[1].tocsc().data,arrays['K_data'])
        original_merit=max(base[2],base[3]);stage='full';full=driver._advance(parent,d,1.);full_response=driver._assemble(full,factor,*origins,pattern=driver._pattern)
        assert max(full_response[2],full_response[3])>=original_merit
        amount=2.4947614527173763e-14;stage='event';event=driver._advance(parent,d,amount);event_response=driver._assemble(event,factor,*origins,pattern=driver._pattern)
        free=np.r_[owner._free,np.arange(owner._K.shape[0],owner._K.shape[0]+len(parent.multipliers))];np.testing.assert_array_equal(free,saved_free)
        from scipy.sparse import linalg as spla
        import warnings
        stage='post_switch_solve';count('global_linear_solve')
        with warnings.catch_warnings():
            warnings.simplefilter('error',spla.MatrixRankWarning)
            step=spla.spsolve(event_response[1][free,:][:,free],-event_response[0][free])
        if not np.isfinite(step).all():raise RuntimeError('finite post-switch correction required')
        correction=np.zeros(len(d));correction[free]=step
        linear=event_response[1][free,:][:,free]@step+event_response[0][free]
        np.savez_compressed(folder/'post-switch-correction.npz',correction=correction,free=free,linear_residual=linear)
        stage='compound';endpoint=driver._advance(event,correction,1.);changed=driver._assemble(endpoint,factor,*origins,pattern=driver._pattern)
        q4=lambda evaluation:tuple(tuple(float(x)>float(y) for x,y in zip(after['alpha'],before['alpha'])) for after,before in zip(evaluation[4],origins[0]))
        event_switch=q4(event_response)!=q4(base);escape=q4(changed)!=q4(base)
        improved=max(changed[2],changed[3])<original_merit
        result=dict(parent_merit=float(original_merit),full_merit=float(max(full_response[2],full_response[3])),event_amount=amount,
            event_merit=float(max(event_response[2],event_response[3])),compound_merit=float(max(changed[2],changed[3])),
            actual_event_switch=event_switch,endpoint_branch_escape=escape,strict_original_parent_decrease=improved,
            supports_candidate=bool(event_switch and escape and improved),parent_activity=q4(base),event_activity=q4(event_response),compound_activity=q4(changed),
            compound_equilibrium=float(changed[2]),compound_gap=float(changed[3]),linear_max_abs=float(np.max(np.abs(linear))),
            budget=dict(parent_preparation_assemblies=1,candidate_slots=3,candidate_limit=13,actual_global_solves=1,
                charged_corrections_including_saved_parent_solve=2,correction_limit=24),
            prefix_bytes_equal=owner.checkpoint()==raw,generation=owner._generation,origin_bytes_equal=digest(origins)==origin_sha,
            controller_bytes_equal=encoded(driver._adaptive_state)==controller,history_commits=0)
        assert result['prefix_bytes_equal'] and result['origin_bytes_equal'] and result['controller_bytes_equal'] and owner._generation==3
        write(folder/'result.json',result);return result
    finally:
        for control in reversed(controls):control.stop()
        write(folder/'counts.json',[dict(stage=s,method=m,count=v) for (s,m),v in counts.items()])
        write(folder/'partial-result.json',result)
        if owner is not None:owner.close()

