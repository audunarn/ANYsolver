# Candidate E0 source and formulation derivation

## Registered identity

Candidate E0 is registered as
`candidate_e0.wg2020_n7_k0_gww1992_allman_6dof_static_v1`.  The registration
is intentionally narrower than the attached Candidate E proposal.  The
proposed rules `k_D = sqrt(det(A_s0))` and `j_D = rho_A ell_e^2` are excluded:
they are not conventional DNV material properties and were not derived by the
selected primary sources.

## What the acquired 2020 source establishes

The official open PDF of Wagner and Gruttmann, *An improved quadrilateral
shell element based on the Hu-Washizu functional* (2020), has raw SHA-256
`DB68AD45455999D47D6152E736D7277F28AC1C0D85063790B15FE4089293A712`,
3,267,230 bytes, and 27 pages.  All pages were rendered and reviewed.

The paper supplies:

- the Hu-Washizu functional and first/second variation framework, Eqs. (1)-(6);
- the finite-element stress and strain-resultant interpolation, Eqs. (10)-(18);
- the selectable membrane interpolation whose first seven columns define
  `n=7`, and the curvature choice `k=0`;
- the mixed block equations and local elimination, Eqs. (21)-(25); and
- 2 by 2 Gauss integration except when the last quadratic functions are used.

It does not supply the registered 24-coordinate all-node formulation.  Page 7
states that the element has five or six degrees of freedom at a node: six only
at intersections of shell elements, and five at the remaining nodes.  Its
single-element rank example consequently uses a 20 by 20 stiffness matrix.

## Hostile source check

The open 2004 Wagner-Gruttmann report cited by the later formulation has raw
SHA-256
`8EBDBA969BB3E2A34288EA3B5D52014C68C0E30FD2A9B36B1F92EB3073AEE7A0`,
878,871 bytes, and 34 pages.  All pages were rendered and reviewed.

Its finite-element kinematics makes the conflict explicit.  In the ordinary
five-parameter case the drilling increment is fixed and no drilling stiffness
is available; three global rotations are used at intersection nodes only.
This source therefore closes omitted details of the mixed core but does not
authorize giving every node an active drilling coordinate.

## Missing 1992 equations

The metadata and abstract of Gruttmann, Wagner, and Wriggers, *A nonlinear
quadrilateral shell element with drilling degrees of freedom*, Archive of
Applied Mechanics 62 (1992), 474-486, DOI `10.1007/BF00810238`, are publicly
available.  The full text was not lawfully acquired in this execution.  The
2020 reference list prints 1962; the DOI, journal, and publisher records give
1992.

The unavailable material includes the exact Allman displacement field,
independent spin/skew-force interpolation, normalization, local elimination,
residual, and consistent tangent needed to reproduce the cited drilling
element.  The 2020 and 2004 sources do not prescribe splicing that element into
the `n=7`, `k=0` core at every node.  Performing such a splice would create a
new derived hybrid rather than reconstruct the registered source-exact E0.

## Material compatibility conclusion

Candidate D cannot be a DNV-standard-material-only element because its
positive Cosserat and micro-inertia properties are not present in the existing
Cauchy material contract.  Candidate E0's intended input shape is compatible
with the existing contract: `E`, `nu`, density, thickness, and explicit
strength/hardening data.  The current ANYmaterial catalogue contains five
grades and 17 thickness rows from DNV-RP-C208 September 2019, amended October
2022.  This establishes an input-shape seam only; it neither establishes a
Candidate E0 element nor converts RP data into July 2025 RU-SHIP authority.

## Terminal consequence

The source gate is incomplete and internally conflicts with the requested
all-node 24-coordinate identity.  The exact terminal is
`BLOCKED_CANDIDATE_E_SOURCE_OR_IDENTITY`, reason
`MISSING_EXACT_ALL_NODE_DRILL_FORMULATION_AND_SOURCE_CONFLICT`.

No stiffness, rank, singular value, stress, recovery, stability, locking, or
buckling result is produced.  All downstream stages are
`NOT_RUN_DUE_TO_SOURCE_GATE`; production remains unchanged.
