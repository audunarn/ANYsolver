# BL5 native distributed loading — 2 October 2026

Experimental integration on solver base a0465a88. Existing native force/couple
quadrature, actual retained-variable work, derivatives, equilibrium checks and
checkpoint policies are reused unchanged. The shared admission predicate now
admits existing point owners or objective-Q4 elastic BL5 owners, including a
tested mixed point/BL5 layout. Historical Q4 lines, L1 and footprints remain
rejected. Capabilities and compilation use the same predicate.

## Executed checks

- Four initial failures came from a test-fixture attribute mistake: native input
  wrappers do not expose element_id. The corrected fixture uses compiled beam
  identities. Original failure output is retained; no product fix was needed.
- Four corrected source tests pass in 24.988 s. P0 and coarse continuous-P1
  histories exercise signed force/couple densities, physical support wrench
  balance, compatibility/equilibrium, cancellation, injected trial failure,
  rebase, restore and identical continued checkpoint/beam positions. Final
  elastic response agrees with the independently stepped fixed-load path.
- Actual-update load derivatives and assembled load/Jacobian differences pass.
  This checks reuse of the external operator; it is not a whole-system physical
  reference or a new BL5 derivative qualification.
- Ten installed checks pass in 35.559 s, peak sampled process tree 186736640
  bytes. They include the four new tests plus affected point-load descriptor,
  linear factorization/restart, finite lifecycle and checkpoint-relabel guards.
- Independent Read review identified implicit admission of mixed point/BL5.
  A concrete tip-point plus line model now passes balance, both recovery types,
  chart rebase and exact continued restart in source (6.228 s) and the same
  installed wheel (5.944 s). Reviewer confirmed the concern was resolved for
  this bounded combination, without claiming arbitrary layouts.

Wheel SHA256:
`dd8ce52c2ab4ce072f4e4540f89e6fa5deb4600ed3511b2a1669de62f954cc74`.
All 398 source/wheel/site module bytes match; module bytes were rechecked before
using that wheel for the additional mixed-layout test. Actual imported solver
paths and effective one-thread BLAS/Numba, JIT-off settings are in runtime.json.
Python 3.14.2 on Windows, unchanged version 0.4.7 and existing dependencies.
All jobs use the existing 600 s / 1 GiB supervisor. These are verification costs,
not performance claims. No timed jobs ran concurrently.

Independent OpenAI source review covered admission, work reuse, finite numerical
policy and private checkpoint restoration; no unresolved consequential finding.
This is not a different-family or scientific acceptance review.

[evidence-v1.zip](evidence-v1.zip) SHA256
`381d84db2088c06964d5039c9bed5d2f712e2a2151274490a634060eef46508a`.
[evidence-v1.json](evidence-v1.json) binds raw output, safe execution metadata,
installed runner/fixtures, module identities and runtime paths. No full process
environment is copied. Reproduction runners use no-index/no-deps wheel builds
and isolated installed targets through the existing bounded supervisor.

## Remaining boundary

No physical BL5 acceptance, formal F03 execution, tolerance amendment or release.
Zero-load relative assessment remains unresolved. Shell pressure, gravity,
plastic/S3 lines, full topology and scientific reference obligations remain open.
ANYfem BL5 distributed-input persistence is not yet implemented. Broader material,
scale, platform, consumer and external obligations remain mandatory.
