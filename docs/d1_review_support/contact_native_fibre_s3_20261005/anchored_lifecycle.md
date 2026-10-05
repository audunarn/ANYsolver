# Anchored whole-band root enclosure and fine lifecycle

Development candidate, 5 October 2026. Parent source `47dc4070`; exact artifact,
resource and checkpoint identities are in [the summary](anchored_lifecycle_summary.json).
No native engineering acceptance, release or balanced speedup claim.

## Decision and equations

The previous componentwise fine opening timed out at 120.154642 seconds without
an accepted second target. The retained first actual Newton trace isolated full
trial root uncertainty and half-trial integration exhaustion. This candidate
changes only an explicitly selected conservative root tangent enclosure.

For one fixed complete scaled gradient anchor v, direct whole-band variation
bounds E and positive common mass bound F, the leading difference is bounded by
F*(vi*v1 + 2*(vi*E1 + Ei*v1 + Ei*E1)). Here vi/Ei are infinity norms and v1/E1
are one norms. Decomposing each integral into mass*v*v^T plus its variation
remainder establishes the bound. The mass bound includes fallback quadrature.
The direct g-v envelope covers the entire declared arc and axial band, including
additive cancellation rounding. The previous doubled spatial/general remainder
is unchanged. Take the minimum only among valid leading bounds.

`root_tangent_enclosure_policy='anchored'` is explicit and restart-bound.
Defaults, componentwise/spectral equations, integration limits and scientific
tolerances remain unchanged. No failed increment switches policy automatically.
Supporting same-family implementation review found no consequential defect; it
does not substitute for independent engineering assessment.

## Results

| Installed check | Elapsed s | Peak bytes | Result |
|---|---:|---:|---|
| Local work, bounds and policy identities | 6.113 | 186130432 | 7 passed |
| Saved actual full opening trial | 10.782 | 180355072 | passed |
| Fresh first target from coordinates only | 5.945 | 180109312 | passed |
| Opening from new checkpoint | 6.310 | 180432896 | passed |
| Recontact from opening checkpoint | 8.369 | 180125696 | passed |
| Exact active/open/recontact fixture replay | 4.316 | 181211136 | 3 passed |

All 526 production Python files match the installed wheel. Imported module paths
were checked; no import-root errors. JIT disabled, effective numerical pools one.
Each native process/owner retains its original 120-second/953-MiB limit, counted
from construction without resetting. No unchanged full opening was retried.

Saved full trial: 7 intervals/5760 evaluations, scaled tangent uncertainty
9.060432e-7 <=1e-6. Independent analytic residual relative discrepancy
4.889345e-13. At h=(2e-6,1e-6), tangent errors (9.394188e-8,2.386901e-8) and
virtual-work errors (5.794105e-7,1.452288e-7) pass the unchanged 1e-5 criteria.
The larger h=1e-5 virtual-work failure remains retained; the smaller-h trend is
consistent with second-order finite-difference truncation, not a retroactive pass.

The componentwise checkpoint is never restored under the anchored identity.
It supplies only a structurally bound coordinate guess for a fresh first-target
solve with virgin physical material origins. New accepted first-target response
differs by at most 6.470004e-16 relative in the reported quantities. This policy
parity allows reuse of the unaffected preceding 8e7-vs4e7 enforcement evidence;
that convergence run was not repeated.

Opening: 25 candidates/10 pair evaluations/15 reuse hits, no trial failures;
independent gap +9.321261e-5 m, zero contact force/storage. Recontact: 23/10/13,
no trial failures; independent gap -6.300831e-6 m within 30 um. Both pass complete
wrench balance, independent material-history reconstruction from the committed
origin, monotone cumulative plasticity, exact prefix/restart and cache/lock cleanup.
Three accepted checkpoints are byte-preserved under tests/data; hashes are in
the summary and exact-replay tests.

## Reproduction and next boundary

The archived [first-target runner](anchored_first_target_runner.py),
[lifecycle runner](anchored_lifecycle_runner.py) and
[saved-pose runner](anchored_opening_pose_runner.py) preserve executed inputs.
Raw logs/preflights remain under
`C:/ANYworkspaceWork/contact_native_fibre_s3_20261005/candidate12/`.
Earlier timeout and larger-perturbation failures remain under candidate11.
Do not replay completed coupled stages merely to recreate evidence.

This closes the fine enforcement-profile opening/recontact development gap for
one curved physical-fibre beam and one deformable S3 patch. Multiple native beams,
section/material breadth, spatial convergence and independent native acceptance
remain open, along with the wider friction/dynamics/application programme.
