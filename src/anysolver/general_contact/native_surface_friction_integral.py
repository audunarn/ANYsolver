"""Bounded reference-area friction integration of replayed material history.

Normal work is supplied by the separate continuous normal potential. Integration
nodes have no physical history identity: every query reconstructs its own history
from the same declared path. Error estimates are developmental, not certified
quadrature bounds or acceptance of arbitrary contact histories.
"""
from dataclasses import dataclass
from math import cos,sin,fsum

import numpy as np
from numpy.polynomial.legendre import leggauss

from .native_retained_station import _readonly
from .native_surface_extrema import straight_patch_s3_gap
from .native_surface_history import NativeSurfaceHistoryField,NativeSurfaceReplayBudget
from .native_surface_normal import _breakpoints
from .native_surface_path import material_path_pose


@dataclass(frozen=True)
class NativeSurfaceFrictionIntegrationSettings:
    force_absolute_tolerance: float
    tangent_absolute_tolerance: float
    energy_absolute_tolerance: float
    characteristic_length_m: float
    maximum_panels: int=128
    maximum_queries: int=2048
    maximum_point_paths: int=8192
    maximum_support_intervals: int=128
    maximum_cache_bytes: int=67108864

    def __post_init__(self):
        for name in ('force_absolute_tolerance','tangent_absolute_tolerance','energy_absolute_tolerance',
                     'characteristic_length_m'):
            value=float(getattr(self,name))
            if not np.isfinite(value) or value<=0:raise ValueError('positive dimensional friction integration controls required')
            object.__setattr__(self,name,value)
        for name in ('maximum_panels','maximum_queries','maximum_point_paths','maximum_support_intervals','maximum_cache_bytes'):
            if type(getattr(self,name)) is not int or getattr(self,name)<1:
                raise ValueError('positive integer friction integration caps required')


@dataclass(frozen=True)
class NativeSurfaceFrictionIntegral:
    residual: np.ndarray
    tangent: np.ndarray
    stored_energy_j: float
    dissipated_increment_j: float
    released_storage_j: float
    cumulative_dissipation_j: float
    diagnostics: dict


def _coefficients(field,pose,cell):
    corners=field.patch.target.adapter.current_positions(pose.shell_displacement)
    normal=np.asarray(field.patch.target.physical_pose(pose.shell_displacement).material_frame)[:,2]
    frame=pose.cell_rotations[cell]@field.patch.rule.samples[0].station.reference.nodal_triads[0]
    radius=field.patch.rule.definition['radius']
    base=np.array([fsum((float(pose.positions[cell,i]),float(pose.position_low[cell,i]),
                        -float(corners[0,i]))) for i in range(3)])
    chord=np.array([fsum((float(pose.positions[cell+1,i]),float(pose.position_low[cell+1,i]),
                         -float(pose.positions[cell,i]),-float(pose.position_low[cell,i]))) for i in range(3)])
    # g(xi,angle) = offset + slope*xi + a*cos(angle)+b*sin(angle).
    slope=float(normal@chord)
    offset=float(normal@base)+(slope if cell==0 else 0.)
    return offset,slope,radius*float(normal@frame[:,1]),radius*float(normal@frame[:,2])


def integrate_material_friction(field,settings):
    """Friction-only work at the endpoint of the field's last declared segment.

    Its tangent holds earlier physical segments fixed. Partitions include contact
    fronts at every saved pose, with axial roots resolved for each angular query.
    Zero panels additionally need a conservative whole-history open certificate.
    """
    from .native_surface_support import panel_open_over_history,history_endpoint_support_certified,SupportIntervalBudget
    if type(field) is not NativeSurfaceHistoryField or type(settings) is not NativeSurfaceFrictionIntegrationSettings:
        raise TypeError('exact material history field and integration settings required')
    if not history_endpoint_support_certified(field):
        raise ValueError('native friction integration requires resolved historical contact envelope')
    support_budget=SupportIntervalBudget(settings.maximum_support_intervals)
    poses=[field.initial]
    for segment in field.segments:
        poses.append(material_path_pose(poses[-1],segment.translations,segment.angular,segment.shell_increment,1.))
    for pose in poses:straight_patch_s3_gap(field.patch.rule,field.patch.target,pose)
    rule=field.patch.rule;lo,hi=rule.definition['xi_range'];alo,ahi=rule.definition['angle_range']
    reference=rule.samples[0].station.reference
    panels=[];coefficients={}
    for cell,left,right in ((0,max(-1.,lo),min(0.,hi)),(1,max(0.,lo),min(1.,hi))):
        if right<=left:continue
        data=[_coefficients(field,pose,cell) for pose in poses];coefficients[cell]=data
        breaks={alo,ahi}
        for offset,slope,a,b in data:
            for front in _breakpoints(offset+slope*left,offset+slope*right,a,b,alo,ahi):
                if alo<front<ahi:
                    # Keep a floating-point guard band around a computed front.
                    # The law is unchanged and the band is integrated, not dropped.
                    # An open neighboring panel then has a resolved positive margin.
                    width=np.sqrt(np.finfo(float).eps)*max(1.,abs(front))
                    breaks.update((max(alo,front-width),min(ahi,front+width)))
        angles=sorted(breaks)
        panels.extend((cell,left,right,a,b) for a,b in zip(angles[:-1],angles[1:]))
    budget=NativeSurfaceReplayBudget(settings.maximum_point_paths)
    cache={};visited=accepted=empty_certificates=0
    size=60+60*60+4
    rotational=np.ones(60)
    for first in (3,9,15,18,21,45,51,57):rotational[first:first+3]=1/settings.characteristic_length_m
    scale=np.concatenate((rotational/settings.force_absolute_tolerance,
        (rotational[:,None]*rotational[None,:]).ravel()/settings.tangent_absolute_tolerance,
        np.full(4,1/settings.energy_absolute_tolerance)))

    def query(xi,angle):
        key=(float(xi),float(angle))
        if key not in cache:
            if len(cache)>=settings.maximum_queries or (len(cache)+1)*size*8>settings.maximum_cache_bytes:
                raise MemoryError('native friction material-query/cache cap exhausted')
            value=field.query(*key,budget=budget)
            point=value.last_contribution
            packed=np.zeros(size)
            if point is not None:
                packed[:60]=point.residual-point.normal_residual
                packed[60:3660]=(point.spatial_tangent()-point.normal_spatial_tangent()).ravel()
                trial=point.trial
                packed[-4:]=(trial.stored_energy_density,trial.dissipated_increment_density,
                    trial.released_storage_density,value.history.cumulative_dissipation_density)
            if not np.all(np.isfinite(packed)):raise ValueError('nonfinite replayed friction work')
            cache[key]=packed
        return cache[key]

    gauss=[leggauss(4),leggauss(8)]
    def estimate(panel,order):
        cell,left,right,lower,upper=panel
        result=np.zeros(size);points,weights=gauss[order]
        measure=rule.definition['radius']*np.linalg.norm(reference.coordinates[cell+1]-reference.coordinates[cell])
        for angular,wa in zip(points,weights):
            angle=(lower+upper)/2+(upper-lower)*float(angular)/2
            roots={left,right}
            for offset,slope,a,b in coefficients[cell]:
                if slope:
                    root=-(offset+a*cos(angle)+b*sin(angle))/slope
                    if left<root<right:roots.add(root)
            edges=sorted(roots)
            for x0,x1 in zip(edges[:-1],edges[1:]):
                for axial,wx in zip(points,weights):
                    xi=(x0+x1)/2+(x1-x0)*float(axial)/2
                    if not x0<xi<x1:raise ValueError('native friction axial resolution exhausted')
                    result+=query(xi,angle)*(float(wx*wa)*(x1-x0)*(upper-lower)*measure/4)
        return result

    total=np.zeros(size);errors=np.zeros(size)
    while panels:
        if visited>=settings.maximum_panels:raise MemoryError('native friction integration panel cap exhausted')
        panel=panels.pop();cell,left,right,lower,upper=panel;visited+=1
        low=estimate(panel,0);high=estimate(panel,1);error=np.abs(high-low)
        share=(right-left)*(upper-lower)/((hi-lo)*(ahi-alo))
        zero=not np.any(high) and not np.any(low)
        safe_zero=(not zero or field.patch.pairs[0].friction_coefficient==0 or
            panel_open_over_history(field,cell,(left,right),(lower,upper),
                maximum_intervals=settings.maximum_support_intervals,budget=support_budget))
        if not safe_zero and support_budget.intervals>=settings.maximum_support_intervals:
            raise MemoryError('native friction aggregate support interval cap exhausted')
        if safe_zero and np.max(scale*error)<=share:
            total+=high;errors+=error;accepted+=1;empty_certificates+=int(zero)
        else:
            if (right-left)/(hi-lo)>=(upper-lower)/(ahi-alo):
                middle=(left+right)/2
                if middle in (left,right):raise ValueError('native friction axial panel resolution exhausted')
                panels.extend(((cell,left,middle,lower,upper),(cell,middle,right,lower,upper)))
            else:
                middle=(lower+upper)/2
                if middle in (lower,upper):raise ValueError('native friction angular panel resolution exhausted')
                panels.extend(((cell,left,right,lower,middle),(cell,left,right,middle,upper)))
    return NativeSurfaceFrictionIntegral(_readonly(total[:60]),_readonly(total[60:3660].reshape(60,60)),
        *map(float,total[-4:]),dict(panels=visited,accepted_panels=accepted,queries=len(cache),
            point_paths=budget.point_paths,cache_bytes=len(cache)*size*8,zero_panels_certified=empty_certificates,
            support_intervals=support_budget.intervals,
            maximum_scaled_error_estimate=float(np.max(scale*errors)),estimator='GAUSS_4_8_DIFFERENCE'))
