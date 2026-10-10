"""Independent P1/P1 polygon penalty energy, first derivatives and Exp skins.

No production contact geometry, AD, work maps or gap kernel is imported.
The fixed target plane and source tangent/binormal projection match the declared
law. Exact polynomial triangle integration is used; derivatives are independent
first-order dual arithmetic, not the production Jet2 implementation.
"""
import numpy as np

class D:
    def __init__(self,v,g=None):
        self.v=float(v);self.g=np.zeros(12) if g is None else np.asarray(g,float)
    def __add__(a,b):
        b=dual(b);return D(a.v+b.v,a.g+b.g)
    __radd__=__add__
    def __neg__(a):return D(-a.v,-a.g)
    def __sub__(a,b):return a+-dual(b)
    def __rsub__(a,b):return dual(b)+-a
    def __mul__(a,b):
        b=dual(b);return D(a.v*b.v,a.g*b.v+b.g*a.v)
    __rmul__=__mul__
    def __truediv__(a,b):
        b=dual(b);return D(a.v/b.v,(a.g*b.v-b.g*a.v)/(b.v*b.v))
    def __rtruediv__(a,b):return dual(b)/a

def dual(v):return v if isinstance(v,D) else D(v)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def norm(a):
    v=dot(a,a);s=np.sqrt(v.v);return D(s,v.g/(2*s))
def unit(a):
    n=norm(a);return [v/n for v in a]
def cross2(a,b):return a[0]*b[1]-a[1]*b[0]
def shape(tri,p):
    e=sub(tri[1],tri[0]);f=sub(tri[2],tri[0]);x=sub(p,tri[0]);det=cross2(e,f)
    u=cross2(x,f)/det;v=cross2(e,x)/det;return [1-u-v,u,v]

def precise_corner_gaps(s,t):
    """Independent Decimal80 primal control of the same affine plane equation.

    Dual gradients remain independent first-order derivatives. Decimal primals
    avoid global-coordinate reconstruction/subtraction cancellation; no
    production helper is called. Old raw oracle versions remain evidence.
    """
    from decimal import Decimal as Z,localcontext
    with localcontext() as ctx:
        ctx.prec=80
        a=[[Z(v.v) for v in row] for row in s];b=[[Z(v.v) for v in row] for row in t]
        ns=cross(sub(a[1],a[0]),sub(a[2],a[0]));nt=cross(sub(b[1],b[0]),sub(b[2],b[0]))
        square=dot(ns,ns);den=dot(nt,ns)
        if square<=0 or den<=0:raise ValueError('independent plane chart refused')
        js=cross(sub(s[1],s[0]),sub(s[2],s[0]));jt=cross(sub(t[1],t[0]),sub(t[2],t[0]))
        ds=dot(js,js);ds=D(float(square),ds.g);length=norm_from_square(ds)
        dd=dot(jt,js);dd=D(float(den),dd.g)
        result=[]
        for point,exact in zip(s,a):
            numerator=dot(jt,sub(point,t[0]));numerator=D(float(dot(nt,sub(exact,b[0]))),numerator.g)
            result.append(numerator*length/dd)
        return result

def norm_from_square(v):
    root=np.sqrt(v.v);return D(root,v.g/(2*root))

def primitive(reference,source,target,stiffness,order=None):
    points=[[D(source[i,k],np.eye(12)[3*i+k]) for k in range(3)] for i in range(4)]
    S=[D(0) for _ in points];W=[D(0) for _ in points];signatures=[]
    for ids in ((0,1,3),(0,3,2)):
        s=[points[i] for i in ids];ns=unit(cross(sub(s[1],s[0]),sub(s[2],s[0])))
        tangent=unit(sub(s[1],s[0]));binormal=cross(ns,tangent)
        def project(p):
            x=sub(p,s[0]);return [dot(x,tangent),dot(x,binormal)]
        xy=[project(p) for p in s]
        ratio=np.linalg.norm(np.cross(reference[ids[1]]-reference[ids[0]],reference[ids[2]]-reference[ids[0]]))/norm(cross(sub(s[1],s[0]),sub(s[2],s[0])))
        for tid in ((0,1,3),(0,3,2)):
            t=[[D(v) for v in target[i]] for i in tid];nt=cross(sub(t[1],t[0]),sub(t[2],t[0]))
            if dot(ns,nt).v<=0:raise ValueError('oracle mutual chart refused')
            tx=[project(p) for p in t];polygon=xy;signature=[]
            scale=max(np.hypot(p[0].v,p[1].v) for p in xy+tx);tol=1e-10*scale*scale
            for i in range(3):
                if not polygon:break
                edge=sub(tx[(i+1)%3],tx[i]);out=[];old=polygon[-1];od=cross2(edge,sub(old,tx[i]))
                for current in polygon:
                    d=cross2(edge,sub(current,tx[i]))
                    if min(abs(od.v),abs(d.v))<=tol:raise ValueError('oracle clipping tie refused')
                    signature.append(int(d.v>0))
                    if (od.v>0)!=(d.v>0):
                        f=od/(od-d);out.append([x+f*(y-x) for x,y in zip(old,current)])
                    if d.v>0:out.append(current)
                    old,od=current,d
                polygon=out
            signatures.append((ids,tid,tuple(signature)))
            for i in range(1,len(polygon)-1):
                vertices=[polygon[0],polygon[i],polygon[i+1]]
                area=cross2(sub(vertices[1],vertices[0]),sub(vertices[2],vertices[0]))/2
                if area.v<=tol:raise ValueError('oracle integration triangle refused')
                shapes=[shape(xy,p) for p in vertices]
                corner_gaps=precise_corner_gaps(s,t)
                gaps=[sum(a*b for a,b in zip(phi,corner_gaps)) for phi in shapes]
                if order is None:
                    for local,node in enumerate(ids):
                        phi=[v[local] for v in shapes];total=sum(phi)
                        S[node]+=ratio*area*total/3
                        W[node]+=ratio*area*(total*sum(gaps)+sum(a*b for a,b in zip(phi,gaps)))/12
                else:
                    nodes,weights=np.polynomial.legendre.leggauss(order)
                    for u,wu in zip((nodes+1)/2,weights/2):
                        for v,wv in zip((nodes+1)/2,weights/2):
                            bary=(1-u-(1-u)*v,u,(1-u)*v)
                            measure=ratio*2*area*(1-u)*wu*wv
                            gap=sum(a*b for a,b in zip(bary,gaps))
                            for local,node in enumerate(ids):
                                phi=sum(bary[k]*shapes[k][local] for k in range(3))
                                S[node]+=measure*phi;W[node]+=measure*phi*gap
    if any(v.v<=0 for v in S):raise ValueError('oracle unsupported P1 row')
    energy=sum(stiffness*w*w/(2*s) for s,w in zip(S,W) if w.v<0)
    energy=dual(energy)
    return dict(energy=energy.v,physical_gradient=energy.g.reshape(4,3),support=np.array([s.v for s in S]),weighted_gap=np.array([w.v for w in W]),signature=signatures)

def skins(model,q):
    positions=[];directors=[];offsets=[];dofs=[];reference=[]
    for nid in (1,2,3,4):
        ids=model.mesh.dof_manager.get_node_dofs(nid)[:6];dofs.append(ids)
        node=model.mesh.nodes[nid];x=np.array((node.x,node.y,node.z));reference.append(x+np.array((0.,0.,-.035)))
        theta=np.asarray(q)[ids[3:]];angle=np.linalg.norm(theta);d=np.array((0.,0.,1.))
        if angle:
            axis=theta/angle;d=d*np.cos(angle)+np.cross(axis,d)*np.sin(angle)+axis*np.dot(axis,d)*(1-np.cos(angle))
        positions.append(x+np.asarray(q)[ids[:3]]-.035*d);directors.append(d);offsets.append(-.035)
    return np.array(reference),np.array(positions),np.array(directors),np.array(offsets),np.array(dofs)

def response(model,tool,q,stiffness,order=None):
    reference,p,d,h,ids=skins(model,q);raw=primitive(reference,p,np.asarray(tool.vertices),stiffness,order)
    nodal=np.zeros(model.mesh.dof_manager.total_dofs)
    for i,row in enumerate(ids):
        f=raw['physical_gradient'][i];nodal[row[:3]]=f;nodal[row[3:]]=h[i]*np.cross(d[i],f)
    raw['force']=nodal;return raw


def enclosed_skins(model,q):
    """80-digit independent Rodrigues; Taylor tail and Decimal operation margin.

    For |theta|<=1.2, 64 sin/cos terms give tail <1e-190. A
    conservative 1e-60 coordinate margin exceeds rounding in this fixed
    four-node fixture (coordinates <2m); conversion errors retained exactly.
    """
    from decimal import Decimal as Z,localcontext
    with localcontext() as ctx:
        ctx.prec=80
        result=[];errors=[]
        for nid in (1,2,3,4):
            ids=model.mesh.dof_manager.get_node_dofs(nid)[:6]
            node=model.mesh.nodes[nid];x=[Z(float(v)) for v in (node.x,node.y,node.z)]
            t=[Z(float(v)) for v in np.asarray(q)[ids[3:]]];a2=sum(v*v for v in t)
            if a2>Z('1.44'):raise ValueError('oracle angle envelope refused')
            # sinc and (1-cos)/theta^2 avoid division by a small angle.
            si=Z(1);co=Z('.5');ts=Z(1);tc=Z('.5')
            for k in range(1,64):
                ts*= -a2/Z((2*k)*(2*k+1));tc*= -a2/Z((2*k+1)*(2*k+2))
                si+=ts;co+=tc
            td=[t[1],-t[0],Z(0)];ttd=[t[0]*t[2],t[1]*t[2],-t[0]*t[0]-t[1]*t[1]]
            d=[Z(k==2)+si*td[k]+co*ttd[k] for k in range(3)]
            p=[x[k]+Z(float(q[ids[k]]))-Z(float(.035))*d[k] for k in range(3)]
            f=[float(v) for v in p];e=[float(abs(Z(v)-z)+Z('1e-60')) for v,z in zip(f,p)]
            result.append(f);errors.append(np.nextafter(e,np.inf))
        return np.asarray(result),np.asarray(errors)


def gap_enclosure(model,tool,q):
    """Independent rational corner bound of source-normal ray gap."""
    from fractions import Fraction as F
    from itertools import product
    p,e=enclosed_skins(model,q);target=np.asarray(tool.vertices)
    def iv(v,err=0):return (F(float(v))-F(float(err)),F(float(v))+F(float(err)))
    def plus(a,b):return (a[0]+b[0],a[1]+b[1])
    def minus(a,b):return (a[0]-b[1],a[1]-b[0])
    def times(a,b):
        v=[x*y for x,y in product(a,b)];return min(v),max(v)
    def ds(a,b):return [minus(x,y) for x,y in zip(a,b)]
    def dp(a,b):
        out=(F(0),F(0))
        for x,y in zip(a,b):out=plus(out,times(x,y))
        return out
    def cr(a,b):return [minus(times(a[1],b[2]),times(a[2],b[1])),minus(times(a[2],b[0]),times(a[0],b[2])),minus(times(a[0],b[1]),times(a[1],b[0]))]
    boxes=[[iv(x,y) for x,y in zip(row,err)] for row,err in zip(p,e)];bounds=[]
    for ids in ((0,1,3),(0,3,2)):
        source=[boxes[i] for i in ids];ns=cr(ds(source[1],source[0]),ds(source[2],source[0]))
        nl=max(min(abs(a),abs(b)) if a*b>0 else F(0) for a,b in ns)
        nu=sum(max(abs(a),abs(b)) for a,b in ns)
        for ti in ((0,1,3),(0,3,2)):
            t=[[iv(v) for v in target[i]] for i in ti];nt=cr(ds(t[1],t[0]),ds(t[2],t[0]));den=dp(nt,ns)
            if den[0]<=0 or nl<=0:raise ValueError('independent physical chart unresolved')
            h=min(dp(nt,ds(x,t[0]))[0] for x in source)
            bound=h*(nl/den[1] if h>=0 else nu/den[0]);value=float(bound)
            if F(value)>bound:value=np.nextafter(value,-np.inf)
            bounds.append(value)
    return dict(lower_m=min(bounds),pairs=bounds,enclosure='independent Decimal Rodrigues + rational interval plane/source-normal conversion')
