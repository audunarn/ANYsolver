"""Independent finite-skin P1/P1 reference; no production contact imports."""
from decimal import Decimal,localcontext
from fractions import Fraction as F
import numpy as np


def director(theta,reference):
    with localcontext() as context:
        context.prec=80
        a=[Decimal(float(v)) for v in theta];term=[Decimal(float(v)) for v in reference];total=term.copy()
        for n in range(1,100):
            x,y,z=term;ax,ay,az=a
            term=[(ay*z-az*y)/n,(az*x-ax*z)/n,(ax*y-ay*x)/n]
            total=[v+w for v,w in zip(total,term)]
        return tuple(total)


def roles(definition):
    pair=definition.interactions[0];surfaces={s.name:s for s in definition.surfaces}
    return surfaces[pair.surface],surfaces[pair.target]


def oriented_ids(model,eid,definition):
    source,target=roles(definition)
    surface=source if eid in source.element_ids else target
    role=-1. if eid in source.element_ids else 1.
    element=model.mesh.elements[eid];ids=tuple(element.node_ids)
    reference=np.asarray(element.get_node_coordinates(model.mesh),float)
    desired=role*(-1. if surface.side=='bottom' else 1.)*np.asarray(element.reference_normal,float)
    alignment=float(np.cross(reference[1]-reference[0],reference[2]-reference[0])@desired)
    if not np.isfinite(alignment) or alignment==0:raise ValueError('independent reference orientation unresolved')
    return ids if alignment>0 else (ids[0],ids[2],ids[1])


def projected_axis_lower(model,sid,definition,normal):
    ids=oriented_ids(model,sid,definition)
    reference=np.array([(model.mesh.nodes[n].x,model.mesh.nodes[n].y,model.mesh.nodes[n].z) for n in ids])
    axis=np.cross(reference[1]-reference[0],reference[2]-reference[0]);j=int(np.argmax(abs(axis)))
    return normal[j][0] if axis[j]>0 else -normal[j][1]


def vertices(model,q,definition):
    source_surface,target_surface=roles(definition)
    sides={eid:surface.side for surface in (source_surface,target_surface) for eid in surface.element_ids}
    values={};boxes={}
    for eid,e in model.mesh.elements.items():
        h=float(.5*e.thickness*(-1. if sides[eid]=='bottom' else 1.)-getattr(e,'reference_surface_offset',0.))
        for nid in e.node_ids:
            n=model.mesh.nodes[nid];d=model.mesh.dof_manager.get_node_dofs(nid)
            theta=q[d[3:]]
            if sum(F(float(t))**2 for t in theta)>F(1.2)**2:raise ValueError('oracle finite-rotation envelope')
            exact=director(theta,e.reference_normal);point=[];box=[]
            for x,u,v in zip((n.x,n.y,n.z),q[d[:3]],exact):
                # Under ||theta||<=1.2, the 100-term exponential tail is below
                # 1e-140. Eighty-digit Decimal operations, <=100 bounded terms,
                # give <1e-70 absolute uncertainty. Subsequent box arithmetic is
                # exact rational; float conversion is only diagnostic/output.
                center=F(float(x))+F(float(u))+F(h)*F(v)
                radius=abs(F(h))*F(1,10**70)
                point.append(float(center));box.append((center-radius,center+radius))
            if nid in values and boxes[nid]!=tuple(box):raise ValueError('independent shared skin mismatch')
            values[nid]=np.asarray(point);boxes[nid]=tuple(box)
    return values,boxes


def add(a,b):return a[0]+b[0],a[1]+b[1]
def neg(a):return -a[1],-a[0]
def sub(a,b):return add(a,neg(b))
def mul(a,b):
    p=(a[0]*b[0],a[0]*b[1],a[1]*b[0],a[1]*b[1]);return min(p),max(p)
def vsub(a,b):return tuple(sub(x,y) for x,y in zip(a,b))
def cross(a,b):return tuple(sub(mul(a[i],b[j]),mul(a[j],b[i])) for i,j in ((1,2),(2,0),(0,1)))
def dot(a,b):
    terms=[mul(x,y) for x,y in zip(a,b)];return sum(v[0] for v in terms),sum(v[1] for v in terms)


def gap_bound(model,q,definition):
    source_surface,target_surface=roles(definition)
    _,p=vertices(model,q,definition);lower=F(0);margins=[]
    for sid in source_surface.element_ids:
        source=[p[n] for n in oriented_ids(model,sid,definition)]
        sn=cross(vsub(source[1],source[0]),vsub(source[2],source[0]))
        denominator=projected_axis_lower(model,sid,definition,sn)
        if denominator<=0:raise ValueError('independent source triangle projected normal unresolved')
        for tid in target_surface.element_ids:
            target=[p[n] for n in oriented_ids(model,tid,definition)]
            tn=cross(vsub(target[1],target[0]),vsub(target[2],target[0]))
            margin=dot(sn,tn)[0]
            if margin<=0:raise ValueError('independent P1/P1 relative chart unresolved')
            numerator=min(dot(vsub(x,y),sn)[0] for x in source for y in target)
            lower=min(lower,min(F(0),numerator)/denominator);margins.append(str(margin))
    return dict(lower_m=float(lower),lower_fraction=str(lower),gate_pass=lower>=-F(5e-5),
                chart_margin_fractions=margins,director_absolute_uncertainty='1e-70',all_pairs=len(source_surface.element_ids)*len(target_surface.element_ids))

def opening_bound(model,q,definition):
    """Strict separation of the actual P1 skins from both target P1 planes.

    Each target plane is fixed across its triangle. Its numerator on a P1
    source patch is affine, hence a convex combination of three corner
    numerators. Positive enclosed corner numerators imply positive distance
    everywhere. The rational L1 upper bound of the target normal also bounds
    its Euclidean norm. Positive source/target normal dot products certify
    that the declared source-normal projected gap has the same sign.
    """
    source_surface,target_surface=roles(definition)
    _,p=vertices(model,q,definition);pairs=[]
    for sid in source_surface.element_ids:
        s=[p[n] for n in oriented_ids(model,sid,definition)]
        ns=[cross(vsub(s[1],s[0]),vsub(s[2],s[0]))]
        for tid in target_surface.element_ids:
            t=[p[n] for n in oriented_ids(model,tid,definition)]
            tn=cross(vsub(t[1],t[0]),vsub(t[2],t[0]))
            numerators=[dot(vsub(x,t[0]),tn)[0] for x in s]
            margin=min(dot(n,tn)[0] for n in ns)
            norm_upper=sum(max(abs(a),abs(b)) for a,b in tn)
            positive=min(numerators)>0 and margin>0 and norm_upper>0
            distance=min(numerators)/norm_upper if norm_upper>0 else None
            pairs.append(dict(source_face=sid,target_face=tid,positive_separation=positive,
                corner_numerator_lower_fractions=[str(v) for v in numerators],
                source_target_normal_dot_lower_fraction=str(margin),
                target_normal_norm_upper_fraction=str(norm_upper),
                distance_lower_fraction=str(distance),distance_lower_m=float(distance) if distance is not None else None))
    return dict(gate_pass=all(v['positive_separation'] for v in pairs),pairs=pairs,
                minimum_distance_lower_m=min(v['distance_lower_m'] for v in pairs if v['distance_lower_m'] is not None),
                director_absolute_uncertainty='1e-70',all_pairs=len(source_surface.element_ids)*len(target_surface.element_ids),
                scope='fixture-specific exact rational interval whole-P1/P1 target-plane separation; positive sign witness, no changed 50um gate')


def source_plane_opening_bound(model,q,definition):
    """Positive declared gap on whole target triangles, including their overlap.

    For a planar source P1 face, every source point x satisfies
    n_s.(x-a_s)=0. Thus its source-normal gap from any target point y is
    n_s.(a_s-y)/||n_s||, independent of the selected source point. The numerator
    is affine over a P1 target face, so enclosed positive values at all three
    target corners prove positivity everywhere on it. Projected overlap is a
    subset. Positive mutual chart normals retain the declared projection sign.
    This does not require the larger source's corners to belong to the target.
    """
    source_surface,target_surface=roles(definition);_,p=vertices(model,q,definition);pairs=[]
    for sid in source_surface.element_ids:
        source=[p[n] for n in oriented_ids(model,sid,definition)]
        sn=cross(vsub(source[1],source[0]),vsub(source[2],source[0]))
        chart_lower=projected_axis_lower(model,sid,definition,sn)
        norm_upper=sum(max(abs(a),abs(b)) for a,b in sn)
        for tid in target_surface.element_ids:
            target=[p[n] for n in oriented_ids(model,tid,definition)]
            tn=cross(vsub(target[1],target[0]),vsub(target[2],target[0]))
            mutual=dot(sn,tn)[0]
            numerators=[dot(vsub(source[0],y),sn)[0] for y in target]
            positive=min(numerators)>0 and chart_lower>0 and mutual>0 and norm_upper>0
            distance=min(numerators)/norm_upper if norm_upper>0 else None
            pairs.append(dict(source_face=sid,target_face=tid,positive_separation=positive,
                target_corner_source_normal_numerator_lower_fractions=[str(v) for v in numerators],
                source_reference_axis_normal_lower_fraction=str(chart_lower),
                source_target_normal_dot_lower_fraction=str(mutual),source_normal_norm_upper_fraction=str(norm_upper),
                distance_lower_fraction=str(distance),distance_lower_m=float(distance) if distance is not None else None))
    return dict(gate_pass=all(v['positive_separation'] for v in pairs),pairs=pairs,
        minimum_distance_lower_m=min(v['distance_lower_m'] for v in pairs if v['distance_lower_m'] is not None),
        director_absolute_uncertainty='1e-70',all_pairs=len(source_surface.element_ids)*len(target_surface.element_ids),
        scope='exact rational interval source-plane gap positive over every whole target P1 triangle; includes all represented overlap',
        inequality='min_target_corners n_source.(source_anchor-target_corner) / source_normal_L1_upper > 0')


def clip(subject,target):
    polygon=[(v[:2],('s',i)) for i,v in enumerate(subject)];ties=[]
    for edge in range(3):
        a,b=target[edge,:2],target[(edge+1)%3,:2];normal=np.array((-(b-a)[1],(b-a)[0]))
        if not polygon:break
        output=[]
        previous,ptag=polygon[-1];fp=float((previous-a)@normal)
        for point,tag in polygon:
            f=float((point-a)@normal)
            if f==0.:ties.append((edge,tag))
            if (f>=0.)!=(fp>=0.):
                output.append((previous+(point-previous)*(fp/(fp-f)),('e',edge,ptag,tag)))
            if f>=0.:output.append((point,tag))
            previous,ptag,fp=point,tag,f
        polygon=output
    return polygon,ties


def integral(model,physical,z,order,definition):
    source_surface,target_surface=roles(definition)
    pressure_ids=sorted({n for eid in source_surface.element_ids for n in model.mesh.elements[eid].node_ids})
    mode={n:i for i,n in enumerate(pressure_ids)}
    roots,weights=np.polynomial.legendre.leggauss(order);r=.5*(roots+1);w=.5*weights
    u,v=np.meshgrid(r,r,indexing='ij');measure=(w[:,None]*w[None,:]*(1-u)).ravel();u=u.ravel();v=v.ravel()
    support=np.zeros(len(pressure_ids));weighted=np.zeros(len(pressure_ids));signature=[];ties=[];charts=[]
    reference,_=vertices(model,np.zeros(model.mesh.dof_manager.total_dofs),definition)
    for sid in source_surface.element_ids:
        ids=oriented_ids(model,sid,definition);source=np.array([physical[n] for n in ids]);ref=np.array([reference[n] for n in ids])
        e1=source[1]-source[0];e2=source[2]-source[0];normal=np.cross(e1,e2)
        jac=np.linalg.norm(normal);normal=normal/jac;tangent=e1/np.linalg.norm(e1);binormal=np.cross(normal,tangent)
        axes=np.column_stack((tangent,binormal));src=(source-source[0])@axes
        ref_jac=np.linalg.norm(np.cross(ref[1]-ref[0],ref[2]-ref[0]))
        if np.cross(ref[1]-ref[0],ref[2]-ref[0])@normal<=0:raise ValueError('independent source polarity')
        for tid in target_surface.element_ids:
            target=np.array([physical[n] for n in oriented_ids(model,tid,definition)]);dst=(target-source[0])@axes
            threshold=1e-10*max(1.,float(np.max(np.abs(np.r_[src.ravel(),dst.ravel()]))))**2
            source_jac=float(np.linalg.det(np.stack((src[1]-src[0],src[2]-src[0]))))
            target_jac=float(np.linalg.det(np.stack((dst[1]-dst[0],dst[2]-dst[0]))))
            if min(source_jac,target_jac)<=threshold:raise ValueError('independent P1/P1 chart orientation')
            polygon,pair_ties=clip(src,dst);ties+=pair_ties;signature.append((sid,tid,tuple(tag for _,tag in polygon)))
            charts.append(dict(source_face=sid,target_face=tid,source_jac=source_jac,target_jac=target_jac))
            for i in range(1,len(polygon)-1):
                a,b,c=(polygon[j][0] for j in (0,i,i+1));det=float(np.linalg.det(np.stack((b-a,c-a))))
                if det<=0:raise ValueError('independent integration triangle')
                points=a+u[:,None]*(b-a)+(1-u)[:,None]*v[:,None]*(c-a)
                rhs=np.vstack((points.T,np.ones(len(points))))
                ss=np.linalg.solve(np.vstack((src.T,np.ones(3))),rhs).T
                ts=np.linalg.solve(np.vstack((dst.T,np.ones(3))),rhs).T
                gap=(ss@source-ts@target)@normal;weights=det*measure*ref_jac/jac
                for j,nid in enumerate(ids):
                    contribution=weights*ss[:,j];support[mode[nid]]+=np.sum(contribution);weighted[mode[nid]]+=np.sum(contribution*gap)
    if np.any(support<=0) or not np.isfinite(np.r_[support,weighted]).all():raise ValueError('independent positive P1 support')
    return dict(support=support,gap=weighted/support,work=float(-z@(weighted/support)),signature=signature,ties=ties,chart_certificate=charts)
