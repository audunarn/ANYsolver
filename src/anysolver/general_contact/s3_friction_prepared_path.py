"""Exact full-coverage S3 path moments with conservative eligibility proofs.

Optional internal acceleration. Uncertified paths keep the ordinary evaluator.
Rational Bernstein coefficients certify polynomial signs over the whole affine
segment; time samples are verification inputs, not the coverage certificate.
"""
from fractions import Fraction
from math import comb

import numpy as np


def _trim(p):
    while len(p)>1 and p[-1]==0:p.pop()
    return p


def _add(a,b):
    return _trim([(a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0)
                  for i in range(max(len(a),len(b)))])


def _mul(a,b):
    result=[Fraction(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):result[i+j]+=x*y
    return _trim(result)


def _negative(a):return [-x for x in a]
def _sub(a,b):return _add(a,_negative(b))
def _vsub(a,b):return tuple(_sub(x,y) for x,y in zip(a,b))
def _scale(v,p):return tuple(_mul(x,p) for x in v)


def _dot(a,b):
    result=[Fraction(0)]
    for x,y in zip(a,b):result=_add(result,_mul(x,y))
    return result


def _cross(a,b):
    return tuple(_sub(_mul(a[i],b[j]),_mul(a[j],b[i]))
                 for i,j in ((1,2),(2,0),(0,1)))


def _vector(a,b=None):
    return tuple([Fraction(float(x))] if b is None else
                 _trim([Fraction(float(x)),Fraction(float(y))-Fraction(float(x))])
                 for x,y in zip(a,a if b is None else b))


def _positive(p,*,strict=True):
    degree=len(p)-1
    coefficients=[sum((p[i]*Fraction(comb(k,i),comb(degree,i)) for i in range(k+1)),Fraction(0))
                  for k in range(degree+1)]
    return all(x>0 if strict else x>=0 for x in coefficients)


class PreparedS3PlanePressurePath:
    """One certified affine segment; batched exact P1 normal-pressure values."""
    def __init__(self,owner,first,last,cross,height,*,full_coverage=True):
        self.full_coverage=full_coverage
        self.owner=owner
        self.cross=np.zeros((3,max(map(len,cross))))
        for i,p in enumerate(cross):self.cross[i,:len(p)]=list(map(float,p))
        self.height=np.zeros((3,max(map(len,height))))
        for i,p in enumerate(height):self.height[i,:len(p)]=list(map(float,p))
        self.normal=np.asarray(first["normal"]).copy()
        self.stiffness=owner.normal.law.stiffness
        self.indices=tuple(owner.normal.law.source_node_ids.index(node)
                           for node in owner.template.source_adapters[0].node_ids)
        self.maximum_samples=owner.friction_settings.maximum_path_samples
        self.first,self.last=first,last
        if not full_coverage:
            # Authoritative affine work maps are evaluated only at preparation.
            # Stage batches interpolate these physical positions, never a
            # reconstructed displacement or a cached approximate pressure.
            self.position_first=owner.normal._positions(owner._full(first["local"]))
            self.position_last=owner.normal._positions(owner._full(last["local"]))
            for array in (*self.position_first,*self.position_last):array.setflags(write=False)
        for array in (self.cross,self.height,self.normal):array.setflags(write=False)

    def pressure(self,fractions):
        if not self.full_coverage:
            frames=self.frames(fractions)
            if any(frame is None for frame in frames):
                raise ValueError("prepared partial pressure requires an ordinary stage fallback")
            return np.array([frame["pressure"] for frame in frames]).reshape(-1,len(self.indices))
        t=np.asarray(fractions,dtype=float)
        if t.ndim!=1 or not np.all(np.isfinite(t)) or np.any((t<0)|(t>1)):
            raise ValueError("prepared pressure needs finite path fractions in[0,1]")
        if len(t)>self.maximum_samples:raise MemoryError("prepared pressure sample cap exceeded")
        cross=np.polynomial.polynomial.polyval(t,self.cross.T).T
        height=np.polynomial.polynomial.polyval(t,self.height.T).T
        denominator=cross@self.normal
        if np.any(denominator<=0):raise ValueError("prepared source-normal projection is unresolved")
        ratio=np.linalg.norm(cross,axis=1)/denominator
        gaps=height*ratio[:,None]
        pressure=self.stiffness*np.maximum(-(gaps.sum(axis=1)[:,None]+gaps)/4,0.)
        if not np.all(np.isfinite(pressure)):raise ValueError("nonfinite prepared pressure")
        result=np.empty_like(pressure);result[:,self.indices]=pressure
        return result

    def frames(self,fractions):
        """Small disposable batches; no quadrature domains or physical state."""
        t=np.asarray(fractions,dtype=float)
        if t.ndim!=1 or not np.all(np.isfinite(t)) or np.any((t<0)|(t>1)):
            raise ValueError("prepared pressure needs finite path fractions in[0,1]")
        if len(t)>self.maximum_samples:raise MemoryError("prepared pressure sample cap exceeded")
        pressure=self.pressure(t) if self.full_coverage else None
        first,last=self.first,self.last
        local=first["local"]+t[:,None]*(last["local"]-first["local"])
        source=first["source"][0]+t[:,None,None]*(last["source"][0]-first["source"][0])
        targets={e:c+t[:,None,None]*(last["target"][e]-c) for e,c in first["target"].items()}
        area=sum((np.cross(c[:,1]-c[:,0],c[:,2]-c[:,0]) for c in targets.values()),np.zeros((len(t),3)))
        normal=area/np.linalg.norm(area,axis=1)[:,None]
        initial=next(iter(targets.values()))
        tangent=initial[:,1]-initial[:,0];tangent/=np.linalg.norm(tangent,axis=1)[:,None]
        if not self.full_coverage:
            # Pressure still uses the ordinary per-face polygons and shape
            # guards. This path removes full-frame work maps, patch/hull
            # preparation and unused material integration domains at each time.
            physical=[a+t[:,None,None]*(b-a) for a,b in zip(self.position_first,self.position_last)]
            pressure=[]
            for i in range(len(t)):
                values=self.owner._partial_planar_pressure(physical[0][i],physical[1][i],
                    {e:c[i] for e,c in targets.items()},normal[i],initial[i,0])
                pressure.append(values)
        frames=[]
        for i in range(len(t)):
            if pressure[i] is None:
                # Exact path eligibility need not survive floating interpolation
                # bit-for-bit. The owner performs a counted ordinary fallback.
                frames.append(None)
                continue
            corners={e:c[i] for e,c in targets.items()}
            basis=np.column_stack((tangent[i],np.cross(normal[i],tangent[i]),normal[i]))
            frame=dict(local=local[i],pressure=pressure[i],target=corners,normal=normal[i],
                       basis=basis,origin=initial[i,0],source=(source[i],))
            for array in (frame["local"],frame["pressure"],frame["normal"],frame["basis"],
                          frame["origin"],*frame["source"],*corners.values()):
                array.setflags(write=False)
            frames.append(frame)
        return frames


def prepare_s3_plane_pressure_path(owner,first,last,*,allow_partial=False):
    """Return None unless the complete segment is provably eligible.

    The existing owner supplies a conforming disk topology. This specialization
    currently accepts one source triangle; other source topologies fall back.
    """
    if (len(owner.template.source_adapters)!=1 or owner.normal.augmented
            or owner.normal.law.pressure_basis is not None
            or np.any(owner.normal.normal_multipliers)
            or not np.array_equal(first["normal"],last["normal"])):return None
    n=_vector(first["normal"])
    source=tuple(_vector(a,b) for a,b in zip(first["source"][0],last["source"][0]))
    cross=_cross(_vsub(source[1],source[0]),_vsub(source[2],source[0]))
    denominator=_dot(cross,n)
    reference=owner.template.source_adapters[0].reference_positions
    ref=tuple(_vector(x) for x in reference)
    if not _positive(denominator) or not _positive(_dot(cross,_cross(_vsub(ref[1],ref[0]),_vsub(ref[2],ref[0])))):
        return None
    origin=_vector(first["origin"],last["origin"])
    vertices={};edges=[]
    for element,adapter in owner.template.target_adapters.items():
        triangle=tuple(_vector(a,b) for a,b in zip(first["target"][element],last["target"][element]))
        target_cross=_cross(_vsub(triangle[1],triangle[0]),_vsub(triangle[2],triangle[0]))
        target_ref=tuple(_vector(x) for x in adapter.reference_positions)
        ref_cross=_cross(_vsub(target_ref[1],target_ref[0]),_vsub(target_ref[2],target_ref[0]))
        if not _positive(_dot(target_cross,n)) or not _positive(_dot(target_cross,ref_cross)):return None
        for node,position in zip(adapter.node_ids,triangle):
            if any(_dot(_vsub(position,origin),n)):return None
            if node in vertices and vertices[node]!=position:return None
            vertices[node]=position
        for i,node in enumerate(adapter.node_ids):
            following=adapter.node_ids[(i+1)%3]
            if tuple(sorted((node,following))) in owner.template.boundary_edges:
                edges.append((node,following))
    heights=tuple(_dot(_vsub(x,origin),n) for x in source)
    full_coverage=True
    for a,b in edges:
        start=vertices[a];edge=_vsub(vertices[b],start)
        # Convexity throughout the path, including collinear boundary vertices.
        for vertex in vertices.values():
            if not _positive(_dot(_cross(edge,_vsub(vertex,start)),n),strict=False):return None
        for position,height in zip(source,heights):
            # Multiply source-normal projected edge distance by the certified
            # positive denominator: this is a polynomial of degree at most4.
            relative=_vsub(_scale(_vsub(position,start),denominator),_scale(cross,height))
            if not _positive(_dot(_cross(edge,relative),n)):
                if not allow_partial:return None
                full_coverage=False
    return PreparedS3PlanePressurePath(owner,first,last,cross,heights,full_coverage=full_coverage)
