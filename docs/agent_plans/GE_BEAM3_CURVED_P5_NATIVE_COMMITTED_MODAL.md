# P5 accepted-state augmented operator and elastic-interior modes

Parent `8cc53a89d0e323cb6f830ac932cb008791fdb17f`, tree
`4e762637a057cf4f3dc9390c6bed355972f68da7`.

## Progress toward the native eigen workflows

The previous checkpoint connected reference full-inertia matrices to native
FEModel DOFs and supports. This successor takes actual accepted native Newton
states, validates their model and shared nodal rotation authority, and builds
the **current** 24-coordinate operator for each element. The public modal and
buckling APIs are not registered for this private candidate by this change.

The accepted-state adapter:

1. Copies the supplied state, displacement and SPD section-inertia inputs.
2. Revalidates accepted-origin mechanical replay. A detached native rotation
   store checks shared nodal operators without beginning a trial or attaching
   to a caller-owned store.
3. Evaluates the unchanged 36-coordinate compensated mixed potential at the
   accepted positions, nodal operators, cell rotations and endpoint moments,
   using the **previous accepted origins** belonging to that increment.
4. Checks internal stationarity, negative moment block, force/station equality,
   and eliminates only the 12 endpoint moments to form the 24-coordinate Hessian.
5. Checks that a further static cell Schur complement reproduces the stored
   accepted 18-coordinate tangent. This is a witness check only: those six cell
   coordinates are **not eliminated from the dynamic pencil**.
6. Evaluates the existing lifted kinetic field at current cell orientation and
   zero velocity/acceleration. This is the mass for linear perturbations about
   the current configuration at rest, not the reference mass and not Guyan mass.
7. Assembles nodal and internal operators globally, then applies native supports.

The current mass policy is explicit:
`CURRENT_LIFTED_KINETIC_FIELD_LINEARIZED_AT_REST`.
This is a private successor policy for review; it does not silently replace an
accepted production mass policy. No density, strain, potential, kinetic field,
quadrature schedule or accepted mechanical response is modified.

## Material and external-work authority

An accepted plastic increment has an algorithmic Hessian tied to that increment's
origin and return-map branch. It is not automatically a unique small-vibration
modulus. The adapter preserves and verifies that Hessian as a diagnostic but
does **not** silently advance to the new history, re-origin the response, or
label that plastic tangent a vibration modulus.

The initial modal interpretation is permitted only when every station is
strictly inside an elastic branch: no active plastic return and a positive
yield margin exceeding a 64-epsilon scale guard. This is a roundoff exclusion
around a nonsmooth boundary, not a changed material yield law. An actual
uniaxial state on the yield boundary is tested and rejected. Plastic/branch-
boundary modal semantics remain a separate unresolved qualification decision.

Only explicitly supplied nodal **spatial dead translational forces** are
admitted. Their free assembled equilibrium is checked at the existing normalized
1e-11 development tolerance, with moments converted by the model's maximum
element length. Fixed-coordinate residuals are reactions. Nodal moments,
followers, distributed loads and unprovided external tangents are not supported
by this interface. Result provenance binds the current operator and supplied
dead-force work identity; differing reactions cannot silently reuse load evidence.

## Signed spectrum and bounds

The new private source module `_native_stationary_spectrum.py` solves a signed
symmetric pencil. It assembles no mechanics and makes no equilibrium/material
claims itself. The dynamic mass must be positive definite after eliminating
the declared **exactly zero-inertia** trace coordinates. Their assembled
stiffness block must be positive definite: negative algebraic energy cannot
be hidden behind a positive finite spectrum. Negative and zero **physical**
eigenvalues remain present; there is no clipping, inertia regularization,
pseudoinverse or inferred mass kernel.

Full-pencil free-row residual and mass normalization are verified. All six
cell spins per element remain dynamic. Outputs are byte-backed read-only arrays.
The descriptor returns `production_qualified=false`; a negative eigenvalue is
not by itself a qualified continuum buckling factor or critical-point proof.

The development scope remains at most 256 augmented coordinates, homogeneous
nodal supports, no MPCs, point masses or activity/deletion. The earlier reference
adapter now rejects an oversized model **before factor construction**, not just
at eigensolve entry. Cancellation checks bracket solve stages but cannot interrupt
a synchronous LAPACK call. No formal process watchdog is replaced by this helper.

## Verification

Initial two smoke checks passed in 4.09 s. The first 21-test set passed in
10.74 s; the expanded 25-test set passed in 12.11 s. Two actual two-element
checks then passed in 6.26 s. These are separate development runs, not additive
qualification counts. No failing scientific run was retried or reclassified.

After all code changes, the final combined correctness regression completed:
**139 passed in 80.55 s**, using one numerical-library thread, Python 3.13,
`-B`, disabled pytest cache and a fresh temporary basetemp.

The exact combined file inventory was:

- `test_ge_beam3_curved_p5_native_committed_modal.py` (27 new tests)
- `test_ge_beam3_curved_p5_native_modal.py`
- `test_ge_beam3_curved_p5_native_driver_probe.py`
- `test_ge_beam3_curved_p5_native_restart_recovery.py`
- `test_ge_beam3_curved_p5_native_controls.py`
- `test_ge_beam3_mixed_p3_optin.py`
- `test_native_rotation_state.py`
- `test_nonlinear_state_cleanup.py`

Checks include actual native Newton accepted states, matching the separate
moment-reduced elastic potential Hessian, accepted plastic tangent preservation,
unchanged histories, stress-free/reference equality, genuinely current mass and
stiffness, rigid-motion covariance, two-element shared trace balance, rejection
of mechanically replayable but globally inconsistent nodal rotations, negative
physical eigenvalues, singular/negative algebraic blocks, missing/inconsistent
inputs, mutated evidence, cancellation, deterministic output and yield-boundary
rejection. Small straight fixtures show tension stiffening and compression
softening. This is not a 2% Euler/modal benchmark or full buckling qualification.

The alternate elastic Hessian and kinetic checks reuse existing source-equation
helpers. They are not a newly independent scientific review or a formal two-cycle
qualification campaign. No benchmark, resource request, ledger write or external
authority was created; the checks are bounded ordinary correctness tests.

## Continuation and preserved boundaries

The native reference and current elastic-interior full-inertia paths now exist.
Next work must consolidate the candidate's native operator/capability interfaces
and independently verify engineering modal/prestress/buckling references before
public registration. Load classification/tangents, branch-aware nonlinear section
parity, compensated fine-mesh coordinates, full straight/curved qualification and
the objective beam-shell joint remain required. The previously unresolved lateral
critical-point sign is not resolved by these small-mesh checks.

Existing B2/B3/Q4/S3 mechanics, defaults, accepted/failed proof packets and recovery
remain unchanged. A private source module is added; do not describe this as having
no source-code delta. No selector, default, version, release, tag, push or merge
is introduced. The overall user goal remains active and unfulfilled.
