"""Independent source-equation coefficient checker; no producer/mechanics import.

Authored from e4_pl_element._source_fields/_compatible/_stationary_blocks and
elements._nonlinear_geometry. Only exact scalar arithmetic is shared.
"""
from fractions import Fraction
from itertools import combinations_with_replacement
from math import isqrt
from ge_beam3_q4_exact_field import Field as F

FIXTURES = {
    'MO16_SQUARE_EXACT': [(-1,-1),(1,-1),(1,1),(-1,1)],
    'MO16_AFFINE_RHOMBUS_EXACT': [('-8/5','-4/5'),('2/5','-4/5'),('8/5','4/5'),('-2/5','4/5')],
}

def zero(m,n):return [[F(0) for _ in range(n)] for _ in range(m)]
def tr(a):return [list(x) for x in zip(*a)]
def dot(a,b):return sum((x*y for x,y in zip(a,b) if x and y),F(0))
def mm(a,b):return [[dot(row,col) for col in tr(b)] for row in a]

def root(q):
    """Independently verify the positive square root of a rational norm."""
    if any(q.c[1:]) or q.c[0]<=0:raise ValueError('unregistered norm')
    v=q.c[0];ans=F(1)
    for number,denominator in ((v.numerator,False),(v.denominator,True)):
        factor=F(1)
        for p in (2,3,5):
            count=0
            while number%p==0:number//=p;count+=1
            factor*=p**(count//2)
            if count%2:factor*=F.root(p)
        n=isqrt(number)
        if n*n!=number:raise ValueError('norm outside registered field')
        factor*=n
        ans=ans/factor if denominator else ans*factor
    if ans*ans!=q:raise ValueError('root identity')
    return ans

def unit(v):
    size=root(dot(v,v));return [x/size for x in v]

def frames(nodes):
    a=unit([nodes[2][i]-nodes[0][i] for i in range(2)])
    b=unit([nodes[1][i]-nodes[3][i] for i in range(2)])
    x=unit([a[i]+b[i] for i in range(2)])
    y=unit([a[i]-b[i] for i in range(2)])
    if dot(x,y)!=0 or x[0]*y[1]-x[1]*y[0]!=1:raise ValueError('frame orientation')
    centre_x=unit([sum((nodes[j][i]*s for j,s in enumerate((-1,1,1,-1))),F(0))/4 for i in range(2)])
    centre_y=[-centre_x[1],centre_x[0]]
    return [x,y],[centre_x,centre_y]

def shape(r,s):
    signs=((-1,-1),(1,-1),(1,1),(-1,1))
    return ([((1+a*r)*(1+b*s))/4 for a,b in signs],
            [a*(1+b*s)/4 for a,b in signs], [b*(1+a*r)/4 for a,b in signs])

def derivatives(xy,r,s):
    n,dr,ds=shape(r,s)
    xr,yr=[dot(dr,v) for v in tr(xy)];xs,ys=[dot(ds,v) for v in tr(xy)]
    det=xr*ys-xs*yr
    if any(det.c[1:]) or det.c[0]<=0:raise ValueError('Jacobian sign')
    return n,[(ys*a-yr*b)/det for a,b in zip(dr,ds)],[(xr*b-xs*a)/det for a,b in zip(dr,ds)],(xr,xs,yr,ys,det)

def natural(xy,r,s,direction):
    n,dr,ds=shape(r,s);dn=(dr,ds)[direction]
    dx,dy=[dot(dn,v) for v in tr(xy)];row=[F(0)]*24
    for i in range(4):row[6*i+2]=dn[i];row[6*i+3]=-dy*n[i];row[6*i+4]=dx*n[i]
    return row

def compatible(xy,r,s):
    n,dx,dy,j=derivatives(xy,r,s);b=zero(8,24)
    for i in range(4):
        k=6*i
        for row,col,value in ((0,k,dx[i]),(1,k+1,dy[i]),(2,k,dy[i]),(2,k+1,dx[i]),
                              (3,k+4,dx[i]),(4,k+3,-dy[i]),(5,k+4,dy[i]),(5,k+3,-dx[i])):b[row][col]=value
    xr,xs,yr,ys,det=j
    a=natural(xy,F(0),F(-1),0);c=natural(xy,F(0),F(1),0)
    d=natural(xy,F(-1),F(0),1);e=natural(xy,F(1),F(0),1)
    for i in range(24):
        br=((1-s)*a[i]+(1+s)*c[i])/2;bs=((1-r)*d[i]+(1+r)*e[i])/2
        b[6][i]=(ys*br-yr*bs)/det;b[7][i]=(xr*bs-xs*br)/det
    return b

def spaces(xy,r,s):
    _,_,_,(xr,xs,yr,ys,det)=derivatives(xy,F(0),F(0))
    # Both fixtures are affine; verify, do not assume, the absent shifts.
    mixed=[sum((xy[i][j]*v for i,v in enumerate((1,-1,1,-1))),F(0)) for j in range(2)]
    if any(mixed):raise ValueError('nonaffine fixture')
    stress=[[xr*xr,xs*xs,2*xr*xs],[yr*yr,ys*ys,2*yr*ys],[xr*yr,xs*ys,xr*ys+xs*yr]]
    strain=[[xr*xr,xs*xs,xr*xs],[yr*yr,ys*ys,yr*ys],[2*xr*yr,2*xs*ys,xr*ys+xs*yr]]
    ns=zero(8,14);ne=zero(8,21)
    for i in range(8):ns[i][i]=F(1);ne[i][i]=F(1)
    for first,column in ((0,8),(3,10)):
        for row in range(3):
            ns[first+row][column]=stress[row][0]*s;ns[first+row][column+1]=stress[row][1]*r
            ne[first+row][column]=strain[row][0]*s;ne[first+row][column+1]=strain[row][1]*r
    for a,out in ((ns,12),(ne,12)):
        a[6][out]=xr*s;a[6][out+1]=xs*r;a[7][out]=yr*s;a[7][out+1]=ys*r
    enrich=[[r,0,0,0,r*s,0,0],[0,s,0,0,0,r*s,0],[0,0,r,s,0,0,r*s]]
    enriched=mm(strain,enrich)
    for i in range(3):ne[i][14:]=enriched[i]
    return ns,ne

def solve(a,b):
    """Independent Gauss-Jordan elimination, checking every original equation."""
    n=len(a);w=[list(x)+list(y) for x,y in zip(a,b)]
    for k in range(n):
        pivot=next((j for j in range(k,n) if w[j][k]),None)
        if pivot is None:raise ValueError('singular stationary source')
        w[k],w[pivot]=w[pivot],w[k];v=w[k][k]
        w[k]=[x/v for x in w[k]]
        for i in range(n):
            if i==k or not w[i][k]:continue
            f=w[i][k];w[i]=[x-f*y for x,y in zip(w[i],w[k])]
    result=[row[n:] for row in w]
    if mm(a,result)!=b:raise ValueError('stationary solve residual')
    return result

def reconstruct(fixture_id,checkpoint=None):
    ping=checkpoint or (lambda _:None);ping('checker initialization')
    nodes=[[F(x) for x in row] for row in FIXTURES[fixture_id]]
    frame,centre=frames(nodes);xy=[[dot(v,axis) for axis in frame] for v in nodes]
    cy=[[dot(v,axis) for axis in centre] for v in nodes]
    rotation=[[dot(a,b) for b in centre] for a in frame]
    transform=zero(24,24)
    for first in range(0,24,3):
        for i in range(2):
            for j in range(2):transform[first+i][first+j]=rotation[i][j]
        transform[first+2][first+2]=F(1)
    a,b=rotation[0];c,d=rotation[1]
    engineering=[[a*a,b*b,a*b],[c*c,d*d,c*d],[2*a*c,2*b*d,a*d+b*c]]
    ping('checker frames')
    material=zero(8,8);membrane=F('1/10')/(1-F('1/4')*F('1/4'))
    for start,scale in ((0,F(1)),(3,F('1/1200'))):
        material[start][start]=material[start+1][start+1]=membrane*scale
        material[start][start+1]=material[start+1][start]=membrane*scale/4
        material[start+2][start+2]=membrane*scale*F('3/8')
    material[6][6]=material[7][7]=F('1/30')
    A=[row[:3] for row in material[:3]];H=zero(35,35);load=zero(35,24);quad=zero(35,10)
    pairs=list(combinations_with_replacement(range(4),2));source3={};source4={};stations=[]
    invsqrt=1/F.root(3)
    for station,(rs,ss) in enumerate(((-1,-1),(1,-1),(1,1),(-1,1))):
        r,s=rs*invsqrt,ss*invsqrt;ns,ne=spaces(xy,r,s)
        B=mm(compatible(xy,r,s),transform);n,dx,dy,(_,_,_,_,weight)=derivatives(cy,r,s)
        if derivatives(xy,r,s)[3][4]!=weight:raise ValueError('station measures')
        stations.append(dict(natural=[r.coefficients(),s.coefficients()],weight=weight.coefficients()))
        nonlinear=zero(3,10);linear=zero(3,24)
        for i in range(4):
            linear[0][6*i]=dx[i];linear[1][6*i+1]=dy[i]
            linear[2][6*i]=dy[i];linear[2][6*i+1]=dx[i]
        for k,(i,j) in enumerate(pairs):
            factor=F('1/2') if i==j else F(1)
            nonlinear[0][k]=factor*dx[i]*dx[j];nonlinear[1][k]=factor*dy[i]*dy[j]
            nonlinear[2][k]=dx[i]*dy[j]+(dx[j]*dy[i] if i!=j else F(0))
        inframe=mm(engineering,nonlinear)+zero(5,10)
        cross=mm(tr(ns),ne);gram=mm(mm(tr(ne),material),ne)
        stationload=mm(tr(ns),B);stationquad=mm(tr(ns),inframe)
        for i in range(14):
            for j in range(21):H[i][14+j]-=weight*cross[i][j];H[14+j][i]-=weight*cross[i][j]
            for j in range(24):load[i][j]+=weight*stationload[i][j]
            for j in range(10):quad[i][j]+=weight*stationquad[i][j]
        for i in range(21):
            for j in range(21):H[14+i][14+j]+=weight*gram[i][j]
        cubic=mm(mm(tr(linear),A),nonlinear);quartic=mm(mm(tr(nonlinear),A),nonlinear)
        for i in range(24):
            for j,p in enumerate(pairs):
                key=tuple(sorted((i,6*p[0]+2,6*p[1]+2)))
                source3[key]=source3.get(key,F(0))+weight*cubic[i][j]
        for i,p in enumerate(pairs):
            for j,q in enumerate(pairs):
                key=tuple(sorted(tuple(6*k+2 for k in (*p,*q))))
                source4[key]=source4.get(key,F(0))+weight*quartic[i][j]/2
        ping('checker station '+str(station))
    solved=solve(H,[x+y for x,y in zip(load,quad)]);j_solved=[row[24:] for row in solved]
    cross=mm(tr(load),j_solved);fourth=mm(tr(quad),j_solved);stationary3={};stationary4={}
    for i in range(24):
        for j,p in enumerate(pairs):
            key=tuple(sorted((i,6*p[0]+2,6*p[1]+2)))
            stationary3[key]=stationary3.get(key,F(0))-cross[i][j]
    for i,p in enumerate(pairs):
        for j,q in enumerate(pairs):
            key=tuple(sorted(tuple(6*k+2 for k in (*p,*q))))
            stationary4[key]=stationary4.get(key,F(0))-fourth[i][j]/2
    linear_condensed=mm(tr(load),[row[:24] for row in solved])
    if linear_condensed!=tr(linear_condensed):raise ValueError('degree two symmetry')
    strain_solution=[row[:24] for row in solved[14:]]
    energy_operator=mm(mm(tr(strain_solution),[row[14:] for row in H[14:]]),strain_solution)
    physical=[[-x for x in row] for row in linear_condensed]
    if energy_operator!=physical:raise ValueError('degree two energy/Schur identity')
    records=[]
    for degree,stationary,source in ((3,stationary3,source3),(4,stationary4,source4)):
        for indices in combinations_with_replacement(range(24),degree):
            left,right=stationary.get(indices,F(0)),source.get(indices,F(0))
            records.append(dict(degree=degree,indices=list(indices),coefficient=(left-right).coefficients(),
                                stationary=left.coefficients(),source=right.coefficients()))
    ping('checker coefficient completion')
    def full_frame(rows):
        return [[x.coefficients() for x in row] for row in
                [[rows[0][0],rows[1][0],F(0)],[rows[0][1],rows[1][1],F(0)],[F(0),F(0),F(1)]]]
    nonzero=[row for row in records if any(x!='0' for x in row['coefficient'])]
    return dict(schema='G3C_Q4_RETAINED_SPACE_COEFFICIENT_FIXTURE_V1',fixture_id=fixture_id,
        field_basis=['1','sqrt(2)','sqrt(3)','sqrt(6)','sqrt(5)','sqrt(10)','sqrt(15)','sqrt(30)'],
        variables='24_SOURCE_CENTRE_FRAME_NODAL_U_V_W_RX_RY_RZ',coefficient_records=records,
        coefficient_count=20150,degree_counts={'3':2600,'4':17550},zero_count=20150-len(nonzero),
        nonzero_count=len(nonzero),first_nonzero=nonzero[0] if nonzero else None,
        linear_physical_operator=[[x.coefficients() for x in row] for row in physical],
        frames=dict(mixed=full_frame(frame),inherited=full_frame(centre)),stations=stations,
        exact_checks={key:True for key in ('frame_orthogonality','physical_director','positive_jacobians',
            'same_station_measures','stationary_symmetry','stationary_solve_residual','degree_two_physical_energy_schur')},
        numerical_channels='PL_AND_HOURGLASS_EXCLUDED_UNCHANGED_QUADRATIC',
        physical_recovery_qualified=False,universal_impossibility_claim=False)

def verify(proof,checkpoint=None):
    if type(proof) is not dict or proof.get('fixture_id') not in FIXTURES:raise ValueError('fixture authority')
    expected=reconstruct(proof['fixture_id'],checkpoint)
    # Canonical encoding also distinguishes booleans from integers, unlike ==.
    import json
    encode=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
    if encode(proof)!=encode(expected):raise ValueError('independent proof disagreement')
    return dict(fixture_id=proof['fixture_id'],coefficient_count=20150,nonzero_count=expected['nonzero_count'],
                first_nonzero=expected['first_nonzero'],independently_verified=True,
                recovery_qualified=False,full_g3c_qualified=False)
