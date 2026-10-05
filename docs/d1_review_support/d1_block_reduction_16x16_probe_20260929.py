"""Historical same-pose probe; requires the removed private candidate branch."""
import json
import time
import traceback
from pathlib import Path

import numpy as np
import psutil

import anysolver.general_contact.q4_s3_overlap_derivatives as derivatives
if not hasattr(derivatives, "_BLOCK_REDUCTION_ENABLED"):
    raise RuntimeError("historical block-reduction candidate is not installed")
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from docs.d1_review_support.d1_two_body_16x16_linearization_preflight import interpolate_target
from docs.d1_review_support.d1_two_body_refined_target_route import build_refined_case

output = Path('reports/d1_block_reduction_16x16_probe_20260929.json')
record = {'status': 'started', 'runs': []}
start = time.perf_counter()
try:
    saved = json.loads(Path('docs/d1_review_support/d1_target_grid_8x8_prediction_20260929.json').read_text())
    assert saved['status'] == 'completed' and saved['accepted_steps'] == 2
    old_model, _, _, _, old_x, old_y = build_refined_case(4, 8, 8)
    fine_model, definition, settings, _, fine_x, fine_y = build_refined_case(4, 16, 16)
    pose = interpolate_target(old_model, np.asarray(saved['final_displacements'], dtype=float),
                              old_x, old_y, fine_model, fine_x, fine_y)
    step = saved['steps'][-1]
    forces = (np.asarray(step['numerical_pressure_pa'], dtype=float)
              * np.asarray(step['reference_support_m2'], dtype=float))
    fine_model.apply_boundary_conditions()
    manager = GeneralS3PatchManager(fine_model, definition, settings)
    record['setup_seconds'] = time.perf_counter()-start
    record['source_module'] = derivatives.__file__
    record['pose_source'] = 'd1_target_grid_8x8_prediction_20260929.json'
    states = {}
    for label in ('old', 'new', 'new', 'old'):
        derivatives._BLOCK_REDUCTION_ENABLED = label == 'new'
        began = time.perf_counter()
        state = linearize(manager, pose, forces, tangent=True)
        duration = time.perf_counter()-began
        record['runs'].append({'path': label, 'seconds': duration,
                               'evaluations': state.evaluations,
                               'triangles': state.state.integration_triangles})
        states[label] = state
    a, b = states['old'], states['new']
    record['branch_parity'] = (a.state.overlap_signature == b.state.overlap_signature)
    record['triangle_parity'] = (a.state.integration_triangles == b.state.integration_triangles)
    record['evaluation_parity'] = (a.evaluations == b.evaluations)
    record['scaled_errors'] = {}
    for name, left, right in (
        ('support', a.state.reference_support, b.state.reference_support),
        ('weighted_gap', a.state.reference_weighted_gap, b.state.reference_weighted_gap),
        ('normalized_gap', a.state.normalized_gap, b.state.normalized_gap),
        ('pressure_gram', a.state.pressure_gram, b.state.pressure_gram),
        ('force', a.force, b.force),
        ('local_force', a.local_force, b.local_force),
        ('gap_gradient', a.gap_gradient, b.gap_gradient),
        ('tangent', a.tangent.toarray(), b.tangent.toarray()),
    ):
        left, right = np.asarray(left), np.asarray(right)
        scale = np.maximum(1., np.maximum(np.abs(left), np.abs(right)))
        record['scaled_errors'][name] = float(np.max(np.abs(left-right)/scale))
    old_times = [item['seconds'] for item in record['runs'] if item['path'] == 'old']
    new_times = [item['seconds'] for item in record['runs'] if item['path'] == 'new']
    record['old_median_seconds'] = float(np.median(old_times))
    record['new_median_seconds'] = float(np.median(new_times))
    record['speed_ratio'] = record['old_median_seconds']/record['new_median_seconds']
    record['rss_mb'] = psutil.Process().memory_info().rss/1e6
    assert record['branch_parity'] and record['triangle_parity'] and record['evaluation_parity']
    assert max(record['scaled_errors'].values()) <= 1e-13
    record['status'] = 'passed'
except Exception:
    record['status'] = 'failed'
    record['traceback'] = traceback.format_exc()
    raise
finally:
    derivatives._BLOCK_REDUCTION_ENABLED = False
    record['elapsed_seconds'] = time.perf_counter()-start
    output.write_text(json.dumps(record, indent=2))
    print(json.dumps({key: record.get(key) for key in (
        'status', 'setup_seconds', 'old_median_seconds', 'new_median_seconds',
        'speed_ratio', 'branch_parity', 'triangle_parity', 'evaluation_parity',
        'scaled_errors', 'rss_mb', 'elapsed_seconds')}, indent=2))
