"""Exact topology, ownership and sparse-incidence envelope checks only."""
from fractions import Fraction as F

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_grid as local
from scripts import _b3_e4_f03_spatial_contract as c


@pytest.mark.parametrize('p',(1,2,3))
def test_shared_axis_nodes_and_exact_support_elimination(p):
    xs=[F(-1,2),F(1,2),F(3,2)];ys=[F(-1,2),F(0),F(1,2)]
    grid=local.compile_grid(xs,ys,p)
    assert grid.free_dofs==2*(2*p-1)*(2*p+1)
    assert len(grid.rectangles)==4
    q=np.arange(grid.free_dofs,dtype=float)
    full=np.zeros(grid.full_dofs);full[grid.free_to_full]=q
    for j in range(len(grid.y_nodes)):
        for component in (0,1):
            base=component*grid.full_dofs//2+j*len(grid.x_nodes)
            assert full[base]==full[base+len(grid.x_nodes)-1]==0
    # The two vertical traces share the exact same nodal identities.
    left=grid.full_gathers[0].reshape(2,p+1,p+1)
    right=grid.full_gathers[1].reshape(2,p+1,p+1)
    np.testing.assert_array_equal(left[:,:,-1],right[:,:,0])
    xs[1]=F(2,3)
    assert grid.x_cuts[1]==F(1,2)
    for array in (grid.free_to_full,grid.full_to_free,grid.full_gathers,
                  grid.free_gathers,grid.root_incidence,*grid.trace_incidence):
        assert not array.flags.writeable
        with pytest.raises(ValueError): array.setflags(write=True)


def test_exact_station_partition_preserves_collapsed_positive_intervals():
    grid=local.compile_grid(c.X_CUTS,c.Y_CUTS,1)
    small=[(a,b) for a,b in zip(grid.station_cuts,grid.station_cuts[1:])
           if float(a)==float(b)]
    assert small and all(b>a for a,b in small)
    assert (1-2*(c.Q_DX+c.Q_A),2*(c.Q_DX+c.Q_A)) in small
    assert len(grid.trace_incidence)==len(grid.station_cuts)-1
    assert all(len(ids)>0 for ids in grid.trace_incidence)


def test_bitset_pattern_matches_small_dense_boolean_oracle():
    grid=local.compile_grid((F(-1,2),F(1,2),F(3,2)),(F(-1,2),F(1,2)),1)
    result=local.incidence_envelope(grid,max_graph_bytes=1024**2)
    n=grid.free_dofs+3;pattern=np.zeros((n,n),dtype=bool)
    for raw in (*grid.free_gathers,*grid.trace_incidence):
        ids=np.unique(raw[raw>=0]);pattern[np.ix_(ids,ids)]=True
    for multiplier in range(grid.free_dofs,n):
        pattern[multiplier,grid.root_incidence]=True
        pattern[grid.root_incidence,multiplier]=True
    np.testing.assert_array_equal(result['row_nnz_envelope'],pattern.sum(axis=1))
    assert result['kkt_nnz_envelope']==pattern.sum()
    assert result['dense_L_plus_U_entries_bound']==n*(n+1)
    assert result['graph_storage_bound_bytes']<=1024**2
    assert not pattern[-3:,-3:].any()


def test_invalid_geometry_and_preallocation_resource_limits():
    xs=(F(-1,2),F(1,2),F(3,2));ys=(F(-1,2),F(1,2))
    with pytest.raises(ValueError): local.compile_grid((-.5,.5,1.5),ys,1)
    with pytest.raises(ValueError): local.compile_grid((xs[0],xs[1],xs[1],xs[2]),ys,1)
    with pytest.raises(ValueError): local.compile_grid(xs,ys,True)
    with pytest.raises(ValueError,match='incidence'):
        local.compile_grid(xs,ys,2,max_incidence_entries=1)
    grid=local.compile_grid(xs,ys,1)
    with pytest.raises(ValueError,match='budget'):
        local.incidence_envelope(grid,max_graph_bytes=1)


def test_pattern_is_an_envelope_and_fixed_footprint_incidence_grows():
    xs=(F(-1,2),F(1,2),F(3,2));ys=(F(-1,2),F(1,2))
    coarse=local.compile_grid(xs,ys,1)
    fine=local.compile_grid(xs,ys,3)
    a=local.incidence_envelope(coarse,max_graph_bytes=1024**2)
    b=local.incidence_envelope(fine,max_graph_bytes=1024**2)
    assert b['max_active_trace_dofs']>a['max_active_trace_dofs']
    assert b['beam_nnz_envelope']>a['beam_nnz_envelope']
    assert b['dense_L_plus_U_entries_bound']>a['dense_L_plus_U_entries_bound']
    assert 'no factorization' in b['claim']


def test_factory_boundary_and_exact_input_bounds():
    from dataclasses import replace
    xs=(F(-1,2),F(1,2),F(3,2));ys=(F(-1,2),F(1,2))
    grid=local.compile_grid(xs,ys,1)
    with pytest.raises(TypeError,match='factory'):
        local.CompiledGrid()
    with pytest.raises(TypeError,match='factory'):
        replace(grid,root_incidence=np.array([0,1]))
    with pytest.raises(ValueError,match='partition'):
        local.compile_grid((F(-1,2),F(1,2**256),F(3,2)),ys,1)
    def never_consume():
        raise AssertionError('unbounded iterator was consumed')
        yield
    with pytest.raises(ValueError,match='partition'):
        local.compile_grid(never_consume(),ys,1)
    # Bounded odd-denominator inputs may create an over-budget difference
    # with a dyadic pad edge. Reject at compilation, not during a later trial.
    odd=(1<<254)+1
    with pytest.raises(ValueError,match='derived exact station'):
        local.compile_grid((F(-1,2),F(1,odd),F(3,2)),ys,1)
