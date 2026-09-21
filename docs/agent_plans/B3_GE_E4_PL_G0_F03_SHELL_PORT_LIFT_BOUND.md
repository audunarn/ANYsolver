# F03 planar shell-port lifting bound and banded moment application

22 September 2026. **Mathematical contract for the registered planar
trace family, pending independent mechanics review.** This derives a
mesh-independent bound for the supported shell-port compression in
the *positive broken-trace norm*. It is not a signed native KKT
inf-sup proof, a six-channel formulation, a loaded reference, or
permission to begin G1.

## Exact scope and spaces

The straight attachment is `s∈[0,L0]` with `L0=1 m`. Let uniform native
half-cells have width `h=1/Nb` in the current one-metre fixture,
with Nb even. The existing executable fixture verifies Nb=4,8,16;
the bound for other even Nb is **conditional** on extending the same
straight two-half-cell native trace and test-row formulas. The fixed beam root
translations are zero; the panel has its two outer x edges fixed,
while the physical four-sample shell pose at `s=0` is free. Each
shell trace is constructed from the existing Q4 or S3-V2D in-plane
nodal translations at a flat reference. Its four sample x positions
are `s±.2 m`, and its yaw is the actual centered proper-fit
derivative. The shell mesh has integer `Ns≥1` and nodes at `x=.5 m`.
The native beam translational trace is continuous P1 on its half-cells,
and native retained yaw is P0. The shell centroid/yaw traces are
continuous and piecewise affine on the reference overlay. Thus the
scaled physical gap `w=(g_x,g_y,ell*g_yaw)`, `ell=.46 m`, has two
continuous H1 translation channels and a broken H1 yaw channel whose
only value jumps occur at native half-cell boundaries. This is an
assumption about the admitted *linearized planar trace*, not a generic
finite-rotation or curved-member theorem.

The existing local Riesz assembly exactly represents

```text
||w||_R² = Σ_overlay ∫ (|w|²/L0 + L0 |w'|²) ds
          + (L0 Nb) Σ_native interior |[w_yaw]|².
```

Here the third component already includes `ell`. No nodewise yaw
continuity is imposed. The registered local-matrix/source parity and
affine-overlay checks establish this finite-element identity in the
ten frozen cases; the argument below uses its exact piecewise form.
At the fixed `L0=1` of this fixture, `L0 Nb=1/h` numerically. The
source's jump coefficient must be rederived for a different length;
this note makes no unit/general-length assertion about it.

## Supported root ports and their bound

Let `p(x)=2(1−|x−.5|)` for `x∈[−.5,1.5]`, with `p=0` at both fixed
outer edges and a kink exactly at the shell node `x=.5` for every
integer Ns. Two supported physical shell nodal fields move only x
or y with amplitude `−p(x)`, independent of y. Q4 interpolation of
an x-only P1 field and S3 affine interpolation represent the same
piecewise p exactly. Their *actual* shell pose derivatives give
gap ports `P_x,P_y`; the y port may induce a nonzero yaw and that
yaw is retained. Their translational trace at the root satisfies

```text
[P_x,t(0) P_y,t(0)] = I₂,
χ(0) = (p(−.2)+p(.2))/2 = (.6+1.4)/2 = 1.
```

Since p is Lipschitz with fixed slopes `±2` and the sample window,
ell and L0 remain fixed, both ports have bounded R norm independent
of Nb, Ns and Q4/S3 topology. They have no native yaw jumps. For
any continuous translation `w_t`, an endpoint trace estimate follows
by integrating `w_t(0)=L0⁻¹∫w_t−∫(1−s/L0)w_t'` and Cauchy–Schwarz:

```text
|w_t(0)|² ≤ (2/L0)||w_t||²_L2 + (2L0/3)||w_t'||²_L2.
```

Consequently `c=w_t(0)` and `||P c||_R ≤ C_port ||w||_R`, with
`C_port` independent of mesh counts. Choosing a shell port supported
in a *fixed number of shrinking mesh cells* would invalidate that
constant. A beam-rooted P1 field alone cannot represent `c≠0`
at the root at all. Matching its nodal values or moments away from
the root instead creates a first-cell ramp with derivative energy
proportional to `1/h`; this is why the physical shell root port is
essential.

## Moment-preserving compression

Subtract the ports and set `v=w−P c`, so `v_t(0)=0`. For each
translation channel, define `Q_h v_t` in the rooted continuous P1
space by the Nb moment equations against the registered K4 P1 test
functions on free native nodes. This is the L2 projection onto that
space. Alternatively use the registered local-dual tests, whose
cellwise polynomials pair biorthogonally with the nodal P1 functions.
For scaled yaw, define `A_h v_yaw` as its P0 average on each native
cell. The compressor is

```text
Lw = P c + (Q_h v_x, Q_h v_y, A_h v_yaw).
```

The beam nodal/cell traces used here are the actual native columns;
in particular, the P0 yaw is a retained cell rotation, not a nodal
shell drilling coordinate. This L preserves `w_t(0)` and every row
of the existing K4 or local-dual functional F, with no condition at
the free tip. It is an **oblique** projection onto the span S of two
shell ports, rooted native P1 translations and retained P0 yaw:
`L²=L`, `L|_S=I`, and `FL=F` on the reachable trace image.

For K4, one-dimensional rooted nodal interpolation `I_h v_t` obeys
`||(I_h v_t)'||_L2≤||v_t'||_L2`. On each cell the error
`e=v_t−I_h v_t` vanishes at its endpoints, so
`||e||_L2≤(h/π)||v_t'||_L2`. The L2 projector is a contraction,
reproduces `I_h v_t`, and the uniform P1 inverse bound
`||q_h'||_L2≤√12 h⁻¹||q_h||_L2` yields
`||(Q_h v_t)'||_L2≤(1+√12/π)||v_t'||_L2`.
It is also L2-stable. These constants do not depend on Nb.

For local dual, the translation moment matrix is diagonal with
interior entries h and tip entry h/2 (the root row is absent).
Its test functions have uniformly bounded coefficients and at most
two-cell support. It reproduces the rooted nodal interpolant.
For `e=v_t−I_h v_t`, each coefficient of the local-dual image is
bounded by `C h⁻¹/²||e||` over its two-cell patch. Bounded patch
overlap, the same interpolation error and the P1 inverse estimate
give `||Q_h e||_L2≤C||e||_L2` and
`||(Q_h e)'||_L2≤C||v_t'||_L2` with mesh-independent C. No exact
constant is claimed for this branch.

The yaw cell-average map contracts the L2 norm and has zero
within-cell derivative. At a native interface, write the difference
of its adjacent averages as the actual yaw jump plus the two
endpoint-to-average errors. On a cell, the square of each such error
is at most `(h/3)∫|v_yaw'|²`. By the three-term square bound,

```text
(L0 Nb) Σ|[A_h v_yaw]|²
  ≤ 3(L0 Nb) Σ|[v_yaw]|² + C Σ∫|v_yaw'|²,
```

with C independent of Nb. Port yaw is continuous and H1 bounded,
so subtraction does not create new physical jumps.

Combining the endpoint, fixed-width port, translation and yaw bounds
gives `||Lw||_R ≤ C ||w||_R` with C independent of Nb, integer Ns,
and Q4/S3 within the stated straight linearized geometry and
uniform native mesh. This is an analytical boundedness statement
for the reachable trace R norm; the finite ten-case experiment
supports the algebra and has no `>2×` adverse growth, but is not
the proof itself.

## Dual consequence and sparse application

Let `Y=range(E)`, `S=range(L)⊂Y`. For any multiplier vector λ,
the dual quadratic forms defined by the R norm are

```text
λᵀBλ  = sup_{w∈Y} (λᵀFw)²/||w||²_R,
λᵀB0λ = sup_{z∈S} (λᵀFz)²/||z||²_R.
```

The subspace relation gives `B0≼B`; moment preservation and the
bounded lift give `B≼C²B0`. This equivalence is for the **reachable
image**, not the ambient DG dual `FR⁻¹Fᵀ`, which had an adverse
non-equivalence trend. It does not establish a lower bound for the
full signed retained KKT or select K4 versus local dual.

The translation moment application needs no dense model-wide matrix.
K4 has the rooted P1 mass matrix: diagonal h/3 at the free tip,
`2h/3` at interior nodes, with adjacent off-diagonals h/6, except
the first free node for Nb=1. A tridiagonal Cholesky factor and two
triangular solves use O(Nb) storage and work for each trace vector.
The local-dual matrix is diagonal (h interior, h/2 tip); P0 yaw
averaging is diagonal by native cell. The shell ports are fixed
physical nodal fields and the original F/E assemblies retain their
local overlay support. The *inverse* K4 mass matrix is generally
dense, so this is a banded solve/apply, **not** a fixed-stencil
local operator or permission to assemble a dense projector.

## Remaining qualifications

Review must verify each trace-continuity and norm assumption through
the actual source mappings. Next verify the banded/diagonal application
against the frozen dense oracle on the registered cases and measure
its work without a dense global projector. A physical load-response
reference still needs endpoint law, matched shell/section idealization,
independent beam/shell/mortar refinements and a continuous-gap bound.
The full curved/eccentric six-channel pose, torque/shear, material
updates, signed KKT and production sparse assembly remain separate
mandatory F03/G0–G6 obligations. This note alone closes none of them.
