# GE-B3 P5: native coordinate-state correction

## Status and preserved authority

Private development successor: `CANDIDATE_GE_BEAM3_P5_NATIVE_COORDINATE_V2`.
The coordinate-precision defect is corrected through the native state path;
**independent review and production qualification remain pending**. There is no
public selector, activation, release, tag, push or merge in this checkpoint.

The seventeen-file V1 package at
`cdf71995570b3d1aaeda44b7ed046c04528ae6b8` and the diagnostic checkpoint
`70dd5fc9274cb7cff718107b39fc054039ea7e2d` are preserved without modification.
The new seven-module package is `anysolver._ge_beam3_p5_coordinates`. Its source
map binds all 24 modules, identifies the five adapted V1 files, checks their
unchanged dependencies and records review as `PENDING`, not an empty accepted
independent review. This is a development binding, not execution authority.

New source is added; this is **not** a no-`src/`-delta checkpoint. Existing B2,
legacy B3, qualified shells, public GE-B3 P3 routing, section laws, stationary
operators, coefficients, quadrature, tolerances and defaults remain unchanged.

## Implemented correction

The native total displacement is authoritative. Each position is represented by
the rounded native high coordinate plus the retained residual of `X + u`.
The high coordinate must match the live native pose exactly. State validation
recomputes the pair and rejects changed lows even when an attacker/test reseals
all state hashes. No displacement is inferred by subtracting rounded poses.

New core, driver, codec and formulation identities bind the coordinate policy
`GE_BEAM3_P5_REFERENCE_PLUS_TOTAL_TWO_COMPONENT_V1`. Old V1 histories cannot be
hot-restarted into V2, and V2 histories cannot be read as V1.

- Initialization, local solves, trial state, accepted-origin replay, commit and
  typed restart consistently retain both coordinate parts.
- Cancellation, rejected trials, displacement control, arc-length control,
  loading/unloading/reversal and split continuation use the existing native
  transaction boundary. No accepted history is re-originated or advanced during
  validation or recovery.
- Physical recovery uses the exact frozen station schedule and the same reference
  offset expression as the local operator. It returns `current_positions` as the
  rounded display/high component and `current_position_low` as the retained
  component, with explicit policy/provenance. It does not manufacture fibre stress.
- Cold-path station-position recovery accumulates exact products of supplied
  binary64 weights, rotations and coordinates before rounding to two components.
  This is not a claim that all reference geometry or every real-valued product is
  exactly represented by two floats; the final low component may itself round.
- Accepted-state augmented stiffness uses the same pair. At-rest retained-cell
  mass is translation-independent: its physical velocity map depends on the
  reference lift and current cell rotations, not absolute nodal positions. The
  wrapper validates the pair and evaluates the unchanged kinetic operator only
  with zero velocity/acceleration. No finite-velocity momentum/dynamics route is
  exposed by this wrapper, and no fictitious trace-rotation mass is introduced.

The exact axial witnesses now retain extension and compression below the ULP of
the high positions. Native force, strain, resultants, energy and accepted-state
operator agree with the independent analytical reference. When all nodal lows
are zero, native residual, tangent and stationary response are byte-identical to
V1 in the frozen straight axial comparison.

## Validation

Final source regression: **94 passed in 86.30 seconds**. It covers:

- Forty successor checks: sub-ULP axial commit/replay/work, exact pair addition,
  hash/state/codec mutations, V1/V2 restart rejection, recovery, coupled curved
  elastic/plastic paths, exact split restart, native control and cancellation,
  current/reference modes, a two-element shared-node arch, finite rigid motions,
  source-map mutation rejection, and directional tangent/symmetry checks.
- Fourteen unchanged native-package equivalence checks, three preserved package
  checkpoint checks, eleven historical precision-diagnostic checks, 21 accepted
  P3 opt-in checks and five generic state-cleanup checks.

Tangent directional agreement retains `1e-7`; symmetry/invariant checks retain
`1e-11`. The small axial reference uses its nonzero reference magnitude, not an
absolute scale that would conceal complete loss of its tiny force.

The first smoke helper incorrectly requested a trial token after successful
commit (five failures). The next run had four passes and one failure because its
test tried to JSON-encode a sparse matrix. Both were test-harness defects, fixed
without changing mechanics. Subsequent suites passed 20 checks in 15.81 seconds,
33 in 54.69 seconds, and five additional checks in 6.91 seconds before the final
94-check regression. These were small development checks, not retries of any
consumed formal resource request.

Installed-wheel lane: **one test passed in 31.83 seconds**. It builds a disposable
wheel, installs offline into a fresh virtual environment, removes repository
search paths, rejects research imports, and checks all 24 deployed source hashes.
Two fresh-process runs produce byte-identical canonical records. Each exercises
plastic split restart, physical recovery, reference/current modal operators and
the actual sub-ULP native axial commit with typed state replay.

The source runtime is Python 3.13.9 / NumPy 2.4.3 / SciPy 1.16.3. The isolated
wheel uses the preserved exact offline dependency graph (including NumPy 2.5.2
and SciPy 1.18.1), hash-checked before installation and bound by the receipt.
There is no cross-version bitwise-equality claim or performance speed claim.
No formal qualification campaign, ledger update or resource request ran.

Post-evidence inspection passed three separate static checks in 0.12 seconds;
the read-only source-map check confirms seven successor and seventeen preserved
modules. These checks inspect bindings and archived artifacts without rerunning
mechanics or the installed-wheel lane.

## Preserved artifacts

Archive:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-p5-coordinate-state-development-20260906-362985c7a9db`

Six files, 1,327,084 bytes, preserve the wheel, source map, installed check script,
receipt and both process records. Copies were exclusive and verified by byte
count and SHA-256. Only verified workspace relay duplicates were removed; the
original temporary files and external archive remain.

- Wheel: 1,298,800 bytes,
  `362985c7a9db130bb88d1ebfb21f376338ceb3db28363b3dbe629d3eea866ba9`.
- Each process record: 6,491 bytes,
  `f5c02ec875bba588ee5294576d488625a47e3ac5c87ba45089d0a0522e46750f`.
- Source map:
  `4aee73cf0ec59a4190e9a2e4a8d2d97c1bf86d31331a0a53fedbe14f4c1fc8f5`.

The wheel retains existing `0.4.2` development metadata. **Do not publish it as a
replacement 0.4.2 release.** Candidate package bytes are unchanged after the
installed check; later edits in this turn are tests, binding evidence and docs.

## Remaining programme

The previous coordinate-successor plan remains preserved as the pre-implementation
checkpoint; this document records its implemented development correction. It is
not complete production qualification or a public integration claim.

Next audit the direct reference-geometry polynomial sums under large common
translations. Those sums are unchanged here; the successful finite rigid-motion
checks do not prove large-offset accuracy. If defective, use a separately bound
reference-evaluation successor and targeted tests rather than silently expanding
this correction. Independent review of the native package/state work is still
required. Continue explicit public operator routing, load-work/tangent parity,
general nonlinear section semantics, straight/curved modal and buckling reference
gates, then the separately qualified objective beam-shell connection.

Arc-length development tests cover bounded native state/control behaviour, not
post-buckling qualification. Current modes are restricted to equilibrated elastic
interior states at rest; plastic vibration branches remain rejected. Direct
public mass/geometric-stiffness APIs remain fail-closed in this private candidate.
Finite-rotation dynamics, shared beam-shell joints, broad nonlinear section parity
and all required engineering qualification are not completed by these tests.

No preserved 32-element study is rerun or reclassified. Any future heavy campaign
requires a fresh clean freeze, resource request/approval and global lease. The
overall straight-and-curved GE-B3 plus objective connection goal remains active.
