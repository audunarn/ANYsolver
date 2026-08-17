# Corrected E3 HW29 identity and MITC9i reference plan

## Authority and purpose

This plan is governed by E2-A closeout commit
`2ac678a7f94c250fe433f66378a83508d86ee499`, tree
`f7382e2b88343ac29c9a9e3c424f618a3652cc01`.  It binds the user-supplied
route proposal at 35,837 bytes and SHA-256
`7D86FE7A6D205BFEDDA4C884A2AFAD5C80EF0F3DE6BA350C48BBB2150BFC5108`
as design input, superseded where this plan is more restrictive.

Two independent non-production studies are registered:

* `study_e3_p.hw29_linear_isotropic_identity_v1` determines whether the
  printed HW29 formulation is reproducible as a homogeneous-isotropic,
  linear-static, 24-external-DOF identity.
* `reference_e3_q9.mitc9i_open_theory_extraction_v1` records an independent
  Q9 reference packet.  Its status cannot block, select, or modify HW29.

No candidate mechanics, production source, API, selector, export,
serialization, dispatch, default, package, workflow, push, publication, or
cleanup is authorized.

## Baseline and transport

The historical baseline remains three closed-world tiers, never one live
118-test suite: E0 has 94 nodes, E1 has 16 nodes, and E2-A has 8 nodes across
three files.  Each tier is executed only at its exact authority commit in an
isolated worktree.  Existing A/B/C/rank-four/E0/E1/E2 evidence and the six
inventoried untracked roots are immutable.  Cleanliness means an empty tracked
and index diff plus those preserved roots.

All new text uses UTF-8/LF.  JSON is duplicate-free, nonfinite-free, sorted-key
compact canonical JSON with one terminal LF.  Oracles use only the Python
standard library and are run twice in fresh processes with caller-bound
contract hashes.

## HW29 identity gate

The fatal source matrix is limited to homogeneous isotropic linear statics.
It must print or uniquely imply, before oracle outcomes:

* standard Q1 four-node translations and rotations with no Allman lift;
* 7 membrane-stress, 9 membrane-strain, 2 EADG, 4 shear-stress,
  4 shear-strain, and 3 drill-multiplier parameters;
* complete skew-coordinate/EADG2/mixed-shear maps, ordering, and 2x2 rule;
* `T=q15+xi*q16+eta*q17`, `gamma_PL=G`, exact deletion of the `xi*eta`
  rotation-only term, the geometry hourglass vector `gamma_HG`, and printed
  energy scale `alpha_HG=1e-3`;
* the uncondensed functional, internal block order and assumptions, Schur
  condensation, linear virtual work, loads, and physical-resultant recovery.

Only coefficients printed in a public source are admissible.  Algebraic
residuals, tangents, and condensation may be independently derived only as
unique consequences of a fully frozen functional.  Missing spaces, maps,
mode rules, or coefficients cannot be inferred from rank, conditioning, or
benchmarks.  `G=E/[2(1+nu)]` uses existing isotropic material inputs; RP-C208
provenance remains separate from RU-SHIP metadata and no DNV approval is
claimed.  General sections, orthotropy, laminates, mass, geometric stiffness,
nonlinear mechanics, buckling, and dynamics are later identities.

The source-independent oracle classifies the flat drill polynomial, deletion
and residual alternating mode; checks printed hourglass action and exact rigid
invariance; proves the E2-A interior bubble is outside Q1; forbids an Allman
insertion; and verifies field/block counts and only those condensation facts
supported by the frozen source.

HW29 component terminals are:

* `BLOCKED_E3_P_HW29_PUBLIC_SOURCE` for missing indispensable public input;
* `UNCLASSIFIED_E3_P_HW29_IDENTITY` for multiple source-consistent identities;
* `NO_GO_E3_P_HW29_IDENTITY` for explicit contradiction; and
* `PROVISIONAL_GO_E3_P_HW29_ISOTROPIC_LINEAR_STATIC_PLAN` only when every
  mandatory row closes and independent review accepts it.

## MITC9i independent reference

The open MITC9i source is transcribed only into bibliographic/equation maps,
independently derived formulas, cases, and oracles.  The packet records the
centre-Jacobian COVc approximation without claiming exact covariance; corrected
Q9 functions and selected shift solves; drilling polynomial and source-tested
retained/deleted/scaled variants; rotation-update conventions and missing
variations; and a bounded benchmark inventory without copying figures/tables.

Its independent statuses are
`BLOCKED_REFERENCE_E3_Q9_MITC9I_SOURCE_IDENTITY`,
`UNCLASSIFIED_REFERENCE_E3_Q9_MITC9I_EXTRACTION`,
`GO_REFERENCE_E3_Q9_MITC9I_PARTIAL_PACKET`, and
`GO_REFERENCE_E3_Q9_MITC9I_OPEN_PACKET`.

## Evidence graph, route rule, and extent

The acyclic graph is: authority/environment/search log -> source matrices and
cases -> independent oracles/contracts/outputs -> component reports -> route
contract/output and exactly one conditional successor plan -> independent
review -> final status -> completion report and closeout test.

Required new paths are the governing plan; three common manifests; source
registry/search log/material fixture; HW29 report/coverage/cases/oracle/
contract/output; MITC9i report/source-map/cases/oracle/contract/output; route
report/contract/output/status/completion/review; and five E3 tests.  Conditional
paths are exactly one of
`S4_E3_P_HW29_LINEAR_QUALIFICATION_PLAN.md` or
`S4_E3_A_VARIATIONAL_CLOSURE_STUDY_PLAN.md`.  `.gitattributes` is the sole
modifiable existing path.  The emitted contract expands and checks the exact
literal path list before any output.

Run failures use `BLOCKED_E3_BASELINE_OR_CLOSEOUT_MISMATCH` or
`BLOCKED_E3_EVIDENCE_OR_REVIEW` and produce no route result.  Otherwise:

```text
if HW29 == PROVISIONAL_GO_E3_P_HW29_ISOTROPIC_LINEAR_STATIC_PLAN:
    SELECT_E3_P_HW29_FOR_LINEAR_QUALIFICATION
else:
    UNCLASSIFIED_E3_Q4_FORMULATION_ROUTE
    AUTHORIZE_E3_A_VARIATIONAL_CLOSURE_STUDY
```

The fallback is a study plan, not a candidate registration.  Every outcome
retains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`; legacy `ShellElement` remains
the default.  A coordinator and at most three non-recursive agents are used,
with one evidence freeze and at most one correction/re-review cycle.  One local
evidence commit is permitted; no merge or push is permitted.
