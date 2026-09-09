# N32 full native stiffness sign-count gate

Parent7783d87f198a35ea2ceb6228d535e3c03c0ecc65. Six additive research paths:
this plan; ge_beam3_n32_front_inertia.py, ge_beam3_n32_scaled_inertia.py,
ge_beam3_n32_energy_inertia.py, ge_beam3_n32_inertia_worker.py and its test.
No src/default/public interface/mechanics/load/mass/recovery changes.

Bind N32 factor archive manifest c4d423901838d9b47f8b4273a2e69359abfc96eea102389d9fa597e35fc68343
through the existing exact factor loader, and accepted spectral manifest
05df67c233cd21d0f69340a88f3809b9758c3774718dbfa91dac38d3d202b067.
Signed100digit spectra are91134/91222bytes, SHA-256
9a1c89d8ab13d0c6d2e4c0d44fe225de377fd8cfe9bc4672ab679d2cca69facc /
4e41d4da4b407b0ad6b8af7c11bb28fe210cd4a8987d8e0881e94c0e93e0dc45.
All original prefix/model/state/reference chains remain immutable. No native
capture, equilibrium, continuation, BVP or eigenproblem is rerun.

Copy the three historical front-aware/scaled/energy audit kernels with only
capacity512->640, factor-row8192->12288 and their new local import routes.
Require AST identity after exactly these substitutions. Preserve complete
original K=(LR)^T(LR)+sym(H), M=B^TB at Decimal80/100; no early rounded tangent,
drop, stabilization, artificial trace inertia or control-support substitution.
At each precision prove positive trace189 stiffness and positive physical381
mass numerically with the same full congruence. Count all570 free original
stiffness coordinates at shift0. Both precisions/signs must produce the same
counts and agree with the saved six-low-mode negative count. Do not prereplace
the full result with an expected1negative/569positive count.

Retain pivot multiplier<=2, front<=96, two-million update bound, growth bound,
1e-50 unresolved-pivot floor, exact sparse nonzero preservation, full reverse
Schur reconstruction<=1e-60, positive diagonal congruence and original-coordinate
reconstruction<=1e-60. Zero/unresolved pivots fail closed; no zero-mode rounding.
Raw geometric symmetry remains independently disclosed and bounded1e-11.
Decimal and residual checks are not interval-certified inertia or a proof of
the full continuum Morse index. This limitation must stay explicit.

Tests: capacity-only ASTs, known nonsingular570-coordinate L D L^T signed
congruences at80/100, byte-identical historical small-factor results, raw
symmetry/zero/nonfinite/fill/capacity/cancellation rejection, original120second
deadline, source mutation and full-count/pivot/scale/reconstruction/scope mutation.

Clean freeze then one plus100 smoke. If it completes, run remaining seven
sign/precision/replica jobs, maxthree concurrent. Each child one numerical
thread,600seconds/24GiB; internal audit120seconds; CPU-inactivity120seconds;
complete wave1800seconds. No automatic retry or reused directories. Complete
aggregate only after all eight launched trees are terminal. Same-profile raw
inertia records must be byte-identical. Counts agree across signs/precisions.
Process/malformed/precision/replica failure blocks; genuine disagreement with
the retained modal negative count is a NO-GO diagnostic and must be preserved.

Success closes the full native inertia check only at these two equilibria.
Next broaden prestressed/postbuckling state and parity coverage. Overall
straight/curved beam qualification, nonlinear generalized/fibre material/state/
restart/solver/recovery parity and independent review remain unfinished, as do
objective finite-rotation eccentric/curved beam-shell joints. Existing B2/B3,
S3/Q4, defaults and versions are unchanged; no merge, tag or publication.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
