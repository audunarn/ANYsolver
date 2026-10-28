"""Physical rigid mass attached to a six-DOF node; all quantities in model axes/SI."""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class ConcentratedMass:
    mass: float
    offset: tuple = (0., 0., 0.)
    inertia_cg: tuple = ((0.,0.,0.),(0.,0.,0.),(0.,0.,0.))

    def __post_init__(self):
        m = float(self.mass)
        r = np.asarray(self.offset, dtype=float)
        J = np.asarray(self.inertia_cg, dtype=float)
        if not np.isfinite(m) or m < 0 or r.shape != (3,) or not np.all(np.isfinite(r)):
            raise ValueError('concentrated mass and offset must be finite; mass must be nonnegative')
        if J.shape != (3,3) or not np.all(np.isfinite(J)) or not np.array_equal(J,J.T):
            raise ValueError('inertia_cg must be a finite symmetric 3x3 tensor')
        e = np.linalg.eigvalsh(J)
        tol = 1e-12 * max(float(np.max(np.abs(e))), np.finfo(float).tiny)
        if e[0] < -tol or e[2] > e[0]+e[1]+tol or (m == 0 and np.any(J)):
            raise ValueError('inertia must be physical: nonnegative principal moments, triangle inequalities, positive mass')
        object.__setattr__(self,'mass',m)
        object.__setattr__(self,'offset',tuple(float(v) for v in r))
        object.__setattr__(self,'inertia_cg',tuple(tuple(float(v) for v in row) for row in J))

    def matrix(self):
        x,y,z=self.offset
        S=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
        B=np.eye(6); B[:3,3:]=-S
        D=np.zeros((6,6)); D[:3,:3]=self.mass*np.eye(3); D[3:,3:]=self.inertia_cg
        return B.T@D@B


def entries(mesh):
    for node_id, values in sorted(getattr(mesh,'concentrated_masses',{}).items()):
        node=mesh.get_node(int(node_id))
        if node is None or len(node.dofs)!=6:
            raise ValueError('concentrated mass requires an existing six-DOF attachment node')
        for value in values:
            if not isinstance(value,ConcentratedMass):
                raise ValueError('concentrated_masses must contain ConcentratedMass records')
            # Revalidate even objects restored through transports bypassing constructors.
            checked=ConcentratedMass(value.mass,value.offset,value.inertia_cg)
            yield node,checked


def identity(mesh):
    return tuple((int(n.id),v.mass,v.offset,v.inertia_cg) for n,v in entries(mesh))


def add_to_matrix(mesh, matrix):
    from scipy import sparse
    rows=[]; cols=[]; data=[]
    for node,value in entries(mesh):
        block=value.matrix()
        rows.extend(np.repeat(node.dofs,6)); cols.extend(np.tile(node.dofs,6)); data.extend(block.ravel())
    if not data: return matrix
    return (matrix+sparse.coo_matrix((data,(rows,cols)),shape=matrix.shape)).tocsr()
