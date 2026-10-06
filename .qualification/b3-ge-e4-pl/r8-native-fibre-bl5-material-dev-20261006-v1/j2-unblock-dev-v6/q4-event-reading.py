from pathlib import Path
import json,math
R=Path(__file__).resolve().parent;F=R/'paired-v1'
def read(n):return json.loads((F/(n+'.json')).read_text())
base=read('A-failure-3-parent');plus=read('A-plus-1e-05');minus=read('A-minus-1e-05')
rows=[]
for member,(b,p,m) in enumerate(zip(base['callbacks'],plus['callbacks'],minus['callbacks'])):
    if b['family']!='q4':continue
    curve=b['curve'];E,nu=b['E'],b['nu'];C=E/(1-nu*nu)
    for layer,(e,ep,em,z,p0) in enumerate(zip(b['candidate']['layer_strain'],p['candidate']['layer_strain'],m['candidate']['layer_strain'],b['origin']['plastic_strain'],b['origin']['alpha'])):
        de=[(x-y)/(2e-5) for x,y in zip(ep,em)];strain=[x-y for x,y in zip(e,z)]
        def stress(x):return [C*(x[0]+nu*x[1]),C*(nu*x[0]+x[1]),C*(1-nu)/2*x[2]]
        s,ds=stress(strain),stress(de);sy=curve['sigma_prop']+(curve['sigma_yield']-curve['sigma_prop'])/curve['eps_p_y1']*p0
        def phi(x):return (x[0]+x[1])**2/12+(x[0]-x[1])**2/4+x[2]**2
        a=phi(ds);b1=(s[0]+s[1])*(ds[0]+ds[1])/6+(s[0]-s[1])*(ds[0]-ds[1])/2+2*s[2]*ds[2]
        c=phi(s)-sy**2/3-1e-10*max(sy**2,1.)
        roots=[]
        if a:
            discr=b1*b1-4*a*c
            if discr>=0:
                q=-.5*(b1+math.copysign(math.sqrt(discr),b1))
                roots=[q/a,c/q] if q else [0.]
        elif b1:roots=[-c/b1]
        roots=[x for x in roots if 0<x<=1]
        if roots:rows.append(dict(member=member,layer=layer,current_switch_margin=c,coefficients=[a,b1,c],positive_roots=roots,
            strain= e,strain_direction_from_saved_fine_pair=de,stress=s,stress_direction=ds,actual_parent_label='PLASTIC' if c>0 else 'ELASTIC'))
rows.sort(key=lambda r:min(r['positive_roots']))
(R/'q4-event-reading-v1.json').write_text(json.dumps(dict(source='Saved h +/-1e-5 strain pair only; derivative fit is diagnostic, not an adopted product formula',events=rows),indent=2)+'\n')
print(json.dumps(rows[:3]))
