# Uniform arch development diagnostic closeout

Research implementation: `6ea1c654ebed0c372a54cf7fe6e49a489cc654f0`.
Tree: `a1e5464adb91cbce5d2babda0e373b608e86795d`.
Base: `c34baeea2ab155b071abe90c2963a31856763f7d`.

Outcome: `DEVELOPMENT_NATIVE_SMOKE_FAILED_LINE_SEARCH`.
The full beam/joint goal remains active. No production qualification,
independent review, native limit-point crossing, full spatial stability,
default change or release is claimed.

## Separate inventories

| Inventory | Result | Tests | Supervisor seconds |
| --- | --- | ---: | ---: |
| Continuum equations and BVP7/BVP9 resolution | Passed | 9 | 3.614 |
| Early continuum turning-region samples | Passed | 1 | 4.016 |
| Native four-step two-macro smoke | Failed at step four | 1 | 60.551 |
| Initial prefix CLI | Import failure before mechanics | Not a test suite | 1.210 |
| Corrected prefix CLI | Accepted prefix replayed | Not a test suite | 5.820 |

The native test retains its real failure assertion; it has not been changed
to a passing test or rerun with smaller steps. The first three steps were
committed and their exact checkpoint remains available. The failure is
`RuntimeError: native arc line search exhausted`, not a timeout, memory
breach, material-state failure or demonstrated formulation NO-GO.

The first read-only prefix command selected the installed package, which does
not contain the private source module. It failed before native mechanics.
Its source and logs are preserved. Only explicit source-path setup and an
import-origin check were added; a separately identified corrected reader
replayed the existing checkpoint without advancing the failed path.

## Scientific findings

The separate continuum implementation uses the Simo-Reissner balances with
uniform spatial downward load per reference arclength, not a crown point load.
The background is [Bali et al., DOI 10.1002/nme.6994](https://pmc.ncbi.nlm.nih.gov/articles/PMC9543773/),
equations 6--11 and 15--17. The half-arch elimination and variational sensitivity
are a same-author specialization, not independent review. The reference
imports only NumPy/SciPy and standard-library modules, not ANYsolver mechanics.

The parabola is y=.1(1-X^2), span 2; EA=1000, GA=400 and planar EI=.01.
The continuum is normalized by EA without changing the equations or units
of its reported load density. Both ends are clamped and a symmetric half-arch
BVP solves horizontal reaction and distributed load density for prescribed
crown drop. It verifies off-grid equations, analytic sensitivity, boundaries,
positive stretch and distributed-load virtual work.

Maximum BVP7/BVP9 normalized load-density/slope discrepancy:
1.5134542613592927e-7 (registered reference-resolution bound 1e-5).
The early reference slope changes from positive at drop .006 to negative at
.008. Densities there are .05408713292651055 and .054656377258078495.
This brackets an observed symmetric turning region; it is not an interval
certificate, a uniqueness proof, or exclusion of earlier spatial bifurcation.
The computed zero-drop density 2.6098975295848295e-11 is numerical residual,
not claimed to be exactly zero.

The two-macro native smoke uses the identical parabola and in-plane section,
uniform load, full end clamps and all interior spatial DOFs free. It uses
the unchanged generalized native element, four-point cell integration and
elastic histories. Four registered arc steps are .2, with length scale .1
and load-parameter scale .1. No coefficient or tolerance was tuned.

| Accepted step | Crown drop | Native density | Reference density | Relative load error |
| --- | ---: | ---: | ---: | ---: |
| 1 | .0009924835187201996 | .01999206146363932 | .019801830382851316 | .00960674226119762 |
| 2 | .002196594350540417 | .03998249409628208 | .03787756382743095 | .055571954902937426 |
| 3 | .004368321784681136 | .059961557254118565 | .05158617822669609 | .16235703661970802 |

All saved histories are elastic. Maximum observed reflection/out-of-plane
coordinate residual is 1.1600963245594897e-16. The native load slopes at the
three accepted states are 18.786089350518836, 14.114106937242703 and
4.975297499811057; the reference slopes at the same drops are
18.096300759508054, 11.578946447574294 and 2.6691850923902254.
No native accepted state has demonstrated a negative load slope.

The state decoder and predictor replay both accept the preserved prefix.
This is deterministic native implementation replay, not independent mechanics.
The discrepancy is present before the failed step and demands mesh/field
convergence study. A two-element model is too coarse to infer a formulation
defect or to claim the required 2% engineering accuracy. Step-four failure
likewise does not by itself establish the cause of a native turning point.

## Preservation and extent

Checkpoint: 298555 bytes, SHA-256
`A73AF73CC0433E72850A5B8BD2B17624AEF8AAEAB09C247C8FC5D42B2E0740C0`.

Archive:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-uniform-arch-6ea1c65-20260908`.

38 data files (615423 bytes) plus the manifest preserve all five invocations,
raw outputs, failed logs, XML, source snapshots, commands, observed supervisor
bounds and the read-only audit. The original native tool observation was
truncated; complete stdout remains in the archive. No result was reconstructed
from missing output. All copied byte counts and SHA-256 hashes were verified.

Manifest: 5349 bytes, SHA-256
`807CF58F329E321EB85A855D9194CDC66F0837A15D07E21A3DE28FA0AE63D385`.
Audit SHA-256:
`D127DAE0FD96D1EB5F9ABB9D755070B686EA2AACBC1F31EE8C70AE1C0D27EB93`.

The source freeze adds five research/test/documentation paths only. There is
no change under src/, no shared solver or beam/shell mechanics change, no
public API/default/version change, and no historical evidence modification.
All five processes terminated within their 600-second/24-GiB limits and
reported zero child descendants. No automatic retry or formal A/B mechanics
cycle was launched after the failed smoke. The only removable data is the
hash-verified staging duplicate; original runs and archive remain intact.

## Next action and remaining goal

Prepare a distinct four-macro displacement-controlled diagnostic at exactly
the three accepted crown drops above. Use the unchanged native translation
programme and uniform load, keeping geometry, section, quadrature and
tolerances fixed. This separates spatial-discretization error from arc-step
selection. Compare loads and fields with independently reconstructed continuum
values, not only summary errors. Rehearse one bounded child before expansion.

If refinement improves the engineering error, preregister bounded algorithmic
arc cutback/step adaptation that preserves accepted-prefix state and predictor
orientation. This is a solver-control successor, not permission to modify
mechanics or retry the consumed smoke. Preserve every failed attempt.

Actual native limit-point/postbuckling traversal, practical-mesh convergence,
broader loads/supports/materials, physical mass, modal/prestress/buckling,
slenderness, independent review, package/public integration, and objective
beam-shell joints remain required. No progress here changes that full scope.
