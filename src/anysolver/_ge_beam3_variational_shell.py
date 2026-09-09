"""Private conservative shell pullback for the GE-B3 connection successor.

Unchanged local Q4/S3 operators supply forces, material history and tangent.
The new connection policy differentiates the COMPLETE deformational map, not
just its rigid rotation. It neither replaces the existing corotational route
nor grants production qualification. See GE_BEAM3_VARIATIONAL_SHELL_MAP.md.
"""
import numpy as np

from ._ge_beam3_mixed_ad import Jet2, matmul, matvec, transpose, so3_exp, so3_log
from ._ge_beam3_pose_joint import _exp_terms

POLICY = 'GE_BEAM3_PROCRUSTES_VARIATIONAL_SHELL_PULLBACK_V2'


def _davenport(c):
    trace = np.trace(c)
    z = np.array([c[2, 1]-c[1, 2], c[0, 2]-c[2, 0], c[1, 0]-c[0, 1]])
    return np.block([[np.array([[trace]]), z[None, :]],
                     [z[:, None], c+c.T-trace*np.eye(3)]])


def rotation_jets(reference, current):
    """Equal nodal-weight proper Procrustes fit and analytic two derivatives.

Centered vectors retain their lengths (no unit-vector normalization). The
normalized largest quaternion eigenpair is differentiated implicitly. Only
the top eigenvalue must be simple; repeated lower eigenvalues are harmless.
"""
    ref = np.asarray(reference, dtype=float)
    x = np.asarray(current, dtype=float)
    if (ref.ndim != 2 or ref.shape[1:] != (3,) or len(ref) not in (3, 4)
            or x.shape != ref.shape or not np.isfinite(ref).all() or not np.isfinite(x).all()):
        raise ValueError('finite three/four-node shell fit required')
    ref = ref-ref.mean(axis=0)
    x = x-x.mean(axis=0)
    n = 6*len(ref)
    # Constant reference scaling improves eigenspace conditioning without
    # introducing a displacement-dependent coefficient into differentiation.
    scale = np.linalg.norm(ref)
    if not np.isfinite(scale) or scale == 0.:
        raise ValueError('degenerate reference shell fit')
    ref = ref/scale
    c = (x/scale).T@ref
    eigenvalues, vectors = np.linalg.eigh(_davenport(c))
    gap = eigenvalues[-1]-eigenvalues[-2]
    if not gap > 1e-11*max(np.finfo(float).tiny, np.max(np.abs(eigenvalues))):
        raise ValueError('nonunique proper shell fit; refine or cut back')
    q = vectors[:, -1]
    inverse = (vectors[:, :-1]/(eigenvalues[-1]-eigenvalues[:-1]))@vectors[:, :-1].T
    derivatives = np.zeros((n, 4, 4))
    for node, r in enumerate(ref):
        for axis in range(3):
            dc = np.zeros((3, 3)); dc[axis] = r/scale
            derivatives[6*node+axis] = _davenport(dc)
    dq = np.einsum('ab,jbc,c->aj', inverse, derivatives, q)
    dl = np.einsum('a,jab,b->j', q, derivatives, q)
    reduced = derivatives-dl[:, None, None]*np.eye(4)
    rhs = np.einsum('jab,bk->ajk', reduced, dq)
    ddq = np.einsum('ab,bjk->ajk', inverse, rhs+rhs.transpose(0, 2, 1))
    ddq -= q[:, None, None]*(dq.T@dq)[None, :, :]
    w, a, b, d = [Jet2(q[i], dq[i], ddq[i]) for i in range(4)]
    return [[w*w+a*a-b*b-d*d, 2*(a*b-w*d), 2*(a*d+w*b)],
            [2*(a*b+w*d), w*w-a*a+b*b-d*d, 2*(b*d-w*a)],
            [2*(a*d-w*b), 2*(b*d+w*a), w*w-a*a-b*b+d*d]]


def deformation(reference, displacement):
    """Value, differential and Hessian of all corotated nodal coordinates."""
    ref = np.asarray(reference, dtype=float)
    u = np.asarray(displacement, dtype=float)
    if u.shape != (6*len(ref),) or not np.isfinite(u).all():
        raise ValueError('finite complete shell coordinates required')
    n = len(u)
    current = ref+u.reshape(-1, 6)[:, :3]
    rotation = rotation_jets(ref, current)
    rt = transpose(rotation)
    jets = [[Jet2.variable(u[6*i+j], 6*i+j, n) for j in range(6)] for i in range(len(ref))]
    x = [[jets[i][j]+ref[i, j] for j in range(3)] for i in range(len(ref))]
    centre = [sum(row[j] for row in x)/len(x) for j in range(3)]
    refc = ref-ref.mean(axis=0)
    values = []
    for i in range(len(ref)):
        local = matvec(rt, [x[i][j]-centre[j] for j in range(3)])
        values.extend(local[j]-refc[i, j] for j in range(3))
        values.extend(so3_log(matmul(rt, so3_exp(jets[i][3:]))))
    return (np.array([v.value for v in values]),
            np.array([v.gradient for v in values]),
            np.array([v.hessian for v in values]))


def response(model, element, displacement, origin, layers):
    """Spatial wrench rows, additive columns, and unchanged local trial state.

g=D.T f; H=D.T K D + sum(f_i Hess(d_i)). Spatial rows then follow
P.T r=g and P.T J=H-dP.T r. No post-hoc symmetrization is performed.
"""
    ref = np.array([model.mesh.nodes[i].coords() for i in element.node_ids])
    u = np.asarray(displacement, dtype=float)
    local, differential, second = deformation(ref, u)
    material = model.get_material(element.material_name)
    # This successor currently owns virgin elastic shells only. Do not imply
    # a conservative potential for active plastic/unsupported section states.
    if material.yield_stress != 0. or material.hardening_curve is not None or element.shell_section is not None:
        raise ValueError('variational shell successor requires its owned elastic section')
    f, k, candidate = element.compute_nonlinear_response(model.mesh, material,
        local, origin, layers, True)
    f, k = np.asarray(f), np.asarray(k)
    if not np.isfinite(f).all() or not np.isfinite(k).all():
        raise ValueError('nonfinite local shell response')
    if np.linalg.norm(k-k.T) > 1e-11*max(1., np.linalg.norm(k)):
        raise ValueError('nonconservative local shell tangent')
    g = differential.T@f
    h = differential.T@k@differential+np.einsum('i,ijk->jk', f, second)
    p = np.eye(len(u)); blocks = []
    for node, row in enumerate(u.reshape(-1, 6)):
        _, a, da = _exp_terms(row[3:])
        singular = np.linalg.svd(a, compute_uv=False)
        if singular[-1] <= 1e-11*max(1., singular[0]):
            raise ValueError('singular additive shell chart; owner rebase required')
        s = slice(6*node+3, 6*node+6)
        p[s, s] = a; blocks.append((s, da))
    residual = np.linalg.solve(p.T, g)
    correction = np.zeros_like(h)
    for s, da in blocks:
        correction[s, s] = np.einsum('ijk,i->jk', da, residual[s])
    tangent = np.linalg.solve(p.T, h-correction)
    return residual, tangent, candidate
