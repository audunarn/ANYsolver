"""One copied actual-state force error budget; never solve or commit."""
import argparse,copy,hashlib,json,pickle,time
from pathlib import Path
from decimal import Decimal as D,localcontext
import numpy as np
import arc_reference as arc
import anysolver.corotational as cr
from shell_precision_probe import decimal_array,precise_deformation,atan,norm,mean


def planar_beam(X,u):
    chord=(X+u[:,:3])[-1]-(X+u[:,:3])[0]
    length=norm(chord); c=chord[0]/length; s=-chord[2]/length
    angle=atan(s/c)
    Rt=np.array([[c,D(0),-s],[D(0),D(1),D(0)],[s,D(0),c]],dtype=object)
    arm=X-mean(X); trans=u[:,:3]-mean(u[:,:3]); value=np.empty(u.shape,dtype=object)
    for i in range(len(X)):
        value[i,:3]=Rt@trans[i]+(Rt-decimal_array(np.eye(3)))@arm[i]
        value[i,3:]=[D(0),u[i,4]-angle,D(0)]
    return value.reshape(-1)


def reduce_decimal(T,full):
    result=np.array([D(0)]*T.shape[1],dtype=object)
    coo=T.tocoo()
    for i,j,v in zip(coo.row,coo.col,coo.data): result[j]+=D.from_float(float(v))*full[i]
    return result


def main():
    p=argparse.ArgumentParser(); p.add_argument('capture'); p.add_argument('output'); a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=False); started=time.perf_counter()
    model,load,*_=arc.build_model(32,'matching',arc.oracle(0.,30.))
    refs=cr._corotational_cache(model); rows=[]; raws={}; capture=Path(a.capture)
    for filename in ['raw-0116-unaccepted-after-linear-solve.pkl','raw-0118-unaccepted-after-linear-solve.pkl']:
        path=capture/filename; data=pickle.loads(path.read_bytes()); before=pickle.dumps(data)
        u=data['u']; T=data['T']; size=len(u); current=np.zeros(size); errors={k:np.zeros(size) for k in ['shell','beam']}
        exact=np.array([D(0)]*size,dtype=object); remainder=np.zeros(size); element_rows=[]
        assert not data['rotating_map_active']
        with localcontext() as ctx:
            ctx.prec=70
            for eid,ref in refs.items():
                if ref.category not in errors: continue
                el=model.mesh.elements[eid]; dofs=np.array(el.get_dof_mapping(model.mesh)); ue=u[dofs].reshape(el.num_nodes,6)
                assert np.max(np.abs(ue[:,[1,3,5]]))==0.
                X=ref.coordinates.copy(); dX=decimal_array(X); du=decimal_array(ue)
                planar=np.array([6*i+j for i in range(el.num_nodes) for j in [0,2,4]])
                if ref.category=='shell':
                    dx,de=ref.center_dN
                    evaluate=lambda v:precise_deformation(dX,v,decimal_array(dx),decimal_array(de))
                else: evaluate=lambda v:planar_beam(dX,v)
                value=evaluate(du); B=np.empty((ue.size,len(planar)),dtype=object); h=D('1e-25')
                for k,j in enumerate(planar):
                    plus=du.copy().reshape(-1); minus=plus.copy(); plus[j]+=h; minus[j]-=h
                    B[:,k]=(evaluate(plus.reshape(ue.shape))-evaluate(minus.reshape(ue.shape)))/(D(2)*h)
                material=model.get_material(el.material_name); stiffness=el.compute_stiffness_matrix(model.mesh,material)
                local_exact=decimal_array(stiffness)@value; force=np.array([D(0)]*ue.size,dtype=object)
                force[planar]=B.T@local_exact
                value_float=np.asarray(value,dtype=float)
                accurate_local,*_=el.compute_nonlinear_response(model.mesh,material,value_float,copy.deepcopy(data['committed_states'].get(eid)),data['num_layers'],False)
                local_remainder=accurate_local-stiffness@value_float
                force_remainder=np.zeros(ue.size); force_remainder[planar]=np.asarray(B,dtype=float).T@local_remainder
                vd,R,geom=cr._corotational_deformation_state(ref,el,ue.reshape(-1))
                dd,uu,gg=cr._pullback_jacobian_factors(ref,el,geom,ue[:,3:],R); actualB=dd+uu@gg
                ff,*_=el.compute_nonlinear_response(model.mesh,material,vd,copy.deepcopy(data['committed_states'].get(eid)),data['num_layers'],False)
                actual=actualB.T@ff; np.add.at(current,dofs,actual)
                np.add.at(errors[ref.category],dofs,actual-np.asarray(force,dtype=float))
                np.add.at(remainder,dofs,force_remainder)
                for i,j in enumerate(dofs): exact[j]+=force[i]
                element_rows.append(dict(eid=eid,category=ref.category,local_law_remainder=float(np.linalg.norm(local_remainder)),pulled_remainder=float(np.linalg.norm(force_remainder)),force_error=float(np.linalg.norm(actual-np.asarray(force,dtype=float))),deformation_error=float(np.linalg.norm(vd-value_float)),planar_jacobian_error=float(np.linalg.norm(actualB[:,planar]-np.asarray(B,dtype=float)))))
                assert np.array_equal(X,ref.coordinates)
            reduced_exact=reduce_decimal(T,exact); external=decimal_array(data['F_ext_red']); accurate_residual=external-reduced_exact
            corrected_residual=np.asarray(accurate_residual,dtype=float)-np.asarray(T.T@remainder).reshape(-1)
        matrix=data['matrix']; rhs=data['rhs']; delta=data['delta']; q=data['q_trial']; updated=q+delta
        representable=updated-q; ulp=np.abs(np.spacing(q)); nz=ulp>0
        assert pickle.dumps(data)==before
        row=dict(file=filename,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),stamp=data['stamp'],reference=data['reference'],captured_residual=data['residual_norm'],captured_relative=data['relative_residual'],planarity_verified=True,
            assembly_closure=float(np.linalg.norm(current-data['F_int'])),assembly_closure_reduced=float(np.linalg.norm(T.T@(current-data['F_int']))),
            residual_reconstruction=float(np.linalg.norm(data['F_ext_red']-T.T@data['F_int']-data['residual'])),
            accurate_elastic_residual=float(np.linalg.norm(np.asarray(accurate_residual,dtype=float))),accurate_with_float_local_remainder_residual=float(np.linalg.norm(corrected_residual)),
            local_remainder_reduced=float(np.linalg.norm(T.T@remainder)),
            category_errors={k:dict(full=float(np.linalg.norm(v)),reduced=float(np.linalg.norm(T.T@v))) for k,v in errors.items()},
            actual_linear_backward_error=float(np.linalg.norm(matrix@delta-rhs)/max(np.linalg.norm(rhs),1e-300)),
            delta_norm=float(np.linalg.norm(delta)),coordinate_count=len(q),changed_coordinate_count=int(np.count_nonzero(updated!=q)),
            delta_below_half_ulp=int(np.count_nonzero(np.abs(delta)<.5*ulp)),max_delta_in_ulps=float(np.max(np.abs(delta[nz])/ulp[nz])),
            represented_correction_norm=float(np.linalg.norm(representable)),unrepresented_correction_norm=float(np.linalg.norm(delta-representable)),
            achieved_linear_change=float(np.linalg.norm(matrix@representable-rhs)),elements=element_rows,inputs_unchanged=True)
        rows.append(row); raws[filename]=dict(exact=exact,current=current,remainder=remainder,errors=errors,accurate_residual=accurate_residual,corrected_residual=corrected_residual)
        (out/'partial.json').write_text(json.dumps(dict(rows=rows,elapsed=time.perf_counter()-started),indent=2))
    report=dict(diagnostic_only=True,no_FE_solve=True,decimal_digits=70,float64_mantissa=np.finfo(float).nmant,longdouble_mantissa=np.finfo(np.longdouble).nmant,
                reference='Same float geometry/u/stiffness and captured external force; Decimal planar pullback with independent symmetric 1e-25 derivative. Float nonlinear local-law remainder measured separately, not silently discarded.',
                limitations='Frozen float stiffness/constitutive arithmetic remain; high-precision planar subspace verified against current full assembly. No constitutive high-precision implementation or true arithmetic lower-bound claim.',rows=rows,elapsed=time.perf_counter()-started)
    (out/'raw.pkl').write_bytes(pickle.dumps(raws)); (out/'result.json').write_text(json.dumps(report,indent=2)); print(json.dumps({k:v for k,v in report.items() if k!='rows'}))


if __name__=='__main__': main()
