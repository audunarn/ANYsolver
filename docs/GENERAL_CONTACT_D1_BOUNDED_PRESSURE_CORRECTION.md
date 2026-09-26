# D1 bounded pressure correction — development candidate

The opt-in `supported_schur_dev` correction is an algorithmic proposal inside
the existing nested augmented contact solve. It does not commit a structural
increment, material state or friction history. This note records the local
method and its current evidence; it does not establish C1 acceptance.

At an equilibrated iterate with supported multiplier vector
\(\lambda_0\), normalized weighted gap \(g_0\), normal stiffness
\(\epsilon_n\), and constrained equilibrium response
\(H=\mathrm{d}g/\mathrm{d}\lambda\), define the local affine gap

\[
g_{\rm lin}(\lambda)=g_0+H(\lambda-\lambda_0)
\]

and projected residual

\[
R_{\rm lin}(\lambda)=
\max\{0,\lambda-\epsilon_n g_{\rm lin}(\lambda)\}-\lambda.
\]

The first candidate is the existing fixed-active-set Newton direction,
backtracked within declared pressure and step caps. If that fails, the
existing projected directional search is tried. The new fallback solves a
small, bounded least-squares problem for the same local projected residual.
It uses the branch Jacobian \(-\epsilon_n H\) on positive projected
arguments and \(-I\) on inactive rows. It starts deterministically from
the current pressure and the lower pressure bound, with at most
`min(8*m + 16, 256)` local evaluations per start for `m` supported modes.
The existing cancellation hook is checked during local residual and Jacobian
evaluation. Candidate choice minimizes the predicted infinity-norm residual, then step
size and pressure norm. The declared supported-mode cap still applies.

The local candidate must be finite, nonnegative, inside the pressure and
step caps, away from a projected kink, and predicted to reduce the residual
by at least 25%. The static owner then re-equilibrates the actual nonlinear
structure and accepts the algorithmic proposal only when its physical gap,
actual active IDs and 25% actual residual reduction pass the unchanged
checks. Rejection restores the original algorithmic state; the original
augmentation and proposal budgets remain in force. The affine response is
local to the current contact branch. The bounded solve is therefore a
proposal generator, not a contact solution or acceptance test.

## Current development evidence

The fixed-pose partial-overlap exact Q1 oracle passed at 4, 8 and 16 source
divisions. In the coupled partial-contact node-1 path, a two-Q4 source
completed with the earlier correction. A four-Q4 source initially rejected
after seven augmentations: pressure change was 0.01593 Pa versus the 0.002
Pa limit, despite a full-rank six-mode scaled pressure Gram. Its second
Newton direction pointed outside the pressure cone and the bounded
projected directional search predicted no improvement.

An independent bounded local calculation found a near-zero projected
residual at approximately \([2.82775,0,0,0,0,0]\) Pa. An explicit branch
Jacobian reproduced it. The production fallback proposed that branch; the
ordinary static owner re-equilibrated and verified it. The local predicted
residual was about \(6.9\times10^{-7}\) Pa; the actual re-equilibrated
pressure change was 0.0014707 Pa. The same four-Q4 mechanical inputs then
completed in four augmentations with physical gap pass, balanced pair forces and a version-2
checkpoint. A fresh-model restart reproduced the checkpoint exactly.
Focused scalar tests passed 7/7, existing affected path tests 7/7, and the
new four-Q4 coupled/restart test 1/1. The first rejected and subsequent
completed full traces are retained under
`reports/general_contact_d1_coupled_refinement_*_20260927.json`.

The independent mechanics reviewer found the local branch calculation
sound as a disposable proposal and required finite/bound/kink controls and
full nonlinear verification. Final source review found no mechanics defect
but identified a missing cancellation point in the local optimizer; it was
added, and its focused checks passed. Neither this four-Q4 case nor
the earlier two-Q4 case establishes general pressure-space stability,
engineering gap convergence, installed-package qualification or the first
accepted shell handoff. The historical 64-Q4 coupled rejection remains
unchanged and has not been rerun.
