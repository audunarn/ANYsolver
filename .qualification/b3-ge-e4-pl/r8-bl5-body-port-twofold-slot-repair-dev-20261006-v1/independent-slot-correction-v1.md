# Independent slot-domain correction

Disposition: I explicitly withdraw my previous indexing finding. It was wrong, and the global-vector-only change I recommended introduced incorrect material reads. The final explicit shell-count offset corrects that mistake in source. No beam/material evaluation occurred on the wrongly indexed path. Tests remain unexecuted; retry approval is pending and this review grants no job authority or qualification.

Authoritative evidence:
- Current src/anysolver/_stiffened_shell_ge_experimental.py _beam_reference lines346-349 builds beam-local slots: nodal6*beamindex plus retained range(nodal+24*i,nodal+24*(i+1)). Line769 stores tuple(beam_parts) unchanged.
- Exact immutable installed counterpart .qualification/b3-ge-e4-pl/r8-native-fibre-bl5-dev-20261005-v1/installed-s3-v1/anysolver/_stiffened_shell_ge_experimental.py has the same construction at lines345-348 and unchanged storage at767; independently read/hash-checked SHA256 f7f1567a1d485508bd363a53354f8833130dfcf5369218552cd0d6f52961641e. The exact file needed authorized host escalation after default sandbox ACL denial; no directory traversal was performed.
- Native finite assembly separately adds owner._shell_count at scatter. Therefore _beam_parts is not in the full-owner coordinate domain. The original material(owner,beam.coordinates) consumer was correctly indexed; my assertion that those slots began at90 was unsupported and false.
- The prior immutable workflow review f2e741ef581c4c52fb4684da5f6f03035733dbcd10c4e6b382f4fa84a284296b must not support the withdrawn claim or its misleading mocked global-slot fixture. Its bytes are preserved, with this explicit correction separate.

Final affected files independently read/hash-checked:
- workflow script a0dfea5ebf0a1ca93f43d028122e54d5aff2bfb0e7d24c99327bad6d0c15c3cb.
- tests bb5c3d5d80b1e42a8c994200b7cd7efd42de2ac135ee5d500e8da699047749f4.
- doc 3e72e9fb33b5f3bb669022591df040bda8258adb3a049a2085d372b9a6a74e12.

Final material(owner,q) explicitly documents global input and computes global_slots=owner._shell_count+np.asarray(slots,dtype=np.intp), gathering both q.high and q.low at these indices. This is consistent with the actual local member-slot contract while leaving the full global vector available for line traces. Existing support Python-int conversion remains separate; no physical criteria were weakened.

The revised run fixture uses actual local slot semantics [0,1], distinct shell900/901 versus beam3/4 values, and distinct positive/negative low parts. More substantially, test_actual_material_gather_feeds_beam_local_resultant_parts_to_cell invokes real material() rather than replacing it. Its local member layout is nodal0:18 plus retained30:54, representing the first42-coordinate member with beam nodal inventory30; the resultant portion must therefore be beam-local36:54. It records the actual zero/pHi/pLo cell-call seam and asserts both supplied/result-record halves match those beam indices, with differing shell values preventing accidental-domain success. This is appropriate targeted source coverage of the corrected gather. Mocked cell/reference responses do not verify constitutive mechanics, and neither test has run.

This review isolates indexing/control effects and does not repeat or renew the prior mathematical review. Source inspection supports the corrected domain conversion; runtime regression, immutable runner/source binding, user retry approval and any conditional specimen gate remain outstanding. Original failures, consumed authority and earlier review bytes remain unchanged.

