# GE-B3 P5: centered reference adopted by the native candidate

## Status

Private development candidate: `CANDIDATE_GE_BEAM3_P5_NATIVE_CENTERED_V3`.
Independent review and production qualification remain pending. No new public
selector, default activation, release, tag, push or merge is authorized by this
checkpoint. The broad straight/curved beam and objective beam-shell connection
programme remains incomplete.

Parent: `1ced65643faa63fe01bdcb23e31a0f9da0fc7250`, tree
`cb03b6780a4f15999786e0357e8d682e569ed1ae`. The previous centered-reference
operator, V1/V2 native packages, source contracts, tests, formal studies and
external evidence remain unchanged. This checkpoint adds eight private source
modules in `anysolver._ge_beam3_p5_centered`; it is not a no-source-delta claim.
Existing B2/B3, qualified Q4/S3, public straight GE-B3 routing, coefficients,
section laws, quadrature, tolerances and defaults are unchanged.

## Implemented successor

The native core now owns the centered Q2 reference evaluator. Its fingerprint
and evaluation ID enter model/state identity, descriptors and recovery
provenance. The constructor preserves the supplied geometry's admission
tolerances. A subsequently substituted historical evaluator or mutated
coefficient array fails model validation before use.

Native initialization, trial solves, commit, accepted-origin replay and restart
all use the centered stationary operator and the retained high/low coordinates.
The driver/core/codec IDs are V3; historical V2 checkpoints cannot hot-restart as
V3. Physical section histories still advance only on accepted global commits.

Reference elastic and kinetic factors, current accepted Hessians, at-rest mass
and recovery use the same centered frames, Jacobians and analytic half-cell
lift. No world-coordinate polynomial subtraction is used to reconstruct that
lift. The full retained-cell mass has rank 15 with nine massless trace rotations;
cell spins remain dynamic. There is no Guyan cell-mass reduction or invented
trace mass. Shared trace equations are eliminated by the existing global modal
adapter, not independently element by element. The inertia wrapper rejects
nonzero velocity/acceleration; this is not finite-rotation dynamics support.

### Additional recovery defect found during adoption

The first native integration suite passed 12 tests and failed four translated
recovery tests. The preserved V2 helper accumulates separately rounded binary64
`1-t` and `t` as exact rational weights. Their rational sum can differ from
one, amplifying a common world offset. At the registered Gauss witness, the
deficit is `1/18014398509481984`; translations of `2^30` and `2^40` make
the defect visible even though local strain/resultant solutions remain stable.

V3 uses the equivalent affine expression
`left + t*(right-left) + U*reference_lift`, accumulated with exact rational
arithmetic over the supplied floats before rounding to two components. V2 is
preserved and tested as a historical witness. The initial regression witness
picked a Gauss point whose weights actually summed to one; changing only that
test index from 0 to 3 exposed the intended defect. The corrected 17-check
integration suite passed in 75.96 seconds before the final expanded regression.

This does not recover geometric information already lost when input coordinates
are rounded. Two-component outputs are not arbitrary precision. The centered
reference's analytical minimum-tangent calculation is not an outward-rounded
domain coercivity/sign certificate.

## Validation and restart accounting

After the restart, the old protocol-only session handle was unavailable and no
Python test process remained. Its unavailable terminal result is not counted.
A fresh small development regression was run; no consumed formal resource
request was restarted. One invocation first used an incorrect test filename,
so pytest ran no tests; the corrected invocation is the one recorded below.

Source regression: **123 passed in 126.59 seconds**:

- 43 native successor checks: one/two-element elastic/plastic Newton paths at
  offsets 0, `2^30` and `2^40`; byte-identical displacements, station responses,
  reference/current operators and reference spectra; physical recovery and
  split positions; exact split plastic restart; sub-ULP axial commit; state,
  codec and geometry mutations; tangent directional agreement; load/unload/
  reversal, displacement and arc-length controls; cancellation safety.
- 32 centered reference checks, 14 centered local-operator checks and two
  read-only diagnostic checks.
- Six preserved native-package/coordinate evidence checks, 21 existing straight
  P3 opt-in checks and five generic nonlinear state-cleanup checks.

No tolerance was relaxed. Invariant/symmetry checks retain `1e-11`, and
directional tangent checks retain `1e-7`. Control tests do not constitute
post-buckling engineering qualification. Plastic accepted-Hessian consistency
does not authorize modes on a nonsmooth plastic vibration branch.

Installed-wheel lane: **one test passed in 38.15 seconds**. A disposable build
snapshot deliberately uses CRLF candidate sources. The wheel is installed
offline in a fresh virtual environment from ten hash-bound dependency wheels.
Both isolated processes run outside the repository, forbid research imports,
verify 36 canonical source bindings and actual installed byte hashes, and
exercise plastic restart, physical recovery, reference/current modes, sub-ULP
axial commit and translated native solutions. Their canonical outputs are
byte-identical. This is a small package-development check, not two full
qualification cycles or a performance benchmark.

Source runtime: Python 3.13.9 / NumPy 2.4.3 / SciPy 1.16.3. The isolated wheel
uses the preserved offline graph including NumPy 2.5.2 and SciPy 1.18.1.
There is no cross-runtime bitwise-equality or speed claim.

Post-evidence inspection: **six static checks passed in 0.19 seconds**, covering
source-map mutation detection, development-only status, artifact inventory and
the actual archived byte counts, hashes and installed provenance. No mechanics
or package lane was rerun for this inspection.

## Artifacts

Archive:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-centered-native-development-20260906-bf5ddc4e92ff`

Six files, **1,358,351 bytes**, preserve the wheel, source map, installed check,
receipt and two process records. Copies were exclusive and byte/hash verified.
Only six verified workspace relay duplicates and their empty directory were
removed; the original temporary files and external archive remain.

- Wheel: 1,321,709 bytes,
  `bf5ddc4e92ff6965cbcf60ef3cdf1f119dbdd2f8944f8505a5ff85064531c21a`.
- Each process record: 9,391 bytes,
  `3fbb9d3bddd306a79e98854e201310d6b33c5d91e954f532cb381706a50c655f`.
- Source map: 6,131 bytes,
  `5f6a8cbfce0b6a05eb7839b1db8541d89b0284e66516c2d1748c39f66dbd0493`.

The source map binds eight new and 28 preserved modules and explicitly records
review as PENDING. It is a development source binding, not new formal execution
authority. The archived wheel binds the full installed artifact. Existing 0.4.2
metadata is unchanged: **do not publish this wheel as a replacement 0.4.2**.

## Next gate

Independently review the centered-reference adoption, recovery correction and
native state/operator bindings before treating this package as a frozen
qualification candidate. Keep public workflow routes fail-closed until their
load/work/tangent and material-state contracts are completed. Broader engineering
modal/buckling, slenderness/stability, general section and objective beam-shell
joint qualification remain required. Rigorous reference-domain coverage also
remains open.

No 32-element campaign was rerun or reclassified. Any subsequent heavy campaign
needs a fresh clean freeze, exact resource request/approval and global lease;
the ordinary unit/package checks here create no resource request or ledger row.
