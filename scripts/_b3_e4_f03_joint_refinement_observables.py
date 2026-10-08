"""Fixed-band and true RMS diagnostics from owned classical states."""

import math
import numpy as np

import _b3_e4_f03_area_line as line
import _b3_e4_f03_area_port as port
import _b3_e4_f03_independent_beam as beam
from _b3_e4_f03_independent_line import YAW_LENGTH

BANDS=((0.,1/32),(1/32,1/16),(15/16,31/32),(31/32,1.))


def fixed_bands(density,atoms,intervals=BANDS):
    """Integrate linear density and its linear lever arm exactly by Gauss2."""
    density=np.asarray(density,dtype=float); atoms=np.asarray(atoms,dtype=float)
    n=len(density)-1
    if (n not in (4,8,16) or density.shape!=(n+1,3) or atoms.shape!=(2,3) or
            not np.all(np.isfinite(density)) or not np.all(np.isfinite(atoms))):
        raise ValueError('invalid fixed-band physical coefficients')
    result=[]
    for a,b in intervals:
        knots=sorted({a,b,*[i/n for i in range(n+1) if a<i/n<b]})
        wrench=np.zeros(3)
        for left,right in zip(knots[:-1],knots[1:]):
            for root in (-1/math.sqrt(3),1/math.sqrt(3)):
                station=(left+right)/2+(right-left)*root/2
                cell=min(int(station*n),n-1); t=station*n-cell
                value=(1-t)*density[cell]+t*density[cell+1]
                wrench+=(right-left)/2*np.array((value[0],value[1],
                                                station*value[1]+YAW_LENGTH*value[2]))
        total=wrench.copy()
        if a==0:
            total+=atoms[0]*[1.,1.,YAW_LENGTH]
        if b==1:
            total+=atoms[1]*[1.,1.,YAW_LENGTH]+[0.,0.,atoms[1,1]]
        result.append({'interval_m':[a,b],'line_wrench':wrench.tolist(),
                       'total_wrench':total.tolist()})
    return result


def gap_metrics(model,n_beam,n_mortar,q):
    """8-point quadrature per fixed-reference overlay; interval length is1m."""
    qs=q[:model.dof_count]; qb=q[model.dof_count:]
    knots=line.overlay(model,n_beam,n_mortar,.05)
    roots,weights=np.polynomial.legendre.leggauss(8)
    gap_squared=np.zeros(3); motion_squared=np.zeros(3)
    for left,right in zip(knots[:-1],knots[1:]):
        for root,weight in zip(roots,weights):
            station=(left+right)/2+(right-left)*root/2
            pb=beam.trace(n_beam,station)@qb
            ps=port.pose(model,station,.05)@qs
            pb[2]*=YAW_LENGTH; ps[2]*=YAW_LENGTH
            measure=(right-left)*weight/2
            gap_squared+=measure*(pb-ps)**2
            motion_squared+=measure*(pb**2+ps**2)/2
    if (not np.all(np.isfinite(np.r_[gap_squared,motion_squared])) or
            np.any(gap_squared<0) or np.any(motion_squared<0)):
        raise ValueError('invalid RMS integrals')
    return {'gap_rms_m':math.sqrt(float(np.sum(gap_squared))),
            'motion_rms_m':math.sqrt(float(np.sum(motion_squared))),
            'gap_channel_rms_m':np.sqrt(gap_squared).tolist(),
            'motion_channel_rms_m':np.sqrt(motion_squared).tolist()}
