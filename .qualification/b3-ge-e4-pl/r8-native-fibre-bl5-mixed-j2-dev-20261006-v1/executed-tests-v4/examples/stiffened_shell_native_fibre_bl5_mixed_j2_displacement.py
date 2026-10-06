"""Native fibre BL5 all-S3/mixed isotropic J2 fixed translation development route."""
from dataclasses import replace
import json
from anysolver import stiffened_shell as ss
from anymaterial import DNVC208MaterialCurve
from examples.stiffened_shell_native_fibre_bl5 import definition as elastic_definition
from examples.stiffened_shell_native_fibre_bl5_displacement import ACTIONS, CONTROL, OPTIONS, TARGETS


def definition(shell='mixed',family='biaxial',beams='mixed',basis='p0'):
    if shell not in ('s3','mixed'):raise ValueError('all-S3 or mixed shell required')
    model=elastic_definition(family,beams,basis,yield_stress=1e5,shell=shell)
    curve=DNVC208MaterialCurve(1e6,1.05e6,1.1e6,.005,.01,4e6,.2)
    return replace(model,shell=replace(model.shell,j2_curve=curve),
                   bl5_material_policy=ss.BL5_NATIVE_FIBRE_MIXED_SHELL_MATERIAL_V1)


def workflow(shell='mixed',family='biaxial',beams='mixed',basis='p0',on_accepted=None):
    model=definition(shell,family,beams,basis)
    owner=ss.create_analysis(definition=model);fresh=ss.create_analysis(definition=model)
    try:
        seed=owner.solve(ACTIONS,(.001,),**OPTIONS)
        if seed.status!='completed':raise RuntimeError('ordinary native force seed failed')
        raw_seed=owner.checkpoint();fresh.restore(raw_seed)
        assert fresh.checkpoint()==raw_seed
        loaded=owner.solve(ACTIONS,TARGETS[:2],displacement_control=CONTROL,on_accepted=on_accepted,**OPTIONS)
        raw=owner.checkpoint();fresh.restore(raw)
        assert fresh.checkpoint()==raw
        final=owner.solve(ACTIONS,TARGETS[2:],displacement_control=CONTROL,**OPTIONS)
        continued=fresh.solve(ACTIONS,TARGETS[2:],displacement_control=CONTROL,**OPTIONS)
        assert owner.checkpoint()==fresh.checkpoint()
        assert final.shell_s3_material and final.beam_fibre_material
        if beams=="mixed":assert final.beam_generalized_material
        return dict(status=final.status,shell=shell,policy=model.bl5_material_policy,
            target=final.target,amplitude=final.amplitude,generation=final.generation,
            shell_alpha_max=max(map(max,loaded.shell_layer_alpha)),
            fibre_alpha_max=max(map(max,loaded.beam_station_accumulated)),
            free_equilibrium_ratio=final.free_equilibrium_ratio,constraint_max=final.constraint_max,
            fresh_restore_bytes_equal=True,continued_bytes_equal=True,production_qualified=False)
    finally:owner.close();fresh.close()

if __name__=='__main__':print(json.dumps(workflow(),indent=2))
