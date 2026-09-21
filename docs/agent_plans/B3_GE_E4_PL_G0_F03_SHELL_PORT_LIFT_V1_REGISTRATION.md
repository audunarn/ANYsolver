# F03 supported shell-port lifting diagnostic v1: registration

22 September 2026. Status: **proposed exploratory falsification diagnostic,
not F03/G0B acceptance**. Freeze the source and this registration at a
clean integration commit, obtain independent pre-execution mechanics/code
review, and execute once under a new exclusive evidence root. Preserve
all previous evidence and its adverse physical-response result.

## Mechanical distinction and candidate

The supported native beam root translations are zero, but the physical
shell four-sample pose at attachment coordinate `s=0` can translate.
Representing a nonzero shell-induced root gap by beam-rooted P1 functions
alone forces a first-cell ramp: its derivative contribution scales like
`L0/h` for cell width `h`. An endpoint law that sets the *gap* to zero
at `s=0` is therefore not implied by the supported beam boundary.

Use the existing scaled three-channel gap `w=(g_x,g_y,ell*g_yaw)`,
`ell=.46 m`, the registered broken-overlay `R` with its L2, H1 and
native yaw-jump terms, and the **actual** supported shell and native
beam trace map `E`. Define two physical shell displacement fields,
one per in-plane direction, with nodal amplitude `-p(x)` independent
of y, where `p(x)=2(1−|x−.5|)` on the panel `x∈[−.5,1.5]`.
They vanish on the fixed x-end edges. Both Q4 and S3 represent this
piecewise P1-in-x field exactly at the nodes. The four physical samples
at `s=0` have x positions `±.2`, so their centroid response to the
negative shell fields gives shell-induced positive gap translations
`(p(−.2)+p(.2))/2=(.6+1.4)/2=1`. Retain the *actual* yaw trace
induced by each shell field; do not erase it to make a scalar port.
These ports have fixed physical width as the shell mesh refines.

Let `S` contain these two reachable shell port traces, every free
native beam nodal P1 x/y translation trace, and every native cell P0
scaled-yaw trace. For a reachable `w=Eq`, set `c=w_t(0)` and subtract
the two shell ports `P c`. Determine the rooted P1 translation
coefficients from all existing K4 P1 moments (or the local-dual
biorthogonal moments) of the remaining translations, and determine
P0 yaw coefficients from its cell-average moments. This defines
`Lw ∈ span(S)` with actual root translation and `F Lw=Fw` for the
existing K4 or local-dual row functional `F`. All tests use the
physical shell port, retained native yaw, supported root and the
unchanged test-row ordering. Nothing is added to the product solver.

For a bounded oracle, calculate `B=FE(EᵀRE)⁺EᵀFᵀ` and
`B0=FS(SᵀRS)⁻¹SᵀFᵀ`. Since `span(S)⊂range(E)`, `B0≤B`.
Report the maximum generalized eigenvalue of `(B,B0)` and the
maximum amplification `||LEq||²_R/||Eq||²_R` over the nonkernel image.
The ambient broken-space dual `A=FR⁻¹Fᵀ` is a separate, generally
larger quantity; growth of `A/B` does not falsify this supported
reachable-image construction. Also report the root port trace/R energy
and a beam-only nodal-interpolation root-ramp comparator to illustrate
the boundary energy. The latter is not a moment-preserving alternative
lift and enters no dual inequality.
Finite flat ratios here are necessary evidence for a local stable
lifting, not a uniform proof or line-law selection. The K4 moment
inverse is a banded one-dimensional mass problem whose inverse is
generally global; the present dense diagnostic does **not** establish
a fixed-stencil local lift. The local-dual translation pairing is
diagonal. Locality and sparse execution need separate derivation.

## Frozen executable inventory and checks

Run Q4 and S3-V2D with `(Nb,Ns)=(4,4),(8,8),(16,16),(8,1),(8,64)`:
ten cases in total. For each, test K4 and local-dual functionals.
Use the prior registered source identities, physical scales and mesh
overlay. Eigen cutoffs relative to the maximum scaled graph eigenvalue
are `1e−12,1e−10,1e−8`; preserve rank and sensitivity, never silently
drop a test row. Compare both load-independent channel moments and
root traces at all cases.

Required numerical checks per case: exact supported shell boundary
values and shell-port root translations `≤1e−12` error; `S` is in
`range(E)` by construction; graph pullback and `FE=C` relative
`≤1e−10`; row-moment parity `||FLE−FE||` relative `≤1e−9`;
`B0` and `B` are positive definite on the full registered test rows;
`B−B0` has no materially negative eigenvalue (`≥−1e−8` relative
to its spectral scale); oblique-projector idempotence `||LS−S||`
relative `≤1e−9` (not R-orthogonality);
numerical-null action at the smallest `1e−12` cutoff `≤1e−8`, with
dropped-subspace action at all three cutoffs reported separately;
and finite outputs. Keep the signed full
retained KKT, loaded physical response, and continuous gap as separate
mandatory F03 requirements. An algebraic failure is preserved, not
converted into a favorable ratio.

Run serial child processes with one BLAS/Numba thread, sampled child
RSS ≤8 GiB, 900 s/case, 7,200 s total. Preserve exact source and
dependency identities, import paths, previous-evidence hashes,
stdout/stderr, all case work/resources, and failures under
one exclusive root. Independent post-run raw/mechanics review is
required. At the common `1e−10` cutoff, flag an adverse growth screen
if either `B/B0` or the maximum lift-energy amplification increases by
more than `2×` on either joint doubling `4/4→8/8→16/16`. Report both
ratios at all three cutoffs and the fixed-eight shell reaches even if
the growth screen does not trigger. Rank, kernel, moment or port
failures falsify the construction; the growth screen rejects a claim
of resolved finite-mesh stability and requires further analysis.
Passing finite
checks does not accept a multiplier law, supply the missing converged
external/independent physical target, or permit G1 production work.
