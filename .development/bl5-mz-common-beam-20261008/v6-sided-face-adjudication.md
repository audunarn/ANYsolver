# V6 saved C3D20 cut-face diagnostic

One user-approved V6 attempt completed against source head `dcdb80fc` and
saved V5 inputs. It reconstructed stresses from the existing resolved beam
solution; it launched **no new equilibrium solve**, external job, or F03 run.
The one-use authority is consumed. The 30 s process cap and 2 GiB tree limit
were respected: process wall `2.5653282 s`, sampled peak `160,354,304 B`,
exit 0, no stop reason. The child reported CPU affinity `[0]`, JIT disabled,
one Numba thread and one thread in each loaded BLAS pool.

The raw outward cut-face resultants at `x=0.5 m` do **not** establish a
balanced sided action. The left/right y-forces are `+7.349246346` and
`+13.008910282 N`, giving `+20.358156629 N`. Their force-sum norm divided by
the sum of side norms is `1.0`. The moment sum is approximately
`(0.099191774, 0, 0.005680789) N m`; its analogous ratio is
`0.925551917`. Consequently the calculated `1.631405007e-9 J` broken-trace
virtual-work difference is **unqualified for comparison** with the native
reference-linearized station work `4.009200810e-7 J`. It cannot allocate the
V5 body-work gap or accept/reject the BL5 law.

Independent read-only source/result review found no concrete normal, Voigt,
Jacobian, area, saved-q ordering or sign error. A conforming displacement FE
solution satisfies weak nodal equilibrium; raw recovered boundary stresses
need not equilibrate. The weak line action also loads shared cut nodes, so
zero raw cut-traction sum is not the correct assumption without load
partition. This result does **not** overturn V5's verified global discrete
equilibrium.

The next discriminator, if authorized, is a bounded **saved-only** volume-work
audit: recover the adjacent C3D20 element nodal internal actions from
`integral B^T sigma dV`, match them to the saved load and gauge covectors,
partition cut-node external actions, and check complete left/right subdomain
rigid-force, moment and virtual-work balances. Only an equilibrated,
work-conjugate side port can support a subsequent seam comparison. Do not
repeat V6, tune a sign to make it pass, refine automatically, or run F03.

Protected raw files: `v6-sided-face-registration.json` SHA-256
`c93f7f15292934862d5e78576619b805b39bcee8322d486b5443e11a322b3b01`,
`receipt-v6-sided-face.json` SHA-256
`00fb66823f2fc518e39b6cc78184a9768e126711199cf86a5c620dbbc4839a11`,
and `case-v6-sided-face/result.json` SHA-256
`96bf50e4d67390f946943ab7c8efa93c666a1ce9645f6a24d892163cbf9e51d5`.
The stdout/stderr files are retained beside them.
