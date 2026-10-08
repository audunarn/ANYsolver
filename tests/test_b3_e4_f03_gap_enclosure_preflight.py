"""Exact-input rational field bounds on bounded analytic gap patches."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_gap_enclosure as enclosure
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell


@pytest.mark.parametrize('topology', ['Q4','CST'])
def test_exact_overlay_contains_stored_geometry_and_rational_beam_breaks(topology):
    model=shell.panel(3,6,topology)
    knots=enclosure.exact_overlay(model,3,2)
    assert knots[0]==0 and knots[-1]==1
    assert Fraction(1,3) in knots and Fraction(2,3) in knots
    assert all(a<b for a,b in zip(knots[:-1],knots[1:]))
    for dx,dy in shell.OFFSETS:
        offset=Fraction.from_float(dx)
        for i in range(2*model.n_s+1):
            crossing=Fraction.from_float(float(model.nodes[i,0]))-offset
            if 0<=crossing<=1:
                assert crossing in knots
    if topology=='CST':
        xs,ys=enclosure._axes(model)
        y=Fraction.from_float(shell.OFFSETS[0][1])
        j=next(j for j in range(model.n_y) if ys[j]<y<ys[j+1])
        crossing=xs[1]+(y-ys[j])*(xs[2]-xs[1])/(ys[j+1]-ys[j])
        crossing-=Fraction.from_float(shell.OFFSETS[0][0])
        if 0<=crossing<=1:
            assert crossing in knots


@pytest.mark.parametrize('topology', ['Q4','CST'])
def test_constant_and_interior_quadratic_gap_are_enclosed(topology):
    model=shell.panel(3,6,topology)
    qs=np.zeros(model.dof_count)
    qb=np.zeros(beam.dof_count(1))
    qb[:3]=.125
    bounds=enclosure.gap_bounds(model,1,1,qs,qb,depth=2)
    assert bounds[0][0]<=.125<=bounds[0][1]
    assert bounds[0][1]-bounds[0][0]<1e-14
    assert all(hi<1e-14 for lo,hi in bounds[1:])

    qb[:]=0
    qb[4]=1
    qb[6]=-1
    # Hermite v(s)=s(1-s) is zero at both ends and peaks at s=1/2.
    coarse=enclosure.gap_bounds(model,1,1,qs,qb,depth=0)[1]
    fine=enclosure.gap_bounds(model,1,1,qs,qb,depth=6)[1]
    assert coarse[0]<=.25<=coarse[1]
    assert fine[0]<=.25<=fine[1]
    assert fine[1]-fine[0]<=coarse[1]-coarse[0]
    assert fine[1]-.25<1e-9


@pytest.mark.parametrize('topology', ['Q4','CST'])
def test_nonsmooth_overlay_fields_stay_inside_component_bounds(topology):
    model=shell.panel(3,6,topology)
    rng=np.random.default_rng(84)
    qs=rng.standard_normal(model.dof_count)*1e-4
    qb=rng.standard_normal(beam.dof_count(4))*1e-4
    bounds=enclosure.gap_bounds(model,4,2,qs,qb,depth=5)
    knots=line.overlay(model,4,2)
    maxima=np.zeros(3)
    for a,b in zip(knots[:-1],knots[1:]):
        for s in np.linspace(a,b,11):
            gap=beam.trace(4,float(s))@qb-shell.pose(model,float(s))@qs
            gap[2]*=line.YAW_LENGTH
            maxima=np.maximum(maxima,np.abs(gap))
    for maximum,(lower,upper) in zip(maxima,bounds):
        assert lower<=upper
        assert maximum<=upper+1e-12
        # A station grid may miss the attained Bernstein subdivision value.
        assert upper-lower<1e-7
