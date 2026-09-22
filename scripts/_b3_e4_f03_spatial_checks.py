"""Fixed-cell recovery and independent integral identities for saved states.

This is a classical diagnostic, not a native element or equilibrium driver.
The adjudicator consumes the bounded raw integrals; it does not repeat a
structural solve or pretend that small integration defects establish accuracy.
"""
from __future__ import annotations

import json
from fractions import Fraction

import numpy as np
from numpy.polynomial import legendre as lg

from scripts import _b3_e4_f03_primal_exact_pose as exact
from scripts import _b3_e4_f03_spatial_contract as c
from scripts import _b3_e4_f03_spatial_fields as physical
from scripts import _b3_e4_f03_spatial_tests as tests


SCHEMA='f03_spatial_residual_integrals_v1'
MAX_JSON_BYTES=32*1024**2
RULE_SHAPES={
    'cell_load_wrenches':(45,3,3),
    'cell_residual_wrenches':(45,3),
    'cell_residual_squares':(45,),
    'cell_load_work':(45,27,3),
    'cell_strain_work':(45,27),
    'cell_volume_work':(45,27),
    'cell_shell_energy':(45,),
    'free_wrenches':(18,3),
    'free_traction_squares':(18,),
    'free_work':(18,27),
    'support_wrenches':(10,3),
    'support_work':(10,27),
    'trace_work':(27,3),
    'beam_weak_work_parts':(27,3),
    'beam_energy_load_root_work':(3,),
}
SIDE_SHAPES={'coordinates':(45,4,3,2),'stress':(45,4,3,3),
             'divergence':(45,4,3,2),'load_channels':(45,4,3,3,2),
             'residual':(45,4,3,2)}
DESC_SHAPES={'density_difference':None,'atom_difference':(2,3),
             'old_reactions':(2,3)}
WRENCH_SCALE=np.array((c.F0,c.F0,c.F0*c.L0))
RIGID_SCALE=np.array((c.U0,c.U0,c.U0/c.L0))


def work_counts():
    points=sum(c.ORDERS)
    return {'saved_state_compilations':1,'fixed_rule_integrations':2,
            'exact_pose_decodes':3,'functional_binding_checks':2,
            'raw_integral_adjudications':2,
            'shell_field_calls':2*73+45,
            'shell_field_points':45*sum(o*o for o in c.ORDERS)+28*points+540,
            'area_adjoint_calls':2*45+45,
            'area_adjoint_points':45*sum(o*o for o in c.ORDERS)+540,
            'test_field_calls':2*73,'test_field_points':
                45*sum(o*o for o in c.ORDERS)+28*points,
            'trace_calls':4,'trace_station_points':points+4,
            'density_calls':2,'section_calls':2,
            'functional_reconstructions':3,'reaction_recoveries':4,
            'one_sided_cell_evaluations':45,'one_sided_points':540,
            'equilibrium_solves':0,'element_stiffness_assemblies':0,
            'old_numerical_verifications':0,'projection_constructions':0,
            'green_norm_evaluations':0}


def definition_record():
    return {'schema':SCHEMA,'rule_shapes':{k:list(v) for k,v in RULE_SHAPES.items()},
            'one_sided_shapes':{k:list(v) for k,v in SIDE_SHAPES.items()},
            'orders':list(c.ORDERS),'test_fields':tests.definition_record(),
            'work':work_counts(),'json_bytes':MAX_JSON_BYTES,
            'functional_coefficients':'exact canonical rational channel-major '
                'Legendre density, plus separate cosine and endpoint atoms',
            'work_part_order':['distributed_load','negative_beam_internal',
                               'negative_root_multiplier'],
            'sides':['left','right','bottom','top'],
            'side_locations':['first_corner','midpoint','second_corner'],
            'check_limit':c.IDENTITY_LIMIT,
            'scope':'reconstruction and integration only; no physical error bound'}


def _integral(weights,values):
    return np.tensordot(weights,values,axes=(tuple(range(weights.ndim)),
                                              tuple(range(weights.ndim))))


def _wrench(x,y,force):
    return np.stack((force[...,0],force[...,1],
                     x*force[...,1]-y*force[...,0]),axis=-1)


def _traction(stress,nx,ny):
    return np.stack((nx*stress[...,0]+ny*stress[...,2],
                     nx*stress[...,2]+ny*stress[...,1]),axis=-1)


def _rule(model,pose,order):
    if order not in c.ORDERS:
        raise ValueError('unregistered spatial integration order')
    raw={key:np.zeros(shape,dtype=np.float64) for key,shape in RULE_SHAPES.items()}
    nodes,weights=np.polynomial.legendre.leggauss(order)
    for index,(xl,xh,yl,yh) in enumerate(c.CELLS):
        xv=(float(xl+xh)+float(xh-xl)*nodes)/2
        yv=(float(yl+yh)+float(yh-yl)*nodes)/2
        x,y=np.meshgrid(xv,yv,indexing='xy')
        w=np.outer(weights,weights)*float((xh-xl)*(yh-yl))/4
        f=physical.shell_fields(model,x,y)
        load=physical.area_load(model,x,y,index)
        residual=f['divergence']+load.sum(axis=-2)
        z=tests.fields(x,y)
        raw['cell_load_wrenches'][index]=_integral(w,_wrench(
            x[...,None],y[...,None],load))
        raw['cell_residual_wrenches'][index]=_integral(w,_wrench(x,y,residual))
        raw['cell_residual_squares'][index]=_integral(w,np.sum(residual**2,axis=-1))
        raw['cell_load_work'][index]=_integral(w,np.einsum(
            '...fc,...ac->...fa',z['values'],load))
        raw['cell_strain_work'][index]=_integral(w,np.einsum(
            '...fc,...c->...f',z['strain'],f['stress']))
        raw['cell_volume_work'][index]=_integral(w,np.einsum(
            '...fc,...c->...f',z['values'],residual))
        raw['cell_shell_energy'][index]=_integral(w,.5*np.sum(
            f['strain']*f['stress'],axis=-1))
    for index,(side,_,xl,xh,y0) in enumerate(c.FREE_EDGES):
        x=(float(xl+xh)+float(xh-xl)*nodes)/2
        y=np.full_like(x,float(y0));w=weights*float(xh-xl)/2
        f=physical.shell_fields(model,x,y);z=tests.fields(x,y)
        traction=_traction(f['stress'],0,side)
        raw['free_wrenches'][index]=_integral(w,_wrench(x,y,traction))
        raw['free_traction_squares'][index]=_integral(w,np.sum(traction**2,axis=-1))
        raw['free_work'][index]=_integral(w,np.einsum(
            '...fc,...c->...f',z['values'],traction))
    for side in (-1,1):
        for j,(yl,yh) in enumerate(zip(c.Y_CUTS[:-1],c.Y_CUTS[1:])):
            index=(0 if side==-1 else 5)+j
            y=(float(yl+yh)+float(yh-yl)*nodes)/2
            x=np.full_like(y,-.5 if side==-1 else 1.5)
            w=weights*float(yh-yl)/2
            f=physical.shell_fields(model,x,y);z=tests.fields(x,y)
            traction=_traction(f['stress'],side,0)
            raw['support_wrenches'][index]=_integral(w,_wrench(x,y,traction))
            raw['support_work'][index]=_integral(w,np.einsum(
                '...fc,...c->...f',z['values'],traction))
    s=(nodes+1)*c.L0/2;ds=weights*c.L0/2
    trace=tests.trace(s);end=tests.trace(np.array((0.,c.L0)))
    density=physical.line_density(model,s)
    section=physical.section_resultants(model,s)
    raw['trace_work'][:,0]=_integral(ds,np.einsum(
        '...fc,...c->...f',trace['values'],density))
    for e in (0,1):
        raw['trace_work'][:,e+1]=end['values'][e]@model.atoms[e]
    load=c.F0/c.L0+c.F0/(4*c.L0)*np.cos(c.OMEGA*s)
    v=trace['values'];dv=trace['derivative']
    raw['beam_weak_work_parts'][:,0]=_integral(ds,load[:,None]*v[...,1])
    raw['beam_weak_work_parts'][:,1]=-_integral(ds,
        section[:,0,None]*dv[...,0]+
        section[:,1,None]*(dv[...,1]-v[...,2])+
        section[:,2,None]*dv[...,2])
    raw['beam_weak_work_parts'][:,2]=-end['values'][0]@np.array(
        [float(v) for v in model.eta])
    b=np.stack([lg.legval(2*s/c.L0-1,[float(v) for v in p])
                for p in pose.legendre],axis=-1)
    b0=np.array([sum(float(v)*(-1)**k for k,v in enumerate(p))
                 for p in pose.legendre])
    raw['beam_energy_load_root_work'][:]=(
        _integral(ds,.5*np.sum(section**2/np.array((c.EA,c.GAS,c.EI)),axis=-1)),
        _integral(ds,load*b[:,1]),
        b0@np.array([float(v) for v in model.eta]))
    return {key:value.tolist() for key,value in raw.items()}


def _one_sided(model):
    raw={key:np.zeros(shape,dtype=np.float64) for key,shape in SIDE_SHAPES.items()}
    for index,(xl,xh,yl,yh) in enumerate(c.CELLS):
        xy=_side_coordinates(xl,xh,yl,yh)
        x=xy[...,0];y=xy[...,1]
        f=physical.shell_fields(model,x,y);load=physical.area_load(model,x,y,index)
        raw['coordinates'][index]=xy;raw['stress'][index]=f['stress']
        raw['divergence'][index]=f['divergence'];raw['load_channels'][index]=load
        raw['residual'][index]=f['divergence']+load.sum(axis=-2)
    return {key:value.tolist() for key,value in raw.items()}


def _side_coordinates(xl,xh,yl,yh):
    xl,xh,yl,yh=map(float,(xl,xh,yl,yh));xm=(xl+xh)/2;ym=(yl+yh)/2
    return np.array([[(xl,yl),(xl,ym),(xl,yh)],
                     [(xh,yl),(xh,ym),(xh,yh)],
                     [(xl,yl),(xm,yl),(xh,yl)],
                     [(xl,yh),(xm,yh),(xh,yh)]])


def _pair(value):
    return [str(value.numerator),str(value.denominator)]


def _identical(observed,expected):
    if type(observed) is not type(expected):
        raise ValueError('spatial saved binding type mismatch')
    if isinstance(expected,dict):
        if set(observed)!=set(expected):
            raise ValueError('spatial saved binding keys mismatch')
        for key in expected: _identical(observed[key],expected[key])
    elif isinstance(expected,list):
        if len(observed)!=len(expected):
            raise ValueError('spatial saved binding list length mismatch')
        for a,b in zip(observed,expected): _identical(a,b)
    elif isinstance(expected,float):
        if observed.hex()!=expected.hex():
            raise ValueError('spatial saved binding float mismatch')
    elif observed!=expected:
        raise ValueError('spatial saved binding value mismatch')


def evaluate_saved(n,arrays,pose_record):
    # from_record validates exact coefficients, not only metadata or q identity.
    pose=exact.from_record(pose_record)
    model=physical.model_from_saved(n,arrays['q'],arrays['eta'],pose)
    density=np.array([[float(v) for v in p] for p in model.density_coefficients]).T
    record={'schema':SCHEMA,'degree':n,'orders':list(c.ORDERS),
            'field_ids':list(tests.FIELD_IDS),'work':work_counts(),
            'functional':{'density':[[_pair(v) for v in p]
                                    for p in model.density_coefficients],
                          'atoms':[[_pair(v) for v in row]
                                   for row in model.atom_coefficients],
                          'gamma':_pair(model.gamma),
                          'cosine':[0.,c.F0/(4*c.L0),0.]},
            'rules':{str(o):_rule(model,pose,o) for o in c.ORDERS},
            'one_sided':_one_sided(model),
            'descriptive_parent':{
                'density_difference':(density-arrays['density_coefficients']).tolist(),
                'atom_difference':(model.atoms-arrays['atoms']).tolist(),
                'old_reactions':np.asarray(arrays['edge_route1']).tolist()}}
    # A checked record contains raw data only: the supervisor independently
    # computes identities and descriptive summaries from these integrals.
    return record


def validate_saved_binding(record,n,arrays,pose_record):
    """Small exact functional/state binding, without spatial field recovery.

    Called once in the child and once by its independent receipt reader.
    Exact coefficients are checked against the validated saved pose; copied
    parent data and floating descriptive differences require bit equality.
    """
    pose=exact.from_record(pose_record)
    q=arrays['q'];eta=arrays['eta']
    if (pose.n!=n or not isinstance(q,np.ndarray) or q.dtype!=np.float64 or
            q.shape!=(2*(n*n-1),) or not np.all(np.isfinite(q)) or
            tuple(Fraction.from_float(float(v)) for v in q)!=pose.q or
            not isinstance(eta,np.ndarray) or eta.dtype!=np.float64 or
            eta.shape!=(3,) or not np.all(np.isfinite(eta))):
        raise ValueError('spatial saved-state binding mismatch')
    def derivative(p):
        # Independent explicit coefficient derivative in the physical s chart.
        return tuple(sum((p[k]*(2*j+1)*2/c.Q_L0
                          for k in range(j+1,len(p),2)),Fraction(0))
                     for j in range(len(p)))
    bu,bv,theta=pose.legendre
    section=(tuple(c.Q_EA*v for v in derivative(bu)),
             tuple(c.Q_GAS*(v-t) for v,t in zip(derivative(bv),theta)),
             tuple(c.Q_EI*v for v in derivative(theta)))
    density=(derivative(section[0]),
             tuple(v+(c.Q_F0/c.Q_L0 if k==0 else 0)
                   for k,v in enumerate(derivative(section[1]))),
             tuple(v+qv for v,qv in zip(derivative(section[2]),section[1])))
    atoms=tuple(tuple(sum((v*(side**k) for k,v in enumerate(p)),Fraction(0))
                *(1 if side==-1 else -1)-
                (Fraction.from_float(float(eta[i])) if side==-1 else 0)
                for i,p in enumerate(section)) for side in (-1,1))
    expected={'density':[[_pair(v) for v in row] for row in density],
              'atoms':[[_pair(v) for v in row] for row in atoms],
              'gamma':_pair(pose.gamma),'cosine':[0.,c.F0/(4*c.L0),0.]}
    _identical(record['functional'],expected)
    d=np.array([[float(v) for v in row] for row in density]).T
    a=np.array([[float(v) for v in row] for row in atoms])
    previous={key:np.asarray(arrays[key]) for key in
              ('density_coefficients','atoms','edge_route1')}
    for key,shape in (('density_coefficients',(n+1,3)),('atoms',(2,3)),
                      ('edge_route1',(2,3))):
        if previous[key].dtype!=np.float64 or previous[key].shape!=shape or not np.all(
                np.isfinite(previous[key])):
            raise ValueError('invalid spatial parent description')
    _identical(record['descriptive_parent'],{
        'density_difference':(d-previous['density_coefficients']).tolist(),
        'atom_difference':(a-previous['atoms']).tolist(),
        'old_reactions':previous['edge_route1'].tolist()})


def _finite_array(value,shape,name):
    def walk(v,dims):
        if not dims:
            if type(v) not in (float,int):
                raise ValueError(f'nonfinite/non-numeric spatial value: {name}')
            try: finite=np.isfinite(float(v))
            except (OverflowError,ValueError) as exc:
                raise ValueError(f'unrepresentable spatial value: {name}') from exc
            if not finite:
                raise ValueError(f'nonfinite spatial value: {name}')
            return
        if type(v) is not list or len(v)!=dims[0]:
            raise ValueError(f'spatial shape mismatch: {name}')
        for item in v: walk(item,dims[1:])
    walk(value,shape)
    return np.array(value,dtype=np.float64)


def _fraction(value):
    if (type(value) is not list or len(value)!=2 or
            any(type(v) is not str or len(v)>4096 for v in value)):
        raise ValueError('invalid bounded spatial rational pair')
    try: fraction=Fraction(int(value[0]),int(value[1]))
    except (ValueError,ZeroDivisionError) as exc:
        raise ValueError('invalid spatial rational integers') from exc
    if _pair(fraction)!=value:
        raise ValueError('noncanonical spatial rational pair')
    return fraction


def _error(a,b,floor):
    a=np.asarray(a);b=np.asarray(b)
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError('nonfinite derived spatial identity inputs')
    with np.errstate(over='raise',invalid='raise',divide='raise'):
        try:
            value=float(np.max(np.abs(a-b)/np.maximum(floor,np.maximum(np.abs(a),np.abs(b)))))
        except FloatingPointError as exc:
            raise ValueError('overflow in spatial identity arithmetic') from exc
    if not np.isfinite(value): raise ValueError('nonfinite spatial identity metric')
    return value


def _scaled_error(a,b,scale):
    a=np.asarray(a);b=np.asarray(b)
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError('nonfinite derived spatial physical identity inputs')
    with np.errstate(over='raise',invalid='raise',divide='raise'):
        try: value=float(np.max(np.abs(a-b)/scale))
        except FloatingPointError as exc:
            raise ValueError('overflow in spatial physical identity') from exc
    if not np.isfinite(value): raise ValueError('nonfinite spatial physical metric')
    return value


def adjudicate_record(record,n):
    if (type(n) is not int or not 2<=n<=24 or type(record) is not dict or
            set(record)!={'schema','degree','orders','field_ids','work','functional',
                          'rules','one_sided','descriptive_parent'} or
            record['schema']!=SCHEMA or type(record['degree']) is not int or
            record['degree']!=n or record['orders']!=list(c.ORDERS) or
            any(type(v) is not int for v in record['orders']) or
            record['field_ids']!=list(tests.FIELD_IDS) or
            record['work']!=work_counts() or
            any(type(v) is not int for v in record['work'].values())):
        raise ValueError('spatial record identity mismatch')
    if len(json.dumps(record,allow_nan=False).encode('utf-8'))>MAX_JSON_BYTES:
        raise ValueError('spatial JSON exceeds 32MiB')
    func=record['functional']
    if type(func) is not dict or set(func)!={'density','atoms','gamma','cosine'}:
        raise ValueError('spatial functional inventory mismatch')
    for key,shape in (('density',(3,n+1)),('atoms',(2,3))):
        value=func[key]
        if (type(value) is not list or len(value)!=shape[0] or
                any(type(row) is not list or len(row)!=shape[1] for row in value)):
            raise ValueError('spatial functional shape mismatch')
        for row in value:
            for pair in row: _fraction(pair)
    if _fraction(func['gamma'])!=c.Q_GAMMA:
        raise ValueError('spatial held-J gamma changed')
    if func['cosine']!=[0.,c.F0/(4*c.L0),0.]:
        raise ValueError('spatial cosine changed')
    _finite_array(func['cosine'],(3,),'cosine')
    if type(record['rules']) is not dict or set(record['rules'])!={'48','64'}:
        raise ValueError('spatial fixed-rule inventory mismatch')
    rules={}
    for order,value in record['rules'].items():
        if type(value) is not dict or set(value)!=set(RULE_SHAPES):
            raise ValueError('spatial raw integral inventory mismatch')
        rules[order]={key:_finite_array(value[key],shape,key)
                      for key,shape in RULE_SHAPES.items()}
        if any(np.any(rules[order][key]<0) for key in
               ('cell_residual_squares','free_traction_squares','cell_shell_energy')):
            raise ValueError('negative squared integral or elastic energy')
        if rules[order]['beam_energy_load_root_work'][0]<0:
            raise ValueError('negative elastic beam energy')
    side=record['one_sided']
    if type(side) is not dict or set(side)!=set(SIDE_SHAPES):
        raise ValueError('spatial one-sided inventory mismatch')
    side={key:_finite_array(side[key],shape,key) for key,shape in SIDE_SHAPES.items()}
    expected_xy=np.stack([_side_coordinates(*cell) for cell in c.CELLS])
    if not np.array_equal(side['coordinates'],expected_xy):
        raise ValueError('spatial one-sided coordinates changed')
    desc=record['descriptive_parent']
    if type(desc) is not dict or set(desc)!=set(DESC_SHAPES):
        raise ValueError('spatial parent description inventory mismatch')
    desc={key:_finite_array(desc[key],(n+1,3) if key=='density_difference'
                            else shape,key) for key,shape in DESC_SHAPES.items()}
    metrics={};summaries={}
    metrics['one_sided_residual_identity']=_error(side['residual'],
        side['divergence']+side['load_channels'].sum(axis=-2),c.F0/c.L0**2)
    for order,r in rules.items():
        area=r['cell_load_work'].sum(axis=0)
        strain=r['cell_strain_work'].sum(axis=0)
        volume=r['cell_volume_work'].sum(axis=0)
        free=r['free_work'].sum(axis=0);support=r['support_work'].sum(axis=0)
        mu=r['trace_work'].sum(axis=-1)
        weak=r['beam_weak_work_parts'].sum(axis=-1)
        prefix=f'order_{order}_'
        metrics[prefix+'cell_load_wrench_work']=_scaled_error(
            r['cell_load_wrenches'],r['cell_load_work'][:,:3,:].transpose(0,2,1)/RIGID_SCALE,
            WRENCH_SCALE)
        metrics[prefix+'cell_residual_wrench_work']=_scaled_error(
            r['cell_residual_wrenches'],r['cell_volume_work'][:,:3]/RIGID_SCALE,WRENCH_SCALE)
        metrics[prefix+'free_wrench_work']=_scaled_error(
            r['free_wrenches'],r['free_work'][:,:3]/RIGID_SCALE,WRENCH_SCALE)
        metrics[prefix+'support_wrench_work']=_scaled_error(
            r['support_wrenches'],r['support_work'][:,:3]/RIGID_SCALE,WRENCH_SCALE)
        metrics[prefix+'adjoint_channels']=_error(area,r['trace_work'],c.E0)
        metrics[prefix+'beam_weak_identity']=_error(mu,weak,c.E0)
        metrics[prefix+'strong_weak_identity']=_error(strain-area.sum(axis=-1),
                                                     free+support-volume,c.E0)
        metrics[prefix+'supported_test_trace']=_error(support[9:],0.,c.E0)
        metrics[prefix+'rigid_strain_work']=_error(strain[:3],0.,c.E0)
        reactions=(strain[3:9]-mu[3:9]).reshape(2,3)/RIGID_SCALE
        boundary_reactions=(support[3:9]+free[3:9]-volume[3:9]).reshape(2,3)/RIGID_SCALE
        metrics[prefix+'reaction_identity']=_scaled_error(reactions,boundary_reactions,WRENCH_SCALE)
        area_wrench=r['cell_load_wrenches'].sum(axis=(0,1))
        trace_wrench=mu[:3]/RIGID_SCALE
        metrics[prefix+'rigid_wrench']=_scaled_error(area_wrench,trace_wrench,WRENCH_SCALE)
        metrics[prefix+'global_reaction_balance']=_scaled_error(reactions.sum(axis=0),
                                                         -trace_wrench,WRENCH_SCALE)
        metrics[prefix+'divergence_theorem']=_scaled_error(
            r['cell_residual_wrenches'].sum(axis=0)-area_wrench,
            r['free_wrenches'].sum(axis=0)+r['support_wrenches'].sum(axis=0),WRENCH_SCALE)
        summaries[order]={'cell_residual_squared_scaled':(
                    r['cell_residual_squares']*c.L0**2/c.F0**2).tolist(),
            'free_traction_squared_scaled':(
                    r['free_traction_squares']*c.L0/c.F0**2).tolist(),
            'reactions':reactions.tolist(),
            'parent_reaction_difference':(reactions-desc['old_reactions']).tolist(),
            'area_wrench':area_wrench.tolist(),'trace_wrench':trace_wrench.tolist(),
            'shell_energy':float(r['cell_shell_energy'].sum()),
            'beam_energy':float(r['beam_energy_load_root_work'][0]),
            'external_work':float(r['beam_energy_load_root_work'][1]),
            'root_multiplier_work':float(r['beam_energy_load_root_work'][2])}
        summaries[order]['signed_physical_differences']={
            'reaction_identity':(reactions-boundary_reactions).tolist(),
            'rigid_wrench':(area_wrench-trace_wrench).tolist(),
            'global_reaction_balance':(reactions.sum(axis=0)+trace_wrench).tolist(),
            'divergence_theorem':(r['cell_residual_wrenches'].sum(axis=0)-area_wrench-
                (r['free_wrenches'].sum(axis=0)+r['support_wrenches'].sum(axis=0))).tolist()}
    summaries['signed_quadrature_differences']={}
    for key in RULE_SHAPES:
        floor=(WRENCH_SCALE if 'wrenches' in key else
               c.F0**2/c.L0**2 if key=='cell_residual_squares' else
               c.F0**2/c.L0 if key=='free_traction_squares' else c.E0)
        metrics['quadrature_'+key]=_error(rules['48'][key],rules['64'][key],floor)
        summaries['signed_quadrature_differences'][key]=(
            rules['48'][key]-rules['64'][key]).tolist()
    # JSON finiteness also guards descriptive reductions: a valid raw scalar
    # can still overflow during summation. No NaN may silently pass a limit.
    json.dumps({'metrics':metrics,'summaries':summaries},allow_nan=False)
    failures={key:value for key,value in metrics.items() if value>c.IDENTITY_LIMIT}
    return {'status':'FAILED_NUMERICAL_IDENTITY' if failures else
                    'PASSED_SPATIAL_RESIDUAL_DIAGNOSTIC',
            'metrics':metrics,'failures':failures,'summaries':summaries,
            'scope':'spatial numerical diagnostic; physical convergence unresolved'}
