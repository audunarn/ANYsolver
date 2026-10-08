"""Independent interval certificate for represented B3/affine-S3 Hermite paths.

No production geometry/work/path imports. Rational controls represent binary
endpoint data exactly. Directed interval arithmetic encloses conversion,
normalization, norms and complete Bezier hulls; time subdivision is finite.
This verifies the declared Hermite segment, not a nonlinear DAE lift.
"""
from fractions import Fraction as F
import math
import numpy as np

RADIUS=F(1,128)
HEIGHT=F(1,128)
GAP_GATE=1.e-5
RIM=.02
MAX_VISITED=4096
MAX_DEPTH=8

def lo(x):return math.nextafter(float(x),-math.inf)
def hi(x):return math.nextafter(float(x),math.inf)
def point(x):return (lo(x),hi(x))
def subtract_lower(value,*positive_bounds):
    """Directed at EVERY subtraction, including severe cancellation."""
    for bound in positive_bounds:value=lo(value-bound)
    return value
def add(a,b):return (lo(a[0]+b[0]),hi(a[1]+b[1]))
def neg(a):return (-a[1],-a[0])
def sub(a,b):return add(a,neg(b))
def mul(a,b):
    q=[x*y for x in a for y in b];return (lo(min(q)),hi(max(q)))
def div(a,b):
    if b[0]<=0:raise ValueError('unresolved positive denominator')
    return mul(a,(lo(1/b[1]),hi(1/b[0])))
def dot(a,b):
    r=(0.,0.)
    for x,y in zip(a,b):r=add(r,mul(x,y))
    return r
def cross(a,b):return [sub(mul(a[1],b[2]),mul(a[2],b[1])),sub(mul(a[2],b[0]),mul(a[0],b[2])),sub(mul(a[0],b[1]),mul(a[1],b[0]))]
def subtract(a,b):return [sub(x,y) for x,y in zip(a,b)]
def norm(a):
    low=high=0.
    for x,y in a:
        nearest=0. if x<=0<=y else min(abs(x),abs(y));far=max(abs(x),abs(y))
        low=lo(low+lo(nearest*nearest));high=hi(high+hi(far*far))
    return (lo(math.sqrt(max(0.,low))),hi(math.sqrt(max(0.,high))))
def box(p):return [point(x) for x in p]
def split(controls):
    levels=[controls]
    while len(levels[-1])>1:levels.append([(a+b)/2 for a,b in zip(levels[-1],levels[-1][1:])])
    return np.array([x[0] for x in levels],object),np.array([x[-1] for x in levels[::-1]],object)

def geometry_controls(model,u0,u1,v0,v1,duration):
    h=F(float(duration));q=[[F(float(x)) for x in row] for row in (u0,u1,v0,v1)]
    controls=[q[0],[x+h*y/3 for x,y in zip(q[0],q[2])],[x-h*y/3 for x,y in zip(q[1],q[3])],q[1]]
    geometry=[]
    for control in controls:
        points=[]
        for node in (1,6,2,3,4,5):
            ids=model.mesh.dof_manager.get_node_dofs(node);reference=[F(float(x)) for x in model.mesh.nodes[node].coords()]
            p=[reference[i]+control[ids[i]] for i in range(3)]
            if node in (3,4,5):
                p[0]+=HEIGHT*control[ids[4]];p[1]-=HEIGHT*control[ids[3]];p[2]+=HEIGHT
            points.append(p)
        # Exact Q2 Lagrange -> quadratic Bezier spatial controls.
        points[1]=[2*x-(a+b)/2 for a,x,b in zip(points[0],points[1],points[2])]
        geometry.append(points)
    return np.array(geometry,object)

def enclosure(controls):
    anchor=[box(p) for p in controls[0]];skin=anchor[3:]
    e1=subtract(skin[1],skin[0]);e2=subtract(skin[2],skin[0]);C=cross(e1,e2);cn=norm(C)
    if cn[0]<=0:return dict(resolved=False,reason='anchor degeneracy')
    n=[div(x,cn) for x in C]
    displacement=[]
    for node in range(6):
        displacement.append(max(norm(subtract(box(row[node]),anchor[node]))[1] for row in controls))
    d1=hi(displacement[4]+displacement[3]);d2=hi(displacement[5]+displacement[3])
    term1=hi(norm(e1)[1]*d2);term2=hi(norm(e2)[1]*d1);term3=hi(d1*d2)
    change=hi(hi(term1+term2)+term3)
    floor=lo(cn[0]-change);orientation=lo(C[2][0]-change)
    if floor<=0 or orientation<=0:return dict(resolved=False,reason='normal/orientation unresolved')
    # For true unit vectors: ||n(t)-n0|| <=2||C(t)-C0||/||C0||.
    normal_change=hi(hi(2*change)/cn[0])
    relative=[subtract(p,skin[0]) for p in anchor[:3]]
    U=hi(max(displacement[:3])+displacement[3]);reach=max(norm(x)[1] for x in relative)
    gap=subtract_lower(min(dot(n,x)[0] for x in relative),hi(float(RADIUS)),U,hi(normal_change*reach))
    rims=[]
    for i,j in ((0,1),(1,2),(2,0)):
        edge=subtract(skin[j],skin[i]);length=norm(edge)
        de=hi(displacement[3+i]+displacement[3+j])
        if lo(length[0]-de)<=0:return dict(resolved=False,reason='edge degeneracy unresolved')
        tangent=[div(x,length) for x in edge];inward=cross(n,tangent)
        tangent_change=hi(hi(2*de)/length[0]);axis_change=hi(normal_change+tangent_change)
        rel=[subtract(p,skin[i]) for p in anchor[:3]]
        movement=hi(max(displacement[:3])+displacement[3+i]);reach=max(norm(x)[1] for x in rel)
        rims.append(subtract_lower(min(dot(inward,x)[0] for x in rel),movement,hi(axis_change*reach)))
    return dict(resolved=gap>=-GAP_GATE and min(rims)>=RIM,gap_lower=gap,rim_lower=min(rims),normal_floor=floor,orientation_floor=orientation,reason='complete_hull_bounds')

def certify(controls,*,budget=MAX_VISITED):
    queue=[(controls,0)];visited=0;leaves=[]
    while queue:
        c,depth=queue.pop();visited+=1
        if visited>budget:return dict(certified=False,visited=visited,reason='finite interval budget',leaves=len(leaves))
        result=enclosure(c)
        if result['resolved']:leaves.append(result);continue
        if depth>=MAX_DEPTH:return dict(certified=False,visited=visited,reason=result['reason']+'; depth exhausted',failed=result,leaves=len(leaves))
        left,right=split(c);queue.extend(((right,depth+1),(left,depth+1)))
    return dict(certified=True,visited=visited,leaves=len(leaves),gap_lower=min(x['gap_lower'] for x in leaves),rim_lower=min(x['rim_lower'] for x in leaves),normal_floor=min(x['normal_floor'] for x in leaves),orientation_floor=min(x['orientation_floor'] for x in leaves))
