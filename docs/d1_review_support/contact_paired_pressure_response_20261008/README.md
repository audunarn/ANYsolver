# Paired pressure response development

This diagnostic consumes the existing finite Q4 contributor and the actual consistent corotational structural tangent. It changes no contact law, constraint, support, pressure space, state or admission criterion.

## Equations and norms

P is the literal complement of static boundary conditions and prescribed unit nodal path controls. All angular triplets are entirely free or excluded. Define K=P.T(Kstruct+Kcontact_fixed_z)P, B=Gspin P, G=Gchart P. Solve K D=B.T; A=G D. B maps supported force coefficients to **unconstrained spatial residual loads**, including nodal couples. G maps additive chart perturbations to normalized weighted gaps. Their distinction and K's nonsymmetry are retained. This is not a symmetric LCP or a Gram-rank substitute.

Each pose records every positive moving overlap support S. The pressure probe is dz=(Fref/sqrt(Aref))*sqrt(S)*alpha; lambda=dz/S. Its declared dimensionless lumped pressure norm is sqrt(Aref)*sqrt(sum S lambda^2)/Fref. S is frozen during the local directional diagnostic, not silently differentiated as a normalization. This is a lumped Q1 norm, not a claim that it equals the consistent squared-field integral.

Translations use Lref=1 m and spatial forces Fref=1e-4 N; rotations use 1 rad and spatial moments Mref=1e-4 N m. Aref=1 m^2 is the registered nominal full-source reference area, shared across meshes. Bhat uses separate force/moment row scaling; Rhat uses chart displacement/angle scaling; Ahat=Fref/(Lref*Aref)*sqrt(S) A sqrt(S). Khat, dimensionless solve backward error, singular values, weakest signed modes and response reconstructions are saved. Raw mixed-unit solve error is only an algebraic check. Floating-point SVD resolution is not a universal physical cutoff. No eigenvalue coercivity, pressure acceptance or mesh-uniform stability follows from these numbers.

## Matched physical comparison

The base input is an authenticated immutable 60-degree sliding pose from the completed per-surface-frame workflow. Its outer checkpoint is an input fixture only; it is not resealed or continued under the new package. Existing mechanical payload identities are inspected for reuse.

The single refinement splits source X cells from two to four: pressure nodes6->10 and source structural elements2->4. Target remains four Q4 elements. This changes source structural and pressure spaces together, so it cannot isolate pressure-resolution error. Physical anchor/load locations, skins, material, history and scientific tolerances remain fixed. An explicit ordinary pair preserves the original pressure integration side; automatic area-tie behavior is not tested or renamed to force a role.

Two shared source-material X bins are integrated with independent exact-binary Fraction Q1 rectangle formulas. These are FULL-reference numerical pressure traces, including portions outside contact. They are not physical bin forces or reactions. Actual physical resultants/moments and common-material-node normal displacements are reported separately. No bin-force or spatial-convergence pass gate is asserted without an independently matched overlap-supported physical integration. Physical rims/corners and generic pressure/spatial qualification remain open.

See OUTCOME.md for results and IMPACT.md for source/evidence reuse. Full commands, source snapshots, private packages, runtime and retained failures are under C:/ANYworkspaceWork/contact_paired_pressure_response_20261008.
