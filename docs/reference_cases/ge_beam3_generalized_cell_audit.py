"""Independent primal station-work audit; no producer/cell/beam imports."""
from decimal import Decimal as D,localcontext
from .ge_beam3_generalized_ellipsoid_oracle import response,linear


def unpack(value):return [D.from_float(h)+D.from_float(l) for h,l in zip(*value)]
def dot(a,b):return sum((x*y for x,y in zip(a,b)),D(0))
def mv(a,b):return [dot(row,b) for row in a]
def zero(n,m):return [[D(0) for _ in range(m)] for _ in range(n)]


def audit(section,stations,p,result):
    with localcontext() as ctx:
        ctx.prec=96;p=list(map(D.from_float,p));g=unpack(result['gradient'])
        forces=[D(0)]*6;curvatures=[D(0)]*12;primal=D(0)
        size=6+3*len(stations);a=zero(size,size);load=zero(size,18)
        for i in range(6):load[i][i]=D(1)
        errors={k:D(0) for k in ('force','moment','compatibility','section','history','work','curvature','hessian','station_potential')}
        for j,(station,fields,old,new) in enumerate(zip(stations,result['stations'],result['origin']['stations'],result['history']['stations'])):
            cell=station['cell'];t=D.from_float(station['t']);w=D.from_float(station['weight'])
            v=[list(map(D.from_float,row)) for row in station['v']]
            e=unpack(fields['strain']);s=unpack(fields['resultants'])
            expected=[(1-t)*p[6+6*cell+i]+t*p[9+6*cell+i] for i in range(3)]
            errors['moment']=max(errors['moment'],*(abs(x-y) for x,y in zip(expected,s[3:])))
            errors['compatibility']=max(errors['compatibility'],*(abs(x-y) for x,y in zip(mv(v,g[3*cell:3*cell+3]),e[:3])))
            data=dict(section,strain=list(map(float,e)),plastic=old['plastic'],accumulated=old['accumulated'])
            ref=response(data)
            errors['section']=max(errors['section'],*(abs(x-D.from_float(y)) for x,y in zip(s,ref['stress'])))
            proposed=[D.from_float(h)+D.from_float(l) for h,l in new['plastic']]
            errors['history']=max(errors['history'],*(abs(x-D.from_float(y)) for x,y in zip(proposed,ref['plastic'])),
                abs(sum(map(D.from_float,new['accumulated']))-D.from_float(ref['accumulated'])))
            primal+=w*D.from_float(ref['potential'])
            errors['station_potential']=max(errors['station_potential'],abs(unpack(fields['incremental_potential'])[0]-D.from_float(ref['potential'])))
            for i in range(3):
                forces[3*cell+i]+=w*sum(v[k][i]*s[k] for k in range(3))
                curvatures[6*cell+i]+=w*(1-t)*e[3+i];curvatures[6*cell+3+i]+=w*t*e[3+i]
                load[6+3*j+i][6+6*cell+i]=w*(1-t);load[6+3*j+i][9+6*cell+i]=w*t
            # Reconstruct the opposite (primal strain) elimination from the
            # independent section's consistent tangent, not a producer matrix.
            indices=list(range(3*cell,3*cell+3))+list(range(6+3*j,9+3*j))
            mapping=zero(6,6)
            for i in range(3):
                mapping[i][:3]=v[i];mapping[3+i][3+i]=D(1)
            c=[list(map(D.from_float,row)) for row in ref['tangent']]
            for i,ii in enumerate(indices):
                for k,kk in enumerate(indices):
                    a[ii][kk]+=w*sum(mapping[r][i]*c[r][s]*mapping[s][k] for r in range(6) for s in range(6))
        recovered=linear(a,load)
        h=[[sum(load[k][i]*recovered[k][j] for k in range(size)) for j in range(18)] for i in range(18)]
        observed=[unpack(row) for row in result['hessian']]
        errors['hessian']=max(abs(x-y)/max(D(1),abs(y)) for row,other in zip(observed,h) for x,y in zip(row,other))
        errors['force']=max(abs(x-y) for x,y in zip(forces,p[:6]))
        errors['curvature']=max(abs(x-y) for x,y in zip(curvatures,g[6:]))
        errors['work']=abs(dot(p,g)-primal-unpack(result['potential'])[0])
        return {k:float(v) for k,v in errors.items()}
