# S4 full-production qualification program

Status: authorized implementation program; mechanics gate active.

## 1. Frozen authority and evidence

The program starts from `cdc592df5e95f32d2ce922b44589edebea54da4b`
(tree `91c690be3bdbe7d903b4e0f6a36198758d6350d2`) on branch
`codex/s4-full-production-qualification`. The user selected:

- full production, not a restricted linear subset;
- a preregistered comparison of constrained/reduced and energetic mechanics;
- all-at-once parity before public exposure; and
- an explicit opt-in formulation with the legacy S4 default unchanged.

The following evidence is immutable input, never an output target:

| Artifact | SHA-256 |
|---|---|
| `docs/S4_DRILL_CONSTRAINT_DERIVATION.md` | `73CC92FBC445B1267C5C9721E7FEDD21333B65BDDD3285518F5B5DB6BE4CD7F3` |
| `docs/reference_cases/s4_drill_constraint_oracle_output.json` | `8005C6D285263E33FF7F6D4B5138D5FBE4EFAB6A95834C401F94AF044ACD9E1B` |
| `docs/S4_NULLSPACE_SEMANTICS_PROOF.md` | `713465F03BE6221119C1CCB7539301BE01324445DE54FC466D398185B7B481CD` |
| `docs/S4_RESTRICTED_RELEASE_STATUS.md` | `9570D0C58A04AF43E3E94C18926225925E790B753959EE0CE0290DDECC362ACF` |
| Ko-Zhang-Bathe 2025 PDF | `89C10DE1FB13056EB967111C2DBB28FE2D18179090814141455F4E8901D919EA` |
| Ko-Lee-Bathe 2017 nonlinear PDF | `6AF371B5EC7D9B2ED679BA8A7319F30A06331795103471096BE360E339B2FB96` |

The 2025 source is DOI `10.1016/j.compstruc.2024.107622`, preserved at
`.perf2-worktrees/s4-improved-integration/tmp/pdfs/mitc4_d_2025.pdf`
(9,046,388 bytes). The nonlinear source is DOI
`10.1016/j.compstruc.2017.01.015`, preserved at
`.perf2-worktrees/s4-improved-integration/tmp/pdfs/mitc4_plus_nonlinear_2017.pdf`
(1,479,648 bytes). These paths are read-only evidence locations; a missing or
hash-mismatched source blocks derivation review.

The existing result remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`: the literal published operator is
rank 16 with positive-mass `Z`, and the first parameter-free drill constraint
is categorically unstable on `warped_varied_directors` at 160 dps and the
preregistered 0.25 sensitivity multiplier. No later stage may tune a threshold,
fixture, penalty, stiffness, or stabilization to erase that result.

## 2. Ownership and mutation boundaries

- Odin owns the read-only mechanics comparison and independent derivation
  review. Odin edits nothing.
- Heimdall owns the read-only production-seam map and final independent audit.
  Heimdall edits nothing.
- Forsete owns the read-only qualification matrix and contract audit. Forsete
  edits nothing.
- The coordinator is sole editor and integrator. Each stage is committed
  separately and no activation commit is created before all prior gates pass.

Until mechanics selection, permitted tracked changes are limited to this
program, new mechanics case/oracle/derivation/test artifacts, and a versioned
successor qualification contract. Production source, root exports,
`ShellElement`, serialization, assembly, activity, nonlinear, recovery, and
batch code remain frozen.

At every stage preserve the legacy default, activity/native assembly history,
all accepted S4 proof/handoff histories, sibling repositories, and existing
qualification evidence. Do not contact or route decisions through an external
boss; user authority governs this task directly.

## 3. Stage M - mechanics selection

Two separately named formulations are evaluated against identical cases.

### M1 - exact constrained/reduced candidate

Use Fox-Simo's polar-rotation constraint as the primary continuous anchor
(DOI `10.1016/0045-7825(92)90002-2`; the source must be obtained and
content-addressed before equation implementation). From the modified
midsurface deformation gradient `Fbar=R_p U` and independent shell rotation
`R_h`, constrain the continuous relative twist of `Q=R_p.T R_h` about the
reference shell direction to zero. Its small-rotation limit must independently
recover `theta_D-omega_p,D=0`; branch-ambiguous finite rotations fail closed.

Derive the mixed functional with an explicit multiplier field. At the linear
reference solve `[K C.T; C 0] [q;lambda] = [f;0]`. The nonlinear tangent is
`[K + sum(lambda_a Hessian(g_a)), G.T; G, 0]`, with `G=dg/dq`. The constraint,
multiplier space, admissible space, branch convention, and nonlinear
configuration derivative must all be explicit. The implementation may use the
raw KKT system or an exactly equivalent reduced basis, but may not form a
penalty, `C.T C`, or suppress modes using a result-tuned rank target. The
published free operator remains reported as rank 16; a constrained result is
never called local rank 18.

Acceptance requires the admissible operator to contain only the surviving
rigid quotient in its nullspace, `Z_C=0`, and stable constraint rank for every
registered topology and sensitivity. It must explicitly serialize every
removed/constrained subspace and prove exact virtual-work and energy equivalence
on the quotient. It may not remove a positive-energy physical membrane,
bending, shear, or published `/D` drill direction. The previously rejected
`C_D` candidate removed two energetic drill directions and is not grandfathered.

### M2 - variational energetic candidate

The coefficient-free candidate retains the Eq. 15-16 `H_D` enrichment and the
literal Eqs. 24-25 base field, but intentionally supersedes Eq. 21 in its own
strain-energy operator with the fully derived compatible surface strain of
`H_D`, including the midside derivatives intentionally omitted by the
published assumed-strain interpolation. The accepted published identity,
modules, and literal Eq. 21 remain immutable baseline evidence and are not
rewritten or reinterpreted by this candidate. Its potential uses the existing
physical constitutive tensor and no added drill coefficient. It must be named
separately from, and must never be reported as, the literal published 2025
formulation.

This candidate cannot energize the exact zero-mass common-drill gauge because
`H_D q=0` there. It may therefore use only the already permitted explicit and
reported exact-`G` reduction. Acceptance requires coercivity on the
positive-mass `Z` quotient, exact rigid annihilation, correct thin/thick limits,
and no membrane/shear locking. An unconstrained rank-18 version would require a
new compatible displacement field or measured Cosserat/couple-stress material
constants. Values inferred from shear modulus, thickness, element size, or an
empirical scale are hidden penalties and are forbidden.

### M3 - common calculus and selection

Candidate A must preserve literal corrected 2025 Eq. 21. Both candidates must
preserve literal Eqs. 24-25, the full Appendix-B definitions, and the
unused/non-default status of the 2017 Eq. 27 comparison path. Candidate B's
explicit Eq. 21 supersession is governed only by M2 and cannot alter the
published baseline. Apply the accepted mixed-unit scaling and invariant
quotient definitions. Use:

- binary64 `eps64 = 2^-52` and
  `tau(A) = multiplier * 64 * max(m,n) * eps64 * sigma_max(A)`;
- multipliers `0.25`, `1`, and `4` with inherited parent scales;
- `r_tol(d) = 4096 * d * eps64`, where `d` is the maximum of one and
  every row, column, or inner dimension participating in that check; and
- 80-, 160-, and 320-decimal independent calculations plus exact or interval
  certification of every borderline warped singular value.

For a finite binary64 `(m,n)` matrix, an empty or exactly zero matrix has rank
zero, largest singular value and threshold zero, and kernel `I_n`; `n=0` gives
an empty kernel/projector. A derived restriction inherits the multiplier-one
parent scale and never rescales from its own roundoff spectrum. If the parent
is exactly zero, its restriction must be exactly zero. Residuals use
`r_zero(A,X)=||AX||_F/(||A||_2||X||_F)` and
`r_eq(L,R)=||L-R||_F/max(||L||_F,||R||_F)`; a zero denominator returns zero
only for a zero numerator and positive infinity otherwise. All nonfinite data
fail closed. A singular decision is `borderline` when an interval enclosure of
`sigma_i-tau` contains zero at any registered multiplier, or when the resulting
dimension changes across precision or multiplier. Borderline decisions require
an exact or interval sign/rank certificate and otherwise remain unclassified.
Projector symmetry, idempotence, containment, orthogonality, annihilation,
mapped-intersection, and quotient-reconstruction checks use the same
`r_tol(d)`. The trace residual is
`abs(trace(P)-rank(P))/max(1,rank(P))`. Every rank, projector, canonical-basis,
intersection, residual, and zero-matrix convention not restated here is
inherited without override from the frozen nullspace proof SHA-256
`713465F03BE6221119C1CCB7539301BE01324445DE54FC466D398185B7B481CD`.

Required fixtures include flat, affine, skew, tapered, distorted, warped
varied-director, curved patches, noncoplanar fans, connected/disconnected and
odd-cycle meshes, supports/MPCs/coupling, positive activity, hard deletion,
orphans, and cyclic/reversal/frame/origin/scale transforms.

Select the constrained candidate if and only if it passes every gate. Otherwise
select the energetic candidate if and only if it passes every gate. If neither
passes, record a deterministic scientific
`NO_GO`, preserve the dormant release restriction, and stop the program before
production wiring.

## 4. Stage P - common production mechanics

This stage starts only after M3 selects one formulation.

Implement one immutable reference and one potential/strain source used by all
paths. Deliver scalar linear stiffness, consistent mass, residual, exact
reduction or energetic terms, diagnostics, and generalized-section operators.
Then implement total-Lagrangian finite rotations, exact first and second
variations, material and geometric tangent, initial stress/prestrain, follower
load tangent, recovery, state commit/reject/restart, and homogeneous compiled
batches. A production finite-difference tangent or legacy fallback is forbidden.

Every dispatch and cache key must include formulation identity, mechanics
signature, reference/provenance signature, constraint policy where applicable,
and state-layout version. Current compiled stiffness/mass/KG, nonlinear, and
recovery eligibility must be made formulation-aware before any selector exists.
Canonical `ElementActivity` remains element-local and pre-scatter; hard deletion
alone changes topology.

Parity includes every currently supported Q4 workflow: isotropic and
orthotropic elasticity, generalized `A/B/D/As` sections, supported J2 and
Hill-48 shell material paths, initial fields, static/dynamic/modal analysis,
nonlinear response, KG/buckling, follower loads, recovery, current beam-shell
coupling, activity/deletion, direct-reduced assembly, and optimized batches.
It also includes the repository's currently supported limited shell-contact,
transient-impact, simplified damage, and erosion workflows. This requirement
does not create new contact/damage capabilities; it requires parity with the
legacy Q4 combinations accepted at the frozen base.

For a constrained candidate, every linear/modal/dynamic operator uses the same
admissible map (`T.T @ K @ T`, `T.T @ M @ T`, and mapped loads/recovery) or the
mathematically equivalent KKT system. Nonlinear residual/tangent/KG include the
configuration derivative of the constraint and multiplier contribution.

## 5. Stage A - public contract and activation

Activation is all-at-once. After local scientific and functional gates pass,
create a quarantined activation-candidate commit adding the versioned explicit
formulation identity to `ShellElement`, factories, serialization, restart, and
installed-package exports. Use only that quarantined commit for installed-wheel
and hosted qualification. It is not merged to or exposed from `main` unless the
terminal packet records `GO`. Missing or
historical formulation data continue to mean legacy S4. Unknown identities,
mechanics-signature mismatches, unsupported combinations, or state-layout
mismatches fail closed. There is no silent migration and legacy remains the
default for the first release.

The historical 113-claim contract remains immutable. Its successor inventory
is a strict superset of all 113 exact historical case IDs; no ID may be dropped,
renamed, or converted to an unexecuted umbrella claim. It must record
for every case the selected formulation/mechanics/reference identities,
activation counts for scalar/compiled/batch paths, `legacy_fallback=false`,
environment and output hashes, and an executed result. Missing, skipped,
xfail, unavailable, or external-but-unmaterialized evidence is not a pass.

## 6. Frozen acceptance matrix

- Scalar/compiled relative and scaled absolute error: `<= 2e-12`; symmetry
  `<= 2e-12`; negative spectrum ratio `<= 2e-10`; rigid eigenvalue ratio
  `<= 1e-9`.
- Patch relative L2: `<= 2e-9`, distorted patch `<= 1e-8`; rigid residual
  `<= 2e-9`; objectivity `<= 2e-8`; virtual work `<= 2e-10`.
- Convergence slope fraction `>= 0.85` over the existing slenderness,
  aspect-ratio, distortion, curvature, and refinement matrices.
- Mass error `<= 2e-12`, mass moments `<= 2e-10`, modal frequency error
  `<= 5e-4`, repeated-mode MAC `>= 0.995`, and no spurious low drill modes.
- Nonlinear directional tangent error `<= 2e-5`; undeformed tangent-to-linear
  agreement `<= 2e-12`; residual and tangent must be the first and second
  variations of the selected potential.
- Restarted versus uninterrupted displacement, reaction, and state arrays:
  `rtol=2e-10`, `atol=1e-14`; rejected trials leave committed state bytes
  unchanged.
- Dead-load KG symmetry `<= 2e-12`; buckling-factor error `<= 2%`; repeated
  buckling-mode MAC `>= 0.995`; inverse preload scaling and original-pencil
  residuals pass. Follower-load tangents are tested independently and are not
  forced symmetric.
- Recovery relative error `<= 2e-11`, scaled absolute `<= 5e-10`; direct/full
  scatter and coupling virtual-work error `<= 5e-12`.
- All scalar, compiled, batch, recovery, restart, and direct-reduced results
  satisfy the same gates with no legacy fallback.
- The full hosted Windows/Ubuntu Python 3.11-3.14, Numba, Pardiso, wheel, and
  compatibility matrix passes, and installed wheels exercise both legacy and
  opt-in identities.

The hosted matrix is the 24-job `.github/workflows/ci.yml` shape accepted at
the frozen base: eight full pytest jobs, eight Numba jobs, two Pardiso jobs,
two wheel-smoke jobs, and two two-row compatibility matrices. Attempt one must
be the sole Tests run for the activation-candidate head and all 24 jobs must
pass; any Publish or unexpected workflow run blocks acceptance. Local
historical-proof source origins are pinned to ANYfileIO
`5513881827cdee9fd337497a2730a5912d8ea751`, while hosted and installed-wheel
qualification pins its child
`48c6423c2aaf1f94f7bea8e7a971adf99500a91f`; their `src` trees are
byte-identical at Git tree `d622317d7237b808d2f1ec82efedd554882cb291`.
The other pinned source origins are ANYmaterial
`4626887667f4c251479d26f321b9e73b046a2783`, ANYmesh
`979f6a88f0d81507e1ac61b854f1f56362ce5e37`, and ANYgeometry
`939e047f19177692c861a68eaef0eaa18b2976c5`; a later pin requires an explicit
content-addressed amendment before execution.

The performance baseline is the frozen base commit/tree above, measured in the
same process and environment as its candidate. The preregistered host lane is
CPython 3.13.9, NumPy 2.4.3, Numba 0.65.0, Windows 11 AMD64, processor identity
`AMD64 Family 25 Model 97 Stepping 2, AuthenticAMD`, 32 logical processors,
and one-thread OpenBLAS 0.3.31.dev reporting architecture `SkylakeX`. Before
timing, bind interpreter/runtime/NumPy/Numba/BLAS binary hashes and controlled
thread variables into the packet; any mismatch between baseline and candidate
invalidates the pair rather than changing a limit.

Performance uses warm-JIT paired adjacent runs, one Numba thread, at least 11
samples, and no unavailable/fallback case. Candidate/baseline median limits are
1.70 linear K, 1.30 mass, 1.80 KG, 2.50 elastic residual/tangent, 3.50
direct-reduced residual/tangent, 2.00 plastic residual/tangent, 2.25 recovery,
and 1.80 retained bytes per Q4. Performance never relaxes correctness.

## 7. Terminal conditions

Production `GO` requires every scientific, functional, external-evidence,
compatibility, performance, and hosted gate. Any positive-mass quotient
mechanism, categorical rank drift, unproved coefficient, lost physical mode,
legacy fallback, missing external case, skip/xfail, restart mismatch, or hosted
failure preserves `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

No package publication or change of the legacy default is part of this program.
