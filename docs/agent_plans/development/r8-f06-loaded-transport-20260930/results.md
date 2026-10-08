# Accepted-state observation and loaded chart transport — development

Source base484043fa,30 September2026. This record preserves earlier failures;
it does not amend F06 criteria, consume F03, qualify an aggregate gate or release.

Optional finite GE `on_accepted(result)` now observes every complete accepted
increment through the existing public solve. It receives a deep detached result
after atomic physical/material/controller/checkpoint publication. Reads are
allowed; reentrant writes are rejected. Callback errors propagate unchanged,
including typed numerical failures and MemoryError, without cutback. Cancellation
preserves the accepted prefix. No observer, model or checkpoint identity is added
to serialized data; absent observers retain no extra accepted history.

Wheel243b2d8a2f1b03a6f08c49624f449e6e282749203b77b37b4be7817cd8758317
is retained under accepted-observer-v1/wheels. All387 source/site/wheel modules
match; each observer campaign records210 actual installed imports, binary64
Python3.14.2, JIT disabled and one effective BLAS/Numba thread.55 current checks
pass:39 unchanged broader finite/controller/S3-checkpoint cases fromV1,
14 observer cases fromV2, and the two ownership/default-parity cases fromV3.
Their explicit inventory is observer-check-inventory.json. V1 had a stale fixture;
V2 exposed an ownership fixture's unsupported assumption that its plastic loading
would accept two targets directly. Only that fixture's load changed to10N inV3;
all ownership/default assertions remain. Both earlier failures are retained.
V3's two checks take10.6725s, sampled process-tree peak219115520bytes. These costs
are observations, not a speedup claim. Independent installed review is clear.

The stronger F06 fixture remains fixed at beam Fz1MN and opposite shell375kN
forces, factors.125/.5/1,20Newton iterations/12backtracks, rotation>=.05rad and
actual consecutive-increment commutator>=1e-5rad. V2 direct final increments
fail the Newton budget in both formulations after passing prefix/reset/restore.
V3 uses existing default adaptive cutback and the new observer. Both formulations
complete the same actual accepted path(.125,.5,.75,1) in all three branches.
Every matched successor passes physical/material comparisons; same-state hashes
and irreversible histories retain their exact obligations.

S3 meets all coverage predicates: shell rotation.1237818rad, beam.0941316rad;
commutators1.6788121e-5 and1.1080759e-5rad. Q4 reaches shell.1221956rad and
beam.0974536rad but both commutators9.9134242e-6rad miss1e-5. The reported failure
is retained without rounding it into a pass. No proportional-amplitude retry is
planned. This diagnostic is outside ordinary CI discovery; its frozen exact
source, snapshots and JUnit remain in loaded-transport-v3-adaptive.

V3's run lasts158.8295s/219443200bytes, with pytest1pass/1fail. Its final import
guard also fails: Windows8.3 TEMP directory spelling differs from resolved import
paths. The guard fails before writing the original numerical-run import manifest.
Separate import-route-v1 replays only the same frozen import route, proves the
two directory names identify the same directory, verifies209 canonical installed
imports and387 source/site modules, and executes no numerical solve. This
corroborates aliasing; it is not a replacement successful original import gate.

Decision: retain the tested observer capability and S3 development evidence.
Q4 loaded coverage and aggregate F06 remain open. Use genuinely independent
physical loading through the required model-bound staged programme if further
transport coverage is needed, rather than tune this proportional fixture.
