# Supporting source review: B2 physical-end pair

Scope: read-only supporting mechanics review of `C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001`, 2026-10-04. Read new geometry/manager/test files, reused projection/integration/topology functions and conditional core diff. No tests, imports or repository edits performed. Same-family supporting scrutiny, not formal independent engineering acceptance. Canonical policy read: ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1 revision 2026-09-24.2. This checkout has no ECOSYSTEM_GUIDE.md; no policy invented.

## Finding requiring a discriminating regression

**P2: swept admission can approve an intermediate active line-clamp plateau.** Initial source `beam_pair_ends.py:172-203` certifies curve regularity, whole-pair gap and endpoint branches, but does not certify the distributed-line plateau excluded by `:89` / `beam_chain_consistent.py:213-218`. Disposition after delta review: corrected at source level by `admissible_line_projection_path` and manager invocation; execution evidence remains with the lead. The initial source counterexample is retained below.

Counterexample, analytically derived (not executed): R=0.02, gap_tol=1e-5, z=0.019999, a=0.1, L=0.2, epsilon=1e-6. Source endpoints `(x,-a,z),(x,a,z)` move from x=-epsilon to x=+epsilon. Target stays `(0,0,0),(L,0,0)`. Attach an unselected classical beam to the target's first node so it is not a physical end. Source ends and target's remaining genuine end are open throughout; both selected curves stay regular. The complete minimum gap is at least -1e-6, and the initial coarse Lipschitz bound is at least approximately -2e-6 > -gap_tol because relative speed is 2*epsilon. Endpoint certificates therefore allow the path. At path midpoint x=0, source projections are identically target parameter zero and a positive-measure central source interval is active. `_integrate_direction` explicitly rejects this pose. A full-path admission result must retain this rejection, including when endpoint ownership cannot expose it.

## Mechanics checked against equations

No additional implementation defect found in the inspected scope.

- Endpoint energy `E=.5*ke*g^2`, residual `ke*g*Dg` and tangent `ke*(Dg outer Dg+g*D2g)` are consistent (`beam_pair_ends.py:130-139`). The distributed contribution remains half of each directional integral (`:154-155`). These are different declared discrete measures.
- Strict source ownership `d.a<0` plus strict target clamp makes an end/end feature reciprocal. Exactly one full spring is assembled. The dedup key uses side/local endpoint rather than node IDs; for this enforced one-cell-per-side, disjoint-node profile these are one-to-one with material identities, so no present double count or missed collision follows.
- `_projection_work` uses the reduced distance Hessian `Hxx-Hxt*Htx/Htt` (`beam_pair.py:263-287`). Its target-vector derivative and moving target shape produce both-body cross blocks. Source-side exchange changes coefficient ordering correctly.
- Rectangle minimum equations agree with minimizing `|w+s*u-t*v|^2`: `s=(ab*vw-bb*uw)/(aa*bb-ab^2)` and `t=(aa*vw-ab*uw)/(aa*bb-ab^2)`. Complete four edge candidates preserve parallel/collapsed cases; exact rational determinant decisions and outward lower sqrt/float conversion are conservative (`beam_pair_end_geometry.py:47-71`).
- Endpoint Bernstein branch polynomials match the derivation: interior distance numerator `ww*bb-h^2`; interior ownership numerator `(w.a)*bb-h*(v.a)`; parameter-one squared distance `ww-2*h+bb`. Strict positive bb is proved before a whole interval is admitted. Whole-segment coordinate hull and infinite-line distance are valid lower bounds. Samples only reject; subdivision exhaustion fails closed. Active hidden/double transition roots cannot be accepted merely because sampled signs agree.
- All-pairs nodal relative speed bound `max_ij |delta_A_i-delta_B_j|` covers the convex bilinear material-velocity differences, and its sqrt is upper rounded (`beam_pair_ends.py:180-195`).
- Endpoint topology uses all classical material-node incidence, including unselected cells and B3 middle nodes (`beam_end_topology.py:4-15`). Selected shared nodes are rejected by base validation. Restart captures endpoint stiffness, physical-end node lists, law/revision plus inherited settings. Core diff only adds hemisphere dispatch; existing no-cap paths are unchanged.

## Initial coverage gaps and current disposition

Initial bounded development coverage gaps are retained for traceability; the subsequent delta addresses several of them:

1. Body exchange and selected-cell connectivity reversal with nodal permutation of residual/tangent and equal energy.
2. Unselected B3 middle-node attachment removing a selected B2 endpoint; owned active projection to a nonphysical target end must reject; topology-change restart must reject.
3. Actual endpoint-path active projection equality and an active ownership double root at a nonsampled parameter (e.g. 1/3), with open-pose control, finite-budget rejection and no accidental admission from endpoint samples.
4. Restart rejection after a swept-subdivision setting change; the inherited contract contains it, but the current fresh restart test alters only endpoint stiffness.

The existing scalar oracle has independent projection, ownership, activation cuts and quadrature; it checks both end/end and end/interior work. The two coupled direction sizes, symmetry/wrench checks, independently balanced two-bar force/displacement solve and active fresh JSON restart are meaningful source-level checks. This review does not endorse their execution results without the saved run evidence.


## Delta review: exact distributed-line plateau path certificate

Read appended `beam_pair_end_geometry.py:235-269`, manager call `beam_pair_ends.py:205-206`, and added tests through line 283. No tests/imports executed.

The new certificate is sound for affine B2 paths. Let `u` be the source tangent, `v` target tangent, and `w` source-first-node minus target-first-node. Source raw projection is `(h+s*slope)/bb`, with `slope=u.v`, `h=w.v`, `bb=v.v`. A positive-measure clamp plateau requires simultaneous zeros `slope=0` and either `h=0` or `h-bb=0`. Strict Bernstein exclusion of zero in slope, or in both clamp-level polynomials, excludes that possibility throughout an interval. These quantities have degree at most two under affine nodal motion. `min(bb)>0` protects the denominator. For every pair of material coordinates the separation is a convex combination of the four nodal differences; their coordinate Bernstein hull therefore encloses every moving segment-pair separation. Its lower norm bound >=R proves the whole pair open and can safely bypass a plateau. Both source directions are tested; finite unresolved intervals return False, including hidden or double roots. Binary subdivision at finite configured depth is bounded (worst-case <=2^(depth+1)-1 intervals per direction); no unmeasured runtime/scaling claim follows.

New body exchange/connectivity/covariance test and B3 middle-node junction rejection test address initial items 1 and 2 at source-test level. The hidden fractional ownership-root test addresses root rejection, but its current root also has a zero centerline distance; a cleaner test keeps a finite normal to isolate ownership: target `((0,0,-1),(0,0,1))`, c=1/100, source first node `(0,c,-1)` fixed, source end moving from `(-1/3,c,0)` to `(2/3,c,0)`, R=1/50, source physical ends `(1,)`, target ends empty. Target projection stays strictly interior, distance at root is c>0, and ownership is `(t-1/3)^2`. End poses are open and curve remains regular. Lead received this refinement.

The new hidden-line-plateau test directly calls the geometry helper with an open control; manager integration should also be isolated with the unselected-junction counterexample above. Initialize its reference source at x=-.003,z=.019999 (open), then use displaced start/end source x=-epsilon/+epsilon with epsilon=1e-6; whole-gap and endpoint certificates pass, so the new line certificate alone must reject. Lead received this targeted regression. Topology/settings restart and actual exception/cancel reuse checks are being added by the lead and were not yet inspected in this delta.
