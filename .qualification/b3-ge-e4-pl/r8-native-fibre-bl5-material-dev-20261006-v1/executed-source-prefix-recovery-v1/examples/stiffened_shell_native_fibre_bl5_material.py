"""Experimental Q4/native physical-fibre BL5 material history and restart."""
from dataclasses import replace
import json
from anymaterial import DNVC208MaterialCurve
from anysolver import b3_ge, stiffened_shell as ss
from examples.stiffened_shell_native_fibre_bl5 import definition as elastic_definition


def definition(family='biaxial', beams='mixed', basis='p0', shell_material=True):
    model = elastic_definition(family, beams, basis, yield_stress=1e5)
    if beams == 'mixed':
        element, inertia = model.beams[0].instantiate()
        section = b3_ge.EllipsoidalGeneralizedSection(element.section.elastic,
                                                     element.section.metric, 5., 1e8)
        generalized = b3_ge.define_beam('b3-ge', element.element_id, element.node_ids,
            element.operator.reference.coordinates, element.operator.reference.nodal_triads,
            section, inertia, quadrature=element.operator.order)
        model = replace(model, beams=(generalized,)+model.beams[1:])
    curve = DNVC208MaterialCurve(1e6, 1.05e6, 1.1e6, .005, .01, 4e6, .2)
    return replace(model, shell=replace(model.shell, j2_curve=curve if shell_material else None),
                   bl5_material_policy=ss.BL5_NATIVE_FIBRE_MATERIAL_V1)


ACTIONS = (ss.NodalAction('beam', 105, (0., 0., 500., 0., 0., 0.)),)
CONTROLS = dict(max_iterations=24, max_backtracks=12,
                increment_control=ss.AdaptiveIncrementControl(4, 64))


def workflow():
    model = definition()
    owner = ss.create_analysis(definition=model)
    fresh = ss.create_analysis(definition=model)
    try:
        prefix = owner.solve(ACTIONS, (.5, 1.), **CONTROLS)
        raw = owner.checkpoint()
        fresh.restore(raw)
        if fresh.checkpoint() != raw:
            raise RuntimeError('fresh restore changed material checkpoint')
        continued = owner.solve(ACTIONS, (1.1,), **CONTROLS)
        resumed = fresh.solve(ACTIONS, (1.1,), **CONTROLS)
        if owner.checkpoint() != fresh.checkpoint():
            raise RuntimeError('continued material histories differ')
        return dict(status=continued.status, policy=ss.BL5_NATIVE_FIBRE_MATERIAL_V1,
                    model_identity=owner.preflight()['identity'], production_qualified=False,
                    retained_dofs=owner.preflight()['retained_dofs'],
                    shell_alpha_max=max(map(max, prefix.shell_layer_alpha)),
                    fibre_alpha_max=max(map(max, prefix.beam_station_accumulated)),
                    free_equilibrium_ratio=continued.free_equilibrium_ratio,
                    constraint_max=continued.constraint_max,
                    fresh_restore_bytes_equal=True, continued_bytes_equal=True,
                    generation=continued.generation, resumed_generation=resumed.generation)
    finally:
        owner.close()
        fresh.close()


if __name__ == '__main__':
    print(json.dumps(workflow(), indent=2, allow_nan=False))
