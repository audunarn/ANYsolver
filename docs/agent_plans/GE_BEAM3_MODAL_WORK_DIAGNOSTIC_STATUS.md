# Saved modal-work diagnostic completed; engineering comparison still fails

Frozen source 28c2d30e0a3cb16ccd29f6a6f068b65bebdcb9d1,
tree bde42efd74b1df60ae46e6cd7a0b175ac9bcd008. Four research-only paths;
11 targeted tests passed in 0.62 seconds before freeze. Existing beam/shell
mechanics, material/state laws, mass, recovery, defaults and versions unchanged.

## Result and limits

Both signs and both replicas completed the declared saved-work diagnostic.
All six modes were retained. Original native factors reconstructed their modal
Rayleigh quotients within 1e-11, using Decimal80 without a new eigenanalysis.
Reference material/geometric terms reconstructed the saved finest trial Hessian
and physical mass within 1e-11 normalized matrix error. Separate cross-product
modal densities agreed within 3.110383041650948e-13 normalized component work.

For the failed third sorted mode at the positive endpoint, physical mass is one:

| Contribution per physical modal mass | Native | Reference | Difference |
|---|---:|---:|---:|
| Material stiffness work | 2.347354709146605 | 2.339749250293772 | +0.007605458852833369 |
| Geometric/prestress work | -2.2650518274607467 | -2.26134740624102 | -0.0037044212197265836 |
| Signed total | 0.08230288168585821 | 0.07840184405275163 | +0.003901037633106577 |

The cancellation ratio (sum of absolute component works divided by absolute
total) is 56.04186 native and 58.68608 reference. Thus small changes in large
opposing contributions have substantial relative effect on the weak mode.
The native material contribution is higher and partly offset by a more negative
geometric contribution. Negative-endpoint diagnostics reproduce this pattern.

This supports investigating discretization/equilibrium sensitivity. It does NOT
prove a transcription defect, isolate load-error causality, demonstrate a stable
branch, or authorize changing mechanics. Each operator was evaluated at its own
equilibrium and its own mass-normalized mode, so the contributions cannot be
interpreted as an exact common-state error decomposition.

The earlier 2.45764797% modal rate error still fails the unchanged strict 2% gate.
No engineering acceptance is inferred from this diagnostic's successful checks.
The separately accumulated reference modal Rayleigh errors are diagnostics,
as preregistered; some exceed 1e-11 relatively (e.g. 6.78e-11 for the weak second
mode) while the original saved pencil checks and this diagnostic's declared
matrix/component checks pass. No original eigenanalysis threshold is replaced.

## Process and logging incident

Four workers exited zero, empty Job trees, no timeout/memory/cleanup failures.
Same-sign diagnostics were byte-identical. Positive smoke first, then three
concurrent workers. Wave 11.978282 seconds; child 5.331-6.645 seconds;
peak tree 505421824 bytes. Existing one-thread, 600s/24GiB child, 1800s wave,
120s inner and inactivity bounds retained. No equilibrium/BVP/eigensolver rerun.

The coordinator's final noncanonical stdout line mistakenly used the label
comparison_passed=True for diagnostic completion. This administrative label is
NOT scientific authority: the canonical aggregate correctly records
decomposition_passed=true and comparison_gate_passed=false, and every diagnostic
also records comparison_gate_passed=false. The consumed helper is preserved in
the archive and its original terminal output remains in the task history. Do not
rewrite these or rerun the wave. Future helpers must use the correct label.

## Archive and audit

C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-modal-work-28c2d30-20260909.
30 manifest-bound files plus manifest, exclusive staging/external copies verified
by exact bytes/hash/extent; original TEMP remains intact.

Manifest 3898 bytes, SHA-256
524bc3b7abbf7ead29cf7f6181a006f54a73fb604f765d3ee701739e4705dd44.
Saved audit 3063 bytes, SHA-256
d1ceb11c58100567b5e155fc12f06fb982a3beb29d88c729b6cf9a8ea9bd4fa5.
Aggregate wave/complete.json 3119 bytes, SHA-256
51ecdf773e46c035c41aeb25ec04966ec91d7cd2ef1c6fca1e8c8280eebd6851.
Positive wave/plus-a/output/diagnostic.json 5476 bytes, SHA-256
f016002f93db1c496bef88279b948d993f0119c48dc332ec7b533e99b553d423.
Negative wave/minus-a/output/diagnostic.json 5566 bytes, SHA-256
56e435b3d778b3312d63577431ea41249c6c4f52fab1c8b0f6a2018af2e35687.

The standard-library saved audit checks canonical parsing, bound replica bytes,
four bounded terminal receipts, explicit failed-comparison scope, six-mode work
and difference accounting, positivity, cancellation and declared diagnostic errors.
It is not an independently authored mechanics review.

## Next gate preparation

Preregister a same-problem native mesh-convergence successor before any new solve.
Retain the already checked N24 results and resolved continuum polynomials/spectra.
An N32 candidate can test whether the discrepancy decreases with refinement at
the same +/-0.0065 amplitude, section, loads, physical clamps and arithmetic policy.
This is a proposed new case, NOT authorization to rerun any consumed N24 worker,
relax the 2% gate, replace the finite-element formulation, or activate the beam.

First inspect and test research capacity assumptions. N32 requires 582 full
coordinates (570 free, 189 algebraic and 381 physical), 576 resultant links and
64 half-cell velocity maps. Current 512-coordinate/8192-row spectral limits,
24-element model/owner caps and hardcoded N24 comparison maps must not be silently
overridden. Any capacity-only successor needs its own frozen exact extent,
dimension/mapping tests and bounded smoke. Preserve historical N24 code/evidence.
New elastic equilibrium seeds must be genuinely solved/enrolled, not relabelled
N24 history. Do not extend per-process limits merely because refinement is slow.

Then compare all six signed rates and physical MAC at both signs using unchanged
criteria, with replica agreement and proper bounded termination. A decreasing
error supports discretization convergence but is not, alone, full beam qualification.
If bounded N32 cannot be implemented without mechanics changes, stop for explicit
successor design rather than tuning. Full straight/curved beam, materials/state,
solver/load/dynamics parity, independent review and objective beam-shell joints
remain incomplete. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
