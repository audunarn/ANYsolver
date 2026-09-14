# Independent confirmation: isolated SO(3) kernel only

Subject `3defc6fa57fc106ef7d5b576b0a33433d6704035`, tree
`5d71910b4bcc64b328ebbdcffaad92212ad3db55`. Separate reviewer
`/root/g3b_independent_review` accepts the isolated, unrouted private kernel.
There are no outstanding findings within this exact scope.

## Source and authority review

Reviewed the full kernel, test/oracle connection, bounded runner, design and
prior diagnostics. Stable coefficient evaluation matches the mathematical
contract: differentiated Horner for the frozen series, half-angle cosc outside
the series region, and closed Log evaluation away from cancellation. The
relative chart cut and analytic continuation for slight trace roundoff remain
unchanged. The kernel imports only permitted shared arithmetic helpers, not
old coefficient/rotation entrypoints. No existing caller is redirected.

The separate source/lease audit verified all 3318 frozen files against immutable
Git blob identities, all six author/reviewer leases, exact eight-added-path
extent from the diagnostic closeout, clean tree, and diff-check. No inherited
file or shared source changed. The independently authored Decimal oracle is
copied byte-identically and has no solver or NumPy imports. All raw process,
stdout, stderr and lease hashes are in the canonical confirmation receipt.
The audit used one Git tree inventory, not thousands of per-file Git processes,
and completed in 0.682 seconds.

## Prior finding disposition

Initial subject `38a983f` had passing author runs, but its set-based grid dropped
negative zero. Those runs remain incomplete-coverage historical diagnostics.
The test-only successor retains both zero signs explicitly and asserts/records
their execution. It also compares full-Jet values, gradients and Hessians
separately, including covariance; one large group cannot hide another's error.
Kernel bytes are unchanged by this correction. The preliminary assessment is
preserved separately; no earlier passing run is retroactively reclassified as
complete confirmation.

## Separate confirmation inventories

| Lane | Author result | Independent result | Independent child time | Peak tree bytes |
|---|---:|---:|---:|---:|
| Static isolation/authority | 3 passed | 3 passed | 25.302 s | 143556608 |
| Scalar accuracy/bounds | 3 passed | 3 passed | 26.005 s | 141451264 |
| Full-Jet accuracy/domain | 4 passed | 4 passed | 25.701 s | 146120704 |

Every child used the registered isolated process wrapper, one numerical-library
thread, 24-GiB tree limit and 600-second ceiling. Three independent workers ran
concurrently after the author workers finished. Each ended with exit zero and
zero active descendants. No retry or mechanics/graph test was performed. The
only stderr content was the known nonfatal Git global-ignore permission warning.

Scalar Exp tested 68 arguments, including both zero signs, minimum positive
subnormal, old/new switches and neighbours, and the selected range through
(2pi)^2. Log tested 57 arguments including its relative boundary and both
switch sides. Full-Jet Exp and Log each tested twelve curved-input/matrix cases,
plus principal identity, covariance, rejection and no-clipping checks.

Worst normalized scalar errors were 9.194034422677078e-17 (Exp) and
4.3226846911180474e-16 (Log). Worst full-Jet group errors were
2.6996973722348944e-16 (Exp) and 8.857026259447574e-16 (Log).
The independent and author diagnostics match exactly, and corresponding input
leases are byte-identical. All required comparisons retain 1e-11.

Independent raw directories under the local Temp root:

- static: `anysolver-g3c-so3-kernel-q0o0bp8x`;
- scalar: `anysolver-g3c-so3-kernel-u05nm7ut`;
- full-Jet: `anysolver-g3c-so3-kernel-8d716id4`.

## Next gate, not implicit integration

This result permits preparing an explicit private successor dependency graph
that binds the kernel and precise native/local/joint/chart callers. That graph
requires separate source-authority and implementation review before execution.
No process-wide monkeypatch, dynamic code cloning, silent shared-source hash
replacement or public routing change is authorized.

The earlier mixed-owner directional failure remains failed historical evidence;
these elementary tests do not prove the assembled discrepancy is cured. The
unchanged component diagnostics and bridge directional gate at every registered
step must pass after separately authorized integration. Full graph/restart and
G3c confirmation remain outstanding, as do conventional Q4 finite physical
recovery and B2 clamp-domain recovery. No public replacement, defaults, release
or full-parity claim follows from this kernel confirmation.
