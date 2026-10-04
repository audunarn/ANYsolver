"""Curved native material normal work against a fixed plane.

Local open/fully compressed development kernel, not an analysis owner. Actual material reference area
and retained work maps are preserved. Gauss8/16 tensor differences control
energy, force and spatial tangent under existing dimensioned settings. They
are error estimates, not rigorous integration error certificates.
"""
from dataclasses import asdict,dataclass
from fractions import Fraction
from math import cos,sin,fsum,isfinite
import numpy as np
from numpy.polynomial.legendre import leggauss

from anysolver._ge_beam3_mixed_ad import Jet2
from anysolver._ge_beam3_generalized_static_boundary import spatial_jacobian
from anysolver._ge_beam3_p5_seeded.core import sha
from .native_retained_station import NativeRetainedRoundStation,_readonly
from .native_surface_quadrature import NativeRoundSurfaceRule,surface_geometry
from .native_surface_normal import StraightNormalIntegrationSettings
from .native_curved_geometry import curved_patch_geometry_control

PROFILE='NATIVE_RETAINED_CURVED_MATERIAL_PLANE_LOCAL_WORK_DEV_V1'


def _projected_gap(high, low, cell, t, arm, origin, normal):
    """Project exact binary products before converting to one scalar value.

    Shape weights form an exact partition of unity in this scalar projection.
    A tangential change of plane origin cannot lose coordinate differences.
    """
    F=lambda v:Fraction(float(v))
    weight=F(t)
    value=sum(((1-weight)*(F(high[cell,i])+F(low[cell,i])-F(origin[i]))+
               weight*(F(high[cell+1,i])+F(low[cell+1,i])-F(origin[i]))+
               F(arm[i]))*F(normal[i]) for i in range(3))
    try:result=float(value)
    except (OverflowError,ValueError) as exc:
        raise ValueError('curved material scalar projection unresolved') from exc
    if not isfinite(result) or (value!=0 and result==0):
        raise ValueError('curved material scalar projection unresolved')
    return result


@dataclass(frozen=True)
class CurvedMaterialPlaneResult:
    normal_storage_j: float
    residual: np.ndarray
    tangent: np.ndarray
    source_force: np.ndarray
    target_force: np.ndarray
    source_moment: np.ndarray
    target_moment: np.ndarray
    geometry: object
    intervals: int
    accepted_intervals: int
    integrand_evaluations: int
    estimated_errors: tuple

    def spatial_tangent(self):
        return self.tangent


class NativeCurvedMaterialPlaneWork:
    """Fixed-plane local kernel; no solve/restart/history or generic insertion."""
    def __init__(self,rule,*,plane_origin_m,plane_normal,normal_stiffness_Pa_per_m,
                 integration_settings):
        if type(rule) is not NativeRoundSurfaceRule or type(integration_settings) is not StraightNormalIntegrationSettings:
            raise TypeError('exact material surface rule and existing normal integration settings required')
        origin=np.asarray(plane_origin_m,dtype=float);normal=np.asarray(plane_normal,dtype=float)
        if (origin.shape!=(3,) or normal.shape!=(3,) or not np.all(np.isfinite(origin))
            or not np.all(np.isfinite(normal)) or abs(np.linalg.norm(normal)-1.)>1e-12):
            raise ValueError('finite plane origin and unit normal required')
        if isinstance(normal_stiffness_Pa_per_m,(bool,np.bool_)):
            raise ValueError('dimensioned curved normal stiffness must not be boolean')
        stiffness=float(normal_stiffness_Pa_per_m)
        if not isfinite(stiffness) or stiffness<=0:
            raise ValueError('positive dimensioned curved normal stiffness required')
        self.rule=rule;self.reference=rule.samples[0].station.reference
        self.origin=_readonly(origin);self.normal=_readonly(normal)
        self.stiffness=stiffness;self.settings=integration_settings
        self.identity=sha(self.definition())
        self.reference_geometry=curved_patch_geometry_control(rule,self.reference.coordinates,
            np.zeros((3,3)),np.tile(np.eye(3),(2,1,1)),origin,normal)

    def definition(self):
        return dict(profile=PROFILE,rule=self.rule.definition,
            origin_m=self.origin,normal=self.normal,
            stiffness_N_per_m3=self.stiffness,settings=asdict(self.settings),
            reference=self.reference.canonical_data(),measure='actual_fixed_reference_material_area',
            branch_admission='continuous_whole_patch_open_or_fully_compressed',
            numerical='GAUSS_8_16_TENSOR_EXACT_BINARY_PROJECTION_JET2_SPATIAL_ONCE_V2')

    def evaluate(self,positions,position_low,cell_rotations):
        if sha(self.definition())!=self.identity:
            raise ValueError('curved material plane definition/settings changed')
        geometry=curved_patch_geometry_control(self.rule,positions,position_low,
            cell_rotations,self.origin,self.normal)
        # No sampled quadrature may silently miss a thin active region.
        # Mixed/contact-front poses require future curved segmentation.
        if geometry.gap_lower_m<0<=geometry.gap_upper_m:
            raise ValueError('curved material mixed-contact segmentation unresolved')
        high=np.asarray(positions);low=np.asarray(position_low);U=np.asarray(cell_rotations)
        settings=self.settings;radius=float(self.rule.definition['radius'])
        lo,hi=self.rule.definition['xi_range'];alo,ahi=self.rule.definition['angle_range']
        total_area=(hi-lo)*(ahi-alo)
        limits=(settings.energy_absolute_tolerance,settings.force_absolute_tolerance,
                settings.tangent_absolute_tolerance)
        gauss=(leggauss(8),leggauss(16))
        global_residual=np.zeros(42);global_hessian=np.zeros((42,42))
        energies=[];errors=[];visited=accepted=evaluations=0
        last_error=last_rectangle=None
        scale=np.ones(42)
        for index in (3,9,15,18,21):
            scale[index:index+3]=1/settings.characteristic_length_m
        for cell,left,right in ((0,max(lo,-1.),min(hi,0.)),(1,max(lo,0.),min(hi,1.))):
            if right<=left:continue
            mapping=np.zeros((9,42))
            mapping[:3,6*cell:6*cell+3]=np.eye(3)
            mapping[3:6,6*(cell+1):6*(cell+1)+3]=np.eye(3)
            mapping[6:9,18+3*cell:21+3*cell]=np.eye(3)
            pending=[(left,right,alo,ahi)]
            while pending:
                if visited>=settings.max_intervals:
                    failure=MemoryError('curved normal integration interval budget exhausted')
                    failure.integration_diagnostics=dict(visited=visited,accepted=accepted,
                        evaluations=evaluations,last_errors=last_error,last_rectangle=last_rectangle)
                    raise failure
                xl,xr,al,ar=pending.pop();visited+=1
                xm=(xl+xr)/2;am=(al+ar)/2;dx=(xr-xl)/2;da=(ar-al)/2
                if xm in (xl,xr) or am in (al,ar) or dx==0 or da==0:
                    raise ValueError('curved normal integration parameter resolution exhausted')
                estimates=[]
                for points,weights in gauss:
                    estimate=Jet2.constant(0.,9)
                    for qx,wx in zip(points,weights):
                        xi=float(xm+dx*qx)
                        if not xl<xi<xr:
                            raise ValueError('curved normal integration axial station unresolved')
                        t=xi+1 if cell==0 else xi
                        frame=self.reference.frame(xi)
                        lift=self.reference.half_cell_lift(cell,t)
                        for qa,wa in zip(points,weights):
                            angle=float(am+da*qa)
                            if not al<angle<ar:
                                raise ValueError('curved normal integration angular station unresolved')
                            factor=float(dx*da*wx*wa)
                            if not isfinite(factor) or factor==0:
                                raise ValueError('curved normal integration quadrature measure unresolved')
                            radial=radius*(cos(angle)*frame[:,1]+sin(angle)*frame[:,2])
                            arm=U[cell]@(lift+radial)
                            gap=_projected_gap(high,low,cell,t,arm,self.origin,self.normal)
                            evaluations+=1
                            if gap<0 and geometry.gap_lower_m>=0:
                                raise ValueError('curved material gap disagrees with open enclosure')
                            if gap>=0:
                                if geometry.gap_upper_m<0:
                                    raise ValueError('curved material gap disagrees with compressed enclosure')
                                continue
                            gradient=np.r_[(1-t)*self.normal,t*self.normal,np.cross(arm,self.normal)]
                            hessian=np.zeros((9,9))
                            hessian[6:9,6:9]=(np.outer(arm,self.normal)+np.outer(self.normal,arm))/2-float(self.normal@arm)*np.eye(3)
                            value=Jet2(gap,gradient,hessian)
                            station=NativeRetainedRoundStation(self.rule.samples[0].station.element_id,
                                self.reference,xi,radius,angle)
                            area=surface_geometry(station,self.reference.coordinates,np.zeros((3,3)),
                                np.tile(np.eye(3),(2,1,1))).area_jacobian
                            coefficient=factor*area*.5*self.stiffness
                            if not isfinite(coefficient) or coefficient==0:
                                raise ValueError('curved normal integration reference measure/stiffness unresolved')
                            estimate=estimate+coefficient*value*value
                    estimates.append(estimate)
                difference=estimates[1]-estimates[0]
                residual=mapping.T@difference.gradient
                tangent=spatial_jacobian(residual,mapping.T@difference.hessian@mapping)
                error=np.array((abs(difference.value),np.linalg.norm(scale*residual,np.inf),
                    np.linalg.norm(scale[:,None]*tangent*scale[None,:],np.inf)))
                if not np.all(np.isfinite(error)):
                    raise ValueError('nonfinite curved normal integration error estimate')
                last_error=tuple(map(float,error));last_rectangle=(xl,xr,al,ar)
                budget=np.asarray(limits)*(xr-xl)*(ar-al)/total_area
                if np.all(error<=budget):
                    integral=estimates[1];accepted+=1;errors.append(tuple(map(float,error)))
                    energies.append(integral.value)
                    global_residual+=mapping.T@integral.gradient
                    global_hessian+=mapping.T@integral.hessian@mapping
                else:
                    if (xr-xl)/(hi-lo)>=(ar-al)/(ahi-alo):
                        pending.extend(((xl,xm,al,ar),(xm,xr,al,ar)))
                    else:
                        pending.extend(((xl,xr,al,am),(xl,xr,am,ar)))
        tangent=spatial_jacobian(global_residual,global_hessian)
        energy=fsum(energies)
        if not isfinite(energy) or not np.all(np.isfinite(global_residual)) or not np.all(np.isfinite(tangent)):
            raise ValueError('nonfinite curved normal work')
        forces=-global_residual[:18].reshape(3,6)[:,:3]
        force=forces.sum(axis=0)
        moment=sum((np.cross(high[i],forces[i])+np.cross(low[i],forces[i]) for i in range(3)),start=np.zeros(3))
        moment-=global_residual[18:24].reshape(2,3).sum(axis=0)
        return CurvedMaterialPlaneResult(energy,_readonly(global_residual),_readonly(tangent),
            _readonly(force),_readonly(-force),_readonly(moment),_readonly(-moment),geometry,
            visited,accepted,evaluations,tuple(fsum(e[i] for e in errors) for i in range(3)))
