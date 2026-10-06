"""Standard-library postprocessing of already executed operators; no evaluations."""
from pathlib import Path
import ast,array,io,json,math,struct,zipfile
ROOT=Path(__file__).resolve().parent;F=ROOT/'paired-v1'
def load(name):return json.loads((F/(name+'.json')).read_text())
def arrays(name):
    result={}
    with zipfile.ZipFile(F/(name+'.npz')) as z:
        for file in z.namelist():
            b=io.BytesIO(z.read(file));assert b.read(6)==b'\x93NUMPY';version=b.read(2)
            n=struct.unpack('<H' if version[0]==1 else '<I',b.read(2 if version[0]==1 else 4))[0]
            header=ast.literal_eval(b.read(n).decode());assert not header['fortran_order']
            kind={'<f8':'d','<i8':'q','<i4':'i','|b1':'B'}[header['descr']];a=array.array(kind);a.frombytes(b.read())
            result[file[:-4]]=dict(shape=header['shape'],values=list(a))
    return result
def v(a,k):return a[k]['values']
def norm(x):return math.sqrt(math.fsum(a*a for a in x))
def mv(a,x):
    out=[0.]*v(a,'K_shape')[0];terms=[[] for _ in out]
    data,indices,indptr=(v(a,k) for k in ('K_data','K_indices','K_indptr'))
    for j in range(len(x)):
        for i in range(indptr[j],indptr[j+1]):terms[indices[i]].append(data[i]*x[j])
    return [math.fsum(row) for row in terms]
roles=(('shell',0,48),('beam_nodal',48,78),('generalized_cells',78,84),('generalized_resultants',84,102),('physical_cells',102,108),('physical_resultants',108,126),('multipliers',126,146))
def attr(error,expected,w):
    denominator=max(norm([a*b for a,b in zip(expected,w)]),1.)
    return dict(relative=norm([a*b for a,b in zip(error,w)])/denominator,
        channels={name:norm([error[i]*w[i] for i in range(lo,hi)])/denominator for name,lo,hi in roles},
        largest_rows=sorted([dict(row=i,error=e,weighted_error=e*w[i],expected=expected[i]) for i,e in enumerate(error)],key=lambda r:abs(r['weighted_error']),reverse=True)[:10])
def q4_labels(row):
    curve=row['curve'];origin=row['origin'];candidate=row['candidate'];out=[]
    if curve is None:return [dict(layer=i,label='ELASTIC',switch_margin=None) for i,_ in enumerate(candidate['alpha'])]
    E,nu=row['E'],row['nu'];C=E/(1-nu*nu)
    for j,(strain,ep,p0,p1) in enumerate(zip(candidate['layer_strain'],origin['plastic_strain'],origin['alpha'],candidate['alpha'])):
        assert p0<=curve['eps_p_y1'],'unimplemented diagnostic beyond first accepted hardening segment'
        sy=curve['sigma_prop']+(curve['sigma_yield']-curve['sigma_prop'])/curve['eps_p_y1']*max(p0,0.)
        e=[a-b for a,b in zip(strain,ep)];sx=C*(e[0]+nu*e[1]);syy=C*(nu*e[0]+e[1]);tau=C*(1-nu)/2*e[2]
        phi=(sx+syy)**2/12+(sx-syy)**2/4+tau*tau;f=phi-sy*sy/3;cutoff=1e-10*max(sy*sy,1)
        switched=f>cutoff;advanced=p1>p0
        out.append(dict(layer=j,label='PLASTIC' if switched else 'ELASTIC',switch_margin=f-cutoff,ideal_margin=f,cutoff=cutoff,
            trial_stress=[sx,syy,tau],origin_alpha=p0,candidate_alpha=p1,output_advanced=advanced,decision_agrees_output=switched==advanced,
            hardening_segment=0 if p1<=curve['eps_p_y1'] else 1 if p1<=curve['eps_p_y2'] else 2))
    return out
def labels(row):
    out=[]
    for member,c in enumerate(row['callbacks']):
        if c['family']=='q4':
            out.extend(dict(key='q4-%d-layer-%d'%(member,r['layer']),**r) for r in q4_labels(c))
        elif c['family']=='physical':
            for station in c['labels']:
                for fibre in station['fibres']:
                    out.append(dict(key='physical-%d-fibre-%s'%(station['station'],fibre['id']),label=fibre['branch'],
                        sign=math.copysign(1,float(fibre['drive'])),table_interval=fibre['table_interval'],margin=fibre['margin'],knots=fibre['knot_distances']))
        elif c['family']=='generalized':
            out.extend(dict(key='generalized-%d'%s['station'],label=s['branch'],margin=s['margin']) for s in c['labels'])
    return out
def compare(base,current):
    a,b=labels(base),labels(current);assert [x['key'] for x in a]==[x['key'] for x in b]
    changes=[]
    for x,y in zip(a,b):
        fields=('label','sign','table_interval','hardening_segment')
        if any(x.get(k)!=y.get(k) for k in fields):changes.append(dict(key=x['key'],base=x,current=y))
    return changes
results={'q4_margin_provenance':'source formula reconstructed from actual captured layer_strain and immutable accepted origins; no return-map calls; represented scalar evaluation can differ by last-bit operation order'}
for prefix,base_name in (('A','A-failure-3-parent'),('B','B-base')):
    base=load(base_name);a=arrays(base_name);direction=arrays(prefix+'-direction');d,w,expected=(v(direction,k) for k in ('direction','weights','expected'))
    R=v(a,'R');rows=[]
    for h in (1e-4,1e-5,1e-6):
        names=[prefix+'-'+sign+'-'+str(h) for sign in ('plus','minus')];positive,negative=[load(n) for n in names];p,m=[arrays(n) for n in names]
        fd=[(x-y)/(2*h) for x,y in zip(v(p,'R'),v(m,'R'))];error=[x-y for x,y in zip(fd,expected)]
        rows.append(dict(h=h,**attr(error,expected,w),plus_changes=compare(base,positive),minus_changes=compare(base,negative),
            minimum_q4_switch_margin=min((abs(r['switch_margin']) for r in labels(positive)+labels(negative) if r.get('switch_margin') is not None),default=None)))
    results[prefix]=dict(base_labels=labels(base),stencils=rows)
    if prefix=='A':
        linear=arrays('A-failure-3-linear');free=v(linear,'free');error=v(linear,'linear_residual');rhs=v(linear,'rhs');fw=[w[i] for i in free]
        results['A']['linear_relative']=norm([x*y for x,y in zip(error,fw)])/norm([x*y for x,y in zip(rhs,fw)])
        results['A']['linear_max_abs']=max(map(abs,error));results['A']['linear_rhs_max_abs']=max(map(abs,rhs))
        results['A']['Kd_plus_R_weighted_free']=norm([(x+y)*w[i] for i,(x,y) in enumerate(zip(expected,R)) if i in free])
        results['A']['weighted_parent_residual_free']=norm([R[i]*w[i] for i in free])
        candidates=[]
        for i in range(13):
            name='A-failure-3-candidate-%02d'%i;r=load(name);c=arrays(name);Rc=v(c,'R');h=r['amount'];delta=[(Rc[j]-R[j])/h for j in range(len(R))]
            candidates.append(dict(index=i,amount=h,relative=r['relative'],gap=r['gap'],ratio=r['relative']/base['relative'],
                changes=compare(base,r),secant_direction=attr([x-y for x,y in zip(delta,expected)],expected,w),
                weighted_free_norm=norm([Rc[j]*w[j] for j in free]),
                residual_largest_rows=sorted([dict(row=j,residual=Rc[j],weighted=Rc[j]*w[j]) for j in free],key=lambda x:abs(x['weighted']),reverse=True)[:6]))
        results['A']['candidates']=candidates;results['A']['parent_relative']=base['relative'];results['A']['parent_gap']=base['gap']
        results['A']['parent_largest_rows']=sorted([dict(row=j,residual=R[j],weighted=R[j]*w[j],Kd=expected[j]) for j in free],key=lambda x:abs(x['weighted']),reverse=True)[:10]
(ROOT/'saved-analysis-v1.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({p:[dict(h=s['h'],relative=s['relative'],plus_changes=len(s['plus_changes']),minus_changes=len(s['minus_changes'])) for s in results[p]['stencils']] for p in ('A','B')}))
print(json.dumps({k:results['A'][k] for k in ('linear_relative','linear_max_abs','linear_rhs_max_abs','weighted_parent_residual_free','Kd_plus_R_weighted_free','parent_largest_rows')}))
print(json.dumps([dict(index=c['index'],amount=c['amount'],relative=c['relative'],ratio=c['ratio'],changes=[x['key'] for x in c['changes']]) for c in results['A']['candidates']]))
