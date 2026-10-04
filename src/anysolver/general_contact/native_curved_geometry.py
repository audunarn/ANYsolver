"""Whole curved patch admission controls for fixed-plane development work.

These are sufficient conservative controls, independent of contact quadrature.
An unresolved orientation bound is not a proof of physical inversion. Current
plane-gap enclosures do not certify a moving path or a collision time.
"""
from dataclasses import dataclass
from fractions import Fraction
from math import sqrt

import numpy as np

from anysolver._ge_beam3_p5.arrays import _array
from .capped_cylinder import _sqrt_bound
from .native_surface_bounds import _reference_radial_gain, _rotation_gain, _restrict_q2
from .native_retained_station import _readonly


@dataclass(frozen=True)
class CurvedPatchGeometryControl:
    orientation_lower: float
    cell_orientation_lower: tuple
    gap_lower_m: float
    gap_upper_m: float
    search_box: np.ndarray


def _reference_norm_bounds(reference, cell, *, actual_roll=False):
    """Affine Q2 tangent norm and frame-derivative norm bounds.

    Normalized affine tangent has |n'|<=|b|/min|v|. Shortest transport
    T=I+K+K²/d has |T'|<=A*N1+2*A²*N1/d+A³*N1/d².
    Roll derivative is bounded by5*N1+2*roll_rate, with the formulation's
    frozen roll_rate<0.9*pi. The Q2 tangent remains in the endpoint cone;
    nodal tangent misalignment and arithmetic reduce the denominator bound.
    """
    F=lambda v:Fraction(float(v))
    X=[[F(v) for v in row] for row in reference.coordinates]
    a=[(X[2][j]-X[0][j])/2 for j in range(3)]
    b=[X[0][j]-2*X[1][j]+X[2][j] for j in range(3)]
    left,right=(Fraction(-1),Fraction(0)) if cell==0 else (Fraction(0),Fraction(1))
    bb=sum(v*v for v in b)
    ab=sum(v*w for v,w in zip(a,b))
    minimum=left if bb==0 else max(left,min(right,-ab/bb))
    square=lambda xi:sum((v+xi*w)**2 for v,w in zip(a,b))
    jmin=float(_sqrt_bound(square(minimum)))
    jmax=float(_sqrt_bound(max(square(left),square(right)),upper=True))
    B=float(_sqrt_bound(bb,upper=True))
    eps=np.finfo(float).eps
    scale=max(1.,jmax,B)
    jmin-=128*eps*scale
    jmax+=128*eps*scale;B+=128*eps*scale
    if jmin<=0. or not np.all(np.isfinite((jmin,jmax,B))):
        raise ValueError('curved material reference derivative bound unresolved')
    nodes=reference.nodal_triads
    k0=reference.tangent(float(left));k1=reference.tangent(float(right))
    A=_rotation_gain(nodes[cell])
    mismatch=float(np.linalg.norm(nodes[cell,:,0]-k0))+128*eps
    # Compensated affine evaluation still rounds products. Near a small
    # Jacobian, its angular uncertainty must reduce the whole-cell cone bound.
    tangent_error=32*eps*scale/jmin
    denominator=1+float(k0@k1)-mismatch-8*tangent_error-256*eps
    if denominator<=1+np.cos(.9*np.pi):
        raise ValueError('curved material frame interval denominator unresolved')
    N1=B/jmin
    T=1+A+A*A/denominator
    T1=A*N1+2*A*A*N1/denominator+A**3*N1/denominator**2
    # The work support control may use the formulation-owned constant roll
    # rate; the historical whole-patch control retains its frozen worst case.
    roll=abs(float(reference._half_frame_data[cell][1])) if actual_roll else .9*np.pi
    if not np.isfinite(roll) or (actual_roll and roll>=.9*np.pi):
        raise ValueError('curved material reference roll bound unresolved')
    # At exactly zero owned roll, its axis rotation is identically I and its
    # derivative is zero. Only shortest transport contributes; no fitted bound.
    roll_derivative=0. if actual_roll and roll==0. else 5*N1+2*roll
    prime=(roll_derivative*T+(1+128*eps)*T1)*A
    prime*=1+4096*eps/denominator**2
    gram=max(float(np.linalg.norm(f.T@f-np.eye(3))) for f in nodes)
    gram+=128*eps*(1+max(float(np.linalg.norm(f))**2 for f in nodes))
    # Transported first column error, including clipped dot products and roll.
    first_error=64*(gram+128*eps)/denominator**2+8*tangent_error
    return jmin,jmax,prime,first_error


def curved_patch_geometry_control(rule, positions, position_low, cell_rotations,
                                  origin, normal):
    """Require positive oriented material area throughout all cells/arcs.

    Let W=(Uc*R0 e2) cross (Uc*R0 e3), independent of arc angle.
    Signed area/r² is (c+Uc*L'+Uc*R0'*rho).dot(W).
    c+Uc*L'=Uc*J*n + (c-Uc*c_ref). A near-rotation Gram bound
    encloses W-Uc*n; no sampled positivity establishes this test.
    """
    origin=_array(origin,(3,),'curved material plane origin')
    normal=_array(normal,(3,),'curved material plane normal')
    if abs(np.linalg.norm(normal)-1.)>1e-12:
        raise ValueError('unit curved material plane normal required')
    bounds=rule.current_bounds(positions,position_low,cell_rotations)
    reference=rule.samples[0].station.reference
    radius=float(rule.definition['radius'])
    high=np.asarray(positions);low=np.asarray(position_low);U=np.asarray(cell_rotations)
    Fgain=_reference_radial_gain(reference)
    cell_bounds=[]
    for cell in bounds.cells:
        jmin,jmax,prime,first_error=_reference_norm_bounds(reference,cell)
        gain=_rotation_gain(U[cell])
        eps=np.finfo(float).eps
        EU=float(np.linalg.norm(U[cell].T@U[cell]-np.eye(3)))+512*eps
        # Bound upper and lower Gram deviations of admitted transport/roll.
        E=4*((gain*Fgain)**2-1)+1024*eps
        if E>=.1 or not np.isfinite(E):
            raise ValueError('curved material orientation frame bound unresolved')
        # For proper near rotations, |cofactor(X)-X|<=2*|X.T*X-I|.
        error=2*E+gain*first_error
        chord=np.array([float((Fraction(float(high[cell+1,i]))+Fraction(float(low[cell+1,i])))-
                              (Fraction(float(high[cell,i]))+Fraction(float(low[cell,i]))))
                        for i in range(3)])
        ref_chord=reference.coordinates[cell+1]-reference.coordinates[cell]
        difference=float(np.linalg.norm(chord-U[cell]@ref_chord))
        padding=8192*eps*max(1.,jmax,difference,radius*prime,
                            np.max(np.abs(reference.coordinates)))
        lower=(jmin*(1-EU-128*eps)-difference*gain-
               (gain*jmax+difference)*error-
               radius*gain*prime*(gain*Fgain)**2-padding)
        if not np.isfinite(lower) or lower<=0.:
            raise ValueError('curved material whole-patch orientation unresolved')
        cell_bounds.append((cell,float(lower)))
    # Direct oriented projection avoids axis-box inflation under rigid motion.
    F=lambda v:Fraction(float(v))
    X=[[F(v) for v in row] for row in reference.coordinates]
    b=[X[0][j]-2*X[1][j]+X[2][j] for j in range(3)]
    p=[[F(h)+F(l) for h,l in zip(hr,lr)] for hr,lr in zip(high,low)]
    lo,hi=rule.definition['xi_range'];slabs=[]
    for cell,left,right in ((0,max(lo,-1.),min(hi,0.)),(1,max(lo,0.),min(hi,1.))):
        if right<=left:continue
        turn=[sum(F(U[cell,i,j])*b[j] for j in range(3)) for i in range(3)]
        controls=[p[cell],[(p[cell][i]+p[cell+1][i])/2-turn[i]/4 for i in range(3)],p[cell+1]]
        lane=tuple(sum((point[i]-F(origin[i]))*F(normal[i]) for i in range(3)) for point in controls)
        l=F(left)+(1 if cell==0 else 0);r=F(right)+(1 if cell==0 else 0)
        restricted=_restrict_q2((lane,),l,r)[0]
        extent=F(radius*Fgain*_rotation_gain(U[cell])*float(np.linalg.norm(normal)))
        extent+=F(bounds.roundoff_padding_m*max(1.,float(np.linalg.norm(normal,1))))
        slabs.append((min(restricted)-extent,max(restricted)+extent))
    lower=float(np.nextafter(float(min(s[0] for s in slabs)),-np.inf))
    upper=float(np.nextafter(float(max(s[1] for s in slabs)),np.inf))
    if not np.all(np.isfinite((lower,upper))):
        raise ValueError('curved material plane enclosure overflow')
    return CurvedPatchGeometryControl(min(v for _,v in cell_bounds),tuple(cell_bounds),
                                     lower,upper,bounds.as_search_box())
