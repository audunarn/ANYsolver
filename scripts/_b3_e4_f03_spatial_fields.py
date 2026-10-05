"""Independent represented-polynomial fields for the F03 residual diagnostic.

This evaluates saved fields and the finite-square adjoint only. It neither
assembles a structural operator nor changes the saved equilibrium state.
Exact coefficients denote the mathematical polynomials of binary64 inputs;
returned point values and the explicit cosine are ordinary floating values.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

import numpy as np
from numpy.polynomial import legendre as lg

from scripts import _b3_e4_f03_primal_exact_pose as exact
from scripts import _b3_e4_f03_spatial_contract as contract


ZERO = Fraction(0)
ONE = Fraction(1)
Poly = tuple[Fraction, ...]
Tensor = tuple[tuple[Fraction, ...], ...]


def _add(a: Poly, b: Poly) -> Poly:
    return tuple((a[k] if k < len(a) else ZERO) +
                 (b[k] if k < len(b) else ZERO)
                 for k in range(max(len(a), len(b))))


def _scale(a: Poly, c: Fraction) -> Poly:
    return tuple(c * v for v in a)


def _derivative(a: Poly) -> Poly:
    """Derivative of exact Legendre coefficients with respect to argument."""
    result = [ZERO] * len(a)
    for degree in range(1, len(a)):
        for lower in range(degree - 1, -1, -2):
            result[lower] += a[degree] * (2 * lower + 1)
    return tuple(result)


def _multiply_argument(a: Poly) -> Poly:
    result = [ZERO] * (len(a) + 1)
    for k, value in enumerate(a):
        result[k+1] += value * Fraction(k+1, 2*k+1)
        if k:
            result[k-1] += value * Fraction(k, 2*k+1)
    return tuple(result)


def _primitive_s(a: Poly) -> Poly:
    """Legendre coefficients of a primitive for physical station s.

    The arbitrary constant cancels in every endpoint difference.
    """
    result = [ZERO] * (len(a) + 1)
    for k, value in enumerate(a):
        if k == 0:
            result[1] += value * contract.Q_L0 / 2
        else:
            result[k+1] += value * contract.Q_L0 / (2*(2*k+1))
            result[k-1] -= value * contract.Q_L0 / (2*(2*k+1))
    return tuple(result)


def _multiply_s(a: Poly) -> Poly:
    return _scale(_add(_multiply_argument(a), a), contract.Q_L0/2)


def _legendre_shell(n: int, q: tuple[Fraction, ...]) -> tuple[Tensor, Tensor]:
    size=n+1
    m=n*n-1
    values=[[[ZERO]*size for _ in range(size)] for _ in range(2)]
    for i in range(n-1):
        unit=tuple(ONE if j==i else ZERO for j in range(i+1))
        factor=_add(unit, _scale(_multiply_argument(_multiply_argument(unit)), -ONE))
        for j in range(n+1):
            for c in range(2):
                coefficient=q[c*m+i*(n+1)+j]
                for k, f in enumerate(factor):
                    values[c][k][j] += coefficient*f
    return tuple(tuple(tuple(row) for row in v) for v in values)  # type: ignore[return-value]


def _tensor_add(a: Tensor, b: Tensor) -> Tensor:
    return tuple(_add(x,y) for x,y in zip(a,b))


def _tensor_scale(a: Tensor, factor: Fraction) -> Tensor:
    return tuple(_scale(row,factor) for row in a)


def _tensor_dx(a: Tensor) -> Tensor:
    size=len(a)
    result=[[ZERO]*len(a[0]) for _ in range(size)]
    for j in range(len(a[0])):
        derivative=_derivative(tuple(a[i][j] for i in range(size)))
        for i,value in enumerate(derivative): result[i][j]=value
    return tuple(tuple(row) for row in result)


def _tensor_dy(a: Tensor) -> Tensor:
    return tuple(_scale(_derivative(row),Fraction(2)) for row in a)


def _tensor_float(a: Tensor) -> np.ndarray:
    value=np.asarray([[float(v) for v in row] for row in a],dtype=np.float64)
    if not np.all(np.isfinite(value)):
        raise ValueError('nonfinite converted represented tensor coefficient')
    return value


def _readonly(values: object) -> np.ndarray:
    a=np.asarray(values,dtype=np.float64)
    if not np.all(np.isfinite(a)):
        raise ValueError('nonfinite converted represented physical coefficient')
    return np.frombuffer(a.tobytes(),dtype=np.float64).reshape(a.shape)


@dataclass(frozen=True)
class SpatialModel:
    n: int
    q: tuple[Fraction, ...]
    eta: tuple[Fraction, ...]
    shell_coefficients: tuple[Tensor, Tensor]
    strain_coefficients: tuple[Tensor, Tensor, Tensor]
    stress_coefficients: tuple[Tensor, Tensor, Tensor]
    divergence_coefficients: tuple[Tensor, Tensor]
    section_coefficients: tuple[Poly, Poly, Poly]
    density_coefficients: tuple[Poly, Poly, Poly]
    density_primitives: tuple[Poly, Poly, Poly]
    theta_moment_primitive: Poly
    atom_coefficients: tuple[tuple[Fraction,Fraction,Fraction], ...]
    held_J: Fraction
    J_geom: Fraction
    gamma: Fraction

    @property
    def atoms(self) -> np.ndarray:
        """Owned immutable physical endpoint atoms (N,N,Nm)."""
        return _readonly([[float(v) for v in row] for row in self.atom_coefficients])


def model_from_saved(n: int, q: np.ndarray, eta: np.ndarray,
                     pose: exact.ExactPose) -> SpatialModel:
    """Bind a finite saved state to independently represented physical fields."""
    if type(n) is not int or not 2<=n<=24:
        raise ValueError('bounded spatial degree must be integer 2..24')
    m=2*(n*n-1)
    if (not isinstance(q,np.ndarray) or q.dtype!=np.float64 or
            q.shape!=(m,) or not np.all(np.isfinite(q)) or
            not isinstance(eta,np.ndarray) or eta.dtype!=np.float64 or
            eta.shape!=(3,) or not np.all(np.isfinite(eta))):
        raise ValueError('invalid saved physical q/eta')
    q_exact=tuple(Fraction.from_float(float(v)) for v in q)
    e_exact=tuple(Fraction.from_float(float(v)) for v in eta)
    if (not isinstance(pose,exact.ExactPose) or pose.n!=n or pose.q!=q_exact or
            pose.dx!=contract.Q_DX or pose.dy!=contract.Q_DY or
            pose.a!=contract.Q_A or pose.held_J!=contract.Q_J or
            pose.J_geom!=contract.Q_J_GEOM or
            pose.gamma!=contract.Q_GAMMA):
        raise ValueError('pose/state/represented geometry mismatch')
    shell=_legendre_shell(n,q_exact)
    strain=(_tensor_dx(shell[0]),_tensor_dy(shell[1]),
            _tensor_add(_tensor_dy(shell[0]),_tensor_dx(shell[1])))
    c=contract.Q_PLANE
    thick=contract.Q_THICKNESS
    stress=tuple(_tensor_scale(_tensor_add(
        _tensor_add(_tensor_scale(strain[0],c[i][0]),
                    _tensor_scale(strain[1],c[i][1])),
        _tensor_scale(strain[2],c[i][2])),thick) for i in range(3))
    divergence=(_tensor_add(_tensor_dx(stress[0]),_tensor_dy(stress[2])),
                _tensor_add(_tensor_dx(stress[2]),_tensor_dy(stress[1])))
    bu,bv,theta=pose.legendre
    n_poly=_scale(_derivative(bu),2*contract.Q_EA/contract.Q_L0)
    q_poly=_scale(_add(_scale(_derivative(bv),Fraction(2)/contract.Q_L0),
                       _scale(theta,-ONE)),contract.Q_GAS)
    m_poly=_scale(_derivative(theta),2*contract.Q_EI/contract.Q_L0)
    section=(n_poly,q_poly,m_poly)
    density=(_scale(_derivative(n_poly),2/contract.Q_L0),
             _add(_scale(_derivative(q_poly),2/contract.Q_L0),
                  (contract.Q_F0/contract.Q_L0,)),
             _add(_scale(_derivative(m_poly),2/contract.Q_L0),q_poly))
    def endpoint(poly: Poly, side: int) -> Fraction:
        return sum((v*(side**j) for j,v in enumerate(poly)),ZERO)
    roots=tuple(endpoint(poly,-1) for poly in section)
    tips=tuple(endpoint(poly,1) for poly in section)
    atoms=(tuple(roots[i]-e_exact[i] for i in range(3)),
           tuple(-tips[i] for i in range(3)))
    return SpatialModel(n,q_exact,e_exact,shell,strain,stress,divergence,
                        section,density,tuple(_primitive_s(p) for p in density),
                        _primitive_s(_multiply_s(density[2])),atoms,
                        pose.held_J,pose.J_geom,pose.gamma)


def _coordinates(x: object,y: object) -> tuple[np.ndarray,np.ndarray]:
    xx,yy=np.broadcast_arrays(np.asarray(x,dtype=np.float64),
                              np.asarray(y,dtype=np.float64))
    if not np.all(np.isfinite(xx)) or not np.all(np.isfinite(yy)):
        raise ValueError('nonfinite panel coordinate')
    if (np.any(xx<-.5) or np.any(xx>1.5) or
            np.any(yy<-.5) or np.any(yy>.5)):
        raise ValueError('outside frozen panel')
    return xx,yy


def _evaluate_tensor(coeff: Tensor,x: np.ndarray,y: np.ndarray) -> np.ndarray:
    return np.asarray(lg.legval2d(x-.5,2*y,_tensor_float(coeff)),dtype=np.float64)


def shell_fields(model: SpatialModel,x: object,y: object) -> dict[str,np.ndarray]:
    if not isinstance(model,SpatialModel): raise ValueError('invalid spatial model')
    xx,yy=_coordinates(x,y)
    groups=(('displacement',model.shell_coefficients),
            ('strain',model.strain_coefficients),
            ('stress',model.stress_coefficients),
            ('divergence',model.divergence_coefficients))
    result={name:np.stack([_evaluate_tensor(c,xx,yy) for c in group],axis=-1)
            for name,group in groups}
    if any(not np.all(np.isfinite(v)) for v in result.values()):
        raise ValueError('nonfinite evaluated shell field')
    return result


def _station(model: SpatialModel,s: object) -> np.ndarray:
    if not isinstance(model,SpatialModel): raise ValueError('invalid spatial model')
    ss=np.asarray(s,dtype=np.float64)
    if not np.all(np.isfinite(ss)) or np.any(ss<0) or np.any(ss>float(contract.L0)):
        raise ValueError('outside beam station')
    return ss


def _evaluate_poly(poly: Poly,s: np.ndarray) -> np.ndarray:
    return np.asarray(lg.legval(2*s/contract.L0-1,
                  np.asarray([float(v) for v in poly],dtype=np.float64)),
                  dtype=np.float64)


def section_resultants(model: SpatialModel,s: object) -> np.ndarray:
    ss=_station(model,s)
    result=np.stack([_evaluate_poly(p,ss) for p in model.section_coefficients],
                    axis=-1)
    if not np.all(np.isfinite(result)): raise ValueError('nonfinite section')
    return result


def line_density(model: SpatialModel,s: object) -> np.ndarray:
    ss=_station(model,s)
    result=np.stack([_evaluate_poly(p,ss) for p in model.density_coefficients],
                    axis=-1)
    result[...,1]+=float(contract.Q_F0/(4*contract.Q_L0))*np.cos(contract.OMEGA*ss)
    if not np.all(np.isfinite(result)): raise ValueError('nonfinite density')
    return result


def _primitive_difference(poly: Poly,a: np.ndarray,b: np.ndarray) -> np.ndarray:
    return _evaluate_poly(poly,b)-_evaluate_poly(poly,a)


def area_load(model: SpatialModel,x: object,y: object,cell: int) -> np.ndarray:
    """Line/root/tip area forces in N/m^2, using one fixed cell branch.

    Row-major cell numbering is j*9+i: five y strips, nine x strips.
    Points on a shared cut use the chosen cell's one-sided continuation.
    """
    if not isinstance(model,SpatialModel) or type(cell) is not int or not 0<=cell<45:
        raise ValueError('invalid model or frozen cell')
    xx,yy=_coordinates(x,y)
    xlo,xhi,ylo,yhi=contract.CELLS[cell]
    if (np.any(xx<float(xlo)-1e-14) or np.any(xx>float(xhi)+1e-14) or
            np.any(yy<float(ylo)-1e-14) or np.any(yy>float(yhi)+1e-14)):
        raise ValueError('point outside selected one-sided cell closure')
    xmid=(xlo+xhi)/2;ymid=(ylo+yhi)/2
    shape=xx.shape+(3,2)
    result=np.zeros(shape,dtype=np.float64)
    S=float(contract.Q_AREA);J=float(model.held_J)
    for l,r,yl,yh in contract.PADS:
        if not yl<ymid<yh: continue
        active=max(ZERO,xmid-r)<min(contract.Q_L0,xmid-l)
        if active:
            a=np.zeros_like(xx) if xmid-r<=0 else xx-float(r)
            b=np.full_like(xx,contract.L0) if xmid-l>=contract.Q_L0 else xx-float(l)
            integrated=[_primitive_difference(p,a,b)
                        for p in model.density_primitives]
            integrated[1]+=float(contract.Q_F0/(4*contract.Q_L0))/contract.OMEGA*(
                np.sin(contract.OMEGA*b)-np.sin(contract.OMEGA*a))
            moment=_primitive_difference(model.theta_moment_primitive,a,b)
            result[...,0,0]+=(integrated[0]-yy*integrated[2]/J)/S
            result[...,0,1]+=(integrated[1]+(xx*integrated[2]-moment)/J)/S
        for e,atom_index in ((ZERO,1),(contract.Q_L0,2)):
            if e+l<xmid<e+r:
                alpha=model.atom_coefficients[atom_index-1]
                result[...,atom_index,0]+=(float(alpha[0])-yy*float(alpha[2])/J)/S
                result[...,atom_index,1]+=(float(alpha[1])+
                                           (xx-float(e))*float(alpha[2])/J)/S
    if not np.all(np.isfinite(result)): raise ValueError('nonfinite area adjoint')
    return result
