# Native fibre finite history — experimental development, 30 September 2026

**Implemented and verified within the stated slice; no qualification gate closed.**
Solver product `7adee4f511fb173a5fbaef8e30938e7dbd0ba076`; consumer tests
`268001efc9102b46ffeb6ea776472a26205b4152`, unchanged consumer runtime `a615c4b`.

The existing sparse finite point owner now retains native physical-fibre and
mixed generalized/fibre material histories. Both the last material predecessor
and resulting history are owned and published atomically. Native station
strain/stress/plastic-increment recovery uses that predecessor and verifies the
resulting history. New binary native-material V7 stores all high/low components
in compiled model order; restore repeats the native update and requires exact
history equality before publication. Corrupt histories, alternate JSON V7,
rejected trials and cancellation leave accepted state unchanged. Generalized
checkpoint kinds/identities, equations, material tolerances, defaults and version
are unchanged. Recovery does not replay the full accepted loading path.

## Executed checks and artifact identity

- Final source: **41/41**, 252.02 s, including legacy finite regressions.
- Fresh installed solver: **62/62**, 255.78 s; two public Q4 fibre-history
  examples also complete pure/mixed load, restore and unload. Supervisor:
  280.4420938 s, 242937856 B peak process-tree RSS, exit 0.
- Installed ANYfem: **4/4 selected**, 5 unrelated cases deselected, 26.47 s.
  Pure/mixed reference-linear inputs and partial-yield Q4 finite inputs preserve
  experimental native definitions on save/reopen; fresh restore and unload agree
  with uninterrupted execution. Supervisor:29.8077037 s,216891392 B,exit0.
- Python3.14.2; actual BLAS pools one thread, actual Numba threads1/JIT disabled.
  NumPy2.4.6, SciPy1.17.1, Numba0.65.1, pytest9.0.3, ANYmaterial0.2.0,
  ANYmesher0.5.0, ANYfileio0.3.2. Full **385 solver +97 consumer** Python-module
  catalogs match source/wheel/site byte-for-byte;269/270 imports stay onsite.
- Solver wheel SHA256:
  `909f26ce982470dec3c2030ea72f78b227085672855c67b99897579c7872a531`.
  Reused unchanged consumer wheel:
  `ff143e5fece9dd4cec261aa69edbec03acc801d3d0bbfcb90cea7519d814f0c0`
  from the adjacent fibre-linear evidence. No consumer runtime rebuild needed.
- Independent solver state/code review leaves no consequential finding in this
  experimental slice; the parent independently inspected the consumer author's
  test changes. See [review](review.md), exact manifests, XML inventories,
  imported-site records, raw consumer inputs, logs and supervisor outputs.

## Retained failures and open mechanics

Passing regressions include two pure-fibre S3 **completion-or-truthful-failure
contract checks**. They are not successful physical-case qualification.
Positive finite evidence covers elastic Q4 pure/mixed and elastic S3 mixed
histories, plus Q4 pure/mixed partial-fibre yielding (one weak fibre; other
fibres elastic). It does not establish full-section yielding or pure-fibre S3
convergence, independent material accuracy, G3 or complete V15/V16 coverage.

The source folder preserves every development failure:
v1: one Q4 success, mixed S3 at100 N failed backtracking;
yield-v1: all four fibres with100 kPa initial flow and1 GPa hardening failed;
diagnostic-v1: matched physical S3 at1000 N completed,100 N stalled, strong
Q4 yield failed. Its `generalized-s3` label actually names a **Q4** control;
it must not be used as a matched S3 comparator.
v2: two elastic successes, strong yield still failed with incremental targets;
v3: repaired partial-fibre Q4 slice3/3;
v4: pure-fibre S3 elastic failure after2 successes;
v5: pure-fibre S3 partial-yield failure after5 successes;
v6: final41/41 state/compatibility regressions. No tolerance was relaxed.
These Level-A probes were not prospectively frozen qualification campaigns;
their logs, commands and known physical input variations are retained, without
claiming an exact original full-source catalog for each early probe.

Wheel buildv1 failed because pip attempted an inaccessible cache directory.
Buildv2 used `--no-cache-dir`; the environmental failure remains retained.

Still required: simultaneous shell J2/fibre histories, integrated native stored
energy/dissipation, robust strong-yield/pure-S3 response, broader histories and
chart coverage, lines/footprints, independent mechanics/material acceptance,
external references, scale, complete consumer persistence and final artifacts.
The V7 restore verifies endpoint plus last update, not trusted full-path
provenance. G0B/G1 acceptance/G3 remain open. No speedup, release, publication
or main-merge claim follows from these timings or checks.
