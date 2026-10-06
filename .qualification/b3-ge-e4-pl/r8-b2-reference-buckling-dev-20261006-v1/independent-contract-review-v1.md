# Independent B2 reference-buckling development contract review

State: completed source/contract Read assessment, with root's subsequent adopted guards recorded below. No numerical imports, jobs, tests, implementation, acceptance or qualification claim. No historical B2 equation/default, scientific criterion or execution authority changed. This is distinct-author OpenAI supporting review; required different-model-family acceptance remains unmet. Root owns scientific adoption and final acceptance.

## Governing development law and reference-work compatibility

The physical B2 route uses its actual force-flexibility operator and scalar or coupled generalized positive-definite section, without the historical shear floor. For a section point rho=(0,y,z), the adopted finite station continuation is chi(s,rho)=r(s)+R(s)rho. Finite endpoint positions and rotations are mapped through their geodesic midpoint frame, the exact existing linear station trace, and finite centerline/director reconstruction. This is a newly declared second-order spectral continuation, not a new public nonlinear B2 constitutive law.

Section data are source-bound explicit (y,z,positive physical area weight,3x6 traction reconstruction map). The map must satisfy sum w [I;skew(rho)] traction_map=I6 in resultant order [N,Qy,Qz,Mx,My,Mz]. It reconstructs the initial S11,S12,S13 stress components; transverse normal/shear stress components S22,S23,S33 are declared zero. Geometry, stress-weighted/Wagner moments and density are not inferred from section stiffness or mass. Normalization fixes first work but does not uniquely determine higher stress moments: distinct self-equilibrated stress reconstructions with identical six resultants may produce different geometric Hessians. Bind the actual reconstruction in identity/provenance.

At the straight reference, the compatible first variations are:

    delta E11 = u' + z theta_y' - y theta_z'
    2 delta E12 = v' - theta_z - z theta_x'
    2 delta E13 = w' + theta_y + y theta_x'

Full symmetric stress contraction and the map normalization therefore give:

    N u' + Qy (v' - theta_z) + Qz (w' + theta_y)
      + Mx theta_x' + My theta_y' + Mz theta_z'.

This matches `_b2_physical_flexibility_linear._pose_polynomials` at source line419, together with its exact trace and strain recovery. Missing the factor2 in shear work, dropping shear traction, or using another resultant ordering would break parity. Geodesic midpoint rigid-motion removal/reconstruction preserves the first station derivative because the existing trace reproduces all six reference rigid fields. Exact parity is still an implementation check, not a source-assessment pass claim.

For an independent scalar work oracle, let a=chi_s, b=R e_y and c=R e_z. At each section datum the initial stress work is:

    0.5 S11 (a dot a - 1) + S12 (a dot b) + S13 (a dot c).

Integrate this over physical reference length and section area using frozen initial stress. Its full second variation includes both products of first field derivatives and initial stress contracted with the second field derivative. It is not merely N times transverse centerline slope products. Constitutive prestress resultants must remain frozen during this differentiation.

## Complete attachment curvature and chart

The adopted shell port is the equal-weight proper polar fit of the same physical vertices used by the reference translation fit. The beam port uses the geodesic-midframe finite continuation of the exact old trace and the physical offset R d. Its first differential must equal the old offset trace. The full multiplier curvature is:

    J.T H_joint(lambda) J + sum_i gradient_joint_i(lambda) H_port_i.

Both shell and beam port Hessians enter exactly once. For an eccentric beam offset, a term F dot [delta theta cross (delta theta cross d)] is generally nonzero; an affine port's zero Hessian cannot justify omitting it. The shell polar-fit rotation likewise has second derivatives even though centroid translation is affine.

Use the objective joint's symmetric Exp-chart `chart_hessian`, not its spatial residual derivative. `_ge_beam3_pose_joint.py:190–198` explicitly distinguishes these. Existing reference constraint C and mixed primal/multiplier blocks remain unchanged. Add only the frozen-multiplier primal curvature to the geometric matrix; do not insert the joint's mixed C blocks a second time or multiply them by the spectral factor.

## Root-adopted initial load and support guards

The initial request admits zero prescribed offset u0 only and Cartesian dead nodal forces only; rotational RHS entries must be zero. Cartesian force potential is affine in actual position and has zero Hessian. Arbitrary fixed spatial couples generally lack a conservative three-dimensional rotation potential; a chart-covector rotational load would require a separately declared potential and checks. No such load is implicitly admitted here.

If future work admits prescribed offsets or fixed prestress, they must not be scaled with the proportional eigenvalue. The required split is K+G_fixed+eta G_proportional, with member resultants, attachment multipliers and shell stresses split consistently. The present zero-u0 guard avoids adopting that additional problem prematurely.

## Root-adopted shell boundaries

Q4 uses its actual reference-linear preload recovery for membrane N and bending M, and the existing qualified geometric kernel. For the explicitly homogeneous through-thickness membrane/bending reconstruction, the physical stress second moment is N h^2/12; it is not stiffness-derived inertia. Shear prestress is refused using prospectively declared arithmetic bounds. Initial stress, geometry/director, units and kernel sign conventions must remain those of the actual Q4 owner.

S3 retains its existing frozen uniform-membrane geometric kernel as an explicitly named thin approximation that omits physical director stress second moment. Admission requires uniform membrane N, zero bending M and zero shear Q within declared arithmetic bounds. It does not claim full sectional Green behavior for S3 or bypass its qualified guards. General S3 prestress remains mandatory open work.

## Discriminating implementation checks and double-count controls

1. Exact old first station/offset differential, static K, attachment C, loads/reactions and profile behavior for scalar and coupled generalized sections. Include oblique frames, offsets, reversal, both bending planes and nonzero multipliers.
2. Independent first/second differentiation of the sectional scalar work above and actual physical joint/port work. Exercise nonzero axial, bending, torsional and shear resultants and the supplied stress-weighted moments; normalization alone is insufficient.
3. Constitutive K once, frozen member stress Hessian once, frozen attachment Hessian once, and original C once. Verify the assembled split against an independently formed total scalar second variation. Do not also differentiate the recovered preload constitutive state while forming the geometric term, or count its already-represented first internal force again.
4. Finite common rigid motion of the actual reconstructed fields. Along a nonlinear rigid nodal path, the objectivity identity includes gradient contracted with path acceleration. Requiring the isolated prestress Hessian to annihilate every linear rigid vector would be incorrect. Keep internal objectivity tests distinct from the full system with fixed Cartesian external forces.
5. Datum covariance: transform section coordinates, reference axis, resultants, traction reconstruction, offsets and constitutive work consistently. Leaving one datum-dependent input unchanged does not test physical invariance. Source-bind and validate the geometry/stress record with its dimensional force/moment conventions.
6. Actual homogeneous Q4 recovery/kernel parity, S3 uniform-membrane admissibility/refusal, zero-u0/zero-rotational-RHS guards, cancellation and immutable snapshot identity. No GE accepted-state machinery may substitute for the physical B2 reference-linear preload.
7. Full supported conservative constrained pencil with original equation/constraint residuals and distinct algebraic multiplier roles, independent small dense checks, analytic physical controls and required refinement. No penalty, mass floor, unverified variable elimination or historical shear-floor reuse.

## Review disposition and mandatory remaining scope

No blocking mechanical contradiction was found in this adopted endpoint/fixed-Cartesian-dead-force development contract. Its reference sectional work is compatible with the actual physical B2 trace under the stated tensor/resultant conventions; implementation and verification remain outstanding. The source checkpoint `docs/reference_cases/stiffened_shell_b2_reference_buckling.md` describes the member/physical-port route and its unresolved breadth; this assessment does not promote it to runtime evidence.

Broader S3 preload, physical director second moments, interior loaded ports/bubbles, line, rigid/distributing footprint attachment curvature and complete F12/B14 reference/external/convergence obligations remain mandatory open work. The current developmental scope is a bounded milestone, not a narrowing or completion of the programme. Installed qualification, complete-spectrum claims and required different-family independence remain separate unmet acceptance boundaries. No numerical authority was consumed by this review.
