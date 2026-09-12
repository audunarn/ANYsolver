# Local shell assertion-strength correction

The corrected source at a4ef59e22f50be785ba9212b29ced10912a6c755 passed its two
smoke tests and 28 full local tests (8.72 seconds, child 20.4519563 seconds,
peak 238837760 bytes, zero active processes). Those passing runs are preserved
at Temp anysolver-g3c-shell-development-hvnefda9 (smoke) and
anysolver-g3c-shell-development-o4q2tc4d (full). They are not reviewer acceptance.

Read-only review identified two remaining assertion weaknesses: snapshot
comparison checked local force but not the later P/dP spatial pullback, and
pairwise current-field covariance alone could admit coherently zero current
tensors. No source mechanics error or failed mechanics result is asserted.

This test-only successor compares the complete detached trial, including all
kinematics, chart/spatial outputs, every channel and candidate bytes after exact
passed-object mutation. A deliberately borrowed-coordinate mutant proves why
local-force equality alone misses the error and is rejected by the full oracle.
Within every record, independent source-field tensor reconstruction is now
compared to current fields using the actual checked extraction pose. Deliberately
zeroing all current fields coherently is rejected, including when both sides of
the transport comparison are corrupted identically.

Full inventory is now 29 nodes. Source adapter, runner, equations, shapes,
thresholds, all prior evidence, public mechanics/defaults remain unchanged.
The a4ef59e smoke already covers the identical source; run only the separately
frozen new full test lane in a fresh directory, then independent review. This
does not reuse or retry any consumed run. Original graph/state/recovery/full
parity obligations remain open.
