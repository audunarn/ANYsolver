# Candidate E1 qualification report

## Decision

Candidate E1 was evaluated as two separate identities.  They were never
assembled together and neither was connected to production.

| Identity | Result | Meaning |
| --- | --- | --- |
| `candidate_e1.wg2020_n7_k0_independent_allman_q4_static_v1` | `NO_GO_CANDIDATE_E1_A_RANK_DEFICIENCY` | The independent four-edge enrichment has a common-drill null mode and can have rank at most 17, not the required 18. |
| `candidate_e1.sestra_pattern_planar_gauge_regularizer_v1` | `PROVISIONAL_GO_CANDIDATE_E1_R_PLANAR_REGULARIZER_ONLY` | The exact planar projector, component gauge, host eligibility, and static/buckling non-intrusion rules close for the registered fallback scope only. |

The production release remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.  Legacy `ShellElement` remains the
default.  E1-R does not change E1-A's result and is not a physical rank-18
element.

## E1-A exact screen

The minimal serendipity edge space is uniquely determined once the registered
`L/8` edge normalization is imposed.  Exact trace solves give rank eight for
each eight-coefficient edge system; admitting the Q2 interior bubble would
leave one coefficient free and is excluded before outcomes.

The four drill columns factor through the cyclic edge-incidence matrix.  That
matrix has exact rank three and annihilates the common nodal drill vector.
The 20-coordinate physical core contains six rigid modes and therefore has
rank at most 14.  The complete 24-coordinate operator consequently has rank
at most `14+3=17`.  The common-drill vector is independent of the six physical
rigid modes, so nullity is at least seven.  Exact D4 numbering and reversal
checks preserve the same row space.  Zero-factor calculations also show that
local Hu-Washizu condensation and a consistent mass Gram operator cannot
restore the missing column.

This necessary failure is independent of material, thickness, quadrature,
tolerance, or benchmark selection.  DNV material response, thin sweeps,
stability, and buckling were therefore not run for E1-A.

## E1-R exact fallback scope

For positive `Dmean`, the registered Q4 scalar block has diagonal `c`,
off-diagonal `-c/3`, zero row sums, rank three, and eigenvalues
`{0,4c/3,4c/3,4c/3}`.  Its full embedding acts only on rotations projected
onto the exact common planar normal.  Exact D4 permutations, a rational 3-4-5
frame rotation, and normal reversal preserve the block.

The active-element assembly is a positive graph Laplacian.  A 2 by 2 patch
has rank eight and the registered quarter-area weights close its single
constant gauge.  For several disconnected components, existing supports and
pure-drill MPCs act on the full component-gauge basis `Z`; a canonical basis
of `ker(AZ)` determines exactly the remaining area-weighted gauge rows.  A
cross-component equality therefore adds one row, not one row per component.
Deletion and zero activity rebuild the graph; positive softening retains its
connectivity, and activity is applied exactly once.

Exact block examples retain the physical static displacement `(2,3)`,
physical recovery `8`, and finite buckling factors `(2,3)` for decade
sensitivities `{0.1,1,10}`.  E1-R supplies no geometric stiffness, recovery,
stress, resultant, yield, fatigue, or applied drill-moment channel.

The mass pattern is only conditionally certified for a host satisfying
`Mphys Q=0`; it is not a modal or transient qualification.  The current
legacy shell already has drill stabilization and positive all-axis rotary
inertia.  It fails both E1-R host audits, so neither E1-R stiffness nor mass
may be layered onto it.

## Material and source boundary

All 17 existing RP-C208-backed API records across S235, S275, S355, S420, and
S460 were exercised without adding a public material field.  The records
remain attributed to DNV-RP-C208 September 2019, amended October 2022.  They
are not relabelled as July 2025 RU-SHIP rule records.  July 2025 remains the
registered default project rule edition, and the result is described only as
compatible with DNV analysis workflows, not DNV-approved.

The installed Sestra 8.6 manual is evidence for the artificial stiffness and
mass pattern and its defaults.  The current installed manual corroborates the
current defaults and eligible shell-family context while identifying itself
as version 11.0.0 despite the 11.1 installation path.  No manual page, image,
figure, quotation, or PDF is committed.  The area-weighted component gauge
and the exact mass normalization are independently registered ANYsolver
rules, not claimed as a Sestra binary reproduction.  The superseded
`k_D=sqrt(det(As0))` and `j_D=rho_A ell^2` proposals remain excluded.

## Reproducibility and identities

The immutable pre-E1 matrix ran in a detached E0 checkout materialized with
Git-LF transport: `94 passed in 113.45s`.  The active E1 candidate-specific
matrix ran separately: `15 passed in 0.89s`.  This two-tier procedure is
required because E0's accepted closeout tests intentionally reject successor
paths.

The two fresh-process outputs are canonical UTF-8/LF JSON and byte-identical:

- E1-A contract `78ACB0EA...C5BFFA`; output `8022ECC3...10788`.
- E1-R contract `9F3F19DD...F7A4C`; output `ED26CF65...B749B`.
- Combined status record `D9DDF6EF...CC22D`.

Every accepted A, B, C, E0, and rank-four output remains byte-identical.  No
production source, API, serialization, selector, export, dispatch, or default
was changed.  The packet authorizes no push, publication, production
activation, cleanup, or combined E1-A/E1-R formulation.
