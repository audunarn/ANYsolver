"""Independent classical plane-stress panel and four-sample pose for F03.

The Q4/CST mesh and operators are deliberately separate from E4-PL and
the native coupling fixture. This is a small-strain continuum comparator.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse


E = 210e9
NU = .3
THICKNESS = .07
CONSTITUTIVE = E/(1-NU**2)*np.array(((1.,NU,0.),
                                      (NU,1.,0.),
                                      (0.,0.,(1-NU)/2)))
OFFSETS = ((-.2,-.23),(.2,-.23),(.2,.23),(-.2,.23))
YAW_DENOMINATOR = sum(x*x+y*y for x,y in OFFSETS)


@dataclass(frozen=True)
class Panel:
    n_s: int
    n_y: int
    topology: str
    nodes: np.ndarray
    elements: tuple[tuple[int, ...], ...]

    @property
    def dof_count(self) -> int:
        return 2*len(self.nodes)

    @property
    def supported(self) -> np.ndarray:
        nx=2*self.n_s
        return np.array([2*(j*(nx+1)+i)+axis
                         for j in range(self.n_y+1) for i in (0,nx)
                         for axis in (0,1)],dtype=int)


def panel(n_s: int, n_y: int, topology: str) -> Panel:
    if (not isinstance(n_s,int) or not isinstance(n_y,int) or
            not 1<=n_s<=128 or not 2<=n_y<=64 or
            topology not in ('Q4','CST','CST-CB') or
            (topology=='CST-CB' and n_y%2)):
        raise ValueError('unsupported bounded classical panel definition')
    nx=2*n_s
    nodes=np.array([(-.5+i/n_s,-.5+j/n_y)
                    for j in range(n_y+1) for i in range(nx+1)],dtype=float)
    nodes.flags.writeable=False
    elements=[]
    for j in range(n_y):
        for i in range(nx):
            bl=j*(nx+1)+i
            br=bl+1
            tl=bl+nx+1
            tr=tl+1
            if topology=='Q4':
                elements.append((bl,br,tr,tl))
            elif topology=='CST-CB' and (i+j)%2:
                elements.extend(((bl,br,tl),(br,tr,tl)))
            else:
                # Fixed BL-to-TR diagonal; both triangles are CCW.
                elements.extend(((bl,br,tr),(bl,tr,tl)))
    return Panel(n_s,n_y,topology,nodes,tuple(elements))


def q4_shape(xi: float, eta: float) -> tuple[np.ndarray,np.ndarray]:
    if not np.isfinite(xi) or not np.isfinite(eta) or abs(xi)>1+1e-12 or abs(eta)>1+1e-12:
        raise ValueError('Q4 local coordinate outside host')
    n=.25*np.array(((1-xi)*(1-eta),(1+xi)*(1-eta),
                     (1+xi)*(1+eta),(1-xi)*(1+eta)))
    dn=.25*np.array(((-(1-eta),-(1-xi)),
                      (1-eta,-(1+xi)),
                      (1+eta,1+xi),
                      (-(1+eta),1-xi)))
    return n,dn


def shape(coordinates: np.ndarray, topology: str,
          at: tuple[float,float]) -> tuple[np.ndarray,np.ndarray,float]:
    """N, physical gradients, and positive Jacobian/area for one host."""
    if topology=='Q4':
        if coordinates.shape!=(4,2) or not np.all(np.isfinite(coordinates)):
            raise ValueError('Q4 host must have four finite physical nodes')
        x0,y0=np.min(coordinates,axis=0)
        x1,y1=np.max(coordinates,axis=0)
        expected=np.array(((x0,y0),(x1,y0),(x1,y1),(x0,y1)))
        if x1<=x0 or y1<=y0 or not np.allclose(coordinates,expected,rtol=0,atol=1e-12):
            raise ValueError('only regular axis-aligned Q4 hosts are admitted')
        xi=2*(at[0]-x0)/(x1-x0)-1
        eta=2*(at[1]-y0)/(y1-y0)-1
        n,dn=q4_shape(xi,eta)
        jac=coordinates.T@dn
        determinant=float(np.linalg.det(jac))
        if determinant<=0:
            raise ValueError('inverted Q4 host')
        return n,dn@np.linalg.inv(jac),determinant
    if topology not in ('CST','CST-CB'):
        raise ValueError('unknown plane-stress host')
    if coordinates.shape!=(3,2) or not np.all(np.isfinite(coordinates)):
        raise ValueError('CST host must have three finite physical nodes')
    transform=np.column_stack((np.ones(3),coordinates))
    determinant=float(np.linalg.det(transform))
    if determinant<=0:
        raise ValueError('inverted CST host')
    inverse=np.linalg.inv(transform)
    n=np.r_[1.,at]@inverse
    return n,inverse[1:,:].T,determinant/2


def strain_matrix(gradients: np.ndarray) -> np.ndarray:
    result=np.zeros((3,2*len(gradients)))
    result[0,0::2]=gradients[:,0]
    result[1,1::2]=gradients[:,1]
    result[2,0::2]=gradients[:,1]
    result[2,1::2]=gradients[:,0]
    return result


def local_stiffness(coordinates: np.ndarray, topology: str) -> np.ndarray:
    size=2*len(coordinates)
    result=np.zeros((size,size))
    if topology=='Q4':
        roots=(-1/np.sqrt(3),1/np.sqrt(3))
        x0,y0=np.min(coordinates,axis=0)
        x1,y1=np.max(coordinates,axis=0)
        for xi in roots:
            for eta in roots:
                point=(x0+(xi+1)*(x1-x0)/2,y0+(eta+1)*(y1-y0)/2)
                _,grad,jac=shape(coordinates,topology,point)
                b=strain_matrix(grad)
                result+=THICKNESS*jac*(b.T@CONSTITUTIVE@b)
    else:
        _,grad,area=shape(coordinates,topology,tuple(np.mean(coordinates,axis=0)))
        b=strain_matrix(grad)
        result+=THICKNESS*area*(b.T@CONSTITUTIVE@b)
    return (result+result.T)/2


def stiffness(model: Panel) -> sparse.csr_matrix:
    rows=[]; cols=[]; values=[]
    for element in model.elements:
        ids=np.array([2*node+axis for node in element for axis in (0,1)])
        local=local_stiffness(model.nodes[list(element)],model.topology)
        rows.extend(np.repeat(ids,len(ids)))
        cols.extend(np.tile(ids,len(ids)))
        values.extend(local.ravel())
    matrix=sparse.coo_matrix((values,(rows,cols)),shape=(model.dof_count,)*2).tocsr()
    matrix.sum_duplicates()
    return matrix


def sample(model: Panel, x: float, y: float) -> tuple[tuple[int,...],np.ndarray]:
    """Reference host interpolation, with deterministic boundary ownership."""
    if not np.isfinite(x) or not np.isfinite(y) or not -.5-1e-12<=x<=1.5+1e-12 or not -.5-1e-12<=y<=.5+1e-12:
        raise ValueError('shell sample outside panel')
    nx=2*model.n_s
    i=min(max(int(np.floor((x+.5)*model.n_s-1e-12)),0),nx-1)
    j=min(max(int(np.floor((y+.5)*model.n_y-1e-12)),0),model.n_y-1)
    bl=j*(nx+1)+i
    br=bl+1
    tl=bl+nx+1
    tr=tl+1
    if model.topology=='Q4':
        indices=(bl,br,tr,tl)
    else:
        xx=(x-model.nodes[bl,0])*model.n_s
        yy=(y-model.nodes[bl,1])*model.n_y
        if model.topology=='CST-CB' and (i+j)%2:
            indices=(bl,br,tl) if xx+yy<=1 else (br,tr,tl)
        else:
            indices=(bl,br,tr) if yy<=xx else (bl,tr,tl)
    weights,_,_=shape(model.nodes[list(indices)],model.topology,(x,y))
    if abs(float(np.sum(weights))-1)>1e-12 or np.min(weights)<-1e-10:
        raise ValueError('invalid shell sample host interpolation')
    return indices,weights


def pose(model: Panel, s: float) -> sparse.csr_matrix:
    """Physical centroid translations and centered proper-fit yaw at s."""
    if not np.isfinite(s) or not 0<=s<=1:
        raise ValueError('shell attachment parameter outside material interval')
    rows=[]; cols=[]; values=[]
    for dx,dy in OFFSETS:
        indices,weights=sample(model,s+dx,dy)
        for index,weight in zip(indices,weights):
            for row,col,value in ((0,2*index,weight/4),
                                  (1,2*index+1,weight/4),
                                  (2,2*index,-dy*weight/YAW_DENOMINATOR),
                                  (2,2*index+1,dx*weight/YAW_DENOMINATOR)):
                rows.append(row); cols.append(col); values.append(value)
    result=sparse.coo_matrix((values,(rows,cols)),shape=(3,model.dof_count)).tocsr()
    result.sum_duplicates()
    return result
