"""Exact affine chart-image producer, independently authored from source laws.

No production mechanics or checker import. Earlier helpers reused here were
authored by this producer author; checker shares only scalar exact arithmetic.
Execution, source binding and process limits belong to the reviewed runner.
"""
from itertools import combinations_with_replacement

from ge_beam3_q4_exact_field import Field, matmul, solve, transpose, zeros
from ge_beam3_q4_recovery_coefficient_producer import (
    PAIRS, SIGNS, _compatible, _engineering_transform, _frames, _geometry,
    _local_coordinates, _nonlinear_coefficients, _section, _source_fields,
)

FIXTURES = {
    'AFFINE_Q4_SQUARE': ((0,0),(1,0),(1,1),(0,1)),
    'AFFINE_Q4_RECTANGLE': ((0,0),(2,0),(2,1),(0,1)),
    'AFFINE_Q4_RHOMBUS': (('-8/5','-4/5'),('2/5','-4/5'),('8/5','4/5'),('-2/5','4/5')),
}


def encoded(matrix):
    return [[value.coefficients() for value in row] for row in matrix]


def _require_equal(left, right, label):
    if left != right:
        raise ArithmeticError(label)


def _constraints(nodes, centre_frame):
    origin = [sum((node[i] for node in nodes),Field(0))/4 for i in range(3)]
    relative = [[node[i]-origin[i] for i in range(3)] for node in nodes]
    local = matmul(relative,centre_frame)
    matrix = zeros(6,24)
    for node,(x,y,z) in enumerate(local):
        index = node*6
        for axis in range(3):
            matrix[axis][index+axis] = Field('1/4')
        matrix[3][index],matrix[3][index+1] = y,-x
        matrix[4][index],matrix[4][index+2] = z,-x
        matrix[5][index+1],matrix[5][index+2] = z,-y
    rref = [row[:] for row in matrix]
    pivots=[]
    for column in range(24):
        row=len(pivots)
        if row==6:break
        pivot=next((i for i in range(row,6) if rref[i][column]),None)
        if pivot is None:continue
        rref[row],rref[pivot]=rref[pivot],rref[row]
        inverse=rref[row][column].inverse()
        rref[row]=[value*inverse for value in rref[row]]
        for i in range(6):
            if i!=row:
                value=rref[i][column]
                rref[i]=[a-value*b for a,b in zip(rref[i],rref[row])]
        pivots.append(column)
    if len(pivots)!=6:
        raise ArithmeticError('affine image constraint rank is not six')
    free=[i for i in range(24) if i not in pivots]
    Z=zeros(24,18)
    for j,column in enumerate(free):
        Z[column][j]=Field(1)
        for row,pivot in enumerate(pivots):
            Z[pivot][j]=-rref[row][column]
    _require_equal(matmul(matrix,Z),zeros(6,18),'chart image membership')
    for column in [6*n+i for n in range(4) for i in (3,4,5)]:
        if column not in free:
            raise ArithmeticError('rotation incorrectly constrained')
        j=free.index(column)
        if any(Z[i][j] != int(i==column) for i in range(24)):
            raise ArithmeticError('rotation freedom was coupled to translations')
    return matrix,rref,pivots,Z


def _station_saddle(C,weight):
    block,inverse=zeros(16,16),zeros(16,16)
    coupling=zeros(16,8)
    solution=zeros(16,8)
    for i in range(8):
        block[i][8+i]=block[8+i][i]=-weight
        inverse[i][8+i]=inverse[8+i][i]=-1/weight
        coupling[8+i][i]=weight
        solution[i][i]=Field(1)
        for j in range(8):
            block[i][j]=weight*C[i][j]
            inverse[8+i][8+j]=-C[i][j]/weight
            solution[8+i][j]=C[i][j]
    identity=[[Field(int(i==j)) for j in range(16)] for i in range(16)]
    _require_equal(matmul(block,inverse),identity,'station right inverse')
    _require_equal(matmul(inverse,block),identity,'station left inverse')
    solved=matmul(block,solution)
    _require_equal(solved,[[-x for x in row] for row in coupling],'full station equilibrium')
    schur=matmul(matmul(transpose(coupling),inverse),coupling)
    _require_equal(schur,[[-weight*x for x in row] for row in C],'station Schur metric')
    return block,inverse,coupling,solution


def _restrict_quadratic(n,Z):
    """Eight strain polynomials in 18 variables; retain exact monomial factors."""
    result={}
    for column,(i,j) in enumerate(PAIRS):
        if not any(n[row][column] for row in range(8)):continue
        for a in range(18):
            if not Z[i][a]:continue
            for b in range(18):
                factor=Z[i][a]*Z[j][b]
                if not factor:continue
                key=tuple(sorted((a,b)))
                values=result.setdefault(key,[Field(0)]*8)
                for row in range(8):
                    values[row]+=n[row][column]*factor
    return {key:value for key,value in result.items() if any(value)}


def _energy_terms(M,n,C,weight,Z):
    linear=matmul(M,Z)
    quadratic=_restrict_quadratic(n,Z)
    cubic,quartic={},{}
    Clinear=matmul(C,linear)
    Cquadratic={key:[sum((C[i][j]*values[j] for j in range(8) if C[i][j] and values[j]),Field(0)) for i in range(8)]
                for key,values in quadratic.items()}
    for pair,values in quadratic.items():
        for variable in range(18):
            value=weight*sum((Clinear[i][variable]*values[i] for i in range(8) if Clinear[i][variable] and values[i]),Field(0))
            if value:
                key=tuple(sorted((variable,)+pair))
                cubic[key]=cubic.get(key,Field(0))+value
        for other,Cvalues in Cquadratic.items():
            value=weight*sum((values[i]*Cvalues[i] for i in range(8) if values[i] and Cvalues[i]),Field(0))/2
            if value:
                key=tuple(sorted(pair+other))
                quartic[key]=quartic.get(key,Field(0))+value
    return cubic,quartic


def _sum_polynomial(target,source):
    for key,value in source.items():target[key]=target.get(key,Field(0))+value


def _poly_clean(polynomial):
    return {key:value for key,value in polynomial.items() if value}


def _poly_add(left,right):
    result=left.copy()
    for key,value in right.items():result[key]=result.get(key,Field(0))+value
    return _poly_clean(result)


def _poly_scale(polynomial,factor):
    return {key:value*factor for key,value in polynomial.items() if value and factor}


def _poly_mul(left,right):
    result={}
    for left_key,left_value in left.items():
        for right_key,right_value in right.items():
            key=tuple(sorted(left_key+right_key))
            result[key]=result.get(key,Field(0))+left_value*right_value
    return _poly_clean(result)


def _poly_derivative(polynomial,variable):
    result={}
    for key,value in polynomial.items():
        multiplicity=key.count(variable)
        if multiplicity:
            shortened=list(key)
            shortened.remove(variable)
            result[tuple(shortened)]=value*multiplicity
    return result


def _polynomial_matvec(matrix,vector):
    result=[]
    for row in matrix:
        value={}
        for coefficient,polynomial in zip(row,vector):
            if coefficient:value=_poly_add(value,_poly_scale(polynomial,coefficient))
        result.append(value)
    return result


def _combine_schur_terms(material,geometric):
    """Keep the mandatory force-weighted term independently mutation-testable."""
    return _poly_add(material,geometric)


def _nonlinear_station_context(M,n,C,weight,Z,inverse):
    """Prepare checked exact station/work polynomials once, without any solve.

    Build the internal fields through the actual saddle inverse, rather than
    assign them F and C F and then label that assignment a stationary solve.
    The independent derivative path differentiates the scalar energy directly;
    the work path contracts J and the second field derivatives with resultants.
    """
    linear=matmul(M,Z)
    quadratic=_restrict_quadratic(n,Z)
    fields=[{(j,):linear[i][j] for j in range(18) if linear[i][j]} for i in range(8)]
    for pair,values in quadratic.items():
        for i,value in enumerate(values):
            if value:fields[i][pair]=value
    forcing=[{} for _ in range(8)]+[_poly_scale(value,-weight) for value in fields]
    internal=_polynomial_matvec(inverse,forcing)
    strains,resultants=internal[:8],internal[8:]
    _require_equal(strains,fields,'nonlinear stationary compatibility residual')
    _require_equal(_polynomial_matvec(C,strains),resultants,'nonlinear constitutive residual')
    energy={}
    for strain,resultant in zip(strains,resultants):
        energy=_poly_add(energy,_poly_scale(_poly_mul(strain,resultant),weight/2))
    J=[[_poly_derivative(field,j) for j in range(18)] for field in fields]
    work=[]
    for j in range(18):
        force={}
        for i in range(8):
            force=_poly_add(force,_poly_scale(_poly_mul(J[i][j],resultants[i]),weight))
        _require_equal(force,_poly_derivative(energy,j),'nonlinear external work coefficient')
        work.append(force)
    return {'fields':fields,'resultants':resultants,'energy':energy,'J':J,
            'work':work,'constitutive':C,'weight':weight}


def _nonlinear_hessian_terms(context,j,k):
    """Compute a selected actual material/geometric entry from checked context."""
    if not (0<=j<18 and 0<=k<18):
        raise ValueError('unregistered reduced coordinate')
    C,weight,J=context['constitutive'],context['weight'],context['J']
    resultants=context['resultants']
    material={}
    geometric={}
    for a in range(8):
        for b in range(8):
            if C[a][b]:
                material=_poly_add(material,_poly_scale(_poly_mul(J[a][j],J[b][k]),weight*C[a][b]))
        second=_poly_derivative(J[a][j],k)
        geometric=_poly_add(geometric,_poly_scale(_poly_mul(resultants[a],second),weight))
    return material,geometric


def _verify_nonlinear_hessian_entry(context,j,k):
    material,geometric=_nonlinear_hessian_terms(context,j,k)
    hessian=_combine_schur_terms(material,geometric)
    _require_equal(hessian,_poly_derivative(context['work'][j],k),'nonlinear external Schur coefficient')
    _require_equal(hessian,_poly_derivative(_poly_derivative(context['energy'],j),k),'energy second derivative coefficient')


def _nonlinear_station_work(M,n,C,weight,Z,inverse):
    """Verify all nonlinear entries; mutation tests can reuse prepared context."""
    context=_nonlinear_station_context(M,n,C,weight,Z,inverse)
    # Each of the 324 Hessian entries is checked as an exact polynomial. The
    # force-weighted second derivative is deliberately distinct from J^T C J.
    for j in range(18):
        for k in range(18):
            _verify_nonlinear_hessian_entry(context,j,k)


def audit(fixture_id,checkpoint=None):
    if fixture_id not in FIXTURES:
        raise ValueError('unregistered affine exact fixture')
    progress=checkpoint if checkpoint is not None else lambda label:None
    progress('initialization')
    nodes=[[Field(x),Field(y),Field('1/8')] for x,y in FIXTURES[fixture_id]]
    mixed,centre=_frames(nodes)
    local=_local_coordinates(nodes,mixed)
    inherited=_local_coordinates(nodes,centre)
    rotation=matmul(transpose(mixed),centre)
    dofmap=zeros(24,24)
    for block in range(8):
        for i in range(3):
            for j in range(3):dofmap[block*3+i][block*3+j]=rotation[i][j]
    strainmap=_engineering_transform(rotation)
    constraints,rref,pivots,Z=_constraints(nodes,centre)
    C=[[100*x for x in row] for row in _section()]
    membrane=[row[:3] for row in C[:3]]
    _require_equal(matmul(matmul(transpose(strainmap),membrane),strainmap),membrane,
                   'isotropic engineering frame work congruence')
    H,b0=zeros(35,35),zeros(35,24)
    retained=[]
    gauss=Field.root(3)/3
    progress('frames_constraints')
    for station,(ar,as_) in enumerate(SIGNS):
        r,s=ar*gauss,as_*gauss
        sigma,epsilon=_source_fields(local,r,s)
        B=matmul(_compatible(local,r,s),dofmap)
        _,_,_,weight,_=_geometry(local,r,s)
        _,dx,dy,sourceweight,_=_geometry(inherited,r,s)
        _require_equal(weight,sourceweight,'station measures differ')
        F=matmul(transpose(epsilon),sigma)
        gram=matmul(matmul(transpose(epsilon),C),epsilon)
        coupling=matmul(transpose(sigma),B)
        for i in range(21):
            for j in range(14):
                H[14+i][j]-=weight*F[i][j]
                H[j][14+i]-=weight*F[i][j]
            for j in range(21):H[14+i][14+j]+=weight*gram[i][j]
        for i in range(14):
            for j in range(24):b0[i][j]+=weight*coupling[i][j]
        bm=zeros(3,24)
        for i in range(4):
            bm[0][6*i],bm[1][6*i+1]=dx[i],dy[i]
            bm[2][6*i],bm[2][6*i+1]=dy[i],dx[i]
        compatible=matmul(strainmap,bm)
        n=matmul(strainmap,_nonlinear_coefficients(dx,dy))+zeros(5,len(PAIRS))
        internal,inverse,station_coupling,station_solution=_station_saddle(C,weight)
        retained.append((r,s,weight,epsilon,compatible,n,internal,inverse,station_coupling,station_solution))
        progress('station_'+str(station))
    _require_equal(H,transpose(H),'original stationary symmetry')
    progress('original_stationary_solve')
    solution=solve(H,b0)
    physical=[[-x for x in row] for row in matmul(transpose(b0),solution)]
    linear_energy=zeros(24,24)
    new3,new4,old3,old4={},{},{},{}
    stations=[]
    global_block,global_inverse=zeros(64,64),zeros(64,64)
    global_coupling,global_solution=zeros(64,32),zeros(64,32)
    global_metric=zeros(32,32)
    for index,(r,s,weight,epsilon,compatible,n,internal,inverse,scoupling,ssolution) in enumerate(retained):
        M=[[-x for x in row] for row in matmul(epsilon,solution[14:])]
        _nonlinear_station_work(M,n,C,weight,Z,inverse)
        energy=matmul(matmul(transpose(M),C),M)
        for i in range(24):
            for j in range(24):linear_energy[i][j]+=weight*energy[i][j]
        c3,c4=_energy_terms(M,n,C,weight,Z)
        s3,s4=_energy_terms(compatible+zeros(5,24),n,C,weight,Z)
        _sum_polynomial(new3,c3);_sum_polynomial(new4,c4)
        _sum_polynomial(old3,s3);_sum_polynomial(old4,s4)
        for i in range(16):
            for j in range(16):
                global_block[16*index+i][16*index+j]=internal[i][j]
                global_inverse[16*index+i][16*index+j]=inverse[i][j]
            for j in range(8):
                global_coupling[16*index+i][8*index+j]=scoupling[i][j]
                global_solution[16*index+i][8*index+j]=ssolution[i][j]
        for i in range(8):
            for j in range(8):global_metric[8*index+i][8*index+j]=weight*C[i][j]
        stations.append({'natural':[r.coefficients(),s.coefficients()], 'weight':weight.coefficients(),
                         'mixed_strain_map':encoded(M),'compatible_membrane_map':encoded(compatible),
                         'nonlinear_map':encoded(n),'internal_block':encoded(internal),'internal_inverse':encoded(inverse)})
        progress('energy_and_schur_station_'+str(index))
    _require_equal(physical,linear_energy,'source physical linear energy identity')
    # Assemble all four independent station blocks explicitly. The Schur metric
    # identity holds for arbitrary station derivatives, including actual J=M+Dn
    # and its common-chart pullback. Direct force-weighted second derivatives
    # remain in Kdd and are not replaced by this metric contraction.
    global_stationarity=matmul(global_block,global_solution)
    _require_equal(global_stationarity,[[-x for x in row] for row in global_coupling],'64-variable equilibrium')
    global_schur=matmul(matmul(transpose(global_coupling),global_inverse),global_coupling)
    _require_equal(global_schur,[[-x for x in row] for row in global_metric],'64-variable Schur identity')
    progress('complete_coefficient_inventory')
    records=[];nonzero=[]
    for degree,new,old in ((3,new3,old3),(4,new4,old4)):
        for indices in combinations_with_replacement(range(18),degree):
            a,b=new.get(indices,Field(0)),old.get(indices,Field(0))
            difference=a-b
            row={'degree':degree,'indices':list(indices),'coefficient':difference.coefficients(),
                 'new_physical':a.coefficients(),'source':b.coefficients()}
            records.append(row)
            if difference:nonzero.append(row)
    if len(records)!=7125:raise ArithmeticError('affine monomial coverage mismatch')
    progress('evidence_completion')
    return {'schema':'GE_BEAM3_Q4_AFFINE_RECOVERY_EXACT_FIXTURE_V1','fixture_id':fixture_id,
            'representation_id':'GE_BEAM3_Q4_AFFINE_STATION_RECOVERY_64_V1',
            'field_basis':['1','sqrt(2)','sqrt(3)','sqrt(6)','sqrt(5)','sqrt(10)','sqrt(15)','sqrt(30)'],
            'variables':'18_EXACT_CHART_IMAGE_COORDINATES_FROM_24_SOURCE_CENTRE_LOCAL_DOFS',
            'material':{'E':'100','nu':'1/4','thickness':'1/10'},'nodes':encoded(nodes),
            'frames':{'mixed':encoded(mixed),'inherited':encoded(centre)},'constitutive':encoded(C),
            'constraints':encoded(constraints),'rref':encoded(rref),'pivots':pivots,'nullspace':encoded(Z),
            'stationary_matrix':encoded(H),'stationary_coupling':encoded(b0),'stationary_solution':encoded(solution),
            'linear_physical_operator':encoded(physical),'stations':stations,
            'coefficient_records':records,'degree_counts':{'3':1140,'4':5985},'coefficient_count':7125,
            'zero_count':7125-len(nonzero),'nonzero_count':len(nonzero),'first_nonzero':nonzero[0] if nonzero else None,
            'exact_checks':{'source_frames':True,'positive_station_weights':True,
                            'constraint_rank_six':True,'image_dimension_eighteen':True,'unrestricted_rotations':True,
                            'linear_stationarity':True,'linear_energy_schur':True,
                            'station_two_sided_inverse':True,'station_constitutive_schur':True,
                            'nonlinear_stationarity':True,'nonlinear_external_work':True,
                            'nonlinear_external_schur':True,'section_frame_work':True,
                            'full64_stationarity':True,'full64_schur':True,'numerical_energy_excluded':True},
            'numerical_channels':'PL_AND_HOURGLASS_EXCLUDED_UNCHANGED_QUADRATIC',
            'physical_recovery_qualified':False,'full_g3c_qualified':False}
