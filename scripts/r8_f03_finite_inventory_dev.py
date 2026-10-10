"""Literal <=2-cell rectangle strip/one member geometry certificate inputs.

Exact applicable P0 transverse action closes yaw. An exact supported five-row
minor certifies this single whole-member support only, never a growing family.
"""
from fractions import Fraction as F
from scripts.r8_f03_finite_local_dev import (Unresolved, rational, zero, rectangle_work,
    rectangular_strip_bounds, native_halfcell, native_chain_bounds, close_yaw, geometry_constant,
    solve, identity, multiply)


def literal_inventory(a, b, ell, cells, constitutive, drill, cn, cm, *, arm_z, width, shell_top, budget):
    """All shell6/node and native24 coordinates, with original physical G_X.

    Beam root0..4 supported. Shell both root nodes fully supported. Source
    scalar Q4 H1 /area; physical nodal beam P1 rotations; constant independent
    halfcell rotations and actual lift arm; separately measured shell drilling.
    """
    a, b, ell, arm_z, width, shell_top = map(rational, (a, b, ell, arm_z, width, shell_top))
    if type(cells) is not int or not 1 <= cells <= 2 or width < 0 or shell_top <= 0:
        raise Unresolved('literal bounded geometry inventory')
    work = rectangle_work(a, b, ell, constitutive, drill, budget)
    sb = rectangular_strip_bounds(work, cells, budget)
    shell_count = 12*(cells+1); length = 2*a*cells
    native = native_halfcell(length/2, ell, cn, cm, budget)
    bounds = [v for pair in sb['node_pair_bounds'] for v in pair]+native_chain_bounds(length, ell, budget)
    entries = {}
    def add(i, j, value):
        if value:
            entries[i, j] = budget.check(entries.get((i, j), F())+value)
    area = 4*a*b*cells
    for cell in range(cells):
        # pair layout bottom/top; source local order BL,BR,TR,TL.
        nodes = (2*cell, 2*(cell+1), 2*(cell+1)+1, 2*cell+1)
        for r, wr in ((F(-1), F(1, 3)), (F(), F(4, 3)), (F(1), F(1, 3))):
            for s, ws in ((F(-1), F(1, 3)), (F(), F(4, 3)), (F(1), F(1, 3))):
                signs = ((-1, -1), (1, -1), (1, 1), (-1, 1))
                shape = [(1+ri*r)*(1+si*s)/4 for ri, si in signs]
                nx = [F(ri, 4)*(1+si*s)/a for ri, si in signs]
                ny = [F(si, 4)*(1+ri*r)/b for ri, si in signs]
                measure = a*b*wr*ws/area
                discrepancy = {}
                for i, node in enumerate(nodes):
                    discrepancy[6*node] = ell*ny[i]/2
                    discrepancy[6*node+1] = -ell*nx[i]/2
                    discrepancy[6*node+5] = shape[i]
                    for j, other in enumerate(nodes):
                        scalar = measure*(shape[i]*shape[j]+ell**2*(nx[i]*nx[j]+ny[i]*ny[j]))
                        for axis in range(5):
                            add(6*node+axis, 6*other+axis, scalar)
                for i, x in discrepancy.items():
                    for j, y in discrepancy.items():
                        add(i, j, measure*x*y)
    # Literal straight native H_T from beam_norm, retaining original lift.
    n0 = shell_count; half = length/2
    for cell in range(2):
        for i in range(2):
            for j in range(2):
                mass = half*F(2 if i == j else 1, 6)
                grad = F(1 if i == j else -1)/half
                for axis in range(3):
                    scalar = (mass+ell**2*grad)/length
                    add(n0+6*(cell+i)+axis, n0+6*(cell+j)+axis, scalar)
                    add(n0+6*(cell+i)+3+axis, n0+6*(cell+j)+3+axis, scalar)
        for axis in range(3):
            extra = arm_z**2 if axis in (0, 1) else F()
            if axis in (0, 2):
                extra += width**2/12
            add(n0+18+3*cell+axis, n0+18+3*cell+axis, half/length*(1+extra/ell**2))
        # skew(0,0,az)=[(0,-az,0),(az,0,0),(0,0,0)].
        for node in (cell, cell+1):
            for phi, u, value in ((0, 1, -arm_z), (1, 0, arm_z)):
                i, j = n0+18+3*cell+phi, n0+6*node+u
                add(i, j, half/(2*length*ell)*value); add(j, i, half/(2*length*ell)*value)
    # Original shell TOP lift and native reference arm, not a midsurface guess.
    # P0 density ty: shell(v-top*theta_x) - (beam v - az*phi_x).
    actions, rigid = zero(5, len(bounds)), [F()]*len(bounds)
    for cell in range(cells):
        for node in (2*cell, 2*(cell+1)):
            for axis in range(3): actions[axis][6*node+axis] += a
            actions[0][6*node+4] += a*shell_top/ell
            actions[1][6*node+3] -= a*shell_top/ell
            actions[3][6*node+4] += a/ell
            actions[4][6*node+3] -= a/ell
    for cell in range(2):
        for node in (cell, cell+1):
            for axis in range(3): actions[axis][n0+6*node+axis] -= half/2
        actions[0][n0+18+3*cell+1] -= arm_z*half/ell
        actions[1][n0+18+3*cell] += arm_z*half/ell
        actions[3][n0+18+3*cell+1] -= half/ell
        actions[4][n0+18+3*cell] += half/ell
    c = actions[1]
    for node in range(3):
        rigid[n0+6*node+1] = node*half
        rigid[n0+6*node+5] = ell
    for cell in range(2):
        rigid[n0+18+3*cell+2] = ell
    closed, cr = close_yaw(bounds, rigid, c, budget)
    if cr != -length**2/2:
        raise Unresolved('literal exact P0 yaw integral mismatch')
    # Supported native middle-node translations and first independent cell
    # director rotations give an actual five-row minor for THIS one support.
    pivot = (n0+6, n0+7, n0+8, n0+18, n0+19)
    minor = [[row[j] for j in pivot] for row in actions]
    inv = solve(minor, identity(5), budget, order_cap=5)
    if multiply(minor, inv, budget) != identity(5):
        raise Unresolved('literal P0 exact work-minor identity')
    triples = [(i, j, v) for (i, j), v in sorted(entries.items()) if v]
    cgeom = geometry_constant(triples, closed, budget)
    k0 = min(work['bound']['k0_N_per_m'], native['bound']['k0_N_per_m'])
    return {'shell_work': work, 'native_work': native, 'geometry_bounds': closed,
            'Gz_sparse_exact': triples, 'yaw_rigid_z': rigid, 'P0_ty_action_z': c,
            'P0_five_channel_actions_z': actions,
            'P0_row_rank_certificate': {'scope': 'single whole-member constant-density support, all five channels',
                'supported_minor_columns': pivot, 'minor': minor, 'inverse': inv},
            'P0_yaw_action': cr, 'Cgeom': cgeom, 'k0_N_per_m': k0,
            'candidate_ideal_kappa_N_per_m': budget.check(k0/cgeom),
            'scope': 'literal exact ideal elastic strip with positive numerical completion',
            'full_C_row_rank_certified': True, 'growing_C_row_rank_certified': False,
            'qualification': False}
