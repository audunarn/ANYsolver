# Independent DC globalization, wrapper and continuation review

2026-10-18; static review while Mistral's objective-mean delivery remains active.
No imports, numerical execution, tests, product edits or workers. Reviewed the
current DC helper, both performance-wrapper forwarding branches, relevant state
transaction helpers, continuation assertions, D1 spy and temporary SO(3) helper.
The previous parent TypeError is retained failed evidence; this review does not
claim the corrected wrapper has been executed successfully.

## Product seams statically corrected

- The adaptive retry now requires a strictly positive finite attempted span and
  cutbacks_this_step<8. A zero target span cannot satisfy the positive-span test;
  even a pathological span cannot cause unbounded cutback retries. The original
  DC1 infinite-loop defect is resolved by inspection. A dedicated zero-span
  regression was not present in the inspected Slice3 test modules.
- step_iterations resets after an accepted subdivision before attempting the
  remainder, avoiding the prior double count in later accepted records. The
  solve-wide total remains separate. This statically resolves DC2.
- The ordinary assembled augmented system declares GENERAL. The D1 test spies
  on nonlinear_static.factorize, requires at least one n_red+1 factorization,
  and asserts every captured augmented class is GENERAL. The old symmetric
  declaration would fail even if SciPy LU happened to solve correctly; optional
  PARDISO availability is not required for this test to discriminate.
- nonlinear_performance._solve_static_displacement_control_block now accepts
  recover_initial_load_factor=False, sends it through both original-solver
  branches (around1563 and1627), and includes it in checkpoint_path admission.
  The original DC helper accepts the same optional argument. No remaining
  missing-keyword forwarding defect was found in those paths.

The guard's comment also claims representable target progress, but the actual
test does not compare the newly halved floating-point target with
attempt_start_control. A tiny positive remaining span can round a half target
back to the accepted start; that candidate can be published as a zero-progress
accepted subdivision. The new cutback cap bounds this case, so it is no longer
an infinite-loop bug. For the claimed monotone subdivision contract, refuse a
halving whose constructed target is not strictly between start and milestone.

## Line-search and ordinary-resume lifecycle

The added contact-free rotating-map line search evaluates at most eight alpha
values, using the current residual/control convergence scales. It never commits
the residual-only candidate. Persistent begin_state_evaluation replaces/discards
the previous pending transaction; ordinary assemblies return fresh dictionaries.
The next Newton iteration reevaluates the chosen state with its tangent, while
failed increments restore q/lambda and discard the last pending candidate.
Thus an explicit discard between every line-search alpha is not required by the
current replace_trial contract. Cancellation/exception cleanup remains owned by
the public finally scope, and no residual-only state is directly committed.

If no alpha meets the decrease test the implementation takes the original full
Newton step. This is explicitly documented compatible fallback, so the code
does not establish a guaranteed descent method or convergence improvement.
Actual target completion remains an empirical gate. No constituent-error
backtracking guarantee is present: an assembly exception propagates through the
existing cleanup instead of being silently treated as a successful line search.
Do not broad-catch cancellation/validation failures as recoverable cutbacks.

The initial-lambda predictor is gated to ordinary supplied displacement/history,
explicit equilibrate_initial_state=False, active rotating map, and no restored
serialized path. It assembles the copied initial state, discards that diagnostic
trial, projects reduced internal-minus-constant force onto the actual initial
proportional force, and uses the scalar as a Newton guess. It does not commit a
new material state or weaken residual checks. Serialized checkpoints keep their
stored lambda, while legacy no-map defaults are unchanged. If supplied initial
state is not proportional equilibrium, the projection is still only a guess;
do not label it a validated prior load factor without checking its residual.

## Concrete continuation-test findings

### G1 — P1: inverse/forward round trip is not a manifold oracle

Around continuation test lines502–507, the code claims
apply_kinematics(to_linear_displacement(stored_u)) checks MPC membership. Those
helpers are ambient inverse coordinate corrections. Their composition equals
the identity for an arbitrary slave perturbation, including an incompatible
one. This test can pass with a violated MPC.

Use constraint_residual_summary(model,to_linear_displacement(stored_u)) with
the existing tolerances, and/or independently evaluate the physical translation
and orientation relations. The existing Slice2 perturbation test demonstrates
the right distinction. Keep the round-trip test if useful as a separate inverse
property, but do not call it a constraint residual.

### G2 — P1: resume material comparison requests a snapshot that does not exist

At continuation test line678 the loop includes `[-0.10]+tail_milestones` and
looks up every value in resumed_result.snapshots. Ordinary resume records only
new accepted increments after the -.10 initial state; it does not append that
input state as an accepted snapshot. _snapshot_at_control(...,-.10) therefore
has no match on a correct resumed solve. Compare the split state using the half
result (already done in the half-prefix loop), and compare resume snapshots only
at tail milestones. Do not insert an unevolved fake accepted step just to satisfy
this assertion.

### G3 — P2: reconstruction immutability snapshots are shallow aliases

stored_u=np.asarray(snapshot.displacements) at488 is a view, and
stored_states=dict(snapshot.element_states) at489 copies only the outer mapping.
Comparing these after reconstruction to the same underlying values does not
prove they were unchanged. Inside _independent_equilibrium, material state is
deep-copied before assembly but no before/after comparison of that supplied copy
is performed; mutation of the disposable reconstruction input could go unnoticed.

Freeze independent np.array(...,copy=True) and copy.deepcopy(...) snapshots of
stored values, and freeze/check the assembly's own supplied copy too. The new
per-snapshot residual is correctly evaluated at snapshot.load_factor and now
uses achieved-load normalization; the remaining issue is the no-mutation oracle.

### G4 — P2: full-history helper overchecks metadata and mishandles nested lists

_assert_states_allclose compares every state key, including origin/cache/seal
bookkeeping, rather than explicitly selecting physical plastic_strain, alpha
and relevant fiber/section history fields. Nonphysical trial-origin records can
legitimately differ across subdivisions; exact string/key equality there can
reject equal physical history. Conversely the docstring should not imply that
any future physical field may be ignored. Declare the relevant physical field
set/schema and retain its existing strict tolerances/shapes/element identities.

The helper's recursive call on a nested list/tuple is also wrong: its entry
assumes mappings (`set(left)` then `left[key]`). A list of dictionaries raises
unhashable-type error; a numeric nested list is indexed by its values. This may
be latent if current physical states use only dicts/arrays, but the branch does
not implement its advertised recursive support. Use a type-dispatched recursive
comparer or remove the unsupported generic branch after selecting known fields.

### Coverage now present and still missing

- Every accepted snapshot now receives an independent residual reconstruction,
  including adaptive states, at its own achieved lambda. This is materially
  better than the former final-only check, subject to G1/G3. Full GP/fiber arrays
  are now compared, subject to G2/G4; scalar maxima are no longer the sole intent.
- Per-snapshot wrench checks currently run only for direct coupling while the
  interp objectivity repair is open. Retain that limitation in reported status;
  after the new mean, restore identical physical-wrench acceptance on both routes.
- Refusal now retains/checks both displacement and material caller inputs.
  Cancellation checks exact input preservation and successful reuse. These are
  distinct from tolerant resumed-vs-uninterrupted physical-history comparisons.
- The stopped-resume test still passes restart arrays/history inline and checks
  only the returned control coordinate and record/snapshot counts. It cannot
  demonstrate exact caller preservation or that returned plastic fields equal
  the last accepted state. Retain named inputs/frozen copies and compare them,
  plus last accepted physical fields. Cancellation still observes events rather
  than complete accepted snapshot contents surviving later trials; a focused
  snapshot capture can close that gap without changing mechanics.

## Temporary objective-mean helper: consequential guard/differential review

Reviewed patch/_so3_mean_block.py, not yet the integrated product. The proposed
implicit derivative is correct on a smooth stationary branch. For
psi_i=Log(R_m.T R_i), A_i=J_l(psi_i)^(-1), B=sum(w_i A_i), varying spatial master
spins gives B*R_m.T*Omega_m=sum(w_i A_i R_m.T Omega_i), hence the shown Ghat_i
and additive-coordinate G_i. The differential identity follows algebraically.
This does not establish uniqueness, branch selection or a valid shortcut.

### M1 — P1: principal relative logs + nonsingular determinant do not imply a unique mean

The helper accepts a stationary mean whenever each |psi_i|<pi and detB is not
tiny. Equal-weight Rx(+pi/2), Rx(-pi/2) has two equal-energy means I and Rx(pi).
At either, every |psi_i|=pi/2; B has eigenvalues1,pi/4,pi/4, so its determinant
is nonzero and comfortably above the threshold. The existing guard accepts the
ambiguity. The old arithmetic initialization also changes under a global rigid
rotation and can select a different basin; local convergence is not objectivity.

Admit a strict declared common convex domain based on an equivariant physical
anchor, and require both inputs and returned mean to lie in it. A conservative
construction is an anchor ball of radius rho<pi/4, whose pair distances remain
strictly below pi/2; use a stated margin and verify the symmetric mean Hessian's
positive definiteness/conditioning. This is a proposed sufficient bounded domain,
not adoption of a particular rho. An objective anchor-relative initializer avoids
frame-dependent basin selection. A different rigorously justified convex domain
is acceptable; determinant magnitude alone is not a convexity/uniqueness test.

### M2 — P1: identical shortcut has an absolute-chart discontinuity

For exactly identical master vectors with norm>pi the shortcut returns the raw
vector. An arbitrarily perturbed set instead reaches rotation_vector_from_matrix
and returns the principal logarithm, differing by about2*pi. The returned slave
rotation coordinates jump even though physical master orientations change
infinitesimally; the supplied derivative is not the derivative of that piecewise
map. A mean at/near absolute angle pi has the analogous log-branch issue even
when all relative psi_i are small.

For active multi-master interpolation, define and enforce the supported absolute
rotation-vector chart with a strict margin before identical shortcuts and before
return. Do not silently claim chart crossings. Keep the one-master/direct legacy
limit separately compatible; a new arbitrary direct-route refusal is not implied.
If nonprincipal input vectors are intentionally admitted, use a continuous
explicitly stateful chart/branch treatment throughout restart/Jacobian/force maps
instead; that is larger than the currently bounded local-mean scope.

There is also a near-partition shortcut inconsistency: a stationary intrinsic
mean's coincident derivative is (w_i/sum(w))*I, while the exact-identical shortcut
returns w_i*I for any sum accepted within tolerance. Use a consistent admitted
partition in mean equations, shortcuts and linearized map; do not claim the
exact spin identity for an uncorrected nonunit sum. Standard current weights may
sum exactly1, but the helper guard itself admits the discrepancy.

These findings require candidate guard/branch decisions, not another derivation
of the old nonobjective map. No algorithm or scientific tolerance is adopted by
this report. Product convergence/objectivity outcomes remain unverified.
