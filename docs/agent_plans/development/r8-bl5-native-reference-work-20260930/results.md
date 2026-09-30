# Native BL5 work in the positive reference norm — development

Source parent7987074b. New private script
`scripts/b3_e4_bl5_reference_actions_dev.py`; no product/API edits.
One8x2 Q4 shell,16 native halfcells and P0 span2, unchanged fixed root supports.
The question: does independently integrated physical work descend through the
proposed kinematic quotient and use the same density/basis as native C?

## Method and evidence

The [independent derivation](independent-work-derivation.md) fixes force/couple
signs, frames and cell moments. Lambda=Q mu with Q=diag(1,1,1,ell,ell), ell=.4m.
Director densities have units N, translation densities N/m. Reference loads
integrate piecewise constant physical densities across the union of multiplier
support and auxiliary grid boundaries. They are not native Gauss-point atoms.
Beam translations are continuous; retained rotations remain cellconstant and
free at the root. Shell fields are translations and tangential physical spins
(equivalent to director variations through the fixed orthogonal cross-normal map).
Drilling and native nodal beam rotations/resultants are omitted from the norm,
and remain in the actual mechanical K/KKT.

[Independent review](independent-review.md) is clear for this bounded slice.
V3 verifies every one of40 density basis columns including supported rows:
independent physical covectors match−C-transpose exactly. Seven uniform-force,
director, signed-mixed and arm-cancellation actions agree on active fields to
6.94e−18. Q and reciprocal row-basis transformations preserve virtual work.
All222 omitted kinematic-coordinate columns of C are exactly zero. These
facts establish this reference-work quotient, not mechanical gauge removal.
All three retained cell rotations stay positive in the norm, including normal
spin even where the centerline law sees no work from it.

## Auxiliary enrichment

Fixed native model and rotation partition; independently enriched auxiliary
shell/beam translations at2/4/8. Beam norm orders144/240/432; shell five-field
orders400/1440/5440. Inverse residuals≤3.44e−13 against1e−10. The two domain
dual energies add, with no cross-domain term; all seven duals increase on these
nested spaces. Beam norm uses its previously declared .1m width average;
shell width=.2m, zero native lift and constant reference frames/arms.

| Final relative dual increment | Result |
|---|---:|
| Uniform forces | 0.03430%–0.03439% |
| Director actions | 0.02525%–0.02532% |
| Mixed density | 0.21055% |
| Force-arm cancellation | 0.03464% |

These are successive increments, not certified reference errors. Seven
positive actions do not prove positivity or accuracy for the complete
multiplier quotient. In particular the mixed action's reference accuracy is
still open. Neither a beta nor an acceptance floor has been calculated.

## Runs, failures and resulting decision

[V3 raw output](v3/result.json), [execution](v3/execution.json),
[identity](v3/identity.json) and [actual imports](v3/imports.json) retain source
and installed-site bindings:387 unchanged product modules,207 onsite imports
from existing wheel5079b270…. No rebuild was needed. Effective BLAS1thread,
JIT disabled; supervision2.4238s/154509312B against600s/8GiB limits.
Final frozen helpers/fixtures are in `final-inputs/`; run with that scripts
package and fixtures on PYTHONPATH after the declared installed site.

V1 failed import closure before model construction: missing copied helper
scripts. Its exit1, log, frozen script and identity remain preserved. V2 passed
seven work actions; V3 adds complete basis parity without changing those
dual results. Later executions do not expand or relabel earlier inventories.
Raw data is ordinary development evidence, not a helper qualification package.

Retain the current physical map and quotient. Next establish a defensible
reference-error/control and numerical stability criterion contract before
candidate spectra, then assess the registered full ratios and actual mixed
system. Reuse these checks within their exact flat/zero-lift/support scope.
Other charts, support/frame mappings, curved members and complete physical
accuracy remain open. No automatic mechanical refinement, native beta,
uniform-stability, F03 execution or M2/G0B acceptance follows.

## Criterion argument and owner decision

The [independent argument](independent-criterion-argument.md) supplies a bounded
mean-preserving scalar projection for aligned supports containing at least two
primal intervals, and an exact one-interval deteriorating control. Its full
product-domain analytical floor still needs a supported shell bulk-H1 line-work
projection/lifting bound. A beam-only dual-dominance shortcut is invalid at
increasing frequency. The note's explicit sine example is an interior-centerline
reference; our boundary-line fixture instead has ratio W alpha coth(W alpha).
Both exhibit that frequency obstruction; they are distinct physical traces.

Root checked the scalar identities/constants and coupled norm-equivalence
argument. They do not establish a new full-domain acceptance criterion.
The note's requirement for an analytical full-product inequality is sufficient
for its proof route, not an additional programme gate: R8 §4.5 explicitly
permits numerical evidence over the registered domain without a universal
h-uniform proof or certified infinite refinement tail. Preserve that boundary.

Decision: pursue that permitted finite-domain route, not an unbounded lifting
proof. Next implement the independently derived shell modal line-source dual
with an explicit series-tail bound for piecewise constant actions. Use it to
check reference accuracy and independent admissible/deficient macroelement
controls, then justify/freeze criteria before native spectra. The reference
bound distinguishes inadequate auxiliary resolution from actual work-space
loss. No numerical floor is supplied by the current evidence.
