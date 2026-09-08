# Bounded actual-preload Euler point waves

Base: 60e42facb4013866dafec8239755dcf87180adea. This is a research-only
scheduling successor, not a formulation or tolerance successor. Preserve all
prior sources and archives. B2/B3/Q4/S3, defaults, public APIs and mechanics
remain unchanged.

The identical evaluator is extracted from test_ge_beam3_retained_prestress:
each preload performs a virgin actual nodal Newton programme, complete accepted
checkpoint and authenticated current-rest factor capture. Both bending spectra,
exact structural-zero partition, fixed axial/torsional families, analytical
displacement/reaction checks and N1 full-spectrum comparisons remain identical.
The old monolithic test remains available with the same search and serialization.

Each worker receives a canonical SHA-bound assignment naming source, mesh count,
point index, exact binary64 load and a bound complete preceding transcript.
The initial family proof is separately verified before/after use. No generic
cached state, skipped mechanics, manufactured preload or retry is allowed.
Standard-library scheduling independently reconstructs the same four initial
loads and 18 bisections, validates every row and preserves the final buckling
record's exact schema and bytes. Every request/output directory is exclusive.

At most three mesh searches advance concurrently, one live worker per mesh.
Each point has one numerical-library thread, 24 GiB process-tree memory,
600-second wall time and 120-second CPU-inactivity protection. A wave has a
hard 1800-second limit. Failure stops further dispatch, joins all workers after
process-tree cleanup and preserves external diagnostics; no aggregate is
published for a failed/incomplete wave. Complete results are canonically staged
on the same volume and published with an exclusive atomic hard link. Pending
files are retained as diagnostics. No production or qualification GO is implied.

Commands, from the frozen worktree with C:/Python/Python314/python.exe -B:

`-m docs.reference_cases.ge_beam3_retained_prestress_wave --run --revision COMMIT --meshes 1 2 4 --output FRESH_EXTERNAL_PATH`

The coordinator alone dispatches `--point ASSIGNMENT --expected-sha256 HASH
--output FRESH_EXTERNAL_POINT_PATH`. Authority checks precede scientific imports.
Run disposable scheduler/serialization/mutation/process-tree tests plus the six
original partition checks first. Rehearse 1/2/4 and require every one of their
45 numerical files to match the bound 16bef8b archive. Only then run N8 once.
If successful, run two complete fresh-directory waves for meshes 1/2/4/8,
requiring byte-identical aggregates and per-point science. Keep separate test
inventories and raw timing data; failure never authorizes automatic retries.

Unchanged acceptance: tension > unloaded > compressed > 0, a negative upper
root, 18 bisections, opposite-sign bracket width/Euler <1e-5, decreasing error
with refinement, finest N8 Euler-load error <2%, all original 1e-11 checks.
No finite spatial postbuckling, public selector, environment completeness or
independent review claim is created by these reference-case results.
The full straight/curved GE-B3 and objective beam-shell connection goal remains
active. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
