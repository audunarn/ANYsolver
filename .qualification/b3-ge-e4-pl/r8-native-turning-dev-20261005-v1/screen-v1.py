from pathlib import Path
from hashlib import sha256
import json,sys,os
import numpy as np
from threadpoolctl import threadpool_info
from anysolver import b3_ge,stiffened_shell as ss
RAW=Path(__file__).resolve().parent;ROOT=RAW.parents[2]
ART=RAW.parent/'r8-native-arc-dev-20261005-v1'
assert Path(ss.__file__).resolve().is_relative_to(ART/'site-v1')
artifact=json.loads((ART/'artifact-v1.json').read_bytes())['artifacts']['solver']
assert sha256(Path(artifact['wheel']).read_bytes()).hexdigest()==artifact['sha256']
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
assert threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
E=210e9;nu=.3;G=E/(2*(1+nu));density=7850.;a=1.;h=.03
width=.01;height=.004;area=width*height
iyy=width*height**3/12;izz=height*width**3/12
# Declared rectangular Saint-Venant approximation; no torsional load in screen.
j=width*height**3*(1/3-.21*height/width*(1-height**4/(12*width**4)))
section=b3_ge.EllipsoidalGeneralizedSection(np.diag((E*area,G*area*5/6,G*area*5/6,G*j,E*iyy,E*izz)),np.eye(6),1e20,1e9)
inertia=density*np.diag((area,area,area,iyy+izz,iyy,izz))
xs=np.linspace(-a,a,5);xyz=np.array([(x,-.05,h*(1-(x/a)**2)) for x in xs])
frames=[]
for x in xs:
    tangent=np.array((1.,0.,-2*h*x/a**2));tangent/=np.linalg.norm(tangent)
    dy=np.array((0.,1.,0.));frames.append(np.column_stack((tangent,dy,np.cross(tangent,dy))))
frames=np.asarray(frames)
beams=tuple(b3_ge.define_beam('b3-ge',i+1,tuple(range(101+2*i,104+2*i)),
    xyz[2*i:2*i+3],frames[2*i:2*i+3],section,inertia) for i in range(2))
shell=ss.ShellPanel((1,2,3,4,5,6),tuple((x,y,0.) for y in (-.05,.05) for x in (-1.,0.,1.)),
    ((1,2,5,4),(2,3,6,5)),2e-5,E,nu,density)
model=ss.LinearDefinition(ss.B3_GE_E4_PL_STIFFENED_SHELL_V1,shell,beams,
    tuple(ss.PointConnection(i,100+2*i-1) for i in (1,2,3)),
    tuple(ss.FixedCoordinate('shell',i,k) for i in (1,3,4,6) for k in range(6)),
    q4_pullback_policy=ss.Q4_ALGORITHMIC_PULLBACK_V1)
weights=np.zeros(11)
for cell in shell.q4_elements:
    for node in cell:weights[node-1]+=.1*shell.thickness_m/4
gauss,quad=np.polynomial.legendre.leggauss(8)
for i,native in enumerate(beams):
    element,_=native.instantiate()
    local=np.zeros(3)
    for xi,qw in zip(gauss,quad):
        shape=np.array((xi*(xi-1)/2,1-xi*xi,xi*(xi+1)/2))
        local+=qw*element.operator.reference.jacobian(float(xi))*shape*area
    weights[6+2*i:9+2*i]+=local
assert np.all(weights>0.)
weights/=weights.sum()
record=dict(status='IN_PROGRESS',production_qualified=False,rows=[],
    artifact=artifact,metric_weights=weights.tolist(),pools=threadpool_info(),
    comparator=dict(first_w=.0115758306,first_P=91.0644984,not_exact_native_oracle=True),
    section=dict(area=area,iyy=iyy,izz=izz,st_venant_approx_j=j))
def save():(RAW/'result-v1.json').write_bytes((json.dumps(record,indent=2)+'\n').encode('ascii'))
save();analysis=None;resumed=None
try:
    analysis=ss.create_analysis(definition=model)
    record['preflight']=analysis.preflight();save()
    analysis.solve((ss.NodalAction('beam',103,(0.,0.,0.,0.,0.,0.)),),(1.,),max_iterations=20,max_backtracks=12)
    control=ss.ArcLengthControl('beam',103,2,ss.PhysicalChordMetric(weights,a),.003,orientation=-1)
    actions=(ss.NodalAction('beam',103,(0.,0.,-1.,0.,0.,0.)),)
    desc=0;peak=0.;restart=False;previous_w=0.;previous_p=0.
    for step in range(48):
        prefix=analysis.checkpoint()
        result=analysis.continue_arc_length(actions,control)
        raw=analysis.checkpoint();(RAW/'last-prefix.checkpoint').write_bytes(raw)
        w=h-float(result.beam_positions[2,2]);p=result.amplitude
        assert result.free_equilibrium_ratio<=1e-8 and result.constraint_max<=1e-9
        decline=p<previous_p and w>previous_w
        if decline and not restart:
            (RAW/'turning-predecessor.checkpoint').write_bytes(prefix)
            resumed=ss.create_analysis(definition=model);resumed.restore(prefix)
            repeated=resumed.continue_arc_length(actions,control)
            assert resumed.checkpoint()==raw
            assert repeated.history==result.history and repeated.amplitude==result.amplitude
            (RAW/'turning-successor.checkpoint').write_bytes(raw)
            restart=True
        desc=desc+1 if decline else 0;peak=max(peak,p)
        record['rows'].append(dict(step=step+1,w=w,load=p,eq=result.free_equilibrium_ratio,
            gap=result.constraint_max,generation=result.generation,
            radius=result.history[-1][0],attempts=[r.__dict__ for r in result.increment_attempts],
            point_wrenches=len(result.point_wrenches)))
        record.update(observed_peak=peak,descending_count=desc,exact_turning_restart=restart)
        save();print(f'step={step+1} w={w:.8g} P={p:.8g} descend={desc}',flush=True)
        if desc>=3 and p<=.95*peak:
            record['status']='OBSERVED_ACCEPTED_LOAD_TURN_NOT_QUALIFIED';break
        previous_w=w;previous_p=p
    else:record['status']='COMPLETED_NO_TURN_WITHIN_BUDGET'
    record['final_checkpoint_sha256']=sha256(analysis.checkpoint()).hexdigest();save()
except BaseException as error:
    record.update(status='FAILED_SCREEN',failure=repr(error));save();raise
finally:
    if resumed is not None:resumed.close()
    if analysis is not None:analysis.close()
