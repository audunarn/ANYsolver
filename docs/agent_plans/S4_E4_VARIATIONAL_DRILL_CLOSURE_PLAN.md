# E4-0 open-core and variational drill-route closure

## Authority and scope

This bounded evidence wave supersedes the attached long-range E4 program as
the executable plan.  It starts exactly from E3 closeout commit
`c55ad9e5f8e78b1749c4152e4ba66b6f9e20b198`, tree
`e7e35bb880a88a8f7d736d32652c80442d8b9ec1`.  The attachment is design input
only: 30,628 bytes, SHA-256
`EF02CDFD814F57704EA6CC1972340C09563B35123393645353371EFFC2BCBFC8`.

The run registers only these studies:

- `study_e4_core.wg2020_n7_k0_full_integration_reference_v1`;
- `study_e4_ws.wg2020_local_weak_symmetry_feasibility_v1`; and
- `study_e4_pl.wg2020_surface_reduced_perturbed_lagrange_v1`.

No candidate, selector, serialization token, public API, production dispatch,
or default is created.  Every historical A/B/C, rank-four, E0, E1, E2-A, and
E3 result remains immutable.  E1-R remains a provisional planar-reference
regularizer and E1-RH remains `DEFERRED_NOT_RUN`.

## Shared core gate

The source-closed physical reference is the flat-affine, linear WG2020
Hu-Washizu Q4 with `n=7`, `k=0`, source MITC shear, and positive `2 x 2`
quadrature.  It has 20 physical nodal coordinates, 14 independent
stress-resultant parameters, and 21 independent shell-strain parameters.

In a single constant right-handed element frame, define the node-major
orthogonal split `T5: R20 -> R24` and `QD: R4 -> R24`.  The exact oracle must
prove `T5^T T5=I20`, `QD^T QD=I4`, `T5^T QD=0`, and
`T5 T5^T+QD QD^T=I24`.  The 20-coordinate core must be PSD with rank 14 and
six rigid modes; the embedded core must have rank 14 and nullity ten, exactly
the six rigid modes plus four drill coordinates.  Stationary mixed and Schur-
condensed residual, tangent, energy, physical load work, and physical
resultant recovery must agree.  Loads lie in `range(T5)` and direct drill
moments are excluded.

Core `GO_E4_OPEN_CORE_IDENTITY` is a prerequisite for both branch screens.
Mass, geometric stiffness, finite rotations, non-affine geometry, nonlinear
response, buckling, and performance are outside E4-0.

## Weak-symmetry feasibility screen

For `Pi(q,lambda)=Pi0(q)+lambda^T C q`, the multiplier block is exactly zero.
Before selecting any finite-element spaces, prove whether a nonzero local
constraint can simultaneously retain 24 unconstrained external coordinates,
zero added drill energy, no global mixed unknown, exact local condensation,
and a finite rank-18 PSD condensed stiffness.

If the proof shows that the branch must instead retain a saddle unknown,
reduce the external space, add displacement energy, or regularize, issue
`NO_GO_E4_WS_LOCAL_CONDENSATION_AND_RANK` and run no macroelement or inf-sup
campaign.  Only an exact counterexample satisfying every requirement may
authorize a separately registered WS stability-qualification plan.

## Perturbed-Lagrange identity and necessary screens

Use the local linear measure
`c=theta_D-(v_,x-u_,y)/2`, and retain only its centre-linear projection
`c1=c0+r*c_r+s*c_s`.  The omitted `r*s` coefficient is the unique
rotation-only mode.  Freeze `P=[1,r,s]`, unnormalized and element-local, with
positive `2 x 2` quadrature.

The source volume functional is reduced without changing units:

`Pi_PL=int_A h*(T_h*c1-T_h^2/(2*G)) dA`,

where `T_h=P*tau` and `G=E/[2*(1+nu)]`.  With
`B=int_A h*P^T*C1 dA` and `M=int_A h*P^T*P dA`, stationary elimination gives
`tau=G*M^-1*B*q` and condensed energy
`G/2*q^T*B^T*M^-1*B*q`.

The remaining affine drill mode is controlled only by
`Pi_hg=10^-3*G*(h*A)*(gamma_hg^T*d)^2`, with
`gamma_hg=(1,-1,1,-1)^T/4`.  The WG core, three multiplier parameters, and
hourglass term are combined at functional level before condensation.
Physical, PL, and hourglass energies and recovery remain separate.

Exact acceptance requires retained constraint rank three, an independent
fourth hourglass row, total rank 18, exactly six rigid modes, stationary
mixed/condensed parity, square and arbitrary nonsingular affine covariance,
all D4/reversal/frame/origin/unit actions, constant membrane/bending/shear
patch closure, and unchanged hostile E1/A/C/E2-A certificates.  Common drill
and translation-only spin are separately energetic while their matched rigid
combination is null; alternating drill is controlled only by the hourglass
term.  Decade parameter variants are diagnostic and cannot alter the frozen
identity.

A passing packet authorizes only
`PROVISIONAL_GO_E4_PL_LINEAR_QUALIFICATION_PLAN`; distortion, locking,
generalized sections, nonlinear mechanics, buckling, mass, coupling, and
production integration remain later work.

## Evidence and terminals

The path contract is frozen before outcomes.  Each standard-library oracle is
caller-bound to a canonical contract, rejects duplicate/nonfinite JSON and
identity drift, and must emit byte-identical UTF-8/LF output in two fresh
processes.  Exact arithmetic classifies; floating computation may corroborate
only.  One independent read-only review is mandatory.

Precedence is baseline mismatch; contract/nondeterminism/review block; shared
core block or no-go; WS result; PL result; route result.  A route is no-go only
if the core or both branches are definitively disproved; otherwise, absent a
passing branch, it remains unclassified.  Every outcome retains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.

Only evidence documents, canonical reference artifacts, and closed-world
tests may change, plus E4 LF attributes.  One local evidence commit is
permitted.  Push, merge, publication, production changes, and cleanup of the
six preserved evidence roots are forbidden.
