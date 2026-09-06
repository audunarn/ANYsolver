# P5 discrete arch crossing and small-mesh refinement — 2026-09-06

Research successor to `cc8744e696f4ab9ed0a8652c5ef94e8f60f0da5e`, tree
`7ddc8ce5472d5598d9389f6a8482828a058fe7e8`. The preceding separate continuum
reference and all accepted/failed earlier evidence remain unchanged. This is
same-author development, not an independently reviewed qualification result.

## Unchanged physical case and algorithms

Use the span-2 parabolic reference y0=0.1*(1-X^2), clamped at both ends, with
concentrated downward crown load. Full 3D nodal DOFs remain in the assembly.
The material basis has its second axis along global z, so the section ordering
is C=diag(1000,400,400,0.02,0.01,0.02). The in-plane bending stiffness matches
the continuum EI=0.01. A large existing yield threshold leaves this particular
comparison elastic; it does not alter or replace the nonlinear section law.

The new helper calls the existing curved geometry builder, mixed stationary
operators, global assembly, objective pseudo-arclength controller and exact
accepted-origin replay validator. Reference comparison calls the separate
continuum BVP at the *actual* crown displacement of each accepted discrete
state. Reference forces are not used to assemble or correct the discrete beam.
The continuum implementation does not import this helper or discrete mechanics.

At most twelve steps of size 0.01 are admitted. Each corrector retains sixteen
updates and 256 mixed evaluations per element. The helper has a 60-second
cooperative deadline checked before/after increments and reference evaluation;
it is not an OS process-tree watchdog. Each global increment is separately
iteration/evaluation bounded. A future resource wave must supply the normal
external process containment rather than misrepresent this cooperative guard.

Failures retain only completed diagnostic records, never a partial result model
or a PASS classification. The reference load must be positive and finite on
this registered branch. No automatic retry, stabilization, tangent shift, mode
deletion, qualification promotion or change of mechanics/tolerances occurs.

## Predictor direction is not the accepted-state tangent

The existing continuation trial stores the direction used to predict from the
old state. It is intentionally retained as the orientation for the next solve.
Reporting its last component as the new-state load slope would place a turning
point one step late.

The comparison therefore recomputes a tangent at the accepted state using its
spatial residual derivative and the existing bordered tangent routine, oriented
consistently with the old predictor. It divides the parameter direction by the
crown-displacement direction to report dP/dd. Both old predictor and new current
parameter directions are retained explicitly. No continuation algorithm itself
is modified by this reporting correction.

Negative eigenvalues of the complete free spatial energy Hessian are reported,
not suppressed. A negative minimum is a numerical local stability diagnostic,
not an exact rank/PSD certificate or a complete mode-classification analysis.

## Observed paths and accuracy status

An initial two-element twelve-step diagnostic completed, crossing a load maximum
and continuing along a descending-load branch. Representative accepted states:

| Step | Crown drop | Load | Minimum free eigenvalue |
|---:|---:|---:|---:|
| 6 | 0.034874677341926424 | 0.03540107823276123 | 0.008411503421661312 |
| 7 | 0.04281041502362582 | 0.03572101898920831 | -0.0034790624101745564 |
| 8 | 0.050723997006543245 | 0.03520528990366921 | -0.020702588380745634 |
| 12 | 0.0818915525945857 | 0.028925908054706254 | -0.055943233087734 |

The sampled two-element maximum is about 24% above the continuum maximum
0.02881081291259526. It is a sampled peak, not a root-located discrete limit
load. All twelve physical and arc residuals passed 1e-11, but convergence does
not make the coarse response accurate.

After coarse correctness tests, four- and eight-element eight-step paths were
run serially as small correctness diagnostics, with the same settings. Each
completed once; no failure retry was needed. End-of-path matched-displacement
comparisons were:

| Elements | Crown drop | Discrete load | Continuum load | Relative load error |
|---:|---:|---:|---:|---:|
| 4 | 0.041373416115468055 | 0.03161819365355845 | 0.028328250356721613 | 0.11613648055945736 |
| 8 | 0.0436478917554617 | 0.028876956202538905 | 0.028041934692863604 | 0.029777599827582657 |

These also were the maximum pointwise load errors over the respective eight
records. The meshes have different arclength-generated crown samples, so these
maxima do not by themselves establish a formal convergence order. The reference
is recomputed at each matching displacement; raw sampled loads at different
displacements are not compared as if they were the same case.

Both meshes crossed from positive to negative current dP/dd and continued on
the descending branch. Their final slopes were -0.10596049030401537 (four) and
-0.13889809765399763 (eight). Final free minimum eigenvalues were approximately
-0.00717184 and -0.00478069. Physical and arc residuals remained below 1e-11;
four-element correctors used at most 60 mixed evaluations, eight-element ones
at most 120. All accepted-origin replays matched exactly and histories remained
elastic.

**Eight elements still fail the 2% response-accuracy criterion** at some sampled
states. The 2.98% maximum is not rounded down, waived or relabeled as qualified.
The paths demonstrate traversal and refinement progress only. Neither a stable
precritical solution nor a negative global eigenvalue alone proves accurate
full spatial buckling behavior or qualifies this element.

The observation records above were captured in completed command output. No
external formal certificate, raw-packet hash or resource receipt is invented
for these ordinary small correctness diagnostics.

## Tests and next bounded gate

Final new suite: **12 passed in 7.51 seconds** (the earlier eleven-test version
passed in 7.08 seconds). It covers the coarse turning-point crossing, explicit
failure of the coarse accuracy criterion, fresh-tangent versus predictor signs,
physical/arc equilibrium, bounds, replay, canonical finite record serialization,
invalid extents, zero deadline before mechanics, injected second-step failure
and invalid-reference rejection without a partial result.

The separate continuum reference regression suite passed **17 tests in 1.21
seconds**. These inventories are separate; timings are not performance gates.

Helper SHA-256:
`B63667ED490C5D650E971DCAB3C0A490725338F8384791A124BD55B8284706E6`.
Test SHA-256:
`94F20208AAD996C9CF0A476024CB6B10204C778B9D8AB83AF96D4C862F1AF1A4`.

Next prepare a separately frozen, resource-approved 16-element refinement using
the existing explicit REFINEMENT16 assembly envelope. Do not silently expand
this helper's two/four/eight-element extent or reuse the prior consumed cyclic
refinement request. Bind the geometry/section/load case, source identities and
fresh output directory; retain process-tree resource limits and no automatic
retry. Include physical recovery/work comparisons as well as load-displacement
accuracy, and keep full spatial stability separate from the symmetric reference.
No 16-element arch run or new resource request was executed in this checkpoint.

The complete goal remains active. General nonlinear sections, broader curved
and slender families, robust extreme local solves, prestressed modal/dynamics,
production integration, independent review and objective beam-shell joints are
not closed here. Only this record, helper and tests are added. Existing src,
B2/B3/Q4/S3 mechanics/defaults, packages and accepted evidence are unchanged.
No push, merge, release or activation. `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
