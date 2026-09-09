"""Small isolated-wheel correctness check; never qualification authority."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-map',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if not sys.flags.isolated or sys.prefix == sys.base_prefix:
        raise RuntimeError('isolated virtual environment required')
    if any(str(Path(p).resolve()).lower().startswith('c:\\github') for p in sys.path if p):
        raise RuntimeError('repository search path present')
    class NoResearch:
        def find_spec(self,fullname,path=None,target=None):
            if fullname.split('.')[0] in {'docs','tests'}:
                raise ImportError('research imports forbidden')
            return None
    sys.meta_path.insert(0,NoResearch())

    import numpy as np
    import scipy
    import anysolver
    from anysolver.fe_core import FEModel
    from anysolver.boundary import BoundaryCondition
    from anysolver.control import CancellationToken
    from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as Reference
    from anysolver._ge_beam3_p5_loads import NativeP5BeamElement, DirectedHardeningSection
    from anysolver._ge_beam3_p5_loads.core import canonical, sha
    from anysolver._ge_beam3_load_program import ForceProgram, solve_force_program

    root = Path(anysolver.__file__).resolve().parent
    if not root.is_relative_to(Path(sys.prefix).resolve()):
        raise RuntimeError('ANYsolver did not originate in installed target')
    source_map = json.loads(args.source_map.read_text(encoding='utf-8'))
    if source_map['output_text_normalization'] != 'UTF8_LF':
        raise RuntimeError('explicit source text normalization required')
    files = {}
    for source,expected in source_map['outputs'].items():
        relative = Path(source).relative_to('src/anysolver')
        raw = (root/relative).read_bytes()
        text = raw.decode('utf-8').replace('\r\n','\n').encode('utf-8')
        if dict(bytes=len(text),sha256=hashlib.sha256(text).hexdigest()) != expected:
            raise RuntimeError('installed source identity mismatch: '+source)
        files[relative.as_posix()] = dict(canonical_sha256=expected['sha256'],
            installed_bytes=len(raw),installed_sha256=hashlib.sha256(raw).hexdigest())

    def model(*,plastic=False,count=1,shift=0.):
        made = FEModel('installed-force-program')
        ids = (7,23,55) if count == 1 else (7,23,55,81,103)
        parameters = np.linspace(-1.,1.,2*count+1)
        points = np.array([[x,.5*(1-x*x),.25*(1-x*x)] for x in parameters])+shift
        frames = []
        for x in parameters:
            first = np.array([1.,-x,-.5*x]); first /= np.linalg.norm(first)
            second = np.array([0.,0.,1.]); second -= first*float(first@second); second /= np.linalg.norm(second)
            frames.append(np.column_stack((first,second,np.cross(first,second))))
        for i,point in zip(ids,points): made.add_node(i,*point)
        factor = np.array([[2.,.1,0.,.2,-.1,0.],[0.,3.,.2,0.,.3,.1],[0.,0.,4.,.1,0.,.2],
                           [0.,0.,0.,1.,.1,.2],[0.,0.,0.,0.,1.5,.1],[0.,0.,0.,0.,0.,2.]])
        for index in range(count):
            ref = Reference(points[2*index:2*index+3],np.array(frames[2*index:2*index+3]))
            section = DirectedHardeningSection(factor.T@factor,np.array([1.,.2,-.1,.3,-.4,.5]),.02 if plastic else 1000.,.4)
            element = NativeP5BeamElement(index+1,ids[2*index:2*index+3],ref,section,line_force=np.array([.03,-.02,.01]))
            made.add_element(index+1,element); made.materials[element.material_name] = element.core.section
        made.add_boundary_condition(BoundaryCondition('root',[ids[0]],
            {name:0. for name in ('ux','uy','uz','rx','ry','rz')}))
        return made

    def run(made,program,**kwargs):
        result = solve_force_program(made,program,**kwargs)
        if result.status != 'completed': raise RuntimeError(str((result.status,result.failure)))
        if result.production_qualified: raise RuntimeError('private result claimed qualification')
        return result

    print('installed_force: source binding complete',flush=True)
    program = ForceProgram((.5,1.,0.,-.5),((55,.025,-.01,.005),))
    full_model = model(plastic=True); full = run(full_model,program)
    paused = solve_force_program(model(plastic=True),program,stop_after=2)
    if paused.status != 'paused': raise RuntimeError('installed pause failed')
    resumed = run(model(plastic=True),program,checkpoint=paused.checkpoint)
    if resumed.checkpoint != full.checkpoint: raise RuntimeError('installed program restart differs')
    decoded = json.loads(full.checkpoint)['element_states'][0]['state']
    element = full_model.mesh.elements[1]
    state = element.validate_model_bound_nonlinear_state(full_model.mesh,element.core.section,decoded,1,
        expected_committed_total_u=full.displacements)
    if not any(h.accumulated > 0. for h in state['material_state']['histories']):
        raise RuntimeError('installed plastic path not exercised')
    recovery = element.recover_native_fields(full_model.mesh,state)
    if recovery['load_parameter'] != -.5: raise RuntimeError('installed recovery load mismatch')
    print('installed_force: plastic reversal and restart complete',flush=True)

    shared_program = ForceProgram((.5,1.))
    origin = run(model(count=2),shared_program)
    translated = run(model(count=2,shift=2.**40),shared_program)
    if not np.array_equal(origin.displacements,translated.displacements):
        raise RuntimeError('installed shared-node translation changed displacement')
    if not np.array_equal(origin.physical_imbalance,translated.physical_imbalance):
        raise RuntimeError('installed shared-node translation changed physical reaction')

    token = CancellationToken()
    def cancel(event):
        if event['stage'] == 'native_force.before_commit': token.cancel('installed cancellation fixture')
    cancelled = solve_force_program(model(),shared_program,cancellation_token=token,progress=cancel)
    virgin = solve_force_program(model(),shared_program,stop_after=0)
    if cancelled.status != 'cancelled' or cancelled.checkpoint != virgin.checkpoint:
        raise RuntimeError('installed cancelled trial changed accepted capsule')
    print('installed_force: shared nodes and cancellation complete',flush=True)
    for name,module in tuple(sys.modules.items()):
        if name == 'anysolver' or name.startswith('anysolver.'):
            origin_path = getattr(module,'__file__',None)
            if origin_path is not None and not Path(origin_path).resolve().is_relative_to(root):
                raise RuntimeError('ANYsolver import escaped installed target')
    if hasattr(anysolver,'ForceProgram') or hasattr(anysolver,'NativeP5BeamElement'):
        raise RuntimeError('private driver or element was publicly exported')
    with (args.output.parent/'accepted-checkpoint.json').open('xb') as stream: stream.write(full.checkpoint)
    record = dict(schema='GE_BEAM3_NATIVE_FORCE_PROGRAM_INSTALLED_CHECK_V1',production_qualified=False,
        runtime=dict(python=sys.version.split()[0],numpy=np.__version__,scipy=scipy.__version__),
        imports_isolated=True,research_imports_forbidden=True,restart_exact=True,plastic_reversal_exercised=True,
        translated_shared_node_output_exact=True,precommit_cancellation_preserved=True,
        checkpoint_bytes=len(full.checkpoint),checkpoint_sha256=hashlib.sha256(full.checkpoint).hexdigest(),
        displacement_sha256=sha(full.displacements),physical_reaction_sha256=sha(full.physical_imbalance),
        recovery_sha256=sha(recovery),source_files=files,
        source_map_sha256=hashlib.sha256(args.source_map.read_bytes()).hexdigest())
    with args.output.open('xb') as stream: stream.write(canonical(record))
    print('installed_force: evidence complete',flush=True)


if __name__ == '__main__': main()
