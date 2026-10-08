# V7 saved weak nodal-port diagnostic

The user authorized the prepared V7 check and future necessary plan actions in
the current conversation on 8 October 2026. One numerical child ran from the
saved V5 resolved-beam displacement and V6 face result; it performed **zero new
equilibrium solves**, no external run and no formal F03 execution. The V7
one-use registration is consumed. The first attempt to launch the runner with
the workstation default Python failed before `main()` because that interpreter
lacked `psutil`; [its preserved note](v7-launcher-failure-20261008.md) records
that environment failure. The explicit registered-runtime invocation then
exited 0 after `2.1464037999976426 s` process wall, with a sampled peak tree
RSS of `161181696 B`, CPU0, one thread and JIT disabled.

The original C3D20 `B^T sigma` element actions reconstruct the saved full
physical residual within `3.415419611e-12 N`. The projected saved load is
reconstructed from the original four P0 weak intervals and independent end
traction within `5.551115123e-17 N`; the volume-action equilibrium residual
including the saved gauge is `3.546888861e-12 N`. The gauge's maximum nodal
component is `3.011719253e-13 N` and remains reported separately.

At `x=0.5 m`, each side's **source-partitioned cut nodal port** is the volume
internal action minus that side's physical load. Its left/right y-force is
`+5.59377556436748 / -5.59377556437416 N`. The left/right section moments
about `(0.5, 0, 0.04) m` are approximately
`(+0.123123784342395, 0, -0.402617092485958)` and
`(-0.123123784342079, 0, +0.402617092485962) N m`.
The summed cut-port y-force is `-6.683542608e-12 N`; the force components
and moment components otherwise sum at the reported roundoff scale. The
noncut port maximum is `3.299010370e-12 N` on the left and
`2.269448518e-12 N` on the right. Their full nodal port-work pairings are
`-1.56688671013318e-7` and `+1.56688671014188e-7 J`, with noncut pairings
`5.2133e-19` and `5.4700e-20 J`.

Thus the saved finite-element **weak nodal** action yields a two-sided,
work-conjugate discrete cut port after the physical P0 load is partitioned by
source interval. V6's unbalanced raw stress-face tractions (y-force sum
`+20.358156629 N`) are not equivalent to that discrete port and remain an
invalid sided reference. This V7 result does **not** establish a finite-state
native B3 trace equivalence, allocate the V5 body-work gap, establish BL5
physical accuracy or select a multiplier space.
Independent read-only result review found the saved FE balance convincing
within this scope and no overlooked source/sign defect. It noted that the
`0.402617092486 N m` cut moment matches the saved native station moment in
magnitude, but equal moment scale alone is expected from the common action;
the conforming V7 cut work is not the native broken-spin work.

An explicit native half-cell trace map remains necessary to interpret the
broken virtual field. Merely lifting the native spin jump rigidly onto this
already balanced V7 section wrench will reproduce moment-times-jump work by
algebraic duality; even agreement would **not** allocate the V5 compliance or
body-work difference. The next substantive decision therefore needs a bounded
two-sided *response* reference with independently declared cut kinematics,
loads and support/gauge treatment, or another reference that measures the
left/right port flexibility under the same physical action. Derive and review
that contract before a new solve. No automatic refinement, V5/V6 rerun or
formal F03 follows merely from V7.

Protected raw SHA-256: registration
`1eb4b4064e8e9e3996a5951a814567aaf6034e35e10c64efc41a3b57ce367fe6`,
receipt `1696de335325959a239aa62a332a2b15093f843764af11cda2b4cefbe7193353`,
result `43e592a917e3e716cb2d9bcfcc46cfbe271b03191eeb624b657506e96a85e8ec`.
Full stdout/stderr are preserved beside the receipt.
