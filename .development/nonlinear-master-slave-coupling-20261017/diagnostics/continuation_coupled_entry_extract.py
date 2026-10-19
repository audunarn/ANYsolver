"""Read-only algebra/metadata extraction; no material or force evaluation."""
import argparse
import hashlib
import json
import pickle
from pathlib import Path
import numpy as np


def convert(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    raise TypeError(type(value).__name__)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('coupled')
    p.add_argument('oldcone')
    p.add_argument('output')
    args = p.parse_args()
    folder, oldfolder, out = map(Path, (args.coupled, args.oldcone, args.output))
    out.mkdir(parents=True, exist_ok=False)
    raw = pickle.loads((folder/'raw.pkl').read_bytes())
    result = json.loads((folder/'result.json').read_text())
    old = pickle.loads((oldfolder/'predictor-raw.pkl').read_bytes())
    cone = json.loads((oldfolder/'cone.json').read_text())
    base = raw['base']
    oldbase = old['accepted_H11']
    oldA, oldB = old['direction-1-selected'], old['direction-2-selected']
    oldswitch = np.asarray(cone['switching_indices'], dtype=int)
    names, loading, hardening, near = [], [], [], []
    eps = np.finfo(float).eps
    for block in result['stress_layout']:
        eid, count, kind = block['element'], block['points'], block['kind']
        entry = 1e-9 if kind == 'beam' else 1e-10
        closure = 1e-8 if kind == 'beam' else 1e-10
        for law in ('loading', 'hardening_y1', 'hardening_y2'):
            for point in range(count):
                index = len(names)
                names.append(dict(index=index, element=eid, point=point, kind=kind, law=law))
                loading.append(law == 'loading')
                hardening.append(law != 'loading')
                near.append(law == 'loading' and abs(oldbase['events'].values[index]+entry) <= closure+64*eps)
    loading, hardening, near = map(np.asarray, (loading, hardening, near))
    fixed = near.copy()
    fixed[oldswitch] = False
    assert int(near.sum()) == 42 and int(fixed.sum()) == 26
    assert len(names) == len(base['events'].values)
    def changes(signature, reference, mask=None):
        difference = signature != reference
        if mask is not None:
            difference &= mask
        return [names[i] for i in np.flatnonzero(difference)]
    branches = []
    values = []
    previous = base['events'].signature
    for path in sorted(folder.glob('post-entry-iterate-*.pkl')):
        value = pickle.loads(path.read_bytes())
        values.append(value)
        signature = value['events'].signature
        branches.append(dict(file=path.name,
            production_R=float(np.linalg.norm(value['rp'])),
            extended_R=float(np.linalg.norm(value['re'])),
            local_strain_norm=float(np.linalg.norm(value['local'])),
            branch_sha256=hashlib.sha256(signature.tobytes()).hexdigest(),
            actual_loading_points=int(np.sum(signature & loading)),
            loading_changed_vs_base=changes(signature, base['events'].signature, loading),
            hardening_changed_vs_base=changes(signature, base['events'].signature, hardening),
            changed_vs_previous=changes(signature, previous),
            old_fixed26_changed_vs_base=changes(signature, base['events'].signature, fixed),
            old_fixed26_changed_vs_A=changes(signature, oldA['events'].signature, fixed),
            old_fixed26_changed_vs_B=changes(signature, oldB['events'].signature, fixed),
            old_A_differences=changes(signature, oldA['events'].signature),
            old_B_differences=changes(signature, oldB['events'].signature)))
        previous = signature
    final = values[-1]
    n = len(final['q'])
    G = final['matrix'][:n, n+1:]*4000.
    local = final['local']
    contributions, vectors = [], []
    for block in result['stress_layout']:
        for point in range(block['points']):
            first = block['offset']+point*block['components']
            last = first+block['components']
            vector = G[:, first:last]@local[first:last]
            vectors.append(vector)
            contributions.append(dict(element=block['element'], point=point, kind=block['kind'],
                mismatch_vector_norm_N=float(np.linalg.norm(vector)),
                scaled_stress_mismatch=local[first:last].copy(),
                stress_mismatch_Pa=final['E'][first:last]*local[first:last],
                vector=vector.copy()))
    sum_vector = np.sum(vectors, axis=0)
    discrepancy = final['re']-final['rp']
    closure = float(np.linalg.norm(sum_vector-discrepancy))
    arithmetic = 64*eps*(sum(np.linalg.norm(v) for v in vectors)+np.linalg.norm(final['re'])+np.linalg.norm(final['rp']))
    # Stored physical force accumulation and reduced dot products use different
    # orders, so report closure/envelope rather than inventing an exact identity.
    ordered = sorted(contributions, key=lambda v: v['mismatch_vector_norm_N'], reverse=True)
    summary = dict(metadata_only=True, force_material_global_solves=0,
        canonical_source_base_matches_old=bool(np.array_equal(base['events'].values, oldbase['events'].values)),
        old_switching_faces=int(len(oldswitch)), old_near_faces=int(near.sum()), old_fixed_faces=int(fixed.sum()),
        iterations=len(branches), branches=branches,
        final_actual_R_N=float(np.linalg.norm(final['rp'])),
        final_extended_R_N=float(np.linalg.norm(final['re'])),
        final_constitutive_force_N=float(np.linalg.norm(discrepancy)),
        attribution_sum_norm_N=float(np.linalg.norm(sum_vector)),
        attribution_closure_N=closure, point_summation_roundoff_estimate_N=float(arithmetic),
        unmeasured_attribution_roundoff='Accumulation/reduction of the stored full physical forces is not included in the point-summation estimate.',
        sum_point_norms_N=float(sum(np.linalg.norm(v) for v in vectors)),
        dominant_points=[{k: v for k, v in item.items() if k != 'vector'} for item in ordered[:8]],
        any_old_fixed26_changed=any(bool(item['old_fixed26_changed_vs_base']) for item in branches),
        hardening_changes_present=any(bool(item['hardening_changed_vs_base']) for item in branches),
        interpretation='Stored metadata and algebra only; contributions cancel as vectors; no new force/material/geometry evaluation or nonlinear-root/nonexistence inference.')
    arrays = dict(indicator_metadata=names, near_mask=near, old_fixed_mask=fixed,
        old_switching_indices=oldswitch, branches=branches, point_contributions=contributions,
        sum_vector=sum_vector, actual_constitutive_discrepancy=discrepancy)
    (out/'attribution.pkl').write_bytes(pickle.dumps(arrays))
    (out/'result.json').write_text(json.dumps(summary, indent=2, default=convert))
    print(json.dumps({k: v for k, v in summary.items() if k not in ('branches', 'dominant_points')}, default=convert))


if __name__ == '__main__':
    main()
