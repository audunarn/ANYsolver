"""One fixed-prefix checkpoint/frame discriminant; no production bypass."""
import copy, importlib.util, json, pickle, sys, traceback
from pathlib import Path
import numpy as np
import anysolver.nonlinear_static as ns
from anysolver.corotational import _corotational_cache, _corotational_deformation_state

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('retry_example', HERE/'blocked-candidate/examples/beam_shell_coupling.py')
example = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = example
spec.loader.exec_module(example)
original = ns.create_nonlinear_checkpoint
report = {}
def capture(**kw):
    (HERE/'retry-prefix-input.pkl').write_bytes(pickle.dumps(kw))
    before = pickle.dumps(kw['element_states'])
    try:
        return original(**kw)
    except Exception:
        report['checkpoint_failure'] = traceback.format_exc()
        model = kw['model']
        cache = _corotational_cache(model)
        for eid in (1, 2):
            element = model.mesh.elements[eid]
            q = kw['displacements'][element.get_dof_mapping(model.mesh)]
            local, _, _ = _corotational_deformation_state(cache[eid], element, q)
            for name, u in [('global',q), ('deformational',local)]:
                key = f'{eid}:{name}'
                try:
                    state = element._seal_solver_finalized_current_tangent_state(
                        model.mesh, model.get_material(element.material_name), u,
                        copy.deepcopy(kw['element_states'][eid]), kw['analysis_contract']['num_layers'])
                    element.validate_committed_current_tangent_state(
                        model.mesh, model.get_material(element.material_name), u, state, kw['analysis_contract']['num_layers'])
                    report[key] = 'sealed and validated'
                except Exception:
                    report[key] = traceback.format_exc()
        report['input_states_unchanged'] = before == pickle.dumps(kw['element_states'])
        raise
ns.create_nonlinear_checkpoint = capture
if '--replay' in sys.argv:
    try:
        capture(**pickle.loads((HERE/'retry-prefix-input.pkl').read_bytes()))
    except Exception:
        pass
else:
    report['result'] = example.run_plastic('direct', stage='prefix')
(HERE/'retry-discriminant.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))

