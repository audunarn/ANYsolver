"""Frozen actual Newton-state element derivative decomposition; harness only."""
import argparse
import copy
import json
import pickle
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tests'))
from test_nonlinear_beam_shell_slice3_continuation import _build_ep_model
import anysolver.corotational as cr
from assessment_support import identical, source_identity


def main():
    p = argparse.ArgumentParser()
    p.add_argument('capture'); p.add_argument('output')
    a = p.parse_args(); out = Path(a.output)
    out.mkdir(parents=True, exist_ok=False)
    c = pickle.loads(Path(a.capture).read_bytes())
    model, *_ = _build_ep_model('interp')
    mapping = cr.build_nonlinear_rotating_mpc_map(model, c['T'])
    before = copy.deepcopy(c['states']); u_before = c['u'].copy()
    du = np.asarray(mapping.jacobian(c['u']) @ c['delta'][:-1]).reshape(-1)
    rows = []; raw = {}
    for eid, el in model.mesh.elements.items():
        ref = cr._corotational_cache(model).get(eid)
        if ref is None or ref.category is None:
            continue
        dofs = np.concatenate([model.mesh.dof_manager.get_node_dofs(n) for n in el.node_ids])
        ue = c['u'][dofs]; direction = du[dofs]
        state = c['states'].get(eid)
        material = model.get_material(el.material_name)
        def evaluate(alpha):
            value = ue + alpha*direction
            history = copy.deepcopy(state); frozen = copy.deepcopy(history)
            f, k, trial = cr.corotational_work_conjugate_response(model, eid, el, value, True, history)
            assert identical(history, frozen)
            ud, R, deformed = cr._corotational_deformation_state(ref, el, value)
            D, U, G = cr._pullback_jacobian_factors(ref, el, deformed, value.reshape(-1, 6)[:, 3:], R)
            fl, kl, local_trial = el.compute_nonlinear_response(model.mesh, material, ud, copy.deepcopy(state), 5, True)
            return dict(f=f, k=k, ud=ud, fl=fl, kl=kl, b=D+U@G, trial=trial)
        base = evaluate(0)
        predicted = base['k']@direction
        predicted_local = base['kl']@(base['b']@direction)
        records = []
        for h in (1e-4, 1e-5, 1e-6, 1e-7, 1e-8):
            plus, minus = evaluate(h), evaluate(-h)
            rec = dict(h=h)
            for name, key, expected in [('global', 'f', predicted), ('local', 'fl', predicted_local)]:
                scale = max(float(np.linalg.norm(expected)), 1e-30)
                rec[name] = dict(scale=scale,
                    forward=float(np.linalg.norm((plus[key]-base[key])/h-expected)/scale),
                    backward=float(np.linalg.norm((base[key]-minus[key])/h-expected)/scale))
            for name, ev in [('base',base), ('plus',plus), ('minus',minus)]:
                rec[name+'_alpha_max'] = float(np.max(ev['trial'].get('alpha', 0)))
                rec[name+'_alpha_changes'] = int(np.count_nonzero(np.asarray(ev['trial'].get('alpha', 0))-np.asarray((state or {}).get('alpha', 0))))
            records.append(rec)
            raw[eid,h] = (base,plus,minus)
        rows.append(dict(eid=eid, category=ref.category, checks=records))
    assert identical(c['states'], before) and np.array_equal(c['u'], u_before)
    (out/'raw.pkl').write_bytes(pickle.dumps(raw))
    report=dict(identity=source_identity(), input_unchanged=True, elements=rows)
    (out/'result.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(rows), flush=True)

if __name__ == '__main__': main()
