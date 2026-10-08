"""Bounded assembled kinematic proofs; no energy, equilibrium or science run."""
from fractions import Fraction as F

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_moments as moments


def rank_exact(rows):
    rows=[list(r) for r in rows];pivot=0
    for column in range(len(rows[0])):
        chosen=next((i for i in range(pivot,len(rows)) if rows[i][column]),None)
        if chosen is None: continue
        rows[pivot],rows[chosen]=rows[chosen],rows[pivot]
        divisor=rows[pivot][column];rows[pivot]=[v/divisor for v in rows[pivot]]
        for i in range(pivot+1,len(rows)):
            factor=rows[i][column]
            rows[i]=[a-factor*b for a,b in zip(rows[i],rows[pivot])]
        pivot+=1
        if pivot==len(rows): break
    return pivot


def assembled_trace(grid,a,b):
    coefficients=[[[F(0)]*(grid.p+3) for _ in range(grid.free_dofs)] for _ in range(3)]
    for rect,gather in zip(grid.rectangles,grid.free_gathers):
        trace=moments.trace_segment(rect,grid.p,a,b)
        for channel in range(3):
            for local,global_dof in enumerate(gather):
                if global_dof<0: continue
                for k,value in enumerate(trace.coefficients[channel][local]):
                    coefficients[channel][global_dof][k]+=value
    return coefficients


def at_endpoint(coefficients,a,b,side,order):
    result=[]
    for channel in coefficients:
        result.append(tuple(sum((poly[k]*F(k if order else 1)*F(side)**(k-order)
                      for k in range(order,len(poly))),F(0))/(b-a)**order for poly in channel))
    return tuple(result)


@pytest.mark.parametrize('p',[1,2,3])
def test_exact_shared_trace_continuity_and_root_slope_freedom(p):
    grid=topology.compile_grid((F(-1,2),F(0),F(1,2),F(1),F(3,2)),
                               (F(-1,2),F(0),F(1,2)),p)
    previous=None
    # Test the complete assembled operator, not just one rigid nodal field.
    for i,(a,b) in enumerate(zip(grid.station_cuts,grid.station_cuts[1:])):
        coefficients=assembled_trace(grid,a,b)
        left=tuple(at_endpoint(coefficients,a,b,0,order) for order in (0,1))
        right=tuple(at_endpoint(coefficients,a,b,1,order) for order in (0,1))
        if previous is not None:
            assert left==previous
        else:
            root=left[0];root_transverse_slope=left[1][1]
            assert rank_exact(root)==3
            assert rank_exact((*root,root_transverse_slope))==4
        previous=right
        actual={j for channel in coefficients for j,row in enumerate(channel) if any(row)}
        assert actual.issubset(set(grid.trace_incidence[i]))
    actual_root={j for channel in root for j,v in enumerate(channel) if v}
    assert actual_root.issubset(set(grid.root_incidence))


def test_exact_root_rank_detects_a_coarse_space_that_artificially_clamps_slope():
    # One Q1 x span between two supports leaves no free physical x node.
    # A two-span Q1 mesh has root rank 3 but root transverse slope is dependent.
    grid=topology.compile_grid((F(-1,2),F(1,2),F(3,2)),(F(-1,2),F(0),F(1,2)),1)
    a,b=grid.station_cuts[:2]
    coefficient=assembled_trace(grid,a,b)
    root=at_endpoint(coefficient,a,b,0,0)
    slope=at_endpoint(coefficient,a,b,0,1)[1]
    assert rank_exact(root)==3
    assert rank_exact((*root,slope))==3
