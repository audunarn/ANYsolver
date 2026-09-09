# Sixteen-macro arch capacity and accuracy closeout

Implementation `8bfd385d7f9a1548ec2649ccd6da087783df452b`, tree
`396fa2e7afd97b102806cfa98c3e6de89f6f3a5a`, from `121d196b578ef949410abdaf9e83cabea0e0744c`.

Outcome: `DEVELOPMENT_SIXTEEN_MACRO_ACCURACY_MEASURED_ONLY`.
All three sampled load errors are below 2%. This does not establish the full
beam qualification, an actual native arc-length limit-point crossing, or
spatial stability. The overall goal remains active.

## Separate inventories

| Inventory | Passed tests | Scientific JSON files | Supervisor seconds |
| --- | ---: | ---: | ---: |
| Sixteen-macro rehearsal | 1 | 6 | 300.713 |
| Frozen cycle A | 1 | 6 | 313.915 |
| Frozen cycle B | 1 | 6 | 315.719 |

All six scientific files are byte-identical across all three invocations.
Each inventory includes all three equilibria, complete checkpoint roundtrip,
zero plastic history, native physical recovery, and direct BVP9 comparison
at 128 stations per target. The prior profile and field-map inventories are
inherited, not rerun or recounted here.

## Measured errors

| Crown drop | Eight-macro load error | Sixteen-macro load error | Resultant-compliance norm error |
| --- | ---: | ---: | ---: |
| .0009924835187201996 | .0007825801147887113 | .00019890156706048323 | .002412166826489594 |
| .002196594350540417 | .006708921466316298 | .0017432639879781942 | .0029785403335160277 |
| .004368321784681136 | .02441550400234216 | .0062351096570898434 | .006835601045471236 |

Errors are fractions, not percentages. Worst load error is approximately
0.624%, versus 2.442% at eight macros. No thresholds were rounded or relaxed.
Maximum constitutive consistency error is 5.551115123125783e-17 under the
unchanged 1e-11 check. Position maxima are 2.4325007655793054e-06,
6.282977357809083e-06, and 2.7737932244115138e-05; frame component maxima
are .0001500079456233927, .00037456528948313916 and .0012255101307284827.
Full saved-field norms and load errors were recomputed by the read-only audit,
without rerunning the native solve or continuum BVP.

The authentic checkpoint is 2372889 bytes, above the old 2097152-byte default
and below the explicitly selected 8-MiB profile. SHA-256:
`C65730E97EC1097832C95DA21312EC67162A8B0B2422274C701BE4131B1EFCA0`.
It was authenticated, decoded, and re-encoded exactly with complete history.
The old default profile remains unchanged and does not implicitly admit it.

## Process bounds and preservation

All children finished normally with zero active descendants. Longest child:
315.7192403999943 seconds. Peak process-tree memory: 340508672 bytes.
Observed frozen-wave span: 315.71924 seconds. One numerical thread per child,
24-GiB memory, 600-second wall and 120-second CPU-inactivity limits, at most
three workers, and 1800-second wave bound were retained. No worker failed
or was automatically retried.

A pre-freeze staged diff check flagged one trailing blank line in this plan's
companion implementation document. That whitespace alone was corrected;
the test was unchanged, and initial/frozen snapshots preserve the difference.

Archive: `C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-uniform-arch-sixteen-8bfd385-20260908`.

48 data files (9475150 bytes) plus the manifest preserve raw runs, exact
commands, source/input snapshots, supervisor observations, audit and a proposed
next diagnostic. All byte counts and SHA-256 hashes were verified.
Manifest: 7092 bytes, SHA-256
`70678CD6261CC90F29A03BF77E1E55C01F7DA2D4272315C8A2BE67091FA4C1DB`.
Audit SHA-256: `BA1ECFB7666AD0553EEBB9B01A20EF9BA95BD0CB65532EF3A6665EDCE1F4CC93`.

Only the verified staging duplicate may be removed. Original run directories
and the external archive remain. The previous failed two-macro arc smoke stays
failed and preserved; it was not retried or reclassified.

Exactly two research paths were added at freeze. All source mechanics,
reference equations, section properties, loads, frames, quadrature, tolerances,
recovery, public routing, defaults, packages and existing evidence are unchanged.
No push, merge, release or independent authorship review is claimed.
Independent review remains PENDING.

## Next gate and full scope

The three current targets lie before the continuum's observed load peak.
Preregister a separate bounded native diagnostic across the peak and descending
branch, comparing loads and recovered fields to the same continuum authority.
Do not silently extend an authenticated old programme/checkpoint. Preserve any
failure, with no automatic retry or tolerance/resource-limit relaxation.
Then establish objective arc step adaptation and an actual crossing.

Practical scale/history efficiency, broader loads/supports/material/state parity,
slenderness, physical mass/modal/prestress/buckling, independent review,
installed-wheel/public integration and objective beam-shell connections remain.
This accuracy result does not narrow or complete the full objective.
