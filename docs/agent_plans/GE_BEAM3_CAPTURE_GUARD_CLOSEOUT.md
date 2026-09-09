# Captured-identity work reduction: completed development validation

Frozen source: `fec94ba119f9efbbfb93bee4828d975a553db1bf`, tree
`71afb7c3f79ef20b09cea4b6f85f09d44517c71b`. The process wave completed before
restart; resumption inspected its receipts and evidence, without rerunning it.

Cell/identity lane: 53 tests passed. Owned-state/controller/modal lane: 87
tests passed. All five children exited successfully with empty process trees.
Maximum child duration was 116.128 seconds and peak recorded tree memory was
465,387,520 bytes. Existing 600-second child, 1,800-second wave, 24-GiB,
one-thread, three-worker and native-context limits were not changed.

The same preserved N8 checkpoint was profiled before and after. Instrumented
capture time changed from 29.8973652 to 22.7481431 seconds (about 24% lower in
this observation). JSON dumps changed from 322,297 to 232,463; JSON loads from
87,917 to 189; dataclass encodings from 41,246 to 39,140. Model-identity checks
remained 9,900, total guard calls 288,380 and modal checks 2,106. This demonstrates
removed redundant encoding, not skipped callback validation. Profiling timings
are overlapping development diagnostics, not a repeated performance benchmark.

N8 packet: 2,016,359 bytes, SHA-256
`D5C263B2051CCD0799C0914AB5CE66FACF206D6FE1DB903A7CF54D9ACD56F0D9`.
Both fresh N24 captures: 16,498,745 bytes each, SHA-256
`2E4E441D62DD3422F00B80564E1607652512B4A475B945D11137CC758514C59D`.
All packets are byte-identical to their original archived factors. N24 native
capture durations were 68.977562 and 68.335652 seconds; whole-child durations
were 72.257799 and 71.655791 seconds. No controller solution was rerun to create
these captures. The regression tests exercised their usual solver cases.

Archive (122 entries, copied and reverified):
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-capture-guard-fec94ba-20260909`.
Manifest: 16,953 bytes, SHA-256
`9F86BC47422DFD87981A5D086D4192DD918FA2F541268CB24E6F6503D115D5ED`.
Audit: 1,212 bytes, SHA-256
`1A89FDB3D17BB98ECD6ECC833B0639E02467D311EDE06F14354C06E3CFE855EB`.
Raw profiles, stdout/stderr, process receipts, exact inputs, packets, helpers
and test artifacts remain preserved. No consumed command is retried.

Independent review remains PENDING. This closes the bounded development check
for the guard optimization, not beam qualification, onset agreement, state
parity, production integration or beam-shell connection qualification. No
existing B2/B3/S3/Q4 mechanics, defaults, package versions or aliases changed.
The earlier N4/N8/N12 onset NO-GO remains unchanged.

Next: separately freeze an actual N20/N24 fine-mesh onset search. The preserved
0.045/count-zero points are lower-endpoint evidence only, never initial states
for a different Programme. Obtain actual upper/midpoint equilibria and exact
factor audits; retain the conservative 2% drop AND load criterion. Use bounded
small waves and stop on failure; do not infer first-root or branch uniqueness.
