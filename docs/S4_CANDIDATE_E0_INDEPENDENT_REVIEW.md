# Candidate E0 independent review

## Verdict

`ACCEPT` — no P0 or P1 defect remains in the Candidate E0 source-gate
qualification packet.

Candidate E0 is correctly classified
`BLOCKED_CANDIDATE_E_SOURCE_OR_IDENTITY`, with exact reason
`MISSING_EXACT_ALL_NODE_DRILL_FORMULATION_AND_SOURCE_CONFLICT`.  This is a
source and formulation-identity block, not a mechanics NO-GO.  No rank,
stiffness, stability, locking, material-response, recovery, or buckling result
is claimed.

## Source review

The official Wagner-Gruttmann 2020 PDF was independently checked at 3,267,230
bytes and SHA-256
`DB68AD45455999D47D6152E736D7277F28AC1C0D85063790B15FE4089293A712`.
It supports the Hu-Washizu functional, `n=7`, `k=0`, 2 by 2 integration,
mixed equations, and local condensation.  It also states that ordinary nodes
have five coordinates, intersections may have six, and its single-element
example has 20 coordinates.

The open Wagner-Gruttmann 2004 report was independently checked at 878,871
bytes and SHA-256
`8EBDBA969BB3E2A34288EA3B5D52014C68C0E30FD2A9B36B1F92EB3073AEE7A0`.
It confirms that the ordinary-node drilling increment is fixed and has no
stiffness in that core, while three global rotations are reserved for
intersection nodes.

The indispensable Gruttmann-Wagner-Wriggers 1992 Allman displacement,
spin/skew-force, normalization, elimination, residual, and tangent equations
were unavailable as lawful full text.  The acquired sources do not define the
registered all-node 24-coordinate composition.  Constructing it would require
an unregistered hybrid.

## Material boundary

The existing ANYmaterial contract and RP-C208 dataset identities were
independently reproduced at commit
`4626887667f4c251479d26f321b9e73b046a2783`, tree
`0d40fe67ea5e0b52f11a47aeb467d6993b205a2b`.  The input shape is ordinary
Cauchy material plus thickness and requires no new public drill, Cosserat, or
inertia property.  The five grades and 17 thickness rows are correctly
identified as DNV-RP-C208 September 2019, amended October 2022—not as July
2025 RU-SHIP rule data and not as DNV approval.  Candidate-element material
qualification remains `NOT_RUN_DUE_TO_SOURCE_GATE`.

## Content-addressed audit

The following stable identities were independently verified:

- `.gitattributes`: 1,328 bytes,
  `DA5B76EC3ECB83B28114668EE1425C33D3EDCBE8FB2E708F775BEA47477CEC87`;
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
- canonical output: 2,159 bytes,
  `513465CB4993C398C9B10334244F07A26AC9A1980D49A24F79F5FC3CC7EB04AD`;
- qualification report: 4,178 bytes,
  `EC6F8A468384D65A75F783CC1947F6F5AC9E49D0FD3CDE741FEB02A45037C6FE`;
- source-gate test: 12,555 bytes,
  `96366B71BBAAA07F4E34B9B02FC27FC2101F673BFF4AC16243C5504F71B4CE9D`.

The oracle validates the exact base-75 inventory, all 14 accepted test-file
identities, and the ordered 85-node digest before contract emission or
execution.  Missing, malformed, duplicate-key, noncanonical, or caller-hash
mismatched contracts fail as
`BLOCKED_CANDIDATE_E_NONDETERMINISTIC_EXECUTION`.  Two fresh oracle runs are
byte-identical.

The accepted baseline passed 85 tests.  The focused source gate passed eight
tests, and the combined pre-review matrix passed 93 tests.  No `src/`, public
API, selector, serialization, dispatch, package, workflow, or production path
changed.  Legacy `ShellElement` and the accepted A/B/C/rank-four terminals
remain unchanged.  Existing untracked evidence was preserved.
