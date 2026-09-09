# GE-B3 V5: seed and conservative-control checkpoint

Status: **DEVELOPMENT INCOMPLETE — curved spectral covariance unresolved**.
Independent review: **PENDING**. No production qualification or public routing.

Base: `39e00ced31b325012dd773277c4960b79e52a2b0`, tree
`0aaecb0a32901cf95a37140d44806a9c02967e05`. Work remains on
`codex/ge-beam3-curved-p5-objective-lift-v1`. B2/B3, Q4/S3, public defaults,
the accepted straight candidate and all previously committed mechanics are
unchanged. This checkpoint adds private successors, not replacement evidence.

## What changed

The preserved V4 local initialization reconstructs cell rotation seeds from
nodal frames times reference-frame transposes. Even at the reference state,
that introduces tiny symmetric stretch. Large section contrast amplifies it
into a nonzero external force despite converged internal equations. The old
implementation and its failing negative controls remain untouched.

V5 seeds directly from authoritative nodal rotation operators. A common
operator is copied exactly; distinct operators use their SO(3) midpoint.
The potential, local Newton equations, section law, quadrature and local
accuracy limits are unchanged. Candidate/model/state IDs distinguish V5;
cross-V4/V5 hot restart is rejected. The six-file private native package is
copied from V4, with namespace/identity changes and this explicit seed only.

The conservative V5 force controller additionally reuses the preserved
research Armijo decision (c=1e-4). It evaluates the native incremental
potential and subtracts nodal dead-load work exactly once. Distributed work
already belongs to the element potential. Fixed history origins remain
fixed until global acceptance. Non-descent directions fail with a request
for explicit continuation; the tangent is never shifted. The final chart
AND physical equilibrium tolerance remains 1e-11. A line-search trial that
already meets that stopping condition is allowed through to revalidation and
transactional commit, even if rounded energy values cannot resolve descent.

Objective-energy backtracking is a standard alternative to residual-norm
backtracking; see [PETSc's primary documentation](https://petsc.org/main/manualpages/SNES/SNESLINESEARCHBT/).
This is not a new physical beam formulation or an empirical stiffness repair.
The stateful controller is distinct from the older virgin elastic seed probe.

The V5 modal adapter retains a current lifted kinetic factor, avoiding dense
mass Cholesky whitening. Its signed numerical successor retains material
strain rows through trace elimination. Geometric signs, cell inertia and
exactly massless nodal rotation traces are preserved. The kinetic-factor
adapter owns its inertia inputs and checks their Gram matrix against the
preserved current-rest mass. These changes are still insufficient for the
extreme curved covariance gate; they are experimental, not qualified.

## Observed results

The complete small correctness run completed in **82.49 seconds: 65 passed,
1 failed**. Its complete JUnit report is archived, including the actual
unconditional failure (not an xfail, skip, waived gate or widened tolerance).

| Inventory | Passed | Failed |
| --- | ---: | ---: |
| Authoritative seed and loaded/restart replay | 12 | 0 |
| Conservative controller, plastic reversal and transaction safety | 39 | 0 |
| Numerical helpers and Decimal arithmetic audit | 12 | 0 |
| Curved reference-mode covariance | 2 | 1 |

The reference forces, strains, resultants and moments are exactly zero for
the registered L/h=100, 10000 and 1000000 specimens. The coupled L/h=100
two-element load programme at p=0.5 and p=1 completes in five Newton iterations
per target. Its accepted state and signed modes replay byte-identically.
The residual-only draft had consumed its twelve-iteration bound without an
accepted target. No failed resource request was retried; these were ordinary
small development tests, with no resource request or ledger mutation.

The remaining failure is E/R90 modal covariance at L/h=1000000. With
rtol=atol=1e-11 unchanged, two roots miss the comparison; the largest relative
difference among failures is 1.43633542e-11. Both processes returned their
full mode records, which remain diagnostics, not accepted scientific output.

A separately coded standard-library Decimal audit forms the supplied-factor
Gram matrices, eliminates massless traces and solves the symmetric pencil at
60 and 90 digits. Its first six roots agree across precisions within 1e-30.
The supplied E/R90 factors differ in their audited roots by at most about
1.53e-12 relatively. This localizes most of this probe's error to binary64
reduction. It does not establish arbitrary-geometry accuracy, mathematical
interval bounds, beam mechanics independence or an independent review.

## Preservation and next work

External archive: `C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-seeded-development-20260907-c813bb63b109`.
It contains **74 files, 1,746,933 bytes**, checked by per-file size and SHA-256
from the ordinary workspace context. The canonical manifest is
`docs/reference_cases/ge_beam3_seeded_development_evidence.json`. It binds all
20 new implementation/test/audit sources with UTF8-LF normalization, raw
diagnostics, failed drafts and the full final JUnit report.

The early session 14872's terminal transcript is unavailable. Its actual
saved outputs are archived without inventing a complete-run result. A later
logging-only test defect (closed stream during replay) is also preserved; the
corrected test passed. Only verified relay duplicates may be removed; all
original temporary evidence and the external archive remain.

Next: close high-relative-accuracy signed reduction and mode shapes against
the Decimal audit, then broaden curved/slender loaded and stability tests.
Do not change the 1e-11 invariant tolerance. V5 displacement/arc control parity,
general nonlinear/fibre sections, broader prestressed modes and buckling,
performance/scalability, objective beam-shell connections and independent
review remain open. No merge, publication, default activation or qualification
is authorized by this checkpoint.
