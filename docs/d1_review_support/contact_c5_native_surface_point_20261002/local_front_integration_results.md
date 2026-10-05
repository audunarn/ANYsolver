# Local stationary-front integration — development, 2 October 2026

**Mixed-endpoint integration remains unpassed. No increase to support128 or other caps.**

Implemented explicit integrate_event_friction_fronts alongside unchanged open-only and
historical helpers. Only stationary uncertainty strips must be open at captured endpoints;
neighboring closed material retains its endpoint friction force/tangent. Still one segment,
one stationary branch. No native analysis-owner or acceptance admission.

## Derivation and guards

H=-A/B, B angle-independent. A certified simple stationary branch obeys H_t=0, hence
its total angular derivative is -A_angle/B. Bound |A_angle| by padded target cross-product
norm times radius; divide by the padded strict |B| lower bound over its complete branch
bracket. Mid-angle isolated root interval expanded by this angular variation plus the
full declared per-angle uncertainty encloses every skipped stationary strip. Outward
rounding, definition identity, branch matching and full-envelope _minimum checks retained.
Zero stationary branches imply an open panel only when the full captured endpoint rectangle
is open. An initially open panel ending closed must still integrate physical contact.

Owned OpenAI read-only reviewer checked derivation/source. Its zero-branch counterexample
was addressed before testing. Reviewer also accepted eliminating duplicate endpoint interval
cuts: existing captured-pose roots still partition the entire domain, nothing is omitted.
Endpoint uncertainty caps remain. Gauss4/8 is developmental, not a rigorous kink-error bound.

## Runs and principal discrepancy

1. Whole-angle envelope/closed-neighbor geometry and budget check: passed,4.01s pytest.
2. First mixed integration: failed4.22s. Duplicate endpoint root/interval-edge cuts created
   micro-panels with gap~-1.7e-13m; point guard correctly rejected unresolved sign.
3. Sole captured-pose endpoint cuts, retaining stationary strips: failed17.31s pytest,
   13.46s test. Support128 exhausted at panel4,464queries,18fixed-anglefrontqueries.
4. Exact same angular proof reused across axial children: failed18.60s pytest,14.74s test.
   Support128 exhausted at same panel,488queries,21frontqueries. Small extra progress,
   no whole-route speed-up and no integration pass. Previous scaled error37.4572.
5. No-stationary-branch closed material: independent integrated force check passed8.40s
   pytest,2.61s test. Physical stored/dissipated work nonzero; not discarded as empty.

All bounded180s/953MiB,JIT off. Successful and failed logs/resources/runtime/selection
retained in local_front_integration_raw.zip; final development hashes in source JSON.
The unresolved mixed test now requires ANYSOLVER_RUN_UNRESOLVED_MIXED_FRONT=1 for explicit
replay. It is not an ordinary-suite pass or an XFAIL acceptance. Do not rerun unchanged.

## Next decision

The current cap is spent mostly re-enclosing stationary roots for each new quadrature
angle. Existing whole-angle coverage already proves each branch and nonzero B. Next derive
and prepare reusable band-wide coefficient/derivative roundoff bounds for safeguarded root
isolation and coordinate uncertainty at queried angles. Count actual newly computed bounds,
retain cap semantics and root residual/uncertainty gates; do not call uncomputed bounds cached.
Verify against existing slab oracle and analytical stationary roots before repeating the
same mixed case. No affine special case or mesh retuning. If this cannot meet the cap,
classify that result before any further integration retry. Multisegment accounting and
saved coupled secondload/split restart remain open.
