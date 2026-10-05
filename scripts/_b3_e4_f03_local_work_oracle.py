"""Exact manufactured work identities for a conforming 2x2 rectangular Qp patch.

This is a small classical membrane oracle, not an element/stiffness assembly.
The physical finite pads use the represented binary64 constants lifted to
Fractions. Two independent polynomial integration orders compute interface
work: spatial clipped area forces and moving station/pad moments.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F

from scripts import _b3_e4_f03_spatial_contract as c


Z=F(0);O=F(1)
XC=(F(-1,2),F(1,2),F(3,2))
YC=(F(-1,2),Z,F(1,2))
P=dict[tuple[int,int],F]
Q=tuple[F,...]


def _add(a:P,b:P) -> P:
    r=a.copy()
    for k,v in b.items():r[k]=r.get(k,Z)+v
    return {k:v for k,v in r.items() if v}


def _scale(a:P,v:F) -> P:
    return {k:x*v for k,x in a.items() if x*v}


def _mul(a:P,b:P) -> P:
    r={}
    for (i,j),x in a.items():
        for (k,l),y in b.items():r[(i+k,j+l)]=r.get((i+k,j+l),Z)+x*y
    return {k:v for k,v in r.items() if v}


def _deriv(a:P,axis:int) -> P:
    r={}
    for (i,j),v in a.items():
        n=(i,j)[axis]
        if n:
            key=(i-1,j) if axis==0 else (i,j-1)
            r[key]=n*v
    return r


def _integrate(a:P,x0:F,x1:F,y0:F,y1:F) -> F:
    return sum((v*(x1**(i+1)-x0**(i+1))/(i+1)*
                (y1**(j+1)-y0**(j+1))/(j+1)
                for (i,j),v in a.items()),Z)


def _edge(a:P,axis:int,at:F,lo:F,hi:F) -> F:
    if axis==0:
        return sum((v*at**i*(hi**(j+1)-lo**(j+1))/(j+1)
                    for (i,j),v in a.items()),Z)
    return sum((v*at**j*(hi**(i+1)-lo**(i+1))/(i+1)
                for (i,j),v in a.items()),Z)


def _lagrange(lo:F,hi:F,p:int) -> tuple[Q,...]:
    nodes=tuple(lo+(hi-lo)*F(i,p) for i in range(p+1))
    result=[]
    for i,x in enumerate(nodes):
        q=(O,)
        for j,y in enumerate(nodes):
            if i!=j:q=_qm(q,(-y/(x-y),O/(x-y)))
        result.append(q)
    return tuple(result)


def _qm(a:Q,b:Q) -> Q:
    r=[Z]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):r[i+j]+=x*y
    return tuple(r)


def _qa(a:Q,b:Q) -> Q:
    return tuple((a[i] if i<len(a) else Z)+(b[i] if i<len(b) else Z)
                 for i in range(max(len(a),len(b))))


def _qs(a:Q,v:F) -> Q:return tuple(v*x for x in a)
def _qat(a:Q,x:F) -> F:
    r=Z
    for v in reversed(a):r=r*x+v
    return r


def _qi(a:Q,lo:F,hi:F) -> F:
    return sum((v*(hi**(i+1)-lo**(i+1))/(i+1) for i,v in enumerate(a)),Z)


def _affine(value:F,slope:F=Z) -> Q:return (value,slope)


def _power(a:Q,n:int) -> Q:
    r=(O,)
    for _ in range(n):r=_qm(r,a)
    return r


@dataclass(frozen=True,slots=True)
class Patch:
    """Shared nodal values in component, global-y, global-x order."""
    p:int
    values:tuple

    def __post_init__(self):
        if type(self.p) is not int or self.p not in (1,2,3):
            raise ValueError('bounded Qp order must be 1..3')
        n=self.p*2+1
        if type(self.values) not in (tuple,list) or len(self.values)!=2:
            raise ValueError('two-component shared nodal values required')
        result=[]
        for component in self.values:
            if type(component) not in (tuple,list) or len(component)!=n:
                raise ValueError('invalid shared nodal y layout')
            rows=[]
            for row in component:
                if type(row) not in (tuple,list) or len(row)!=n:
                    raise ValueError('invalid shared nodal x layout')
                if any(type(v) is not F or
                       max(v.numerator.bit_length(),v.denominator.bit_length())>1024
                       for v in row):
                    raise ValueError('bounded exact Fraction nodal values required')
                rows.append(tuple(row))
            result.append(tuple(rows))
        object.__setattr__(self,'values',tuple(result))

    @classmethod
    def sample(cls,p:int,field):
        if type(p) is not int or p not in (1,2,3):
            raise ValueError('bounded Qp order must be 1..3')
        xs=tuple(XC[i]+(XC[i+1]-XC[i])*F(j,p)
                 for i in range(2) for j in range(p))+(XC[-1],)
        ys=tuple(YC[i]+(YC[i+1]-YC[i])*F(j,p)
                 for i in range(2) for j in range(p))+(YC[-1],)
        pairs=tuple(tuple(field(x,y) for x in xs) for y in ys)
        return cls(p,tuple(tuple(tuple(pair[k] for pair in row)
                                   for row in pairs) for k in range(2)))

    def cells(self):
        for j in range(2):
            ly=_lagrange(YC[j],YC[j+1],self.p)
            for i in range(2):
                lx=_lagrange(XC[i],XC[i+1],self.p)
                components=[]
                for component in self.values:
                    poly={}
                    for b in range(self.p+1):
                        for a in range(self.p+1):
                            v=component[j*self.p+b][i*self.p+a]
                            if v:
                                for ix,cx in enumerate(lx[a]):
                                    for iy,cy in enumerate(ly[b]):
                                        key=(ix,iy)
                                        poly[key]=poly.get(key,Z)+v*cx*cy
                    components.append({k:v for k,v in poly.items() if v})
                yield (XC[i],XC[i+1],YC[j],YC[j+1]),tuple(components)


@dataclass(frozen=True,slots=True)
class Load:
    density:tuple[F,F,F]
    atoms:tuple[tuple[F,F,F],tuple[F,F,F]]

    def __post_init__(self):
        if (type(self.density) not in (tuple,list) or len(self.density)!=3 or
            type(self.atoms) not in (tuple,list) or len(self.atoms)!=2 or
            any(type(a) not in (tuple,list) or len(a)!=3 for a in self.atoms)):
            raise ValueError('physical line density and two endpoint atoms required')
        if any(type(v) is not F or
               max(v.numerator.bit_length(),v.denominator.bit_length())>1024
               for v in (*self.density,*(x for a in self.atoms for x in a))):
            raise ValueError('bounded exact physical load required')
        object.__setattr__(self,'density',tuple(self.density))
        object.__setattr__(self,'atoms',tuple(tuple(a) for a in self.atoms))


def sum_poly_terms(weights,terms) -> P:
    r={}
    for weight,term in zip(weights,terms):r=_add(r,_scale(term,weight))
    return r


def stress(displacement:tuple[P,P]) -> tuple[P,P,P]:
    ux,uy=displacement
    e=(_deriv(ux,0),_deriv(uy,1),_add(_deriv(ux,1),_deriv(uy,0)))
    return tuple(_scale(sum_poly_terms(c.Q_PLANE[k],e),c.Q_THICKNESS)
                 for k in range(3))


def divergence(T:tuple[P,P,P]) -> tuple[P,P]:
    return (_add(_deriv(T[0],0),_deriv(T[2],1)),
            _add(_deriv(T[2],0),_deriv(T[1],1)))


def _traction_work(T,z,axis:int,normal:F,at:F,lo:F,hi:F) -> F:
    first,second=((T[0],T[2]) if axis==0 else (T[2],T[1]))
    return normal*(_edge(_mul(first,z[0]),axis,at,lo,hi)+
                   _edge(_mul(second,z[1]),axis,at,lo,hi))


def _stress_work(T,z,rect) -> F:
    x0,x1,y0,y1=rect
    zstrain=(_deriv(z[0],0),_deriv(z[1],1),
             _add(_deriv(z[0],1),_deriv(z[1],0)))
    return sum((_integrate(_mul(t,e),x0,x1,y0,y1)
                for t,e in zip(T,zstrain)),Z)


def _area_load_work(z_cells,load:Load) -> F:
    """Integrate physical clipped spatial load over x/y subregions."""
    total=Z
    for rect,z in z_cells:
        x0,x1,y0,y1=rect
        for l,r,b,t in c.PADS:
            lowy,highy=max(y0,b),min(y1,t)
            if lowy>=highy:continue
            cuts=sorted({x0,x1,*(v for v in (l,r,l+1,r+1) if x0<v<x1)})
            for xa,xb in zip(cuts,cuts[1:]):
                mid=(xa+xb)/2
                low=_affine(Z) if mid-r<0 else _affine(-r,O)
                high=_affine(O) if mid-l>1 else _affine(-l,O)
                if _qat(low,mid)>=_qat(high,mid):continue
                length=_qa(high,_qs(low,-O))
                firstmoment=_qs(_qa(_power(high,2),_qs(_power(low,2),-O)),F(1,2))
                # Turn univariate x polynomials into bivariate x/y polynomials.
                width={(i,0):v for i,v in enumerate(length) if v}
                xmoment={(i,0):v for i,v in enumerate(_qa(_qm((Z,O),length),
                                                          _qs(firstmoment,-O))) if v}
                fx=_scale(_add(_scale(width,load.density[0]),
                                _scale(_mul(width,{(0,1):O}),
                                       -load.density[2]/c.Q_J)),O/c.Q_AREA)
                fy=_scale(_add(_scale(width,load.density[1]),
                                _scale(xmoment,load.density[2]/c.Q_J)),O/c.Q_AREA)
                total+=_integrate(_add(_mul(fx,z[0]),_mul(fy,z[1])),
                                  xa,xb,lowy,highy)
            for endpoint,atom in enumerate(load.atoms):
                xa,xb=max(x0,l+endpoint),min(x1,r+endpoint)
                if xa>=xb:continue
                fx=_scale(_add({(0,0):atom[0]},
                               {(0,1):-atom[2]/c.Q_J}),O/c.Q_AREA)
                fy=_scale(_add({(0,0):atom[1]},
                               {(1,0):atom[2]/c.Q_J,
                                (0,0):-endpoint*atom[2]/c.Q_J}),O/c.Q_AREA)
                total+=_integrate(_add(_mul(fx,z[0]),_mul(fy,z[1])),
                                  xa,xb,lowy,highy)
    return total


def _moment_on_moving_rectangle(poly:P,low:Q,high:Q,y0:F,y1:F) -> Q:
    result=(Z,)
    for (i,j),v in poly.items():
        xpart=_qs(_qa(_power(high,i+1),_qs(_power(low,i+1),-O)),F(1,i+1))
        ypart=(y1**(j+1)-y0**(j+1))/(j+1)
        result=_qa(result,_qs(xpart,v*ypart))
    return result


def _direct_pad_work(z_cells,load:Load) -> F:
    """Independent moving-station square-pad moment integration."""
    total=Z
    for rect,z in z_cells:
        x0,x1,y0,y1=rect
        for l,r,b,t in c.PADS:
            lowy,highy=max(y0,b),min(y1,t)
            if lowy>=highy:continue
            events=sorted({Z,O,*(v for edge in (x0,x1) for padedge in (l,r)
                                   if Z<(v:=edge-padedge)<O)})
            for sa,sb in zip(events,events[1:]):
                mid=(sa+sb)/2
                low=_affine(x0) if x0>mid+l else _affine(l,O)
                high=_affine(x1) if x1<mid+r else _affine(r,O)
                if _qat(low,mid)>=_qat(high,mid):continue
                zx=_moment_on_moving_rectangle(z[0],low,high,lowy,highy)
                zy=_moment_on_moving_rectangle(z[1],low,high,lowy,highy)
                xzy=_moment_on_moving_rectangle(_mul(z[1],{(1,0):O}),
                                                 low,high,lowy,highy)
                yzx=_moment_on_moving_rectangle(_mul(z[0],{(0,1):O}),
                                                 low,high,lowy,highy)
                yaw=_qs(_qa(_qa(xzy,_qs(_qm((Z,O),zy),-O)),
                            _qs(yzx,-O)),O/c.Q_J)
                action=_qa(_qa(_qs(zx,load.density[0]),
                               _qs(zy,load.density[1])),
                           _qs(yaw,load.density[2]))
                total+=_qi(action,sa,sb)/c.Q_AREA
            for station,atom in enumerate(load.atoms):
                low,high=max(x0,l+station),min(x1,r+station)
                if low>=high:continue
                lowq,highq=(low,),(high,)
                zx=_qat(_moment_on_moving_rectangle(z[0],lowq,highq,lowy,highy),Z)
                zy=_qat(_moment_on_moving_rectangle(z[1],lowq,highq,lowy,highy),Z)
                xzy=_qat(_moment_on_moving_rectangle(_mul(z[1],{(1,0):O}),
                                                          lowq,highq,lowy,highy),Z)
                yzx=_qat(_moment_on_moving_rectangle(_mul(z[0],{(0,1):O}),
                                                          lowq,highq,lowy,highy),Z)
                total+=(atom[0]*zx+atom[1]*zy+
                        atom[2]*(xzy-station*zy-yzx)/c.Q_J)/c.Q_AREA
    return total


def work_identity(u:Patch,z:Patch,load:Load) -> dict[str,F]:
    """Exact a, pad work, residual, jumps and boundary work.

    j=(T_plus-T_minus)n, n from minus to plus. The supported test identity
    is load-a=volume_residual+jump-free; general virtual reaction is
    support+free-volume_residual-jump=a-load.
    """
    if not isinstance(u,Patch) or not isinstance(z,Patch) or not isinstance(load,Load):
        raise ValueError('bounded patch and physical load required')
    if u.p!=z.p:raise ValueError('patch polynomial orders must agree')
    uc=list(u.cells());zc=list(z.cells())
    T=[stress(v) for _,v in uc]
    energy=volume=Z
    for ((rect,_),(_,test),sigma) in zip(uc,zc,T):
        x0,x1,y0,y1=rect
        energy+=_stress_work(sigma,test,rect)
        div=divergence(sigma)
        volume+=_integrate(_add(_mul(div[0],test[0]),
                                _mul(div[1],test[1])),x0,x1,y0,y1)
    jump=Z;support=Z;free=Z
    for j in range(2):
        minus=2*j;plus=minus+1
        delta=tuple(_add(T[plus][k],_scale(T[minus][k],-O)) for k in range(3))
        jump+=_traction_work(delta,zc[minus][1],0,O,XC[1],YC[j],YC[j+1])
    for i in range(2):
        minus=i;plus=2+i
        delta=tuple(_add(T[plus][k],_scale(T[minus][k],-O)) for k in range(3))
        jump+=_traction_work(delta,zc[minus][1],1,O,YC[1],XC[i],XC[i+1])
    for j in range(2):
        support+=_traction_work(T[2*j],zc[2*j][1],0,-O,XC[0],YC[j],YC[j+1])
        support+=_traction_work(T[2*j+1],zc[2*j+1][1],0,O,XC[2],YC[j],YC[j+1])
    for i in range(2):
        free+=_traction_work(T[i],zc[i][1],1,-O,YC[0],XC[i],XC[i+1])
        free+=_traction_work(T[2+i],zc[2+i][1],1,O,YC[2],XC[i],XC[i+1])
    area=_area_load_work(zc,load)
    direct=_direct_pad_work(zc,load)
    residual=volume+area
    reaction=support+free-residual-jump
    return {'strain_work':energy,'area_load_work':area,
            'direct_pad_work':direct,'volume_divergence_work':volume,
            'volume_residual_work':residual,'jump_work':jump,
            'supported_boundary_work':support,'free_boundary_work':free,
            'reaction_work':reaction,
            'integration_by_parts_defect':energy+volume+jump-support-free,
            'pad_adjoint_defect':area-direct,
            'reaction_defect':reaction-(energy-direct)}
