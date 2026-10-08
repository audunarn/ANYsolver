# Native pair event-control development — 5 October 2026

Baseline: `5a56024d`, isolated `codex/contact-main-reconcile-20261001`.
This is development evidence, not native engineering acceptance.

## Decision and observed obstruction

The user-interrupted explicit k4000 N/m2 case was resumed with fresh owner;
all 527 installed Python files and historical pending inputs matched. It timed
out at 120.101516 s / 199888896 B. No accepted prefix was persisted. Earlier
k100 single/staged failures remain unchanged.

A ten-contact trace (21.103116 s / 200474624 B) deliberately stopped with no
accepted target. The first free Newton step produced ownership rejection,
then gaps -1.784 mm and -392 um before an open +304 um pose was accepted.
Residual decreased .0025 to .0021875 N before another overshoot sequence.
Thus the stronger line law cannot help before activation. This does not prove
that nonlinear equilibrium exists or that ownership has no further obstruction.

Opt-in `gap_step_control` now proposes a safeguarded shorter fraction from
certified origin/trial gaps. Every proposed pose still passes complete contact,
endpoint gap, swept path and residual merit gates. The finite backtrack budget,
all 84 retained coordinates and physical material transactions are unchanged.
The default dyadic route and default restart identity remain unchanged; enabled
algorithm identity rejects incompatible continuation.

The source V1 candidate reached active gap -25 um and lowered residual to
.00177873 N. It then timed out at 120.164395 s / 201527296 B while doing roughly
40 full contact evaluations for swept checks needing only a conservative gap.
No complete solve or accepted prefix is claimed. V2 therefore separates swept
geometry from force/tangent integration under the same opt-in algorithm. Actual
candidate/commit evaluations retain full mechanical admission.

## Checks and independent input

- Combined distributed/tip force and endpoint spring reference work controls:
  2 pass, 1.173404 s / 101650432 B. These verify the independent linear
  continuous reference, not nonlinear-native mechanics.
- Affine event proposal/restart binding, independent rank-one retained solve,
  and default generalized open split restart: 3 pass, 4.984049 s / 190652416 B.
- Supporting same-family read review found no blocking change to default
  fractions, identity, gap/swept/merit checks or commit behavior. It identified
  ownership-certificate limits near shared junctions. This is not the required
  different-family scientific acceptance.

Raw evidence: `C:/ANYworkspaceWork/contact_native_fibre_s3_20261005/candidate15/`
under `installed_mechanically_refined_pair_resumed`,
`source_tip_combined_endpoint_control`, `installed_refined_law_path_discriminator`,
`source_gap_event_controls` and `source_gap_event_coupled`.

## Next decision

Verify the geometry-only conservative gap query against independent geometry,
full mechanical evaluation and internal-coordinate motion, including cancellation.
Then run one V2 integrated candidate within the unchanged 120s/953MiB limits.
A further failure is retained and classified; no unchanged full retries, resource
increases, physical law changes, weakened criteria or main integration are implied.
Shared integration/testing infrastructure stays separately owned.

## Final V2 integrated outcome

Candidate16 wheel SHA256:
`a096989ad6c5d9a633443e2d4c183e95814af5590815da01898398c5ab1604d4`.
All527 Python files match source. Installed28 focused controls pass in11.162513s
with193982464B peak; imports/runtime report no errors, JIT disabled/pools1.
Threshold-qualified swept query validates all cells, then uses the existing
complete-source chord certificate only when it proves the requested minimum;
otherwise every union scan runs. Saved active query:3.894698s full mechanical
versus0.017452s geometry; one-pose observation, not whole-route speed claim.

The k4000 integrated solver completes target1 in the51.787574s/200830976B run.
Pytest then fails on the test harness's nonexistent accepted.origins field;
this raw failure remains. The repaired test derives the committed physical origin
from the preceding checkpoint. Its saved-state verification passes6.050572s/
188911616B without replaying the solve: exact checkpoint restart,30 yielded
stations, positive material dissipation, gap-19.609961um, normalized force balance
8.67e-17 and zero moment-balance error. This establishes a completed development
solve plus subsequently verified accepted state, not a retroactive test pass.

A prospective k8000 comparison at unchanged mechanics/gates completes and passes
in81.973390s/200704000B, including independent material returns and exact restart.
Relative changes: force0.109499%, moment0.027066%, beamA tip0.080005%, beamB tip
0.062473% (all below2%); penetration13.784964um versus19.609961um. This is fixed-
discretization normal-enforcement sensitivity, not spatial convergence or full
native admission. The historical k100/k4000-default failures are not regraded.

Failed development checks retained: an exploratory active-curved comparison
hits existing full-mechanical ownership nonadmission; a first chord discriminator
incorrectly orders two independently conservative lower bounds. The repaired
chord test uses independent finite-segment distance, retaining the same1e-13
numerical margin. No physical/scientific criterion changed.

[Exact summary and raw paths](fibre_pair_event_control_summary.json).
Next: reuse these accepted states for native spatial/geometry/material coverage;
never repeat either coupled solve just for reporting. Native automatic/friction,
finite-velocity dynamics, coupled impact and application completion remain open.

## Reproduce the bounded development example

Use the repository example with the candidate16 installed package on PYTHONPATH:

```python
from examples.general_contact_native_retained_whole_pair import analysis
owner = analysis(
    physical_fibres=True, plastic_fibres=True,
    separation=0.101, force=-0.05, targets=(0.05,),
    line_stiffness_n_per_m2=4000.0, gap_tolerance_m=5e-5,
    gap_step_control=True,
)
result = owner.solve()
assert result.status == "completed", result.failure
```

This is a private development workflow. Start a fresh owner immediately before
solving; its construction-to-expiry120s clock includes idle time. Reuse the saved
checkpoint/evidence for review instead of replaying consumed comparison runs.
