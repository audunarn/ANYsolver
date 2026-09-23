# F09-L: unregistered mixed-elbow conditioning diagnostic

23 September 2026. This is an adverse **diagnostic**, not a scientific execution registration, F09 acceptance, a supported-domain bound, or G0B closure. It does not change the physical B2 operator or any admission rule.

The reproducible runner is `scripts/probe_b3_ge_e4_pl_g0_f09_mixed_elbow_conditioning.py`, SHA-256 `7bd6670c059d4a334e124d2f42cd884ed22fe7a48df69c518ac4ea7f12d9e947`, run from integration commit `3e026ede09deeeb750039c17fb2ad4c9a087af52` with Python 3.14.2, NumPy 2.4.6 and SciPy 1.17.1; `anysolver` imported from this checkout's `src`. Raw JSON is preserved at `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f09-unregistered-mixed-elbow-20260923/results.json`, SHA-256 `cb9e88a0124cf74e7f22179e6fb82239e0edde232055981e47fffd9f13813271`. The focused existing B2 mechanics suite passed 27 tests.

The case is a root-fixed two-member L elbow with a mixed tip wrench. Both samples share geometry, frames, bending/torsion stiffness and applied couples; axial area and proportional tip forces change. The runner compares the binary64 sparse solve to an independent exact-rational cut-wrench energy derivative and to an exact-rational solve of the **rounded assembled binary64 matrix**. Rational arithmetic in the latter separates assembly rounding from the sparse factorization. The energy's affine wrenches make three-point Simpson integration exact for this quadratic case.

| Quantity | Moderate, area `1e-4` | Extreme, area `2^-80` |
|---|---:|---:|
| Maximum exact-rounded versus physical translation difference, component-scaled | `3.33e-16` | `1.72e-16` |
| Maximum sparse versus physical translation difference, component-scaled | `4.59e-13` | `1.74e7` |
| Sparse free-force residual relative to largest tip force | `3.77e-13` | `1.71e7` |
| Sparse free-moment residual relative to largest tip moment | `5.92e-16` | `2.96e-16` |
| Indicative binary64 condition estimate | `1.59e5` | `1.07e26` |

Translation and rotation errors use separate componentwise floors of 1 m and 1 rad in this numerical fixture. Force and moment residual ratios measure resolution relative to the applied signals; they are not certified backward-error measures. In the extreme case the binary64 sparse tip `z` displacement is about `5.98e7` versus the physical reference `3.43125`. The absolute free residual is only `1.58e-16`, which is misleading beside tip-force components of order `1e-25`. The extreme condition estimate is far beyond reliable binary64 SVD resolution; its digits do not define an admission threshold.

An independent read-only mechanics/code review checked the frame orientation, cut-wrench sign, half-energy integral, exact derivative, local-to-global assembly and root clamp. It found no blocker in this narrow diagnostic. A later F09 candidate must register a physical range, unit-aware scales and more than these two conditioning samples before making a support or accuracy claim.
