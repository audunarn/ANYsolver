# D1 two-body cut-front pressure-work counterexample

**29 September 2026. Development mechanics finding; production law unchanged.**
This tests the actual flat Q4/S3 physical work map on one admitted
eight-Q4/two-S3 nonmatching family. It does not qualify or reject every
shell/contact profile, and it is not a completed nonlinear path.

## Question and exact construction

The [one-hat shell bridge](d1_cut_front_shell_bridge_20260929.md) showed
that free S3 target motion detects a source-only weak pressure direction.
Does the *full two-body* map retain a pressure combination whose discrete
work collapses faster than its physical work as a positive cut support
vanishes? The answer for the stated two-S3 target is yes.

Use the same shape-regular four-by-two Q4 source, whose x nodes are
`0,.5,1,1.5,2` and y nodes are `0,1,2`, and two S3 target triangles on
`x=[−.113,2.127], y=[−.087,1+θ]`. The source x=0 edge and target left
edge are fixed. Source x hats `h1,h1.5`, centered at 1 and 1.5, have
entire supports at least 0.5 from the prescribed source edge. Their
physical shell skins touch at zero displacement. For each x hat use the
exact [corrected cut-row y pressure](d1_cut_front_exact_counterexample_20260929.md)
`pθ=αq0+βq1+q2` with

```
b=θ²/2−θ³/3;  d=1/4+θ−θ²+θ³/3;
β=−b/d;  α=−β/2.
```

The source Q1 normal work is zero on its first two y rows and
`r2=θ³/3−b²/d=O(θ³)` on its last row. Both source x hats therefore
have `O(θ³)` work on every source Q4 normal test.

For the two free target normal nodes, the independent limiting y
pressure measure is `(1−3y)dy` on `[0,1]` plus `½δ_(y=1)`. The target
P1 tests obey `ψ17+ψ18=ξ(x)` on *both* triangles. Since the limiting
measure has zero mass, the two target work rows are exact negatives.
The [independent piecewise-polynomial integral](d1_cut_front_two_hat_limit.py)
gives the corrected leading matrix, before the target normal sign:

```
T0 = [−0.02541607853  −0.009283277741]
     [+0.02541607853  +0.009283277741].
```

Its unit coefficient null is `c=(+0.34308319365,−0.93930502087)`;
`||T0 c||=1.51e−17` numerically. The rank-one identity is exact, not an
SVD inference. The finite-cut target integral is analytic at `θ=0` after
splitting at the moving S3 diagonal and has expansion
`θ² T0 c+O(θ³)=O(θ³)`. The source work is already `O(θ³)`. At touching,
constant zero physical gap removes support-motion boundary terms from the
first variation; parallel flat skins make tangential and director
variations orthogonal to the normal. Thus the complete *ideal discrete*
two-body work on this signed mode is `O(θ³)` after constraints.

The independent oracle initially missed the small x interval where the
S3 diagonal falls below y=0. Its v1/v2 outputs and the corresponding
earlier production-mode records remain retained as **failed derivation
evidence**. The corrected v3 oracle splits at that exact crossing for
both the limit and each finite cut. The corrected production v4 records
use the corrected `c`; no old value is treated as the reference.

## Physical witness and structural energy

On x in `[0.8,1.1]`, `c1 h1+c2 h1.5` is positive and at least
`0.08660555`. Take the H² source transverse motion
`w_x=(x−.8)²(1.1−x)²` there and zero elsewhere, times
`w_y=y²(1−y)²` on `[0,1]` and zero elsewhere. Set target motion and
shell rotations to zero. The motion vanishes at the prescribed x edge
and has finite shell energy. Its normal pressure work equals
`(∫(c1h1+c2h1.5)w_x dx) β/120`, with nonzero magnitude of order
`θ²`. The displayed x lower bound gives a limiting unnormalized work
coefficient of at least `1.169e−7` per `θ²`; its finite, fixed energy
norm changes only the positive constant.

The [zero-cut contact-free structural check](d1_cut_front_zero_cut_energy_v2_20260929.json)
finds 84 free coordinates, symmetric reduced stiffness and eigenvalues
`0.0930677447` to `30584.5138`. The geometry and element matrices vary
continuously and remain nondegenerate for θ near zero, so the reduced
discrete energy is uniformly coercive there. The physical discrete dual
work is therefore `O(θ³)` while the continuous admissible witness gives
an `Ω(θ²)` dual-work lower bound. Their ratio tends to zero for this
family. This defeats a cut-phase-uniform pressure-work inf-sup assertion
for the unchanged Q1 pairing under this profile.

## Bounded production work and cone checks

The [production probe](d1_cut_front_shell_work.py) used actual physical
Q4/S3 skin maps, all structural translation/director coordinates, support
normalization, constraint reduction and the existing shell stiffness.
Every pose was at touching, with six selected pressure hats assigned a
strictly positive 1-Pa baseline. Both signs of a 0.5-Pa perturbation in
the signed null direction remain nonnegative; the smallest pressure is
0.5303 Pa. All six selected rows remain projected active. Supported
positive support is retained even on the vanishing cut row.

| θ | Source free normal work | Target free normal work | Discrete energy-dual work / θ³ |
|---:|---:|---:|---:|
| .100 | 8.0440e−5 | 1.5024e−4 | 0.18287 |
| .050 | 1.0978e−5 | 2.1690e−5 | 0.20451 |
| .025 | 1.4527e−6 | 2.9541e−6 | 0.21916 |

The source normal work matches exact tensor-Q1 mass to ≤9e−15 relative.
The free target normal vectors match the **corrected independent
finite-cut polynomial integral** to ≤6.7e−14 relative. Other tangential
and director work is at roundoff scale. Full virtual-work residuals are
below 5e−19; reduced energy-response residuals are below 8e−13 relative.
Each completed case took under 3.3 s / 180 MB process-tree RSS under
the 180 s / 1 GB development cap. Source was `664b023c` plus the
hash-recorded offline probe edits; Python 3.14.2, NumPy 2.4.6 and
SciPy 1.17.1 with one BLAS thread are recorded in raw files.

The [θ=.05 manufactured-load record](d1_cut_front_two_hat_touch_005_v7_20260929.json)
lists 14 free `uz` nodal loads that balance the baseline contact force
at the stress-free zero pose. Other free force components are at most
`2.23e−19`, the reduced equilibrium residual is `3.54e−19`, and
selected complementarity L1 is `3.20e−14 N`. The other nine supported
pressure modes have zero force and zero geometric gap to `1.88e−18 m`;
the complete complementarity L1 is `6.57e−14 N`. These loads construct a
mathematically admissible six-strictly-active contact equilibrium; an ordinary
nonlinear solver path to it has **not** been run or accepted.

Final-source corrected [θ=.1](d1_cut_front_two_hat_touch_010_v7_20260929.json),
[θ=.05](d1_cut_front_two_hat_touch_005_v7_20260929.json) and
[θ=.025](d1_cut_front_two_hat_touch_0025_v7_20260929.json) results
have adjacent captured logs and resource records. The corrected
[independent oracle record](d1_cut_front_two_hat_limit_v3_20260929.json)
contains the limit matrix, coefficients and finite-cut target work.
The zero-cut stiffness run has its own bounded resource and log files.
The intermediate v4–v6 records remain retained as development history;
their mechanics are unchanged but their probe source predates the final
complementarity and load reporting fields.
The [final-source comparison script](d1_cut_front_two_hat_compare.py) and
[summary](d1_cut_front_two_hat_compare_20260929.json) confirm exact probe
hashes, completed bounded runs, maximum source/target oracle relative
errors of `8.55e−15`/`6.66e−14`, positive zero-cut stiffness and the
declared active/cone checks.

## Disposition and limits

This is a counterexample to a **uniform pressure-work stability claim for
the unchanged fine-Q1 pairing over this admitted nonmatching Q4/S3
cut-rim family**. It is not a claim that the saved two-active D1 trajectory
has a pressure null, that every S3 target mesh has the same rank, or that
the production solver failed to solve this manufactured load path.

The current D1 breadth includes finite sliding and changing partial
overlap, so a qualification that ignores arbitrarily small positive
cut supports would need an explicit narrower boundary. The required
breadth has not been narrowed. The next implementation slice must derive
and independently check a stable pressure/displacement pairing or a
consistent stabilization that retains physical work and small supported
features. Do not delete positive-support hats, weaken the gap gate, or
increase iterations to mask this issue. Existing geometry, virtual-work
and state evidence can be reused after source-impact review; pressure
stability, coupled response and route timing need a new candidate.
