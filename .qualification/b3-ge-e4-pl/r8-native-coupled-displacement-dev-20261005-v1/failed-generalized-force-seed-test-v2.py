"""Native generalized yielding through fixed point displacement histories."""
from dataclasses import replace
from math import fsum
import numpy as np
from anysolver import b3_ge,stiffened_shell as ss
from test_stiffened_shell_native_point_displacement import owner,model,compare,native_state,OPTIONS


def test_native_generalized_yielding_displacement_reload(request,tmp_path):
    base=model('generalized');beams=[]
    for native in base.beams:
        element,inertia=native.instantiate()
        # Reuse the already-exercised generalized branch's development strength/hardening.
        section=b3_ge.EllipsoidalGeneralizedSection(element.section.elastic,
            element.section.metric,5.,1e6)
        reference=element.operator.reference
        beams.append(b3_ge.define_beam('b3-ge',element.element_id,element.node_ids,
            reference.coordinates,reference.nodal_triads,section,inertia,
            quadrature=element.operator.order))
    definition=replace(base,beams=tuple(beams))
    analysis=owner(request,definition);resumed=owner(request,definition)
    # The stronger force-controlled seed is retained as a failed diagnostic.
    # Define physical displacement targets from the existing elastic model;
    # this is a different load-control problem, not agreement at the failed force.
    elastic=owner(request,base)
    elastic.solve((ss.NodalAction('beam',105,(0.,0.,250.,0.,0.,0.)),),(1.,),**OPTIONS)
    load=(ss.NodalAction('beam',105,(0.,0.,1.,0.,0.,0.)),)
    analysis.solve(load,(1.,),**OPTIONS)
    dof=analysis._shell_count+6*analysis._beam_index[105]+2
    initial=elastic._finite_driver._state.q[dof]
    direction=(ss.NodalAction('beam',105,(0.,0.,100.,0.,0.,0.)),)
    kw=dict(OPTIONS,displacement_control=ss.DisplacementControl('beam',105,2))
    loaded=analysis.solve(direction,(initial*.5,initial),**kw)
    assert max(max(row) for row in loaded.beam_station_accumulated)>0.
    prefix=analysis.solve(direction,(initial*.99,),**kw)
    saved=analysis.checkpoint();before=native_state(analysis)
    assert prefix.beam_generalized_material and not prefix.beam_fibre_material
    restored=resumed.restore(saved)
    assert resumed.checkpoint()==saved;compare(prefix,restored)
    (tmp_path/'generalized-yield-prefix.checkpoint').write_bytes(saved)
    final=analysis.solve(direction,(initial*1.01,),**kw)
    again=resumed.solve(direction,(initial*1.01,),**kw)
    assert analysis.checkpoint()==resumed.checkpoint();compare(final,again)
    after=native_state(analysis)
    changes=[]
    for current,previous in zip(after['beam_accumulated'],before['beam_accumulated'],strict=True):
        change=fsum((*current,*-previous))
        budget=64*np.finfo(float).eps*max(abs(fsum(current)),abs(fsum(previous)))
        assert change>=-budget;changes.append(change)
    assert any(change>0. for change in changes)
    assert final.free_equilibrium_ratio<=1e-8 and final.constraint_max<=1e-9
    assert not final.production_qualified
    (tmp_path/'generalized-yield-completed.checkpoint').write_bytes(analysis.checkpoint())
