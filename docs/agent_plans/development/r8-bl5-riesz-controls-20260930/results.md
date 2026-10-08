# Supported positive reference-norm controls — development

Source parent `855610d94e65570d360f6716d2fda447b54bf186`, new private
`scripts/b3_e4_bl5_riesz_controls_dev.py`; no product or consumer changes.
This implements controls for the [mathematical contract](../../B3_GE_E4_PL_M2_TRACE_NORM_CONTRACT_DEV.md),
not F03 execution, candidate stability, physical accuracy or M2 acceptance.

## Decision and method

Do the supported auxiliary forms reproduce independently derived physical
work, or contain boundary/normalization defects? Sparse P1 beam-axis translations
retain four fixed cellconstant directors; only axis translations at the root are
fixed. The coupled form includes section arms and finite-width averaging. Shell
Q1 has three translations and two physical directors, all fixed at x=0 and free
elsewhere. Drilling and the actual indefinite mechanical K are absent.

Control inputs: L=1m, W=.2m, ell=.4m; beam arm z=−.05m and width=.1m;
shell arm z=.0175m. These are not final candidate acceptance choices.
The [independent oracle](independent-analytic-controls.md) derives beam and
shell volume controls. The executed sine manufactured beam field and shell
boundary-line modal solution were independently checked in the
[review](independent-review.md). Line loads have y-dependent representers;
they are not replaced by uniform volume loads.

Before execution the script requires inverse residual and norm/work discrepancy
≤1e−10, finest analytic norm error <1e−3 and error reduction below .35 per
doubling. Pure cell moments are exact to1e−12. These verify the auxiliary
implementation and expected Galerkin convergence; they do not set native beta
floors or mechanical tolerances.

## Executed results

Final [v3 output](v3/result.json) uses16/32/64 beam translation elements with
fixed cell partition, and shell16x4/32x8/64x16. Beam controls: constant/ramped
force, endpoint force, integrated cell moments and eccentric manufactured work.
Shell controls: line force, line director couple, eccentric line work and
y-uniform volume work. Nodal representers and norm/work identity are checked.

| Finest dual-norm relative error | Result |
|---|---:|
| Beam constant / ramped force | 4.42401e−5 / 1.58310e−5 |
| Beam endpoint force | 5.92884e−5 |
| Beam cell moments | 2.22045e−16 |
| Beam coupled manufactured field | 1.19249e−5 |
| Shell line actions | ≤1.14974e−4 |
| Shell volume action | 1.42092e−5 |

All predicted O(h²) error predicates pass. Maximum checked final nodal errors:
beam5.93e−5, shell7.19e−5. Metres/millimetres preserve .202453900292958N²;
coordinate-basis congruence differs by at most6.43e−14. This is a primal
coordinate check, not yet the actual BL5 multiplier-basis/Q map.

A prescribed cellwise P2 density is orthogonal to the coarse P1 fields: assembled
action norm3.95024e−16. Independent enriched reference duals remain positive:
.001520996/.001731995/.001801129N². Thus the reference detects an action
coarse fields miss. A supported constant force is detected; an exact duplicate
action cancels separately. These scalar controls do not identify native gauges.

All three runs pass. V1 had analytical controls; V2 added rescaling/resolution;
V3 added field/norm-work checks. Their frozen scripts, logs and results remain
separate. V3:.4678s, sampled process-tree peak62341120B, ceiling600s/8GiB,
effective BLAS pools1thread. [Identity](v3/identity.json) binds Python3.14.2,
NumPy2.4.6, SciPy1.17.1 and script hash. No product assembly/import is invoked,
so the preceding product wheel is unchanged and was not rebuilt.

## Resulting action and boundaries

Independent review is clear for this bounded slice. Integrate actual physical
BL5 beam/shell work into independent reference inverse actions next. Verify
native retained-variable gauge annihilation, multiplier density/Q pairing and
enrichment accuracy for those actions before candidate spectra. Freeze justified
admissibility/deterioration criteria before the full seven-ratio assessment;
retain separate actual mixed-system kernel, locking and transfer checks.

Unequal cells, every signed Cartesian amplitude, the polynomial/P2 manufactured
variant and generalized frames/reference lifts were not executed. The controls
do not prove convergence for every line action. Native gauges, multiplier work,
beta criteria, full ratios, external accuracy and aggregate gates remain open.
Formal F03 authority is unconsumed. No fourth loaded-mesh refinement or speedup
claim follows. Raw evidence is ordinary development data, not a new formal gate.
