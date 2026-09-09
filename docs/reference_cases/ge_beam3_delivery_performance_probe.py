"""Frozen warmed B2/B3 operations; no import/startup time in the comparison."""
from pathlib import Path
from hashlib import sha256
import gc
import json
import sys
import time


def main():
    target, dependencies, output = map(lambda p: Path(p).resolve(), sys.argv[1:4])
    index = int(sys.argv[4])
    assert sys.flags.isolated and not sys.flags.optimize and -1 <= index < 12
    assert not Path.cwd().is_relative_to(Path('C:/Github'))
    sys.path[:] = [str(target), str(dependencies)] + [p for p in sys.path if p
        and not Path(p).resolve().is_relative_to(Path('C:/Github'))
        and 'site-packages' not in p.lower()]
    import numpy as np
    import anysolver
    from anysolver.fe_core import FEModel
    from anysolver.elements import BeamElement, QuadraticBeamElement
    from anysolver.boundary import BoundaryCondition, LoadCase
    from anysolver.assembly import solve_linear
    from anysolver.matrix_assembly import assemble_stiffness_matrix
    from anysolver.nonlinear_static import solve_static_nonlinear
    from anysolver.nonlinear_restart import load_nonlinear_checkpoint, canonical_checkpoint_json_bytes
    assert Path(anysolver.__file__).resolve().is_relative_to(target)
    def digest(raw): return sha256(raw).hexdigest()
    def array_digest(a): return digest(np.ascontiguousarray(a, dtype='<f8').tobytes())
    def recovery_digest(value):
        def encode(v):
            if isinstance(v,np.ndarray):return v.tolist()
            if isinstance(v,np.generic):return v.item()
            raise TypeError('unsupported recovery record')
        return digest(json.dumps(value,default=encode,sort_keys=True,separators=(',', ':'),allow_nan=False).encode('ascii'))
    def measure(operation, repetitions):
        operation()  # Every operation in every isolated process is warmed.
        gc.collect(); enabled = gc.isenabled(); gc.disable()
        wall = time.perf_counter_ns(); cpu = time.process_time_ns()
        try:
            for _ in range(repetitions): operation()
        finally:
            cpu = time.process_time_ns()-cpu; wall = time.perf_counter_ns()-wall
            if enabled: gc.enable()
        return dict(wall_ns=wall/repetitions, cpu_ns=cpu/repetitions, repetitions=repetitions)
    result = {}; science = {}
    for family in ('B2', 'B3'):
        cls = BeamElement if family == 'B2' else QuadraticBeamElement
        ids = [1, 2] if family == 'B2' else [1, 2, 3]
        coordinates = (0., 2.) if family == 'B2' else (0., 1., 2.)
        section = dict(Iy=3e-5, Iz=2e-5, J=4e-5, area=.02, orientation=(0., 1., 0.))
        def fixture():
            model = FEModel('native-delivery-performance-'+family)
            mat = model.add_material('mat', 210e9, .3, density=7850.)
            for node, x in zip(ids, coordinates): model.add_node(node, x, 0., 0.)
            element = cls(1, ids, 'mat', cross_section=dict(section)); model.add_element(1, element)
            model.add_boundary_condition(BoundaryCondition('fixed', [1], dict.fromkeys(('ux','uy','uz','rx','ry','rz'), 0.)))
            load = LoadCase('physical-tip-dead-force'); load.add_nodal_load(ids[-1], forces=np.array([10., -3., 2.]))
            return model, element, mat, load
        model, element, material, load = fixture()
        displacement = np.linspace(-1e-5, 2e-5, 6*len(ids))
        settings = dict(max_iterations=12, tolerance=1e-12, convergence_settings='legacy',
                        emit_restart_checkpoint=True, num_layers=5)
        def nonlinear(**extra):
            made, _, _, forces = fixture()
            return solve_static_nonlinear(made, forces, **settings, **extra)
        full = nonlinear(max_load_factor=1., num_steps=4)
        first = nonlinear(max_load_factor=.5, num_steps=2)
        assert full.status == first.status == 'completed'
        checkpoint = first.restart_checkpoint_bytes()
        assert canonical_checkpoint_json_bytes(load_nonlinear_checkpoint(checkpoint)) == checkpoint
        def restart():
            return nonlinear(max_load_factor=1., num_steps=2, restart_checkpoint=checkpoint)
        replay = restart()
        assert replay.status == 'completed' and replay.restart_checkpoint_bytes() == full.restart_checkpoint_bytes()
        assert np.array_equal(replay.displacements, full.displacements)
        linear, info = solve_linear(model, load)
        assert info['convergence_info']['status'] == 'converged'
        def physical_force():
            return element.compute_nonlinear_response(model.mesh, material, displacement, tangent=False)[0]
        force=physical_force()
        recovered=element.compute_stresses(model.mesh, displacement, material)
        assert np.isfinite(force).all() and np.linalg.norm(force)>0.
        assert isinstance(recovered,dict) and recovered
        assert any(np.any(np.asarray(v)!=0.) for v in recovered.values() if isinstance(v,(float,int,np.ndarray)))
        ops = dict(CONSTRUCTION=(lambda: cls(2, ids, 'mat', cross_section=dict(section)), 256),
            STIFFNESS=(lambda: element.compute_stiffness_matrix(model.mesh, material), 64),
            INTERNAL_FORCE=(physical_force, 64),
            ASSEMBLY=(lambda: assemble_stiffness_matrix(model), 32),
            SOLVE=(lambda: solve_linear(model, load), 16),
            RECOVERY=(lambda: element.compute_stresses(model.mesh, displacement, material), 64),
            NONLINEAR_SOLVE=(lambda: nonlinear(max_load_factor=1., num_steps=4), 8),
            RESTART=(restart, 8))
        result[family] = {name: measure(operation, repetitions) for name, (operation, repetitions) in ops.items()}
        science[family] = dict(linear_sha256=array_digest(linear),
            force_sha256=array_digest(force),recovery_sha256=recovery_digest(recovered),
            stiffness_sha256=array_digest(element.compute_stiffness_matrix(model.mesh, material)),
            checkpoint_sha256=digest(checkpoint), replay_sha256=digest(replay.restart_checkpoint_bytes()),
            final_sha256=digest(full.restart_checkpoint_bytes()), actual_replay_equal=True)
        print(family+' warmed operations complete', flush=True)
    modules = {}
    for name, module in tuple(sys.modules.items()):
        if name == 'anysolver' or name.startswith('anysolver.'):
            path = Path(module.__file__).resolve(); assert path.is_relative_to(target), name
            modules[path.relative_to(target).as_posix()] = digest(path.read_bytes())
        elif name.split('.')[0] in {'numpy','scipy','anymaterial','anymesher','anyfileio','anygeometry','threadpoolctl','shapely'}:
            if getattr(module, '__file__', None): assert Path(module.__file__).resolve().is_relative_to(dependencies), name
    value = dict(schema='GE_BEAM3_DELIVERY_WARMED_LEGACY_PERFORMANCE_V1', sample=index,
        operations=result, science=science, resolved_solver_modules=modules,
        import_timing_included=False, source_or_target=str(target), dependencies=str(dependencies))
    with output.open('xb') as stream:
        stream.write((json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('ascii'))


if __name__ == '__main__': main()
