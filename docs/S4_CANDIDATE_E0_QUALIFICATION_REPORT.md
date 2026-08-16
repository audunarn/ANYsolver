# Candidate E0 qualification report

## Result

Candidate E0 stops at the mandatory source and identity gate with terminal
`BLOCKED_CANDIDATE_E_SOURCE_OR_IDENTITY` and reason
`MISSING_EXACT_ALL_NODE_DRILL_FORMULATION_AND_SOURCE_CONFLICT`.

This is not a mechanics NO-GO.  No Candidate E0 stiffness, rank, stability,
locking, recovery, or buckling calculation was run.  The proposed formulation
is not sufficiently defined to perform those calculations without inventing a
hybrid.

The production release terminal remains
`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`; legacy `ShellElement` remains the
default.

## Source findings

The official open Wagner-Gruttmann 2020 paper was acquired as 3,267,230 bytes,
SHA-256
`DB68AD45455999D47D6152E736D7277F28AC1C0D85063790B15FE4089293A712`.
Its 27 pages were rendered and reviewed.  It prints the Hu-Washizu functional,
`n=7`, `k=0`, 2 by 2 integration, the mixed block, and local condensation.

The same paper explicitly defines five coordinates at ordinary nodes and six
only at shell intersections.  Its single-element rank example is therefore a
20-coordinate system, not the registered all-node 24-coordinate target.

The open 2004 core report was acquired as 878,871 bytes, SHA-256
`8EBDBA969BB3E2A34288EA3B5D52014C68C0E30FD2A9B36B1F92EB3073AEE7A0`.
Its 34 pages were rendered and reviewed.  It confirms that ordinary-node
drilling increments are fixed because that core supplies no drilling
stiffness; three global rotations are used at intersections only.

The 1992 Gruttmann-Wagner-Wriggers drilling paper was available only through
metadata and abstract.  Its exact Allman displacement, spin/skew-force,
normalization, elimination, residual, and tangent equations were not lawfully
available.  Neither the 2020 paper nor the 2004 report prescribes composing
that independent drilling element with the `n=7`, `k=0` core at all nodes.

## DNV material boundary

Candidate D cannot use only ordinary DNV-compatible material inputs: its
positive Cosserat and micro-inertia properties are absent from the existing
Cauchy material interface.

Candidate E0's intended input shape is compatible with existing
`StructuralMaterial + thickness` data and adds no public material field.  The
registered ANYmaterial catalogue at commit
`4626887667f4c251479d26f321b9e73b046a2783` contains five grades and 17
thickness rows.  Those rows are explicitly DNV-RP-C208 September 2019,
amended October 2022.  They are not relabelled as July 2025 RU-SHIP rules, and
compatibility is not represented as DNV approval.

Because the element identity gate did not close, physical stiffness/recovery
and every DNV material response case are `NOT_RUN_DUE_TO_SOURCE_GATE`.

## Content-addressed evidence

- governing plan: 5,438 bytes,
  `082BABD49F20436BEFBC2C14C123F6904DAAA6597EA99A1F7D85FA13F80B1162`;
- derivation: 4,103 bytes,
  `D9A443D2B7F92E72057AC7317083B34AD586899F5BE75F148E94C2C5798DD211`;
- source registry: 3,705 bytes,
  `E31B419F141B4FC0C80010BE5BDE31A4F85ACE3A84E6B5F01E0D80B34CE617CC`;
- material fixtures: 2,135 bytes,
  `A16024C81522FB783841CC790C11772A10C8D0D936F9E678BE1CA981FD3DD016`;
- oracle: 19,683 bytes,
  `48FBD49E7011197A370492E61C76167BDC038054D47F3ADB2A7DA6DCEAF82A4A`;
- contract: 4,528 bytes,
  `D3ACF44D4690E7ED8E257B1A1A5DB124CE91ADAFE98ACDD186305C56A4740B03`;
- canonical blocked output: 2,159 bytes,
  `513465CB4993C398C9B10334244F07A26AC9A1980D49A24F79F5FC3CC7EB04AD`.

Two fresh standard-library oracle processes emitted byte-identical canonical
output.  The exact accepted 85-test baseline was independently rerun before
the packet and passed.

## Unblocking condition

Resume requires a lawful full text of the 1992 drilling paper and a separately
reviewed, pre-result equation-level derivation showing that its drilling fields
compose with the 2020 `n=7`, `k=0` Hu-Washizu core without double counting and
produce the registered all-node 24-coordinate residual, condensation, and
consistent tangent.  Otherwise a different, explicitly derived candidate must
be registered.

No production source, API, selector, serialization, package, workflow,
activation, push, publication, or cleanup was changed or authorized.
