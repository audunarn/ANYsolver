# GE-B3 private signed loaded modes — 2026-09-07

Baseline `2356029a52ead7d131155a4cb1c9f467865a72a7`, tree
`06113052c775a973c7dba413c2b54731d9788b4b`. Two new private modules add signed
mode shapes and an accepted-state native adapter. Existing B2/B3, Q4/S3,
accepted straight-beam mechanics, private P5 source packages, historical
evidence, defaults, public selectors, dependencies and versions are unchanged.

## Implementation

`_native_signed_factor_modes.py` retains the preceding material-factor plus
signed-geometric reduction. It copies inputs into immutable owned arrays,
checks bounded dimensions/DOFs/massless traces, includes the geometric trace
Schur correction, retains physical cell inertia and brackets the lowest
requested signed squared frequencies. Its root search is bounded to 96 shifts
per root and a 600-second cooperative deadline with cancellation checkpoints.
Native preparation, element/station construction and completion have their own
enclosing 600-second cooperative check. These are not hard process-tree limits;
formal external execution still requires the applicable resource/watchdog
authority. No resource request was consumed in this development work.

Mode extraction uses a fixed off-root shift, complete numerical clusters,
diagonal congruence and transformed-mass-aware selection. Two bounded block
inverse-iteration steps restore small strong-coordinate components. Direct
normalization with twice-applied modified Gram-Schmidt avoids Householder
reconstruction loss of tiny vector components. Small-cluster Rayleigh-Ritz
retains the signed correction. A request cutting through a repeated cluster
fails closed; no arbitrary partial cluster is returned.

The kernel checks numerical brackets, spectral orthogonality, physical mass
normalization and an action-scaled signed-basis residual at 1e-11. This latter
check uses actual diagonal/prestress actions on each mode, not the norm of an
unrelated largest stiffness. A separate full-coordinate backward residual is
also checked, but is explicitly not treated as proof of low-frequency forward
accuracy. Numerical brackets remain binary64 diagnostics, not certified
intervals. No root clipping, mass/stiffness floor, positive-reference fallback
or automatic solver retry is introduced.

`_ge_beam3_signed_loaded_modes.py` uses the existing loaded-state preparation
and identity guard. It owns state/force snapshots, validates actual accepted
free equilibrium and rejects active plastic/yield-boundary modal interpretation
and unqualified nodal moments. It includes accepted distributed dead-load work,
assembles the signed split on native nodal/internal maps and preserves all cell
inertia. State is neither advanced nor committed by this adapter. Its output
binds operator and external-work identities and remains private/unqualified.
Elastic unloading after a genuine plastic history is supported without
discarding that history. Broader nonlinear section families remain unfinished.

Static AST checks establish that the copied material/geometric split and
trace reduction equal the preserved research functions except for additional
checkpoints. This is equivalence checking, not independent authorship or review.

## Validation and honest failure history

The first extraction attempt failed four checks (six passed): signed Ritz
values, cross-mode orthogonality and loaded high-slenderness action residuals.
The failed kernel is preserved with SHA-256
`FBB1AAF483A29DBBD1ECEA5CFBBF391C0ECC265DB5873C4988DEBD2F5C5E83F6`.
Direct component-preserving normalization and bounded inverse iteration fixed
those cases without weakening a check; the resulting ten-test run passed.

The first native-adapter suite had one fixture failure and eighteen passes:
the mutation test assigned a read-only DOF-count property. Its preserved test
source hash is `58BA2ECEB0CD633339DFD1475833628FBCD890993031CC5AE2C7DC5EE0D497A7`.
The fixture now mutates/restores the backing count and verifies that the
post-kernel identity guard rejects it.

An expanded run then had one failure and 65 passes. Selecting modes by
absolute eigenvalue of the congruently scaled pencil could select the wrong
mode: a diagonal pencil can have scaled values all equal to +1 or -1. The
failed kernel hash is
`943F7DB976D3168D507D6C6E86496E8F97D2FCE35AF3C6E46C693EE25475DD19`.
Selection now accounts for transformed mass; extraction also stays off the
root to avoid an exactly absent scaling diagonal. Exact unstressed zero and
positive modes are tested. These changes do not change the physical operator.

The final suite passed **68 tests in 104.35 seconds**, with separate inventories:

- 14 signed-kernel input, extraction, ownership, cancellation and deadline tests.
- Two actual native L/h=1,000,000 tension/compression mode-shape tests.
- Eleven loaded-adapter state, guard, curved/coupled, translation, rotation,
  plastic-unloading and analytical six-rigid-mode tests.
- 23 preserved loaded-modal tests.
- Seven preserved signed-frequency tests.
- Eleven preserved signed-algebra/reference tests.

The two high-slenderness states agree with the separate rational-coefficient,
80-digit finite-shear discrete reference. Under axial load -1 the first pair
is approximately -0.436706580273 and -0.436706580270: both negative modes are
retained. A curved/coupled case matches the preserved moderate-conditioning
dense modes, including mass-weighted mode correlations. Two-element results
are unchanged by a 2^40 coordinate translation. A proper frame rotation
preserves frequencies and mode correlations. The free curved case retains
the complete analytical six-dimensional rigid-motion subspace.

The largest recorded action-scaled residual among the four emitted native
mode records is below 5e-16. These samples do not constitute a universal
forward-error guarantee or full-domain prestressed-modal qualification.

A fresh-directory repeat passed the 27 new tests in 47.48 seconds. All four
emitted mode-shape records are byte-identical. A separate static suite passed
20 tests in 0.39 seconds: eight new checkpoint/equivalence checks, seven prior
signed-spectrum checks and five prior loaded-modal checks.

## Preservation and next gate

Twenty-five files totaling 94,971 bytes, including failed source versions,
intermediate outputs and both final output sets, are preserved and verified by
byte count/SHA-256 from the normal workspace context in:

`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-signed-modes-development-20260907-42d4a0437f25`

The canonical source/archive record is
`docs/reference_cases/ge_beam3_signed_modes_evidence.json`.
Original temporary outputs and all older archives remain. Only verified relay
duplicates are removed. No formal request has been consumed, reused or retried.

Independent review remains PENDING. The next steps are installed-wheel
verification of these exact private modules and multi-element high-contrast
curved/coupled validation, followed by broader engineering modal/buckling and
state/parity gates. General nonlinear sections, geometric-domain coverage,
performance/scalability and objective beam-shell connections remain required.
No public exposure, release, default activation or full qualification is claimed.
