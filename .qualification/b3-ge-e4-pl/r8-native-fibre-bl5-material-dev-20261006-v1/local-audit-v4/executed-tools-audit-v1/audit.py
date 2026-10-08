from pathlib import Path
from decimal import Decimal as D, localcontext
from unittest.mock import patch
import hashlib, json, math
import numpy as np
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_ge_experimental import ExperimentalGEAnalysis
from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver
from anysolver._ge_beam3_fibre_cell import FibreCellConjugate
from anysolver._ge_beam3_generalized_cell import GeneralizedCellConjugate
from anysolver._ge_beam3_retained_fibre import RetainedFibreOperator
from anysolver._ge_beam3_retained_generalized import RetainedGeneralizedOperator
from anysolver._ge_beam3_fibre_section import PhysicalFibreSection, canonical
from anysolver._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
from examples.stiffened_shell_native_fibre_bl5_material import definition

def execute(folder,evidence):
    calls=[];phase='compile';owner=None
    def record(cls,name):
        original=getattr(cls,name)
        def wrapped(self,*args,**kwargs):
            row=dict(index=len(calls),stage=phase,method=cls.__name__+'.'+name,
                     identity=getattr(self,'identity',None),status='running')
            calls.append(row)
            if phase=='audit' and (cls in (FinitePointDriver,RetainedFibreOperator,RetainedGeneralizedOperator)):
                raise AssertionError('local callback isolation violated')
            try:made=original(self,*args,**kwargs)
            except BaseException as error:
                row.update(status='failed',error=type(error).__name__+': '+str(error));raise
            row['status']='completed';return made
        return wrapped
    def forbidden(*args,**kwargs):raise AssertionError('global solve/continuation forbidden in local material audit')
    def decimal_pair(pair):return [D.from_float(float(a))+D.from_float(float(b)) for a,b in zip(*pair)]
    def gradient(response):return decimal_pair(response['gradient'])
    def hessian(response):return [decimal_pair(row) for row in response['hessian']]
    def action(matrix,vector):return [sum((a*b for a,b in zip(row,vector)),D(0)) for row in matrix]
    def norm(vector,weights):return sum(((a*b)**2 for a,b in zip(vector,weights)),D(0)).sqrt()
    def branches(cell,response,origin):
        captured=cell._origins(origin);result=[]
        for station,(row,old) in enumerate(zip(response['stations'],captured)):
            if type(cell) is FibreCellConjugate:
                fibres=[]
                for fibre,item,(z0,p0) in zip(cell.section.fibres,row['fibres'],old):
                    total=D.from_float(item.total_strain[0])+D.from_float(item.total_strain[1])
                    drive=D.from_float(fibre.young)*(total-z0)
                    radius=cell.section.fibres[len(fibres)].curve._at(p0)[0]
                    fibres.append(dict(fibre_id=fibre.fibre_id,branch=item.branch,
                        signed_trial_yield_margin=str(abs(drive)-radius),signed_trial_drive=str(drive),radius=str(radius),
                        algorithmic_modulus=item.algorithmic_modulus,plastic_increment=item.plastic_increment))
                result.append(dict(station=station,fibres=fibres))
            else:
                values=decimal_pair(row['resultants']);z0,p0=old
                metric=cell.section._m;equivalent=sum((values[i]*sum((metric[i][j]*values[j] for j in range(6)),D(0)) for i in range(6)),D(0)).sqrt()
                radius=D.from_float(cell.section.yield_force)+D.from_float(cell.section.hardening)*p0
                result.append(dict(station=station,branch=row['branch'],signed_trial_yield_margin=str(equivalent-radius),radius=str(radius)))
        return result
    def labels(rows):
        return tuple(tuple(f['branch'] for f in row['fibres']) if 'fibres' in row else row['branch'] for row in rows)
    controls=[]
    for cls,name in ((FibreCellConjugate,'response'),(GeneralizedCellConjugate,'response'),
                     (PhysicalFibreSection,'response'),(EllipsoidalGeneralizedSection,'response'),
                     (RetainedFibreOperator,'evaluate'),(RetainedGeneralizedOperator,'evaluate'),(FinitePointDriver,'_assemble')):
        controls.append(patch.object(cls,name,record(cls,name)))
    controls.extend((patch.object(ExperimentalGEAnalysis,'solve',forbidden),patch.object(FinitePointDriver,'_solve_fixed',forbidden)))
    for control in controls:control.start()
    try:
        owner=ss.create_analysis(definition=definition())
        raw=(evidence/'failed-prefix-bending-continuation-v1.bin').read_bytes()
        phase='restore';prefix=owner.restore(raw);assert owner.checkpoint()==raw
        driver=owner._finite_driver;origins=driver._beam_origins
        origin_bytes=[canonical(x) for x in origins]
        with np.load(evidence/'rejected-trial-state-v1/failed-Newton-trial.npz',allow_pickle=False) as saved:p0=saved['resultants'].copy()
        with np.load(evidence/'rejected-trial-state-v1/evaluation-130.npz',allow_pickle=False) as saved:plast=saved['resultants'].copy()
        direction=np.load(evidence/'rejected-trial-state-v1/failed-Newton-fullstep.npy',allow_pickle=False)
        assert p0.shape==plast.shape==(2,18) and direction.shape==(146,)
        generation=owner._generation;phase='audit';results=[]
        with localcontext() as context:
            context.prec=80
            h=D.from_float(1e-4);last_amount=D.from_float(1/4096)
            for i,(element,_,_) in enumerate(owner._beam_parts):
                cell=element.operator.cell;origin=origins[i];base=78+24*i+6
                dp=direction[base:base+18].copy()
                points=dict(base=p0[i],positive=p0[i]+1e-4*dp,negative=p0[i]-1e-4*dp,last=plast[i])
                responses={};observed={}
                for name,point in points.items():
                    assert canonical(origin)==origin_bytes[i]
                    responses[name]=cell.response([float(x) for x in point],origin=origin,check=element.operator.guard)
                    assert responses[name]['origin'] is origin and canonical(origin)==origin_bytes[i]
                    observed[name]=branches(cell,responses[name],origin)
                    (folder/f'member-{i+1}-{name}.json').write_bytes(canonical(responses[name]))
                    assert len(responses[name]['gradient'][0])==18 and len(responses[name]['hessian'])==18
                    assert all(len(row[0])==len(row[1])==18 for row in responses[name]['hessian'])
                weights=[D.from_float(float(x)) for x in owner._coordinate_scale[base:base+18]]
                vector=[D.from_float(float(x)) for x in dp]
                g0,gp,gm,gl=(gradient(responses[k]) for k in ('base','positive','negative','last'))
                H0,Hl=(hessian(responses[k]) for k in ('base','last'))
                expected=action(H0,vector);actual=[(a-b)/(2*h) for a,b in zip(gp,gm)]
                error=[a-b for a,b in zip(actual,expected)]
                smooth_error=norm(error,weights)/max(norm(expected,weights),D(1))
                effective=[(D.from_float(float(a))-D.from_float(float(b)))/(2*h) for a,b in zip(points['positive'],points['negative'])]
                effective_error=norm([a-b for a,b in zip(actual,action(H0,effective))],weights)/max(norm(action(H0,effective),weights),D(1))
                delta=[D.from_float(float(a))-D.from_float(float(b)) for a,b in zip(points['last'],points['base'])]
                predicted=action(H0,delta);defect=[-(a-b-c) for a,b,c in zip(gl,g0,predicted)]
                jump=[-(a-b) for a,b in zip(action(Hl,vector),expected)]
                crossings=[str(last_amount-a/b) if b else None for a,b in zip(defect,jump)]
                stable=labels(observed['base'])==labels(observed['positive'])==labels(observed['negative'])
                results.append(dict(member=i+1,family=type(cell).__name__,cell_identity=cell.identity,section_identity=cell.section.identity,
                    origin_sha256=hashlib.sha256(origin_bytes[i]).hexdigest(),origin_identity=origin.cell_identity,
                    origin_bytes_unchanged=True,points={k:v.tolist() for k,v in points.items()},direction=dp.tolist(),
                    gradient_shape=[18],compliance_shape=[18,18],branch_rows=observed,explicit_branch_stable=stable,
                    smooth_relative_error=str(smooth_error),effective_input_relative_error=str(effective_error),
                    smooth_expected_weighted_norm=str(norm(expected,weights)),smooth_weighted_error_norm=str(norm(error,weights)),
                    smooth_pass=stable and smooth_error<=D('1e-5'),
                    signed_cross_defect=[str(v) for v in defect],weighted_signed_cross_defect=[str(v*w) for v,w in zip(defect,weights)],
                    weighted_compliance_jump_direction=[str(v*w) for v,w in zip(jump,weights)],
                    inferred_crossing_amounts=crossings,
                    derivative_kinds={k:v['derivative_kind'] for k,v in responses.items()},
                    local_iterations={k:dict(iterations=v['iterations'],evaluations=v['evaluations'],line_trials=v['line_trials'],residual=v['residual']) for k,v in responses.items()}))
        assert owner._generation==generation and owner.checkpoint()==raw
        assert all(canonical(x)==b for x,b in zip(origins,origin_bytes))
        audited=[x for x in calls if x['stage']=='audit']
        assert len(audited)==8 and all(x['method'] in ('FibreCellConjugate.response','GeneralizedCellConjugate.response') for x in audited)
        record_result=dict(status='completed' if all(x['smooth_pass'] for x in results) else 'criterion_failed',
            h=1e-4,criterion=1e-5,accepted_factor=prefix.load_factor,accepted_generation=generation,
            model_identity=owner.preflight()['identity'],accepted_checkpoint_sha256=hashlib.sha256(raw).hexdigest(),
            checkpoint_bytes_unchanged=True,history_origins_unchanged=True,compile_owners=1,fresh_restores=1,
            geometry_frozen=True,global_solves=0,global_failedstate_evaluations=0,local_audit_responses=8,
            results=results,calls=calls,
            limitation='Local cell isolation does not certify assembled/chart tangent or global convergence. Endpoint compliance jump is not a bound on geometric finite residual. Signed yield margins reconstruct declared drive/radius from already evaluated high/low station pairs; pair truncation limits apply.')
        (folder/'result.json').write_text(json.dumps(record_result,indent=2)+'\n')
        return record_result
    except BaseException as error:
        (folder/'failure.json').write_text(json.dumps(dict(type=type(error).__name__,message=str(error),stage=phase,calls=calls),indent=2)+'\n')
        raise
    finally:
        for control in reversed(controls):control.stop()
        if owner is not None:owner.close()
