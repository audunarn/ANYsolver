# Same-body BL5 Mx local transfer at 80 and 160 physical P0 rows

The prior response contrast changed the beam and interface together. This
bounded reconstruction held the **same** 16×8×4 C3D20 shell, 32×8×4 C3D20
beam, shell root, section-dual 10 N·m torque, material laws and 32 physical
beam segments fixed. It reproduced the saved 80- and 160-row work to the
unchanged `1e-8` relative control and passed the physical KKT, weak-work and
wrench checks. The 80 rows are sums of adjacent already-integrated 160 rows;
no quadrature crosses a beam element boundary.

| Measure | 80 aggregated rows | 160 segment rows |
|---|---:|---:|
| Applied work | `0.0010104242171 J` | `0.0010029187834 J` |
| RMS pointwise translational-y gap | `3.332e-9 m` | `1.839e-9 m` |
| RMS pointwise slope-y gap | `4.353e-7` | `1.869e-7` |
| Maximum fine-segment mean slope-y gap | `1.098e-6` | `3.39e-20` |
| Maximum absolute fine-segment constraint work | `2.591e-6 J` | `6.22e-20 J` |
| Beam-side segment Mx range | `−2.279` to `+0.004 N·m` | `−4.863` to `+1.527 N·m` |
| Interior segment-Mx sign changes | `4` | `26` |

Both integrated beam-side interface torques are `−10 N·m` within numerical
roundoff, with opposite shell action. Segmentwise shell/beam wrench balance
is below `2.5e-14` in the stored run; totals reproduce the earlier saved
interface wrenches within `9e-15`. The 80-row fine-segment work cancels in
pairs, so its near-zero *total* weak work conceals local work. The 160-row
space closes segment means, but develops strong alternating torque transfer
over the supported interior. This is a **diagnostic warning**, not proof of
locking or a preferred multiplier space. Pointwise gaps remain nonzero for
both exact weak spaces; neither is a pointwise surface weld.

At this mesh ratio the 80-row supports are one shell-trace length; the
160-row supports are half that length. Section 4.5 of the governing Revision
8 plan starts P0 supports at no less than one local shell-trace length for
`c_lambda=1`. Thus the 160-row case is an intentional *over-resolution
control*, outside that initial candidate rule. Its smoother displacement
response or smaller gap cannot qualify it. The 80-row case follows the
candidate support length here but is **not selected**: its physical local
gap/work, shear and drilling interpretation, seven ratios, growing-space
stability and actual mixed-system behavior still require assessment.

**Next decision:** stop loaded refinement of the 160-row control. Check a
physically matched torque/shear transfer reference, then develop and
independently review a positive-norm/mixed-system contract for the coherent
80-row support rule, including
the known checkerboard and an admissible control. If the 80-row local motion
is prohibited by the declared continuous law at the intended accuracy,
revise its resolution policy or law with a justified complete candidate;
otherwise retain its semantics and advance the registered envelope. Do not
infer acceptance from this one response.

[Raw result](result.json), [runner receipt](receipt.json), exact source,
stdout and stderr are preserved. Process wall was `25.067 s`, sampled peak
process-tree RSS `970.6 MB`, CPU affinity `[0]`, with effective one-thread
Numba/threadpool and JIT-off checks inside the numerical process. No F03
authority, release gate or physical tolerance was changed.
