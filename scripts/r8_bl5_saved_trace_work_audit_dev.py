"""Audit saved flat affine reference states; no model construction or solve.

Native director gaps use (director_x,director_y), not (rotation_x,rotation_y).
For the recorded identity frames, common physical channels equal
(-g_tx,-g_ty,-g_tz,g_dy,-g_dx). The same orthogonal map transforms density.
This compares discrete traces, not admissibility of substituting a new trace.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_info


def common_channels(values):
    return np.array((-values[0], -values[1], -values[2], values[4], -values[3]))


def physical_gap(beam, shell, director, rb=-.05, rs=.0175):
    return np.array((beam[0]-shell[0]+rb*director[1]-rs*shell[4],
        beam[1]-shell[1]-rb*director[0]+rs*shell[3], beam[2]-shell[2],
        director[0]-shell[3], director[1]-shell[4]))


def row_action(rows, q, ids):
    offsets = {int(n): 6*i for i, n in enumerate(ids)}
    return np.array([sum(v*q[offsets[n]+d-1] for n, d, v in zip(row[::3], row[1::3], row[2::3]))
                     for row in rows]).reshape(len(rows)//10, 5, 2)


def run(root, output):
    pools = threadpool_info()
    assert pools and all(p['num_threads'] == 1 for p in pools)
    inputs = json.loads((root/'native/inputs.json').read_text())
    summary = json.loads((root/'native/summary.json').read_text())
    nx = inputs['layout']['nx']
    ns = len(inputs['layout']['shell_node_ids'])
    shell_end, physical = 6*ns, inputs['layout']['counts']['physical_dofs']
    traces = inputs['station_traces']
    assert nx in (16, 32) and len(traces) == 4*nx and physical == 6*(ns+2*nx+1)
    support_count = len(inputs['policy']['support_endpoints_m'])-1
    assert (nx, support_count) in ((16, 8), (32, 8), (32, 16))
    assert inputs['policy']['support_endpoints_m'] == [i/support_count for i in range(support_count+1)]
    with np.load(root/'native/operators.npz', allow_pickle=False) as op:
        c = sparse.csr_matrix((op['C_data'], op['C_indices'], op['C_indptr']), shape=tuple(op['C_shape']))
    result = {'scope': 'saved-state trace/work development only; no causal allocation/locking/F03 acceptance',
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'channel_map': 'native g=(-common translation, -common Ry, common Rx); same orthogonal density map',
              'nx': nx, 'support_count': support_count, 'pools': pools, 'cases': {}, 'source_files': {}}
    for name in ('inputs.json', 'operators.npz', 'summary.json'):
        path = root/'native'/name
        result['source_files']['native/'+name] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert summary['status'] == 'COMPLETED_DEVELOPMENT_ONLY'
    cases = tuple(summary['cases'])
    assert cases and set(cases).issubset(('fy', 'mx', 'mz')) and (nx == 16 or support_count == 16 or cases == ('mx',))
    for case in cases:
        paths = [root/'native'/case/'raw-state.npz', root/'native'/case/'physical-transfer.json',
                 root/'external'/case/'inputs.json', root/'external'/case/'raw-inventory.json',
                 root/'external'/case/'recovered-actions.json']
        result['source_files'].update({str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
        with np.load(paths[0], allow_pickle=False) as saved:
            q, lam = saved['q'].copy(), saved['multipliers'].copy()
            ids, load = saved['external_ids'].copy(), saved['load'].copy()
        transfer = json.loads(paths[1].read_text())
        external_inputs = json.loads(paths[2].read_text())
        external_raw = json.loads(paths[3].read_text())
        external_action = json.loads(paths[4].read_text())
        exq = np.array([external_raw['poses'][str(n)] for n in ids]).ravel()
        moments_broken, moments_nodal, moments_external = (np.zeros((support_count, 5, 2)) for _ in range(3))
        psi_error = np.zeros(3); psi_reference = np.zeros(3)
        station_errors, records = [], []
        density_common = np.empty((support_count, 5, 2))
        for support in range(support_count):
            native = np.array([lam[2*(channel*support_count+support):2*(channel*support_count+support)+2] for channel in range(5)])
            density_common[support] = common_channels(native)
        for trace, action in zip(traces, transfer['station_records']):
            port = trace['beam_port']; slots = trace['full_slots']
            assert np.array_equal(port['frame'], np.eye(3)) and np.array_equal(port['lift_m'], np.zeros(3))
            assert trace['reference_arm_m'] == [0., 0., -.05] and trace['thickness_m'] == .035
            first, second = port['node_indices']; alpha = port['weight']; sw = trace['shell_alpha']
            shell = (1-sw)*q[slots[:6]]+sw*q[slots[6:12]]
            exshell = (1-sw)*exq[slots[:6]]+sw*exq[slots[6:12]]
            beam = (1-alpha)*q[shell_end+6*first:shell_end+6*(first+1)]+alpha*q[shell_end+6*second:shell_end+6*(second+1)]
            exbeam = (1-alpha)*exq[shell_end+6*first:shell_end+6*(first+1)]+alpha*exq[shell_end+6*second:shell_end+6*(second+1)]
            cell_slot = physical+24*port['member_index']+3*port['native_cell']
            director = q[cell_slot:cell_slot+3]
            broken = physical_gap(beam, shell, director)
            nodal = physical_gap(beam, shell, beam[3:])
            exterior = physical_gap(exbeam, exshell, exbeam[3:])
            actual = common_channels(action['five_channel_gap'])
            station_errors.append(float(np.max(np.abs(broken-actual))))
            x, weight = action['x_m'], trace['measure_m']
            support = min(support_count-1, int(x*support_count)); xi = 2*support_count*x-(2*support+1)
            for values, target in ((broken, moments_broken), (nodal, moments_nodal), (exterior, moments_external)):
                target[support] += weight*values[:, None]*np.array((1., xi))
            if .25 <= x <= .75:
                psi_error += weight*(director-beam[3:])**2
                psi_reference += weight*director**2
            records.append({'x_m': x, 'measure_m': weight, 'support': support,
                'native_broken_physical_gap': broken.tolist(), 'native_common_nodal_gap': nodal.tolist(),
                'external_common_nodal_gap': exterior.tolist(), 'cell_director': director.tolist(),
                'native_nodal_P1_rotation': beam[3:].tolist()})
        direct_native = (c@q).reshape(5, support_count, 2).transpose(1, 0, 2)
        expected_broken = np.array([common_channels(v) for v in direct_native])
        independent_nodal = row_action(external_inputs['physical_rows'], q[:physical], ids)
        independent_external = row_action(external_inputs['physical_rows'], exq, ids)
        # Independent saved Jacobian and independently integrated external hats.
        np.testing.assert_allclose(moments_broken, expected_broken, rtol=1e-9, atol=1e-17)
        np.testing.assert_allclose(moments_nodal, independent_nodal, rtol=1e-9, atol=1e-17)
        np.testing.assert_allclose(moments_external, independent_external, rtol=1e-9, atol=1e-17)
        assert max(station_errors) < 1e-15
        delta = moments_nodal-moments_broken
        elam = np.array(external_action['row_density_multipliers']).reshape(support_count, 5, 2)
        work = float(q@load)
        contributions = np.sum(density_common*delta, axis=2)
        external_contributions = np.sum(elam*delta, axis=2)
        result['cases'][case] = {'station_broken_reconstruction_max_abs': max(station_errors),
            'native_actual_moment_max_abs': float(np.max(np.abs(moments_broken))),
            'native_common_nodal_moment_max_abs': float(np.max(np.abs(moments_nodal))),
            'external_common_nodal_moment_max_abs': float(np.max(np.abs(moments_external))),
            'actual_native_applied_work_J': work,
            'native_density_trace_difference_work_J': float(np.sum(contributions)),
            'native_density_absolute_trace_difference_work_J': float(np.sum(np.abs(contributions))),
            'external_density_trace_difference_work_J': float(np.sum(external_contributions)),
            'trace_work_to_applied_signed': float(np.sum(contributions))/max(abs(work), 1e-12),
            'interior_cell_minus_nodal_rotation_L2_rad_sqrt_m': np.sqrt(psi_error).tolist(),
            'interior_cell_rotation_reference_L2_rad_sqrt_m': np.sqrt(psi_reference).tolist(),
            'moment_difference_support_channel_degree': delta.tolist(),
            'native_density_work_support_channel_J': contributions.tolist(),
            'external_density_work_support_channel_J': external_contributions.tolist(),
            'native_common_physical_density_support_channel_degree': density_common.tolist(),
            'stations': records,
            'interpretation_limit': 'Common P1 substitution is not an admissible native element variation by assumption. '
                'Different gap/work witnesses do not prove the whole force-distribution discrepancy is caused by this trace.'}
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({case: {key: values[key] for key in ('native_actual_moment_max_abs',
        'native_common_nodal_moment_max_abs','native_density_trace_difference_work_J','trace_work_to_applied_signed')}
        for case, values in result['cases'].items()}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.output)
