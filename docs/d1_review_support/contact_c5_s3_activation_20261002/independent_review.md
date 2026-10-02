# Independent design/source scrutiny and disposition

Mistral Read design6turn and source7turn reviews; no edits/tests/Git changes or
nested workers. Full logs/source snapshots retained. Reviews are independent
input, not C5 acceptance; installed/source checks were run by the lead.

Design review identified missing first-touch history, event/anchor derivative,
stage geometry and event-facet ownership as principal risks. The implemented
option deliberately admits only checked constant-normal affine-FE paths. Within
that domain gaps are affine and hidden entry/exit or double closing roots cannot
occur; moving-normal/cubic paths are rejected rather than sampled or assumed safe.
The review's statement that step-size dependence proves nonconvergence is not
adopted: different subdivisions alone do not establish that. The retained exact
slider demonstrates loss at coarse endpoint initialization and the new rule's
first-order endpoint/chord work convergence explicitly.

Source review supports:

- Complete quadratic facet/convexity/source-coverage checks, using the existing
  `_extrema` implementation. Convexity also relies on positive incident facets
  and fixed conforming topology; boundary turns alone would be insufficient.
- Material stage-anchor convection; event fraction and material coordinates
  recomputed by probes on a fixed event facet; returned-anchor physical work.
- Independent root/reaction/stick tangent/storage checks and deterministic state.

Findings led to changes before the final installed artifact:

1. Normal-parallelism originally scaled by the largest coefficient. It now uses
   the sum of transverse coefficient norms divided by the minimum represented
   facet area, preventing large step coefficients from loosening the bound.
2. Restart recontact text now distinguishes endpoint from first-touch stage
   projection, and explicitly binds the affine-FE/constant-normal path identity.
3. Base and derivative-probe rim contact both reject. Event-fraction and material
   coordinate bounds are separate explicit controls.

Other findings/disposition:

- The stage element-membership guard also validates malformed private probe
  input; valid base records naturally pass it. It is retained.
- Coverage admission and strict barycentric location can disagree close to
  numerical boundaries; that produces explicit rejection, not silent contact loss.
- Direct prepare_commit pressure is recomputed by normal.law.evaluate at the
  same candidate. This exact owner admits finite penalty only; augmented normal
  owners reject. Multipliers are fixed/read-only, not stale augmented history.
- Stage checks still repeat in each derivative evaluation. The measured full
  installed selection fits its declared caps; no speedup is asserted.

The coupled static driver and new per-point rules remain developmental outside
the stated fixtures. No independent acceptance or general swept guarantee follows.
