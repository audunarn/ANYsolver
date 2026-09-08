# Adaptive continuation and nonlinear restart: blocked closeout

Freeze: c2ed59145118e884c2b5ccf4c450af0f92a6a3ca,
tree 7db9d44270d9b77ad5fc91fedbd9be4839dc5298.
The freeze added only the research test and plan. This closeout adds only
status, archive binding and this note. Existing mechanics and defaults,
including qualified Q4/S3, remain unchanged.

## Separate inventories

- Nonlinear restart rehearsal: 2 tests, 12 scientific files; passed in 91.63 s.
- Nonlinear restart cycle A: 2 tests, 12 scientific files; passed in 85.00 s.
- Nonlinear restart cycle B: 2 tests, 12 scientific files; passed in 90.62 s.
- Adaptive arch rehearsal: 1 test, 7 scientific files; passed in 538.71 s.
- Adaptive arch cycle A: incomplete test report; 3 partial scientific files.
- Adaptive arch cycle B: incomplete test report; 3 partial scientific files.

All restart scientific files match byte-for-byte across the three invocations.
Each final restart packet also matches its earlier archived completed target.
Eight positive plastic stations remain; exactly one pending step was executed
for each accepted-prefix/cutback-prefix restart. Source programmes and the
original rejected trial were not rerun; full accepted-history replay remained.

Both arch supervisors exited 1 with bounded test deadline after step 3
committed, at complete_history_roundtrip. The common saved checkpoint is
6,638,985 bytes, SHA-256
B5EF94DE2FB01B76A4444E31E40D129D3E41DEF29709C700890CBBE0B14C99B0.
Matching intermediate bytes do not establish completed validation.
Neither replica produced unit.xml, final comparison or station assessments.

The watchdog error branch combines 600-second wall and 120-second CPU
inactivity. It omitted final elapsed/accounting values on failure, so the
precise trigger and final resource measurements are explicitly unavailable.
Do not invent them. The process-job finally block terminates/closes the tree;
subsequent read-only process inspection found no beam Python workers.
An unrelated ANYtrade process was untouched.

## Disposition and preservation

BLOCKED_GE_BEAM3_PROCESS_OR_EVIDENCE.
The passing rehearsal is not a replacement for the required complete replicas.
This is a process/evidence block, not an observed mechanical contradiction.
No worker was retried, no bound relaxed, and no historical evidence changed.

The new external archive contains 87 data files plus its manifest; all
byte counts and SHA-256 values were verified. It preserves commands,
supervisor outputs, complete successful results, both interrupted folders,
the earlier rehearsal-only audit and the explicit final blocked audit.
The canonical archive record binds their exact location and hashes.
Original temporary run folders are retained; only verified duplicate staging
may be removed.

## Next work

Freeze a successor that separates continuation, complete-history validation,
and station/reference assessment into hash-bound bounded processes. Preserve
all current replay, canonical roundtrip, source-prefix and scientific checks.
Record wall/inactivity causes and final accounting distinctly. Do not reuse
this blocked gate as passed or automatically rerun its failed commands.

Full qualification remains incomplete; independent review is PENDING.
Broader slenderness/spatial stability, physical mass/modal/prestress/buckling,
load/material/state parity, installed public integration, environment
attestation and objective beam-shell qualification remain required.
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
