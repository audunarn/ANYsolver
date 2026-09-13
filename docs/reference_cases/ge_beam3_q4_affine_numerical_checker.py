"""Independent numerical source-equation and physical-work reconstruction.

Only NumPy, standard-library math and the independent analytic chart are used.
No producer/facade/public mechanics/recovery/cached matrices are imported.
"""
import math
import json
from hashlib import sha256
import numpy as np
import ge_beam3_q4_affine_increment_chart as chart

GAUSS = tuple((r/math.sqrt(3),s/math.sqrt(3)) for r,s in ((-1,-1),(1,-1),(1,1),(-1,1)))


def finite(value):
    a=np.asarray(value,dtype=float)
    if not np.isfinite(a).all(): raise ValueError('checker nonfinite array')
    return a


def unit(v):
    v=finite(v); norm=np.linalg.norm(v)
    if norm <= 0 or not math.isfinite(norm): raise ValueError('checker degenerate vector')
    return v/norm


def frames(nodes):
    a=unit(nodes[2]-nodes[0]); b=unit(nodes[1]-nodes[3])
    e=unit(a+b); f=unit(a-b); n=unit(np.cross(e,f))
    f=unit(np.cross(n,e)); e=unit(np.cross(f,n))
    numbered=np.column_stack((e,f,n))
    xr=(-nodes[0]+nodes[1]+nodes[2]-nodes[3])/4
    xs=(-nodes[0]-nodes[1]+nodes[2]+nodes[3])/4
    x=unit(xr); z=unit(np.cross(xr,xs)); y=unit(np.cross(z,x))
    return numbered,np.column_stack((x,y,z))


def transform(frame):
    return np.kron(np.eye(8),frame)


def shape(r,s):
    signs=((-1,-1),(1,-1),(1,1),(-1,1))
    return tuple(np.array(v) for v in zip(*[((1+a*r)*(1+b*s)/4,
                   a*(1+b*s)/4,b*(1+a*r)/4) for a,b in signs]))


def derivatives(xy,r,s):
    n,dr,ds=shape(r,s)
    xr,yr=dr@xy; xs,ys=ds@xy
    det=xr*ys-xs*yr
    if not math.isfinite(det) or det <= 0: raise ValueError('checker nonpositive station Jacobian')
    return n,(ys*dr-yr*ds)/det,(xr*ds-xs*dr)/det,(xr,xs,yr,ys,det)


def natural(xy,r,s,axis):
    n,dr,ds=shape(r,s); dn=(dr,ds)[axis]
    x,y=dn@xy; row=np.zeros(24)
    for i in range(4):
        row[6*i+2]=dn[i]; row[6*i+3]=-y*n[i]; row[6*i+4]=x*n[i]
    return row


def compatible(xy,r,s):
    _,dx,dy,(xr,xs,yr,ys,det)=derivatives(xy,r,s)
    B=np.zeros((8,24))
    for i in range(4):
        j=6*i
        B[0,j]=dx[i]; B[1,j+1]=dy[i]
        B[2,j]=dy[i]; B[2,j+1]=dx[i]
        B[3,j+4]=dx[i]; B[4,j+3]=-dy[i]
        B[5,j+4]=dy[i]; B[5,j+3]=-dx[i]
    br=(1-s)/2*natural(xy,0,-1,0)+(1+s)/2*natural(xy,0,1,0)
    bs=(1-r)/2*natural(xy,-1,0,1)+(1+r)/2*natural(xy,1,0,1)
    B[6]=(ys*br-yr*bs)/det; B[7]=(xr*bs-xs*br)/det
    return B


def spaces(xy,r,s):
    _,_,_,(xr,xs,yr,ys,jc)=derivatives(xy,0,0)
    xrs,yrs=(xy[0]-xy[1]+xy[2]-xy[3])/4
    jr=xr*yrs-xrs*yr; js=xrs*ys-xs*yrs
    rb=jr/(3*jc); sb=js/(3*jc)
    Ts=np.array([[xr*xr,xs*xs,2*xr*xs],[yr*yr,ys*ys,2*yr*ys],
                 [xr*yr,xs*ys,xr*ys+xs*yr]])
    Te=np.array([[xr*xr,xs*xs,xr*xs],[yr*yr,ys*ys,yr*ys],
                 [2*xr*yr,2*xs*ys,xr*ys+xs*yr]])
    ns=np.zeros((8,14)); ne=np.zeros((8,21))
    ns[:,:8]=np.eye(8); ne[:,:8]=np.eye(8)
    for start,column in ((0,8),(3,10)):
        ns[start:start+3,column]=Ts[:,0]*(s-sb)
        ns[start:start+3,column+1]=Ts[:,1]*(r-rb)
        ne[start:start+3,column]=Te[:,0]*(s-sb)
        ne[start:start+3,column+1]=Te[:,1]*(r-rb)
    shear=np.array([[xr*(s-sb),xs*(r-rb)],[yr*(s-sb),ys*(r-rb)]])
    ns[6:,12:14]=shear; ne[6:,12:14]=shear
    enrich=np.array([[r,0,0,0,r*s,0,0],[0,s,0,0,0,r*s,0],[0,0,r,s,0,0,r*s]])
    ne[:3,14:]=jc/derivatives(xy,r,s)[3][4]*(Te@enrich)
    return ns,ne


def section():
    C=np.zeros((8,8)); a=100*.1/(1-.25**2)
    for start,factor in ((0,1.),(3,.1**2/12)):
        C[start,start]=C[start+1,start+1]=a*factor
        C[start,start+1]=C[start+1,start]=a*factor*.25
        C[start+2,start+2]=100/(2*(1+.25))*.1*factor
    C[6,6]=C[7,7]=5/6*100/(2*(1+.25))*.1
    return C


def engineering_map(to_frame,from_frame):
    O=to_frame.T@from_frame
    a,b=O[0,:2]; c,d=O[1,:2]
    return np.array([[a*a,b*b,a*b],[c*c,d*d,c*d],[2*a*c,2*b*d,a*d+b*c]])


def reference_operators(coordinates):
    nodes=finite(coordinates)
    if nodes.shape != (4,3): raise ValueError('checker reference topology')
    frame,centre=frames(nodes)
    xy=(nodes-nodes.mean(axis=0))@frame[:,:2]
    cy=nodes@centre[:,:2]
    T=transform(frame); T0=transform(centre)
    C=section(); H=np.zeros((35,35)); load=np.zeros((35,24))
    E=engineering_map(frame,centre)
    data=[]
    for r,s in GAUSS:
        Ns,Ne=spaces(xy,r,s); B=compatible(xy,r,s)@T.T
        N,dx,dy,(_,_,_,_,w0)=derivatives(cy,r,s)
        weight=derivatives(xy,r,s)[3][4]
        coupling=Ns.T@Ne
        H[:14,14:] -= weight*coupling
        H[14:,:14] -= weight*coupling.T
        H[14:,14:] += weight*(Ne.T@C@Ne)
        load[:14] += weight*(Ns.T@B)
        Gw=np.zeros((2,24)); Gw[0,2::6]=dx; Gw[1,2::6]=dy
        G=Gw@T0.T
        second=np.zeros((8,24,24))
        v=np.array([np.outer(G[0],G[0]),np.outer(G[1],G[1]),
                    np.outer(G[0],G[1])+np.outer(G[1],G[0])])
        second[:3]=np.einsum('ab,bij->aij',E,v)
        Bm=np.zeros((3,24))
        Bm[0,0::6]=dx; Bm[1,1::6]=dy
        Bm[2,0::6]=dy; Bm[2,1::6]=dx
        data.append(dict(N=N,weight=weight,source_weight=w0,Ne=Ne,Ns=Ns,B=B,
                         compatible_membrane=E@Bm@T0.T,nonlinear_hessians=second))
    balance=np.sqrt(np.max(np.abs(H),axis=1))
    if np.any(balance <= 0): raise ValueError('checker stationary zero row')
    scaled=H/balance[:,None]/balance[None,:]
    solution=np.linalg.solve(scaled,load/balance[:,None])/balance[:,None]
    if relative_error(scaled@(solution*balance[:,None]),load/balance[:,None]) > 1e-11:
        raise ValueError('checker actual stationary equation failed')
    for station in data: station['M']=-station['Ne']@solution[14:]
    M=np.array([row['M'] for row in data]); weights=np.array([row['weight'] for row in data])
    K=sum(w*m.T@C@m for w,m in zip(weights,M))
    if relative_error(K,-load.T@solution) > 1e-11:
        raise ValueError('checker actual linear energy-Schur identity failed')
    return dict(frame=frame,centre_frame=centre,C=C,Hsource=H,source_load=load,
                source_solution=solution,M=M,weights=weights,natural=np.array(GAUSS),
                reference_positions=np.array([row['N']@nodes for row in data]),
                compatible_membrane=np.array([row['compatible_membrane'] for row in data]),
                nonlinear_hessians=np.array([row['nonlinear_hessians'] for row in data]),
                Kphysical=K,Kstationary=-load.T@solution,source_residual=H@solution-load,
                shape=np.array([row['N'] for row in data]),
                source_weights=np.array([row['source_weight'] for row in data]))


def physical_fields(strains,resultants,frame,R,normal,polarity):
    director=polarity*unit(normal)
    sigma=1 if frame[:,2]@director > 0 else -1
    Q=frame@np.diag([1.,sigma,sigma])
    signs=np.array([1.,1.,sigma,sigma,sigma,1.,sigma,1.])
    e=strains*signs; s=resultants*signs
    out=dict(physical_strains=e,physical_resultants=s,physical_frame=Q)
    for key,rows,first,factor in (
        ('membrane_strain_tensor',e,0,.5),('curvature_tensor',e,3,.5),
        ('membrane_resultant_tensor',s,0,1.),('moment_tensor',s,3,1.)):
        tensors=[]
        for row in rows:
            a,b,c=row[first:first+3]
            tensor=np.array([[a,factor*c,0],[factor*c,b,0],[0,0,0]])
            tensors.append(Q@tensor@Q.T)
        out['reference_'+key]=np.array(tensors)
        out['current_'+key]=np.array([R@v@R.T for v in tensors])
    for key,rows in (('shear_strain',e),('shear_resultant',s)):
        vectors=rows[:,6:]@Q[:,:2].T
        out['reference_'+key]=vectors; out['current_'+key]=vectors@R.T
    return out


def evaluate(coordinates,q,accepted,*,normal=None,material_direction=None,director_polarity=1):
    q=finite(q)
    op=reference_operators(coordinates)
    kin=chart.evaluate(coordinates,q,accepted)
    d,D,D2=kin['d'],kin['D'],kin['D2']; C=op['C']
    ns=op['nonlinear_hessians']
    nonlinear=.5*np.einsum('gaij,i,j->ga',ns,d,d)
    gradient=np.einsum('gaij,j->gai',ns,d)
    local_J=op['M']+gradient
    strains=np.einsum('gai,i->ga',op['M'],d)+nonlinear
    resultants=strains@C.T
    J=np.einsum('gai,ij->gaj',local_J,D)
    seconds=np.einsum('ij,gaik,kl->gajl',D,ns,D)+np.einsum('gai,ijk->gajk',local_J,D2)
    force=np.einsum('g,gai,ga->i',op['weights'],J,resultants)
    hessian=np.einsum('g,gai,ab,gbj->ij',op['weights'],J,C,J)
    hessian+=np.einsum('g,ga,gaij->ij',op['weights'],resultants,seconds)
    energy=.5*np.einsum('g,ga,ga->',op['weights'],strains,resultants)
    # Independent unchanged-potential expansion, not a relabeled new-resultant sum.
    old_energy=.5*d@op['Kphysical']@d
    old_f=op['Kphysical']@d; old_k=op['Kphysical'].copy()
    A=C[:3,:3]
    for weight,B,n,G,N2 in zip(op['source_weights'],op['compatible_membrane'],
                               nonlinear[:,:3],gradient[:,:3],ns[:,:3]):
        linear=B@d; stress=A@(linear+n)
        old_energy+=weight*(linear@A@n+.5*n@A@n)
        old_f+=weight*(B.T@A@n+G.T@stress)
        old_k+=weight*(B.T@A@G+G.T@A@B+G.T@A@G+np.einsum('a,aij->ij',stress,N2))
    old_g=D.T@old_f
    old_H=D.T@old_k@D+np.einsum('i,ijk->jk',old_f,D2)
    r,sp,P,connection=chart.spatial_work(q,force,hessian)
    block=np.block([[C,-np.eye(8)],[-np.eye(8),np.zeros((8,8))]])
    inverse=np.block([[np.zeros((8,8)),-np.eye(8)],[-np.eye(8),-C]])
    Hii=np.zeros((64,64)); Hii_inverse=np.zeros((64,64)); Hqi=np.zeros((24,64))
    Hqq=np.zeros((24,24)); internal_residual=[]
    for g,w in enumerate(op['weights']):
        sl=slice(16*g,16*g+16)
        Hii[sl,sl]=w*block; Hii_inverse[sl,sl]=inverse/w
        Hqi[:,16*g+8:16*g+16]=w*J[g].T
        Hqq+=w*np.einsum('a,aij->ij',resultants[g],seconds[g])
        internal_residual.extend(w*np.concatenate((C@strains[g]-resultants[g],
                         op['M'][g]@d+nonlinear[g]-strains[g])))
    op.update(kin)
    op.update(strains=strains,resultants=resultants,nonlinear=nonlinear,local_J=local_J,
        physical_energy=float(energy),physical_force=force,physical_hessian=hessian,
        source_physical_energy=float(old_energy),source_local_physical_force=old_f,
        source_local_physical_tangent=old_k,source_physical_force=old_g,
        source_physical_hessian=old_H,phi_energy=float(energy-old_energy),
        phi_force=force-old_g,phi_hessian=hessian-old_H,
        physical_spatial_force=r,physical_spatial_row_tangent=sp,
        P=P,connection=connection,station_J=J,station_second=seconds,
        station_internal=np.array([w*block for w in op['weights']]),
        station_inverse=np.array([inverse/w for w in op['weights']]),
        station_state=np.concatenate((strains,resultants),axis=1),
        full_internal=Hii,full_internal_inverse=Hii_inverse,full_coupling=Hqi,
        full_external_fixed=Hqq,full_internal_residual=np.array(internal_residual),
        full_condensed=Hqq-Hqi@Hii_inverse@Hqi.T,
        current_positions=op['shape']@kin['x'])
    op.update(physical_fields(strains,resultants,op['frame'],kin['R'],
                             op['frame'][:,2] if normal is None else normal,director_polarity))
    if relative_error(Hii@Hii_inverse,np.eye(64)) > 1e-11 or relative_error(Hii_inverse@Hii,np.eye(64)) > 1e-11:
        raise ValueError('checker actual two-sided 64 inverse failed')
    if relative_error(physical_scaled('physical_hessian',op['full_condensed'],coordinates),
                      physical_scaled('physical_hessian',hessian,coordinates)) > 1e-11:
        raise ValueError('checker actual full external-internal Schur failed')
    return op


def relative_error(actual,expected):
    a,b=finite(actual),finite(expected)
    if a.shape != b.shape: raise ValueError('checker comparison shape')
    peak=max(float(np.max(np.abs(a),initial=0)),float(np.max(np.abs(b),initial=0)))
    if peak == 0: return 0.
    an,bn=a/peak,b/peak
    return float(np.linalg.norm(an-bn)/max(np.linalg.norm(an),np.linalg.norm(bn)))


CONTRADICTION_FIELDS=frozenset(('strains','resultants','physical_energy','physical_force',
                              'physical_hessian','station_J','station_second',
                              'source_physical_energy','source_physical_force','source_physical_hessian'))


def physical_scaled(name,value,coordinates):
    name=name.removeprefix('source_')
    X=finite(coordinates)
    L=max(np.linalg.norm(X[(i+1)%4]-X[i]) for i in range(4))
    if not math.isfinite(L) or L <= 0: raise ValueError('checker physical scale')
    u=np.tile([L,L,L,1.,1.,1.],4)
    e=np.array([1.,1.,1.,L,L,L,1.,1.])
    a=finite(value)
    if name == 'physical_force': return a*u
    if name == 'physical_hessian': return a*u[:,None]*u[None,:]
    if name == 'strains': return a*e
    if name == 'resultants': return a/e
    if name == 'station_J': return a*e[None,:,None]*u[None,None,:]
    if name == 'station_second': return a*e[None,:,None,None]*u[None,None,:,None]*u[None,None,None,:]
    if name == 'physical_energy': return a
    raise ValueError('checker unknown physical scale')


def verify_contradiction(payload):
    """Reconstruct a supported complete numerical discrepancy, never a crash flag.

    Runner authority separately binds the actual recorded candidate evaluation.
    This verifier cannot authenticate an arbitrary caller's invented actual data.
    """
    required={'schema','predicate','coordinates','q','accepted','normal',
              'material_direction','director_polarity','actual','tolerance','scale_mode',
              'source_identity','candidate_identity','fixture_identity',
              'node','table','row_id','state_sha256'}
    if type(payload) is not dict or set(payload) != required:
        raise ValueError('checker contradiction schema')
    if payload['schema'] != 'Q4_AFFINE_NUMERICAL_CONTRADICTION_V1':
        raise ValueError('checker contradiction identity')
    name=payload['predicate']
    if name not in CONTRADICTION_FIELDS or payload['tolerance'] != 1e-11:
        raise ValueError('checker unregistered physical predicate')
    if payload['scale_mode'] != 'REFERENCE_EDGE_NONDIMENSIONAL_V1':
        raise ValueError('checker unregistered physical scale')
    for key in ('source_identity','candidate_identity','fixture_identity','node','table','row_id'):
        if type(payload[key]) is not str or not payload[key]: raise ValueError('checker missing identity')
    state=dict(construction_id=payload['fixture_identity'],coordinates=payload['coordinates'],
               q=payload['q'],accepted=payload['accepted'],normal=payload['normal'],
               material_direction=payload['material_direction'],director_polarity=payload['director_polarity'])
    state_sha=sha256(canonical(state)).hexdigest()
    if payload['state_sha256'] != state_sha: raise ValueError('checker observation hash mismatch')
    if np.array_equal(finite(payload['q']),np.zeros(24)) and np.array_equal(finite(payload['accepted']),np.tile(np.eye(3),(4,1,1))):
        raise ValueError('zero-state evidence requires separate tangent-reference scale review')
    expected=evaluate(payload['coordinates'],payload['q'],payload['accepted'],
        normal=payload['normal'],material_direction=payload['material_direction'],
        director_polarity=payload['director_polarity'])
    # These predicates compare the actual OLD source potential to independent
    # constitutive recovery; they must not compare the old potential to itself.
    target=name.removeprefix('source_')
    error=relative_error(physical_scaled(target,payload['actual'],payload['coordinates']),
                         physical_scaled(target,expected[target],payload['coordinates']))
    if error <= 1e-11: raise ValueError('checker claimed contradiction is absent')
    return dict(accepted=True,predicate=name,relative_error=error,
                node=payload['node'],table=payload['table'],row_id=payload['row_id'],
                fixture_identity=payload['fixture_identity'],
                payload_sha256=sha256(canonical(payload)).hexdigest(),state_sha256=state_sha,
                actual=array_digest(payload['actual']),expected=array_digest(expected[target]))


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')


def array_digest(value):
    a=finite(value)
    return dict(shape=list(a.shape),sha256=sha256(a.astype('<f8',copy=False).tobytes()).hexdigest())
