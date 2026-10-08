# V4 tiny active-row load: source-only independent review

No edits or numerical runs were made for this review. The prior V4 FAILED
disposition and 11.6943905 s cumulative execution record are unchanged.

The failing slot 55 is a y displacement row (`55 % 3 == 1`), even under the
verified anti-y reflection. Its load is the beam-side `external - C.T @ lambda`
covector. Away from the tip, this is the sum of y-translation and y-director
P0 interface contributions. Reflection projection changed the saved load by
exactly zero; symmetry alone cannot remove the 3.5664998967e-16 N component.

The 64-digit residual evaluated from the stored binary64 operator, solution,
and load is 9.1302159083e-13 N. The unchanged active-row ratio is 2559.993319.
Global work agreement cannot repair this row. Reintegrating C exactly could
test coefficient roundoff, but it would justify zeroing only if the row
functional or a proved relation among the saved multipliers is identically
zero. Precise load assembly alone cannot reduce a nonzero row's KKT residual
below the current 1e-8 relative criterion.

The next bounded discriminator is to derive the slot-55 C3D20/P0 row
coefficients analytically from exact polynomial integration, evaluate each
segment/channel contribution against the saved multipliers as exact binary64
values, and bound the summation error. A proved structural zero allows an
identity-based assembly correction; a proved nonzero load rules that out.
Either outcome still requires a separate valid equilibrium result before a
body-work comparison. This check has not run and needs the applicable
execution authority. Formal F03 and the separate historical Fz retry remain
untouched.
