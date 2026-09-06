"""Isolated native displacement/arc correctness check, not qualification."""

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
        raise RuntimeError('repository search path present')

    class NoResearch:
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in {'docs', 'tests'}:
                raise ImportError('research imports forbidden')
            return None

    sys.meta_path.insert(0, NoResearch())
    import numpy as np
    import scipy
    import anysolver
    from anysolver.fe_core import FEModel
    from anysolver.boundary import BoundaryCondition
    from anysolver.control import CancellationToken
    from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as Reference
    from anysolver._ge_beam3_p5_loads import NativeP5BeamElement, DirectedHardeningSection
    from anysolver._ge_beam3_p5_loads.core import canonical, sha
    from anysolver._ge_beam3_displacement_program import DisplacementProgram, solve_displacement_program
    from anysolver._ge_beam3_arc_program import ArcProgram, solve_arc_program

    root = Path(anysolver.__file__).resolve().parent
    if not root.is_relative_to(Path(sys.prefix).resolve()):
        raise RuntimeError('ANYsolver did not originate in installed target')
    source_map = json.loads(args.source_map.read_text(encoding='utf-8'))
    if source_map['output_text_normalization'] != 'UTF8_LF':
        raise RuntimeError('explicit source text normalization required')
    files = {}
    for source, expected in source_map['outputs'].items():
        relative = Path(source).relative_to('src/anysolver')
        raw = (root/relative).read_bytes()
        text = raw.decode('utf-8').replace('\r\n', '\n').encode('utf-8')
        if dict(bytes=len(text), sha256=hashlib.sha256(text).hexdigest()) != expected:
            raise RuntimeError('installed source identity mismatch: '+source)
        files[relative.as_posix()] = dict(canonical_sha256=expected['sha256'],
            installed_bytes=len(raw), installed_sha256=hashlib.sha256(raw).hexdigest())

    def model():
        # Independently constructed small curved, coupled, plastic fixture.
        # No imports from repository fixture modules or mechanics oracles.
        made = FEModel('installed-control-programs')
        ids = (7, 23, 55)
        parameters = (-1., 0., 1.)
        points = np.array([[x, .5*(1-x*x), .25*(1-x*x)] for x in parameters])
        frames = []
        for x in parameters:
            first = np.array([1., -x, -.5*x]); first /= np.linalg.norm(first)
            second = np.array([0., 0., 1.]); second -= first*float(first@second)
            second /= np.linalg.norm(second)
            frames.append(np.column_stack((first, second, np.cross(first, second))))
        for i, point in zip(ids, points): made.add_node(i, *point)
        factor = np.array([[2., .1, 0., .2, -.1, 0.], [0., 3., .2, 0., .3, .1],
            [0., 0., 4., .1, 0., .2], [0., 0., 0., 1., .1, .2],
            [0., 0., 0., 0., 1.5, .1], [0., 0., 0., 0., 0., 2.]])
        section = DirectedHardeningSection(factor.T@factor,
            np.array([1., .2, -.1, .3, -.4, .5]), .02, .4)
        element = NativeP5BeamElement(1, ids, Reference(points, np.array(frames)), section,
            line_force=np.array([.03, -.02, .01]))
        made.add_element(1, element); made.materials[element.material_name] = element.core.section
        made.add_boundary_condition(BoundaryCondition('root', [7],
            {name: 0. for name in ('ux', 'uy', 'uz', 'rx', 'ry', 'rz')}))
        return made

    def done(result, count):
        if result.status != 'completed' or result.completed_targets != count:
            raise RuntimeError(str((result.status, result.failure)))
        if result.production_qualified or result.displacements.flags.writeable:
            raise RuntimeError('invalid private-result boundary')

    def rejected(solver, program, capsule):
        try: solver(model(), program, checkpoint=capsule)
        except ValueError: return
        raise RuntimeError('malformed installed checkpoint accepted')

    print('installed_controls: source binding complete', flush=True)
    records = {}
    for name, solver, program, count, split in (
        ('displacement', solve_displacement_program,
         DisplacementProgram((.02, .04, 0., -.02), 55, 'ux'), 4, 2),
        ('arc', solve_arc_program, ArcProgram((.2, .2, .2), 2.), 3, 1),
    ):
        made = model(); full = solver(made, program); done(full, count)
        paused = solver(model(), program, stop_after=split)
        if paused.status != 'paused': raise RuntimeError('installed pause failed')
        resumed = solver(model(), program, checkpoint=paused.checkpoint); done(resumed, count)
        if resumed.checkpoint != full.checkpoint:
            raise RuntimeError('installed split restart differs')
        value = json.loads(full.checkpoint)
        element = made.mesh.elements[1]
        state = element.validate_model_bound_nonlinear_state(made.mesh, element.core.section,
            value['element_states'][0]['state'], 1, expected_committed_total_u=full.displacements)
        if not any(h.accumulated > 0. for h in state['material_state']['histories']):
            raise RuntimeError('installed plastic path not exercised')
        recovery = element.recover_native_fields(made.mesh, state)
        if recovery['load_parameter'] != full.parameter:
            raise RuntimeError('installed recovery parameter mismatch')
        if name == 'arc' and value['last_origin'] is None:
            raise RuntimeError('arc preceding origin missing')
        if name == 'displacement' and value['records'][-1]['displacement_target'] != -.02:
            raise RuntimeError('displacement reversal target missing')
        print('installed_controls: '+name+' plastic restart and recovery complete', flush=True)

        # Test both sides of the commit boundary, then restore the retained state.
        for suffix, accepted in (('before_commit', 0), ('committed', 1)):
            token = CancellationToken()
            def cancel(event):
                if event['stage'] == 'native_'+name+'.'+suffix:
                    token.cancel('installed control cancellation fixture')
            cancelled = solver(model(), program, cancellation_token=token, progress=cancel)
            if cancelled.status != 'cancelled' or cancelled.completed_targets != accepted:
                raise RuntimeError('installed cancellation advanced wrong state')
            retained = solver(model(), program, checkpoint=cancelled.checkpoint, stop_after=accepted)
            if retained.checkpoint != cancelled.checkpoint:
                raise RuntimeError('cancelled installed capsule cannot replay')

        mutated = json.loads(full.checkpoint)
        mutated['physical_imbalance'][0] += .01
        body = {k: v for k, v in mutated.items() if k != 'checkpoint_sha256'}
        rejected(solver, program, canonical({**body, 'checkpoint_sha256': sha(body)}))
        rejected(solver, program, full.checkpoint.replace(b'{', b'{"schema":"duplicate",', 1))
        with (args.output.parent/(name+'-checkpoint.json')).open('xb') as stream:
            stream.write(full.checkpoint)
        records[name] = dict(accepted_steps=count, restart_exact=True, plastic_history_exercised=True,
            commit_boundary_cancellation_preserved=True, resealed_reaction_mutation_rejected=True,
            duplicate_key_rejected=True, recovery_parameter_bound=True,
            checkpoint_bytes=len(full.checkpoint), checkpoint_sha256=hashlib.sha256(full.checkpoint).hexdigest(),
            displacement_sha256=sha(full.displacements), physical_reaction_sha256=sha(full.physical_imbalance),
            recovery_sha256=sha(recovery))
        print('installed_controls: '+name+' cancellation and mutations complete', flush=True)

    for name, module in tuple(sys.modules.items()):
        if name == 'anysolver' or name.startswith('anysolver.'):
            origin = getattr(module, '__file__', None)
            if origin is not None and not Path(origin).resolve().is_relative_to(root):
                raise RuntimeError('ANYsolver import escaped installed target')
    if any(hasattr(anysolver, name) for name in ('DisplacementProgram', 'ArcProgram', 'NativeP5BeamElement')):
        raise RuntimeError('private control or element publicly exported')
    record = dict(schema='GE_BEAM3_NATIVE_CONTROL_PROGRAMS_INSTALLED_CHECK_V1', production_qualified=False,
        release_authorized=False, imports_isolated=True, research_imports_forbidden=True,
        runtime=dict(python=sys.version.split()[0], numpy=np.__version__, scipy=scipy.__version__),
        controls=records, source_files=files, source_map_sha256=hashlib.sha256(args.source_map.read_bytes()).hexdigest())
    with args.output.open('xb') as stream: stream.write(canonical(record))
    print('installed_controls: evidence complete', flush=True)


if __name__ == '__main__': main()
