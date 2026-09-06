"""Small installed-candidate correctness check; no formal qualification authority."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-map', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not sys.flags.isolated or sys.prefix == sys.base_prefix:
        raise RuntimeError('isolated virtual environment required')
    if any(str(Path(p).resolve()).lower().startswith('c:\\github') for p in sys.path if p):
        raise RuntimeError('repository search path is present')
    class NoResearch:
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in {'docs', 'tests'}:
                raise ImportError('research import forbidden in installed candidate')
            return None
    sys.meta_path.insert(0, NoResearch())

    import numpy as np
    import anysolver
    from anysolver.fe_core import FEModel
    from anysolver.boundary import BoundaryCondition, LoadCase
    from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as CurvedBeam3ReferenceGeometry
    from anysolver.nonlinear_static import solve_static_nonlinear
    from anysolver.nonlinear_restart import canonical_checkpoint_json_bytes
    from anysolver._ge_beam3_p5_centered import NativeP5BeamElement, DirectedHardeningSection
    from anysolver._ge_beam3_p5_centered.core import canonical, sha
    from anysolver._ge_beam3_p5_centered.reference_modal import solve as modal
    from anysolver._ge_beam3_p5_centered.committed_modal import solve_elastic_modes

    root = Path(anysolver.__file__).resolve().parent
    if not root.is_relative_to(Path(sys.prefix).resolve()):
        raise RuntimeError('ANYsolver does not originate in isolated installation')
    source_map = json.loads(args.source_map.read_text(encoding='utf-8'))
    if source_map.get('output_text_normalization') != 'UTF8_LF':
        raise RuntimeError('explicit canonical source-text policy required')
    file_hashes = {}
    for source, binding in source_map['outputs'].items():
        relative = Path(source).relative_to('src/anysolver')
        path = root/relative; raw = path.read_bytes()
        canonical_source = raw.decode('utf-8').replace('\r\n','\n').encode('utf-8')
        digest = hashlib.sha256(canonical_source).hexdigest()
        if len(canonical_source) != binding['bytes'] or digest != binding['sha256']:
            raise RuntimeError('installed candidate source hash mismatch')
        file_hashes[relative.as_posix()] = dict(canonical_sha256=digest,
            installed_bytes=len(raw), installed_sha256=hashlib.sha256(raw).hexdigest())

    def problem(yield_force, shift=2.**40):
        model = FEModel('p5-installed-candidate')
        nodes = np.array([[-1.,0.,0.],[0.,.5,0.],[1.,0.,0.]])
        frames = []
        for xi in (-1.,0.,1.):
            axis = np.array([xi-.5,-2*xi,xi+.5])@nodes
            axis /= np.linalg.norm(axis); second = np.array([0.,0.,1.])
            frames.append(np.column_stack((axis,second,np.cross(axis,second))))
        nodes = nodes+shift
        ref = CurvedBeam3ReferenceGeometry(nodes,np.array(frames))
        factor = np.array([[2.,.1,0.,.2,-.1,0.],[0.,3.,.2,0.,.3,.1],[0.,0.,4.,.1,0.,.2],
                           [0.,0.,0.,1.,.1,.2],[0.,0.,0.,0.,1.5,.1],[0.,0.,0.,0.,0.,2.]])
        section = DirectedHardeningSection(factor.T@factor,np.array([1.,.2,-.1,.3,-.4,.5]),yield_force,.4)
        for i, point in enumerate(nodes,1): model.add_node(i,*point)
        element = NativeP5BeamElement(1,(1,2,3),ref,section)
        model.add_element(1,element); model.materials[element.material_name] = element.core.section
        model.add_boundary_condition(BoundaryCondition('root',[1],
            {name:0. for name in ('ux','uy','uz','rx','ry','rz')}))
        load = LoadCase('tip'); load.add_nodal_load(3,forces=np.array([.025,-.01,.005]))
        return model,element,load

    def run(model,load,**kwargs):
        result = solve_static_nonlinear(model,load,max_iterations=12,tolerance=1e-12,num_layers=1,
            min_step_fraction=1.,emit_restart_checkpoint=True,**kwargs)
        if result.status != 'completed': raise RuntimeError('installed native Newton failed')
        return result

    model,element,load = problem(.02); continuous = run(model,load,num_steps=2)
    first_model,_,first_load = problem(.02)
    first = run(first_model,first_load,num_steps=1,max_load_factor=.5)
    last_model,last_element,last_load = problem(.02)
    resumed = run(last_model,last_load,num_steps=2,restart_checkpoint=canonical_checkpoint_json_bytes(first.restart_checkpoint))
    if canonical_checkpoint_json_bytes(resumed.restart_checkpoint) != canonical_checkpoint_json_bytes(continuous.restart_checkpoint):
        raise RuntimeError('installed continuation mismatch')
    recovery = last_element.recover_native_fields(last_model.mesh,resumed.element_states[1])
    if not any(h.accumulated > 0. for h in resumed.element_states[1]['material_state']['histories']):
        raise RuntimeError('plastic path was not exercised')
    inertia = np.diag([2.,2.,2.,.2,.1,.15])
    reference = modal(model,{1:inertia})
    elastic_model,_,elastic_load = problem(1000.); elastic = run(elastic_model,elastic_load,num_steps=2)
    forces = np.zeros(18); forces[12:15] = [.025,-.01,.005]
    packet,current = solve_elastic_modes(elastic_model,elastic.element_states,elastic.displacements,{1:inertia},forces)
    # Exercise the representation defect through real native assembly/commit
    # in the installed wheel, with an independent exact axial reference.
    from anysolver.nonlinear_static import _assemble_nonlinear_system
    from anysolver.nonlinear_state import NonlinearStateStore, create_model_native_rotation_store
    axial = FEModel('installed-sub-ulp-axial')
    points = np.array([[0.,0.,0.],[1.,0.,0.],[2.,0.,0.]])
    ref = CurvedBeam3ReferenceGeometry(points,np.tile(np.eye(3),(3,1,1)))
    section = DirectedHardeningSection(np.eye(6),np.array([1.,0.,0.,0.,0.,0.]),1.,1.)
    for index,point in enumerate(points,1): axial.add_node(index,*point)
    beam = NativeP5BeamElement(1,(1,2,3),ref,section)
    axial.add_element(1,beam); axial.materials[beam.material_name] = beam.core.section
    states = {1:beam.init_model_bound_nonlinear_state(axial.mesh,beam.core.section,1)}
    store = NonlinearStateStore.from_shell_layouts((),states)
    store.attach_native_rotation_store(create_model_native_rotation_store(axial,states,np.zeros(18)))
    total = np.zeros(18); strain = 2.**-54; total[[6,12]] = [strain,2*strain]
    try:
        force,_,_ = _assemble_nonlinear_system(axial,total,store,1)
        expected = np.zeros(18); expected[[0,12]] = [-strain,strain]
        if np.linalg.norm(force-expected) > 1e-11*np.linalg.norm(expected):
            raise RuntimeError('installed coordinate correction lost axial force')
        store.commit(store.active_trial_token(),accepted_full_displacement=total,
                     accepted_full_coordinates=points+total.reshape(3,6)[:,:3])
        accepted = store[1]
        encoded = beam.serialize_native_material_state(axial.mesh,accepted)
        restored = beam.validate_model_bound_nonlinear_state(axial.mesh,beam.core.section,encoded,1,
            expected_committed_total_u=total)
        if canonical(restored) != canonical(accepted): raise RuntimeError('installed split position replay mismatch')
        if np.count_nonzero(accepted['material_state']['committed_position_low']) != 2:
            raise RuntimeError('installed low coordinate authority missing')
    finally:
        if store.has_active_trial: store.discard_trial(store.active_trial_token())
    origin_model,_,origin_load = problem(.02,shift=0.)
    origin = run(origin_model,origin_load,num_steps=2)
    if not np.array_equal(origin.displacements,continuous.displacements):
        raise RuntimeError('installed native solution changed under exact translation')
    if sha(origin.element_states[1]['material_state']['response']) != sha(continuous.element_states[1]['material_state']['response']):
        raise RuntimeError('installed stationary response changed under exact translation')
    for name,module in tuple(sys.modules.items()):
        if name == 'anysolver' or name.startswith('anysolver.'):
            origin = getattr(module,'__file__',None)
            if origin is not None and not Path(origin).resolve().is_relative_to(root):
                raise RuntimeError('ANYsolver module escaped installed target: '+name)
    if hasattr(anysolver,'NativeP5BeamElement'):
        raise RuntimeError('candidate must not be root-exported before qualification')
    record = dict(schema='GE_BEAM3_CENTERED_NATIVE_INSTALLED_DEVELOPMENT_CHECK_V3',production_qualified=False,
        formulation=element.formulation_id,source_map_sha256=hashlib.sha256(args.source_map.read_bytes()).hexdigest(),
        source_files=file_hashes,imports_isolated=True,research_imports_forbidden=True,
        restart_exact=True,plastic_exercised=True,sub_ulp_axial_commit_verified=True,
        coordinate_policy=element.to_dict()['coordinate_policy'],
        reference_evaluation=element.to_dict()['reference_evaluation'],translated_native_solution_verified=True,
        response_sha256=sha(continuous.element_states[1]['material_state']['response']),
        recovery_sha256=sha(recovery),checkpoint_sha256=hashlib.sha256(canonical_checkpoint_json_bytes(resumed.restart_checkpoint)).hexdigest(),
        reference_spectrum_sha256=sha(reference.eigenvalues),current_operator_sha256=sha(packet),
        current_spectrum_sha256=sha(current.eigenvalues))
    with args.output.open('xb') as stream: stream.write(canonical(record))


if __name__ == '__main__': main()
