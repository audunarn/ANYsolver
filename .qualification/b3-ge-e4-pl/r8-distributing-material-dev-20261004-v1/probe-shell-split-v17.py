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
            return element._compute_prepared_nonlinear_response(owner._shell_model.mesh,material,
                values,origin,3,True,prepared=driver._q4_corrections[eid])
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
    record=[]
    for h in (1e-4,1e-5,4e-6,1e-6,1e-7):
        material_difference=np.zeros(size);affine_map_difference=np.zeros(size);branches=[]
        for slots,reference,u,vector,local,dl,force,tangent,rowmap,update,origin,candidate in prepared:
            plus=update(local+h*dl);minus=update(local-h*dl)
            scatter(material_difference,slots,rowmap@((plus[0]-minus[0])/(2*h)))
            poses=[]
            for sign in (1,-1):
                actual=u+sign*h*vector
                changed,differential,second=deformation(reference,actual,stable_translation=True)
                affine_force=force+tangent@(changed-local)
                poses.append(spatial_response(actual,affine_force,tangent,differential,second)[0])
            scatter(affine_map_difference,slots,(poses[0]-poses[1])/(2*h))
            branches.append(dict(active_base=int(np.count_nonzero(candidate['alpha']>origin['alpha'])),
                active_plus=int(np.count_nonzero(plus[2]['alpha']>origin['alpha'])),
                active_minus=int(np.count_nonzero(minus[2]['alpha']>origin['alpha']))))
        measures={}
        for name,observed,predicted in (('local_material',material_difference,predicted_material),
                                       ('affine_material_map',affine_map_difference,predicted_total)):
            predicted_norm=float(np.linalg.norm(predicted[rows]*weights))
            error=float(np.linalg.norm((observed-predicted)[rows]*weights))
            measures[name]=dict(predicted_norm=predicted_norm,absolute_error=error,
                relative_error=error/predicted_norm)
        record.append(dict(h=h,branches=branches,**measures))
    result=dict(scope='saved-state development discriminator, not qualified tangent',
        model=owner._identity,pools=pools,measures=record,
        anchor_sha256=hashlib.sha256((ROOT/'failed-base-v9.npz').read_bytes()).hexdigest(),
        imports={str(Path(m.__file__)):hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()
            for m in (sys.modules[deformation.__module__],sys.modules[spatial_response.__module__])})
    assert owner.checkpoint()==prefix
    (ROOT/'shell-split-v17.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps([dict(h=v['h'],material=v['local_material']['relative_error'],map=v['affine_material_map']['relative_error']) for v in record]))
finally:owner.close()
