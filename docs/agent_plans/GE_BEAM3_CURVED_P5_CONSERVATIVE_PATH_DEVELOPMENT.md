# P5 committed conservative load path — 2026-09-06

Research successor to `8789681b2b4cc689face4e4b566f875d6ee53c01`, tree
`27455f156be823611dc149feac53dc7ca8668c0f`. The energy initializer, original
assembly solver, earlier failed experiments and qualification evidence remain
unchanged. This is same-author development, not independent qualification.

## Actual load increments, not invented shape histories

The new `ConservativeAssemblyPathProbe` takes ownership of a deep copy of an
existing research assembly. A noninitial input must pass its accepted-origin
replay. The controller accepts explicit spatial dead nodal force arrays and
starts each trial from the committed positions, rotations and station histories.
It never accepts a user-supplied replacement shape for a history-bearing state.

At each global correction all local evaluations use the same committed origins.
The existing variational hardening section supplies its incremental potential,
residual, tangent and prospective station history. Consequently plastic activity
is allowed in this physical load-step controller, unlike the virgin elastic
shape initializer. No local convergence or candidate line-search acceptance
advances a material history. All station histories publish together only after
the unchanged assembly replay/commit validation passes.

The scalar merit is the existing incremental internal potential minus work of
the target spatial dead forces. Spatial multiplicative rotations, the existing
spatial residual derivative, Armijo coefficient, bounded halving and energy
roundoff guard are reused from the earlier research helpers. No constitutive
operator or load measure is changed. The supported section remains the existing
single-direction associative hardening probe with its full coupled SPD 6x6
elastic matrix. This is not general fibre/J2/softening section parity.

Limits per explicit trial remain sixteen global updates, ten backtracks and
256 mixed evaluations per element. Invalid bounds and nonfinite inputs fail
closed. A missing finite descent direction requires an explicit continuation
strategy; no stiffness shift, automatic load subdivision or retry is performed.
This minimum-seeking merit is not asserted to follow unstable branches or
nonconservative follower loads.

## Correctness finding during implementation

The first five-test run produced four passes and one failure before its planned
late-commit injection. On the existing curved coupled case, a committed load
factor 0.01 followed by target 0.02 reached residual 2.390060499352696e-10.
Its next full Newton candidate already had residual 3.669879131908042e-15.

The candidate was nevertheless rejected by the auxiliary energy test:

    old total energy = -4.1446190327312595e-5
    new total energy = -4.144619032731158e-5
    predicted slope  = -2.5292033469819363e-20

The measured energy difference, approximately +1.02e-18, exceeded the old
small-energy roundoff guard. Further unnecessary backtracking ended in a
line-search failure after 150 mixed evaluations. The committed epoch stayed 1.
One explicit diagnostic printed the checkpoints to establish this sequence;
it did not create a raw scientific packet or reuse a formal resource request.

The controller correction checks a finite candidate against the actual existing
equilibrium criterion before enforcing auxiliary merit decrease. A candidate
with physical residual at most 1e-11 is recorded as `ACCEPT_EQUILIBRIUM` and
proceeds to the normal global convergence and replay/commit checks. Nonfinite
energy/scale/merit quantities are still rejected. All other candidates continue
to use the unmodified energy/roundoff acceptance helper.

This changes convergence-test precedence, not the physical tolerance or the
size of the roundoff allowance. The formerly failed small increment now reaches
the intended late-commit test in three updates. That test injects failure after
commit on a private copy and confirms that no state escapes to the controller.
The earlier seed module is not silently edited to acquire this successor rule.

## Transaction and restart contract exercised

- An outstanding trial must be explicitly committed or discarded; another
  `trial` call cannot silently erase it.
- Commit requires the owned object, matching epoch and unchanged digest.
  Copied, stale or mutated trials cannot publish state.
- The proposed assembly and diagnostics are private until success. Failure
  leaves the committed checkpoint and accepted replay unchanged.
- Commit works on another staged copy and publishes only after all element
  validation and output construction succeed. Discard publishes nothing.
- Returned model snapshots are copies and cannot mutate controller state.
- Existing assembly restart is used unchanged. Recreating this controller from
  an explicitly restored assembly reproduces the next trial, accepted state
  and serialized assembly byte-for-byte in the tested path.

This last check does not claim a production controller fingerprint or migration
schema: the research codec preserves assembly physics/state, and callers still
choose this successor controller explicitly. Production algorithm provenance,
hot restart policy and general solver integration remain future work.

## Tests and scientific scope

The final new suite passed **10 tests in 14.48 seconds**, one numerical thread.
It exercises:

1. Curved coupled-section plastic trial, atomic commit and accepted-origin replay.
2. Pending-trial ownership, discard, stale/copy rejection and mutation rejection.
3. Zero-budget failure, followed by an explicitly requested smaller target;
   there is no automatic retry or automatic cutback loop.
4. Late private-commit failure without state publication.
5. The existing two-element height-0.4 curved case under factors
   `[0.1,0.2,0.1,0,-0.2,0]`, order 4: plastic loading and reverse loading,
   elastic unloading, nonnegative dissipation, monotone accumulated history,
   permanent set, resultant/moment balance and exact replay.
6. Restart after the second plastic-cycle increment and identical next trial,
   checkpoint and canonical assembly serialization.
7. The resolved two-element postcritical elastic seed under explicit factors
   `[0.995,1.005,1]`: decrease/increase/return, no false collapse to the straight
   branch, unchanged elastic histories, original force restoration and residual
   agreement at 1e-11. Exact displacement return is not claimed merely from
   force convergence on this ill-conditioned coarse branch.
8. Invalid bounds/nonfinite forces and copy isolation.
9. Rigid reference re-expression of two curved plastic increments: positions,
   rotation matrices, residuals, tangents and station histories agree under
   their physical transforms at the unchanged 1e-11 scale.

The earlier five-test corrected smoke passed in 3.45 seconds and the nine-test
version passed in 12.82 seconds; these are intermediate suite revisions, not
additional qualification inventories. All are small correctness runs, not
performance evidence or a formal resource-controlled qualification wave.

The unchanged conservative initializer regression suite passed **18 tests in
10.60 seconds**, separately from this controller's test inventory.

Implementation SHA-256:
`1AA974A9A96855ED142E5B46E71D21D9F7B5E286D75ABD1C2734C6EAAC49DEA4`.
Test SHA-256:
`60438865DB6ADBE1D21D8D6103FD5889B7A381438D6167FCEF19B4BF6033AC16`.

## Next gate and full-goal status

The curved plastic path and straight postcritical load path are now exercised;
they are not a substitute for an independently referenced curved arch with an
actual limit point. Next, establish a bounded curved arch/postcritical reference
case and use the existing objective continuation controller where load control
ceases to have a valid descent direction. Do not force energy minimization
through an unstable branch or relabel solver failure as physical snap-through.

Broader curved/slender/coupled coverage, general nonlinear section adapters,
robust extreme local stationary solves, prestressed modes, dynamics, production
integration, independent review and objective beam-shell joints remain open.
The complete goal remains active and incomplete.

Only this record, the new research controller and its test are added. Existing
src, B2/B3/Q4/S3 mechanics, defaults, packages, dependencies, workflows and
accepted evidence remain unchanged. No push, merge, release or activation.
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
