"""First-principles oracle for the S3 V2D von Karman membrane law (S3_V2D_VK_R1).

Scope: the *von Karman excess* of the layered elastic S3 V2D element, i.e. everything
the VK strain adds to the element-local linear response, for any flat triangle in 3-D,
any reference-surface offset and director polarity, all 18 dofs (translations and
rotations).  The linear remainder (assumed shear, drilling, PL stabilisation) is
unchanged by the law and is not modelled here.

Derivation (nothing is read from production element code; formulas in
docs/S3_VON_KARMAN_ELEMENT_DEFINITION.md):
  local frame  x = (p1-p0)/|.|, z = n, y = z x x (nodes ordered so that (p1-p0)x(p2-p0).n > 0)
  P1 shape gradients G (3x2); local dofs per node (u, v, w, tx, ty, tz)
  curvature    kappa = p*(dty/dx, -dtx/dy, dty/dy - dtx/dx)         (p = director polarity)
  membrane     eps_m = (du/dx, dv/dy, du/dy+dv/dx) - offset*kappa    (strain at the mid-surface)
  VK           eps_vk = (wx^2/2, wy^2/2, wx*wy), (wx,wy) = grad of the node values w_i
  energy       U = area * 1/2 eps^T (t Q) eps, eps = eps_m + eps_vk
  excess       U_vk = U(eps_m + eps_vk) - U(eps_m)   (purely quadratic part removed)
Elastic layered integration is exact (Lobatto, >=3 points, integrand degree <= 2),
and the section is symmetric about the mid-surface, so membrane and bending decouple.
All functions accept complex u (complex-step differentiation).
"""
import numpy as np


def _frame(points, normal):
    points = np.asarray(points, dtype=float)
    n = np.asarray(normal, dtype=float)
    n = n/np.linalg.norm(n)
    order = (0, 1, 2) if np.cross(points[1]-points[0], points[2]-points[0]) @ n > 0 else (0, 2, 1)
    p = points[list(order)]
    ex = p[1]-p[0]
    ex = ex/np.linalg.norm(ex)
    ey = np.cross(n, ex)
    ey = ey/np.linalg.norm(ey)
    R = np.column_stack((ex, ey, n))
    xy = np.column_stack(((p-p[0]) @ ex, (p-p[0]) @ ey))
    interpolation = np.column_stack((np.ones(3), xy))
    G = np.linalg.inv(interpolation)[1:, :].T      # (3,2): dN_i/dx, dN_i/dy
    area = abs(np.linalg.det(interpolation))/2
    return order, R, G, area


def _operators(G, offset, polarity):
    """Membrane (3x18) and curvature (3x18) operators on local dofs (u,v,w,tx,ty,tz)*3."""
    Bk = np.zeros((3, 18))
    Bm = np.zeros((3, 18))
    for i in range(3):
        gx, gy = G[i]
        c = 6*i
        Bm[0, c] = gx
        Bm[1, c+1] = gy
        Bm[2, c], Bm[2, c+1] = gy, gx
        Bk[0, c+4] = gx
        Bk[1, c+3] = -gy
        Bk[2, c+4], Bk[2, c+3] = gy, -gx
    Bk = polarity*Bk
    return Bm-offset*Bk, Bk


def _plane_stress(E, nu, t):
    return t*E/(1-nu*nu)*np.array(((1, nu, 0), (nu, 1, 0), (0, 0, (1-nu)/2)))


class S3VonKarmanExcess:
    """Excess energy, force and tangent in the external (global) 18-dof ordering."""

    def __init__(self, points, normal, E, nu, thickness, offset=0., polarity=1.):
        self.order, self.R, self.G, self.area = _frame(points, normal)
        self.Bm, self.Bk = _operators(self.G, offset, polarity)
        self.A = _plane_stress(E, nu, thickness)
        # local = L @ external
        L = np.zeros((18, 18))
        for internal, external in enumerate(self.order):
            for part in (0, 3):
                L[6*internal+part:6*internal+part+3, 6*external+part:6*external+part+3] = self.R.T
        self.L = L
        self.grad = np.zeros((2, 18))
        self.grad[:, 2::6] = self.G.T

    def _strain(self, ul):
        wx, wy = self.grad @ ul
        return self.Bm @ ul, np.array((.5*wx*wx, .5*wy*wy, wx*wy)), (wx, wy)

    def energy(self, u):
        ul = self.L @ np.asarray(u)
        em, ev, _ = self._strain(ul)
        e = em+ev
        return .5*self.area*(e @ self.A @ e-em @ self.A @ em)

    def force(self, u):
        ul = self.L @ np.asarray(u)
        em, ev, (wx, wy) = self._strain(ul)
        J = self.Bm.copy().astype(ul.dtype)
        J[0] += wx*self.grad[0]
        J[1] += wy*self.grad[1]
        J[2] += wy*self.grad[0]+wx*self.grad[1]
        e = em+ev
        local = self.area*(J.T @ (self.A @ e)-self.Bm.T @ (self.A @ em))
        return self.L.T @ local

    def tangent(self, u):
        ul = self.L @ np.asarray(u)
        em, ev, (wx, wy) = self._strain(ul)
        J = self.Bm.copy().astype(ul.dtype)
        J[0] += wx*self.grad[0]
        J[1] += wy*self.grad[1]
        J[2] += wy*self.grad[0]+wx*self.grad[1]
        N = self.A @ (em+ev)
        geometric = self.grad.T @ np.array(((N[0], N[2]), (N[2], N[1]))) @ self.grad
        local = self.area*(J.T @ self.A @ J+geometric-self.Bm.T @ self.A @ self.Bm)
        return self.L.T @ local @ self.L
