# B3-GE / E4-PL / B2 current acceptance matrix

**Updated:** 29 September 2026. **Candidate:** current integration branch;
exact development-screen source identities are recorded with their raw evidence.
This is the forward status index, not an
amendment to frozen registrations or historical results. The
[complete programme](B3_GE_E4_PL_B2_COMPLETE_PROGRAMME.md) defines
requirements; the [active note](B3_GE_E4_PL_ACTIVE_STATE.md) identifies
current evidence and failures. No aggregate gate or milestone is accepted.

Statuses describe acceptance, not prototype progress. `IN_PROGRESS`
includes incomplete or failed required cases; it never means a numerical
pass.

| Milestone | Status | Main remaining obligation |
|---|---|---|
| M1 matching-station GE | IMPLEMENTED_NOT_QUALIFIED | Current installed GE/ANYfem checks pass; matched E01, complete V01–V06/V17/V18/V28 evidence and independent acceptance open. |
| M2 bonded line | IN_PROGRESS | BL5 physical law, multiplier resolution, F03 and ratios/refinement/transfer open. |
| M3 physical B2 | IMPLEMENTED_NOT_QUALIFIED | Current 1/10/100 installed checks pass; F09–F11/F13, point/consumer domain and E01 B2 comparison open. |
| M4 remaining mechanics | IN_PROGRESS | Materials, footprints, topology, loads, spectra, imperfections and capacity remain mandatory. |
| M5 scale/release | NOT_STARTED | Practical scale, platforms, external programme and authorized release remain mandatory. |

| Gate | Status | Boundary |
|---|---|---|
| G0A | IN_PROGRESS | Reconcile prior registration before a pass claim. |
| G0B | IN_PROGRESS | No F01–F13 foundation fully accepted; F03 open. |
| G1 | IMPLEMENTED_NOT_QUALIFIED | Experimental sparse owner exists; foundation and full G1 acceptance open. |
| G2 | IN_PROGRESS | Candidate line/footprint and topology incomplete. |
| G3 | IN_PROGRESS | Some yielded histories work; F05 and full material domain open. |
| G4A–G4D | NOT_STARTED | No aggregate load, stability, imperfection or capacity acceptance. |
| G5 | IN_PROGRESS | Development scale screens do not meet practical-scale qualification. |
| G6A–G6D | IN_PROGRESS | Focused installed/consumer checks exist; final graph, external, reviews and release open. |

Every foundation remains open. The earlier bounded F04 distinction result
does not close F04:

| Foundation | Status |
|---|---|
| F01 | IN_PROGRESS |
| F02 | IN_PROGRESS |
| F03 | IN_PROGRESS |
| F04 | IN_PROGRESS |
| F05 | IN_PROGRESS |
| F06 | IN_PROGRESS |
| F07 | IN_PROGRESS |
| F08 | IN_PROGRESS |
| F09 | IN_PROGRESS |
| F10 | IN_PROGRESS |
| F11 | IN_PROGRESS |
| F12 | IN_PROGRESS |
| F13 | IN_PROGRESS |

The individual V01–V28 and B01–B18 obligations below are all
**IN_PROGRESS for acceptance**; none is marked PASSED. Their exact cases
and criteria remain in the programme. Split a group when a row reaches
candidate adjudication; a failed required case cannot disappear within it.

- V inventory: V01, V02, V03, V04, V05, V06, V07, V08, V09, V10, V11, V12, V13, V14, V15, V16, V17, V18, V19, V20, V21, V22, V23, V24, V25, V26, V27, V28.
- B inventory: B01, B02, B03, B04, B05, B06, B07, B08, B09, B10, B11, B12, B13, B14, B15, B16, B17, B18.

V06 development evidence: the signed axial/bending/cross-energy patch and
independently derived boundary-load solves pass both offsets and three 2D
grids, with 6/6 source and isolated installed-wheel regressions on Windows.
The finest-grid force-like retained
coordinates show a 4.40e-9 scaled numerical drift. Representative
engineering-boundary centered-rib responses are now compared with executed
OpenSees cases on three grids: pure-load tip outputs differ by at most 0.1752%,
but local curvature profiles differ and a combined near-cancellation response
needs the registered absolute floor. The homogeneous 1D section formula is
not an exact oracle for that 2D model. Broader installed/platform checks,
independent mechanics review and complete V06 adjudication remain open. See
`.qualification/b3-ge-e4-pl/r8-v06-transformed-energy-dev-20260929-v5/`
`.qualification/b3-ge-e4-pl/r8-v06-installed-dev-20260929-v1/` and
`.qualification/b3-ge-e4-pl/r8-v06-centered-cantilever-dev-20260929-v3/`.

| External comparison | Status | Current boundary |
|---|---|---|
| E01 eccentric elastic panel | IN_PROGRESS | CalculiX six-row deck remains inert after an expansion-map defect. OpenSees signed point screens, including 2×1/4×2/8×4 grids, pass link/work/wrench checks, but physical roll disagreement increases on two-direction refinement. The 8×4 external coupled shell action replays its field to 1.93e-17; changing the coupled action explains 93.6% of the native-to-external roll gap at fixed native shell stiffness, mainly through the physical Mx distribution. Direct +100 N m torque on that geometry gives 19.0% native/external torsional-compliance difference, stable under correction of native sparse-solve roundoff. The beam-only section agrees to roundoff. Shell/point torsional transfer and matched idealization remain unresolved. Formal observables/floors, accepted physical reference and independent review remain open. |
| E02 torque/footprint | NOT_STARTED | No executed matched comparison. |
| E03 curved stiffener | NOT_STARTED | No executed matched comparison. |
| E04 nonlinear GE/capacity | NOT_STARTED | No executed matched comparison. |

Known adverse evidence remains visible: F03's off-ratio mode and historical
timeouts do not select a multiplier; F05's 45 N and 42.5 N cases failed
without changing the accepted 40 N state. See the active note and
`.qualification/b3-ge-e4-pl/r8-f05-45n-ticket-dev-20260929-v1/`.
Formal F03 execution authority is unconsumed. This matrix changes no
scientific criterion, resource limit, release authority or final scope.
