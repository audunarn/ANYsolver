"""Independent original-bilinear overlap reference; no solver/contact imports.

Integration triangles subdivide the 2D domain only. Neither physical surface is
replaced by triangles. All positions, normals, inverse maps and Jref remain Q1.
"""
from functools import lru_cache
from fractions import Fraction as F
import numpy as np


def shape(uv):
    u,v=np.asarray(uv).T
    n=np.column_stack(((1-u)*(1-v),u*(1-v),u*v,(1-u)*v))
    du=np.column_stack((v-1,1-v,v,-v))
    dv=np.column_stack((u-1,-u,u,1-u))
    return n,du,dv


def inverse(points,corners):
    # Independent vector Newton inverse of the original bilinear XY map.
    uv=np.full((len(points),2),.5)
    for _ in range(12):
        n,du,dv=shape(uv);r=n@corners-points;a=du@corners;b=dv@corners
        det=a[:,0]*b[:,1]-a[:,1]*b[:,0]
        if np.min(det)<=1e-12:raise ValueError('reference inverse nonpositive/ill-conditioned')
        step=np.column_stack(((r[:,0]*b[:,1]-r[:,1]*b[:,0])/det,(a[:,0]*r[:,1]-a[:,1]*r[:,0])/det))
        uv-=step
        if np.max(abs(step))<2e-14:break
    if np.max(abs(shape(uv)[0]@corners-points))>2e-12:raise ValueError('reference inverse unresolved')
    return uv


def clip(subject,boundary):
    polygon=[np.asarray(p,float) for p in subject]
    for a,b in zip(boundary,np.roll(boundary,-1,axis=0)):
        old=polygon;polygon=[]
        if not old:break
        cross=lambda p:(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        p=old[-1];dp=cross(p)
        for q in old:
            dq=cross(q)
            if (dp>=0)!=(dq>=0):polygon.append(p+(q-p)*(dp/(dp-dq)))
            if dq>=0:polygon.append(q)
            p,dp=q,dq
    return np.asarray(polygon)


def convex_ccw(polygon):
    edges=np.roll(polygon,-1,axis=0)-polygon;following=np.roll(edges,-1,axis=0)
    turns=edges[:,0]*following[:,1]-edges[:,1]*following[:,0]
    if not np.isfinite(turns).all() or np.min(turns)<=0:
        raise ValueError('nonconvex or non-CCW projected chart')


@lru_cache(None)
def rule(order):
    t,w=np.polynomial.legendre.leggauss(order);t=(t+1)/2;w=w/2
    a,b=np.meshgrid(t,t,indexing='ij');wa,wb=np.meshgrid(w,w,indexing='ij')
    return a.ravel(),b.ravel(),(wa*wb*(1-a)).ravel()


def integrals(reference,points,source_faces,target_faces,count,order=8):
    """S,a and overlap-only bin a; shared node sums, original reference measure."""
    S=np.zeros(count);a=np.zeros(count);ab=np.zeros((2,count));areas=np.zeros(2);mass=np.zeros((count,count))
    aa,bb,ww=rule(order)
    for ids in source_faces:
        ix=np.asarray(ids)-1;src=points[ix];ref=reference[ix]
        normal=np.cross(src[1]-src[0],src[3]-src[0]);normal/=np.linalg.norm(normal)
        e=src[1]-src[0];e/=np.linalg.norm(e);basis=np.stack((e,np.cross(normal,e)),axis=1)
        origin=src[0];xy=(src-origin)@basis
        convex_ccw(xy)
        x0,x1=ref[0,0],ref[1,0]
        for binid,(left,right) in enumerate(((.1,.6),(.6,1.1))):
            lo=max(left,x0);hi=min(right,x1)
            if hi<=lo:continue
            ul,ur=(lo-x0)/(x1-x0),(hi-x0)/(x1-x0)
            boundary=shape(np.array(((ul,0.),(ur,0.),(ur,1.),(ul,1.))))[0]@xy
            convex_ccw(boundary)
            for tids in target_faces:
                tgt=points[np.asarray(tids)-1];txy=(tgt-origin)@basis
                convex_ccw(txy)
                polygon=clip(boundary,txy)
                if len(polygon)<3:continue
                for i in range(1,len(polygon)-1):
                    p0,p1,p2=polygon[[0,i,i+1]]
                    e1,e2=p1-p0,p2-p0;det=float(e1[0]*e2[1]-e1[1]*e2[0])
                    if det<=1e-24:continue
                    at=p0+aa[:,None]*(p1-p0)+((1-aa)*bb)[:,None]*(p2-p0)
                    uv=inverse(at,xy);n,du,dv=shape(uv);nt=shape(inverse(at,txy))[0]
                    current_normal=np.cross(du@src,dv@src)
                    projected_j=current_normal@normal
                    if np.min(projected_j)<=0:raise ValueError('inverted reference projection')
                    jref=np.linalg.norm(np.cross(du@ref,dv@ref),axis=1)
                    physical_normal=current_normal/np.linalg.norm(current_normal,axis=1)[:,None]
                    gap=np.sum(physical_normal*(n@src-nt@tgt),axis=1)
                    weights=ww*det*jref/projected_j
                    si=weights@n;ai=(weights*gap)@n
                    S[ix]+=si;a[ix]+=ai;ab[binid,ix]+=ai;areas[binid]+=weights.sum()
                    mass[np.ix_(ix,ix)]+=n.T@(weights[:,None]*n)
    if np.min(S)<=0:raise ValueError('all positive supports required')
    return S,a,ab,areas,mass


def derivatives(reference,points,sf,tf,count,h=1e-6,order=8,transfer=None):
    """Independent FD of scalar integrals, with frozen pressure trace transfer."""
    p=np.asarray(points);base=integrals(reference,p,sf,tf,count,order)
    E=np.eye(count) if transfer is None else np.asarray(transfer)
    S,a,ab,areas=base[:4];S=E.T@S;a=E.T@a;ab=ab@E
    ds=np.empty((len(S),p.size));da=ds.copy();dab=np.empty((2,len(S),p.size))
    for k in range(p.size):
        delta=np.zeros(p.size);delta[k]=h;delta=delta.reshape(p.shape)
        plus=integrals(reference,p+delta,sf,tf,count,order);minus=integrals(reference,p-delta,sf,tf,count,order)
        ds[:,k]=E.T@(plus[0]-minus[0])/(2*h)
        da[:,k]=E.T@(plus[1]-minus[1])/(2*h)
        dab[:,:,k]=((plus[2]-minus[2])@E)/(2*h)
    g=da/S[:,None]-a[:,None]*ds/S[:,None]**2
    gb=dab/S[None,:,None]-ab[:,:,None]*ds[None,:,:]/S[None,:,None]**2
    return dict(support=S,weighted=a,bin_weighted=ab,bin_area=areas,gap=a/S,gap_gradient=g,bin_gap_gradient=gb)


def exact_rectangles(source_x,target_x=(0.,.5,1.),slide=.02,clearance=2e-7):
    """Fraction supports and cross-body frozen-normal work, in material XY."""
    xs=tuple(F(float(x)) for x in source_x);tx=tuple(F(float(x)) for x in target_x)
    sy=(F(.1),F(1.1));ty=tx;offset=F(float(slide));count=len(xs)*2
    S=[F(0)]*count;M=[[F(0)]*(count+9) for _ in range(count)];bins=[[F(0)]*count for _ in range(2)]
    def product_integral(p,q,lo,hi):
        return p[0]*q[0]*(hi-lo)+(p[0]*q[1]+p[1]*q[0])*(hi**2-lo**2)/2+p[1]*q[1]*(hi**3-lo**3)/3
    def linear(lo,hi):return ((hi/(hi-lo),-1/(hi-lo)),(-lo/(hi-lo),1/(hi-lo)))
    for i,(x0,x1) in enumerate(zip(xs,xs[1:])):
        lx=linear(x0,x1);ly=linear(*sy);ids=(i,i+1,len(xs)+i+1,len(xs)+i)
        for j,(a,b) in enumerate(zip(tx,tx[1:])):
            lo,hi=max(x0,a),min(x1,b)
            if hi<=lo:continue
            for k,(c,d) in enumerate(zip(ty,ty[1:])):
                yl,yh=max(sy[0],c-offset),min(sy[1],d-offset)
                if yh<=yl:continue
                ns=((lx[0],ly[0]),(lx[1],ly[0]),(lx[1],ly[1]),(lx[0],ly[1]))
                tly=linear(c-offset,d-offset);tlx=linear(a,b)
                nt=((tlx[0],tly[0]),(tlx[1],tly[0]),(tlx[1],tly[1]),(tlx[0],tly[1]))
                tids=(3*k+j,3*k+j+1,3*(k+1)+j+1,3*(k+1)+j)
                for l,node in enumerate(ids):
                    one=(F(1),F(0));S[node]+=product_integral(ns[l][0],one,lo,hi)*product_integral(ns[l][1],one,yl,yh)
                    for binid,(bl,br) in enumerate(((F(.1),F(.6)),(F(.6),F(1.1)))):
                        qa,qb=max(lo,bl),min(hi,br)
                        if qb>qa:bins[binid][node]+=product_integral(ns[l][0],one,qa,qb)*product_integral(ns[l][1],one,yl,yh)
                    for q,other in enumerate(ids):M[node][other]+=product_integral(ns[l][0],ns[q][0],lo,hi)*product_integral(ns[l][1],ns[q][1],yl,yh)
                    for q,other in enumerate(tids):M[node][count+other]-=product_integral(ns[l][0],nt[q][0],lo,hi)*product_integral(ns[l][1],nt[q][1],yl,yh)
    return dict(support=np.array(list(map(float,S))),normal_work=np.array([[float(v) for v in row] for row in M]),bins=np.array([[float(v) for v in row] for row in bins]),exact_support=[str(v) for v in S])
