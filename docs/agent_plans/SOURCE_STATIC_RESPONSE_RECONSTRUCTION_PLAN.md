# Source-based static response reconstruction — adopted M8 baseline

Approved by the user on 2026-10-08. This document records the governing decisions;
the living progress/evidence ledger is PREPARED_STATIC_IMPLEMENTATION_TASK.md.

## Objective and scope

Provide opt-in response reconstruction for 10,000 arbitrarily varying linear
static samples: whole-model physical stress/resultant/reaction envelopes and
associated components, plus selected histories. Source coefficients may vary
nonlinearly or discontinuously. Structural geometry, stiffness, constraints,
activity, mass and recovery definition remain fixed. Preserve the existing direct
stream and prepared evaluator, default backends/formulations and all old evidence.
First scope is structural ANYsolver/ANYfem; hydrodynamic transfer imports, dynamics,
automatic compression, new backends and publication are deferred.

## Mechanics and APIs

For full loads F=F0+P*c and u=T*q+up, prepare A=T.T*K*T,
b0=T.T*(F0-K*up), B=T.T*P. Solve A*q0=b0 and A*X=B through existing
scaled backend infrastructure. For admitted affine output recover y=y0+Y*c,
including direct load contributions where the canonical formulation has them.
Prescribed/initial offsets appear once. Prefer homogeneous increments over
subtracting large baseline-containing outputs. No global inverse. Retain full
force columns for Ku-F reactions, including support/slave/master-equivalent
separation. Recompute nonlinear measures from physical component fields.

Free-free uses the same augmented [A,Z;Z.T,0], gauge and multiplier response for
all columns. Algebraic columns may be unbalanced; every physical combination
retains current per-body compatibility and explicit imbalance policy. No artificial
supports or automatic inertia relief.

Add prepare_static_response_evaluator, corresponding ANYfem
prepare_linear_static_response_evaluator and PatternCase(case_id,coefficients,
time=None), preserving StaticCase. Dense/named sparse coefficients are owned
numeric packets; sparse execution touches only active columns. Existing prepared
snapshot/factor/config/cancellation/progress/cleanup services remain owners.
An optional keyword-only canonical_load_case preserves original-time source input
for safe fallback without changing the three positional PatternCase arguments.

## Sampled-periodic adapter

The frozen representative_barge2 fixture SHA256 is
0f64d97108bb958f5b16eaee4a603d368b690b3846843208288edc067b911ce5.
It has 600 samples, step 0.1 s, nominal period 6 s, external pressure ramp,
clipped rho*g*max(0,draft+amp*sin(omega*t-kw*x)-z) and independent connection
moment; no gravity. Full-grid library requires60 pressure phases+moment. Only
phase and moment coefficients are active at a sample. Preserve clipping and
canonical mapping; don't double hydrostatic pressure or divide a zero-ramp case.

ANYfem owns source interpretation and periodic admission through reviewed safe
expressions/declared period+grid+origin. No barge-name specialcase, interpolation,
nearest-phase snapping or subset-row modulo. Source metadata/actual timestamps
identify phases. Unknown/off-grid/changing-shape sources remain direct. Stored
omega and sin argument arithmetic do not establish bit-identical recurrence.
Retain original-time direct packets; source discrepancy must be certified or use
canonical fallback. Broader irregular-sea capability is not inferred from periodic
success. Six force resultants cannot define distributed hydrodynamic pressures.

## Certificates and envelope contract

First route reconstructs full F,q,lambda and evaluates existing backward error
(limit1e-10), compatibility, gauge and actual requested diagnostics per case.
Conditional cheap certificate may use e0=b0-A*q0,E=B-A*X and e(c)=e0+E*c,
but must bound preparation/combination/source/reduction errors, A*delta_q and
checker rounding. R_upper / D_lower <=1e-10 is required; denominator upper
bounds are unsafe. Inconclusive bounds trigger full-state/direct checks. No bound
is enabled without independent derivation review. Actual and bounded diagnostics
have distinct labels.

Canonical governing IDs remain mandatory. Backward error or empirical stress
tolerance is not a safe contender-exclusion bound. Replay every unresolved case,
potentially all cases. Retain original source, operator/factor, recovery and gauge
until completion. No predicted-winner-only replay. Strict earliest exact ties,
signed abs maxima and governing associated fields. No artificial tensor assembled
from independent extrema. Publish only certified transactional block updates;
cancel/failure/early close preserves previous summary incomplete.

## Resources, verification and acceptance

Array storage, bounded element/case tiles and default32case blocks; fixed-width
coefficients do not inherit direct variable-packet one-case restriction. Include
all library/certificate/factor/source/transaction/history workspace in memory
policy. Refuse if onecase cannot fit. No lease crosses iterator/provider/yield.
Use existing pip-delivered numerical stack; no new mandatory native dependency.

Deliver core, periodic vertical slice, then conditional measured optimization.
Use existing scientific criteria unchanged. Cover affine/MPC offsets, reactions,
unbalanced columns/balanced totals/disconnected bodies, sparse equivalence,
cancellation/overflow, false-pass certificates, phase indexing and floating-time
recurrence, clipping/inside-ramp refusals, ties/counterexamples, mutation/lifetimes,
source errors, close/transactionality and bounded retention. Independent review
covers mechanics, authority, certificate and envelope exclusion.

M8 benchmark ceiling600 cumulative process-wall seconds includes prep/warmups,
profiles/fails/fallback. Old ledgers closed. Record CPU/process telemetry. Charge
all phases required for target history, not a misleading subset library. Compare
strongest verified exact direct baseline with same loads/output/runtime settings,
serial alternating matched runs and distinct coefficient holdout. Candidate10k
only if estimated affordable; projections labelled, no automatic long campaign.
Promotion:2x complete-workload speed OR50% lower processRSS with<=5% slowdown,
unchanged scientific accuracy/output scope; supported/free-free adjudicated
separately. Otherwise NO_GO/INCONCLUSIVE. No release/merge follows from screening.
