# Candidate E0 DNV linear and buckling qualification plan

## Authority and objective

This plan implements the user-approved Candidate E0 program from exact
ANYsolver base commit `a9b45ca95303bc4b30b893fbb0d7177f9c98db03`, tree
`6919b33851b63236fc150711a0ccb28fdfa2dbf8`.  The superseded Candidate E
proposal is retained only by raw identity: 36,288 bytes, SHA-256
`4499DA192F97D9BF7D89C3A9A8B5A68E6201CA5E2350E30918583464BF0E98EA`.

The registered candidate identity is
`candidate_e0.wg2020_n7_k0_gww1992_allman_6dof_static_v1`.  It is intended to
combine the Wagner-Gruttmann 2020 Hu-Washizu core, with `n=7`, `k=0`, and a
2 by 2 surface rule, with only the exact six-degree-of-freedom drilling
construction of Gruttmann-Wagner-Wriggers 1992.  It may use conventional
Cauchy material and section data.  It may not introduce a drill modulus,
Cosserat modulus, length scale, numerical drill coefficient, independent
drill inertia, penalty, or stabilization not explicitly supplied by the
selected source formulation.

The branch is a proof and qualification branch.  It owns no production
source, public API, serialization, selector, factory, dispatcher, package,
workflow, or release change.  Legacy `ShellElement` remains the production
default.

## Source gate

Before any mechanics calculation, an equation-level source registry must
establish all of the following:

1. the complete 2020 `n=7`, `k=0` Hu-Washizu interpolation and its 2 by 2
   integration rule;
2. the exact Allman displacement, spin, and skew-force fields used for an
   independent drilling coordinate at every Q4 node;
3. a nonduplicating interface between those fields and the 2020 mixed core;
4. a complete 24-coordinate residual, local mixed block, exact condensation,
   and consistent tangent; and
5. a source-backed reason that all four nodes, rather than intersection nodes
   only, carry six active coordinates.

Every indispensable statement must be either printed by a lawfully acquired
primary source or independently derived, content-addressed, and accepted
before results are known.  Abstracts, metadata, analogy, or a source from a
different formulation cannot close a statement.

If any item is missing or conflicts with another normative source, the
terminal is `BLOCKED_CANDIDATE_E_SOURCE_OR_IDENTITY`, with reason
`MISSING_EXACT_ALL_NODE_DRILL_FORMULATION_AND_SOURCE_CONFLICT`.  Mechanics,
stability, locking, material-response, recovery, and buckling execution then
remain `NOT_RUN_DUE_TO_SOURCE_GATE`.

## Material boundary

The initial compatibility target is homogeneous DNV steel through the
existing ANYmaterial `StructuralMaterial + thickness` interface.  The
existing five-grade, 17-row catalogue is explicitly DNV-RP-C208 September
2019, amended October 2022.  It is not relabelled as July 2025 RU-SHIP data.
The conventional `nu=0.3` and `rho=7850 kg/m^3` defaults remain distinguished
from the RP table.

July 2025 RU-SHIP is the default project rule edition for this qualification.
July 2026 requires explicit early-adoption authority until its 2027 effective
date.  A compatible element is not thereby DNV-approved.

No public material field is added.  Pre-integrated `A/B/D/As` sections form a
separate future linear compatibility gate; current generalized sections do
not establish nonlinear DNV material support.

## Conditional mechanics program

Only a passed source gate releases the following stages, in order:

1. exact mixed and condensed residual, tangent, energy, and virtual-work
   equivalence;
2. element rank 18 with exactly six rigid modes and no negative or seventh
   mode;
3. local mixed-block invertibility for every admitted SPD isotropic section;
4. affine symbolic reproduction, 2 by 2 primary integration, and frozen 3 by
   3 non-affine sensitivity without outcome-driven rule changes;
5. mesh-uniform stability, support/MPC/topology semantics, patch tests,
   distortion, and `t/L=10^-1 ... 10^-6` locking screens;
6. physical DNV-steel stiffness and recovery with numerical drilling excluded
   from `N/M/Q`, stresses, yielding, fatigue, and code checks; and
7. source-consistent prestress and geometric stiffness for linear eigenvalue
   buckling.

Nonlinear collapse, postbuckling, modal dynamics, transient dynamics, and
performance are outside E0.  No independent drilling mass may be introduced.

## Evidence and terminal calculus

The packet consists of a baseline, environment, source registry, formulation
identity, material fixtures, gate cases, test inventory, derivation, standard
library oracle, emitted contract, canonical output, report, tests, and
independent review.  All JSON is duplicate-key-free, nonfinite-free, sorted
compact UTF-8 with LF and one final newline.  Two fresh oracle processes must
emit identical bytes.

Identity or contract corruption outranks the scientific source terminal.  A
passed source gate followed by a certified mechanics failure produces the
corresponding `NO_GO_CANDIDATE_E0_*` terminal.  Incomplete evidence is
`UNCLASSIFIED_CANDIDATE_E0_DNV_LINEAR_BUCKLING`.  A complete linear, stability,
material, recovery, and buckling pass is only
`PROVISIONAL_GO_CANDIDATE_E0_DNV_LINEAR_BUCKLING` and authorizes a new plan,
not production activation.

Throughout this program the release terminal remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.  Existing untracked evidence is
preserved; cleanup, push, publication, and production integration are not
authorized.
