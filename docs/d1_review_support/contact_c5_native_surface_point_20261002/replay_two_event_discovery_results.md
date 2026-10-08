# Native two-event discovery — implementation target changed

Base259a7acc. Source hashes/resource records in matching JSON. Raw logs,
effective runtime/selection, diagnostics and rejected connected source are in
matching ZIP. The compact `replay_two_event_witness.json` binds the original
savedsecond fixture by SHA256 and records roots plus the actual query failure.
All executions used the development runner,JIT off,180s/953MiB. No coupled run.

## Actual mechanics finding

At materialxi0.7244843513242318,angle3.1990185900472157, captured segment1:

- Endpoint gaps6.9740e-10m and6.9321e-10m are positive.
- Midpoint gap−9.3994e-11m is negative.
- Closing is bracketed in[.3125,.328125],root.3281182052876165.
- Opening is bracketed in[.671875,.6875],root.6732072408988641.
- Root residuals4.95e-19m and7.38e-20m.

Angular front isolation at t=.5 finds a stationary zero at
xi.7244843413242318,angle3.1990185900472157, with gap−2.99e-18m and
rate2.17e-19m. Analogous witnesses at t=.25/.75 are retained. These are
diagnostic sign brackets/residuals, not exhaustive spatial certification.

The actual `NativeSurfaceHistoryField.query` at the nearby two-event point fails
after3pointpaths/18certifiedintervals with:
`native/S3 material history path requires subdivision: opening/closure or facet exit`.
This is a real point-level missing capability beneath the aggregate support failure.
The fixture is retained as a failing development test; no XFAIL conversion.

## Work and disposition

Convex target-plane origin uses exact-simplex coefficients and compensated
edge-relative position/velocity. Padding includes pre-cancellation and normal/rate
conditioning. Two independent70-digit Decimal controls on a thin deforming target
near/far by2^20 pass; the hidden pulse cannot be falsely certified. Initial controls
failed for unavailable mpmath, then a mismatched fixture anchor. Both failures
remain; fixture anchors corrected, environment unchanged.

Correlated rate q=g_t−kg preserves axial gap/rate correlation. k is fixed and
finite per slab; q=g_t at zeros. Its spatial bounds and |q_t|≤M2+|k|M1 are
reviewed; padding includes |k| amplification. Real gap/rate bounds stay separate.
Five new core/validation controls pass;14geometry controls and24support controls
pass in the respective recorded runs. Reviews found no consequential formula
defect; padded binary64 is not outward-rounded interval arithmetic. Source review
is not cross-family or engineering acceptance.

Connected savedsecond still fails support128 after240queries:58proof panels with
convex origin,62with correlated rate. The connection is removed. Helpers remain
unpromoted. The at-most-one-crossing predicate cannot admit the demonstrated
two-event neighborhood, irrespective of tighter bounds. No successful solve or
speedup claim follows. Largest sampled process memory in this slice200847360bytes.

## Next implementation

Stop single-crossing bound tuning for this fixture. Implement bounded event-by-event
material replay inside each actual captured segment, including moving-root work
and derivatives. Verify the exact query and an analytical two-event case with
independent force/work/tangent controls. Then make historical-support integration
aware of those fronts. No dropped history, negligible-pulse assumption, changed
tolerance or increased budget. Aggregate/coupled continuation waits for local
success. Full C0–C9, native second-load/restart and acceptance remain incomplete.
