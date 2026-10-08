# F03 finite-pad endpoint: predictions before independent-axis execution

22 September 2026. Independent read-only mechanics analysis of the v2
feasibility fields motivates these diagnostic predictions. They do not
establish a continuum singularity, numerical instability or a qualified
connection law. The `.05 m` finite-area pads and all physical inputs remain
fixed in the next registered axis experiment.

For beam-cell length `hb=1/Nb`, the root transverse displacement's Hermite
test function is `H00(s/hb)=1-3(s/hb)^2+2(s/hb)^3` on the first cell and
zero elsewhere. Its direct port force is exactly

`Rport,y = integral_0^hb H00(s/hb) lambda_y(s) ds`.

For a smooth fixed traction this is `lambda_y(0)*hb/2 + O(hb²)`; the
consistent applied root force has the analogous behavior. For P1 traction
over a mortar cell `hm` with `hb <= hm`, the exact expression is

`Rport,y = hb * [(1/2 - 3 hb/(20 hm))*lambda0 + 3 hb/(20 hm)*lambda1]`.

At the v2 coarse Q4 mesh, `hb=.125`, `hm=.25`, root direct port force
`-160066.972 N`, and first-quarter force `-203976.071 N` imply
`lambda0 ≈ -3.31 MN/m` and `lambda1 ≈ +1.68 MN/m`. This is a sign reversal
within the first quarter. The terminal weighted root force requires at
least one of its first two coefficients to be no greater than approximately
`-9.56 MN/m`. Signed net-quarter force can conceal this concentration and
cancellation. It cannot identify the responsible axis when all resolutions
change together.

For a continuous gap component `g` and exact first P1 hat row,

`integral_0^hm (1-s/hm) g(s) ds = 0`,

integration of `g(s)=g(0)+integral_0^s g'(t)dt` gives

`g(0) = -integral_0^hm (1-t/hm)^2 g'(t) dt`,

and therefore `|g(0)| <= sqrt(hm/5) * ||g'||_L2(0,hm)`.

For a fixed nonzero pad area, the translated shell area-average trace is
bounded by the shell H1 field; it does not have the same endpoint regularity
problem as an isolated two-dimensional point sample. A persistent endpoint
gap under mortar refinement requires a growing local derivative norm. A
tiny assembled weak gap alone gives no bound independent of that norm.

Use the fresh axis snapshots to inspect signed P1 coefficients, their L²
norm and peak, the root-weighted integral above, endpoint pose/gap, and
resultants over fixed physical bands `[0,1/32]`, `[1/32,1/16]` and the
first mortar cell. Retain the previously reported physical quarters.

- Beam-only refinement tests whether the expected shrinking root test
  support explains the shift, or whether the solved traction reorganizes.
- Mortar-only refinement tests concentration/oscillation independently of
  the structural operator; a mass/energy-normalized Schur diagnostic can
  distinguish constrained modes from simple row rank.
- Shell x/y refinement tests the averaging trace and structural compliance
  independently of beam and multiplier resolution.
- A shrinking-band impulse with stable fixed-band resultants is consistent
  with an endpoint distribution; it is not proof or permission to discard
  a registered reaction channel.

P1 nodal coefficients and exact finite-model integrals are directly
recoverable from the owned snapshots. A claim about derivative norms,
pointwise gap maxima or uniform interface stability needs its separately
reviewed computation and normalization. Do not infer it from these
predictions or weaken the physical-reference thresholds.
