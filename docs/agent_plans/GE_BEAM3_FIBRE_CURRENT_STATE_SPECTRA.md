# GE-B3 physical-fibre current-state spectra — development equation map

Parent: `fbc66e6c79e48f5014c5c106c1c63cb9fc17c5fd`, tree
`a2949a57e2099f37705b2e84326de43b6876fa67`.
This extends the private retained physical-fibre candidate. It is not an
independently reviewed qualification or permission to expose a public selector.

## Material policies must be explicit

For the accepted checkpoint, retain the current geometry, retained resultants,
last increment's origin history, and committed physical fibre histories.
The current stationary potential is `Pi(q,p)=p.k(q)-Psi*(p;origin)`.
With `J=dk/dq`, `G=sum_i p_i d2k_i/dq2`, and the cell compliance
`C=d2Psi*/dp2`, elimination of resultant increments gives

`K=G+J^T C^-1 J`.

The coupled cell primal variables `x` and work map `L` satisfy
`sum_j w_j S_j^T s_j(S_j x)=L p`. Consequently,

`A=sum_j w_j S_j^T Ct_j S_j`, `C=L^T A^-1 L`.

Two different questions are supported and never conflated:

- `FROZEN_PLASTIC_COORDINATES_ELASTIC_PERTURBATION`: every committed fibre
  plastic strain is held fixed. `Ct_j` is the elastic section modulus, but
  the affine plastic stress offset is retained. Solve
  `A_el x = Lp + sum_j w_j S_j^T sum_f area_f E_f b_f z_f_committed`
  and verify that `L^T x` reproduces the accepted strain-gradient base.
  This is an explicit elastic-perturbation assumption, not continued yielding.
- `ACCEPTED_INCREMENT_ALGORITHMIC_OPERATOR_DIAGNOSTIC`: reconstruct each
  fibre return at the accepted station strains from the last increment's
  origin. Assemble its actual algorithmic modulus and verify the reconstructed
  cell compliance against the original cell response. A yield boundary or
  hardening knot fails closed. The result describes a last-increment operator,
  not a generally valid plastic vibration frequency.

Station moduli are assembled from individual fibre contributions in 80-digit
Decimal arithmetic before inversion. Serializing a *summed* section tangent
to a high/low pair and then inverting it is not equivalent at extreme contrast.
The initial development run exposed this distinction; its failed output and
source snapshot are preserved, and the compliance tolerance was not loosened.

For `C=R R^T`, keep the inverse root `F=R^-1` as high/low pairs and keep `J`
separate. Check `(F^T F) C=I` before binary64 conversion. The original factor
chain, not a pre-expanded rounded stiffness, is the spectral operator authority.
The existing exact-dyadic factor-chain kernel evaluates complete transformed
bilinear forms with one final rounding. No shifts, stiffness floors, clipped
negative eigenvalues or invented rotary mass are added.

## Current mass and algebraic rotations

Reuse the already declared lifted kinetic field at rest:
`v_h=I v - skew(U lift) omega_cell`, expressed in the current material frame.
The full consistent kinetic factor retains cell-rotation inertia. Nodal
rotation traces have identically zero inertia and their algebraic equations are
eliminated in the spectral solve. The full physical mass must be positive on
the retained dynamic space. This is not a finite-velocity dynamic formulation;
gyroscopic terms and nonlinear transient integration remain unqualified.

The free current-state eigenproblem uses `K phi=lambda M phi`. Negative roots
are retained as signed operator information. A current squared frequency is
not a buckling load factor: a separately defined load-path or reference-pencil
contract is still required for buckling and post-buckling qualification.

## State and scope

Replay the strict accepted fibre checkpoint before construction; do not run
Newton or commit any fibre state during spectra. Bind the checkpoint hash,
operator identities, material policy, supplied section inertias, factor chain,
geometric block and dynamic/algebraic maps in the immutable packet identity.
Cancellation and model guards apply during replay, construction and after the
spectral kernel before publication. Small correctness models only, with an
80-coordinate construction bound and 120-second cooperative construction and
publication deadline; the existing spectral kernel retains its own safeguards.

No existing B2/B3/Q4/S3 implementation, default, package version, public
selector, old checkpoint or prior qualification record is changed.
Independent review remains PENDING. General nonlinear material parity,
finite-velocity dynamics, distributed loads/couples, cutback/arc length,
post-buckling, broad curved-member campaigns and beam-shell joints remain work.

## Separate development inventories and preservation

- Initial compliance smoke: 2 passed, 2 failed, 43.472 seconds; 26 tests
  deliberately outside this smoke inventory. The high-contrast summed-tangent
  reconstruction failure is preserved, not reclassified.
- Corrected complete suite: 30 passed, 90.874 seconds.
- Expanded rotation-fixture attempt: 34 passed, 2 failed, 98.249 seconds.
  Rotated nodes and reference coordinates had used different multiplication
  paths (up to `2.78e-17` difference). The existing exact identity guard rejected
  them. The fixture now constructs references from the actual rotated nodes;
  the guard and covariance tolerance were not changed.
- Final cycle A: 36 passed, 144.618 seconds.
- Final cycle B: 36 passed, 146.812 seconds.

Both final cycles use the same source and yield 18 byte-identical JSON pairs:
accepted fibre histories, native operator packets, spectra and rotated-model
records. They include both contrasts 1 and `1e12`, both material policies, a
separately assembled ordinary generalized eigenproblem at moderate contrast,
the original cell compliance-factor identity, immutable arrays, strict input,
material-claim mutation and cancellation/final-publication guards. Each curved
model is re-solved under the proper common rotation `(0.4,-0.3,0.2)`; maximum
relative eigenvalue covariance error is `3.4149482605596234e-15` against `1e-11`.
These are numerical development checks, not independently authored review.

External archive: `C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-fibre-modes-development-20260907-da3b46826485`.
It preserves 66 content files, 3,766,243 bytes, including all failed outputs and
their source variants. Manifest: 10,160 bytes, SHA-256
`1f9c1b030557499875a6c25195befdbe94dd345a90a9bc974ff63a4360e4185f`.
Original external test outputs remain untouched. No request/ledger operation,
publication, tag, merge or default change occurred.

Next: derive and verify a load-path-consistent fibre stability/buckling and
continuation contract, including the distinction between elastic unloading,
active plastic directions and the last-increment tangent. Do not infer a
critical load from the present current-state eigenvalues alone.
