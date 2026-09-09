# Native directional gate: failed, scalar precision diagnosed

Frozen logging-only revision a6a54a141019105902b81fede77708b36333921c,
tree 82cc10c3c50b32d61bb10228a3f3376092700e6d. All 17 targeted tests passed
in 6.08 seconds; git diff --check passed. Four research-only paths changed;
no src, beam/shell mechanics, material, recovery, defaults or dependencies changed.

## Consumed positive-endpoint smoke

PID 48460 completed all five points and exited 1 after 97.1362029 seconds.
Windows Job after-accounting: 959375000 CPU 100ns units, zero active processes,
359649280 peak bytes. No timeout, memory breach or cleanup failure. No negative
or replica worker launched. No native.json or accepted aggregate exists.

The first failed predicate was the potential second-difference error at h=5e-5:
1.320914472704559e-7 > the unchanged 1e-7 gate. Full results:

| h | Potential error | Scalar residual-work error | Full residual derivative error |
| --- | --- | --- | --- |
| 1e-4 | 1.3284573209494319e-8 | 5.464402027654386e-10 | 9.979937863439305e-10 |
| 5e-5 | 1.320914472704559e-7 | 1.217179232838178e-10 | 9.444499590499492e-10 |

Native mixed directional work -0.001022921338718573 agrees with saved exact
factor work -0.0010229213387185085 under the existing 1e-11 check. Both potential
second differences and scalar residual directional works remain negative.
The original work witness is not lost or reclassified. This gate is nevertheless
FAILED, not accepted. Final checkpoint/recovery checks after adjudication did not
run; unadjudicated diagnostics explicitly say so. Evaluate's own state-immutability
and native coupling/lift checks did finish.

## Read-only and non-owning diagnosis

A standard-library audit recomputed the raw hash-bound potentials, full residual
derivatives, scalar work and metrics. Exact Fraction summation of the saved
element scalar values still gives error 1.3203960885408393e-7 at h=5e-5:
changing only the final global summation cannot resolve this. The discrepancy
in the scalar numerator is approximately 3.30099e-16.

A bounded two-element 80-digit Decimal geometric-map probe completed in
2.4192766 seconds. Its all-24-element extension completed in 4.9293820 seconds,
with 166436864 peak bytes and no live children. These diagnostic probes:

- Read the original hash-bound checkpoint fields; do not issue accepted state.
- Reproduce every corresponding saved native element potential bit-for-bit.
- Require virgin material history; reuse the actual native material conjugate.
- Evaluate the same geometric Exp/Log/chord scalar expressions at 80 digits,
  using precisely the same binary64 input fields and increments.
- Use the same two fixed steps; do not change production code or adjudication.

The full scalar second differences become -0.00102292161160244693 at h=1e-4
and -0.00102292140683239610 at h=5e-5. Discrepancies from native work are
2.7288387400931203e-10 and 6.811382317441275e-11 respectively. This isolates
the observed failure to numerical precision in the scalar geometric-value path,
not to the final sum. It supports a targeted numerical-stability successor.
It is not independently authored theory, a rigorous rounding-error bound,
full material-oracle verification, authentic accepted-state replay, or a
replacement accepted qualification result.

## Preserved custody and next gate

Original failed 301820c archive: 12 entries, manifest 1653 bytes, SHA-256
c796f3e3302088b02ded939784682b5b791fba1167915bf824373a943a09b7b8.

Successor smoke and both precision probes: external ANYrelease archive
ge-beam3-native-directional-diagnosis-a6a54a1-20260909, 38 entries, manifest
6300 bytes, SHA-256
2601ddecd20599fcc5e4431d5c6770077e2d474e7b7c1055c4fdc97901d79a8c.
Includes exact scripts, commands, terminal process receipts, raw diagnostics,
source snapshots and saved audits. UNADJUDICATED manifest SHA-256:
09d2d798e36724e1f4a18efbefa6fc9e4ba552b5d53fc1252234fee1d796e2a3.
All consumed runs remain immutable. No automatic retry or request reuse.

Next: preregister and verify an expression-preserving compensated scalar-value
successor for the private GE-B3 path, or a rigorously justified high-precision
value interface. Bind its source equations and original failure; independently
check the value/gradient/Hessian relation before authentic endpoint replay.
Retain both steps and all existing acceptance thresholds. Do not substitute this
diagnostic's high-precision numbers into the failed native result. Positive smoke
must pass before the negative/replica wave and accepted aggregate are possible.

Full spatial postbuckling, physical loading path from rest, plastic continuation,
broad solver/material/dynamic parity, independent author review, installed
explicit selection and objective beam-shell connections remain open.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED. No public GE-B3 activation, push, merge,
release, version change or existing B2/B3/S3/Q4/default change is authorized here.
