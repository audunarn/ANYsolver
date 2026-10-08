"""Separate unchanged Q4 local update from its spatial pullback at saved state."""
from pathlib import Path
import hashlib,json,os,sys
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_ge_finite_experimental import _State
from anysolver._ge_beam3_variational_shell import deformation
from anysolver._stiffened_shell_algorithmic_pullback import spatial_response
from anysolver._ge_beam3_pose_joint import _exp_terms
from test_stiffened_shell_ge_distributing_material import definition
ROOT=Path(__file__).resolve().parent
assert Path(ss.__file__).resolve().is_relative_to(ROOT/'site')
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
owner=ss.create_analysis(definition=definition())
try:
    prefix=(ROOT/'failed-prefix-v9.bin').read_bytes();owner.restore(prefix)
    driver=owner._finite_driver
    with np.load(ROOT/'failed-base-v9.npz') as data:
        state=_State(*(data[name].copy() for name in ('q','frames','cells','resultants','multipliers')))
        direction=data['direction'].copy()
    assert state.shell_anchors is None
    prepared=[];size=owner._K.shape[0]
    predicted_material=np.zeros(size);predicted_total=np.zeros(size)
    def scatter(target,slots,value):np.add.at(target,slots,value)
    for (eid,element,slots,_),origin in zip(owner._shell_parts,driver._shell_origins):
        reference=np.array([owner._shell_model.mesh.nodes[node].coords() for node in element.node_ids])
        u=state.q[slots];vector=direction[slots]
        local,differential,second=deformation(reference,u,stable_translation=True)
        material=owner._shell_model.get_material(element.material_name)
        def update(values,element=element,material=material,origin=origin,eid=eid):
            prepared=driver._q4_corrections.get(eid)
            if prepared is None:
                return element.compute_nonlinear_response(owner._shell_model.mesh,material,values,origin,3,True)
            return element._compute_prepared_nonlinear_response(owner._shell_model.mesh,material,
                values,origin,3,True,prepared=prepared)
        force,tangent,candidate=update(local)
        chart=np.eye(24)
        for node,row in enumerate(u.reshape(-1,6)):
            chart[6*node+3:6*node+6,6*node+3:6*node+6]=_exp_terms(row[3:])[1]
        rowmap=np.linalg.solve(chart.T,differential.T)
        dl=differential@vector
        scatter(predicted_material,slots,rowmap@tangent@dl)
        scatter(predicted_total,slots,spatial_response(u,force,tangent,differential,second)[1]@vector)
        prepared.append((slots,reference,u,vector,local,dl,force,tangent,rowmap,update,origin,candidate))
    rows=owner._free;weights=owner._coordinate_scale[rows]
    from decimal import Decimal, localcontext
    def dec(x):return Decimal.from_float(float(x))
    def precise_affine_difference(ap,am,force,tangent,lp,lm,local,h):
        with localcontext() as ctx:
            ctx.prec=60
            dp=[dec(x)-dec(y) for x,y in zip(lp,local)]
            dm=[dec(x)-dec(y) for x,y in zip(lm,local)]
            kp=[sum((dec(k)*v for k,v in zip(row,dp)),Decimal(0)) for row in tangent]
            km=[sum((dec(k)*v for k,v in zip(row,dm)),Decimal(0)) for row in tangent]
            out=[]
            for ar,br in zip(ap,am):
                out.append(float((sum(((dec(a)-dec(b))*dec(f)+dec(a)*p-dec(b)*m
                    for a,b,f,p,m in zip(ar,br,force,kp,km)),Decimal(0)))/(2*dec(h))))
            return np.array(out)
    h=1e-6
    production=np.zeros(size);direct=np.zeros(size);factored=np.zeros(size);precise=np.zeros(size);increments=[]
    for slots,reference,u,vector,local,dl,force,tangent,rowmap,update,origin,candidate in prepared:
        maps=[];values=[];poses=[];production_poses=[]
        for sign in (1,-1):
            actual=u+sign*h*vector
            changed,differential,second=deformation(reference,actual,stable_translation=True)
            chart=np.eye(24)
            for node,row in enumerate(actual.reshape(-1,6)):
                chart[6*node+3:6*node+6,6*node+3:6*node+6]=_exp_terms(row[3:])[1]
            amap=np.linalg.solve(chart.T,differential.T)
            maps.append(amap);values.append(changed)
            poses.append(amap@(force+tangent@(changed-local)))
            production_poses.append(spatial_response(actual,force+tangent@(changed-local),tangent,differential,second)[0])
        ap,am=maps;lp,lm=values
        scatter(production,slots,(production_poses[0]-production_poses[1])/(2*h))
        scatter(direct,slots,(poses[0]-poses[1])/(2*h))
        scatter(factored,slots,((ap-am)@force+ap@tangent@(lp-local)-am@tangent@(lm-local))/(2*h))
        scatter(precise,slots,precise_affine_difference(ap,am,force,tangent,lp,lm,local,h))
        increments.append(dict(local_direction_norm=float(np.linalg.norm(dl)),
            local_direction_error=float(np.linalg.norm((lp-lm)/(2*h)-dl)),
            local_even_increment_norm=float(np.linalg.norm(lp+lm-2*local)),
            rowmap_increment_norm=float(np.linalg.norm(ap-am)),
            mapped_force_norm=float(np.linalg.norm(rowmap@force))))
    measures={}
    for name,observed in (('production',production),('direct',direct),('factored',factored),('precise_factored',precise)):
        norm=float(np.linalg.norm(predicted_total[rows]*weights))
        error=float(np.linalg.norm((observed-predicted_total)[rows]*weights))
        measures[name]=dict(predicted_norm=norm,absolute_error=error,relative_error=error/norm)
    result=dict(scope='single-h saved-state value/cancellation discriminator, not qualification',
        h=h,decimal_precision=60,model=owner._identity,pools=pools,measures=measures,
        increments=increments,direct_vs_precise=float(np.linalg.norm((direct-precise)[rows]*weights)),
        anchor_sha256=hashlib.sha256((ROOT/'failed-base-v9.npz').read_bytes()).hexdigest())
    assert owner.checkpoint()==prefix
    (ROOT/'value-cancellation-v19.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(measures))
finally:owner.close()
