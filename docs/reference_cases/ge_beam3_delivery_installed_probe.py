"""Standalone -I public-workflow probe, copied outside the repository before use."""
from pathlib import Path
from hashlib import sha256
from dataclasses import asdict, is_dataclass
import json
import sys


def main():
    target, dependencies, inputs, output = map(lambda p: Path(p).resolve(), sys.argv[1:])
    assert sys.flags.isolated and not sys.flags.optimize
    assert not Path.cwd().is_relative_to(Path('C:/Github'))
    sys.path[:] = [str(target), str(dependencies)] + [p for p in sys.path if p
        and not Path(p).resolve().is_relative_to(Path('C:/Github'))
        and 'site-packages' not in p.lower()]
    class NoResearch:
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in {'docs', 'tests', 'sympy', 'mpmath'}:
                raise ImportError('research import forbidden')
            return None
    sys.meta_path.insert(0, NoResearch())
    import numpy as np
    import anysolver
    from anysolver import ge_beam3_native as api
    from anysolver.boundary import BoundaryCondition
    output.mkdir(exist_ok=False)
    def canonical(value):
        def encode(v):
            if isinstance(v, np.ndarray): return v.tolist()
            if is_dataclass(v): return asdict(v)
            raise TypeError('unsupported output')
        return (json.dumps(value, default=encode, sort_keys=True, separators=(',', ':'),
                           allow_nan=False)+'\n').encode('ascii')
    def write(name, value):
        raw = value if type(value) is bytes else canonical(value)
        with (output/name).open('xb') as f: f.write(raw)
    def digest(raw): return sha256(raw).hexdigest()
    def definitions(v):
        return tuple(api.BeamDefinition.from_bytes(raw.encode('ascii'),
            expected_sha256=digest(raw.encode('ascii'))) for raw in v['definitions'])
    def boundaries(v):
        return tuple(BoundaryCondition(b['name'], b['node_ids'], b['dof_constraints'])
                     for b in v['boundaries'])
    data = json.loads(inputs.read_bytes())
    checks = {}
    for name, v in data['standalone'].items():
        defs = definitions(v); bcs = boundaries(v)
        def make(): return api.create_analysis(api.SELECTOR, defs, bcs)
        if name == 'fibre':
            p = api.FibreTranslationProgram((.01, .02, 0., -.01), 5, (1., 0., 0.), ((5, .4, -.005, 0.),))
        else:
            p = api.TranslationProgram((.0002, .0003, 0., -.0001), 3, (1., 0., 0.),
                                       api.NodalDeadForces(((3, 1., 0., 0.),)))
        owner = make(); run = owner.solve_translation(p)
        assert run.status == 'completed', run.backend_result.failure
        prefix = owner.translation_checkpoint_prefix(p, run.checkpoint, 2, expected_sha256=run.checkpoint_sha256)
        resumed = make().solve_translation(p, checkpoint=prefix, expected_sha256=digest(prefix))
        assert resumed.checkpoint == run.checkpoint and resumed.status == 'completed'
        recovery = owner.recover_translation(p, run.checkpoint, expected_sha256=run.checkpoint_sha256)
        write(name+'-checkpoint.json', run.checkpoint)
        write(name+'-prefix.json', prefix)
        write(name+'-recovery.json', recovery)
        write(name+'-provenance.json', api.workflow_provenance(owner))
        if name == 'fibre':
            assert any(row[2] > 0 for cell in run.backend_result.state.histories
                       for station in cell.stations for row in station.rows)
        else:
            modes = owner.translation_modes(p, run.checkpoint, expected_sha256=run.checkpoint_sha256,
                                             bounds=(-100., 1e6))
            write('standalone-modes.json', modes)
        checks[name] = dict(checkpoint_sha256=run.checkpoint_sha256,
                           recovery_sha256=digest(canonical(recovery)), restart_equal=True)
        print(name+' public history/replay complete', flush=True)
    for name, v in data['coupled'].items():
        p = v['program']; pattern = p['pattern']
        program = api.DistributedProgram(tuple(p['targets']), api.DistributedPattern(
            api.LinePattern(tuple(map(tuple, pattern['line']['rows']))), tuple(map(tuple, pattern['couples']))),
            p['max_iterations'], p['max_backtracks'])
        controls = v['controls']
        shell = dict(v['shell'])
        shell['coordinates'] = np.array(shell['coordinates'], dtype=float)
        shell['reference_normal'] = np.array(shell['reference_normal'], dtype=float)
        owner = api.create_coupled_analysis(api.SELECTOR, definitions(v), boundaries(v), program,
            shell=shell, shell_density=v['shell_density'], targets=tuple(controls['targets']),
            shell_fixed=tuple(controls['shell_fixed']), nodal_forces=np.array(controls['nodal_forces']),
            max_iterations=controls['max_iterations'], max_backtracks=controls['max_backtracks'])
        first = owner.solve(stop_after=1)
        assert first.status == 'paused', first.failure
        recovery = owner.recover(first.checkpoint, expected_sha256=first.checkpoint_sha256)
        modes = owner.modes(first.checkpoint, expected_sha256=first.checkpoint_sha256,
                            bounds=(-100., 10000.), num_modes=2)
        buckling = owner.buckling(first.checkpoint, expected_sha256=first.checkpoint_sha256,
                                  bounds=(0., 1000.), num_modes=2)
        write(name+'-checkpoint.json', first.checkpoint)
        write(name+'-recovery.json', recovery)
        write(name+'-modes.json', modes); write(name+'-buckling.json', buckling)
        write(name+'-provenance.json', api.workflow_provenance(owner))
        checks[name] = dict(checkpoint_sha256=first.checkpoint_sha256,
                           recovery_sha256=digest(canonical(recovery)), exact_v2_owner=True)
        print(name+' public coupled replay/spectra complete', flush=True)
    assert Path(anysolver.__file__).resolve().is_relative_to(target)
    for name, module in tuple(sys.modules.items()):
        if name == 'anysolver' or name.startswith('anysolver.'):
            assert getattr(module, '__file__', None) and Path(module.__file__).resolve().is_relative_to(target), name
        elif name.split('.')[0] in {'numpy', 'scipy', 'anymaterial', 'anymesher', 'anyfileio', 'anygeometry', 'threadpoolctl', 'shapely'}:
            if getattr(module, '__file__', None): assert Path(module.__file__).resolve().is_relative_to(dependencies), name
    write('complete.json', dict(checks=checks, profile_sha256=api.PROFILE_SHA256,
        research_imports=False, exact_target_imports=True, exact_dependency_imports=True,
        artifact_acceptance='PENDING_INDEPENDENT_ADJUDICATION'))


if __name__ == '__main__': main()
