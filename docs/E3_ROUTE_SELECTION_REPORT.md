# E3 HW29 and MITC9i route-selection report

## Decision

The E3 run is complete and reproducible, but it does not select a Q4
formulation.

- `study_e3_p.hw29_linear_isotropic_identity_v1` is
  `BLOCKED_E3_P_HW29_PUBLIC_SOURCE`.
- `reference_e3_q9.mitc9i_open_theory_extraction_v1` is
  `GO_REFERENCE_E3_Q9_MITC9I_PARTIAL_PACKET` and has no route-gating edge.
- The route terminal is `UNCLASSIFIED_E3_Q4_FORMULATION_ROUTE`.
- The only authorized successor is the study-only
  `AUTHORIZE_E3_A_VARIATIONAL_CLOSURE_STUDY` plan.

No candidate was registered and no mechanics, rank, patch, stability,
locking, distortion, production, or performance campaign was run.  Production
remains `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`, with legacy `ShellElement`
as the default.

## HW29 source result

The user-supplied 2011 Wiśniewski-Turska chapter materially narrowed the
source gap.  The complete 22-page file is 310,978 bytes with SHA-256
`E6AFAADE32B33D710D3C038635FE2AD2729E32FB952C5EC6706E68A93A3B1860`.
It closes the standard Q1/24-DOF statement, 29-field count, skew-coordinate
construction, 7p/9p/EADG2 definitions, three-parameter multiplier,
`gamma=G`, deletion of the rotation-only `xi*eta` term, geometry-dependent
hourglass vector, printed `10^-3` energy factor, and `2 x 2` quadrature.

Five indispensable rows remain unclosed:

1. the shell-specific EADG2 transformation explicitly deferred by the source;
2. the four stress and four strain transverse-shear interpolation maps;
3. the complete discrete HW29 functional and internal block order;
4. the actual HW29 condensation equations and invertibility assumptions; and
5. the complete linear load-work and physical-resultant recovery maps.

Those equations cannot be inferred from field counts, rank, conditioning, or
benchmarks.  The terminal is therefore a source block, not a mechanics
NO-GO.  The exact oracle nevertheless reproduces the Q1 drilling polynomial,
the residual alternating mode, rigid cancellation, square and rational-
trapezoid gamma vectors, rank-one residual stabilization, and zero constant-
drill grounding.  Unsupported HW29 mechanics remain `NOT_RUN`.

The second supplied paper, *Degenerated Four Nodes Shell Element with Drilling
Degree of Freedom*, is a distinct formulation with a problem-dependent
absolute torsional penalty.  It closes no HW29 row and is retained as
background only.

## MITC9i reference result

The user-supplied MITC9i PDF is byte-identical to the previously acquired open
primary source: 1,302,612 bytes, 25 pages, SHA-256
`5C66A76D39682F71C13208E71AFFA585FD3CD1E284185360B825572DC8BA048B`.
The packet exactly certifies the fixed-centre COVc reciprocity and its
off-centre approximation boundary, corrected shifted Q9 basis, partition and
nodal/edge/Q2 reproduction, selected shift-parameter cases, and the highest
rotation-only drilling term.  It records the source's retained, deleted, and
scaled variants without selecting one for Q4.

The reference remains partial because the open paper does not print the
complete first/second variations, consistent nonlinear tangent, mass,
geometric-stiffness separation, or load-potential linearization.  Its status
cannot select, block, or modify HW29.

## Reproducibility and identities

The immutable closed-world tiers were verified separately:

- E0: 94 tests at commit `87b639499187736c59d87bc4aa8e6bd7f819d28b`,
  tree `c01fd5cab7b63325e6cb5b70000f4586d4788563`;
- E1: 16 tests at commit `281ed90e148c125edbec27e7336a8f9f0df08edc`,
  tree `1ee60da4717055f5cc1b37ff9369877bb1867861`; and
- E2-A: 8 tests at commit
  `2ac678a7f94c250fe433f66378a83508d86ee499`, tree
  `f7382e2b88343ac29c9a9e3c424f618a3652cc01`.

They are not represented as one live 118-test successor suite.  The E3
component evidence is content-addressed as follows:

- HW29 contract `E07C60EDE72DDD6D19D686F79978C3F0D1826DA91B1D2552534063BD28C394A0`
  and output `3D9E9C858CAD14CB3BDEBFC8866E971658F02E71B16573A320BAF0B08DFE9806`;
- MITC9i contract `86824E91A460AEAC9F67B213048E471AF968C7AA9FE2C43E6B61B148A5C8FBED`
  and output `00A6603A7B163CBC4A25B7FDF74647DDC1BDA300D478598F1403E4582AF5B575`;
- route contract `B39EE05F48EB4D5CF4A1A09C0FF20891886BB388631756FD08328CEE4FB99BF9`;
  and
- route output `A2D3283C1F01A26EF01986A4C5396B6C07797C250B7D2BD3BDA21AD1E14C273E`.

Each component oracle is standard-library-only, caller-bound to its exact
contract, fail-closed on identity drift, and required to emit byte-identical
canonical UTF-8/LF output in two fresh processes.  No external PDF, page,
figure, table, or copied passage is committed.
