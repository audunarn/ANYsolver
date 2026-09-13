"""Independent exact source-equation producer; bounded runner owns execution.

This is a two-fixture identity audit, not recovery qualification. It imports no
production mechanics, former oracle, or numerical environment. All coordinate
polynomials are in the 24 independent inherited-centre-frame nodal variables.
"""
from fractions import Fraction
from itertools import combinations_with_replacement

from ge_beam3_q4_exact_field import (
    Field, dot, matmul, positive_rational_root, solve, transpose, zeros,
)

FIXTURES = {
    'MO16_SQUARE_EXACT': ((-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)),
    'MO16_AFFINE_RHOMBUS_EXACT': (
        ('-8/5', '-4/5', 0), ('2/5', '-4/5', 0),
        ('8/5', '4/5', 0), ('-2/5', '4/5', 0)),
}
SIGNS = ((-1, -1), (1, -1), (1, 1), (-1, 1))
W_INDICES = (2, 8, 14, 20)
PAIRS = tuple(combinations_with_replacement(W_INDICES, 2))


def _difference(a, b):
    return [x - y for x, y in zip(a, b)]


def _cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def _unit(vector):
    length = positive_rational_root(dot(vector, vector))
    result = [x / length for x in vector]
    if dot(result, result) != 1:
        raise ArithmeticError('normalization identity failed')
    return result


def _shape(r, s):
    return ([((1+a*r)*(1+b*s))/4 for a, b in SIGNS],
            [a*(1+b*s)/4 for a, b in SIGNS],
            [b*(1+a*r)/4 for a, b in SIGNS])


def _frames(nodes):
    diagonal_a = _unit(_difference(nodes[2], nodes[0]))
    diagonal_b = _unit(_difference(nodes[1], nodes[3]))
    first = _unit([x+y for x, y in zip(diagonal_a, diagonal_b)])
    second = _unit(_difference(diagonal_a, diagonal_b))
    normal = _unit(_cross(first, second))
    second = _unit(_cross(normal, first))
    first = _unit(_cross(second, normal))
    mixed = transpose([first, second, normal])
    _, dr, ds = _shape(Field(0), Field(0))
    tangent_r = [sum((dr[i]*nodes[i][j] for i in range(4)), Field(0)) for j in range(3)]
    tangent_s = [sum((ds[i]*nodes[i][j] for i in range(4)), Field(0)) for j in range(3)]
    normal0 = _unit(_cross(tangent_r, tangent_s))
    projection = dot(tangent_r, normal0)
    first0 = _unit([tangent_r[i]-projection*normal0[i] for i in range(3)])
    second0 = _unit(_cross(normal0, first0))
    first0 = _unit(_cross(second0, normal0))
    centre = transpose([first0, second0, normal0])
    for frame in (mixed, centre):
        gram = matmul(transpose(frame), frame)
        if any(gram[i][j] != int(i == j) for i in range(3) for j in range(3)):
            raise ArithmeticError('frame is not exactly orthogonal')
        axes = transpose(frame)
        if _cross(axes[0], axes[1]) != axes[2] or axes[2] != [Field(0), Field(0), Field(1)]:
            raise ArithmeticError('physical director or handedness changed')
    return mixed, centre


def _local_coordinates(nodes, frame):
    origin = [sum((p[j] for p in nodes), Field(0))/4 for j in range(3)]
    axes = transpose(frame)
    return [[dot(_difference(point, origin), axes[j]) for j in range(2)] for point in nodes]


def _geometry(local, r, s):
    shape, dr, ds = _shape(r, s)
    xr = sum((local[i][0]*dr[i] for i in range(4)), Field(0))
    xs = sum((local[i][0]*ds[i] for i in range(4)), Field(0))
    yr = sum((local[i][1]*dr[i] for i in range(4)), Field(0))
    ys = sum((local[i][1]*ds[i] for i in range(4)), Field(0))
    determinant = xr*ys-xs*yr
    if any(determinant.c[1:]) or determinant.c[0] <= 0:
        raise ArithmeticError('registered positive rational Jacobian absent')
    dx = [(ys*dr[i]-yr*ds[i])/determinant for i in range(4)]
    dy = [(-xs*dr[i]+xr*ds[i])/determinant for i in range(4)]
    return shape, dx, dy, determinant, (xr, xs, yr, ys)


def _natural_shear(local, r, s, direction):
    shape, dr, ds = _shape(r, s)
    derivative = (dr, ds)[direction]
    x = sum((local[i][0]*derivative[i] for i in range(4)), Field(0))
    y = sum((local[i][1]*derivative[i] for i in range(4)), Field(0))
    result = [Field(0)]*24
    for i in range(4):
        result[6*i+2] = derivative[i]
        result[6*i+3] = -y*shape[i]
        result[6*i+4] = x*shape[i]
    return result


def _compatible(local, r, s):
    _, dx, dy, _, jac = _geometry(local, r, s)
    result = zeros(8, 24)
    for i in range(4):
        q = 6*i
        result[0][q], result[1][q+1] = dx[i], dy[i]
        result[2][q], result[2][q+1] = dy[i], dx[i]
        result[3][q+4], result[4][q+3] = dx[i], -dy[i]
        result[5][q+4], result[5][q+3] = dy[i], -dx[i]
    rm = _natural_shear(local, Field(0), Field(-1), 0)
    rp = _natural_shear(local, Field(0), Field(1), 0)
    sm = _natural_shear(local, Field(-1), Field(0), 1)
    sp = _natural_shear(local, Field(1), Field(0), 1)
    row_r = [(1-s)*a/2+(1+s)*b/2 for a, b in zip(rm, rp)]
    row_s = [(1-r)*a/2+(1+r)*b/2 for a, b in zip(sm, sp)]
    xr, xs, yr, ys = jac
    determinant = xr*ys-xs*yr
    result[6] = [(ys*a-yr*b)/determinant for a, b in zip(row_r, row_s)]
    result[7] = [(-xs*a+xr*b)/determinant for a, b in zip(row_r, row_s)]
    return result


def _source_fields(local, r, s):
    # Derive all bilinear coordinate coefficients; require the registered affine
    # identities rather than assume their vanishing while constructing fields.
    xr = sum((SIGNS[i][0]*local[i][0] for i in range(4)), Field(0))/4
    xs = sum((SIGNS[i][1]*local[i][0] for i in range(4)), Field(0))/4
    yr = sum((SIGNS[i][0]*local[i][1] for i in range(4)), Field(0))/4
    ys = sum((SIGNS[i][1]*local[i][1] for i in range(4)), Field(0))/4
    xrs = sum((a*b*local[i][0] for i, (a,b) in enumerate(SIGNS)), Field(0))/4
    yrs = sum((a*b*local[i][1] for i, (a,b) in enumerate(SIGNS)), Field(0))/4
    jc, jr, js = xr*ys-xs*yr, xr*yrs-xrs*yr, xrs*ys-xs*yrs
    if xrs or yrs:
        raise ValueError('fixture is not affine as registered')
    rbar, sbar = jr/(3*jc), js/(3*jc)
    stress = [[xr*xr,xs*xs,2*xr*xs], [yr*yr,ys*ys,2*yr*ys], [xr*yr,xs*ys,xr*ys+yr*xs]]
    strain = [[xr*xr,xs*xs,xr*xs], [yr*yr,ys*ys,yr*ys], [2*xr*yr,2*xs*ys,xr*ys+yr*xs]]
    sigma, epsilon = zeros(8,14), zeros(8,21)
    for i in range(8):
        sigma[i][i] = epsilon[i][i] = Field(1)
    for row, column in ((0,8), (3,10)):
        for i in range(3):
            sigma[row+i][column] = stress[i][0]*(s-sbar)
            sigma[row+i][column+1] = stress[i][1]*(r-rbar)
            epsilon[row+i][column] = strain[i][0]*(s-sbar)
            epsilon[row+i][column+1] = strain[i][1]*(r-rbar)
    for i, (a,b) in enumerate(((xr,xs),(yr,ys))):
        sigma[6+i][12] = epsilon[6+i][12] = a*(s-sbar)
        sigma[6+i][13] = epsilon[6+i][13] = b*(r-rbar)
    enrichment = [[r,0,0,0,r*s,0,0],[0,s,0,0,0,r*s,0],[0,0,r,s,0,0,r*s]]
    determinant = _geometry(local,r,s)[3]
    enriched = matmul(strain,enrichment)
    for i in range(3):
        for j in range(7):
            epsilon[i][14+j] = jc*enriched[i][j]/determinant
    return sigma, epsilon


def _section():
    nu, thickness = Field('1/4'), Field('1/10')
    plane = [[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]]
    plane = [[Field(x)/(1-nu*nu) for x in row] for row in plane]
    result = zeros(8,8)
    for i in range(3):
        for j in range(3):
            result[i][j] = thickness*plane[i][j]
            result[3+i][3+j] = thickness**3*plane[i][j]/12
    for i in (6,7):
        result[i][i] = Field('5/6')*thickness/(2*(1+nu))
    return result


def _add_matrix(target, source, scale):
    for i, row in enumerate(source):
        for j, value in enumerate(row):
            if value:
                target[i][j] += scale*value


def _nonlinear_coefficients(dx, dy):
    result = zeros(3,len(PAIRS))
    for index, (i,j) in enumerate(PAIRS):
        a, b = i//6, j//6
        factor = 1 if i == j else 2
        result[0][index] = factor*dx[a]*dx[b]/2
        result[1][index] = factor*dy[a]*dy[b]/2
        result[2][index] = dx[a]*dy[b] if i == j else dx[a]*dy[b]+dx[b]*dy[a]
    return result


def _accumulate(polynomial, indices, value):
    if value:
        key = tuple(sorted(indices))
        polynomial[key] = polynomial.get(key,Field(0))+value


def audit(fixture_id, checkpoint=None):
    """Return a complete exact scientific record; caller owns I/O and bounds."""
    if fixture_id not in FIXTURES:
        raise ValueError('unregistered coefficient-audit fixture')
    progress = checkpoint if checkpoint is not None else lambda label: None
    progress('initialization')
    nodes = [[Field(x) for x in row] for row in FIXTURES[fixture_id]]
    mixed_frame, centre_frame = _frames(nodes)
    local = _local_coordinates(nodes,mixed_frame)
    inherited = _local_coordinates(nodes,centre_frame)
    rotation = matmul(transpose(mixed_frame),centre_frame)
    dof_map = zeros(24,24)
    for block in range(8):
        for i in range(3):
            for j in range(3):
                dof_map[3*block+i][3*block+j] = rotation[i][j]
    a,b,c,d = rotation[0][0],rotation[0][1],rotation[1][0],rotation[1][1]
    strain_map = [[a*a,b*b,a*b],[c*c,d*d,c*d],[2*a*c,2*b*d,a*d+b*c]]
    section = _section()
    membrane = [row[:3] for row in section[:3]]
    H, b0, nonlinear = zeros(35,35), zeros(35,24), zeros(35,len(PAIRS))
    E_s = zeros(21,21)
    source3, source4 = {}, {}
    stations = []
    progress('frame_construction')
    gauss = Field.root(3)/3
    for station_index, (r_sign,s_sign) in enumerate(SIGNS):
        r,s = r_sign*gauss,s_sign*gauss
        sigma,epsilon = _source_fields(local,r,s)
        B = matmul(_compatible(local,r,s),dof_map)
        _,_,_,weight,_ = _geometry(local,r,s)
        _,dx,dy,source_weight,_ = _geometry(inherited,r,s)
        if weight != source_weight:
            raise ArithmeticError('source/mixed station measures disagree')
        sigt, epst = transpose(sigma),transpose(epsilon)
        F = matmul(epst,sigma)
        E = matmul(matmul(epst,section),epsilon)
        coupling = matmul(sigt,B)
        for i in range(21):
            for j in range(14):
                H[14+i][j] -= weight*F[i][j]
                H[j][14+i] -= weight*F[i][j]
        for i in range(21):
            for j in range(21):
                H[14+i][14+j] += weight*E[i][j]
        _add_matrix(E_s,E,weight)
        for i in range(14):
            for j in range(24):
                b0[i][j] += weight*coupling[i][j]
        n = _nonlinear_coefficients(dx,dy)
        transformed_n = matmul(strain_map,n)+zeros(5,len(PAIRS))
        j_station = matmul(sigt,transformed_n)
        for i in range(14):
            for j in range(len(PAIRS)):
                nonlinear[i][j] += weight*j_station[i][j]
        bm = zeros(3,24)
        for i in range(4):
            bm[0][6*i],bm[1][6*i+1] = dx[i],dy[i]
            bm[2][6*i],bm[2][6*i+1] = dy[i],dx[i]
        # Independent inherited compatible energy, in its actual centre frame.
        cross = matmul(matmul(transpose(bm),membrane),n)
        fourth = matmul(matmul(transpose(n),membrane),n)
        for i in range(24):
            for j,pair in enumerate(PAIRS):
                _accumulate(source3,(i,)+pair,source_weight*cross[i][j])
        for i,left in enumerate(PAIRS):
            for j,right in enumerate(PAIRS):
                _accumulate(source4,left+right,source_weight*fourth[i][j]/2)
        stations.append({'natural':[r.coefficients(),s.coefficients()], 'weight':weight.coefficients()})
        progress('station_'+str(station_index))
    if H != transpose(H):
        raise ArithmeticError('stationary symmetry identity failed')
    progress('stationary_solve')
    solution = solve(H,[b0[i]+nonlinear[i] for i in range(35)])
    linear_solution = [row[:24] for row in solution]
    nonlinear_solution = [row[24:] for row in solution]
    # Physical strain-energy condensation is an independent identity path from
    # coupling Schur energy, not a call to the public physical matrix.
    physical_schur = matmul(transpose(b0),linear_solution)
    physical_energy = matmul(matmul(transpose(linear_solution[14:]),E_s),linear_solution[14:])
    if any(physical_energy[i][j] != -physical_schur[i][j] for i in range(24) for j in range(24)):
        raise ArithmeticError('degree-two physical energy/Schur identity failed')
    third = matmul(transpose(b0),nonlinear_solution)
    fourth = matmul(transpose(nonlinear),nonlinear_solution)
    stationary3,stationary4 = {},{}
    for i in range(24):
        for j,pair in enumerate(PAIRS):
            _accumulate(stationary3,(i,)+pair,-third[i][j])
    for i,left in enumerate(PAIRS):
        for j,right in enumerate(PAIRS):
            _accumulate(stationary4,left+right,-fourth[i][j]/2)
    progress('coefficient_inventory')
    records,first_nonzero = [],None
    nonzero_count = 0
    for degree,lhs,rhs in ((3,stationary3,source3),(4,stationary4,source4)):
        for indices in combinations_with_replacement(range(24),degree):
            left,right = lhs.get(indices,Field(0)),rhs.get(indices,Field(0))
            difference = left-right
            record = {'degree':degree,'indices':list(indices),
                      'coefficient':difference.coefficients(),
                      'stationary':left.coefficients(),'source':right.coefficients()}
            records.append(record)
            if difference:
                nonzero_count += 1
                if first_nonzero is None:
                    first_nonzero = record.copy()
    if len(records) != 20150:
        raise ArithmeticError('incomplete coefficient inventory')
    progress('evidence_completion')
    return {
        'schema':'G3C_Q4_RETAINED_SPACE_COEFFICIENT_FIXTURE_V1',
        'fixture_id':fixture_id,
        'field_basis':['1','sqrt(2)','sqrt(3)','sqrt(6)','sqrt(5)','sqrt(10)','sqrt(15)','sqrt(30)'],
        'variables':'24_SOURCE_CENTRE_FRAME_NODAL_U_V_W_RX_RY_RZ',
        'coefficient_records':records,
        'coefficient_count':len(records),
        'degree_counts':{'3':2600,'4':17550},
        'linear_physical_operator':[[x.coefficients() for x in row] for row in physical_energy],
        'zero_count':len(records)-nonzero_count,'nonzero_count':nonzero_count,
        'first_nonzero':first_nonzero,
        'frames':{'mixed':[[x.coefficients() for x in row] for row in mixed_frame],
                  'inherited':[[x.coefficients() for x in row] for row in centre_frame]},
        'stations':stations,
        'exact_checks':{'frame_orthogonality':True,'physical_director':True,
                        'positive_jacobians':True,'same_station_measures':True,
                        'stationary_symmetry':True,'stationary_solve_residual':True,
                        'degree_two_physical_energy_schur':True},
        'numerical_channels':'PL_AND_HOURGLASS_EXCLUDED_UNCHANGED_QUADRATIC',
        'physical_recovery_qualified':False,
        'universal_impossibility_claim':False,
    }
