from pathlib import Path
import json
r=Path.cwd();s=(r/'b2_e01_finite_point_native.py').read_text();s=s.replace('import numpy as np',"sys.path.insert(0,"+repr(json.loads((r/'manifest.json').read_text())['native_site'])+")\nimport numpy as np")
a=s.index('                for name, component, magnitude in reference.LOADS:');b=s.index('            finally:',a)
s=s[:a]+'''                for name, component, magnitude in reference.LOADS:
                    source=output.parent/f'panel-{sign}-{name}'/f'panel-{sign}-{name}.json'
                    external=json.loads(source.read_text())
                    u=np.array([v for node in reference.NODE_IDS for v in external['nodal_states'][str(node)]])
                    native_internal=np.asarray(owner._K@u).reshape(-1)
                    external_internal=np.asarray(external['internal_covector'])
                    external_elements={v['element']:np.asarray(v['global_covector']) for v in external['element_global_covectors']}
                    beam_native=np.zeros(54);beam_external=np.zeros(54);beam_checks=[]
                    scale_f=magnitude if component<3 else magnitude/2.
                    for member_id,(compiled,slots) in owner._members:
                        tag=101+int(member_id.split('-')[-1])
                        local_map=compiled.local_dof_map()
                        k=local_map.T@compiled.operator.evaluate(np.zeros(12)).tangent@local_map
                        force=np.asarray(k@u[slots]).reshape(-1)
                        expected_force=external_elements[tag]
                        beam_native[slots]+=force;beam_external[slots]+=expected_force
                        errors=np.abs(force-expected_force)/np.tile([scale_f]*3+[2*scale_f]*3,2)
                        beam_checks.append({'member':member_id,'load_scaled_covector_error':float(np.max(errors))})
                    row_scale=np.tile([scale_f]*3+[2*scale_f]*3,9)
                    shell_difference=native_internal-beam_native-(external_internal-beam_external)
                    full_difference=native_internal-external_internal
                    record['cases'].append({'name':name,'beam_checks':beam_checks,
                        'full_operator_difference_load_scaled':float(np.max(np.abs(full_difference)/row_scale)),
                        'shell_operator_difference_load_scaled':float(np.max(np.abs(shell_difference)/row_scale)),
                        'beam_covector_parity_passed':all(v['load_scaled_covector_error']<=1e-10 for v in beam_checks)})
''' +s[b:]
s=s.replace("PASSED_NATIVE_FIXED_SCREEN_ONLY","SAME_STATE_COVECTOR_DIAGNOSTIC_ONLY")
(r/'allocation.py').write_text(s)
