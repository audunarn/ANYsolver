# Independent consumer and installed review

Reviewer: `/root/anyfem_consumer`, read-only; parent implemented the slice.
Candidate ANYfem `a615c4b299e603264f67d292c8a4415168b1b9c6`.

Code/source review found no actionable correctness issue. The explicitly
selected mass-v2 record preserves nullable density and complete physical mass
source/origin/matrix; static v1 stays the default and rejects unsupported mass.
Physical mass validation and reference-axis pullback stay with ANYsolver.
Static affine inputs survive; unsupported MPC modes fail at operation admission.
Modal requests preserve numerical status/cancellation and close their owner;
unexpected exceptions propagate. Source checks passed 19/19.

Installed review independently rehashed the consumer wheel `ff143e5fece9dd4cec261aa69edbec03acc801d3d0bbfcb90cea7519d814f0c0`
and reused solver wheel `314ea0dffd9c5fa7f70b80538373e42ffd10b5083f231b69a8bd4784773b1a2d`.
All 384 solver and 97 consumer source/site module hashes match identity.json;
all five copied test files and the F09 fixture helper match source. The runner
also verifies every wheel module byte against source/site before tests. No
solver source changed from product `0da6cd12`. Consumer worktree is clean.
All 270 captured solver/consumer imports are inside the isolated site.

Final installed run passed 43/43: B2 consumer 19, GE consumer 5, reference modes
19, in 29.87 s; guard elapsed 33.370 s, peak process-tree RSS 220,983,296 bytes.
Python 3.14.2, effective OpenBLAS thread count one, NUMBA_DISABLE_JIT=1.
Build-cache ACL failure, missing-PYTHONPATH precheck and two missing-fixture
collection failures are retained. The collection attempts exited before tests;
repair copied dependencies without changing numerical criteria.

No unresolved actionable finding. This supports installed experimental consumer
compatibility, not F12/G4B/G6 scientific acceptance, normal native `.anyfem`
persistence, F03, production qualification or release. Reviewer launched no jobs
and made no source edits.
