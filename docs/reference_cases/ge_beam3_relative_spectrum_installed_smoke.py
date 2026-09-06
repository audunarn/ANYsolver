"""Installed V2 reference-spectrum correctness; not qualification or release."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


def pairs(rows):
    result = {}
    for key, value in rows:
        if key in result: raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def reject(_): raise ValueError('nonfinite JSON value')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-map', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not sys.flags.isolated or sys.prefix == sys.base_prefix:
        raise RuntimeError('fresh isolated virtual environment required')
    if any(str(Path(p).resolve()).lower().startswith('c:\\github') for p in sys.path if p):
        raise RuntimeError('repository path present')
    class NoResearch:
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in {'docs', 'tests'}: raise ImportError('research import forbidden')
            return None
    sys.meta_path.insert(0, NoResearch())
    import numpy as np
    import scipy
    from scipy.linalg import expm
    from scipy.optimize import brentq
    import anysolver
    from anysolver.fe_core import FEModel
    from anysolver.boundary import BoundaryCondition
    from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry as Reference
    from anysolver._ge_beam3_p5_loads import NativeP5BeamElement, DirectedHardeningSection
    from anysolver._ge_beam3_p5_loads.core import canonical
    from anysolver._ge_beam3_load_program import ForceProgram, solve_force_program
    from anysolver._ge_beam3_relative_virgin_reference_modes import solve_relative_virgin_reference_modes
    from anysolver._relative_reference_svd import relative_reference_svd

    root = Path(anysolver.__file__).resolve().parent
    if not root.is_relative_to(Path(sys.prefix).resolve()): raise RuntimeError('source import escaped target')
    source_map = json.loads(args.source_map.read_text(encoding='utf-8'), object_pairs_hook=pairs, parse_constant=reject)
    if (source_map['schema'] != 'GE_BEAM3_RELATIVE_SPECTRUM_INSTALLED_SOURCE_MAP_V2'
            or source_map['output_text_normalization'] != 'UTF8_LF'
            or source_map['candidate_commit'] != '72e095f5dba8bc0dca11b84131bcf1da4af06bc8'
            or source_map['candidate_tree'] != '664b2f518758f1011ea640988de5230f69e0394d'):
        raise RuntimeError('wrong installed candidate')
    files = {}
    for source, expected in source_map['outputs'].items():
        relative = Path(source).relative_to('src/anysolver'); item = (root/relative).resolve()
        if not item.is_relative_to(root) or not item.is_file(): raise RuntimeError('source path escape')
        raw = item.read_bytes(); normalized = raw.decode('utf-8').replace('\r\n', '\n').encode('utf-8')
        if dict(bytes=len(normalized), sha256=hashlib.sha256(normalized).hexdigest()) != expected:
            raise RuntimeError('installed source mismatch: '+source)
        files[relative.as_posix()] = dict(canonical_sha256=expected['sha256'],
            installed_bytes=len(raw), installed_sha256=hashlib.sha256(raw).hexdigest())
    print('relative installed: source bindings complete', flush=True)

    def model(count, slenderness):
        h = 2/slenderness; ea = 12/h**2; shear = (5/6)*ea/2.6; rotary = h*h/12
        made = FEModel('installed-relative-spectrum')
        points = np.column_stack((np.linspace(0., 2., 2*count+1), np.zeros((2*count+1, 2))))
        for i, p in enumerate(points, 1): made.add_node(i, *p)
        for e in range(count):
            geometry = Reference(points[2*e:2*e+3], np.tile(np.eye(3), (3, 1, 1)))
            section = DirectedHardeningSection(np.diag([ea, shear, shear, 2., 1., 1.]),
                np.array([1., 0., 0., 0., 0., 0.]), 1e6, 1.)
            element = NativeP5BeamElement(e+1, (2*e+1, 2*e+2, 2*e+3), geometry, section, line_force=np.zeros(3))
            made.add_element(e+1, element); made.materials[element.material_name] = element.core.section
        made.add_boundary_condition(BoundaryCondition('root', [1],
            {name: 0. for name in ('ux', 'uy', 'uz', 'rx', 'ry', 'rz')}))
        inertia = {i: np.diag([1., 1., 1., 2*rotary, rotary, rotary]) for i in made.mesh.elements}
        return made, inertia, shear, rotary

    def continuum(shear, rotary):
        # Independent four-field zero-load continuum reconstruction, not an
        # import of producer/reference fixtures or cached finite-element data.
        def determinant(z):
            system = np.array([[0., 1., 1/shear, 0.], [0., 0., 0., 1.],
                               [-z, 0., 0., 0.], [0., -z*rotary, -1., 0.]])
            return float(np.linalg.det(expm(2*system)[2:, 2:]))
        return np.repeat([brentq(determinant, *b, xtol=1e-13, rtol=1e-13, maxiter=80)
            for b in ((-2., 4.), (10., 100.), (100., 400.))], 2)

    def initial(made):
        return {i: e.init_model_bound_nonlinear_state(made.mesh, e.core.section, 1)
            for i, e in made.mesh.elements.items()}

    rows = []; diagnostics = {}
    for slenderness in (100., 1000000.):
        made, inertias, shear, rotary = model(8, slenderness); states = initial(made)
        before = canonical(states); total = np.zeros(made.mesh.dof_manager.total_dofs)
        packet, modes = solve_relative_virgin_reference_modes(made, states, total, inertias)
        if canonical(states) != before: raise RuntimeError('reference call changed states')
        expected = continuum(shear, rotary)
        error = np.sqrt(modes.eigenvalues/expected)-1.
        if np.max(np.abs(error)) >= .02 or modes.normalized_residual > 1e-11:
            raise RuntimeError('installed reference frequency/residual failed')
        for first, second in ((0, 1), (2, 3), (4, 5)):
            if abs(modes.eigenvalues[first]-modes.eigenvalues[second]) > 1e-11*max(1., modes.eigenvalues[second]):
                raise RuntimeError('installed bending pair split')
        if modes.production_qualified or modes.prestressed_tangent_authorized:
            raise RuntimeError('reference scope upgraded')
        encoded = {i: e.serialize_native_material_state(made.mesh, states[i])
            for i, e in made.mesh.elements.items()}
        decoded = json.loads(canonical(encoded), object_pairs_hook=pairs, parse_constant=reject)
        # Restore through the native typed codec before the virgin-state API;
        # JSON-decoding the diagnostic dataclass view would erase state types.
        replay = {int(i): made.mesh.elements[int(i)].validate_model_bound_nonlinear_state(
            made.mesh, made.mesh.elements[int(i)].core.section, value, 1,
            expected_committed_total_u=np.zeros(18)) for i, value in decoded.items()}
        again_packet, again_modes = solve_relative_virgin_reference_modes(made, replay, total, inertias)
        if canonical((packet, modes)) != canonical((again_packet, again_modes)):
            raise RuntimeError('serialized virgin state replay differs')
        name = f'reference-{int(slenderness)}.json'
        raw = canonical(dict(packet=packet, modes=modes, typed_states=encoded, continuum=expected))
        with (args.output.parent/name).open('xb') as stream: stream.write(raw)
        diagnostics[name] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        rows.append(dict(slenderness=slenderness, macros=8, eigenvalues=modes.eigenvalues,
            continuum=expected, frequency_errors=error, state_replay_exact=True))
        print(f'relative installed: eight-macro reference/replay complete L/h={slenderness}', flush=True)

    # Exercise installed load control, then prove this state cannot enter the
    # virgin PSD-only path. Do not reinterpret it or compare as a reference mode.
    made, inertias, _, _ = model(1, 100.)
    loaded = solve_force_program(made, ForceProgram((1.,), ((3, -.1, 0., 0.),)))
    if loaded.status != 'completed': raise RuntimeError(str(loaded.failure))
    states = {r['element_id']: r['state'] for r in json.loads(loaded.checkpoint)['element_states']}
    before = canonical(states)
    for total in (loaded.displacements, np.zeros(18)):
        try: solve_relative_virgin_reference_modes(made, states, total, inertias)
        except ValueError: pass
        else: raise RuntimeError('installed reference accepted a loaded state')
    if canonical(states) != before: raise RuntimeError('rejection changed loaded states')
    with (args.output.parent/'loaded-checkpoint.json').open('xb') as stream: stream.write(loaded.checkpoint)
    diagnostics['loaded-checkpoint.json'] = dict(bytes=len(loaded.checkpoint),
        sha256=hashlib.sha256(loaded.checkpoint).hexdigest())
    _, tiny, _ = relative_reference_svd(np.diag([0., 1e-20, 1., 1e20]))
    if not np.allclose(tiny, [1e20, 1., 1e-20, 0.], rtol=1e-14, atol=0.):
        raise RuntimeError('installed driver erased a tiny singular value')
    for name, module in tuple(sys.modules.items()):
        if name == 'anysolver' or name.startswith('anysolver.'):
            origin = getattr(module, '__file__', None)
            if origin is not None and not Path(origin).resolve().is_relative_to(root):
                raise RuntimeError('ANYsolver import escaped installed target')
    if any(hasattr(anysolver, name) for name in ('solve_relative_virgin_reference_modes',
        'RelativeReferenceFactorSpectrum', 'NativeP5BeamElement')):
        raise RuntimeError('private path publicly exported')
    result = dict(schema='GE_BEAM3_RELATIVE_SPECTRUM_INSTALLED_CHECK_V2',
        production_qualified=False, release_authorized=False, imports_isolated=True,
        research_imports_forbidden=True, loaded_state_rejected=True, tiny_positive_preserved=True,
        runtime=dict(python=sys.version.split()[0], numpy=np.__version__, scipy=scipy.__version__),
        references=rows, diagnostics=diagnostics, source_files=files,
        source_map_sha256=hashlib.sha256(args.source_map.read_bytes()).hexdigest())
    with args.output.open('xb') as stream: stream.write(canonical(result))
    print('relative installed: evidence complete', flush=True)


if __name__ == '__main__': main()
