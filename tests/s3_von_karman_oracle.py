"""Independent membrane term of the adopted S3 V2D von Karman law (S3_V2D_VK_R1).

Scope: a flat, linear-elastic, isotropic P1 triangle whose in-plane nodal
translations are fixed, so the membrane strain is the pure von Karman part
eps = (wx**2/2, wy**2/2, wx*wy) of an affine normal displacement w.  With the
plane-stress matrix this gives eps.D.eps = E/(4*(1-nu**2))*|grad w|**4, hence
U = area*E*t/(8*(1-nu**2))*|grad w|**4.  This generalises the analytic cubic
used for the retargeted coupled oracle in commit 706bf011c
(area*E*t*w**3/(162*(1-nu**2)) for grad w = (0, w/3)).  Bending and transverse
shear stay in the linear structural stiffness; this adds only the membrane
energy.  No production element, operator or assembly code is called.
"""
import numpy as np


def p1_von_karman_membrane(points, normal, w, E, nu, t):
    """Return energy, gradient and Hessian with respect to the three normal displacements."""
    points = np.asarray(points, dtype=float)
    normal = np.asarray(normal, dtype=float)
    normal = normal/np.linalg.norm(normal)
    assert np.allclose((points-points[0])@normal, 0., atol=1e-14), "flat triangle required"
    seed = np.eye(3)[int(np.argmin(abs(normal)))]
    e1 = np.cross(normal, seed); e1 /= np.linalg.norm(e1)
    e2 = np.cross(normal, e1)
    xy = np.c_[points@e1, points@e2]
    interpolation = np.c_[np.ones(3), xy]
    G = np.linalg.inv(interpolation)[1:, :].T  # rows: nodal shape gradients
    area = abs(np.linalg.det(interpolation))/2
    c = area*E*t/(8*(1-nu*nu))
    w = np.asarray(w)
    g = G.T@w
    s = g@g
    Gg = G@g
    energy = c*s*s
    gradient = 4*c*s*Gg
    hessian = 4*c*(s*(G@G.T)+2*np.outer(Gg, Gg))
    return energy, gradient, hessian


def p1_von_karman_inplane_force(points, normal, w, E, nu, t):
    """Global in-plane nodal forces area*N.grad(N_i) of the VK membrane resultant.

    These act on the fixed in-plane translations (support reactions); they
    are needed only when a check compares full element force vectors.
    """
    points = np.asarray(points, dtype=float)
    normal = np.asarray(normal, dtype=float)
    normal = normal/np.linalg.norm(normal)
    seed = np.eye(3)[int(np.argmin(abs(normal)))]
    e1 = np.cross(normal, seed); e1 /= np.linalg.norm(e1)
    e2 = np.cross(normal, e1)
    interpolation = np.c_[np.ones(3), points@e1, points@e2]
    G = np.linalg.inv(interpolation)[1:, :].T
    area = abs(np.linalg.det(interpolation))/2
    gx, gy = G.T@np.asarray(w)
    D = E*t/(1-nu*nu)*np.array(((1, nu, 0), (nu, 1, 0), (0, 0, (1-nu)/2)))
    Nxx, Nyy, Nxy = D@np.array((gx*gx/2, gy*gy/2, gx*gy))
    local = area*G@np.array(((Nxx, Nxy), (Nxy, Nyy)))
    return local[:, :1]*e1+local[:, 1:]*e2


def model_triangle_von_karman(model, node_ids, normal, u_normal, E, nu, t):
    """Convenience wrapper reading reference coordinates of one triangle from the fixture."""
    points = np.array([[model.mesh.nodes[n].x, model.mesh.nodes[n].y, model.mesh.nodes[n].z]
                       for n in node_ids])
    return p1_von_karman_membrane(points, normal, u_normal, E, nu, t)
