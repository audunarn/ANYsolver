# X2 Q6 saved-state component bound

**24 September 2026. Unregistered diagnostic; F03/G0B open and G1 barred.**

The saved X2 shared-assembly KKT matrix, right-hand side, candidate state and
inverse-infinity upper bound were read without reassembling or refactorizing.
The archive and candidate hashes were checked against the preserved certificate
measurement, and the independently recomputed interval residual two-norm upper
bound exactly matched its earlier value (`2.51118544166614e-13`). The
experimental compiled interval kernel and the same outward-rounding helpers
were used. This result is conditional on the earlier experimental inverse
certificate and floating-point arithmetic checks; it is not a new formal
scientific registration.

| Quantity | Outward upper bound |
|---|---:|
| Scaled residual infinity norm | `1.3137386144224107e-14` |
| Scaled KKT-state component error | `6.202021901144683e-10` |
| Physical displacement component error | `5.141840670509858e-14 m` |
| Physical root force-component error | `0.0006202021901144684 N` |
| Physical root moment-component error | `0.00028529300745265546 N m` |

The state bound uses
`||z-z*||∞ ≤ ||H⁻¹||∞ ||b-Hz||∞` with the saved
`||H⁻¹||∞` upper bound `47208.948820244725`. It then applies the saved
positive displacement and multiplier scales componentwise. The two root force
channels and one root moment channel retain distinct units. It covers the
saved physical coordinate and root-multiplier components only. It does **not**
bound derived tip/station poses, interface work, energies, all signed response
channels, or errors in the mathematical discretization. These observables
still require explicit sensitivity/error propagation and independently settled
physical references. The earlier complete-route X2 process took 2,258.19 s,
above the draft 1,800 s envelope, and remains a resource failure for that
draft envelope.

The source is
[`scripts/_b3_e4_f03_q6_saved_state_bound.py`](../../scripts/_b3_e4_f03_q6_saved_state_bound.py),
SHA-256 `0b10bed8e092d2a7fbc5ae3df0dfdd4f9df870608002504d9d6313f7b0b27683`.
The existing compiled interval kernel SHA-256 is
`4736322960b64aaf1e1aba74a030c4f480c135cd1f9a207dc295dbcb43635185`.
The saved candidate SHA-256 is
`036ed6d3d28e5ee30c1e35cd319db42e1dfb6e0535102cea91e47913165012ed`,
and scaled-system archive SHA-256 is
`c2e1d8445ec425a4c87810191bae269e62c9349bad2023f80a2f0ba93615ba94`.
Focused checks passed **13/13**, including a known-solution enclosure and the
saved X2 replay. An initial run had 11 passes and two test-setup errors because
the default external pytest temp directory was inaccessible; rerunning with a
worktree-local disposable temp directory passed. No product mechanics changed.

**Next:** bound the registered physical functionals from the same saved state
without another full solve, assess whether the complete scientific route can
meet a frozen resource envelope, and resolve the native F03 mechanical
stability and physical-reference requirements before G0B adjudication.
