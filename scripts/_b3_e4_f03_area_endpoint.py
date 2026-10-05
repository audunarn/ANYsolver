"""Floating endpoint diagnostics for the separate classical finite-pad law.

The shell derivative uses moving-pad boundary flux, independently of the
polygon-clipping pose assembly. This is a finite-mesh diagnostic, neither a
certified pointwise enclosure nor a continuum/native qualification.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable

import numpy as np

import _b3_e4_f03_area_line as line
import _b3_e4_f03_area_port as port
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as original
import _b3_e4_f03_independent_shell as shell


@dataclass(frozen=True)
class FirstCellDiagnostic:
    endpoint_gap_m: tuple[float, float, float]
    gap_derivative_l2: float  # m/sqrt(m) for physical station s in metres.
    weighted_derivative_m: tuple[float, float, float]
    first_hat_identity_residual_m: tuple[float, float, float]
    endpoint_bound_m: float  # Floating unconditional bound, including row residual.


def _displacement(model: shell.Panel, q: np.ndarray,
                  x: float, y: float) -> np.ndarray:
    """Direct regular-Q4/triangle interpolation, without pad clipping."""
    nx=2*model.n_s
    i=min(max(math.floor((x+.5)*model.n_s),0),nx-1)
    j=min(max(math.floor((y+.5)*model.n_y),0),model.n_y-1)
    xi=(x-(-.5+i/model.n_s))*model.n_s
    eta=(y-(-.5+j/model.n_y))*model.n_y
    bl=j*(nx+1)+i
    br=bl+1
    tl=bl+nx+1
    tr=tl+1
    if model.topology=='Q4':
        nodes=(bl,br,tr,tl)
        weights=((1-xi)*(1-eta),xi*(1-eta),xi*eta,(1-xi)*eta)
    else:
        if model.topology=='CST-CB' and (i+j)%2:
            nodes=(bl,br,tl) if xi+eta<=1 else (br,tr,tl)
        else:
            nodes=(bl,br,tr) if eta<=xi else (bl,tr,tl)
        a,b,c=model.nodes[list(nodes)]
        matrix=np.column_stack((b-a,c-a))
        uv=np.linalg.solve(matrix,np.array((x,y))-a)
        weights=(1-uv[0]-uv[1],uv[0],uv[1])
    value=np.zeros(2)
    for node,weight in zip(nodes,weights):
        value+=weight*q[2*node:2*node+2]
    return value


def _edge_integrals(model: shell.Panel, q: np.ndarray,
                    x: float, station: float, y0: float, y1: float
                    ) -> np.ndarray:
    """Integrate [ux,uy,(x-s)uy-y ux] on a pad's vertical edge."""
    breaks=[y0,y1]
    breaks.extend(-.5+j/model.n_y for j in range(1,model.n_y)
                  if y0<-.5+j/model.n_y<y1)
    if model.topology in ('CST','CST-CB'):
        i=min(max(math.floor((x+.5)*model.n_s),0),2*model.n_s-1)
        xi=(x-(-.5+i/model.n_s))*model.n_s
        for j in range(model.n_y):
            eta=1-xi if model.topology=='CST-CB' and (i+j)%2 else xi
            crossing=-.5+(j+eta)/model.n_y
            if y0<crossing<y1:
                breaks.append(crossing)
    breaks=sorted(set(breaks))
    nodes,weights=np.polynomial.legendre.leggauss(2)
    result=np.zeros(3)
    for left,right in zip(breaks[:-1],breaks[1:]):
        for node,weight in zip(nodes,weights):
            y=(left+right)/2+(right-left)*node/2
            ux,uy=_displacement(model,q,x,y)
            result+=(right-left)*weight/2*np.array(
                (ux,uy,(x-station)*uy-y*ux))
    return result


def shell_pose_derivative(model: shell.Panel, station: float,
                          halfwidth: float, qs: np.ndarray) -> np.ndarray:
    """d/ds [averaged ux, averaged uy, proper-fit yaw] by boundary flux.

    Only the subtractive mean-uy term in yaw uses ``port.pose``. All moving
    boundary integrals use independent, direct Q4/CST interpolation.
    """
    q=np.asarray(qs,dtype=float)
    if (q.shape!=(model.dof_count,) or not np.all(np.isfinite(q)) or
            not math.isfinite(station) or not 0<=station<=1 or
            not math.isfinite(halfwidth) or not 1e-4<=halfwidth<=.2):
        raise ValueError('invalid finite-pad derivative input')
    area=4*halfwidth**2
    inertia=shell.YAW_DENOMINATOR/4+2*halfwidth**2/3
    flux=np.zeros(3)
    for dx,dy in shell.OFFSETS:
        left=station+dx-halfwidth
        right=station+dx+halfwidth
        bottom,top=dy-halfwidth,dy+halfwidth
        flux+=(_edge_integrals(model,q,right,station,bottom,top)-
               _edge_integrals(model,q,left,station,bottom,top))/(4*area)
    mean_uy=float((port.pose(model,station,halfwidth)@q)[1])
    return np.array((flux[0],flux[1],(flux[2]-mean_uy)/inertia))


def beam_pose_derivative(n_beam: int, station: float,
                         qb: np.ndarray) -> np.ndarray:
    """Analytic [u',v',theta'] of the quadratic/Hermite beam trace."""
    q=np.asarray(qb,dtype=float)
    if (q.shape!=(beam.dof_count(n_beam),) or not np.all(np.isfinite(q)) or
            not math.isfinite(station) or not 0<=station<=1):
        raise ValueError('invalid beam derivative input')
    cell=min(int(station*n_beam),n_beam-1)
    shape,strain=beam.fields(station*n_beam-cell,1/n_beam)
    local=q[beam.element_dofs(n_beam,cell)]
    return np.array((strain[0]@local,
                     (strain[2]+shape[2])@local,
                     strain[1]@local))


def first_hat_moments(breaks: np.ndarray, width: float,
                      derivative: Callable[[float],np.ndarray],
                      order: int = 10) -> tuple[float,np.ndarray]:
    """Floating ||g'|| on [0,h] (m/sqrt(m)) and ∫(1-s/h)^2 g'(s) ds (m).

    If the P1 endpoint row is exactly zero, g(0) is the negative of the
    second return value, with |g(0)| <= sqrt(h/5) ||g'||. With a finite row
    residual that residual norm must also be added to the endpoint bound.
    The caller supplies all branch breaks; this is not an interval certificate.
    """
    knots=np.asarray(breaks,dtype=float)
    if (not math.isfinite(width) or width<=0 or
            knots.ndim!=1 or len(knots)<2 or
            not np.all(np.isfinite(knots)) or
            abs(knots[0])>1e-12 or abs(knots[-1]-width)>1e-12 or
            np.any(np.diff(knots)<=0) or not isinstance(order,int) or
            not 4<=order<=16):
        raise ValueError('invalid first-cell integration partition')
    roots,weights=np.polynomial.legendre.leggauss(order)
    squared=0.
    weighted=np.zeros(3)
    for left,right in zip(knots[:-1],knots[1:]):
        for root,weight in zip(roots,weights):
            s=(left+right)/2+(right-left)*root/2
            d=np.asarray(derivative(float(s)),dtype=float)
            if d.shape!=(3,) or not np.all(np.isfinite(d)):
                raise ValueError('nonfinite gap derivative')
            measure=(right-left)*weight/2
            squared+=measure*float(d@d)
            weighted+=measure*(1-s/width)**2*d
    return math.sqrt(max(squared,0.)),weighted


def first_cell_gap_diagnostic(model: shell.Panel, n_beam: int,
                              n_mortar: int, halfwidth: float,
                              qs: np.ndarray, qb: np.ndarray,
                              order: int = 10) -> FirstCellDiagnostic:
    """Endpoint gap (m), derivative L2 norm (m/sqrt(m)), P1-hat identity.

    The station coordinate is physical metres on the one-metre fixture.
    The returned endpoint bound includes the actual finite first-hat row
    residual and has displacement units of metres. It uses floating
    quadrature, so it is not a certified pointwise bound.
    """
    knots=line.overlay(model,n_beam,n_mortar,halfwidth)
    width=1/n_mortar
    first=np.r_[knots[knots<width-1e-12],width]
    qs=np.asarray(qs,dtype=float)
    qb=np.asarray(qb,dtype=float)
    if (qs.shape!=(model.dof_count,) or
            qb.shape!=(beam.dof_count(n_beam),) or
            not np.all(np.isfinite(qs)) or not np.all(np.isfinite(qb))):
        raise ValueError('invalid finite gap fields')
    gap0=beam.trace(n_beam,0.)@qb-port.pose(model,0.,halfwidth)@qs
    gap0[2]*=original.YAW_LENGTH

    def derivative(s: float) -> np.ndarray:
        result=beam_pose_derivative(n_beam,s,qb)-shell_pose_derivative(
            model,s,halfwidth,qs)
        result[2]*=original.YAW_LENGTH
        return result

    norm,weighted=first_hat_moments(first,width,derivative,order)
    residual=gap0+weighted
    return FirstCellDiagnostic(tuple(map(float,gap0)),norm,
                               tuple(map(float,weighted)),
                               tuple(map(float,residual)),
                               math.sqrt(width/5)*norm+float(np.linalg.norm(residual)))
