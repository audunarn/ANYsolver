# Experimental S3 V2D elastic surface recovery, 2026-10-08

Source parent: `91da2ae937abd68e6bdc71be237542af53850ef7`.
Product and tests are in the accompanying worktree diff/commit. This is an
ordinary development check, not a G0/G1 or release qualification.

The exact isotropic `Material` and no-`shell_section` route now exposes local
membrane, bending, shear, and top/bottom-envelope von Mises stresses through
default `compute_stresses` and public `recover_stress_result`. The calculation
uses the already returned physical N/M/Q and the established Q4 thickness and
shear convention. The existing global tensor path uses the same local arrays.
Preintegrated generalized sections still expose resultants only. Public V2D
committed-state recovery remains a separate, stored-layer route.

Final focused source run: **11 passed**, exit 0, process wall 3.639203 s (exact
receipt in `review-followup-receipt.json`). It includes a mixed Q4/S3 public
affine-strain oracle, nonzero bending/shear and rotated local/global tensor
checks, the generalized-section refusal, and existing elastic/committed public
recovery controls. CPU affinity 1, one BLAS/OpenMP/Numba thread, JIT disabled.
The test interpreter was the existing ANYfem integration environment, with
`PYTHONPATH` set to this solver checkout's `src`.

Preserved attempts: default Python lacked pytest (`focused-receipt.json`);
the solver venv points to a removed interpreter (`focused-venv-receipt.json`);
a malformed `-k` selector deselected all tests (`affected-receipt.json`). The
full two-file run recorded 19 passed and one unrelated historical failure
(`affected-v2-receipt.json`): its frozen V6E production-boundary assertion
expects the old `legacy-s3` default, while current main selects
`e4-pl-s3-v2d`. That historical test and criterion were not changed. The
subsequent exact-node V6E recovery control passed. All stdout/stderr are saved
with their respective receipts; no failed result was rewritten as a pass.

Supporting read-only code/mechanics review found no concrete defect and called
out missing bending/shear and committed-state coverage. These checks were
added to the final run. Installed artifact verification, programme-independent
review, and consumer integration remain open.
