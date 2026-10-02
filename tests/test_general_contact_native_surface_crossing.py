"""Analytic zero counts independent of the production geometry adapter."""
from math import acos,ceil,cos,floor,pi,sin

import pytest

from anysolver.general_contact.native_surface_crossing import GapSlabEnclosure,certify_single_crossing
from anysolver.general_contact.native_surface_support import SupportIntervalBudget


def rotating_family(phase,travel,level):
    # Whole spatial angular strip, including every angle between these limits.
    strip=(-.02,.02)
    def extrema(function,left,right,stationary_offset):
        points=[left,right]
        points.extend(stationary_offset+k*pi for k in range(
            ceil((left-stationary_offset)/pi),floor((right-stationary_offset)/pi)+1))
        values=[function(x) for x in points]
        return min(values),max(values)
    def enclose(left,right):
        low=phase+travel*left+strip[0];high=phase+travel*right+strip[1]
        gl,gu=extrema(cos,low,high,0.)
        dl,du=extrema(lambda x:-travel*sin(x),low,high,pi/2)
        # Conservative arithmetic allowance for this bounded analytic fixture.
        return GapSlabEnclosure(gl-level-1e-12,gu-level+1e-12,dl-1e-12,du+1e-12)
    def roots(offset):
        alpha=acos(level)
        return sorted(t for k in range(-3,4) for sign in (-1,1)
            if 0.<(t:=(sign*alpha+2*pi*k-phase-offset)/travel)<1.)
    return enclose,roots


def test_extremum_away_from_contact_allows_one_transverse_crossing():
    enclose,roots=rotating_family(-.4,2.,.7)
    assert all(len(roots(offset))==1 for offset in (-.02,0.,.02))
    # g' changes sign; the old whole-segment monotonicity proof cannot pass.
    assert enclose(0.,1.).derivative_lower<0<enclose(0.,1.).derivative_upper
    budget=SupportIntervalBudget(128)
    assert certify_single_crossing(enclose,budget=budget)
    assert 1<budget.intervals<128


def test_two_crossings_cannot_pass_even_with_same_signed_endpoints():
    enclose,roots=rotating_family(-1.2,2.4,.7)
    assert all(len(roots(offset))==2 for offset in (-.02,0.,.02))
    assert enclose(0.,0.).gap_upper<0 and enclose(1.,1.).gap_upper<0
    assert not certify_single_crossing(enclose,budget=SupportIntervalBudget(128))


def test_unresolved_tangency_consumes_bounded_budget_and_rejects():
    def tangent(left,right):
        minimum=0. if left<=.5<=right else min((left-.5)**2,(right-.5)**2)
        return GapSlabEnclosure(minimum,max((left-.5)**2,(right-.5)**2),2*(left-.5),2*(right-.5))
    budget=SupportIntervalBudget(8)
    assert not certify_single_crossing(tangent,budget=budget)
    assert budget.intervals==8


def test_strictly_open_gap_needs_no_derivative_sign():
    budget=SupportIntervalBudget(1)
    assert certify_single_crossing(lambda l,r:GapSlabEnclosure(1.,2.,-5.,5.),budget=budget)
    assert budget.intervals==1


@pytest.mark.parametrize('values',[(float('nan'),1.,0.,1.),(2.,1.,0.,1.),(0.,1.,2.,1.)])
def test_invalid_enclosures_rejected(values):
    with pytest.raises(ValueError,match='ordered'):
        GapSlabEnclosure(*values)


@pytest.mark.parametrize('phase,travel,expected',[(-.4,2.,True),(-1.2,2.4,False)])
def test_actual_retained_geometry_single_crossing_and_hidden_pulse(phase,travel,expected):
    import numpy as np
    from anysolver.general_contact.native_surface_history import NativeSurfaceMotionSegment
    from anysolver.general_contact.native_surface_support import segment_gap_slab_enclosure,history_endpoint_support_certified
    from test_general_contact_native_surface_support import _field
    segment=NativeSurfaceMotionSegment(np.zeros((3,3)),np.array(((travel,0.,0.),(0.,0.,0.))),np.zeros(18))
    press=NativeSurfaceMotionSegment(np.tile((0.,0.,-.029),(3,1)),np.zeros((2,3)),np.zeros(18))
    field=_field(height=.05,rotation=phase,segments=(press,segment))
    angles=field.patch.rule.definition['angle_range']
    assert not history_endpoint_support_certified(field)
    enclose=segment_gap_slab_enclosure(field,0,(-.8,-.2),angles,1)
    # Independent physical formula is .021-.03*cos(phase+travel*t+offset).
    _,roots=rotating_family(phase,travel,.7)
    assert all(len(roots(offset))==(1 if expected else 2) for offset in (-.02,0.,.02))
    for left,right in ((0.,1.),(.125,.25),(.5,.75)):
        bounds=enclose(left,right)
        for t in np.linspace(left,right,13):
            for offset in np.linspace(-.02,.02,9):
                theta=phase+travel*t+offset
                assert bounds.gap_lower<=.021-.03*cos(theta)<=bounds.gap_upper
                assert bounds.derivative_lower<=.03*travel*sin(theta)<=bounds.derivative_upper
    assert certify_single_crossing(enclose,budget=SupportIntervalBudget(128)) is expected


def test_actual_slab_adapter_rejects_wrong_half_cell():
    import numpy as np
    from anysolver.general_contact.native_surface_history import NativeSurfaceMotionSegment
    from anysolver.general_contact.native_surface_support import segment_gap_slab_enclosure
    from test_general_contact_native_surface_support import _field
    field=_field(segments=(NativeSurfaceMotionSegment(np.zeros((3,3)),np.zeros((2,3)),np.zeros(18)),))
    with pytest.raises(ValueError,match='half-cell'):
        segment_gap_slab_enclosure(field,1,(-.8,-.2),field.patch.rule.definition['angle_range'],0)


def test_deforming_target_subslab_uses_original_time_derivative():
    import numpy as np
    from anysolver.general_contact.native_surface_history import NativeSurfaceMotionSegment
    from anysolver.general_contact.native_surface_support import segment_gap_slab_enclosure
    from test_general_contact_native_surface_support import _field
    shell=np.zeros(18);shell[8]=.01;shell[14]=-.006;shell[12]=.025
    translations=np.tile((.015,0.,-.002),(3,1));omega=.2
    segment=NativeSurfaceMotionSegment(translations,np.array(((omega,0.,0.),(0.,0.,0.))),shell)
    field=_field(height=.08,rotation=.1,segments=(segment,))
    enclose=segment_gap_slab_enclosure(field,0,(-.8,-.2),field.patch.rule.definition['angle_range'],0)
    bounds=enclose(.3125,.375)
    adapter=field.patch.target.adapter
    corners0=adapter.current_positions(field.initial.shell_displacement)
    motion=np.asarray(adapter.work_map@shell).reshape(3,3)
    frame=field.initial.cell_rotations[0]@field.patch.source.reference.nodal_triads[0]
    def independent_gap(t,xi,angle):
        corners=corners0+t*motion
        cross=np.cross(corners[1]-corners[0],corners[2]-corners[0])
        normal=cross/np.sqrt(cross@cross)
        alpha=xi+1
        base=(1-alpha)*(field.initial.positions[0]+field.initial.position_low[0])+alpha*(field.initial.positions[1]+field.initial.position_low[1])+t*translations[0]
        c,s=np.cos(omega*t),np.sin(omega*t)
        rotation=np.array(((1.,0.,0.),(0.,c,-s),(0.,s,c)))
        arm=rotation@frame@np.array((0.,.03*cos(angle),.03*sin(angle)))
        return normal@(base+arm-corners[0])
    for t in np.linspace(.3125,.375,9):
        for xi in (-.8,-.53,-.2):
            for angle in np.linspace(*field.patch.rule.definition['angle_range'],7):
                gap=independent_gap(t,xi,angle)
                derivative=independent_gap(t+1e-25j,xi,angle).imag/1e-25
                assert bounds.gap_lower<=gap<=bounds.gap_upper
                assert bounds.derivative_lower<=derivative<=bounds.derivative_upper
