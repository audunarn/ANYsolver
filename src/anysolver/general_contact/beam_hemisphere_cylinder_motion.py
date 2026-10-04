"""Explicit prescribed axis translation with actual cylinder-cap work.

Uses the fixed-cylinder geometry and the existing complete reaction/work map.
The fixed profile, validators and checkpoint identities retain their contract.
"""
from dataclasses import dataclass, replace
from .core import ContactValidationReport, validate_general_contact
from .beam_hemisphere_cylinder import (HemisphereCylinderManager,
    HemisphereCylinderResults, validate_hemisphere_cylinder_contact)

PROFILE='CLASSICAL_B2_B3_HEMISPHERE_TRANSLATING_CYLINDER_STATIC_DEV_V1'


def validate_translating_hemisphere_cylinder(model,definition,settings,*,analysis_control='force'):
    issues=[]
    if len(definition.rigid_bodies)!=1:
        return ContactValidationReport('invalid',('one prescribed cylinder required',),PROFILE)
    body=definition.rigid_bodies[0]
    if body.kind!='cylinder' or body.path_translation is None:
        issues.append('translating cylinder requires explicit prescribed axis translation')
    if analysis_control!='force':
        issues.append('translating actual cylinder-cap profile currently requires force continuation')
    fixed=replace(definition,rigid_bodies=(replace(body,path_translation=None),))
    issues.extend(validate_hemisphere_cylinder_contact(model,fixed,settings).issues)
    issues.extend(validate_general_contact(model,definition,
        replace(settings,beam_end_cap_work='owned_point'),analysis_control=analysis_control).issues)
    return ContactValidationReport('invalid' if issues else 'ok',tuple(issues),PROFILE)


@dataclass(frozen=True)
class TranslatingHemisphereCylinderResults(HemisphereCylinderResults):
    def to_dict(self):
        result=super().to_dict()
        result['rigid_motion_profile']='prescribed_axis_translation_affine_static_v1'
        return result


class TranslatingHemisphereCylinderManager(HemisphereCylinderManager):
    profile=PROFILE
    validator=staticmethod(validate_translating_hemisphere_cylinder)
    results_type=TranslatingHemisphereCylinderResults

    def restart_contract(self):
        result=super().restart_contract()
        result['prescribed_rigid_kinematics']='axis_translation_affine_static_v1'
        return result
