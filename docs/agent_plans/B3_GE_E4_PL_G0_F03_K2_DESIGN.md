# F03-K2: physical line-response and stability design

21 September 2026. **Design, not a frozen execution registration or a
mechanics pass.** The independently adjudicated K0, D1 and K1 evidence
narrows the next experiment. K0 found no acceptable multiplier space; D1
identified a broader finite-pose derivative plateau and conditioning-driven
forward-solution sensitivity; K1 found full row rank for five reduced spaces
but unsupported trace modes in 129/130 matrices. None closes F03/G0.

## Scope and comparison choices

Use K1's actual native retained B3 and physical in-plane Q4/S3-V2D shell
fixtures and exact weak KKT, retaining the signed `-S_r` reduced block.
Advance **P1-beam** and **P1-shell-grid** to a physical comparison because
they cover opposite reciprocal mesh-ratio extremes. Preserve P0-shell-grid
as an explicit near alternative: it has fewer scalar rows and lower maximum
row incidence in K1, but three fewer trace constraints per mesh. The K1
rank score does not select either production law.

Compare the same 18 three-level core meshes (`N_b=4,8,16` and
`N_s/N_b=.5,1,2`) and eight one-level reciprocal reach meshes (`N_b=8`,
`N_s/N_b=.125,.25,4,8`). The reach is an adversarial screen, not a
three-level 1:8 convergence claim. All reference geometry, supports,
section axes, material properties, shell trace frames, multiplier knot
interpretation, and stiffness operators remain fixed. Keep only cases
where the actual symmetric work-scaled reduced physical `K_e` is positive
under a preregistered criterion. Record negative and indefinite outcomes;
do not regularize or symmetrize them.

## Fixed physical loading and observables

Use two continuum load densities with the same phase and amplitude at
every refinement level, applied to the *actual native lifted beam trace*:

1. `f_y(s)=f0[1+.25 cos(2πs/L0)]` N/m, the existing smooth K0 case.
2. `f_y(s)=f0 sin(2πs/L0)` N/m, a signed load with fixed wavelength
   `L0=1 m` and `f0=10^6 N/m`.

Split quadrature at all beam, shell-host/diagonal and multiplier knots.
Validate integrated loads with a higher-order independent quadrature on
every mesh and freeze force/work normalizations based on `f0 L0` and
`W0=f0 u* L0`, or on a separately declared integrated absolute/L² load.
The signed sine load has zero net force, so its resultant is not a valid
normalization denominator.
The K0 half-cell alternating `(-1)^j` density changes physical wavelength
as `N_b` changes. Retain it, if useful, **only as a separate varying-load
stress test**, never as a convergence sequence for one continuum problem.

At identical physical stations and frames compare the beam axis, shell
sample poses, support reactions, total force/moment, interface virtual work,
physical shell energy, multiplier traction projections, and the full
pointwise and `L²` gap fields. Record step-free linear solution and all
solver work, factorization warnings and failures. Use at least three core
levels for physical refinement, with a distinct resolved/analytical or
executed external reference for accuracy claims. A small dense oracle
checks the bounded assembled KKT. The forward differences of ill-conditioned
full/condensed solves require a stated error budget alongside backward
residuals and condition estimates; D1 does not waive K0's frozen `1e-10`
parity failure or permit post-hoc threshold changes.

## Two distinct stability questions

The K0 generalized eigenvalue floor of `C_l K_e⁻¹ C_uᵀ` relative to
`L²` multiplier mass is a valid *conditional discrete inf-sup square* for
that particular pair of norms **if** `K_e` is SPD and the coordinate
coupling is symmetric. Its load-independent decay is real under those
assumptions. It is not a stability result for the exact retained native
KKT: eliminating retained variables also produces `-S_r` in the multiplier
block, and the original retained tangent is indefinite.

Derive and review a mesh-independent traction Riesz map before freezing an
additional conditional metric. One proposed definition for the planar
metre-valued gap `(Δu_x,Δu_y,ℓΔθ_z)`, `ℓ=.46 m`, is the Neumann spectral
realization of `(I−L0²∂²_s)^(-1/2)` on `[0,L0]`, including its constant
mode. With multiplier basis `φ_i`, define

```text
H_ij = ∫ φ_i (I−L0²∂²_s)^(-1/2) φ_j ds
H_full = H_scalar ⊗ I3  (basis-major, three gap channels per basis)
||λ||_Q² = λᵀ H_full λ / (f0² L0)
||q_p||_V² = q_pᵀ K_e q_p / W0,  W0 = f0 u* L0
u* = f0 L0/(Et)
β_h² = (f0/u*) λ_min(C_l K_e⁻¹ C_lᵀ, H_full)
```

The last equality requires `K_e` SPD, `C_uᵀ=C_lᵀ`, finite positive
`H_full`, and physical units consistent with the assembled coordinate rows.
The `I3` ordering must match `np.kron(basis[:,None],trace)` after
`ℓ=.46 m` converts the rotational gap into metres and the multiplier
coefficients into the conjugate line-traction basis.
`H_full` must come from the *frozen continuum norm*, not the measured Schur;
never rescale each mesh to flatten β. Specify analytic basis projections,
spectral truncation and quadrature/error limits, boundary conditions,
constant-mode treatment, and a units-change check. The use of `H^-1/2`
for this offset Procrustes trace still requires a separate derivation of
uniform trace/norm equivalence. It is a **conditional physical-primal
diagnostic**, not full mixed inf-sup acceptance.
Without a reviewed uniform trace-continuity/norm-equivalence derivation,
report β only as an exploratory conditional diagnostic and do not set a
mechanical passing threshold for it.

The proposed dual norm is informed by standard mortar interface theory,
where a multiplier acts in the dual of a trace space; its hypotheses do not
automatically hold for this shell pose functional. The beam-to-surface
research model uses Kirchhoff–Love shells and ultimately penalty-regularized
coupling, while this programme requires E4-PL shear behavior and exact
multipliers. See [Nitsche mortar error analysis](https://link.springer.com/article/10.1007/s00211-019-01039-5),
[dual mortar analysis](https://maths-people.anu.edu.au/~lamichh/Thesis/lamichhane_thesis.pdf),
and [Steinbrecher et al. beam-to-surface coupling](https://link.springer.com/article/10.1007/s00466-025-02647-9).

Separately derive a positive native-primal norm and stability criterion
for the full retained saddle system, including its exact signed `S_r` and
constraint curvature in the eventual nonlinear form. Do not infer full
stability from the conditional floor, raw Euclidean KKT singular values,
rank, a penalty comparator, or one smooth load.

## Registration prerequisites and decisions

Before K2 can run, freeze the two candidate spaces, mesh/load inventory,
physical quadrature and output projections, derivative step from D1 with
an independent plateau check, primal and multiplier norms, spectral
realization and its numerical error bounds, source/dependency identities,
one-thread environment, resource limits, evidence grammar, and thresholds.
Obtain an independent mechanics review of the norm and exact signed system
and an independent code/evidence preflight. A negative result is preserved
under its one-shot registration; it cannot be replaced by a penalty or a
different load while keeping the same evidence identity.

Even a favorable K2 outcome would only prioritize a formulation for the
full six-channel, eccentric, curved, torque, transverse-shear, drilling,
thickness, junction, reciprocal-refinement and independent-reference F03
programme. G0B still blocks G1 production integration, and G1–G6 remain
mandatory for the complete release.
