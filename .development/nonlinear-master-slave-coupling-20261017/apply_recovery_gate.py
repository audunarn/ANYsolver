"""One-off exact line edit: caller passes recover_initial_load_factor (CRLF)."""
import io

PATH = 'src/anysolver/nonlinear_static.py'
src = io.open(PATH, 'r', encoding='utf-8', newline='').read()
lines = src.split('\r\n')

anchor = '            initial_load_factor=('
hits = [i for i, line in enumerate(lines) if line == anchor]
assert len(hits) == 1, hits
i = hits[0]
assert lines[i + 1] == '                float(restored_static_path["load_factor"])'
assert lines[i + 4] == '            ),'
gate = [
    '            recover_initial_load_factor=(',
    '                restored_static_path is None',
    '                and rotating_mpc_map is not None',
    '                and initial_displacements is not None',
    '                and initial_element_states is not None',
    '                and equilibrate_initial_state is False',
    '            ),',
]
lines[i + 5:i + 5] = gate

io.open(PATH, 'w', encoding='utf-8', newline='').write('\r\n'.join(lines))
print('ok')
