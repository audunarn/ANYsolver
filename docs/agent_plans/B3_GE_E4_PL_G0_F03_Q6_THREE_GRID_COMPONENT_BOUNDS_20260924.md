# Q6 three-grid saved-state component bounds

**24 September 2026. Unregistered saved-input diagnostic. F03/G0B open;
G1 barred.** The [X2 component-bound method](B3_GE_E4_PL_G0_F03_Q6_X2_SAVED_STATE_COMPONENT_BOUND_20260924.md)
was applied unchanged to the earlier archived X0 and X1 KKT certificates.
This reused saved matrix/RHS, state, scales and certified inverse-norm upper
bounds. No model assembly, factorization or equilibrium solve occurred.
Archive, candidate and canonical KKT/RHS hashes were checked in each case.
The recomputed interval residual two-norm upper equalled each original
certificate's stored bound.

| Grid | Scaled state component error | Displacement component, m | Root force component, N | Root moment component, N m |
|---|---:|---:|---:|---:|
| X0 | `7.067775038421738e-10` | `5.5198253805744005e-14` | `0.0007067775038421738` | `0.00032511765176739996` |
| X1 | `6.806382381879425e-10` | `5.6169346972764937e-14` | `0.0006806382381879427` | `0.0003130935895664536` |
| X2 | `6.202021901144683e-10` | `5.141840670509858e-14` | `0.0006202021901144684` | `0.00028529300745265546` |

The three saved archive SHA-256 values are, in grid order,
`5001042a307329b3166780a7389310c04c2a25e2549e7308d26e4290c4dcde57`,
`99839670c7df0d81fa9e2ea5ba697dd74d79e953d5a335bd2215fa7f614dc8da`,
and `c2e1d8445ec425a4c87810191bae269e62c9349bad2023f80a2f0ba93615ba94`.
The candidate hashes are respectively
`0dea4c0a8ac6f817cc20a1a02ec6d9e8802563653f4868a6f0563c54a1a08e13`,
`be927745bd30069238ba0a147c4925bf26e1531b5079e36fe9ee40a77cf13bb7`,
and `036ed6d3d28e5ee30c1e35cd319db42e1dfb6e0535102cea91e47913165012ed`.
Focused tests passed **15/15** on the three locally retained archives and
small known-solution/invalid-bound cases.

These bounds isolate numerical error in the saved scaled KKT state under the
experimental certificate assumptions and exact application of stored binary
physical scales. Rounding in the separate recovery computation is not
included. They say nothing about discretization
error, full signed physical functionals, interface stability, physical
reference agreement or G0 acceptance. The X2 shared-assembly resource
overrun remains unchanged. Further work should propagate bounds to the
registered physical functionals and resolve the native interface mechanics,
rather than treating small linear-solve error as evidence of a sound coupling.
