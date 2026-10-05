# Independent Read review of the coherent B2 numerical slice

Reviewer: /root/e02_rigid_tip_runner, OpenAI worker separate from product
implementation. No edits or numerical execution. Optional local/Mistral
availability failures from the earlier slice remain unchanged; no different-
family acceptance is claimed.

Initial review found point-only admission scope leakage, a rotation-dependent
bounding-box length, and nonfinite allowance hidden by a finite minimum cap.
Root corrected all three; the reviewer inspected the revisions and reports no
remaining blocker for this development slice.

Certificate: exact Fraction products/sums for active stored-KKT rows, outward
residual bound, downward load cap, zero offset and pure unit selector only.
Sparse immutable KKT is lazy and cleared on close; programming errors propagate.
Public fallback requires footprints. Point-only admission is unchanged.

Footprint gap rule: translation/rotation amplitudes separately map through actual
C coefficients and arms. Each footprint row independently remains below1e-9
of its reference length/rotation scale. Length is twice maximum radius about
reference-node centroid; nonfinite allowances reject. This is a new development
admission rule, not the historical F10/F11 contract or an error-bound theorem.

Claims excluded: element/assembly or forward-error certification, physical
footprint equivalence, E02/F04/F03/aggregate acceptance, performance or release.

# Final independent development review
Reviewer /root/e02_rigid_tip_runner: no edits or numerical jobs; distinct from
product implementer. No remaining blocker for this coherent development slice.
Checked136 source cases,176 installed cases with zero skip/error/failure, example,
retained collection failure, unchanged helpers and same wheel,391 module hashes
and24 comparison input hashes.

The nine cases match geometry/material/positive eccentricity/rigid patch/pure
loads. Work uses conjugate REF translations and ROT rotations. Controls cover
sector decoupling, negligible stub work, patch mapping, transfer/root wrench and
energy. B2/GE maxdifference<6.9e-11; finestexternal Fz+.1478%,Mx-.6203%,My+.1197%.
Native torque lastrefinement+1.3583% remains open. Shared shell code makes GE
agreement insufficient as an independent shell accuracy oracle.

Regression coverage includes exact residual, suppressed tiny loads, real gaps
with successful load certification, affine exclusion, nonfinite allowance,
frame invariance, point-path preservation and cache lifetime. The injected gap
also creates an unloaded equilibrium defect; its test separately proves that
the compatibility predicate rejects it, not an isolated compatibility failure.

No physical footprint/F04/E02/F03/aggregate qualification or speedup accepted.
Solid thickness convergence, tight external output precision, negative
eccentricity, normal spin/full-law and finite GE equivalence remain open.
