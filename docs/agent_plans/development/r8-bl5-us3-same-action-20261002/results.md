# Same-action independent shell response — 2 October 2026

One fixed US3 plate-only reference now executes all three finest native shell
actions. This removes beam and connection feedback and establishes a material
shell-response contribution to the current discrepancy. It does not qualify the
coupled connection, select a multiplier space, prove drilling causation or close
M2/F03. No additional mesh or constitutive/stabilization parameter was introduced.

## Model and result

The protected n64 endpoint inputs supply all6630 shell covectors
`f_s=L_s-C_s.T lambda` and native reference-linear states. The existing1x.2m
plate has1105 unchanged midsurface nodes, thickness.035m, E210GPa, nu.3 and the
same102 root support coordinates. Each64x16 Q4 cell is split into two consistently
oriented US3 triangles:2048 elements. All nodal forces and moments are applied
directly; no beam arm or shell-top offset is added again. Three unit-duration
linear steps replace concentrated loads with `OP=NEW`.

| Action | Native shell work,J | US3 shell work,J | US3/native change | DAT/arithmetical work bound,J |
|---|---:|---:|---:|---:|
| Fy | 2.623821391244348e-4 | 2.595645309605785e-4 | -1.0738567% | 7.304e-11 |
| Mx | 8.796896805056850e-6 | 8.775100784605857e-6 | -0.2477694% | 9.931e-13 |
| Mz | 6.563687143583568e-6 | 6.487750398144638e-6 | -1.1569221% | 5.518e-12 |

Translation relative L2 differences are.986%,.233%,.967%; tangential-director
differences.176%,.295%,.082%. Normal-spin differences4.22%,49.3%,15.2% are
reported separately: normal-spin loading and its direct work are zero. They do
not identify drilling as the cause. Full arrays, component work, applied wrench
about the midsurface origin and uncertainty estimates remain in the raw results.

These differences exceed DAT uncertainty. They are fixed-mesh response results,
not converged cross-solver error norms or a failed/passed1% acceptance gate.
The native full free-equilibrium ratios recomputed from saved operators/actions
are1.83444e-12,2.86670e-9,9.51604e-9; the last remains near the unchanged1e-8 cap.
All existing saved scientific predicates and zero ground coordinates were checked
before the reference run. Raw files marked RETAINED_BEFORE_PREDICATES were not
treated as passed merely because their hashes matched.

## Execution, repairs and independent review

Prepared v1 was not executed. Review corrected DAT conversion/outward uncertainty,
native predecessor checks, nonfinite derived results and STA interpretation.
V2 exited201 while reading STEP3: CalculiX `cloads.f` reads a20-character F20.0
magnitude; a22-character token truncated to an invalid exponent. Two emitted
steps are partial failed evidence and are not scored. Earlier long fixed decimal
tokens could silently truncate, so neither partial step is used as a comparison.

V3 repairs serialization only. Every magnitude fits20characters; decoded deck
actions are retained separately. Maximum relative input difference1.49944e-14.
Direct serialization-pairing estimates are below1e-21J and are separate from DAT
rounding. They are not forward displacement/compliance error certificates.
Mesh, physical law, supports, actions and scientific thresholds remain unchanged.

V3 completes once: three DAT blocks at total times1/2/3, three STA single-increment
steps, clean stdout/stderr, reported numerical CPU count1. Runtime.433032s,
sampled process-tree RSS25,153,536bytes;600s/1GiB supervision, one numerical
thread. These observations are not performance claims or equilibrium certificates
from STA. Pure parser controls reject duplicate nodes, missing components,
nonfinite tokens, incomplete steps and wrong times; signed/extreme load formatting
and expected STEP/INCREMENT headings are exercised without a numerical rerun.

Pinned CalculiX2.23 executable SHA256:
`27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f`.
Reused supervisor SHA256:
`5837645ddf40e591451cbd58f8975ce8f026cb908e750044b848c8c04dcae5d4`.
V3 deck SHA256:`a69a2868bd7d8dce17ee0820717072dcd0c027d06ff66836956b18c652180bfc`.
Prepared and executed runner snapshots are distinct and both retained; the latter
adds honest pairing-estimate labels and pre-run execution identity, without changing
the deck or numerical predicates. No solver product changed; wheelfb12ac66 remains
the391-module tested product. Formal foreign F03 script hashc908b1f3...9481 is unchanged.

Independent Read reviewer `/root/e02_rigid_tip_runner` inspected preparation,
archived CalculiX primary source, repairs and final raw results. No unresolved
correctness finding affects the scoped replay. It is separate OpenAI review, not
different-family acceptance. CalculiX's parser failure is retained and does not
establish a mechanics defect. No formal F03 authority was consumed.

## Combined decision and next action

The completed native endpoint series shows no gross solve/work collapse, while
the independent same-action replay now shows about1.1% differences under Fy/Mz.
Consequently, further multiplier tuning or an automatic fourth reference mesh
cannot be justified as the sole remedy. Subsequent source review resolves the
decomposition seam: flat Q4 physical core has zero normal-spin rows/columns.
PL is k_d T^T G T with T representing theta_z+.5(u_y-v_x); it includes translation
and translation-spin coupling. Hourglass supplies spin-spin stiffness only.
`compute_stiffness_components()` exposes core,PL,hourglass,numerical,total.
Native S3 likewise separates physical membrane/bending/shear and its nodal
spin-minus-displacement-curl PL term. This source finding is not an external
operator-equivalence claim.

Thus the earlier combined PL+hourglass derivative scales the complete flat-Q4
drilling-related numerical sector while preserving the physical core. It is not
bare spin stiffness, a finite-removal prediction or drilling-independence proof.
Do not repeat it. The next missing observable is the assembled supported
completion action after spin relaxation, not another local decomposition API.
With N=PL+HG and a justified physical/spin partition, this is
`N_pp-N_pd solve(N_dd,N_dp)`. Use sparse action/solves and actual supports; never
form a global dense inverse or infer SPD for the native retained mixed system.

The next bounded discriminator evaluates that contribution on the existing
saved physical state at unchanged coefficients. Verify frames, partition and
spin equilibrium first. A material completion contribution directs drilling
independence scrutiny; a small contribution directs attention to the physical
operator/reference approximation, without establishing unique causality.
Continue ready material/consumer work independently. Physical coupled torque/shear
transfer, reference convergence, growing interface spaces, ratios, all mandatory
final gates and release remain open.

[Raw inventory](raw-v1.json) binds [39 files](raw-v1.zip), including unexecuted
preparations, failed and successful commands, decks, decoded actions, native
checks, actual DAT/STA/logs, identities, runner snapshots and parser controls.
Archive SHA256:`8a5aeb708de15726fa5679c89088596696cfe7334db37d2968d7888089859782`,
1,033,159bytes. Original roots are Temp/r8-bl5-us3-same-action-v1/v2/v3.
Protected native inputs remain in the earlier endpoint archive138017d6...3b2.
