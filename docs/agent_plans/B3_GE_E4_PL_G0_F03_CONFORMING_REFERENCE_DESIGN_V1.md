# F03 conforming classical-reference design v1

23 September 2026. This is a **preparatory mechanics contract**, not a
registered execution, a native B3-GE/E4-PL interface law, or evidence that
F03/G0B passed. The consumed F03 attempts and the failed saved-action screen
remain unchanged. The finite-square attachment below is the previously
declared independent *classical reference* law. Its purpose is to test whether
a locally supported shell approximation can converge physically without
changing that law, the three root-pose constraints, or the frozen acceptance
criteria.

## Approximation and physical operator

Use the same panel, four fixed physical pads, section, load and supported
edges as the primal Ritz reference. Let `V0` be the two-component in-plane
`H1` space with zero displacement on both supported `x` edges. Derive the
geometry-fixed partition separately from the actual pad constants of each
declared representation stream; do not round binary64 breakpoints to the
nominal decimals. The nominal stream has 9-by-5 rectangles. Use conforming tensor `Qp`
fields with shared nodal values and exactly those essential edge values
eliminated. The first **design** levels are `p=1,2,3` (96, 374 and 832 free
scalar coefficients for the two components together); these are not yet an
execution inventory or a claim that `p` refinement resolves the mixed
boundary singularities. A separate registered `h` sequence may be necessary.

For station `s` in `[0,1]`, let the four pads have local coordinates
`(xi,eta)` in the squares centred at `(±0.2,±0.23)`, each with halfwidth
`a=0.05 m`. Their total area is `S=16a²`. The physical pose is

```
A(u)(s) = (1/S) sum_pads integral_pad
          [u_x(s+xi,eta), u_y(s+xi,eta),
           (xi*u_y(s+xi,eta)-eta*u_x(s+xi,eta))/J] dxi deta.
```

Preserve the originally represented `J` and its corresponding rigid-yaw
gain `gamma=J_geom/J` in a faithful comparison stream. An intended-rational
geometry stream with `gamma=1` is distinct and must be labelled. In
particular, an apparent yaw defect must not be removed by substituting a
new `J` into one side of a comparison.

The shell form is the original plane-stress membrane energy
`a_s(u,z)=t integral eps(u):D:eps(z)`. The beam uses exactly the mapped
physical pose `(U,V,Theta)=A(u)` and strains `(U',Theta',V'-Theta)`; its
axial, bending and shear energy is integrated over `[0,1]`. Apply the
unchanged smooth beam load and impose only `A(u)(0)=0` with three physical
root multipliers. No beam slope or tip constraint is added. The assembled
system is the symmetric saddle point form from `a_s+a_b` and these three
rows; the shell form is coercive on `V0`, while root-row independence must
be **measured and independently witnessed** for every proposed space.

## Exact trace construction and regularity

For every shell basis function, split a pad integral at all intersected
`x` and `y` cell boundaries. In each intersection, integrate the cell-local
polynomial; the moving `x` limits are affine in `s`. Before quadrature,
partition `[0,1]` at every station where a pad's left or right side crosses
a shell cell edge. Within each resulting open station interval the host
incidence is fixed and each pose-matrix entry is a polynomial in `s`.
Build the pose and its first two derivatives from those polynomial
coefficients, independently checking them against boundary/Leibniz
identities. No closest-host search or finite differencing of the pose may
be hidden in the energy assembly.

The box integration smooths this conforming field enough for the beam
bending energy: for a horizontal pad interval `[l,r]`, an `x` primitive
`F(s)=integral_(s+l)^(s+r) u(x,y) dx` has
`F'=u(s+r,y)-u(s+l,y)` and
`F''=u_x(s+r,y)-u_x(s+l,y)` away from the finitely many crossing stations.
The one-sided formulas agree in `F'` because `u` is continuous, so `F` is
`H2` in `s`; `F''` may jump. For the yaw primitive
`G(s)=integral_(s+l)^(s+r) (x-s)u_y(x,y) dx`, use

```
G'  = r*u_y(s+r,y)-l*u_y(s+l,y)-integral u_y dx,
G'' = r*u_y,x(s+r,y)-l*u_y,x(s+l,y)
      -u_y(s+r,y)+u_y(s+l,y).
```

The `-eta*u_x` part follows the first identity. These identities also
apply under the fixed `y` integral. Evaluate cell-edge values one-sided;
do not treat a derivative jump as a physical discontinuity or change the
pad-to-material correspondence.

`p+1` tensor Gauss points integrate the cell-local shell energy exactly.
On each fixed-incidence station interval, construct the beam pose polynomial
and integrate its energy exactly by coefficient arithmetic or at least
`p+3` Gauss points, with an independently evaluated higher rule. The
weighted yaw pose can have degree `p+2`; the squared shear strain can
therefore have degree `2p+4`, which `p+3` points integrate exactly.
The cosine load is nonpolynomial and retains the predeclared 48/64 rule
comparison **on each station interval**, rather than over the whole
piecewise-polynomial range in one rule. A second, independently implemented pad-moment calculation
must check pose, derivatives and virtual work; reusing the production
trace matrices to check their own adjoint is insufficient.

## Sparse assembly and necessary preflight

The global scalar field uses shared `Qp` nodes. Assemble shell and beam
energy with local scatter into a sparse matrix, keeping the three root
rows separately. Pad width remains fixed in metres while the field is
refined. A node's beam support is limited by its physical influence along
the moving pads; record matrix `nnz`, bandwidth and peak memory. A dense
matrix is permissible only as an independently assembled *small* oracle.

Before any equilibrium run, require these bounded checks:

1. Exact support elimination and `C0` continuity on every internal edge;
   no duplicate or orphan scalar DOFs.
2. Positive shell energy on nonzero admitted fields and three independent,
   dimensionlessly scaled root rows, with an explicit rank witness.
3. Fixed-reference rigid translation/yaw gains, including the represented
   `gamma`, and dimensionless rank six of the stacked pose and derivative
   rows `[A(0); A'(0)]`. This checks that none of the three beam-root
   derivative channels is inadvertently fixed by the three pose rows.
4. Pose, first/second derivative and adjoint-work agreement for fixed
   basis vectors, virtual fields, and random signed combinations.
5. Shell/beam energy and load assembly agreement with independent small
   dense quadrature; conservative matrix symmetry and a directional
   energy derivative plateau.
6. Pad-coverage, moving-boundary and station-breakpoint checks, including
   the exact boundary stations and both one-sided evaluations.
7. An explicit resource estimate under the original applicable limits;
   registration must precede any scientific run.

The initial `Qp` levels are a design screen, not a selection rule. A
failure of rank, work, or resource checks ends that candidate; it does
not justify changing the attachment, adding a penalty, relaxing the
numerical criterion, or silently increasing the frozen budget.

## Physical residual and convergence decision

For a piecewise `C0` Ritz state, let `T=t D eps(u)`, `f_mu=A*mu`, and
`r_K=div(T)+f_mu` in each rectangle. On an internal edge with outward
cell normals `n+`, `n-`, retain the traction jump
`j_e=T+ n+ + T- n-`. For every `z` vanishing on the supported edges,

```
<mu,A z> - a_s(u,z)
  = sum_K integral_K r_K . z
    - integral_top+bottom (T n) . z
    - sum_internal_e integral_e j_e . z.
```

The internal edge term is numerical residual, not a material-interface
load. Recover it and the fixed-pad adjoint from independent operators;
otherwise a piecewise field can appear more balanced simply because a
jump was omitted. The support-reaction identity must likewise include
cell residual, free-boundary traction and interior jumps when a declared
lifting is used. Preserve signed force, moment, work and origin terms.

Physical acceptance still requires the registered energy, full
functional, tip pose, support reaction and interface work to settle on
at least three systematic refinement levels, with near-zero floors and
matched idealizations. Strong-residual localization is diagnostic, not a
solution-error percentage. Passing a small-rank or assembly screen does
not qualify the native line multiplier, shell drilling/torque transfer,
F03, or G0B. Any scientific continuation needs its own immutable source,
case, threshold, resource and one-use evidence registration followed by
independent mechanics review.

## Current preparatory implementation boundary

The separate `_b3_e4_f03_conforming_q1_trace.py` helper implements only
the nominal-geometry Q1 pad trace and its first two one-sided station
derivatives. The grid breakpoints are constructed from the represented
pad constants. Its bounded tests compare against independently integrated
cell monomials, rigid fields, finite-difference derivatives and virtual
work, check all represented station crossings, and test six dimensionally
scaled root pose/derivative rows. The last focused run passed **15/15**
tests. Independent read-only mechanics review found no blocker for this
*preparatory trace* scope after corrections.

The separate `_b3_e4_f03_conforming_q1_energy.py` candidate then assembles
sparse shell and mapped beam energy, three root rows and the smooth load,
and performs one bounded saddle-point solve. Its 4/6-point beam and
48/64-point load comparisons are per station interval. The corrected
solve requires finite small comparison differences, positive scaled shell
energy, symmetric blocks and six scaled root pose/derivative rows before
factorization. The combined trace/energy focused suite passed **23/23**
tests. Independent read-only review found no mechanics sign or scatter
error in the normal `assemble()` to `solve()` path.

These two helpers are not the complete design preflight: they have no
independent polynomial derivative oracle, no independent support-reaction
recovery, no systematic refinement or physical convergence study, and no
registered scientific execution. Their operator records are preparatory,
not immutable provenance certificates: replacing a matrix, load or root
row after assembly can decouple a stored comparison from the problem
solved. Only the unmodified `assemble()` to `solve()` path was reviewed.
The trace's near-edge floating-point snap is applied only at declared
represented crossing stations to resolve one-ulp closure; the one-ulp
station intervals themselves retain their weight but use a limiting
binary64 evaluation, not an exact polynomial integral. An exact rational
breakpoint implementation would be stronger. No F03 multiplier space is
selected and G0B remains open.

The subsequent generic `Qp` trace at `61e6f655` covers `p=1,2,3` with
shared nodes, represented crossing intervals and one-sided derivatives.
Its combined Q1/Qp trace tests passed **24/24**. The Qp energy candidate at
`79d1f6a1`, with numerical return gates at `34519ce2`, uses sparse
tensor-cell shell energy, mapped beam energy, three root rows, and
per-interval 4/6, 5/7 or 6/8 beam-order comparisons and 48/64 load
comparisons. Its eight focused tests passed; three affected guard tests
passed after the final nonnegative-metric change. Independent read-only
review found no mechanics or numerical-return blocker for the bounded,
unmodified `assemble()` to `solve()` path. The Qp solve now rejects
excessive scaled equilibrium, root-compatibility and energy/work defects.

The Qp tests establish p1 parity with the separate Q1 implementation and
exercise p2/p3 random piecewise fields on a small custom grid. They do
not independently reconstruct the finite-pad beam trace for arbitrary
piecewise fields. Default 9-by-5 p2 and p3 assembly/solve completed as
unregistered exploratory checks, not a resource or physical acceptance
run. No accepted p-refinement sequence, physical reaction/functional
recovery, external comparison, native multiplier selection or G0B closure
follows. Qp operator records remain preparatory and are not immutable
provenance certificates against caller mutation.

An independent bounded piecewise Qp pad-moment oracle at `465e2383`
reconstructs each cell in centered local polynomial coordinates and
integrates clipped rectangles analytically. Its combined focused suite
passed **25/25** tests over p1–p3, the default and two custom grids,
random piecewise fields, pose and first/second derivative work, and a
changed represented `J`. Independent read-only review found no blocker
for this *operator* comparison. It samples selected crossing events,
and finite-precision monomial differences can lose digits on one-ulp
slivers; it is not an exact-rational or physical-convergence proof.

Preparatory signed recovery now has a beam-side distribution at `bf60e02c`
with its tighter virtual-work test at `85947596`, and a cellwise shell
Green-identity recovery at `40962eb8`. The beam tests cover custom p1–p3
and default p1–p2 and require a scaled signed work defect at most `1e-10`;
31 focused and related tests passed. Shell tests cover custom-grid p1–p3,
separately retaining volume, supported/free outer-edge, and interior-jump
channels; 34 focused and adjacent tests passed. Independent read-only
mechanics review found no sign, unit, work, or boundary-normal blocker,
within those bounded scopes.

The separate finite-pad area-adjoint candidate pushes the recovered line
density and root/tip atoms over the four physical pad squares. Its custom
p1 nonrigid virtual-work and force/moment check, p1–p3 zero-field/dead-load
checks, shifted-pad moment check, and fixed 48/64-point cosine comparisons
passed four preparatory tests. Independent read-only review found no
physical formula or sign blocker for the p1 nonrigid work scope. This
preparatory suite took about 17 seconds with batched repeated-x station
integrals and fixed reduced area rules whose observed work agreement met
its bounded test limit. Physical settling, F03, G0B and native interface
acceptance do not follow.

The bounded nodal projection assembles the physical pad-area load on all
shared Qp coordinates and compares it with the independently integrated
line density and atoms. It returns the shell-side nodal residual, six
physical supported-edge work reactions, the distinct beam-root reaction,
and global area/line wrenches. Custom p1–p3 solved-state tests passed
**3/3** in 268.16 seconds total before the area-point streaming change;
the affected p1 test passed afterward in 27.66 seconds. The checks
include 48/64 line projection agreement and represented-`J` moment
balance. Independent read-only mechanics review found no blocker for
that *nodal* scope. This is a
costly preparatory test, not a general resource bound. Default-grid
nodal recovery, area-order convergence, explicit cellwise
`div(T)+f_mu`, combined free-edge and interior-jump residual fields,
physical p/h settling and scientific registration remain open.

A further preparatory spatial wrapper exposes `r_K=div(T)+f_mu`, physical
outer-edge tractions and interior jumps, and combines their signed work
with supported-edge reaction liftings. Its p1 custom-grid random-field
test passed **1/1**. The wrapper requires its own area-order check at
`p+5` versus `p+7` points in x before accepting work; p1 used 6/8 and
met a `2e-10` scaled projected-load/wrench comparison. The earlier
`p+3` default nodal projector exceeded a stricter `2e-9` random-lift
work check by about `4.2e-9`, even though its solved-state case passed;
that observed failure is a quadrature diagnostic, not a relaxed
tolerance. The spatial wrapper's checked order does not establish
p2/p3 or default-grid spatial accuracy, nor physical refinement.
