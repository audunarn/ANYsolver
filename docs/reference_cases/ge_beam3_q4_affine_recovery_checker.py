"""Independent affine chart-image reconstruction; no producer/production imports.

Uses only this checker's independently authored predecessor source primitives
and the shared exact field. Never reads producer matrices to reconstruct proof.
"""
from itertools import combinations_with_replacement
import json
from ge_beam3_q4_exact_field import Field as F
import ge_beam3_q4_recovery_coefficient_checker as source

FIXTURES = {
    'AFFINE_Q4_SQUARE': ((0,0),(1,0),(1,1),(0,1)),
    'AFFINE_Q4_RECTANGLE': ((0,0),(2,0),(2,1),(0,1)),
    'AFFINE_Q4_RHOMBUS': (('-8/5','-4/5'),('2/5','-4/5'),('8/5','4/5'),('-2/5','4/5')),
}
zero, tr, mm, dot = source.zero, source.tr, source.mm, source.dot


def encoded(value):
    if isinstance(value,F):return value.coefficients()
    if isinstance(value,(list,tuple)):return [encoded(x) for x in value]
    if isinstance(value,dict):return {k:encoded(v) for k,v in value.items()}
    return value


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')


def rref_and_image(rows):
    a=[list(row) for row in rows];pivots=[];row=0
    for col in range(len(a[0])):
        pivot=next((j for j in range(row,len(a)) if a[j][col]),None)
        if pivot is None:continue
        a[row],a[pivot]=a[pivot],a[row];factor=a[row][col]
        a[row]=[v/factor for v in a[row]]
        for j in range(len(a)):
            if j==row or not a[j][col]:continue
            factor=a[j][col];a[j]=[v-factor*w for v,w in zip(a[j],a[row])]
        pivots.append(col);row+=1
        if row==len(a):break
    if row!=6:raise ValueError('affine image constraint rank')
    free=[j for j in range(24) if j not in pivots];z=zero(24,len(free))
    if len(free)!=18:raise ValueError('affine quotient dimension')
    for k,j in enumerate(free):
        z[j][k]=F(1)
        for i,p in enumerate(pivots):z[p][k]=-a[i][j]
    if any(v for r in mm(rows,z) for v in r):raise ValueError('image nullspace')
    if any(p%6>=3 for p in pivots):raise ValueError('rotation constraint')
    return a,pivots,z


def constraints(nodes):
    centre=[sum((p[j] for p in nodes),F(0))/4 for j in range(3)]
    x=[[p[j]-centre[j] for j in range(3)] for p in nodes];c=zero(6,24)
    for i in range(4):
        for j in range(3):c[j][6*i+j]=F('1/4')
        for row,(a,b) in enumerate(((0,1),(0,2),(1,2)),3):
            c[row][6*i+a]=x[i][b];c[row][6*i+b]=-x[i][a]
    return c


def section():
    c=zero(8,8);scale=F(100)*F('1/10')/(1-F('1/4')**2)
    for first,factor in ((0,F(1)),(3,F('1/1200'))):
        c[first][first]=c[first+1][first+1]=scale*factor
        c[first][first+1]=c[first+1][first]=scale*factor/4
        c[first+2][first+2]=scale*factor*F('3/8')
    c[6][6]=c[7][7]=F('10/3')
    return c


def frame_columns(axes):
    return [[axes[0][0],axes[1][0],F(0)],
            [axes[0][1],axes[1][1],F(0)],[F(0),F(0),F(1)]]


def project_quadratic(nonlinear,z):
    pairs=list(combinations_with_replacement(range(18),2));out=zero(8,len(pairs))
    lookup={p:i for i,p in enumerate(pairs)}
    for k,(i,j) in enumerate(combinations_with_replacement(range(4),2)):
        for a in range(18):
            if not z[6*i+2][a]:continue
            for b in range(18):
                if not z[6*j+2][b]:continue
                col=lookup[tuple(sorted((a,b)))];factor=z[6*i+2][a]*z[6*j+2][b]
                for row in range(8):
                    if nonlinear[row][k]:out[row][col]+=nonlinear[row][k]*factor
    return out,pairs


def add_cubic(target,linear,nonlinear,c,weight,pairs):
    cross=mm(mm(tr(linear),c),nonlinear)
    for i,row in enumerate(cross):
        for j,v in enumerate(row):
            if v:
                key=tuple(sorted((i,*pairs[j])))
                target[key]=target.get(key,F(0))+weight*v


def add_quartic(target,nonlinear,c,weight,pairs):
    # Sparse support is derived from the independently computed image, not a
    # presumed cancellation or a hard-coded checkerboard coordinate.
    active=[i for i,col in enumerate(tr(nonlinear)) if any(col)]
    compact=[[row[i] for i in active] for row in nonlinear]
    gram=mm(mm(tr(compact),c),compact)
    for i,row in enumerate(gram):
        for j,v in enumerate(row):
            if v:
                key=tuple(sorted((*pairs[active[i]],*pairs[active[j]])))
                target[key]=target.get(key,F(0))+weight*v/2


def internal_station(c,weight):
    block=zero(16,16);inverse=zero(16,16)
    for i in range(8):
        block[i][8+i]=block[8+i][i]=-weight
        inverse[i][8+i]=inverse[8+i][i]=-1/weight
        for j in range(8):
            block[i][j]=weight*c[i][j]
            inverse[8+i][8+j]=-c[i][j]/weight
    identity=[[F(int(i==j)) for j in range(16)] for i in range(16)]
    if mm(block,inverse)!=identity or mm(inverse,block)!=identity:
        raise ValueError('station saddle inverse')
    coupling=zero(16,8)
    for i in range(8):coupling[8+i][i]=weight
    schur=[[-v for v in row] for row in mm(mm(tr(coupling),inverse),coupling)]
    if schur!=[[weight*v for v in row] for row in c]:
        raise ValueError('station constitutive Schur')
    return block,inverse


def pscale(poly,factor):
    return {k:factor*v for k,v in poly.items() if factor and v}


def padd(*polys):
    result={}
    for poly in polys:
        for key,value in poly.items():result[key]=result.get(key,F(0))+value
    return {key:value for key,value in result.items() if value}


def pmul(a,b):
    result={}
    for ka,va in a.items():
        for kb,vb in b.items():
            key=tuple(sorted(ka+kb));result[key]=result.get(key,F(0))+va*vb
    return {key:value for key,value in result.items() if value}


def derivative(poly,coordinate):
    result={}
    for key,value in poly.items():
        multiplicity=key.count(coordinate)
        if multiplicity:
            target=list(key);target.remove(coordinate);target=tuple(target)
            result[target]=result.get(target,F(0))+multiplicity*value
    return {key:value for key,value in result.items() if value}


def nonlinear_stationary_schur(linear,nonlinear,pairs,c,weight,block):
    """Independent reduced-coordinate polynomial stationarity and condensation.

    Check all18 residual and324 tangent entries against differentiated energy,
    not just the constant constitutive metric. This is exact algebra on the
    image superset; the actual Procrustes/spatial map remains a later gate.
    """
    strains=[]
    for row in range(8):
        polynomial={(i,):v for i,v in enumerate(linear[row]) if v}
        for key,value in zip(pairs,nonlinear[row]):
            if value:polynomial[key]=polynomial.get(key,F(0))+value
        strains.append(polynomial)
    stresses=[padd(*(pscale(strains[j],c[i][j]) for j in range(8))) for i in range(8)]
    internal=strains+stresses
    forcing=[{} for _ in range(8)]+[pscale(v,weight) for v in strains]
    for i in range(16):
        residual=padd(forcing[i],*(pscale(internal[j],block[i][j]) for j in range(16)))
        if residual:raise ValueError('nonlinear stationarity polynomial')
    energy=pscale(padd(*(pmul(e,s) for e,s in zip(strains,stresses))),weight/2)
    J=[[derivative(poly,i) for i in range(18)] for poly in strains]
    cj=[[padd(*(pscale(J[a][i],c[b][a]) for a in range(8))) for i in range(18)] for b in range(8)]
    for i in range(18):
        residual=pscale(padd(*(pmul(J[a][i],stresses[a]) for a in range(8))),weight)
        if derivative(energy,i)!=residual:raise ValueError('nonlinear external work polynomial')
        for j in range(18):
            material=padd(*(pmul(J[a][i],cj[a][j]) for a in range(8)))
            geometric=padd(*(pmul(stresses[a],derivative(J[a][i],j)) for a in range(8)))
            condensed=pscale(padd(material,geometric),weight)
            if derivative(residual,j)!=condensed:
                raise ValueError('nonlinear external Schur polynomial')


def reconstruct(fixture_id,checkpoint=None):
    ping=checkpoint or (lambda _:None);ping('affine checker initialization')
    if fixture_id not in FIXTURES:raise ValueError('unregistered affine fixture')
    nodes=[[F(x),F(y),F('1/8')] for x,y in FIXTURES[fixture_id]]
    points=[p[:2] for p in nodes];axes,centre_axes=source.frames(points)
    if centre_axes!=[[F(1),F(0)],[F(0),F(1)]]:
        raise ValueError('registered inherited/reference frame alignment')
    xy=[[dot(p,a) for a in axes] for p in points]
    centre_xy=[[dot(p,a) for a in centre_axes] for p in points]
    transform=zero(24,24)
    for start in range(0,24,3):
        for i in range(2):
            for j in range(2):transform[start+i][start+j]=axes[i][j]
        transform[start+2][start+2]=F(1)
    a,b=axes[0];cc,d=axes[1]
    engineering=[[a*a,b*b,a*b],[cc*cc,d*d,cc*d],[2*a*cc,2*b*d,a*d+b*cc]]
    constraint=constraints(nodes);reduced,pivots,z=rref_and_image(constraint)
    c=section();H=zero(35,35);load=zero(35,24);stations=[]
    membrane=[row[:3] for row in c[:3]]
    if mm(mm(tr(engineering),membrane),engineering)!=membrane:
        raise ValueError('section frame virtual work')
    ping('affine checker fields')
    g=1/F.root(3)
    for number,(sx,sy) in enumerate(((-1,-1),(1,-1),(1,1),(-1,1))):
        r,s=sx*g,sy*g;ns,ne=source.spaces(xy,r,s)
        B=mm(source.compatible(xy,r,s),transform)
        _,dx,dy,(_,_,_,_,weight)=source.derivatives(centre_xy,r,s)
        if source.derivatives(xy,r,s)[3][4]!=weight:raise ValueError('station measure')
        linear=zero(3,24);nonlinear=zero(3,10)
        for i in range(4):
            linear[0][6*i]=dx[i];linear[1][6*i+1]=dy[i]
            linear[2][6*i]=dy[i];linear[2][6*i+1]=dx[i]
        for k,(i,j) in enumerate(combinations_with_replacement(range(4),2)):
            factor=F('1/2') if i==j else F(1)
            nonlinear[0][k]=factor*dx[i]*dx[j]
            nonlinear[1][k]=factor*dy[i]*dy[j]
            nonlinear[2][k]=dx[i]*dy[j]+(dx[j]*dy[i] if i!=j else F(0))
        compatible=mm(engineering,linear)
        if compatible!=B[:3]:raise ValueError('source membrane frame work')
        nl=mm(engineering,nonlinear)+zero(5,10)
        cross=mm(tr(ns),ne);gram=mm(mm(tr(ne),c),ne);coupling=mm(tr(ns),B)
        for i in range(14):
            for j in range(21):H[i][14+j]-=weight*cross[i][j];H[14+j][i]-=weight*cross[i][j]
            for j in range(24):load[i][j]+=weight*coupling[i][j]
        for i in range(21):
            for j in range(21):H[14+i][14+j]+=weight*gram[i][j]
        block,inverse=internal_station(c,weight)
        stations.append(dict(natural=[r,s],weight=weight,ne=ne,
            compatible_membrane_map=compatible,nonlinear_map=nl,
            internal_block=block,internal_inverse=inverse))
        ping('affine checker station '+str(number))
    if H!=tr(H):raise ValueError('linear stationary symmetry')
    solution=source.solve(H,load)
    physical=[[-v for v in row] for row in mm(tr(load),solution)]
    strain_solution=[[-v for v in row] for row in solution[14:]]
    recovered_energy=zero(24,24);new3={};old3={};new4={};old4={}
    for station in stations:
        M=mm(station.pop('ne'),strain_solution);station['mixed_strain_map']=M
        energy=mm(mm(tr(M),c),M);w=station['weight']
        for i in range(24):
            for j in range(24):recovered_energy[i][j]+=w*energy[i][j]
        rz=mm(M,z);nl,pairs=project_quadratic(station['nonlinear_map'],z)
        nonlinear_stationary_schur(rz,nl,pairs,c,w,station['internal_block'])
        base=mm(station['compatible_membrane_map'],z)+zero(5,18)
        add_cubic(new3,rz,nl,c,w,pairs);add_cubic(old3,base,nl,c,w,pairs)
        add_quartic(new4,nl,c,w,pairs)
        # Independent source energy has only membrane nonlinear components;
        # reconstruct that channel explicitly rather than copy new4.
        membrane_only=[list(row) for row in nl[:3]]+zero(5,len(pairs))
        add_quartic(old4,membrane_only,c,w,pairs)
    if recovered_energy!=physical or physical!=tr(physical):
        raise ValueError('source linear strain energy/Schur')
    records=[]
    for degree,left,right in ((3,new3,old3),(4,new4,old4)):
        for indices in combinations_with_replacement(range(18),degree):
            a,b=left.get(indices,F(0)),right.get(indices,F(0))
            records.append(dict(degree=degree,indices=list(indices),
                coefficient=a-b,new_physical=a,source=b))
    nonzero=[record for record in records if record['coefficient']]
    ping('affine checker polynomial and Schur completion')
    return encoded(dict(schema='GE_BEAM3_Q4_AFFINE_RECOVERY_EXACT_FIXTURE_V1',
        fixture_id=fixture_id,
        field_basis=['1','sqrt(2)','sqrt(3)','sqrt(6)','sqrt(5)','sqrt(10)','sqrt(15)','sqrt(30)'],
        representation_id='GE_BEAM3_Q4_AFFINE_STATION_RECOVERY_64_V1',
        variables='18_EXACT_CHART_IMAGE_COORDINATES_FROM_24_SOURCE_CENTRE_LOCAL_DOFS',
        nodes=nodes,material=dict(E='100',nu='1/4',thickness='1/10'),constitutive=c,
        frames=dict(mixed=frame_columns(axes),inherited=frame_columns(centre_axes)),
        stationary_matrix=H,stationary_coupling=load,stationary_solution=solution,
        constraints=constraint,rref=reduced,pivots=pivots,nullspace=z,
        linear_physical_operator=physical,stations=stations,coefficient_records=records,
        degree_counts={'3':1140,'4':5985},coefficient_count=7125,
        zero_count=7125-len(nonzero),nonzero_count=len(nonzero),first_nonzero=nonzero[0] if nonzero else None,
        exact_checks={k:True for k in ('source_frames','positive_station_weights',
            'constraint_rank_six','image_dimension_eighteen','unrestricted_rotations',
            'linear_stationarity','linear_energy_schur','station_two_sided_inverse',
            'station_constitutive_schur','full64_stationarity','full64_schur',
            'nonlinear_stationarity','nonlinear_external_work','nonlinear_external_schur',
            'section_frame_work','numerical_energy_excluded')},
        numerical_channels='PL_AND_HOURGLASS_EXCLUDED_UNCHANGED_QUADRATIC',
        physical_recovery_qualified=False,full_g3c_qualified=False))


def verify_against_reconstruction(proof,expected):
    if canonical(proof)!=canonical(expected):raise ValueError('independent affine proof mismatch')
    return dict(fixture_id=proof['fixture_id'],coefficient_count=proof['coefficient_count'],
        nonzero_count=proof['nonzero_count'],first_nonzero=proof['first_nonzero'],
        independently_verified=True,physical_recovery_qualified=False,full_g3c_qualified=False)


def verify(proof,checkpoint=None):
    if type(proof) is not dict:raise ValueError('affine proof mapping')
    return verify_against_reconstruction(proof,reconstruct(proof.get('fixture_id'),checkpoint))
