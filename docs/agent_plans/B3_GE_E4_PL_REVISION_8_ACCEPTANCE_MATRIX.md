# B3-GE / E4-PL / B2 current acceptance matrix

**Updated:** 29 September 2026. **Candidate:** integration branch through
`3009b3d0`, plus the E01 development screen recorded in the active state.
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

| External comparison | Status | Current boundary |
|---|---|---|
| E01 eccentric elastic panel | IN_PROGRESS | CalculiX six-row deck remains inert after an expansion-map defect. OpenSees 2/4/8-interval signed point screens and native source comparisons passed primary-response, link, work and wrench development checks, but secondary responses disagree; formal observable/floor registration, installed comparison, refinement adjudication and independent review remain open. |
| E02 torque/footprint | NOT_STARTED | No executed matched comparison. |
| E03 curved stiffener | NOT_STARTED | No executed matched comparison. |
| E04 nonlinear GE/capacity | NOT_STARTED | No executed matched comparison. |

Known adverse evidence remains visible: F03's off-ratio mode and historical
timeouts do not select a multiplier; F05's 45 N and 42.5 N cases failed
without changing the accepted 40 N state. See the active note and
`.qualification/b3-ge-e4-pl/r8-f05-45n-ticket-dev-20260929-v1/`.
Formal F03 execution authority is unconsumed. This matrix changes no
scientific criterion, resource limit, release authority or final scope.
