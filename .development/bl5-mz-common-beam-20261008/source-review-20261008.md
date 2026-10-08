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

## Source derivation and candidate correction — 8 October 2026

The exact-row derivation resolves the source question more strongly than a
multiplier-specific dot product. Local beam node 18 is the vertical C3D20
midside edge node, with reference coordinates `(1, 1, 0)` and physical
coordinates `(0.5, 0, 0.04)`. Its `y` degree of freedom is local beam slot 55.
Its shape contains `(1-zeta**2)`, so it vanishes identically on both physical
beam faces sampled by the weak five-channel operator, `z=0.01` and `z=0.07`.
Only the `y` position and director rows could otherwise involve this degree
of freedom. Both exact coefficients vanish for every P0 segment, regardless
of the saved multipliers. The end traction loads only `x=1` beam nodes; its
exact slot-55 value is also zero. Thus the analytical reduced beam load on
this slot is exactly zero. The saved V4 nonzero value is an implemented
floating-point assembly artifact, not a physical interface action.

The source's physical-to-reference `center/span` calculation could round a
material-face coordinate slightly inside `zeta=+/-1`. A candidate source
correction now substitutes exact reference boundary coordinates when the
physical sample is on a cell face. A focused algebraic regression confirms
all five local trace channels and all 20 weak rows are exactly zero in the
three top V4 tiny-load columns, beam-local slots 55, 58 and 130: 3 passed,
9 deselected. Their saved loads were respectively `3.5664998967e-16`,
`-1.1916410059e-16` and `-2.3748588913e-16` N. This is not a V5 solve or
a proof of equilibrium. V4 remains FAILED, its cumulative ledger remains
CLOSED, and the prior high-precision residual remains unsatisfied. No old attempt was
rerun, and no F03 or separate Fz body authority was consumed.

To decompose the V4 implemented dot exactly, the actual binary64 C column
would be needed alongside the saved projected multipliers. V4 did not save
that column. The analytical identity has zero error bound; an exact rational
reconstruction of the old *implemented* dot cannot be claimed from the
available arrays. A new solved comparison requires a separately valid
numerical execution authority and its unchanged equilibrium criteria.
