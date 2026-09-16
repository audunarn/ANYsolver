# ANYsolver 0.4.4: bounded B3-GE opt-in release

ANYsolver 0.4.4 publishes the already accepted `B3-GE` workflow through the
explicit `b3-ge` selector. It does not change the legacy B3 default, redirect
the historical `ge-beam3` formulation, or change qualified Q4/S3 mechanics or
defaults.

The release gate is intentionally bounded. It validates the immutable G7
contract, confirmation, review, and status; builds one wheel and source
archive; compares every installed runtime module with the release source;
installs the wheel into a fresh external target; and confirms the selector,
name, provenance boundary, installed origin, and legacy B3 default. Each child
process has a three-minute timeout and no scientific campaign is rerun.

The active tree no longer carries unreferenced development notes. Historical
plans still used by authority tests and hash contracts remain. The complete
pre-cleanup tree is preserved by Git tag
`archive/anysolver-pre-0.4.4-development-20260916`, while raw workspace
residue was moved to the dated external ANYrelease archive. Release source
archives contain only package source, licensing and migration material, and
current user-facing documentation; research plans, raw evidence, tests,
scripts, reports, caches, and temporary worktrees are excluded.

Terminal on success:

`PROVISIONAL_GO_ANYSOLVER_0_4_4_BOUNDED_RELEASE`

This terminal authorizes publication of the exact 0.4.4 artifacts only.
