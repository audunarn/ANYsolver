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


def integrate_event_friction_fronts(field,settings,*,maximum_axial_uncertainty):
    """Development mixed endpoint integration with locally open front strips.

    One stationary branch over the complete history; closed material outside certified open
    strips contributes its full endpoint force and tangent through point replay.
    """
    if not np.isfinite(maximum_axial_uncertainty) or maximum_axial_uncertainty<=0:
        raise ValueError('positive explicit axial-front uncertainty required')
    if field.patch.pairs[0].activation_policy!='transverse_event_sequence':
        raise ValueError('moving-front development requires event-sequence policy')
    return integrate_material_friction(field,settings,_front_uncertainty=maximum_axial_uncertainty,
        _local_front_strips=True)


def integrate_variable_event_friction_fronts(field,settings,*,maximum_axial_uncertainty):
    """Explicit development route for captured-endpoint stationary transitions.

    All angular guard bands remain represented. Point replay supplies closed
    endpoint forces/tangents. A certified-open endpoint has zero R/K/storage;
    unresolved earlier strip work is retained as an integral enclosure. A
    complete-history work bound controls the spatial work error.
    This is not analysis-owner or restart admission.
    """
    if not np.isfinite(maximum_axial_uncertainty) or maximum_axial_uncertainty<=0:
        raise ValueError('positive explicit axial-front uncertainty required')
    if field.patch.pairs[0].activation_policy!='transverse_event_sequence':
        raise ValueError('moving-front development requires event-sequence policy')
    return integrate_material_friction(field,settings,_front_uncertainty=maximum_axial_uncertainty,
        _local_front_strips=True,_variable_endpoint_branches=True)


def integrate_material_friction(field,settings,*,_front_uncertainty=None,_local_front_strips=False,
        _eager_directional_controls=False,_variable_endpoint_branches=False):
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
    if _variable_endpoint_branches and (not _local_front_strips or _front_uncertainty is None):
        raise ValueError('variable endpoint branches require the explicit local-front route')
    panels=[];coefficients={};endpoint_partitions={}

    def front_panels(cell,left,right,lower,upper):
        breaks={lower,upper}
        if _variable_endpoint_branches:
            breaks.update(edge for band in endpoint_partitions[cell].bands
                for edge in band[:2] if lower<edge<upper)
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
        if _variable_endpoint_branches:
            from .native_surface_front_boundary import stationary_endpoint_angular_partition
            endpoint_partitions[cell]=stationary_endpoint_angular_partition(field,cell,(alo,ahi),budget=support_budget)
        panels.extend(front_panels(cell,left,right,alo,ahi))
    budget=NativeSurfaceReplayBudget(settings.maximum_point_paths)
    cache={};front_cache={};front_error={};front_covers={};front_axes={};front_band_cache={};front_prepared={};support_by_panel={};refinement_axes=[];visited=accepted=empty_certificates=0
    front_work_density={}
    last_error=None;last_error_components=None;global_error_components=None
    open_queries=0;open_endpoint_strip_enclosures=0
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

    def scaled_error_components(error):
        weighted=scale*error
        return dict(force=float(np.max(weighted[:60])),tangent=float(np.max(weighted[60:3660])),
            stored=float(weighted[-4]),dissipated=float(weighted[-3]),
            released=float(weighted[-2]),cumulative=float(weighted[-1]))

    def query(xi,angle):
        nonlocal open_queries
        cell=0 if xi<0 else 1
        # Only a locally RESOLVED panel permits this shortcut. Every segment
        # was proved monotone, strictly open, or strictly closed. A closed
        # segment contradicts all-positive endpoints; in the other cases this
        # predicate proves the queried point has never contacted.
        if support.status!='resolved':
            raise RuntimeError('native friction query requires resolved local support')
        if (field.patch.pairs[0].activation_policy!='transverse_event_sequence'
                and not support.event_covered
                and all(fsum((offset,slope*xi,a*cos(angle),b*sin(angle)))>gap_padding
               for offset,slope,a,b in coefficients[cell])):
            open_queries+=1
            return empty
        key=(float(xi),float(angle))
        if key not in cache:
            if len(cache)>=settings.maximum_queries or (len(cache)+1)*size*8>settings.maximum_cache_bytes:
                raise NativeFrictionIntegrationLimit('native friction material-query/cache cap exhausted',
                    dict(queries=len(cache),cache_bytes=len(cache)*size*8,point_paths=budget.point_paths,
                         panels=visited,accepted_panels=accepted,current_panel=panel,
                         previous_panel_scaled_error=last_error,support_intervals=support_budget.intervals,
                         previous_panel_error_components=last_error_components,
                         previous_global_error_components=global_error_components,
                         directional_control_panels=len(front_axes),refined_panels=len(refinement_axes)))
            try:value=field.query(*key,budget=budget)
            except (ValueError,MemoryError) as error:
                # Preserve the typed non-success while binding it to the
                # material coordinate and budgets of this candidate.
                if not hasattr(error,'integration_diagnostics'):
                    error.integration_diagnostics=dict(xi=key[0],angle=key[1],panel=panel,
                        queries=len(cache),point_paths=budget.point_paths,panels=visited,
                        support_intervals=support_budget.intervals,
                        open_endpoint_strip_enclosure_visits=open_endpoint_strip_enclosures,
                        captured_gaps=[fsum((offset,slope*xi,a*cos(angle),b*sin(angle)))
                            for offset,slope,a,b in coefficients[cell]])
                raise
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
        nonlocal open_queries,open_endpoint_strip_enclosures
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
                    cuts=[];strips=[];prepared_partitions=[]
                    for index in range(len(field.segments)):
                        try:
                            if _local_front_strips:
                                from .native_surface_front import stationary_front_partition_prepared
                                partition=stationary_front_partition_prepared(field,
                                    front_prepared[panel][index],float(angle),maximum_axial_uncertainty=_front_uncertainty)
                                _,_,stationary,endpoints=partition
                                prepared_partitions.append((front_prepared[panel][index],partition))
                            else:
                                _,_,stationary,endpoints=stationary_front_partition(field,cell,index,float(angle),
                                    maximum_intervals=field.maximum_intervals,maximum_axial_uncertainty=_front_uncertainty,
                                    budget=support_budget,angular_cover=front_covers[panel][index])
                        except MemoryError as error:
                            raise NativeFrictionIntegrationLimit(str(error),dict(panel=panel,panels=visited,
                                queries=len(cache),front_queries=len(front_cache),support_intervals=support_budget.intervals,
                                previous_scaled_error=last_error,axial_refinements=sum(front_axes.values()),
                                angular_refinements=len(front_axes)-sum(front_axes.values()))) from error
                        # Captured-pose coefficient roots already partition endpoint
                        # transitions. Do not add nearly coincident interval edges:
                        # that manufactures unresolved-gap micro-panels. The full
                        # domain remains covered, with the existing adaptive rule.
                        # Stationary strips alone receive enclosure work accounting.
                        for value in (stationary if _local_front_strips else (*stationary,*endpoints)):
                            cuts.extend(value.axial_interval)
                            # The interval already contains the stationary front.
                            # A second nominal cut within that work-controlled
                            # strip can duplicate the actual captured-pose front
                            # to adjacent binary64 coordinates. Captured fronts
                            # still partition endpoint R/K; the strip is intact.
                            if not _variable_endpoint_branches:
                                cuts.append(value.axial_coordinate)
                        strips.extend(value.axial_interval for value in stationary)
                    front_cache[key]=(tuple(cuts),tuple(strips),tuple(prepared_partitions))
                roots.update(x for x in front_cache[key][0] if left<x<right)
                edges=sorted(roots)
            for x0,x1 in zip(edges[:-1],edges[1:]):
                if _local_front_strips:
                    from .native_surface_front import prepared_front_open_interval
                    if all(prepared_front_open_interval(prepared,partition,x0,x1)
                           for prepared,partition in front_cache[key][2]):
                        open_queries+=len(axial_points)
                        continue
                in_strip=_front_uncertainty is not None and any(a<=x0 and x1<=b for a,b in front_cache[key][1])
                if in_strip and not _variable_endpoint_branches:
                    # Integral enclosure replaces unresolved point evaluations;
                    # no zero point history or never-contacted claim is created.
                    continue
                if in_strip and _variable_endpoint_branches:
                    offset,slope,a,b=coefficients[cell][-1]
                    final_lower=min(fsum((offset,slope*x,a*cos(angle),b*sin(angle))) for x in (x0,x1))
                    if final_lower>gap_padding:
                        # A strictly open final surface has exactly zero endpoint
                        # R/K/storage, independently of any earlier tiny pulse.
                        # Its history work remains an interval enclosure, never
                        # a reset/zero point state. Positive spatial quadrature of
                        # this midpoint is bounded by the same full strip error.
                        midpoint=np.zeros(size);midpoint[-3:]=.5*front_work_density[panel][-3:]
                        result+=midpoint*((x1-x0)*float(wa)*(upper-lower)*measure/2)
                        open_endpoint_strip_enclosures+=1
                        continue
                for axial,wx in zip(axial_points,axial_weights):
                    xi=(x0+x1)/2+(x1-x0)*float(axial)/2
                    if not x0<xi<x1:
                        error=ValueError('native friction axial resolution exhausted')
                        error.integration_diagnostics=dict(panel=panel,angle=angle,interval=(x0,x1),
                            xi=xi,queries=len(cache),point_paths=budget.point_paths,
                            panels=visited,support_intervals=support_budget.intervals)
                        raise error
                    point=query(xi,angle)
                    if in_strip and _variable_endpoint_branches:
                        density=front_work_density[panel]
                        if np.any(point[-4:]<0) or np.any(point[-4:]>density):
                            raise ValueError('replayed strip work exceeds complete-history density bound')
                    result+=point*(float(wx*wa)*(x1-x0)*(upper-lower)*measure/4)
        if panel in front_error and not _variable_endpoint_branches:result+=front_error[panel]
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

    def directional_controls(parent,high):
        # These estimates select an axis; they do not enter the accepted
        # high/low integral or its error. Local-front candidates can therefore
        # defer them until this parent actually needs refinement. The eager
        # switch is retained solely as a bounded parity oracle.
        axial_control=estimate(parent,(0,1));angular_control=estimate(parent,(1,0))
        front_axes[parent]=float(np.max(scale*np.abs(high-axial_control)))>=float(np.max(scale*np.abs(high-angular_control)))

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
            all_endpoints_open=True
            for pose in poses:
                gap,padding=_minimum(pose,field.patch.target,reference.nodal_triads[0],
                    rule.definition['radius'],cell,(left,right),(lower,upper))
                all_endpoints_open=all_endpoints_open and gap>padding
            if not _local_front_strips and not all_endpoints_open:
                raise ValueError('moving-front work slice requires open captured endpoints')
            # Angular proof geometry is independent of an axial child panel.
            # Reuse only identical bands within this immutable field evaluation.
            band=(cell,lower,upper)
            if _local_front_strips and band in front_band_cache:
                covers,envelopes,prepared=front_band_cache[band]
            else:
                domain=(max(rule.definition['xi_range'][0],cell-1),min(rule.definition['xi_range'][1],cell))
                covers=tuple(stationary_front_angular_cover(field,cell,index,(lower,upper),budget=support_budget,
                    xi_bounds=domain if _local_front_strips else None,
                    endpoint_partition=endpoint_partitions.get(cell),
                    _variable_endpoint_branches=_variable_endpoint_branches)
                    for index in range(len(field.segments)))
                envelopes=None
                if _local_front_strips:
                    from .native_surface_front import prepare_stationary_band
                    prepared=tuple(prepare_stationary_band(field,cover,budget=support_budget) for cover in covers)
                else:prepared=()
            front_prepared[parent]=prepared
            branch_count=sum(map(len,covers))
            front_covers[parent]=covers
            if branch_count:
                if branch_count!=1 or (not _local_front_strips and len(field.segments)!=1):
                    raise ValueError('front strip work requires one certified stationary branch; legacy helper requires one segment')
                owner_index=next(index for index,cover in enumerate(covers) if len(cover))
                if _variable_endpoint_branches:
                    from .native_surface_front import stationary_front_angular_envelopes
                    from .native_surface_front_work import history_front_strip_work_bound
                    if envelopes is None:
                        envelopes=tuple(stationary_front_angular_envelopes(field,cover,
                            maximum_axial_uncertainty=_front_uncertainty,budget=support_budget,
                            prepared=item,_include_endpoints=True) for cover,item in zip(covers,prepared))
                    front_band_cache[band]=(covers,envelopes,prepared)
                    density=np.zeros(4)
                    for a,b in envelopes[owner_index][:len(covers[owner_index])]:
                        a,b=max(left,a),min(right,b)
                        if a<b:
                            density=np.maximum(density,history_front_strip_work_bound(field,cell,(a,b),prepared,envelopes))
                    front_work_density[parent]=density
                    measure=rule.definition['radius']*np.linalg.norm(reference.coordinates[cell+1]-reference.coordinates[cell])
                    error=np.zeros(size)
                    error[-4:]=density*_front_uncertainty*(upper-lower)*measure
                    front_error[parent]=error
                    return HistoryPanelSupport('resolved',parent,'variable stationary branches; closed endpoint replay and open endpoint/work enclosure')
                if _local_front_strips:
                    from .native_surface_front import stationary_front_angular_envelopes
                    if envelopes is None:
                        envelopes=stationary_front_angular_envelopes(field,covers[owner_index],
                            maximum_axial_uncertainty=_front_uncertainty,budget=support_budget,
                            prepared=prepared[owner_index])
                    front_band_cache[band]=(covers,envelopes,prepared)
                    for a,b in envelopes:
                        a,b=max(left,a),min(right,b)
                        if a>=b:continue
                        for pose in poses:
                            gap,padding=_minimum(pose,field.patch.target,reference.nodal_triads[0],
                                rule.definition['radius'],cell,(a,b),(lower,upper))
                            if gap<=padding:
                                raise ValueError('stationary uncertainty strip has unresolved or closed captured endpoint')
                from .native_surface_front_work import open_front_strip_work_bound
                density=open_front_strip_work_bound(field,cell,_front_uncertainty,
                    segment_index=owner_index if _local_front_strips else None)
                if _local_front_strips and owner_index<len(field.segments)-1:
                    # Every other segment is proved open on this strip. Its
                    # earlier pulse contributes cumulative work, but cannot
                    # generate final-segment dissipation or storage release.
                    density[1:3]=0.
                measure=rule.definition['radius']*np.linalg.norm(reference.coordinates[cell+1]-reference.coordinates[cell])
                error=np.zeros(size)
                error[-4:]=.5*density*_front_uncertainty*(upper-lower)*measure
                front_error[parent]=error
            if _local_front_strips and not branch_count:
                front_band_cache[band]=(covers,(),prepared)
            # Nonzero B, no stationary H, and open endpoint rectangles exclude
            # all crossings. Stationary branches require explicit moving cuts.
            return HistoryPanelSupport('open' if not branch_count and all_endpoints_open else 'resolved',parent,
                'whole-angle stationary branches; explicit moving cuts')
        pending=[parent];all_open=True;last_unresolved=None;event_covered=False
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
                event_covered=event_covered or result.event_covered
        return HistoryPanelSupport('open' if all_open else 'resolved',parent,
            'complete union of local proofs',event_covered)
    total=np.zeros(size);errors=np.zeros(size)
    leaves=[]
    while panels or leaves:
        if not panels:
            # Sum absolute componentwise estimates over the complete patch.
            # Area-proportional local budgets unnecessarily over-resolve tiny
            # front panels; the public absolute error limits are global.
            total=sum((leaf[1] for leaf in leaves),np.zeros(size))
            errors=sum((leaf[2] for leaf in leaves),np.zeros(size))
            global_error_components=scaled_error_components(errors)
            if all(leaf[3] for leaf in leaves) and np.max(scale*errors)<=1.:
                accepted+=len(leaves)
                break
            index=max(range(len(leaves)),key=lambda i:
                float(np.max(scale*leaves[i][2])) if leaves[i][3] else float('inf'))
            parent,parent_high,_,_=leaves.pop(index)
            if _local_front_strips and not _eager_directional_controls:
                # query() reads this outer context, including when estimate()
                # uses a previously visited leaf. Reuse its proof and budgets.
                panel=parent;support=support_by_panel[parent]
                directional_controls(parent,parent_high)
            if parent in front_axes:refinement_axes.append((parent,front_axes[parent]))
            panels.extend(subdivide(parent))
        if visited>=settings.maximum_panels:raise MemoryError('native friction integration panel cap exhausted')
        panel=panels.pop();cell,left,right,lower,upper=panel;visited+=1
        try:
            support=resolve_support(panel)
        except (ValueError,MemoryError) as error:
            # Retain the original typed failure and add bounded context at
            # the decision point; this neither retries nor admits the panel.
            if not hasattr(error,'integration_diagnostics'):
                error.integration_diagnostics=dict(stage='support',current_panel=panel,
                    panels=visited,queries=len(cache),point_paths=budget.point_paths,
                    support_intervals=support_budget.intervals,
                    cached_angular_front_bands=len(front_band_cache),
                    previous_panel_error_components=last_error_components,
                    previous_global_error_components=global_error_components)
            raise
        if _local_front_strips:support_by_panel[panel]=support
        if support.status=='open' or field.patch.pairs[0].friction_coefficient==0:
            accepted+=1;empty_certificates+=1
            continue
        low=estimate(panel,0);high=estimate(panel,1);error=np.abs(high-low)
        if panel in front_error:error+=front_error[panel]
        if _front_uncertainty is not None and (not _local_front_strips or _eager_directional_controls):
            directional_controls(panel,high)
        last_error=float(np.max(scale*error))
        last_error_components=scaled_error_components(error)
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
            open_endpoint_strip_enclosures=open_endpoint_strip_enclosures,
            front_profile='VARIABLE_ENDPOINT_STRIP_DEV_V1' if _variable_endpoint_branches else 'LEGACY_FRONT_OR_PANEL_DEV',
            certified_intervals=orientation_intervals+budget.certified_intervals,
            support_intervals=support_budget.intervals,
            cached_angular_front_bands=len(front_band_cache),
            directional_control_panels=len(front_axes),refinement_axes=refinement_axes,
            stationary_strip_work_error_j=sum((front_error.get(leaf[0],np.zeros(size))[-4:] for leaf in leaves),np.zeros(4)).tolist(),
            maximum_scaled_error_estimate=float(np.max(scale*errors)),estimator='GAUSS_4_8_DIFFERENCE'))
