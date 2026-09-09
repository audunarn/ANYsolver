"""Saved modal-work decomposition; no equilibrium or eigensolver calls."""
from decimal import Decimal as D,localcontext
from math import isfinite
from time import monotonic

def work_record(material,geometric,mass,eigenvalue):
    values=(material,geometric,mass,eigenvalue)
    if any(not isfinite(float(x)) for x in values) or material<=0 or mass<=0 or eigenvalue==0:
        raise ValueError('finite positive material/physical kinetic work')
    total=material+geometric
    if total==0:raise ValueError('registered nonzero signed modes')
    return dict(material_per_mass=float(material/mass),geometric_per_mass=float(geometric/mass),
        total_per_mass=float(total/mass),physical_mass=float(mass),
        cancellation_ratio=float((abs(material)+abs(geometric))/abs(total)),
        eigenvalue=float(eigenvalue),
        relative_rayleigh_error=float(abs(total/mass/eigenvalue-1)))

def factor_work(ll,rr,gg,bb,q,check=lambda:None):
    def mv(rows,x):
        result=[]
        for row in rows:
            check();result.append(sum((v*x[j] for j,v in row.items()),D(0)))
        return result
    f=mv(ll,mv(rr,q));b=mv(bb,q);g=mv(gg,q)
    return (sum((x*x for x in f),D(0)),sum((a*b for a,b in zip(q,g)),D(0)),
            sum((x*x for x in b),D(0)))

def native(packet,spectrum,progress=lambda row:None):
    from docs.reference_cases.ge_beam3_spatial_physical_pencil import matrix
    start=monotonic()
    def check():
        if monotonic()-start>120:raise ValueError('saved native modal work 120second bound')
    n=len(packet['geometric']);link=len(packet['right'])
    if n!=438 or len(spectrum['full_modes'])!=6 or len(spectrum['eigenvalues'])!=6:
        raise ValueError('registered native six-mode inventory')
    with localcontext() as ctx:
        ctx.prec=80
        ll=matrix(packet['left'],link);rr=matrix(packet['right'],n)
        gg=matrix(packet['geometric'],n);bb=matrix(packet['kinetic'],n)
        rows=[]
        for mode,(values,eig) in enumerate(zip(spectrum['full_modes'],spectrum['eigenvalues'])):
            if len(values)!=n or any(type(v) is not float or not isfinite(v) for v in values):
                raise ValueError('full native mode')
            q=[D.from_float(v) for v in values]
            material,geometric,mass=factor_work(ll,rr,gg,bb,q,check)
            row=work_record(material,geometric,mass,D.from_float(eig))
            if row['relative_rayleigh_error']>1e-11:raise ValueError('original factor modal work')
            rows.append(row);progress(dict(stage='native-modal-work',mode=mode))
    return rows

def reference(value,profile,progress=lambda row:None):
    import numpy as np
    from docs.reference_cases.ge_beam3_spatial_next_reference import unpack
    from docs.reference_cases.ge_beam3_spatial_continuum import matrix
    from docs.reference_cases.ge_beam3_spatial_second_variation import blocks
    from docs.reference_cases.ge_beam3_piecewise_physical_reference import local_basis
    from docs.reference_cases.ge_beam3_spatial_physical_reference import density
    if profile['quadrature']!=128 or profile['bubbles_per_segment']!=12:raise ValueError('frozen finest reference')
    start=monotonic();poly=unpack(value['polynomial']);c=np.diag([1000.,400.,400.,.02,.01,.02])
    modes=np.asarray(profile['result']['full_modes']).T
    if modes.shape!=(306,6):raise ValueError('all six finest polynomial modes')
    hm=np.zeros((306,306));hg=np.zeros_like(hm);mass=np.zeros_like(hm)
    direct_m=np.zeros(6);direct_g=np.zeros(6);direct_b=np.zeros(6)
    points,weights=np.polynomial.legendre.leggauss(128)
    for segment in range(4):
        for t,w in zip(points,weights):
            if monotonic()-start>120:raise ValueError('reference modal work 120second bound')
            u=(t+1)/2;x=-1.+.5*segment+.5*u;jac=float(np.sqrt(1+.04*x*x))
            y=poly(u)[13*segment:13*(segment+1)];r=matrix(y[3:7]);n=y[7:10];m=y[10:13]
            strain=(r.T@n)/np.diag(c)[:3];v=r@(np.array([1.,0.,0.])+strain)
            q,dq=local_basis(segment,t,jac,12);d,b,f=blocks(r,c,v,n,m)
            dm,bm,fm=blocks(r,c,v,np.zeros(3),np.zeros(3))
            hmat=dq.T@dm@dq+dq.T@bm@q+q.T@bm.T@dq+q.T@fm@q
            hgeo=dq.T@(b-bm)@q+q.T@(b-bm).T@dq+q.T@(f-fm)@q
            metric=density(r);measure=float(w*.25*jac)
            hm+=measure*hmat;hg+=measure*hgeo;mass+=measure*q.T@metric@q
            fields=q@modes;derivatives=dq@modes
            for i in range(6):
                theta=fields[3:,i];du=derivatives[:3,i];dt=derivatives[3:,i]
                first=np.r_[r.T@(du-np.cross(theta,v)),r.T@dt]
                direct_m[i]+=measure*(first@c@first)
                direct_g[i]+=measure*(n@(np.cross(theta,np.cross(theta,v))-2*np.cross(theta,du))-m@np.cross(theta,dt))
                direct_b[i]+=measure*(fields[:,i]@metric@fields[:,i])
        progress(dict(stage='reference-work-segment',segment=segment))
    saved_h=np.array(profile['raw_quadrature_hessian']);saved_m=np.array(profile['raw_quadrature_mass'])
    herr=float(np.max(abs(hm+hg-saved_h))/(1+np.max(abs(saved_h))))
    merr=float(np.max(abs(mass-saved_m))/(1+np.max(abs(saved_m))))
    if max(herr,merr)>1e-11:raise ValueError('decomposition reconstructs original trial matrices')
    rows=[];density_error=0.
    for i,eig in enumerate(profile['result']['eigenvalues']):
        q=modes[:,i];material=float(q@hm@q);geometric=float(q@hg@q);kinetic=float(q@mass@q)
        error=max(abs(material-direct_m[i]),abs(geometric-direct_g[i]),abs(kinetic-direct_b[i]))/(1+abs(material)+abs(geometric)+abs(kinetic))
        density_error=max(density_error,error)
        if error>1e-11:raise ValueError('independent cross-product modal work')
        row=work_record(material,geometric,kinetic,eig)
        # Saved rounded-matrix versus separately accumulated modal Rayleigh error is
        # diagnostic, not a new eigenanalysis or a substituted acceptance tolerance.
        row['saved_hessian_rayleigh']=float(q@saved_h@q/(q@saved_m@q))
        rows.append(row)
    return dict(rows=rows,hessian_reconstruction_error=herr,mass_reconstruction_error=merr,
        direct_density_error=density_error)

def differences(native_rows,reference_rows):
    if len(native_rows)!=6 or len(reference_rows)!=6:raise ValueError('six-mode decomposition comparison')
    rows=[]
    for i,(n,r) in enumerate(zip(native_rows,reference_rows)):
        dm=n['material_per_mass']-r['material_per_mass'];dg=n['geometric_per_mass']-r['geometric_per_mass']
        dt=n['total_per_mass']-r['total_per_mass']
        if abs(dm+dg-dt)>1e-11*(1+abs(dm)+abs(dg)):raise ValueError('additive modal work difference')
        rows.append(dict(mode=i,material_difference=dm,geometric_difference=dg,total_difference=dt,
            reference_total=r['total_per_mass'],native_total=n['total_per_mass']))
    return rows
