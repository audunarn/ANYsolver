# Saved failed-trial diagnosis — READ only

The final `.3125` rejection has a concrete constitutive branch-crossing
obstruction. At the last saved Newton trial, the smallest permitted dyadic
candidate crosses one additional fibre activity boundary and increases the
actual merit. Saved residuals and tangents consistently describe that increase.
The separately reported whole-KKT finite-difference errors are dominated by
small axial cancellation/representation effects; their size cannot explain the
saved current equilibrium defect. This does not establish convergence of the
full programme, a material tangent pass, a limit load or formulation failure.

No solve, operator/material/chart evaluation, numerical-package import, parameter
sweep, product edit or numerical lease was used. Only Python standard-library
parsing/arithmetic on the exact saved arrays and source was performed.

## What the whole-free-KKT norm compares

The saved physical coordinate vector has 126 entries, followed by 20 BL5
multipliers. Twelve supported shell coordinates are excluded, leaving 134 free
KKT entries. For the actual saved Newton correction `d` and fixed accepted
predecessor, the probe compares

`e(h) = [R(advance(x,+h*d))-R(advance(x,-h*d))]/(2*h) - K(x)*d`

with `||D_free e(h)|| / max(||D_free Kd||,1)`. The pose scales are reference
length `L=0.3783465619944815 m` for translations and 1 for rotations. Native
retained entries use six force and twelve moment roles; the four axial
compatibility rows have `EA=2.1e9 N` as their work pairing. Multiplier weights
are **1**, not the driver's frozen constraint normalizers. Thus this diagnostic
tail mixes raw constraint units; its tail norm is at most `1.7134e-12` here and
does not produce the observed discrepancy. This is not the physical convergence
metric, which separately checks work equilibrium and scaled constraints.

The explicit mapping is shell `0:48`, beam nodal `48:78`, member-1 cells
`78:84`/resultants `84:102`, member-2 cells `102:108`/resultants `108:126`, and
multipliers `126:146`. The reviewed original JSON mislabeled columns below 108
as kinematic, thereby including member-1 resultants. That original is preserved
byte-exact. `owner-diagnosis-v3-corrected.json` fixes the labels. The independent
material-column splits in the detail/branch reports use both explicit resultant
ranges; the numerical total errors never depended on the bad label.

The standard-library reconstruction reproduces the published Newton-direction
errors exactly: `2.7550217809e-4`, `2.9099988564e-3`, `9.7383324994e-3` at
`h=1e-4,1e-5,1e-6`, with `||D Kd||=1.8097776493`. More than
`99.9999979%` of their squared error comes from rows **84,87,108,111**: the
two half-cell axial compatibility equations in the elastic generalized member
and the physical-fibre member. The largest nodal error norm is `2.3598e-6`;
the retained error norm is `1.7624e-2`. The material masks are stable for all
three Newton-direction differences. The rich direction changes masks and cannot
certify a smooth derivative.

## Cancellation and representability evidence

The compatibility residual is `k(q)-g*(p;origin)`. At row 84, the saved Newton
kinematic and material contributions are about `-3.0408825e-9 m` and
`+3.0408804e-9 m`, leaving `-2.0920731e-15 m`. At row 108 they are
`-1.8223254e-8 m` and `+1.8149612e-8 m`, leaving `-7.3642298e-11 m`.
The FD discrepancies imply errors in the **un-divided plus-minus residual
difference** of `4.57e-19` to `3.81e-17 m`. This explains how an extremely small
value error becomes a failed relative derivative check when divided by `2h`
and paired with `EA`. It does not relax the `1e-5` requirement.

`ULP(.25)` in the original arithmetic report is only a characteristic chord
scale. It is not a proved absolute-coordinate quantization floor: `_assemble`
constructs compensated reference/displacement high-low positions. The saved
last dyadic state confirms nonzero translation increments exceed `7.32e9`
ULPs of their stored displacement and translation rounding is at most
`1.4933e-21 m`.

Cell rotation diagonals are a more specific representation sensitivity. Their
saved values are near 1 with ULP `1.1102230e-16`. At the last dyadic update,
diagonal remainders after subtracting the first-order saved rotation action
range around `1e-18` to `4.6940e-17`; the true second-order norm bound is at
most `3.7048e-20`. For `h=1e-6`, first-order axial diagonal changes range
from about `0.0082` to `0.247` ULP. The double matrix update and subsequent
`(U^T-I)d0` kinematic value are therefore plausibly involved in the FD noise.
The actual +/-FD states and separate kinematic/material values were **not saved**,
so this identifies a credible source, not a measured decomposition of those
specific FD errors. Both members share the same geometry route.

## Why that noise is not the observed equilibrium obstruction

The fixed applied-work denominator is `156.25*L = 59.1166503116 N m`.
Current `||Dq R||=1.8097776465 N m` gives merit `.0306136703779`.
The original saved bare-sparse-solve defect is only
`||D(Kd+R)||=4.4499433462e-7 N m`, relative `2.4588343e-7` to the residual.
Re-summing the same saved matrix products with `math.fsum` changes that defect
by only `2.6574e-13 N m`; it is not just a matvec accumulation discrepancy.
Normalized by applied work, the linear defect is about `7.53e-9`, rather than
the current `.0306` equilibrium defect. The largest raw constraint linear
defect is `6.7147e-16`; frozen constraint scales were not saved, so no separate
scaled-constraint linear-solve pass is claimed. There is no causal evidence
for a factorization/scaling repair from this state.

At `h=1/4096=.000244140625`, the saved linear model predicts merit
`.0306061963373`, below the old value. Actual merit is `.0306443547345`.
The nonlinear residual defect is `.0241497186215 N m`, about 54,270 times
the entire saved linear defect. Row 108 alone adds `.0241197387228 N m`;
rows 118,115,116,119 supply the remaining material-coupled moment channels.
The generalized axial defects are only `6.02e-10` and `1.17e-8 N m`.

The saved activity indicator changes from 8 to 9 fibres; the only newly advancing
entry is physical member 2, **station 0, fibre 1**. These masks compare accumulated
history against the fixed origin; explicit recovery branch labels and signed
yield margins were not saved. Source confirms positive accumulated advancement
arises from the existing return map. Its elastic modulus is `210 GPa`, whereas
the declared `1 GPa` hardening law gives plastic algorithmic modulus
`E H/(E+H)`, a modulus ratio of 211. The coupled compliance can therefore change
strongly at an ordinary yield transition. No constitutive guards were bypassed.

Five saved native channels satisfy the same piecewise-branch relation:

`R_i(h)-R_i(0)-h [K(0)d]_i ≈ (h-h*) [(K(h)-K(0))d]_i`.

Rows 115,116,118,119 independently give
`h* ≈ .00017062445044` (agreement around `1e-13` for the last four dyadic
candidates). Row 108 agrees to the larger axial-value noise scale. Its saved
tangent jump is `328.08739977 N m` per amount from **material columns**; its
geometric contribution is below `1e-6`. For the smallest candidate,
`(h-h*)*328.08739977 ≈ .02411974 N m`, reproducing its actual defect.
This is substantial consistency evidence between saved branch tangent and
residual, rather than evidence of a missing derivative.

The largest directly measured branch-preserving positive FD amount `1e-4`
decreases merit to `.0306106090481`; `1e-5` and `1e-6` also descend. Those
amounts lie below the inferred transition and below the 13-trial dyadic reach.
Thus **insufficient dyadic reach explains this final line-search rejection**.
It does not explain or cure the entire programme: the preserved quadratic
candidate reached smaller descending amounts and still exhausted 24 Newton
iterations at `.3125`. There is no new globalization recommendation here.

## One smallest bounded discriminator, not execution authority

At the already saved failed state and its exact accepted material predecessor,
freeze geometry and use **only the saved resultant part of the Newton direction**
(`84:102` and `108:126`). Audit the existing coupled fibre cell response at
`p0`, `p0±1e-4*d_p`, and the already saved last-candidate `p`. Record its
gradient high/low pairs, compliance high/low pairs, station-0/fibre-1 explicit
branch label and signed `|E(e-z0)|-radius` margin. Compare the branch-preserving
material difference to `H*(p0)d_p`, and its cross-boundary secant to the saved
old/new compliance jump, preserving pairs in standard Decimal arithmetic.
No global solve, new fixture, tolerance change, history commit or parameter sweep is needed.

This direction reproduces the same `p` perturbation as the saved full Newton
probe. Because the coupled cell depends only on `p` and fixed origins, its
material branches at `±1e-4` are the same already observed stable branches.
Its four axial un-divided signals are about `2.32e-13` to `3.63e-12 m`, much
larger than the full-direction cancellation signal, and frame rounding is absent.

If this branch-preserving material derivative or cross-branch compliance relation
fails `1e-5`, isolate the existing cell gradient/compliance or fixed-origin mapping
before touching the global driver. If both pass, the check isolates the existing material compliance and fixed-origin
consistency; it does NOT prove the complete FD error is kinematic noise. Assembly
or chart derivative bias and representation effects remain unresolved. The saved
last rejection is consistent with an ordinary yield-boundary obstruction, but
that separate consistency evidence is not a whole-system tangent pass or a cure
for global convergence. Any next implementation decision needs separately adopted
authority; sparse scaling or a material tangent bug is not established here.
No check proposed here has been executed or authorized by this diagnosis.

The 760- and 779-path consumed manifests and all existing evidence remain intact.
Files created for this diagnosis are listed and hashed in the new
`owner-diagnosis-v3-handoff.json`; the original handoff/manifest files were not
updated. Scientific criteria and full simultaneous material obligations remain open.
