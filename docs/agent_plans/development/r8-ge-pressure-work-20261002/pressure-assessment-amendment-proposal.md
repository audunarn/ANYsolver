# Proposed pressure-only equilibrium amendment — awaiting user decision

This is a prospective proposal, not adopted policy. Product acceptance remains
unchanged. The Revision 8 goal requires a decision before replacing a frozen
scientific assessment; numerical tolerances alone do not define an equivalent
assessment when the normalization changes.

## Concrete finding

The new mixed and all-S3 director-pressure solves fail the current assessment at
their first 0.1 increment. Best observed global work ratios were 1.9252e-14 and
1.0142e-14, with constraint gaps below 2.65e-23. Individual induced pressure
components around 3e-8 N were compared with residuals around 1e-14 N, yielding
component ratios above 1e-8. Both owners correctly retained generation zero.
The earlier mixed follower case has the same type of unresolved normalization.

## Proposed opt-in policy

Add an explicitly selected pressure-only assessment, with a distinct persisted
identity, provisionally `STIFFENED_SHELL_PRESSURE_VECTOR_EQUILIBRIUM_V1_DEV`.
Keep existing defaults, native reference-dead meanings and checkpoints unchanged.

For each shell node, separately assess the norm of its free translational force
residual relative to its free applied pressure-force vector, and the norm of its
free rotational residual relative to its free applied pressure-moment vector.
Use nodal moments, not moments transported to a global origin. Omit inactive
zero-applied groups from this local ratio; they remain in the global residual.
Use the explicit shell/free-DOF map, never group retained variables as node rows.

Require the maximum of these active vector ratios and the unchanged global
scaled work ratio to be <=1e-8. Keep compatibility <=1e-9 and all other physical,
material, finite-state and lifecycle checks. Historical nodal, body, distributed
and non-pressure routes retain their existing assessment. Pressure cannot be
combined with independent nodal/programme loads in the current admitted route.

Apply the selected policy consistently in solve acceptance, trial comparisons,
restart validation and chart rebasing. Bind it to request/checkpoint identity;
old strict-policy results must never silently restore under the new assessment.

## Changed guarantee — explicit tradeoff

This preserves vector-relative accuracy, **not every Cartesian component's
relative accuracy**. A residual (1e-10,0,0) N with applied (1e-10,0,1) N passes:
a much smaller orthogonal contribution at the same node can be entirely missed.
Overlapping pressure patches can create such contributions. A small load on a
separate node remains protected by its own vector check. Exactly cancelled
groups retain global coverage only; near-cancelled groups remain strict.

This is therefore an amendment, not a claim that earlier failed runs actually
passed. It does not qualify the pressure surface, shell model or whole solver.

## Review and counterfactual evidence

Independent Read review judged the proposal defensible prospectively with these
limits. The private script `pressure_assessment_proposal.py` overrides assessment
only within its diagnostic process; product code does not import it.

It checks axis covariance for fully free vectors, consistent force-unit scaling,
partial coordinate selection, separate tiny-load rejection, moment/unloaded/
retained-row residual injection, component zero crossings, and explicitly
demonstrates shared-node masking and exact-cancellation limitations. Constraint
acceptance is not overridden. These controls do not constitute the eventual
complete policy validation suite.

Under the private proposed assessment, mixed director pressure, all-S3 director
pressure and the previously failing mixed follower pressure all complete
0.1/0.2/0.3, accepted-prefix cancellation, identical restart/continuation, rebasing
and physical balance checks. They are counterfactual development results,
**not accepted results under the current contract**. v1 failed because its script
tried to restore into a used owner; corrected v2 uses a fresh owner and completes
all three routes. Original failures remain retained.

Recommendation: approve this opt-in prospective policy, then implement its
versioned identity and full affected source/installed checks. No default change,
retroactive acceptance, qualification claim, merge or publication is included.
