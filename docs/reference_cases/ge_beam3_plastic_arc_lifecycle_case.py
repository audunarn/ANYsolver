"""Successor one/two-macro fixture and owned capture; unchanged native mechanics."""
from hashlib import sha256
from math import fsum
from docs.reference_cases.ge_beam3_plastic_arc_fixture import fixture
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes

def build(macros):
    import numpy as np
    from anysolver.fe_core import FEModel
    from anysolver.boundary import BoundaryCondition
    from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry
    from anysolver._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
    from anysolver._ge_beam3_native_generalized_element import NativeGeneralizedStaticElement
    from anysolver import _ge_beam3_retained_arc as arc
    f=fixture(macros);model=FEModel('active-plastic-arc-smoke-v1')
    for i,point in enumerate(f['points'],1):model.add_node(i,*point)
    law=EllipsoidalGeneralizedSection(f['elastic'],f['metric'],f['yield_force'],f['hardening'])
    for i,ids in enumerate(f['connectivity'],1):
        nodes=[j-1 for j in ids]
        reference=CenteredCurvedBeam3ReferenceGeometry(np.array([f['points'][j] for j in nodes]),np.array([f['frames'][j] for j in nodes]))
        element=NativeGeneralizedStaticElement(i,tuple(ids),reference,law,order=f['order'])
        model.add_element(i,element);model.materials[element.material_name]=law
    model.add_boundary_condition(BoundaryCondition('clamped',[f['fixed_node']],{k:0. for k in ('ux','uy','uz','rx','ry','rz')}))
    programme=arc.Program(tuple(f['steps']),f['length_scale'],arc.NodalDeadForces((tuple(f['force']),)),
        parameter_scale=f['parameter_scale'],initial_sign=f['initial_sign'],max_iterations=f['max_iterations'],max_backtracks=f['max_backtracks'])
    return model,programme

def capture(macros,raw,revision,progress):
    from anysolver import _ge_beam3_retained_arc as arc
    from anysolver._ge_beam3_p5_seeded.core import canonical
    model,programme=build(macros);context=arc.Context(model,programme)
    accepted,records=context.restore(raw,expected_sha256=sha256(raw).hexdigest())
    if accepted.completed_steps!=3:raise ValueError('complete arc-owned programme required')
    before=canonical(accepted);steps=[]
    for index in range(1,4):
        prefix=context.checkpoint(records[:index])
        state,_=context.restore(prefix,expected_sha256=sha256(prefix).hexdigest())
        old=canonical(state)
        _,_,metrics,responses,_=context.physical.assemble(state.mechanical,state.parameter,state.origins)
        if max(metrics)>1e-11:raise ValueError('accepted physical equilibrium changed')
        elements=[]
        for i,((eid,element),response) in enumerate(zip(context.physical.elements,responses,strict=True)):
            material=strict_bytes(response.material);stations=[]
            if canonical(material['origin'])!=canonical(state.origins[i]) or canonical(material['history'])!=canonical(state.histories[i]):
                raise ValueError('original increment material binding')
            for j,(row,origin) in enumerate(zip(material['stations'],state.origins[i].stations,strict=True)):
                sample=element.section.response([fsum((a,b)) for a,b in zip(*row['resultants'])],origin=origin,control='resultant')
                stations.append(dict(material=row,tangent=[sample.tangent,sample.tangent_low],
                    tangent_strain=[sample.strain,sample.strain_low],tangent_resultants=[sample.resultants,sample.resultants_low],tangent_origin=sample.origin))
                progress(dict(stage='station-captured',macros=macros,step=index,element=eid,station=j))
            elements.append(dict(element_id=eid,stations=stations))
        context.recover(state)
        if canonical(state)!=old:raise ValueError('capture advanced committed history')
        steps.append(dict(step=index,record_sha256=strict_bytes(records[index-1])['record_sha256'],elements=elements))
    if canonical(accepted)!=before or context.checkpoint(records)!=raw:raise ValueError('complete source history changed')
    return canonical(dict(schema='GE_BEAM3_PLASTIC_ARC_CAPTURE_V1',revision=revision,fixture=fixture(macros),
        checkpoint_sha256=sha256(raw).hexdigest(),steps=steps,production_qualified=False))
