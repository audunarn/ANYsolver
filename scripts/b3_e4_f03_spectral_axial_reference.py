"""Exploratory Fourier/Legendre shell reference for the F03 axial line case.

The shell basis satisfies both supported x edges exactly and uses a natural
free y boundary. It is assembled independently of Q4/CST and E4-PL. The
beam is the existing separate classical quadratic/Hermite comparator; the
three-channel continuous-P1 line is assembled here from its virtual work.
This is a development diagnostic, not a qualified continuum target.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np
from numpy.polynomial import legendre
from scipy import sparse
from scipy.sparse.linalg import spsolve

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _b3_e4_f03_independent_beam as beam
from _b3_e4_f03_segmented_y import SegmentedYBasis
from _b3_e4_f03_segmented_x import SegmentedXBasis


E = 210e9
NU = .3
THICKNESS = .07
D = E/(1-NU**2)*np.array(((1., NU, 0.),
                         (NU, 1., 0.),
                         (0., 0., (1-NU)/2)))
OFFSETS = ((-.2, -.23), (.2, -.23), (.2, .23), (-.2, .23))
YAW_DENOMINATOR = sum(dx*dx+dy*dy for dx,dy in OFFSETS)
YAW_LENGTH = .46


def _basis(nx: int, ny: int, x: float, y: float,
           y_basis: SegmentedYBasis | None = None,
           x_basis: SegmentedXBasis | None = None) -> np.ndarray:
    if not -.5 <= x <= 1.5 or not -.5 <= y <= .5:
        raise ValueError("spectral shell sample outside panel")
    if x_basis is None:
        k=np.arange(1,nx+1,dtype=float)
        sx=np.sin(k*np.pi*(x+.5)/2)
    else:
        sx=x_basis.values(x)
        if len(sx)!=nx:
            raise ValueError("longitudinal basis size does not match shell layout")
    py=(legendre.legvander(2*y,ny-1).ravel() if y_basis is None
        else y_basis.values(y))
    if len(py)!=ny:
        raise ValueError("transverse basis size does not match shell layout")
    return np.outer(sx,py).ravel()


def shell_pose(nx: int, ny: int, s: float,
               y_basis: SegmentedYBasis | None = None,
               x_basis: SegmentedXBasis | None = None) -> np.ndarray:
    """Independent four-point translation/proper-fit yaw linearization."""
    if not 0<=s<=1:
        raise ValueError("attachment parameter outside material interval")
    m=nx*ny
    result=np.zeros((3,2*m))
    for dx,dy in OFFSETS:
        values=_basis(nx,ny,s+dx,dy,y_basis,x_basis)
        result[0,:m]+=.25*values
        result[1,m:]+=.25*values
        result[2,:m]+=-dy/YAW_DENOMINATOR*values
        result[2,m:]+=dx/YAW_DENOMINATOR*values
    return result


def shell_stiffness(nx: int, ny: int,
                    y_basis: SegmentedYBasis | None = None,
                    x_basis: SegmentedXBasis | None = None) -> np.ndarray:
    """Independent tensor-product plane-stress Galerkin stiffness."""
    x_limit=128 if x_basis is None else 160
    y_limit=64 if y_basis is None else 80
    if not 1<=nx<=x_limit or not 1<=ny<=y_limit:
        raise ValueError("bounded spectral shell order required")
    if y_basis is not None and ny!=y_basis.size:
        raise ValueError("transverse basis size does not match shell layout")
    if x_basis is None:
        roots,weights=legendre.leggauss(4*nx+20)
        x=roots+1  # physical x+0.5 on the two-metre supported interval
        k=np.arange(1,nx+1,dtype=float)[:,None]
        sx=np.sin(k*np.pi*x[None,:]/2)
        dx=k*np.pi/2*np.cos(k*np.pi*x[None,:]/2)
        x00=(sx*weights)@sx.T
        xdd=(dx*weights)@dx.T
        xd0=(dx*weights)@sx.T
    else:
        if nx!=x_basis.size:
            raise ValueError("longitudinal basis size does not match shell layout")
        x00,xdd,xd0=x_basis.matrices()
    x0d=xd0.T

    if y_basis is None:
        roots,weights=legendre.leggauss(max(2*ny+4,20))
        py=legendre.legvander(roots,ny-1).T
        dpy=np.array([2*legendre.Legendre.basis(j).deriv()(roots)
                      for j in range(ny)])
        # y=t/2, dy=dt/2; physical derivatives include factor 2.
        measure=weights/2
        y00=(py*measure)@py.T
        ydd=(dpy*measure)@dpy.T
        y0d=(py*measure)@dpy.T
    else:
        y00,ydd,y0d=y_basis.matrices()
    yd0=y0d.T

    uu=THICKNESS*(D[0,0]*np.kron(xdd,y00)+D[2,2]*np.kron(x00,ydd))
    vv=THICKNESS*(D[1,1]*np.kron(x00,ydd)+D[2,2]*np.kron(xdd,y00))
    uv=THICKNESS*(D[0,1]*np.kron(xd0,y0d)+D[2,2]*np.kron(x0d,yd0))
    return np.block([[uu,uv],[uv.T,vv]])


def coupling(nx: int, ny: int, n_beam: int, n_mortar: int,
             order: int = 12,
             y_basis: SegmentedYBasis | None = None,
             x_basis: SegmentedXBasis | None = None
             ) -> tuple[sparse.csr_matrix,sparse.csr_matrix]:
    if (not 1<=n_beam<=512 or not 1<=n_mortar<=1024
            or not 4<=order<=16):
        raise ValueError("bounded spectral line resolution required")
    rows=3*(n_mortar+1)
    cs=np.zeros((rows,2*nx*ny))
    cb=np.zeros((rows,beam.dof_count(n_beam)))
    knots=np.unique(np.r_[np.linspace(0,1,n_beam+1),
                          np.linspace(0,1,n_mortar+1),
                          [] if x_basis is None else
                          x_basis.crossing_stations(OFFSETS)])
    roots,weights=legendre.leggauss(order)
    scale=np.array((1.,1.,YAW_LENGTH))
    for left,right in zip(knots[:-1],knots[1:]):
        for root,weight in zip(roots,weights):
            s=float((left+right)/2+(right-left)*root/2)
            measure=(right-left)*weight/2
            cell=min(int(s*n_mortar),n_mortar-1)
            xi=s*n_mortar-cell
            shell_rows=scale[:,None]*shell_pose(nx,ny,s,y_basis,x_basis)
            beam_rows=scale[:,None]*beam.trace(n_beam,s).toarray()
            for index,test in ((cell,1-xi),(cell+1,xi)):
                sl=slice(3*index,3*index+3)
                cs[sl]+=measure*test*shell_rows
                cb[sl]+=measure*test*beam_rows
    return sparse.csr_matrix(cs),sparse.csr_matrix(cb)


def _shell_edge_wrench(nx: int, ny: int, q: np.ndarray,
                       side: int,
                       y_basis: SegmentedYBasis | None = None,
                       x_basis: SegmentedXBasis | None = None
                       ) -> tuple[float,float,float]:
    """Truncated-field edge stress traction about the global origin."""
    m=nx*ny
    u=q[:m].reshape(nx,ny)
    v=q[m:].reshape(nx,ny)
    if x_basis is None:
        k=np.arange(1,nx+1,dtype=float)
        edge_derivative=k*np.pi/2*(1 if side==0 else (-1.)**k)
    else:
        edge_derivative=x_basis.edge_derivatives(side)
    normal=-1. if side==0 else 1.
    if y_basis is None:
        zeroth=np.zeros(ny); zeroth[0]=1.
        first=np.zeros(ny)
        if ny>1:
            first[1]=1/6
    else:
        zeroth,first=y_basis.moments()
    fx=normal*THICKNESS*D[0,0]*float(edge_derivative@u@zeroth)
    fy=normal*THICKNESS*D[2,2]*float(edge_derivative@v@zeroth)
    x=-.5 if side==0 else 1.5
    y_fx=normal*THICKNESS*D[0,0]*float(edge_derivative@u@first)
    return fx,fy,x*fy-y_fx


def _interface_wrench(lam: np.ndarray, n_mortar: int) -> np.ndarray:
    """Integrated P1 line force and moment on the shell about the origin."""
    h=1/n_mortar
    measure=np.full(n_mortar+1,h)
    measure[[0,-1]]*=.5
    first=np.zeros(n_mortar+1)
    for cell in range(n_mortar):
        start=cell*h
        first[cell]+=h*(start/2+h/6)
        first[cell+1]+=h*(start/2+h/3)
    fx=float(measure@lam[0::3])
    fy=float(measure@lam[1::3])
    moment=float(first@lam[1::3]+YAW_LENGTH*measure@lam[2::3])
    return np.array((fx,fy,moment))


def _physical_gap(nx: int, ny: int, n_beam: int,
                  qs: np.ndarray, qb: np.ndarray,
                  y_basis: SegmentedYBasis | None = None,
                  x_basis: SegmentedXBasis | None = None
                  ) -> tuple[float,float]:
    """Quadrature L2 gap and a sampled pointwise lower bound."""
    roots,weights=legendre.leggauss(12)
    squared=0.
    maximum=0.
    scale=np.array((1.,1.,YAW_LENGTH))
    knots=np.unique(np.r_[np.linspace(0,1,n_beam+1),
                          [] if x_basis is None else
                          x_basis.crossing_stations(OFFSETS)])
    for left,right in zip(knots[:-1],knots[1:]):
        for root,weight in zip(roots,weights):
            s=float((left+right)/2+(right-left)*root/2)
            gap=scale*(beam.trace(n_beam,s)@qb
                       -shell_pose(nx,ny,s,y_basis,x_basis)@qs)
            squared+=(right-left)*weight/2*float(gap@gap)
            maximum=max(maximum,float(np.max(np.abs(gap))))
    return float(np.sqrt(max(squared,0.))),maximum


def solve(nx: int, ny: int, n_beam: int, n_mortar: int,
          y_basis: SegmentedYBasis | None = None,
          x_basis: SegmentedXBasis | None = None) -> dict:
    started=time.perf_counter()
    ks=shell_stiffness(nx,ny,y_basis,x_basis)
    kb=beam.assembled_stiffness(n_beam)
    cs,cb=coupling(nx,ny,n_beam,n_mortar,y_basis=y_basis,x_basis=x_basis)
    shell_dofs=ks.shape[0]
    k=sparse.block_diag((sparse.csr_matrix(ks),kb),format="csr")
    c=sparse.hstack((-cs,cb),format="csr")
    fbeam=beam.assembled_load(n_beam,"axial_sine")
    f=np.r_[np.zeros(shell_dofs),fbeam]
    supported=shell_dofs+beam.root_dofs(n_beam)
    free=np.setdiff1d(np.arange(k.shape[0]),supported)
    a=sparse.bmat(((k[free,:][:,free],c[:,free].T),
                   (c[:,free],None)),format="csr")
    right=np.r_[f[free],np.zeros(c.shape[0])]
    diagonal=np.ones(a.shape[0])
    scaled=a
    for _ in range(6):
        rowmax=np.asarray(abs(scaled).max(axis=1).toarray()).ravel()
        if not np.all(np.isfinite(rowmax)) or np.any(rowmax<=0):
            raise ValueError("invalid spectral mixed-system equilibration")
        step=1/np.sqrt(rowmax)
        diagonal*=step
        transform=sparse.diags(step,format="csr")
        scaled=(transform@scaled@transform).tocsr()
    solution=diagonal*spsolve(scaled.tocsc(),diagonal*right)
    if not np.all(np.isfinite(solution)):
        raise ValueError("nonfinite spectral reference response")
    q=np.zeros(k.shape[0])
    q[free]=solution[:len(free)]
    lam=solution[len(free):]
    qs=q[:shell_dofs]
    qb=q[shell_dofs:]
    residual=k@q+c.T@lam-f
    beam_root=residual[supported]
    shell_left=_shell_edge_wrench(nx,ny,qs,0,y_basis,x_basis)
    shell_right=_shell_edge_wrench(nx,ny,qs,1,y_basis,x_basis)
    interface=_interface_wrench(lam,n_mortar)
    gap_l2,gap_sampled_max=_physical_gap(nx,ny,n_beam,qs,qb,y_basis,x_basis)
    work=float(f@q)
    shell_energy=float(.5*qs@(ks@qs))
    beam_energy=float(.5*qb@(kb@qb))
    # The classical beam starts at (0,0); its root rotation is a physical Mz.
    # A truncated Galerkin field need not satisfy the strong PDE, so its
    # boundary stress traction need not close global balance at finite order.
    total=np.array(shell_left)+np.array(shell_right)+beam_root
    tip=float(qb[2*n_beam])
    stations=[]
    for station in (.25,.5,.75):
        stations.append(dict(s=station,
            shell_pose=(shell_pose(nx,ny,station,y_basis,x_basis)@qs).tolist(),
            beam_pose=(beam.trace(n_beam,station)@qb).tolist()))
    result=dict(
        status="UNREGISTERED_SPECTRAL_AXIAL_REFERENCE_DIAGNOSTIC",
        shell_modes_x=nx,shell_modes_y=ny,shell_coordinates=shell_dofs,
        beam_elements=n_beam,multiplier_intervals=n_mortar,
        kkt_dimension=a.shape[0],kkt_nnz=a.nnz,
        beam_tip_axial_m=tip,
        shell_left_stress_traction=(shell_left[0],shell_left[1],shell_left[2]),
        shell_right_stress_traction=(shell_right[0],shell_right[1],shell_right[2]),
        beam_root_wrench=beam_root.tolist(),
        interface_wrench_on_shell=interface.tolist(),
        beam_root_interface_discrepancy=(beam_root-interface).tolist(),
        truncated_stress_traction_balance=total.tolist(),
        shell_energy_j=shell_energy,beam_energy_j=beam_energy,
        external_work_j=work,
        work_relative_error=abs(shell_energy+beam_energy-.5*work)
                            /max(abs(.5*work),1e-16),
        algebraic_residual_ratio=float(np.linalg.norm(residual[free])
                /max(np.linalg.norm((k@q)[free]),
                     np.linalg.norm((c.T@lam)[free]),
                     np.linalg.norm(f[free]),1.)),
        weak_gap_l2=float(np.linalg.norm(c@q)),
        continuous_gap_l2_m=gap_l2,
        sampled_gap_component_max_m=gap_sampled_max,
        station_fields=stations,
        shell_tangent_relative_skew=float(np.linalg.norm(ks-ks.T)
                                          /np.linalg.norm(ks)),
        elapsed_seconds=time.perf_counter()-started,
        limitations=("classical planar Fourier/Legendre shell",
                     "not native E4-PL or B3-GE",
                     "finite-order edge traction may not balance",
                     "no continuum convergence claim",
                     "not formal F03 assessment"),
    )
    if y_basis is not None:
        result["transverse_basis"]="C0_THREE_INTERVAL_LOBATTO"
        result["transverse_degree"]=y_basis.degree
        result["transverse_breaks_m"]=(-.5,-.23,.23,.5)
        result["limitations"]=("classical planar Fourier/segmented-polynomial shell",
                               *result["limitations"][1:])
    if x_basis is not None:
        result["longitudinal_basis"]="C0_FIVE_INTERVAL_LOBATTO_SUPPORTED"
        result["longitudinal_degree"]=x_basis.degree
        result["longitudinal_breaks_m"]=(-.5,-.2,.2,.8,1.2,1.5)
        result["limitations"]=("classical planar segmented-polynomial shell",
                               *result["limitations"][1:])
    return result


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nx",type=int)
    parser.add_argument("--segmented-x-degree",type=int)
    parser.add_argument("--ny",type=int)
    parser.add_argument("--segmented-degree",type=int)
    parser.add_argument("--beam",type=int)
    parser.add_argument("--mortar",type=int)
    parser.add_argument("--resolution-suite",action="store_true")
    args=parser.parse_args()
    if args.resolution_suite:
        if any(value is not None for value in (args.nx,args.ny,args.beam,
                                                args.mortar,args.segmented_degree,
                                                args.segmented_x_degree)):
            parser.error("resolution suite does not take single-case options")
        cases=((24,8,128,64),(32,12,128,64),
               (48,16,128,32),(48,16,128,64),(48,16,128,128),
               (48,16,64,64),(48,16,256,64))
        output=dict(suite="UNREGISTERED_SPECTRAL_AXIAL_RESOLUTION_V1",
                    cases=[solve(*case) for case in cases])
    else:
        if any(value is None for value in (args.beam,args.mortar)):
            parser.error("beam and mortar are required")
        if (args.nx is None)==(args.segmented_x_degree is None):
            parser.error("specify exactly one of nx and segmented-x-degree")
        if (args.ny is None)==(args.segmented_degree is None):
            parser.error("specify exactly one of ny and segmented-degree")
        x_basis=(None if args.segmented_x_degree is None else
                 SegmentedXBasis(args.segmented_x_degree))
        y_basis=(None if args.segmented_degree is None else
                 SegmentedYBasis(args.segmented_degree))
        nx=args.nx if x_basis is None else x_basis.size
        ny=args.ny if y_basis is None else y_basis.size
        output=solve(nx,ny,args.beam,args.mortar,y_basis,x_basis)
    print(json.dumps(output,indent=2,sort_keys=True,allow_nan=False))


if __name__=="__main__":
    main()
