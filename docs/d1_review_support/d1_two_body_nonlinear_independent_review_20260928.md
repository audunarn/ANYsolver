# Independent read-only review — bounded two-body nonlinear oracle

The reviewer inspected the comparator and source-bound report at `4636ab34`,
then the active-set provenance and derivative-resolution changes at `22a0334d`.
This note records the review findings; it is not an acceptance adjudication.

**Finding:** No blocking mechanics, sign, work-map or KKT defect was found for
the stated same-structural-model, two-active-mode slide comparison. The oracle
independently integrates current Q4/S3 physical-skin gap and derives its work
map numerically. The structural residual and tangent are intentionally shared
with production. The converged saved residual is 6.14e−13 N, active gap norm
6.82e−19 m and minimum inactive gap 2.62e−6 m. Pressure, force and control
reaction differences remain below the prospective 1e−6 code-comparison target.

The follow-up chooses the initial active modes from the frozen-reference oracle
and checks equality with production only after the nonlinear solve. It records
half/nominal/double step comparisons for 28 free coordinates and two controls:
the maximum resolved-column relative difference is 5.59e−11, and the maximum
absolute difference across all 30 columns is 3.33e−11. The focused regression
gates these checks.

**Limits retained:** The nonlinear solve stays on one prescribed two-mode
branch, starts near the final state, and shares the shell structural model.
Finite-difference self-convergence does not independently prove derivative
correctness. The current clipping signature stores polygon vertex counts,
which does not establish full incidence ownership. The two control reactions
are very small, limiting their value as a global-balance check. Spatial
accuracy, active-set transitions, complete path acceptance and D1 release
remain open.

Evidence: [source-bound nonlinear comparison](d1_two_body_nonlinear_kkt_22a0334d_20260928.json),
[current-skin work comparison](d1_two_body_current_skin_work_67f8627a_20260928.json),
and `tests/test_general_contact_d1_two_body_nonlinear_oracle.py`.
