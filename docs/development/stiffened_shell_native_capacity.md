# Native BL5 stiffened-strip capacity candidate

Status: **development screen executed; full seed failed; accepted prefix verified**.
Candidate `4c5867ce` passed 17 focused source checks; two full numerical tests were
deselected. One installed screen accepted factors 0.1, 0.25 and 0.5, then rejected
0.75 at the Newton iteration limit. No arc step, turning response or capacity was
obtained. Its generation-3 checkpoint passed separate installed restore, physical
recovery, corruption-refusal and pre-cancellation checks. This document adds no
execution authority and renews no historical allowance. The existing native
point turning/refinement campaign remains closed. This is a new native line source
candidate, not a repetition or relabelling of that campaign. F03 and protected
evidence are unchanged. Trace/release semantics remain experimental.

The source is `examples/stiffened_shell_native_capacity.py`; its main entry refuses
execution. After separately granted bounded numerical authority, an investigator
may call `workflow`. Tests in `tests/test_stiffened_shell_native_capacity.py` are
include two full numerical tests that remain **UNRUN**. The focused tests ran
against the frozen candidate. They distinguish a working
restart route from a diagnostic failure; a test that observes failure cannot
establish numerical acceptance.

## Proposed physical experiment

The flat strip is 2 m long, 0.2 m wide and 0.002 m thick. Sixteen Q4 cells form an
8 by 2 mesh, with 27 shell nodes and zero stress-free geometric imperfection. Two
straight stiffeners run along its long edges. Each rectangular section is 0.006 m
wide and 0.04 m high; its axis is 0.021 m above the shell midsurface. Four native
three-node B3 members per stiffener give nine physical beam nodes and eight native
half-cells per line. The shell trace matches those eight segments. All native
internal coordinates are retained; this is neither a point chain nor a rigid
attachment surrogate. Only the three shell nodes at x=0 are fixed, in all six
coordinates. No beam support or extra drill gauge is inserted.

The established five-row BL5 law uses `continuous_p1_coarse` and the current native
material policy, with objective Q4 pullback. It binds the **shell top**, so the
reference beam-frame arm is −0.020 m in z. The neutral-axis/load-centroid distance
uses the different midsurface-to-axis distance of +0.021 m. No bond channels,
floors, stabilizers, constitutive equations, defaults or scientific tolerances
change. Construction admits multiple lines and both generalized and physical-fibre
members when at least one fibre member is present; that source predicate is not
evidence that this two-line construction passes numerical rank/factorization.

The initial mixed inventory alternates generalized and physical biaxial fibre
sections on each stiffener. Four equal fibres reproduce EA, EIy and EIz of the
rectangle; the existing background supplies shear and torsion. Shear area is
explicitly 5A/6 and J=h b³/3 is a thin-rectangle approximation. E=210 GPa, ν=0.3.
The fibre threshold is 10²⁰ Pa. The generalized comparator has an **independent**
threshold of 10¹⁶ N, with force-like hardening 10⁹ N and resultant metric
M=diag(1,1,1,1/h²,1/h²,1/h²), h=0.04 m. Consequently the existing quadratic
q=√(sᵀMs)=√(|F|²+|moment|²/h²) has force units. This explicit high-threshold
resultant convention is an initial-elastic comparator, not physical J2 equivalence
or a declaration of identical generalized/fibre yielding. These thresholds
propose initially elastic behavior under the material-capable native route; they
do not prove it. Shell response is elastic. This does **not** meet a
simultaneous shell/fibre/generalized plasticity obligation; that later obligation
needs a separately adopted material case and evidence. Beam centerline inertia
metadata is ρ diag(A,A,A,Iy+Iz,Iy,Iz), ρ=7850 kg/m³. No spectral claim is made.

## Load law and its discriminating question

Dead axial compression is shared by shell and stiffeners in proportion to their
EA. Skin end-face nodal shares integrate the width with weights (1/4,1/2,1/4).
The combined load passes through the reference composite centroid. Applied loads
remain fixed spatial translations, including their genuine eccentric common-origin
moment; they are not follower loads or a zero-moment axis-only load.

Let EA=EA_s+2EA_b, z_c=2EA_b e/EA. The explanatory clamped-free estimate uses

```text
EI_eff = EI_s + 2(EI_b + EA_b e²) − (2EA_b e)² / EA
P_E = π² EI_eff / (4 L²).
```

This assumes a composite Euler reduction that the 3D Q4/native BL5 discretization
need not satisfy. In particular its released spin and weak trace constraints,
skin deformation and native shear/torsion can change the critical load. P_E is
neither an oracle nor a predicted panel capacity.

The illustrative frozen load proposal is P=1.1 P_E, Q=0.02 P_E. A single ordinary
force seed ramps `F_seed=F_compression+F_positive_probe` at factors
(0.1,0.25,0.5,0.75,1). Its displaced equilibrium is a **loaded reference**, not a
stress-free geometric imperfection. Native material BL5 refuses staged/external/
adaptive arc seeds, so no staged programme is used. The arc load direction is the
opposite probe and its actual law is

```text
F(α) = F_seed − α F_positive_probe
     = F_compression + (1−α) F_positive_probe.
```

For an ideal above-critical bending reduction, U≈a A²+b A⁴−QcA with a<0, b>0
has a selected positive branch that can fold while Q decreases. This motivates
tip-z orientation −1. It does not prove an above-critical stable seed, positive
quartic coefficient, a fold, or branch correctness in the full supported 3D
system. Seed failure is a useful terminal discriminator; no automatic retry,
radius/mesh/parameter sweep or modelling tune is permitted by this candidate.

## Observation and bounded workflow

The explicit `NativeDirectorChordMetric` uses half normalized skin-area nodal
shares and half normalized total beam-arclength nodal shares, with L=2 m. All
weights are positive and follow public preflight order; shell position/director
and beam full-frame contributions retain the existing metric law. The metric's
length-unit covariance is tested separately from the solver's SI contract.

The proposed workflow preflights, records every accepted seed and arc state,
then follows at most 24 requested arc steps (2..64 admitted) at radius 0.01 with
the controller's existing defaults. Its own bounded cutbacks remain visible.
The first arc prefix is checkpointed/restored into a fresh public owner; the next
continuation compares checkpoint bytes **and all public recovery data**. Owners
close on every exit. Actual checkpoint bytes, size and SHA256 accompany the
report inventory; callers must preserve those bytes as binary artifacts under
their separately granted output authority before serializing the remaining
report. No output files are created by the workflow itself.

An optional `on_observation` callback receives an independently owned, complete
observation after **every accepted seed and arc step**. A future authorized
supervisor can stream these witnesses to a unique JSONL file before a process-tree
timeout. Mutation of the delivered copy cannot corrupt the retained report;
writer errors propagate. The separate `on_accepted` callback remains arc-only for
cancellation steering. This example adds no numerical harness or solver API.

Each observation retains complete public shell/beam/cell/chart/material state,
constraint multipliers, full actual positions, physical applied force rows,
support reactions and BL5 station work. Ordinary force recovery currently leaves
`applied_dead_load=None`; its exact load vector is reconstructed from the owned
seed actions and accepted public `load_factor`, with that provenance explicit.
Arc recovery supplies its actual public dead-load vector, checked exactly against
the affine law. Ordinary force recovery also omits explicit shell chart/frame
metadata: its unre-based public rotation coordinates are mapped through the
existing exponential convention with implicit identity anchors. These derived
poses are separately labelled; the raw result fields remain unchanged, including
their `None` values. Arc results supply actual public frames/charts. A scalar
tip-z or amplitude is always accompanied by this state.

Common-origin root reaction moments are aggregated only after verifying that the
fully fixed root chart is zero and its anchors are identity. General shell
rotational covectors are never treated as spatial moments. Actual load positions
and the root positions supply the lever arms. The report exposes the global
wrench residual without inventing an acceptance tolerance. External work uses
trapezoidal endpoint quadrature; it is not exact path-integrated dissipation or
an energy acceptance criterion. BL5 station gradient/gap/multiplier records are
retained without inferring six-channel welding or relabelled nodal moments.

When the declared seed commits its completed factor-1 state, its observation gains
separate affine-origin diagnosis metadata α=0; raw public `amplitude=None` and
`load_factor=1` remain unchanged. This permits the full seed plus first two arc
states to bracket a direction change (for example 0, 0.1, 0.05). Earlier partial
seed factors cannot serve as α=0 because their compressive load also changes.
The tag is attached before the retained and streamed observation copies split,
so both inventories identify the same first-step turning bracket. After the seed
call returns, the workflow validates that existing tag. The committed full seed
remains an authoritative affine origin if a subsequent observation writer fails;
the writer error still propagates. This diagnosis proves no physical stability.

Every observation reports definition-ordered physical fibre accumulation and the
actual generalized high/low accumulated histories, plus exact nonzero update
flags. Any observed accumulated history or active update invalidates an elastic
fold interpretation. A nonelastic branch also makes that screen ineligible. No
tolerance, rounding floor or high-threshold assumption hides an update; full
material records remain attached. Passing this screen proves neither stability
nor capacity and does not replace independent elastic-branch acceptance.

Amplitude increment sign reversals produce only three-generation **unvalidated
turning candidates**. No scalar maximum proves instability, branch correctness,
capacity, mesh convergence or a physical limit point. A bounded path may report
no turning. Only typed finite-increment/arc-selection failure and cooperative
cancellation become terminal diagnostic reports with attempts and the real
committed prefix. Programming/admission/restart/ownership errors propagate.
The cancellation test mutates the callback copy and checks fresh restore of the
actual checkpoint when an arc endpoint exists. These full arc tests remain unrun.

The integration owner adopts this physical load/support proposal only as the
bounded development discriminator. The single approved screen did not obtain a
full seed. Whether a stable buckled seed exists and independent physical acceptance
remain open. The failure does not establish physical instability or a law defect.
No release, capacity or plasticity criterion is adopted from unobserved values.

## Source review disposition

Independent OpenAI review and root inspection corrected shell-top arm geometry,
ordinary-force load/chart reconstruction, typed failure boundaries, dimensional
generalized yield data and the omitted first turning bracket. The final streamed
affine-origin binding was inspected by root after the review's delivery caveat.
Material update flags preserve exact nonzero history. No blocking source finding
remains in the inspected slice. This is not different-family scientific acceptance.
The source review did not supply numerical acceptance. The subsequently executed
development results are recorded below; no execution allowance was transferred
from the preceding director-metric verification.

## Executed bounded development result — 6 October 2026

Evidence: `.qualification/b3-ge-e4-pl/r8-native-capacity-dev-20261006-v1/`.
The unchanged 430-module solver package reused wheel SHA-256 `6464174eb675c4eafd72f01a8ac707bb44d39946c5a7919126e316bc148a63c7`.
Effective CPU affinity was [0], numerical pools and Numba used one thread, JIT
was disabled, and the process-tree memory ceiling was 2 GiB. Runtime/import
bindings and exact process-wall receipts were retained.

The seed failed at factor 0.75 from 0.5: 12 Newton iterations, 73 evaluations,
12 linear solves and 48 rejected trials. The final rejected equilibrium ratio
was 0.2774246521471741 and constraint residual 1.467923660754961e-7. Its
three accepted predecessors satisfy the frozen equilibrium, gap and global
force/moment checks. No accepted material history/update was recorded.

Checkpoint generation 3 has 27,627 bytes and SHA-256
`4e7adf0619e8708102e564949922d0ab73fcc41fc75ddd5699b5f62ea64925ec`.
Restore reproduced bytes and physical recovery at the declared development
tolerances. Reconstruction iteration count and raw chart-field availability are
reported separately; actual physical charts are compared. Corruption was tested
on a fresh owner, followed by valid restore; cancellation preceded any new trial.
The failed physical load route was not retried.

Runner review identified an unreached defect in v1's later arc corruption check
and missing terminal audits on exceptional probe return. The separate v2
prefix-only runner repairs these. V1 returned its typed seed failure normally,
so its terminal runtime/import audits exist. A hard timeout would retain public
streamed states but would not prove a restartable prefix without checkpoint bytes.

The fresh 600-second allowance used 257.2597296 seconds, leaving 342.7402704
seconds within its original scope. It does not authorize another physical screen,
parameter sweep, F03, body retry, closed campaign or release. The next development
decision is the continuation route, not automatic force-control tuning. A
proportional-load arc candidate starting from the verified accepted prefix could
avoid requiring an unproved postbuckled force seed; it needs its own input contract
and permitted execution before any numerical claim. Full qualification remains open.
