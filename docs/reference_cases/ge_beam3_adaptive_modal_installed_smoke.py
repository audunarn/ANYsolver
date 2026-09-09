"""Isolated native adaptive control/loaded-modal correctness check, not qualification."""

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
    from anysolver._ge_beam3_arc_program import ArcProgram
    from anysolver._ge_beam3_adaptive_arc_program import AdaptiveArcProgram, solve_adaptive_arc_program
    from anysolver._ge_beam3_load_program import ForceProgram, solve_force_program
    from anysolver._ge_beam3_loaded_modal import solve_elastic_modes

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

    def model(*, plastic=True):
        # Independently constructed small curved, coupled, plastic fixture.
        # No imports from repository fixture modules or mechanics oracles.
        made = FEModel('installed-adaptive-modal')
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
            np.array([1., .2, -.1, .3, -.4, .5]), .02 if plastic else 1000., .4)
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


    print('installed_adaptive_modal: source binding complete', flush=True)
    program = AdaptiveArcProgram(ArcProgram((.2,), 2., max_iterations=1),
        max_depth=4, max_attempts=31, max_accepted=16)
    full = solve_adaptive_arc_program(model(), program)
    done(full, full.completed_targets)
    attempts = json.loads(full.checkpoint)['attempts']
    if not any(row['outcome'] == 'CUTBACK' for row in attempts):
        raise RuntimeError('installed diagnostic did not exercise numerical cutback')
    first = solve_adaptive_arc_program(model(), program, stop_after_attempts=3)
    if first.status != 'paused': raise RuntimeError('installed adaptive pause failed')
    resumed = solve_adaptive_arc_program(model(), program, checkpoint=first.checkpoint)
    if resumed.checkpoint != full.checkpoint:
        raise RuntimeError('installed consumed-attempt restart differs')
    bad = json.loads(full.checkpoint); bad['attempts'][0]['step_size'] *= 2.
    body = {key: value for key, value in bad.items() if key != 'checkpoint_sha256'}
    bad = canonical({**body, 'checkpoint_sha256': sha(body)})
    try: solve_adaptive_arc_program(model(), program, checkpoint=bad)
    except ValueError: pass
    else: raise RuntimeError('resealed adaptive attempt mutation accepted')
    print('installed_adaptive_modal: bounded cutback/restart complete', flush=True)

    made = model(plastic=False)
    force_program = ForceProgram((.5, 1.))
    equilibrium = solve_force_program(made, force_program); done(equilibrium, 2)
    states = {row['element_id']: row['state'] for row in json.loads(equilibrium.checkpoint)['element_states']}
    before = canonical(states)
    inertia = np.diag([2., 2., 2., .2, .1, .15])
    packet, modes = solve_elastic_modes(made, states, equilibrium.displacements, {1: inertia},
        np.zeros(18), load_parameter=equilibrium.parameter)
    if canonical(states) != before or not np.all(modes.eigenvalues > 0.):
        raise RuntimeError('loaded-mode state or elastic spectrum mismatch')
    if modes.normalized_residual > 1e-11 or modes.production_qualified or modes.buckling_factor_authorized:
        raise RuntimeError('loaded-mode result boundary mismatch')
    again = solve_force_program(model(plastic=False), force_program, checkpoint=equilibrium.checkpoint)
    done(again, 2)
    replay_states = {row['element_id']: row['state'] for row in json.loads(again.checkpoint)['element_states']}
    replay_packet, replay_modes = solve_elastic_modes(model(plastic=False), replay_states, again.displacements,
        {1: inertia}, np.zeros(18), load_parameter=again.parameter)
    if canonical((packet, modes)) != canonical((replay_packet, replay_modes)):
        raise RuntimeError('installed loaded pencil differs after native restart')
    try:
        solve_elastic_modes(made, states, equilibrium.displacements, {1: inertia}, np.zeros(18), load_parameter=.5)
    except ValueError: pass
    else: raise RuntimeError('installed loaded parameter mismatch accepted')
    with (args.output.parent/'modal-diagnostic.json').open('xb') as stream:
        stream.write(canonical((packet, modes)))
    print('installed_adaptive_modal: loaded-state pencil/restart complete', flush=True)
    records = {}
    for name, checkpoint in (('adaptive', full.checkpoint), ('modal', equilibrium.checkpoint)):
        with (args.output.parent/(name+'-checkpoint.json')).open('xb') as stream: stream.write(checkpoint)
        records[name] = dict(restart_exact=True, checkpoint_bytes=len(checkpoint),
            checkpoint_sha256=hashlib.sha256(checkpoint).hexdigest())
    records['adaptive'].update(accepted_steps=full.completed_targets, attempts=len(attempts),
        cutbacks=sum(row['outcome'] == 'CUTBACK' for row in attempts), resealed_attempt_mutation_rejected=True)
    records['modal'].update(pencil_sha256=sha(packet), modes_sha256=sha(modes),
        accepted_history_preserved=True, load_parameter_mismatch_rejected=True,
        retained_coordinates=len(packet.stiffness), physical_mode_columns=modes.dynamic_map.shape[1])

    for name, module in tuple(sys.modules.items()):
        if name == 'anysolver' or name.startswith('anysolver.'):
            origin = getattr(module, '__file__', None)
            if origin is not None and not Path(origin).resolve().is_relative_to(root):
                raise RuntimeError('ANYsolver import escaped installed target')
    if any(hasattr(anysolver, name) for name in ('AdaptiveArcProgram', 'LoadedModes', 'NativeP5BeamElement')):
        raise RuntimeError('private control or element publicly exported')
    record = dict(schema='GE_BEAM3_NATIVE_ADAPTIVE_MODAL_INSTALLED_CHECK_V1', production_qualified=False,
        release_authorized=False, imports_isolated=True, research_imports_forbidden=True,
        runtime=dict(python=sys.version.split()[0], numpy=np.__version__, scipy=scipy.__version__),
        controls=records, source_files=files, source_map_sha256=hashlib.sha256(args.source_map.read_bytes()).hexdigest())
    with args.output.open('xb') as stream: stream.write(canonical(record))
    print('installed_adaptive_modal: evidence complete', flush=True)


if __name__ == '__main__': main()
