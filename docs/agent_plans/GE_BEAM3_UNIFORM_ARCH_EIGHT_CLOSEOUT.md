# Eight-macro uniform arch closeout

Implementation: `d4f277984c91dad5635e7edc97127485bfea4df8`.
Tree: `932df52158b2b0b7c8ec9bd5f21f3e5980870655`.
Base: `26aa0f5ba09b57615430675a10d82eb2057f1240`.

Outcome: `DEVELOPMENT_EIGHT_MACRO_ACCURACY_MEASURED_ONLY`.
Engineering accuracy remains open; the full beam and objective connection goal
is active. No native limit-point crossing or production qualification is claimed.

## Separate inventories

| Inventory | Passed tests | Scientific JSON files | Supervisor seconds |
| --- | ---: | ---: | ---: |
| Eight-macro rehearsal | 1 | 6 | 151.163 |
| Frozen cycle A | 1 | 6 | 156.563 |
| Frozen cycle B | 1 | 6 | 157.559 |

All three complete scientific file sets are byte-identical. Each test includes
three accepted targets, exact full checkpoint roundtrip, elastic-history checks,
native recovery, and direct BVP9 comparison at 64 stations per target.
The earlier 11-test sampling/field-map inventory is inherited, not recounted.
No failed invocation or correction occurred in this diagnostic.

## Resolution evidence

| Crown drop | Four-macro load error | Eight-macro load error | Eight-macro resultant-compliance norm error |
| --- | ---: | ---: | ---: |
| .0009924835187201996 | .0029447622797034168 | .0007825801147887113 | .004882103609243714 |
| .002196594350540417 | .02307843104662788 | .006708921466316298 | .008523198442169146 |
| .004368321784681136 | .08744905893537802 | .02441550400234216 | .025724304887123947 |

The native densities are .019817326901545355, .03813168142848457 and
.05284568076765553. The third load error is still above 2%; the threshold
is not rounded or relaxed. Position maximum errors are 9.333669594161625e-06,
2.459544940155295e-05 and .00010772317613552684. Frame component maximum
errors are .0002896429499456843, .0007301386836626005 and
.0023599659658350494. Constitutive consistency errors are at most
5.551115123125783e-17 under the unchanged 1e-11 check.

These observations support continued spatial refinement. They do not establish
full energy-norm convergence, slenderness qualification, branch uniqueness,
spatial stability or a resolved limit point. The earlier failed two-macro arc
smoke remains failed; it was not restarted or rerun. Displacement control here
uses the same three accepted drops, not a changed mechanical formulation.

## Bounds and preservation

The exact checkpoint is 1181530 bytes, SHA-256
`D7AE95932C57DB4938376A292103298245E7C9761B84312128B9155D916C3EB6`.
A simple doubled-size estimate for sixteen macros is 2363060 bytes, above
the current 2097152-byte cap. This is an estimate, not a claim that a
sixteen-macro checkpoint was constructed or tested. No sixteen-macro run began.

Each child used one numerical thread, a 24-GiB Windows Job tree, 600-second
wall and 120-second CPU-inactivity limit. Longest child: 157.55904950000695
seconds. Maximum recorded tree memory including rehearsal: 326066176 bytes.
Observed frozen-wave span: 157.625586 seconds. All children terminated with
zero active descendants. No automatic retry occurred.

Archive:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-uniform-arch-eight-d4f2779-20260908`.

40 data files (4815783 bytes) plus the manifest preserve the three commands,
raw outputs, source/input snapshots, supervisor observations, audit and a
proposed next-history scope. All byte counts and SHA-256 hashes were verified.
Only the verified staging duplicate may be removed; original runs remain.

Manifest: 5951 bytes, SHA-256
`56E44216B79E13F294B3BB83B6730076F6DC4E98F453CE728F8D068E7AC2CB91`.
Audit SHA-256:
`CB892F47ABA017386B0E1FA18A8BE10F16AC1401E69659F52AC2081DF2E541F0`.

The audit independently recomputes saved load and field error metrics,
checkpoint links, baseline identity, inventories and replica equality.
It does not run the native solver or continuum BVP and is not an independent
authorship review. Independent review remains PENDING.

Exactly two research paths were added at the freeze. All existing source,
mechanics, reference equations, section properties, quadrature, tolerances,
public routes, defaults, packages and historical evidence are unchanged.
No push, merge or release occurs.

## Next implementation gate

Develop an explicit, bounded native-generalized history profile before longer
or sixteen-element runs. The archived next-history-scope.md is a proposal,
not implemented or independently accepted functionality. It identifies the
combined, translation and arc checkpoint envelopes as the affected path.

Preserve default 2-MiB canonical bytes and the shared historical parser.
A proposed 8-MiB opt-in envelope must use distinct schemas and bind the explicit
caller-selected profile in the programme and nested records. Retain complete
genesis/history/rotation/load/equilibrium replay, per-state restrictions,
model/count limits and the current 60-second validation/600-second child bounds.
No global mutable limits, implicit large-payload acceptance or omitted history.

Test default compatibility, profile isolation/mutation, canonical/hash/size/depth
guards, full state roundtrip and accepted-prefix safety before a new sixteen-
macro smoke. Then finish accuracy convergence and objective arc cutback/step
control with actual limit-point/postbuckling evidence. Larger histories may also
require safe incremental validation; do not silently relax process safeguards.

Physical mass/modal/prestress/buckling, broader load/support/material/state
parity, practical scalability, slenderness, independent review, installed-
package/public integration and objective beam-shell connections remain required.
The objective has not been narrowed to this arch comparison.
