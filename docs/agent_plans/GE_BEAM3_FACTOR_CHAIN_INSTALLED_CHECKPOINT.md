# GE-B3 factor-chain installed-wheel development checkpoint

Status: **installed development checks pass; qualification incomplete**.
Independent review: **PENDING**. No production integration or release.

Frozen source: `e5b13eabb7f0b3b115d220d43979cad7134999c7`, tree
`5f9bbb598e98b102c1bb1e66f66ab9f1a3c63c3e`.

## Result

One private wheel was built from the frozen Git source archive, installed
offline into a fresh external virtual environment, and checked by two fresh
isolated processes in separate directories. The package test passed in
**172.317 seconds**, with **15 cases per process**. All **31 JSON records**
(the common result plus 30 state/mode diagnostics) are byte-identical.

The installed workers bound **87 private source files** and verified that
ANYsolver imports originated under the target environment. Research imports
and repository search paths were forbidden. Source bindings use UTF8-LF;
the disposable build used the declared CRLF text fixture. Runtime: Python
3.13.9, NumPy 2.5.2, SciPy 1.18.1. This is not cross-runtime byte equality.

The five inherited cases cover actual straight compression and tension,
a coupled curved pair, elastic unloading with retained plastic history, and
free curved rigid modes. Ten additional cases cover both per-node and batched
coordinate construction: E/R90/general rotation at reference L/h=1,000,000,
plus E/general rotation at a finitely loaded curved L/h=100 state. State
preservation, native restart/replay, signed modes and work binding are checked.
All cases remain small one/two-macro specimens, at most 42 retained coordinates.

The general-rotation covariance case that failed in the earlier installed
wheel now passes for the new factor-chain representation, with the unchanged
rtol=atol=1e-11 gate. The old failure is neither waived nor reclassified:
commit `9e2418020d09b43098da80c94b73b66a8029436d` and failed wheel
`1ef86122b5d35f9ccd35e3edf1e923c367cfcc4c284bef63223a9afdd3663e51`
remain preserved and were not rerun.

## Artifact and preservation

Private wheel: `anysolver-0.4.2-py3-none-any.whl`, **1,437,617 bytes**, SHA-256
`53da0976af61e02fe12a8b55bb008af1e5af8178a643ead435aca8111db81c6d`.
This is a development artifact: **never publish it or replace released 0.4.2**.

Common result: **27,471 bytes**, SHA-256
`5c6f850451203037eb0956de9de54f662d6705d3dba51fac0a78b4a4ae88075f`.

Archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-chain-modes-installed-20260907-53da0976af61`.
It contains **80 files, 6,344,510 bytes**, verified individually by byte count
and SHA-256 from the ordinary workspace context. The canonical evidence record
binds the source zip, wheel, source map, worker/harness, dependency artifacts,
JUnit report, subprocess streams, receipt, and every matching JSON pair.
The original temporary build, environment and evidence remain. Only verified
relay duplicates may be removed.

Each subprocess had a 180-second wall limit, one numerical-library thread,
hidden Windows process creation and process-tree termination on timeout.
There was no automatic retry. These were small correctness tests, not a
formal resource/performance run; no resource request or ledger was changed.
Historical P3 authority supplied dependency artifact hashes only.

## Remaining programme

This closes the tested package defect for the private successor, not the
complete beam qualification. Next is high-contrast accuracy of the nonlinear
controller's variational operators, which still use the preserved assembly.
Broader curved/slender convergence, tension/compression and postbuckling,
V5 displacement/arc-length controls, general nonlinear/fibre sections,
loads/solver/runtime parity, and objective eccentric/curved beam-shell
connections remain open. Independent review and full formal qualification
are required before public integration.

This checkpoint adds only research, tests and evidence. Existing B2/B3,
Q4/S3, accepted straight beam, mechanics, defaults, aliases, dependencies,
package versions, workflows, tags and releases remain unchanged.
