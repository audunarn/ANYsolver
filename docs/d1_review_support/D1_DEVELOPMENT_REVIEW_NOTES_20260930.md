# D1 development review notes - 30 September 2026

These are early development assessments, not independent capability acceptance.
No frozen or consumed evidence authority is renewed.

## Preparation and instantaneous gap cost slice

Read-only reviewer: `/root/candidate_budget`; integrating author: `/root`.
The private preparation sink is fresh for each synchronous manager construction,
populated only after valid admission, then consumed immediately. No global model
cache or pose reuse. Existing work maps, polarity, reference geometry, resource,
initial penetration and D1 coverage checks remain.

Projected-prism pruning is valid for instantaneous overlap-local bounds. Physical
Q4 points project into the convex hull of projected corners along the kernel's
corner-plane normal. S3 points are convex combinations of target corners. The
full target-depth prism contains every matching projection, even at non-nodal
normal separation. Varying source normals affect gap after overlap eligibility.
Empty candidates mean no represented instantaneous surface overlap, not a swept
crossing guarantee. Swept code is unchanged.

The reviewer identified an early-return defect for singleton side selections:
remote degenerate geometry could be pruned without validation. The shared face
checker now validates before returning; the explicit singleton control passes.
[Seven focused checks](d1_preparation_reuse_checks_v2_20260930.log). Initial new
fixture failures from omitted derivative tolerances are retained in v1.

[Same-pose profile](d1_radial_preparation_profile_v4_20260930.json): residual is
exactly equal to v2, gap-gradient relative discrepancy1.14e-16, count1772.
The first-order zero-weight prototype remains available but disabled by default
after its profiled cost exceeded batched Jet2. Prototype derivative/activation
checks remain development evidence.

[Complete cycle comparison](d1_preparation_cycle_compare_v8_20260930.json): all
eight saved displacements, pressures, source/target wrenches, gaps and generalized
reactions are exactly equal. One elapsed comparison234.35 to216.71s and memory
375.71 to416.01MB does not establish a reliable twofold route or memory improvement.

## Spatial force-bin and reaction-work recovery

Read-only reviewer: `/root/radial_observables`. Source-bin helper author:
`/root/candidate_budget`; wrench helper/runner author: `/root`.

Within fixed XY, zero-director, complete-coverage and whole-face source bins,
the actual conversion `(ns.n0)*nt_z/(nt.n0)`, projected/reference measure,
two-sided slope allowance and pair work `p.dW-(p*g).dS` are consistent with the
nodal-force formulation. Numerical quadrature errors are estimates, not interval
certificates. A production-bin claim requires measured production comparison,
per-bin uncertainty/conversion budget and summed-bin parity with independently
reassembled source Fz. `not_checked` remains missing evidence. No target-bin or
moment claim follows from this source-bin helper.

The reviewer identified cancellation in combined source-plus-target wrench checks.
The corrected helper projects the joint constrained reaction once, then partitions
nodal work by disjoint covering body selections. Each body's physical certificate
wrench is transported to the same origin; balance, conversion and structural
defects each enter the retained1e-6 predicates. The equal/opposite defect control
now detects the error that the global sum hides. [Ten focused checks](d1_guided_wrench_body_checks_v3_20260930.log).
Follow-up read-only review found no remaining mathematical/scope blocker in these
new body checks for the saved zero-rotation radial fixture. Actual saved-pose
measurements and final independent assessment remain required.

## Prospective radial assessment review

Read-only reviewer: `/root/radial_observables`; no new numerical runs. The
fixed guided fixture and its declared scales are usable, but emitted diagnostics
alone cannot establish its spatial predicates. The final assessment must require
complete finite evidence, measured physical source bins, per-bin uncertainty and
conversion budgets, same-state source force parity, source displacement, moment
and resultant-position predicates, independent gap and per-step complementarity.
Contact action/reaction needs its own force and moment predicates; recovered
support reactions can otherwise compensate a nonzero contact net wrench.

The physical position may be explicitly defined as the moment-equivalent wrench
point at z=0, x=Ox-My/Fz and y=Oy+Mx/Fz, above the registered force threshold.
Retain the residual vertical couple and full moment check; this is not a pressure
centroid. The matched saved linear QP may assess observed final-state nonlinear
discrepancy after checking identical fixture data and independently reassembling
its equilibrium/complementarity. Include measured discrepancy and reference,
quadrature and conversion uncertainty in the unchanged 0.2% budget. This finite
comparison is not a uniform nonlinear error bound or a general shell admission.
No claim-bearing source/specification freeze has occurred.

## Conservative affine swept search

Kernel author: /root/candidate_budget; owner integration: /root; independent read-only reviewer: /root/radial_observables. The Bernstein enclosure uses the parent corner projection normal over the complete affine corner path, with outward coordinate boxes and endpoint/child error enclosures. All original parent and physical-corner angular/polarity guards remain over every target; union coverage and global geometry checks remain outside pruning. Unresolved bounds fall back to exhaustive enumeration; invalid geometry rejects the proposed path. No endpoint-only search certificate is used.

Independent scrutiny found no concrete blocker in this restricted development path. Twenty-one distinct kernel checks, fourteen owner/rounding checks and a separate old-checkpoint rejection check pass. Contact restart now binds ffine_union_outward_swept_search_v2 on overlap_local_dev. This is development review, not capability acceptance.

The identical saved admissible path measured154.13 to52.66s, with swept calls41,472 to968 and their kernel cost109.00 to7.39s. Endpoint gap and coverage costs are unchanged. [Before](d1_radial_saved_swept_profile_v6_20260930.json), [after](d1_radial_saved_swept_profile_v7_20260930.json). Full coupled v8 subsequently completed2/2 in891.87s/570.46MB; this establishes bounded executability, not a twofold whole-route speed claim.

## Closed reference-uncertainty and assessment findings

Saved-reference helper author: /root/candidate_budget; read-only reviewer:
/root/radial_observables. Reference v2 incorrectly used a componentwise contraction
bound without component coupling and omitted coefficient-error times solution-error
from inactive-gap propagation. Preserve v2 and aggregate v11 as unsuitable for
uncertainty claims. V3 uses `b + eta*max(b)/(1-eta)` and
`(abs(G)+gap_error)@u_error`. The original49-mode branch, observable values and
positive sign margins remain; checked contraction is3.29058e-10. Force uncertainty
is1.87829e-7N. Three affected focused checks pass. Review found no remaining
concrete blocker in those changed equations for this fixed fixture; this is not a
uniform nonlinear-model error bound or capability acceptance.

The aggregate assessor now rejects NaN/infinite physical gaps before penetration
conversion, wrong force/moment scales or origin, and scalar moment broadcasting.
Four gap and four scale/shape controls pass. Physical-bin assessment includes the
independent exact-disk arithmetic estimate. Data-only v12 passes34 predicates;
independently accepted and released remain false.

## Closed actual-path admission finding

Author: /root; read-only reviewer: /root/radial_observables. The previous physical
prescribed-normal guard considered model constraints but omitted solve-path
controls. A rank-aware SVD now projects the physical normal covector onto the
actual free span after `controls@T`; both monolithic and nested path branches
supply those rows. Source-only prescription rejects; target-only, dependent,
coupled and zero-row controls preserve the appropriate source freedom. Seven
focused checks pass. D1 restart binds `model_and_path_constraints_v2`, so old
D1 checkpoints intentionally reject under this candidate. Review found no
concrete blocker in these changed lines. Contact equations, geometry derivatives,
structural solve coordinates, public signatures and no-contact defaults are
unchanged; the radial fixture's active interior modes remain physically free.
The retained measured fields remain development evidence under their recorded
source identities. Final qualification requires a prospective source/specification
freeze and actual current-artifact execution; no historical run is regraded.
