# C6 exact directional touch - source development, 6 October 2026

Status: implemented and focused source-tested; installed V19, full impact,
independent engineering acceptance and release remain OPEN. Parent de32f139
retains the separately verified V18 artifact. Full C0-C9 remains incomplete.

## Mechanical scope

Explicit `allow_directional_beam_s3_dev=True` selects
`ELASTIC_B2_B3_AFFINE_S3_DIRECTIONAL_LINE_HERMITE_DEV_V1` and V19 restart.
At exactly zero gap on a complete represented span, solve algebraic velocity
with the directional derivative of the existing distributed penalty work:
`Z.T (K_struct*v + epsilon*L*integral B.T*min(B*v,0))=0`.
This term is a force RATE, not damping or an additional mechanical force.
Physical velocity/inertia, affine S3 work maps and numerical null-acceleration
secants remain unchanged. Bounds concern the declared endpoint Hermite path;
they do not certify a nonlinear algebraic lift or finite-rotation mechanics.

Exact rational evaluation of stored binary geometry distinguishes full touch
from unresolved floating nearzero. The oriented numerator must be positive,
constant along the line, and squared equal radius squared times normal squared.
Moving-normal and eccentric target variations are included. Quadratic rate
roots use bounded exact-sign brackets; degree-four moments assemble directional
work/Hessian with root-strip/conversion bounds. Floating contact H is removed
once before its directional replacement. Isolated exact minimum touch has zero
distributed measure; a stationary maximum with other active regions is excluded.

## Actual evidence and impact analysis

Raw evidence: `C:/ANYworkspaceWork/contact_c6_beam_s3_20261006`.

- `directional_source_consolidated`: 1 PASS,4.460931000067s,182018048B.
  Independent Decimal quadratic oracle gives0.10753992725048668; residual0;
  component force/H error bounds3.61217e-15/4.08785e-15. Actual public B3/S3
  initial full touch produces3states,0.5m active length, final gap-1.070243um
  against10um, and exact accepted split/checkpoint equality. Non-exact geometry,
  isolated-touch classification and incompatible V18/V19 restart are checked.
- Supporting source review found misplaced control validation that would break
  ordinary load-history construction, and insufficient Euclidean transfer of a
  componentwise directional error box. Both are repaired. The latter now uses
  an outward bound from all null-basis column L1 norms in acceptance/backtracking.
- `directional_source_review_repair`: 1 PASS,3.950055100024s,180772864B;
  legacy construction, exact-bool/conflict refusal and rank-two error transfer.
  The consolidated test was NOT rerun after repair. Its original source hashes
  differ from the final repaired hashes; only the affected selector ran again.

Effective runtime: JIT disabled,Numba1,native pools1,actual source import paths
and empty runtime/import error lists. Inputs, commands, resource records and
logs are retained per job. Final held hashes: `directional_final_source_hashes.json`.
Original candidate hashes/results and the repair delta remain separate. Same-family
review is supporting scrutiny, not independent engineering acceptance.

## Remaining obligations and execution boundary

The flat virgin assembled fixture may have zero B*Z. Its public run cannot prove
general rotational coupling; the nontrivial oracle proves only its local rate
equation. A production coupling case, final installed artifact, impact/temporal/
energy checks and independent acceptance remain required. V18 installed results
retain their exact original scope and cannot qualify the new V19 profile.

All29terminal C6 resource records total178.223450299818/180s, leaving
1.776549700182s. No additional build/install or campaign was attempted.
Requested additional180s remains UNANSWERED. No physics, scientific tolerance,
historical result, consumed authority, public default or release boundary changed.
