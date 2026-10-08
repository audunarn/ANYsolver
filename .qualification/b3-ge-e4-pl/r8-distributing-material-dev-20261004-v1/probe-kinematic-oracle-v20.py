"""Separate unchanged Q4 local update from its spatial pullback at saved state."""
from pathlib import Path
import hashlib,json,os,sys
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_ge_finite_experimental import _State
from anysolver._ge_beam3_variational_shell import deformation
from anysolver._stiffened_shell_algorithmic_pullback import spatial_response
from anysolver._ge_beam3_pose_joint import _exp_terms
from test_stiffened_shell_ge_distributing_material import definition
ROOT=Path(__file__).resolve().parent
assert Path(ss.__file__).resolve().is_relative_to(ROOT/'site')
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
owner=ss.create_analysis(definition=definition())
try:
    prefix=(ROOT/'failed-prefix-v9.bin').read_bytes();owner.restore(prefix)
    driver=owner._finite_driver
    with np.load(ROOT/'failed-base-v9.npz') as data:
        state=_State(*(data[name].copy() for name in ('q','frames','cells','resultants','multipliers')))
        direction=data['direction'].copy()
    assert state.shell_anchors is None
    prepared=[];size=owner._K.shape[0]
    predicted_material=np.zeros(size);predicted_total=np.zeros(size)
    def scatter(target,slots,value):np.add.at(target,slots,value)
    for (eid,element,slots,_),origin in zip(owner._shell_parts,driver._shell_origins):
        reference=np.array([owner._shell_model.mesh.nodes[node].coords() for node in element.node_ids])
        u=state.q[slots];vector=direction[slots]
        local,differential,second=deformation(reference,u,stable_translation=True)
        material=owner._shell_model.get_material(element.material_name)
        def update(values,element=element,material=material,origin=origin,eid=eid):
            prepared=driver._q4_corrections.get(eid)
            if prepared is None:
                return element.compute_nonlinear_response(owner._shell_model.mesh,material,values,origin,3,True)
            return element._compute_prepared_nonlinear_response(owner._shell_model.mesh,material,
                values,origin,3,True,prepared=prepared)
        force,tangent,candidate=update(local)
        chart=np.eye(24)
        for node,row in enumerate(u.reshape(-1,6)):
            chart[6*node+3:6*node+6,6*node+3:6*node+6]=_exp_terms(row[3:])[1]
        rowmap=np.linalg.solve(chart.T,differential.T)
        dl=differential@vector
        scatter(predicted_material,slots,rowmap@tangent@dl)
        scatter(predicted_total,slots,spatial_response(u,force,tangent,differential,second)[1]@vector)
        prepared.append((slots,reference,u,vector,local,dl,force,tangent,rowmap,update,origin,candidate))
    rows=owner._free;weights=owner._coordinate_scale[rows]
    from decimal import Decimal, localcontext
    def dec(x):return Decimal.from_float(float(x))
    def mm(a,b):return [[sum((x*y for x,y in zip(row,col)),Decimal(0)) for col in zip(*b)] for row in a]
    def tr(a):return list(map(list,zip(*a)))
    def eye(n):return [[Decimal(int(i==j)) for j in range(n)] for i in range(n)]
    def solve(a,b):
        a=[list(row)+[value] for row,value in zip(a,b)];n=len(b)
        for i in range(n):
            pivot=max(range(i,n),key=lambda j:abs(a[j][i]));a[i],a[pivot]=a[pivot],a[i]
            z=a[i][i];assert z
            a[i]=[v/z for v in a[i]]
            for j in range(n):
                if j!=i:
                    z=a[j][i];a[j]=[v-z*w for v,w in zip(a[j],a[i])]
        return [row[-1] for row in a]
    def kinematics(reference,values):
        ref=[[dec(v) for v in row] for row in reference]
        u=[list(values[i:i+6]) for i in range(0,len(values),6)];n=len(ref)
        rc=[[r[j]-sum((v[j] for v in ref),Decimal(0))/n for j in range(3)] for r in ref]
        xc=[[r[j]+v[j] for j in range(3)] for r,v in zip(rc,u)]
        xc=[[r[j]-sum((v[j] for v in xc),Decimal(0))/n for j in range(3)] for r in xc]
        c=mm(tr(xc),rc);trace=sum((c[i][i] for i in range(3)),Decimal(0))
        z=[c[2][1]-c[1][2],c[0][2]-c[2][0],c[1][0]-c[0][1]]
        m=[[trace]+z]+[[z[i]]+[c[i][j]+c[j][i]-trace*int(i==j) for j in range(3)] for i in range(3)]
        eig,q=np.linalg.eigh(np.array(m,dtype=float));pivot=int(np.argmax(abs(q[:,-1])))
        rest=[i for i in range(4) if i!=pivot];lam=dec(eig[-1])
        for _ in range(15):
            a=[[lam*int(i==j)-m[i][j] for j in rest] for i in rest]
            b=[m[i][pivot] for i in rest];v=solve(a,b);dv=solve(a,v)
            f=lam-m[pivot][pivot]-sum((x*y for x,y in zip(b,v)),Decimal(0))
            step=f/(1+sum((x*y for x,y in zip(b,dv)),Decimal(0)));lam-=step
            if abs(step)<Decimal('1e-48'):break
        a=[[lam*int(i==j)-m[i][j] for j in rest] for i in rest];v=solve(a,b)
        q=[Decimal(0)]*4;q[pivot]=Decimal(1)
        for i,x in zip(rest,v):q[i]=x
        length=sum((x*x for x in q),Decimal(0)).sqrt();w,a,b,d=[v/length for v in q]
        r=[[w*w+a*a-b*b-d*d,2*(a*b-w*d),2*(a*d+w*b)],
           [2*(a*b+w*d),w*w-a*a+b*b-d*d,2*(b*d-w*a)],
           [2*(a*d-w*b),2*(b*d+w*a),w*w-a*a-b*b+d*d]]
        rt=tr(r);output=[]
        for coord,origin,row in zip(xc,rc,u):
            output.extend(v[0]-x for v,x in zip(mm(rt,[[x] for x in coord]),origin))
            x,y,z=row[3:];cross=[[Decimal(0),-z,y],[z,Decimal(0),-x],[-y,x,Decimal(0)]]
            cross2=mm(cross,cross);t=x*x+y*y+z*z
            ca=Decimal(1);cb=Decimal(1)/2;ta=ca;tb=cb
            for k in range(1,35):
                ta*=-t/((2*k)*(2*k+1));tb*=-t/((2*k+1)*(2*k+2));ca+=ta;cb+=tb
            ex=[[Decimal(int(i==j))+ca*cross[i][j]+cb*cross2[i][j] for j in range(3)] for i in range(3)]
            rel=mm(rt,ex);delta=[[rel[i][j]-int(i==j) for j in range(3)] for i in range(3)]
            assert max(sum(abs(v) for v in row) for row in delta)<Decimal('.5')
            power=delta;log=[[Decimal(0)]*3 for _ in range(3)]
            for k in range(1,100):
                sign=Decimal(1 if k%2 else -1)/k
                log=[[log[i][j]+sign*power[i][j] for j in range(3)] for i in range(3)]
                power=mm(power,delta)
                if max(abs(v) for row in power for v in row)<Decimal('1e-48'):break
            output.extend([(log[2][1]-log[1][2])/2,(log[0][2]-log[2][0])/2,(log[1][0]-log[0][1])/2])
        return output
    records=[]
    with localcontext() as ctx:
        ctx.prec=60
        for slots,reference,u,vector,local,dl,force,tangent,rowmap,update,origin,candidate in prepared:
            uv=[dec(x) for x in u];dv=[dec(x) for x in vector]
            base=kinematics(reference,uv);h=Decimal('1e-6')
            plus=kinematics(reference,[x+h*d for x,d in zip(uv,dv)])
            minus=kinematics(reference,[x-h*d for x,d in zip(uv,dv)])
            observed=np.array([float((a-b)/(2*h)) for a,b in zip(plus,minus)])
            analytic2=np.einsum('ijk,j,k->i',deformation(reference,u,stable_translation=True)[2],vector,vector)
            second=np.array([float((a+b-2*c)/(h*h)) for a,b,c in zip(plus,minus,base)])
            records.append(dict(value_error=float(np.linalg.norm(np.array(list(map(float,base)))-local)),
                first_error=float(np.linalg.norm(observed-dl)),first_norm=float(np.linalg.norm(dl)),
                first_translation_error=float(np.linalg.norm((observed-dl).reshape(-1,6)[:,:3])),
                first_rotation_error=float(np.linalg.norm((observed-dl).reshape(-1,6)[:,3:])),
                second_error=float(np.linalg.norm(second-analytic2)),second_norm=float(np.linalg.norm(analytic2)),
                rotation_max=float(np.max(np.linalg.norm(u.reshape(-1,6)[:,3:],axis=1)))))
    result=dict(scope='60-digit value-only Procrustes/Rodrigues/matrix-log oracle; saved-state development',
        h=1e-6,pools=pools,records=records,
        anchor_sha256=hashlib.sha256((ROOT/'failed-base-v9.npz').read_bytes()).hexdigest())
    assert owner.checkpoint()==prefix
    (ROOT/'kinematic-oracle-v20.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(records))
finally:owner.close()
