"""Fixed native round material patch on one owned S3 target facet.

Shares point laws, structural assembly and transaction replay. No target-boundary
clipping or history transfer is implied by a fixed material quadrature rule.
"""
from dataclasses import dataclass,asdict

import numpy as np

from anysolver._ge_beam3_p5_seeded.core import sha
from .friction_point import initial_friction_point
from .native_retained_station import _readonly
from .native_surface_quadrature import NativeRoundSurfaceRule
from .native_surface_s3_friction import NativeS3MaterialPointFriction, NativeS3MaterialPathResult


@dataclass(frozen=True)
class NativeSurfacePatchHistory:
    definition_sha256: str
    points: tuple


@dataclass(frozen=True)
class NativeSurfacePatchTrial:
    candidate_state: NativeSurfacePatchHistory


@dataclass(frozen=True)
class NativeSurfacePatchResult:
    residual: np.ndarray
    tangent: np.ndarray
    trial: NativeSurfacePatchTrial
    normal_gap_m: float
    normal_storage_j: float
    points: tuple
    continuous_gap: object=None
    normal_integration_diagnostics: object=None

    def spatial_tangent(self):
        return self.tangent


class NativeS3MaterialSurfacePatch:
    """One fixed reference-area rule with independent point histories."""
    def __init__(self, rule, targets, *, normal_stiffness_Pa_per_m,
                 friction_coefficient, tangential_stiffness_Pa_per_m,
                 activation_policy='reject',event_history_substeps=32,gap_check='sampled',
                 normal_integration='point',normal_integration_settings=None):
        if type(rule) is not NativeRoundSurfaceRule:
            raise TypeError('exact native reference surface rule required')
        if gap_check not in ('sampled','straight_patch'):
            raise ValueError('explicit supported patch gap check required')
        self.gap_check=gap_check
        if normal_integration not in ('point','straight_segmented'):
            raise ValueError('explicit supported native normal integration required')
        if normal_integration=='straight_segmented':
            from .native_surface_normal import StraightNormalIntegrationSettings
            if type(normal_integration_settings) is not StraightNormalIntegrationSettings or gap_check!='straight_patch':
                raise ValueError('segmented normal integration requires explicit settings and continuous straight gap check')
        elif normal_integration_settings is not None:
            raise ValueError('normal integration settings supplied for point integration')
        self.normal_integration=normal_integration
        self.normal_integration_settings=normal_integration_settings
        targets=tuple(targets)
        if len(targets)!=len(rule.samples):
            raise ValueError('one explicit material target required per surface sample')
        pairs=tuple(NativeS3MaterialPointFriction(sample.station,target,
            reference_weight_m2=sample.reference_weight_m2,
            normal_stiffness_Pa_per_m=normal_stiffness_Pa_per_m,
            friction_coefficient=friction_coefficient,
            tangential_stiffness_Pa_per_m=tangential_stiffness_Pa_per_m,
            activation_policy=activation_policy,event_history_substeps=event_history_substeps)
            for sample,target in zip(rule.samples,targets))
        # This owner has one S3 domain. Require one exact prepared adapter;
        # material target coordinates can vary at every quadrature point.
        adapter=pairs[0].target.adapter
        if any(pair.target.adapter is not adapter for pair in pairs):
            raise ValueError('native material patch requires one prepared target adapter')
        self.rule,self.pairs=rule,pairs
        self.source,self.target=pairs[0].source,pairs[0].target
        self.definition_sha256=sha(self._definition())

    def _definition(self):
        result=dict(profile='NATIVE_S3_FIXED_MATERIAL_PATCH_DEV_V1',
                    rule=self.rule.identity,rule_definition=self.rule.definition,
                    points=[pair._definition() for pair in self.pairs])
        if self.gap_check!='sampled':result['gap_check']=self.gap_check
        if self.normal_integration!='point':
            result['normal_integration']=self.normal_integration
            result['normal_integration_settings']=asdict(self.normal_integration_settings)
        return result

    def initial_history(self,shell_displacement):
        return NativeSurfacePatchHistory(self.definition_sha256,tuple(
            initial_friction_point(pair.target.physical_pose(shell_displacement).material_frame)
            for pair in self.pairs))

    def evaluate_path(self,committed,history,translations,angular,shell_increment,*,maximum_intervals=256):
        if sha(self._definition())!=self.definition_sha256:
            raise ValueError('native surface patch definition changed')
        if (type(history) is not NativeSurfacePatchHistory or
                history.definition_sha256!=self.definition_sha256 or len(history.points)!=len(self.pairs)):
            raise ValueError('native surface patch history binding')
        # Guard the material rule and all current surface orientations, then
        # evaluate every point from the same committed physical origin.
        self.rule.evaluate(committed.positions,committed.position_low,committed.cell_rotations)
        orientation_intervals=self.rule.certify_orientation_path(committed,translations,angular,
            shell_increment,maximum_intervals=maximum_intervals)
        values=tuple(pair.evaluate_path(committed,state,translations,angular,shell_increment,
                        maximum_intervals=maximum_intervals)
                     for pair,state in zip(self.pairs,history.points))
        current=values[0].configuration
        self.rule.evaluate(current.positions,current.position_low,current.cell_rotations)
        points=tuple(value.contribution for value in values)
        continuous=None; gap=min(p.normal_gap_m for p in points)
        if self.gap_check=='straight_patch':
            from .native_surface_extrema import straight_patch_s3_gap
            continuous=straight_patch_s3_gap(self.rule,self.target,current)
            gap=min(gap,continuous.lower_bound)
        residual=sum((p.residual for p in points),np.zeros_like(points[0].residual))
        tangent=sum((p.spatial_tangent() for p in points),np.zeros_like(points[0].spatial_tangent()))
        storage=sum(p.normal_storage_j for p in points); diagnostics=None
        if self.normal_integration=='straight_segmented':
            from .native_surface_normal import integrate_straight_normal
            normal=integrate_straight_normal(self.rule,self.target,current,
                self.pairs[0].normal_stiffness_Pa_per_m,self.normal_integration_settings)
            residual+=normal.residual-sum((p.normal_residual for p in points),np.zeros_like(residual))
            tangent+=normal.spatial_tangent()-sum((p.normal_spatial_tangent() for p in points),np.zeros_like(tangent))
            storage=normal.normal_storage_j;diagnostics=normal.diagnostics
        trial=NativeSurfacePatchTrial(NativeSurfacePatchHistory(self.definition_sha256,
                                     tuple(p.trial.candidate_state for p in points)))
        result=NativeSurfacePatchResult(_readonly(residual),_readonly(tangent),trial,
            gap,storage,points,continuous,diagnostics)
        return NativeS3MaterialPathResult(current,result,
            sha(dict(definition=self.definition_sha256,paths=[v.path_sha256 for v in values])),
            orientation_intervals+sum(v.certified_intervals for v in values))
