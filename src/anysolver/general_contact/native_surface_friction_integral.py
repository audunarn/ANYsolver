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


class NativeFrictionIntegrationLimit(MemoryError):
    """Resource non-success with a compact diagnostic, never softened work."""
    def __init__(self,message,diagnostics):
        super().__init__(message)
        self.integration_diagnostics=diagnostics


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


def integrate_open_event_friction_fronts(field,settings,*,maximum_axial_uncertainty):
    """Development open-endpoint pulse integration with moving axial cuts.

    This explicit helper is not an analysis-owner/restart admission. Each angular
    band needs complete stationary-branch coverage; uncertainty strips are fully
    integrated. Closed endpoint regions are excluded from this first work slice.
    """
    if not np.isfinite(maximum_axial_uncertainty) or maximum_axial_uncertainty<=0:
        raise ValueError('positive explicit axial-front uncertainty required')
    if field.patch.pairs[0].activation_policy!='transverse_event_sequence':
        raise ValueError('moving-front development requires event-sequence policy')
    return integrate_material_friction(field,settings,_front_uncertainty=maximum_axial_uncertainty)


def integrate_material_friction(field,settings,*,_front_uncertainty=None):
    """Friction-only work at the endpoint of the field's last declared segment.

    Its tangent holds earlier physical segments fixed. Partitions include contact
    fronts at every saved pose, with axial roots resolved for each angular query.
    Zero panels additionally need a conservative whole-history open certificate.
    """
    from .native_surface_support import (classify_history_panel,HistoryPanelSupport,
        history_target_ownership_certified,SupportIntervalBudget)
    if type(field) is not NativeSurfaceHistoryField or type(settings) is not NativeSurfaceFrictionIntegrationSettings:
        raise TypeError('exact material history field and integration settings required')
    support_budget=SupportIntervalBudget(settings.maximum_support_intervals)
    if not history_target_ownership_certified(field,budget=support_budget):
        raise ValueError('native friction integration requires swept whole-patch target ownership')
    poses=[field.initial]
    orientation_intervals=0
    for segment in field.segments:
        orientation_intervals+=field.patch.rule.certify_orientation_path(poses[-1],segment.translations,
            segment.angular,segment.shell_increment,maximum_intervals=field.maximum_intervals)
        poses.append(material_path_pose(poses[-1],segment.translations,segment.angular,segment.shell_increment,1.))
    for pose in poses:straight_patch_s3_gap(field.patch.rule,field.patch.target,pose)
    rule=field.patch.rule;lo,hi=rule.definition['xi_range'];alo,ahi=rule.definition['angle_range']
    reference=rule.samples[0].station.reference
    panels=[];coefficients={}

    def front_panels(cell,left,right,lower,upper):
        breaks={lower,upper}
        for offset,slope,a,b in coefficients[cell]:
            for front in _breakpoints(offset+slope*left,offset+slope*right,a,b,lower,upper):
                if lower<front<upper:
                    # Keep a floating-point guard band around a computed front.
                    # The law is unchanged and the band is integrated, not dropped.
                    # An open neighboring panel then has a resolved positive margin.
                    width=np.sqrt(np.finfo(float).eps)*max(1.,abs(front))
                    breaks.update((max(lower,front-width),min(upper,front+width)))
        angles=sorted(breaks)
        return [(cell,left,right,a,b) for a,b in zip(angles[:-1],angles[1:])]

    for cell,left,right in ((0,max(-1.,lo),min(0.,hi)),(1,max(0.,lo),min(1.,hi))):
        if right<=left:continue
        coefficients[cell]=[_coefficients(field,pose,cell) for pose in poses]
        panels.extend(front_panels(cell,left,right,alo,ahi))
    budget=NativeSurfaceReplayBudget(settings.maximum_point_paths)
    cache={};front_cache={};front_error={};front_covers={};front_axes={};visited=accepted=empty_certificates=0
    last_error=None
    open_queries=0
    size=60+60*60+4
    empty=np.zeros(size)
    gap_padding=512*np.finfo(float).eps*max(1.,rule.definition['radius'],
        *(float(np.max(np.abs(p.positions)))+float(np.max(np.abs(p.position_low)))
          +float(np.max(np.abs(field.patch.target.adapter.current_positions(p.shell_displacement))))
          for p in poses))
    rotational=np.ones(60)
    for first in (3,9,15,18,21,45,51,57):rotational[first:first+3]=1/settings.characteristic_length_m
    scale=np.concatenate((rotational/settings.force_absolute_tolerance,
        (rotational[:,None]*rotational[None,:]).ravel()/settings.tangent_absolute_tolerance,
        np.full(4,1/settings.energy_absolute_tolerance)))

    def query(xi,angle):
        nonlocal open_queries
        cell=0 if xi<0 else 1
        # Only a locally RESOLVED panel permits this shortcut. Every segment
        # was proved monotone, strictly open, or strictly closed. A closed
        # segment contradicts all-positive endpoints; in the other cases this
        # predicate proves the queried point has never contacted.
        if support.status!='resolved':
            raise RuntimeError('native friction query requires resolved local support')
        if field.patch.pairs[0].activation_policy!='transverse_event_sequence' and all(fsum((offset,slope*xi,a*cos(angle),b*sin(angle)))>gap_padding
               for offset,slope,a,b in coefficients[cell]):
            open_queries+=1
            return empty
        key=(float(xi),float(angle))
        if key not in cache:
            if len(cache)>=settings.maximum_queries or (len(cache)+1)*size*8>settings.maximum_cache_bytes:
                raise NativeFrictionIntegrationLimit('native friction material-query/cache cap exhausted',
                    dict(queries=len(cache),cache_bytes=len(cache)*size*8,point_paths=budget.point_paths,
                         panels=visited,accepted_panels=accepted,current_panel=panel,
                         previous_panel_scaled_error=last_error,support_intervals=support_budget.intervals))
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
        axial_order,angular_order=(order,order) if isinstance(order,int) else order
        result=np.zeros(size);points,weights=gauss[angular_order]
        axial_points,axial_weights=gauss[axial_order]
        measure=rule.definition['radius']*np.linalg.norm(reference.coordinates[cell+1]-reference.coordinates[cell])
        for angular,wa in zip(points,weights):
            angle=(lower+upper)/2+(upper-lower)*float(angular)/2
            roots={left,right}
            for offset,slope,a,b in coefficients[cell]:
                if slope:
                    root=-(offset+a*cos(angle)+b*sin(angle))/slope
                    if left<root<right:roots.add(root)
            edges=sorted(roots)
            if _front_uncertainty is not None:
                from .native_surface_front import stationary_front_partition
                key=(cell,float(angle))
                if key not in front_cache:
                    cuts=[];strips=[]
                    for index in range(len(field.segments)):
                        try:
                            _,_,stationary,endpoints=stationary_front_partition(field,cell,index,float(angle),
                                maximum_intervals=field.maximum_intervals,maximum_axial_uncertainty=_front_uncertainty,
                                budget=support_budget,angular_cover=front_covers[panel][index])
                        except MemoryError as error:
                            raise NativeFrictionIntegrationLimit(str(error),dict(panel=panel,panels=visited,
                                queries=len(cache),front_queries=len(front_cache),support_intervals=support_budget.intervals,
                                previous_scaled_error=last_error,axial_refinements=sum(front_axes.values()),
                                angular_refinements=len(front_axes)-sum(front_axes.values()))) from error
                        for value in (*stationary,*endpoints):
                            cuts.extend((*value.axial_interval,value.axial_coordinate))
                        strips.extend(value.axial_interval for value in stationary)
                    front_cache[key]=(tuple(cuts),tuple(strips))
                roots.update(x for x in front_cache[key][0] if left<x<right)
                edges=sorted(roots)
            for x0,x1 in zip(edges[:-1],edges[1:]):
                if _front_uncertainty is not None and any(a<=x0 and x1<=b for a,b in front_cache[key][1]):
                    # Integral enclosure replaces unresolved point evaluations;
                    # no zero point history or never-contacted claim is created.
                    continue
                for axial,wx in zip(axial_points,axial_weights):
                    xi=(x0+x1)/2+(x1-x0)*float(axial)/2
                    if not x0<xi<x1:raise ValueError('native friction axial resolution exhausted')
                    result+=query(xi,angle)*(float(wx*wa)*(x1-x0)*(upper-lower)*measure/4)
        if panel in front_error:result+=front_error[panel]
        return result

    def subdivide(parent):
        cell,left,right,lower,upper=parent
        if front_axes.get(parent,(right-left)/(hi-lo)>=(upper-lower)/(ahi-alo)):
            middle=(left+right)/2
            if middle in (left,right):raise ValueError('native friction axial panel resolution exhausted')
            return (*front_panels(cell,left,middle,lower,upper),
                    *front_panels(cell,middle,right,lower,upper))
        middle=(lower+upper)/2
        if middle in (lower,upper):raise ValueError('native friction angular panel resolution exhausted')
        return ((cell,left,right,lower,middle),(cell,left,right,middle,upper))

    unresolved_support_panels=0;support_panels_visited=0
    def subdivide_support(parent):
        # Support enclosures cover complete rectangles analytically. Pressure
        # fronts belong to quadrature partitioning, not this geometric proof;
        # inserting their guard strips here needlessly fragments child proofs.
        cell,left,right,lower,upper=parent
        if (right-left)/(hi-lo)>=(upper-lower)/(ahi-alo):
            middle=(left+right)/2
            if middle in (left,right):raise ValueError('native friction axial support resolution exhausted')
            return ((cell,left,middle,lower,upper),(cell,middle,right,lower,upper))
        middle=(lower+upper)/2
        if middle in (lower,upper):raise ValueError('native friction angular support resolution exhausted')
        return ((cell,left,right,lower,middle),(cell,left,right,middle,upper))

    def resolve_support(parent):
        # Proof subdivisions need not become quadrature panels. Complete child
        # coverage certifies their union; the parent's independent integration
        # error estimate still decides whether its quadrature must subdivide.
        nonlocal unresolved_support_panels,support_panels_visited
        if _front_uncertainty is not None:
            from .native_surface_front import stationary_front_angular_cover
            from .native_surface_support import _minimum
            cell,left,right,lower,upper=parent
            for pose in poses:
                gap,padding=_minimum(pose,field.patch.target,reference.nodal_triads[0],
                    rule.definition['radius'],cell,(left,right),(lower,upper))
                if gap<=padding:raise ValueError('moving-front work slice requires open captured endpoints')
            branch_count=0;covers=[]
            for index in range(len(field.segments)):
                cover=stationary_front_angular_cover(field,cell,index,(lower,upper),budget=support_budget)
                covers.append(cover);branch_count+=len(cover)
            front_covers[parent]=tuple(covers)
            if branch_count:
                if branch_count!=1 or len(field.segments)!=1:
                    raise ValueError('front strip work requires one certified stationary branch and segment')
                from .native_surface_front_work import open_front_strip_work_bound
                density=open_front_strip_work_bound(field,cell,_front_uncertainty)
                measure=rule.definition['radius']*np.linalg.norm(reference.coordinates[cell+1]-reference.coordinates[cell])
                error=np.zeros(size)
                error[-4:]=.5*density*_front_uncertainty*(upper-lower)*measure
                front_error[parent]=error
            # Nonzero B, no stationary H, and open endpoint rectangles exclude
            # all crossings. Stationary branches require explicit moving cuts.
            return HistoryPanelSupport('resolved' if branch_count else 'open',parent,
                'whole-angle stationary branches; explicit moving cuts')
        pending=[parent];all_open=True;last_unresolved=None
        while pending:
            if support_panels_visited>=settings.maximum_panels:
                raise MemoryError('native friction support panel cap exhausted')
            current=pending.pop();c,l,r,a,b=current;support_panels_visited+=1
            try:
                result=classify_history_panel(field,c,(l,r),(a,b),budget=support_budget)
            except MemoryError as error:
                raise NativeFrictionIntegrationLimit(str(error),dict(
                    queries=len(cache),support_intervals=support_budget.intervals,
                    support_panels_visited=support_panels_visited,support_region=current,
                    quadrature_panel=parent,last_unresolved=last_unresolved)) from error
            if result.status=='unresolved':
                unresolved_support_panels+=1
                last_unresolved=dict(region=result.region,reason=result.reason)
                pending.extend(subdivide_support(result.region))
            else:
                all_open=all_open and result.status=='open'
        return HistoryPanelSupport('open' if all_open else 'resolved',parent,'complete union of local proofs')
    total=np.zeros(size);errors=np.zeros(size)
    leaves=[]
    while panels or leaves:
        if not panels:
            # Sum absolute componentwise estimates over the complete patch.
            # Area-proportional local budgets unnecessarily over-resolve tiny
            # front panels; the public absolute error limits are global.
            total=sum((leaf[1] for leaf in leaves),np.zeros(size))
            errors=sum((leaf[2] for leaf in leaves),np.zeros(size))
            if all(leaf[3] for leaf in leaves) and np.max(scale*errors)<=1.:
                accepted+=len(leaves)
                break
            index=max(range(len(leaves)),key=lambda i:
                float(np.max(scale*leaves[i][2])) if leaves[i][3] else float('inf'))
            parent,_,_,_=leaves.pop(index)
            panels.extend(subdivide(parent))
        if visited>=settings.maximum_panels:raise MemoryError('native friction integration panel cap exhausted')
        panel=panels.pop();cell,left,right,lower,upper=panel;visited+=1
        support=resolve_support(panel)
        if support.status=='open' or field.patch.pairs[0].friction_coefficient==0:
            accepted+=1;empty_certificates+=1
            continue
        low=estimate(panel,0);high=estimate(panel,1);error=np.abs(high-low)
        if panel in front_error:error+=front_error[panel]
        if _front_uncertainty is not None:
            axial_control=estimate(panel,(0,1));angular_control=estimate(panel,(1,0))
            front_axes[panel]=float(np.max(scale*np.abs(high-axial_control)))>=float(np.max(scale*np.abs(high-angular_control)))
        last_error=float(np.max(scale*error))
        zero=not np.any(high) and not np.any(low)
        safe_zero=not zero
        if not safe_zero and support_budget.intervals>=settings.maximum_support_intervals:
            raise MemoryError('native friction aggregate support interval cap exhausted')
        leaves.append((panel,high,error,safe_zero))
    # Also covers a final refinement whose children all have exact-zero proofs.
    total=sum((leaf[1] for leaf in leaves),np.zeros(size))
    errors=sum((leaf[2] for leaf in leaves),np.zeros(size))
    return NativeSurfaceFrictionIntegral(_readonly(total[:60]),_readonly(total[60:3660].reshape(60,60)),
        *map(float,total[-4:]),dict(panels=visited,accepted_panels=accepted,unresolved_support_panels=unresolved_support_panels,support_panels_visited=support_panels_visited,queries=len(cache),
            point_paths=budget.point_paths,cache_bytes=len(cache)*size*8,zero_panels_certified=empty_certificates,
            open_material_queries_certified=open_queries,
            certified_intervals=orientation_intervals+budget.certified_intervals,
            support_intervals=support_budget.intervals,
            stationary_strip_work_error_j=sum((front_error.get(leaf[0],np.zeros(size))[-4:] for leaf in leaves),np.zeros(4)).tolist(),
            maximum_scaled_error_estimate=float(np.max(scale*errors)),estimator='GAUSS_4_8_DIFFERENCE'))
