from scripts import r8_bl5_sparse_envelope_kernel_dev as m
import json
cases=['ns16_b1_8','ns16_b8','ns32_b1_8','ns16_b1_2','ns16_b2','ns32_b1']
old={'ns16_b1_2':m.RAW/'ratios/whole_half/owner-v1','ns16_b2':m.RAW/'ratios/whole_double/owner-v1','ns32_b1':m.RAW/'joint32/installed-v2/owner'}
for key in cases:
 owner=old.get(key,m.RAW/'envelope/owners'/key/'owner-v1')
 m.bind(m.case_from_id(key),owner)
print(json.dumps(dict(status='BOUND',cases=cases,caller_sha256=m.sha(m.__file__))))
