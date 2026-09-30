# Bounded staged point dead-load integration review

Read-only source review, 2026-10-01. No mechanics, imports, candidate spectra or numerical jobs were executed. This review covers root-owned integration, not an independent approval of my descriptor/compiler implementation.

Reviewed source SHA256:

- `_stiffened_shell_ge_finite_experimental.py`: `c6f3d7504ee77e4e85ee81a3dee55e6561c79235a3cfcbad61be39bddd3f7f83`.
- `_stiffened_shell_ge_experimental.py`: `60da6cfc8c84f0f7bb3b18a0a9bf2ff748666a69f1772e03ebbf2ce300d91647`.

No actionable integration defect found in the bounded source review. The following conclusions remain subject to the root's installed tests.

`FinitePointDriver._prepare_load` compiles against the physical owner identity before first acceptance. A programme is bound only when an accepted state is published; a failed initial trial leaves the owner unbound. After acceptance, a changed future programme is rejected, including attempts to mix programme and legacy pattern modes. Fixed targets are admitted before work. Adaptive targets are validated against the accepted position and remaining declared targets; adaptive intermediate factors stay between the accepted position and the next admitted target, so they cannot bypass an integer stage boundary.

`_assemble` receives the absolute interpolated spatial force directly and uses that force in both the residual and equilibrium normalization. It does not reinterpret programme position as a force multiplier. `_programme_result` records the identity, position, cursor, fraction, completion flag and detached applied force from the same trial. The existing immutable legacy pattern route remains distinct.

Before commit, `_prospective_checkpoint` prepares the complete programme-framed checkpoint using the candidate generation, histories, state, applied force and optional adaptive controller in a private driver view. Preparation errors and the final cancellation safe point precede publication. The commit publishes those fields with the physical state, followed by the existing postcommit observer. Rebase preserves programme progress and refreshes the checkpoint for the new chart generation.

All inner formats use `_checkpoint_identity()` and the `applied_dead_load` key in programme mode. The augmented identity prevents admitting a stripped inner checkpoint through a fresh legacy owner. The outer descriptor and progress are independently decoded; staged `restore` compiles on the fresh physical owner, then uses a private owner view with the augmented identity and programme context. Inner restore checks the complete accepted position history, exact stored applied force and mechanical state. The outer progress and pending controller are checked, and durable bytes are prepared before publishing the driver and generation to the live owner. Rebinding the prepared driver to the live physical owner is consistent: future inner checkpoint identity comes from its retained programme, not from the physical owner's identity.

Open limits: translation dead forces on the admitted point owner only; no staged moments, follower loads, lines, footprints or broader programme acceptance. Descriptor admission of a zero endpoint does not establish general finite completion at zero applied load: the unchanged equilibrium normalization reports infinite relative error for a nonzero residual with zero load. No norm, tolerance or scientific floor was changed. Installed fixed/adaptive, cancellation, observer, malformed restore and legacy regression results are required to substantiate execution; this source review does not supply those results or F06/F03 qualification.
