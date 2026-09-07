# GE-B3 paired-plastic current-state spectral development

## Status

The private paired-plastic state now supports an explicit-policy current-state
spectral entry point. Small curved, prestressed two-macro cases pass at section
contrasts 1 and 1e12, including complete loaded-model rebuilds under R90 and a
general rotation. **This is development evidence, not qualification.**
Independent review remains **PENDING**. No public selector, default, version,
existing beam/shell mechanics, accepted state implementation, or historical
qualification evidence is changed.

Base: `c6474656837aa2df5ca355fe57774eb10f6098b9`, tree
`b6f1b02004c33f00e9ef72db4d38be7eb30d2fd8`.

## Explicit material interpretation

The caller must choose a policy; there is no automatic fallback:

- `FROZEN_PLASTIC_COORDINATES_ELASTIC_PERTURBATION`: elastic perturbations
  about the actual committed, prestressed configuration with plastic
  coordinates held fixed. This is a declared linear perturbation assumption,
  not a simulation of continued yielding or dissipative vibration.
- `ACCEPTED_INCREMENT_ALGORITHMIC_OPERATOR_DIAGNOSTIC`: the derivative of
  the last accepted increment, evaluated from that increment's original
  history. Its spectrum is an operator diagnostic, not automatic physical
  vibration authority. A non-unique yield-boundary derivative is rejected.

Neither choice resets the state to virgin material, advances history, invents
drill/trace inertia, clips negative squared eigenvalues, or authorizes a
buckling factor. Returned brackets are numerical, not certified intervals.

## Preserved mechanics and arithmetic

The native entry restores and validates the paired-plastic checkpoint and
its full origin/history chain. The retained operator supplies the unchanged
kinematic derivative J and prestress/geometric tangent G. If C is the chosen
complementary compliance, elimination of resultants gives
`K = J^T C^-1 J + G`.

An 80-digit constitutive Cholesky/inverse factor is converted to high/low
binary64 parts without expanding J. The left factor is `[F_high F_low]` and
the right factor is `[J; J]`. The existing exact-dyadic factor-chain congruence
kernel retains their dependency through full-map spectral reassembly.
This avoids returning to the inaccurate nested dense condensation.
The pre-conversion inverse identity and the selected native algorithmic
compliance are checked. Frozen-coordinate compatibility is checked against
the actual accepted state rather than an invented unloaded state.

The unchanged current lifted kinetic factor retains cell rotational inertia.
Nodal rotation traces have exactly zero inertia and are treated algebraically;
there is no mass floor or Guyan approximation in this path. The new private
entry adds explicit result interpretation, checkpoint/operator identities,
cancellation, strict inertia IDs, and model guards before and after spectral
execution. Runtime imports do not depend on research files.

## Separate test inventories

- Initial policy probe: 4 passed, 8.954 seconds.
- Rebuilt-model covariance: 8 passed, 26.187 seconds.
- Initial native port/guards: 20 passed, 38.963 seconds.
- Final development cycle A: 24 passed, 40.385 seconds, no skips.
- Final development cycle B: 24 passed, 40.362 seconds, no skips.

The final cycles have **52 byte-identical JSON pairs**. They verify both
policies, native/research packet and spectral equality, six positive modes in
the chosen stable cases, mode-action and original-bilinear Ritz residuals,
massless trace coordinates, explicit policy selection, invalid inertia,
yield-boundary and inconsistent-tangent rejection, immutable output arrays,
unchanged checkpoint bytes, and cancellation/model mutation at kernel exit.
The algorithmic tangent is softer than frozen-coordinate elasticity in the
tested convex-hardening cases, as expected; the policies are not conflated.

Both contrasts are rebuilt under R90 and the rotation vector `(0.4,-0.3,0.2)`.
The largest relative eigenvalue difference is `1.2665781912567587e-15`, below
the unchanged `1e-11` gate. Scientific tolerances and root width were not
relaxed. These small correctness runs were not benchmarks or formal
qualification/resource executions; no resource request was consumed.

## Preservation

Archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-plastic-modal-development-20260907-6da809f2c847`.
221 content files, 11,150,531 bytes; manifest 36,381 bytes, SHA-256
`52a25ca97f73f4e48a9b293898ba571fa0891bf3f583ccafbebf11be904a3e74`.
It preserves packet factors, spectra, rotated accepted states, all inventories,
and source snapshots. The canonical development record binds these hashes.
Original pytest outputs and all predecessor evidence remain intact.
The staged whitespace check caught one extra trailing newline in the native
module. It was removed without changing executable text. The final source
hash and tested source hash are both recorded, and a static check proves that
the archived tested bytes equal the final file plus that single newline.

## Next work and limits

Prioritize a formulation-native fibre/nonlinear section protocol with
station-owned trial/commit/discard state, independent work and tangent checks,
and consistent physical fibre recovery. The current directed scalar-hardening
law is not a general fibre or J2 section adapter and must not be relabeled as
one. Reuse orchestration only; derive the actual material potential and its
conjugate rather than substituting a tangent into elastic formulas.

Distributed forces/couples and load tangents, arc-length/cutback/postbuckling,
reference-backed buckling factors, wider straight/curved/slenderness campaigns,
installed-wheel/performance gates, independent review, and objective
eccentric/curved beam-shell connections are still required. Finite-rotation
transient dynamics and plastic vibration are not established by these spectra.
No complete production or standalone qualification claim is authorized.
