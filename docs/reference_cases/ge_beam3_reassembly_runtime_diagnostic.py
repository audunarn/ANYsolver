"""Small arithmetic/runtime diagnosis of a preserved installed covariance failure.

Same fixture, two floating-point coordinate construction orders. Neither
variant is substituted for the failed package gate. No qualification, retry
of a formal request, tolerance changes, or source edits are performed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import scipy
import anysolver
from anysolver.fe_core import FEModel
from anysolver.boundary import BoundaryCondition
from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as Reference
from anysolver._ge_beam3_p5_seeded import NativeP5BeamElement, DirectedHardeningSection
from anysolver._ge_beam3_p5_seeded.core import canonical
from anysolver._ge_beam3_p5.algebra import rotation
import anysolver._ge_beam3_reassembled_signed_modes as adapter

def contrast(slenderness, q, batched):
    model=FEModel('installed-reassembled-curved-contrast')
    xs=np.linspace(-1.,1.,5); points=[]; frames=[]
    for x in xs:
        points.append(np.array([x,.25*(1-x*x),.125*(1-x*x)]))
        first=np.array([1.,-.5*x,-.25*x]); first/=np.linalg.norm(first)
        second=np.array([0.,0.,1.]); second-=first*(first@second); second/=np.linalg.norm(second)
        frames.append(q@np.column_stack((first,second,np.cross(first,second))))
    points=np.array(points); frames=np.array(frames)
    points=points@q.T if batched else np.array([q@point for point in points])
    for i,point in enumerate(points,1): model.add_node(i,*point)
    ea=3*slenderness**2; h=2/slenderness
    factor=np.array([[1.,.05,-.08,.12,-.04,.03],[0.,1.,.06,-.05,.08,.04],
        [0.,0.,1.,.07,.02,-.05],[0.,0.,0.,1.,.1,.05],
        [0.,0.,0.,0.,1.,-.1],[0.,0.,0.,0.,0.,1.]])@np.diag(np.sqrt([ea,ea/3,ea/3.5,2.,1.,1.5]))
    for cell in range(2):
        ids=tuple(range(1+2*cell,4+2*cell))
        section=DirectedHardeningSection(factor.T@factor,np.array([1.,.2,-.1,.3,-.4,.5]),1e6,1.)
        element=NativeP5BeamElement(cell+1,ids,Reference(points[2*cell:2*cell+3],frames[2*cell:2*cell+3]),
            section,line_force=np.zeros(3))
        model.add_element(cell+1,element); model.materials[element.material_name]=element.core.section
    model.add_boundary_condition(BoundaryCondition('root',[1],
        {name:0. for name in ('ux','uy','uz','rx','ry','rz')}))
    return model,{i:np.diag([1.,1.,1.,h*h/6,h*h/12,h*h/12]) for i in model.mesh.elements}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--expected-root',type=Path,required=True)
    parser.add_argument('--source-map',type=Path,required=True)
    args=parser.parse_args()
    root=Path(anysolver.__file__).resolve().parent
    if root!=args.expected_root.resolve(): raise RuntimeError('wrong import origin')
    authority=json.loads(args.source_map.read_text())
    if authority['candidate_commit']!='a36baf8be16f4cac0c2c8f43060e66493bdafa49' or len(authority['outputs'])!=83:
        raise RuntimeError('wrong diagnostic input binding')
    for name,expected in authority['outputs'].items():
        raw=(root/Path(name).relative_to('src/anysolver')).read_bytes().replace(b'\r\n',b'\n')
        if dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())!=expected:
            raise RuntimeError('diagnostic source mismatch '+name)
    args.output.mkdir(exist_ok=False)
    rows=[]; original=adapter.solve_reassembled_factor_modes
    for batched in (False,True):
        values=[]
        for name,q in (('E',np.eye(3)),('GENERAL',rotation([.4,-.3,.2]))):
            label=('batched-' if batched else 'per-node-')+name
            print(label+' initialized',flush=True)
            model,inertias=contrast(1e6,q,batched)
            states={i:e.init_model_bound_nonlinear_state(model.mesh,e.core.section,1)
                for i,e in model.mesh.elements.items()}
            captured={}
            def capture(f,g,b,free,algebraic,**kwargs):
                captured.update(factor=f.copy(),geometric=g.copy(),kinetic=b.copy(),
                    free=np.array(free,dtype=int),algebraic=np.array(algebraic,dtype=int))
                return original(f,g,b,free,algebraic,**kwargs)
            adapter.solve_reassembled_factor_modes=capture
            try:
                packet,modes=adapter.solve_signed_loaded_modes(model,states,np.zeros(30),inertias,np.zeros(30),
                    load_parameter=0.,bounds=(-10000.,100000000.))
            finally:
                adapter.solve_reassembled_factor_modes=original
            captured.update(coordinates=np.array([n.coords() for n in model.mesh.nodes.values()]),
                eigenvalues=modes.eigenvalues,modes=modes.full_modes,mass=packet.mass,rotation=q)
            with (args.output/(label+'.npz')).open('xb') as stream: np.savez(stream,**captured)
            with (args.output/(label+'.json')).open('xb') as stream: stream.write(canonical(modes))
            values.append((packet,modes,q))
            print(label+' captured',flush=True)
        a,b=values; transform=np.kron(np.eye(14),b[2])
        cross=(transform@a[1].full_modes).T@b[0].mass@b[1].full_modes
        error=np.abs(cross)-np.eye(6)
        rows.append(dict(variant=('batched' if batched else 'per-node'),
            eigenvalue_relative_difference=(b[1].eigenvalues-a[1].eigenvalues)/a[1].eigenvalues,
            correlation_error=error,maximum_absolute_correlation_error=float(np.max(np.abs(error))),
            production_qualified=False))
    result=dict(runtime=dict(python=sys.version.split()[0],numpy=np.__version__,scipy=scipy.__version__),
        isolated=bool(sys.flags.isolated),cases=rows,qualification_passed=False)
    with (args.output/'diagnostic.json').open('xb') as stream:stream.write(canonical(result))
    print(canonical(result).decode(),flush=True)

if __name__=='__main__': main()
