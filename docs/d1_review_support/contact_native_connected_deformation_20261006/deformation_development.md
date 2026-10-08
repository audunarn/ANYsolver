# Connected native deformation/support — tested development

6 October 2026. Source candidate `15d34aa340a7af1f8819fa9f40a5ddf9d3384b46`;
product candidate `7986c5bdf04843dd403421e5f42bf399536ab7ab` unchanged.
User approval “I approve” supplied a separate 180-second
`C7_CONNECTED_DEFORMATION_DEV` allowance. Frozen source/input manifest SHA256
`e6b04e0feff115307a670a585c8c8f63f28767af546128a668a55ade903b2c64`.

## Outcome

Three distinct installed tests PASS: independent primitive mass/virtual work/
complete algebraic Schur tangent; full four-step endpoint/stage/initial response
and support accounting; exact full four-step versus fresh 2+2 restart.
The actual public CLI also completes four steps at 6.103515625e-5 seconds.
The work test uses its two-step fixture; optional response/restart [2] variants
were not executed and are not counted. No skipped or failed numerical case.

The primitive four-affine-P1-half-cell reference is independent of production
mass/structural/contact kernels. Initial strain, nonuniform accelerations,
retained forces and nonzero offset-support force/moment are checked. Full
root reaction includes off-diagonal consistent-mass inertia. All physical
coordinates remain in the production trajectory. This closes the bounded axial
deformation/support gap, with unchanged frozen criteria.

| Job | Exact process-wall seconds | Peak tree bytes |
|---|---:|---:|
| mass/work/tangent | 17.264534100075252 | 167325696 |
| full response [4] | 14.319503600010648 | 168710144 |
| fresh restart [4] | 26.69080620002933 | 168054784 |
| actual CLI [4] | 14.77752290002536 | 146407424 |

Four-job measured sum **73.05236680014059 seconds**. Initial runner-root refusal
launched no solver child and produced no helper resource record; observed outer
wall 0.2081476 seconds is conservatively charged, with exact helper wall
unavailable. **Charged 73.2605144001406/180; remaining 106.7394855998594 seconds**,
only for this approved candidate's scoped repair/recheck. No borrowing or renewal.
All jobs terminal; no optional repeat needed. One job <=60s, 953MiB cap.

Maximum recovered normalized energy defect 1.6940658945086004e-16;
linear/angular support-impulse defects 5.551115123125783e-16 and
1.3877787807814457e-16, respectively. These are saved-output accounting measures,
not broader spatial or temporal error estimates. Maximum support force
0.9898152834832071 N; moment 0.2766617823795845 Nm. Full/resumed public result
dictionaries and exact 95,975-byte checkpoint agree; checkpoint SHA256
`0aede56a5f5e494e80239d8774e2d4d4f3263a3fb6ec94728bc4fa3871564de5`.

## Artifact and retained failures

Reused private wheel SHA256
`a9febab4c77ce607c00afe77dd04781b5f6c82e6f53232ec20284d8d1ef516b6`.
Lead byte audit confirms 549 source/wheel/installed payloads, six metadata
records, complete RECORD containment/hashes, and 196 private imports per run.
Effective JIT disabled, Numba one, observed pools one. No build or reinstall.
Documentation changes after this audit do not change frozen numerical inputs
or the product artifact.

Original runner hash 5a507fa1... remains in immutable authority/preparation;
corrected runner d3d16a14... is bound in each actual job. The path-only repair,
prelaunch refusal, original runner and original source review finding are retained.
Preparation/source-only headers are historical, not evidence of passes.

Raw records, exact commands, runtime/import/resource records and actual results:
`C:/ANYworkspaceWork/contact_native_connected_deformation_20261006`.
Private target: `C:/ANYworkspaceWork/contact_native_connected_transient_20261006/connected_shared_installed1`.
[Machine-readable disposition](root_execution_audit.json),
[supporting saved-execution review](final_execution_review.md),
[derivation/usage](../../GENERAL_CONTACT_NATIVE_CONNECTED_DEFORMATION_DEV.md).

## Remaining limits and next action

TESTED DEVELOPMENT only. Supporting same-family review is not independent
engineering acceptance. Fixed-orientation, zero-spin, straight elastic axial
invariant and short horizon; exact-in-time semidiscrete reference, not continuum
spatial convergence. General bending, finite-angle/nonprincipal deformation,
section breadth, full C7 acceptance and C8 common-stage native/shell impact remain
open. Reuse this evidence; select the next required physical discriminator through
the existing retained owner/controller. Do not create another time-driver stack.
No release, publication, merge or historical-default change.
