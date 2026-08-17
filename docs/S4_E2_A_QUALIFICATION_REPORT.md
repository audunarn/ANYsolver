# Candidate E2-A source and kinematic qualification report

## Decision

The registered identity
`candidate_e2_a.wg2020_n7_k0_displacement_allman_q4_kinematic_v1`
is `BLOCKED_E2_A_SOURCE_OR_FORMULATION_IDENTITY`, reason
`RANK_SUFFICIENT_DISPLACEMENT_ENRICHMENT_NONUNIQUE`.

This is an identity block, not a failed rank test.  No E2-A membrane rank,
full rank, stiffness, mass, patch, condensation, warped-geometry, nonlinear,
locking, buckling, dynamics, coupling, performance, or production result was
run or inferred.  E1-RH remains `DEFERRED_NOT_RUN`.

## Source boundary

The Wagner-Gruttmann `n=7`, `k=0` Hu-Washizu spaces, local condensation,
positive `2 x 2` surface rule, and MITC4 shear tying can be fixed from public
primary evidence.  The public quadratic Allman/Cook connector, however, uses
endpoint drill differences.  It is the already accepted E1-A hostile control:
its drill columns factor through the cyclic edge-incidence matrix, it
annihilates common drill, and its full rank is at most 17.

Escaping that null requires absolute drill to be coupled to a translation
spin.  The exact derivation uses the affine-exact physical center-curl
functional, obtained from the center displacement gradient `U_xi A^-1`,

```text
eta = mean(theta_D at the four nodes) - (u_2,1-u_1,2)/2 at the center.
```

and the orientation-corrected physical cofactor map
`C_A = chi sqrt(det(G)) A G^-1`, equivalently
`chi |det(A)| A^-T` in the local two-dimensional frame.  Neither the selected
sources nor the long-horizon design input specifies how this scalar enters a
unique two-dimensional displacement map.  Sestra is background evidence only
and supplies no E2-A equation, coefficient, threshold, or outcome.

## Exact non-uniqueness certificate

The independent standard-library oracle constructs two exact displacement
lifts on both the reference square and the rational skew parallelogram with
`A=[[3,5],[4,12]]`.  Both:

* leave all four nodal translations unchanged;
* have the same complete boundary trace;
* are inactive for every registered affine membrane patch;
* are exactly covariant under all eight D4 operations, normal reversal, the
  registered rational frame rotation, origin shift, and unit scaling;
* give positive strain energy to pure common drill and to translation-only
  rigid spin; and
* annihilate their matching combined rigid state exactly.

They differ by a boundary-zero D4-covariant interior pseudovector.  On the
square its exact engineering strain at `(r,s)=(1/2,1/3)` is
`[8/27,-1/4,-5/18]`, and its exact integrated strain energy is `128/35`.
On the skew parallelogram the orientation-corrected cofactor is
`[[12,-4],[-5,3]]`, its pairing with the geometry is exactly `16 I`, the
difference strain is `[13/4,1007/1728,-203/72]`, and the difference energy is
`305584/175`.  The two maps are therefore inequivalent throughout the frozen
affine geometry contract.  Their square pure-drill energies are respectively
`32/5` and `1952/105`; the skew values are `2266` and `3692602/525`.  In every
case the translation-only rigid spin has the matching positive energy and the
combined rigid-state energy is exactly zero.  No rank or benchmark outcome
was used to obtain either map.

The oracle also reproduces the immutable E1-A hostile result: cyclic drill
rank three, common-drill image zero, and full-rank upper bound 17.  Selecting
the new interior coefficient, deleting its mode, or changing its
normalization using a rank or benchmark would be outcome-driven invention.

## Extension and production boundary

A later formulation would need one selected displacement operator `H(q)` to
generate compatible strains, work-equivalent loads and normal moments,
consistent mass, recovery, geometric stiffness, and finite-rotation first and
second variations.  Because `H` is not unique, those extension rows are
`NOT_RUN_IDENTITY_AMBIGUOUS`; they are not classified as
`NO_GO_E2_A_EXTENSION_CLOSURE`.

Any future interpolation, mixed-space, quadrature, condensation, or work-map
choice must be preregistered as a newly named successor.  This packet changes
no production source, API, export, selector, serialization, dispatch, default,
or historical qualification artifact.  The release terminal remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`, and legacy `ShellElement` remains
the default.

## Reproducibility

The baseline was verified as the two immutable tiers required by the plan,
not as one live 110-test successor suite:

* E0 commit `87b639499187736c59d87bc4aa8e6bd7f819d28b`, tree
  `c01fd5cab7b63325e6cb5b70000f4586d4788563`: `94 passed in 120.03s`.
* E1 commit `281ed90e148c125edbec27e7336a8f9f0df08edc`, tree
  `1ee60da4717055f5cc1b37ff9369877bb1867861`: `16 passed in 1.34s`.

The accepted E1 report's historical text saying 15 focused tests ran remains
byte-identical; this successor merely records that the five committed E1 test
files now collect 16 nodes.

The exact E2-A screen passes four tests.  Two fresh oracle executions emit the
same canonical UTF-8/LF bytes.  Content identities are:

* cases `61ED18EDB32B0DAF288E3EB66FEA522D5D4588542F11D8881B5B7762FCAC3729`;
* oracle `A1796D466DF6DDCDB420987F8FAFC3787B563C16F0B8AEC58C716C0EF194D151`;
* contract `E3AA3BC6AD8FAD7EB64564851FC558B0D1B2ACB533B292EEBA580EBA47B02D3E`;
  and
* output `37C803C565602E1AF983AA8374C3DA090EFD1CC73F2B672F2C815CC6A56B623D`.

An independent review and the downstream closeout record must validate these
identities before this packet is considered complete.  No push, publication,
cleanup, production activation, or E1-RH execution is authorized.
