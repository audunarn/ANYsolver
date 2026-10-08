# F03 local-reference operators: bounded proof results

22 September 2026. **The bounded operator foundation passed its synthetic
checks and independent reviews. G0B remains open; G1 is barred.**

Source commit: `7cb7b77491ef3343b72a231a6bb443e0474ddec1`, on
`codex/b3-ge-e4-pl-integration`. The implementation contract is
`B3_GE_E4_PL_G0_F03_LOCAL_OPERATOR_CONTRACT.md` (SHA-256
`08675c57a92de007f21103d73b88f5d873eb37758f98d1faa8d2f028c6fb5894`).
These are independent classical research helpers under `scripts/`, not
changes to native beam/shell element equations or public solver APIs.

## Implemented and checked

- Exact finite-pad Q1/Q2/Q3 moments on rational rectangles, physical first
  and second derivatives, and explicit held `J/gamma` behavior.
- Shared rectangular topology, prescribed-zero x-edge supports, owned
  numbering arrays, exact station events and conservative incidence bounds.
- Independent classical membrane stiffness and shape derivatives, checked
  against exact rigid/affine identities and a separate Gauss integration.
- Complete assembled pose/first-derivative continuity, exact rank-three
  root constraints and a separately free transverse root slope.
- A degree-five piecewise physical interface functional with exact
  common-partition subtraction, both endpoint atoms and held cosine loading.
- Full-H1 Green evaluation using binary64 prefix/Duffy quadrature and a
  separately implemented 70-digit Decimal direct interval-pair oracle.

The root test includes a coarse Q1 counterexample: rank three alone can
hide a dependent root-slope row. A scientific approximation must pass both
admission checks. No candidate mesh has been accepted solely from this
bounded fixture.

## Test inventory and independent acceptance

All **79 distinct current synthetic checks pass**. Final evidence consists
of the following disjoint groups, with unchanged inputs reused explicitly:

| Current group | Passed | Final log |
|---|---:|---|
| Grid, exact moments, membrane and shared trace space | 30 | `local-derived-coordinate-662d155639544bce943d639267c2014e.log` |
| Corrected binary functional and independent cross-method comparisons | 19 | `local-norm-final-c1b44c76afb74932a8859f9dffc9bfae.log` |
| Unchanged independently reviewed Decimal oracle | 30 | `f03-local-oracle-review-20260922.log` |

An earlier integrated run passed 75 tests before the final adversarial
findings. That log is preserved, not relabeled as acceptance of the corrected
source. The later affected checks supersede the claims for changed inputs.
The seven cross-method tests cover degree-five values, cosine forcing,
all atom/channel terms, different partitions, large common-part subtraction,
signed cross work and a measurable narrow-interval contribution.

`finite_pad_axis_review` independently reviewed the grid, membrane, moments,
binary functional and contract. `f03_port_mechanics` independently reviewed
the separately authored Decimal oracle. Neither accepted its own sole
implementation. The parent implemented the cross-method tests and accepted
the bounded proof scope after final affected checks passed. Exact reviewed
file hashes and conditions are retained in `independent_review.json`.

## Findings preserved and resolved

The first exact-moment tests exposed a padded symbolic polynomial tail;
the exact degree guard now handles zero trailing terms and rejects genuine
degree overflow. That initial failing log is preserved.

Independent review found mutable/invalid direct grid construction,
unbounded iterable and rational inputs, and allocation during the symbolic
memory preflight. The factory is now the ordinary construction boundary;
inputs and derived coordinates are bounded before use, and preflight sizes
are calculated without allocating the proposed row lists or masks. Derived
functional coefficients are checked before each interval is retained.

The important numerical finding was a Duffy-weight underflow defect missed
by the first 75 tests. With an interval of width `10^-161`, density `10^161`
on that interval and density one elsewhere, the defective binary helper
returned squared norm `3.0` while both orders appeared resolved. The
independent Decimal value was approximately `4.3130352854993313`.
The interval area was nonzero, but its weighted diagonal terms vanished.

The corrected helper requires every active weighted Duffy Jacobian to be
finite and normal binary64 before density multiplication. It rejects the
adversarial case explicitly. Two regression tests failed before correction;
both those failures and the independent probe remain preserved. No physical
tolerance changed and no alternate quadrature fallback was introduced.

Cancellation metadata describes completed interval and atom contributions;
it is not an arithmetic error bound. The bitset incidence diagnostic can
use quadratic bit storage and is not a scalable native production assembler.
These limits are explicit in the accepted contract.

## Immutable proof archive

Root: `.qualification/b3-ge-e4-pl/f03-local-operator-proof-v1`.
It contains 13 source/contract/test copies, 24 raw development/review logs,
the manifest and review record: **39 bound files plus the inventory itself**.
Do not add or overwrite files inside this completed archive.

- Inventory SHA-256:
  `b26d4595f6b883d76ad9f2c66cb04f822e3cd8c9b97997ac2cce1f30c870206a`.
- Manifest SHA-256:
  `540c2937496ddef1f8c3e241fa4beae69ffdd19d5fa9602813de554b061ece3c`.
- Independent-review record SHA-256:
  `4e1597ccc8343064dabc1d220d20e936a0540061b45ddc6acfc13413ff291f2c`.

Tests used Python 3.14.2, NumPy 2.4.6 and the five numerical thread caps at
one. Exact environment and original log locations are in the manifest.
Setup permission failures and an archive precheck that caught an outdated
documentation hash are recorded separately from numerical test outcomes.

## Remaining work

This work ran **zero scientific equilibria and zero native element
operations**. It did not replay or extend any consumed diagnostic, establish
physical convergence, execute an external comparison, measure performance
or qualify an installed product artifact.

Next implement the eliminated-primal shell/trace-beam bilinear form and
root KKT assembly, then independently check manufactured work, stress-jump
and support-reaction identities. Before any new scientific execution, freeze
a conforming nested case family, exact prolongation, integration, scaling,
conditioning, resource and physical-settling criteria in a separately
reviewed numerical protocol and registration. Preserve the original
45 scalar observables, full-functional criteria, held physical constants
and all earlier failures.

Main was observed clean at `be41a77a62e1cd7e1767bda6e955253af0819f91`,
matching the locally cached `origin/main` reference. No fresh remote fetch,
product merge, version change or release occurred.
