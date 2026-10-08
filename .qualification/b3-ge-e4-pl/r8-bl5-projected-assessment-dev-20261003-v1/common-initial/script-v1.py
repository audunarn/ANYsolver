"""Independent reference-P1 work for a fixed projected material density.

Exact rational integration includes every native half-cell and reference shape
boundary. This is a common-action development check, not external execution or
mechanical equivalence between native and reference elements.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_info
from scripts.r8_bl5_external_affine_reference_dev import shape_weights

sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def integrated_projected_weights(left,right,intervals,halfcells,first_node=0):
    """Integrate hats times [1, reference half-cell average xi], exactly."""
    left,right=F(left),F(right)
    if (type(intervals) is not int or intervals<1 or type(halfcells) is not int or
        halfcells<2 or type(first_node) is not int or not 0<=left<right<=1 or
        (left*halfcells).denominator!=1 or (right*halfcells).denominator!=1):
        raise ValueError('positive unit trace and whole reference half-cell supports required')
    if (right-left)*halfcells<2:
        raise ValueError('projected affine support requires at least two half-cells')
    knots=sorted({left,right}|{F(i,intervals) for i in range(intervals+1)}|
                 {F(i,halfcells) for i in range(halfcells+1)})
    weights=({},{});pieces=[]
    for a,b in zip(knots,knots[1:]):
        if a<left or b>right: continue
        middle=(a+b)/2;edge=int(middle*halfcells)
        cell_left,cell_right=F(edge,halfcells),F(edge+1,halfcells)
        assert cell_left<=a<b<=cell_right
        xi=(cell_left+cell_right-2*left)/(right-left)-1
        na,nb=shape_weights(a,intervals,first_node),shape_weights(b,intervals,first_node)
        for node in set(na)|set(nb):
            integral=(b-a)*(na.get(node,F(0))+nb.get(node,F(0)))/2
            for degree,coefficient in enumerate((F(1),xi)):
                weights[degree][node]=weights[degree].get(node,F(0))+integral*coefficient
        pieces.append((a,b,xi))
    assert sum(weights[0].values())==right-left and sum(weights[1].values())==0
    H=right-left;h=F(1,halfcells)
    expected=((right*right-left*left)/2,(H*H-h*h)/6)
    for degree in (0,1):
        assert sum(F(node-first_node,intervals)*v for node,v in weights[degree].items())==expected[degree]
    return weights,pieces


def common_rows(nx,nb,supports,shell_top,beam_arm):
    """Native-sign five channels; external virtual fields are nodal P1 poses.

    External engineering rows are beam-minus-shell translations and Rx/Ry.
    Native rows negate translations/Ry and retain Rx, with identical arm work.
    No scalar hat weight or endpoint term is dropped.
    """
    if any(type(v) is not int or v<1 for v in (nx,nb,supports)) or nb%supports:
        raise ValueError('whole-cell support and explicit positive layouts required')
    rs,rb=F(shell_top),F(beam_arm);count=6*(nx+nb+2);rows=[{} for _ in range(10*supports)]
    for support in range(supports):
        left,right=F(support,supports),F(support+1,supports)
        for intervals,first,sign,arm in ((nb,6*(nx+1),F(1),rb),(nx,0,F(-1),rs)):
            weights,_=integrated_projected_weights(left,right,intervals,nb)
            for degree,nodes in enumerate(weights):
                for node,w in nodes.items():
                    col=first+6*node
                    # Independent external common pose row -> native sign/order.
                    for channel in range(3):
                        row=rows[2*(channel*supports+support)+degree]
                        row[col+channel]=row.get(col+channel,F(0))-sign*w
                    for channel,component,orientation in ((3,4,-1),(4,3,1)):
                        row=rows[2*(channel*supports+support)+degree]
                        row[col+component]=row.get(col+component,F(0))+orientation*sign*w
                    row=rows[2*support+degree];row[col+4]=row.get(col+4,F(0))-sign*arm*w
                    row=rows[2*(supports+support)+degree];row[col+3]=row.get(col+3,F(0))+sign*arm*w
    rr=[];cc=[];vv=[]
    for row,entries in enumerate(rows):
        for column,value in entries.items():
            if value: rr.append(row);cc.append(column);vv.append(float(value))
    return sparse.coo_matrix((vv,(rr,cc)),shape=(len(rows),count)).tocsr()


def assess(root):
    from scripts.r8_bl5_projected_density_patch_dev import compile_saved_projection,IDENTITY
    (data,k,c,original,projected,_,_,_,_,_,_,_,_,_)=compile_saved_projection(root)
    nx=data['layout']['nx'];nb=2*nx;ns=len(data['layout']['shell_node_ids'])
    physical=data['layout']['counts']['physical_dofs'];supports=len(data['policy']['support_endpoints_m'])-1
    assert data['line']['shell_nodes']==list(range(1,nx+2))
    common=common_rows(nx,nb,supports,F(data['shell']['thickness_m'])/2,F(data['line']['expected_beam_arm'][2]))
    # A work-field interpolation, NOT mechanical condensation: physical nodal
    # virtual poses are copied; each independent native cell spin gets its mean
    # reference P1 spin. Resultant variables are untouched/zero in this map.
    rr=[];cc=[];vv=[]
    for i in range(nx+1):
        for component in range(6):rr.append(6*i+component);cc.append(6*i+component);vv.append(1.)
    for i in range(nb+1):
        for component in range(6):
            rr.append(6*ns+6*i+component);cc.append(6*(nx+1)+6*i+component);vv.append(1.)
    for member in range(nx):
        for cell in (0,1):
            for axis in range(3):
                for node in (2*member+cell,2*member+cell+1):
                    rr.append(physical+24*member+3*cell+axis)
                    cc.append(6*(nx+1)+6*node+3+axis);vv.append(.5)
    sampling=sparse.coo_matrix((vv,(rr,cc)),shape=(k.shape[0],common.shape[1])).tocsr()
    actual=projected@sampling;difference=actual-common
    relative=float(sparse.linalg.norm(difference)/max(1.,sparse.linalg.norm(common)))
    assert relative<=1e-12
    rng=np.random.default_rng(811);field=rng.normal(size=common.shape[1]);density=rng.normal(size=common.shape[0])
    native_work=float(density@(projected@(sampling@field)));reference_work=float(density@(common@field))
    dual_native=sampling.T@(projected.T@density);dual_reference=common.T@density
    assert abs(native_work-reference_work)<=1e-12*max(1.,abs(reference_work))
    assert np.max(np.abs(dual_native-dual_reference))<=1e-12
    # Include the complete endpoint difference; two interior nodes cannot detect it.
    h=F(1,4);projected_weights,_=integrated_projected_weights(0,1,4,4)
    expected=(-F(3,32),-F(1,8),F(0),F(1,8),F(3,32))
    assert tuple(projected_weights[1][i] for i in range(5))==expected
    return dict(candidate=IDENTITY,nx=nx,halfcells=nb,supports=supports,
        complete_common_matrix_relative=relative,noncompatible_common_work_J=[native_work,reference_work],
        complete_dual_action_max=float(np.max(np.abs(dual_native-dual_reference))),
        endpoint_change_vs_affine=['1/96','-1/96'],
        scope='virgin straight trace common work only; sampling is not a mechanical-state equivalence',
        source_files={name:sha(root/'native'/name) for name in ('inputs.json','operators.npz')})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--coarse',type=Path,required=True)
    p.add_argument('--fine',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    pools=threadpool_info();assert pools and all(v['num_threads']==1 for v in pools)
    result=dict(status='COMPLETED_DEVELOPMENT_ONLY',source_sha256=sha(__file__),pools=pools,
        helpers={name:sha(Path(__file__).parent/name) for name in ('r8_bl5_projected_density_patch_dev.py','r8_bl5_external_affine_reference_dev.py')},
        cases=[assess(a.coarse),assess(a.fine)])
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([v['complete_common_matrix_relative'] for v in result['cases']]))
