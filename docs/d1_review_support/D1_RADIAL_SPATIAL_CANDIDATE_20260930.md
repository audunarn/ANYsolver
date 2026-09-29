# D1 guided two-body radial spatial candidate

**30 September 2026. Prospective development/acceptance proposal; not yet frozen.**
This is one representative spatial-response fixture, alongside separate
free-director work, lifecycle, analytical code and pressure-family evidence.
It neither qualifies ordinary bending response nor changes the shell model.

## Mechanical inputs and reference

Use `build_radial_guided_case(target_cells=12)` in the existing parameterized
runner. Source: 12×12 qualified Q4, [0.1,1.1]² m; target: 12×12 congruent
rectangular cells split into S3 V2D, x=[0,1.3], y=[−0.113,1.2] m.
Both use isotropic elasticity, thickness 0.05 m, ν=0.3; source E=10⁵ Pa,
target E=5×10⁵ Pa. Keep the declared physical skins and target 0.01 m offset.
All in-plane translations and directors are prescribed; transverse interior
motion is free on both bodies. Two ordinary path controls and affine MPCs
ramp the independently derived continuous boundary traces from zero.

Uniform downward source load is 0.08 Pa (0.08 N), with consistent Q1 nodal
loads. Two equal path steps ramp load and traces together. Disk centre is
(0.6,0.6) m, contact radius a=0.35 m, outer reference radius R=1 m.
Physical initial separation is 7.741263872132846×10⁻⁶ m.

The exact radial reference is `d1_radial_two_body_reference.py`, independently
derived from Ds Δws=F−p and Dt Δwt=p with complementarity. Source
Ds=1602.5641025641025 N/m. Retain the actual S3 guided block's MIN3 factor:
φ²≈0.3942384633669111 and Dt=3158.962046209225 N/m. The reference pressure
is uniform inside the disk, p=F Dt/(Ds+Dt); force is
0.02042556989989151 N. Moments about the disk centre are zero.

This is a **frozen guided operator** at these mesh/material inputs. Target4
and target12 have distinct MIN3 coefficients; their comparisons do not show
convergence to one common target4 operator. Continuous analytical Dirichlet
traces define the benchmark. Their nodal interpolation belongs to spatial
error. The independently tested boundary bound concerns displacement, not an
inferred force uncertainty. Reference evaluation error must be recorded.

Development discriminator: the independently clipped linear QP gives 0.9292%
force error, versus 14.43% on target4. The actual nonlinear structural owner
matches the zero-state guided normal tangent to 1.47×10⁻¹⁶ and differs from
the linear first-step normal force by 7.14×10⁻¹¹ relative. These are setup
checks, not nonlinear contact acceptance.

## Prospective observables and scales

Use fixed world bins x/y=(0.1,0.6,1.1) m, four quadrants. Also retain 4×4
bins as resolution diagnostics, without a new universal pressure-field gate.
Exact bin forces are p times disk∩bin area. Report numerical nodal pressure
and reference-area Q1 integrals distinctly from recovered physical traction.
Before using these integrals for force-bin assessment, measure their total
force/moment difference from the complete physical work map; it must consume
at most 0.2% of the registered force/moment scales (one tenth of the 2%
response tolerance). Total conversion agreement alone does not bound local
bin conversion; retain that independent assessment before a physical-bin claim.

Freeze Fref=0.08 N, Mref=0.08 N m about O=(0.6,0.6,0) m,
Lref=1 m and centroid length scale a=0.35 m. Materially nonzero force means
|Fz|>10⁻⁶ Fref=8×10⁻⁸ N. Otherwise report no resultant position and use
absolute error normalized by Fref rather than division by the open force.

Required final-state spatial predicates:

- Vertical contact force relative error ≤2% against the exact disk force.
- Four-bin force L1 and L2 errors ≤2%, normalized by the corresponding exact
  bin-vector norms. Report every individual bin and the 4×4 diagnostic.
- Contact moment error ≤2% of exact force×Lref, and resultant-position
  error ≤2% of a when force is materially nonzero.
- Source displacement at (0.6,0.6), (0.6,0.85), (0.6,1.0) m differs by ≤2%
  from the exact nonzero field; report target displacement at the same points.
  Both fields and their interpolation conventions are retained in raw output.
- Independent physical gap meets 50 µm; equilibrium, complete support/load
  wrench balance and contact action/reaction meet 10⁻⁶ with separate Fref/Mref.
- Monolithic complementarity ||C||₁/Fref≤10⁻⁸. Integration contribution is
  at most one tenth of the response error budget. No pressure on source rims
  or prescribed normal modes; all positive source-face overlap remains wholly
  covered by the target union. Existing clipping/derivative guards stay active.

The current-skin/nonlinear difference needs an explicit bound or matched
same-discrete independent comparison; structural zero-state agreement alone
does not supply it. An observed force-only pass cannot close all predicates.

## Execution and disposition

One candidate, no automatic mesh campaign. Keep the existing 14,144 energy
evaluation cap; conservative candidate-based counting may replace Cartesian
worst-case admission only after exhaustive parity and runtime-cap checks.
Routine preflight/reference checks: 180 s/1 GB. One named coupled run:
900 s/4 GB process tree, exclusive outputs, max18 Newton iterations and the
existing explicit cutback policy. No tolerance change or budget increase.

Before a claim-bearing run, independently review this specification, bind
exact source/input/reference/environment identities and freeze output paths.
A failed gate remains failed; classify the discrepancy and choose one
discriminating corrective action. Installed, transaction, no-contact and
finite pressure-family assessment remain separate D1 obligations.
