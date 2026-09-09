# Actual curved active-plastic arc material smoke: pass

Frozen candidate `334d87260488d907a4bdb6f0985c3589c61b446b`, tree
`46bb68d34ce2c7b18bcda40daf2d798ae1000587`. All five research-only implementation
paths were committed cleanly before mechanics. The pre-freeze analytic/mutation
inventory passed 26 tests. The frozen smoke's separate unit inventory also
passed 26 tests before its three serial scientific workers.

The native arc controller completed the actual three-step curved cantilever
history. All eight stations had positive plastic increments at EVERY accepted
step. Owned full-history and native-created prefix replay reproduced origins,
histories, work and recovery without modifying committed state. The fresh
independent checker loaded no ANYsolver, NumPy or SciPy modules; it audited
all 24 station/increment records using the 96-digit primal KKT oracle at each
original increment origin. No elastic-reference substitution was used.

Maximum normalized material disagreement by increment:

- Step 1: `6.363045628481945e-17`.
- Step 2: `1.3484915352220253e-16`.
- Step 3: `1.6339480115492538e-16`.

These pass the frozen 1e-11 limit for resultants, plastic history, accumulated
strain, incremental/stored/dual energy, dissipation and sampled constitutive
tangent. The original high/low pairs remain in the capture. Tangent comparison
uses the explicitly rounded station resultant, as preregistered; this is not
an exact paired or independent whole-beam tangent claim. All three native
accepted states also satisfy their full residual/arc-gap/correction gates.

Terminal: `PRIVATE_ACTIVE_PLASTIC_ARC_MATERIAL_SMOKE_PASS`.
This verifies this actual active-plastic material path under the arc owner,
not merely an elastic test or a different distributed-force controller.
It does not yet qualify interruption/resume, cancellation, unloading/reversal,
two connected macrocells, postbuckled branches or the complete element.

## Process and preservation

Session8896 completed exit0. All four workers (unit, full solve, native capture,
independent check) completed successfully with empty process trees. Whole wave
13.399140 seconds; longest child5.732991 seconds; peak tree161,529,856 bytes.
These are diagnostics, not a general performance claim. The one-thread,
24GiB/600second child,1800second wave and existing native/inactivity bounds
were not changed. No automatic retry or consumed-output reuse occurred.

Archive with all33 entries byte-verified after publication:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-plastic-arc-smoke-334d872-20260909`.

- Manifest3456 bytes, SHA-256
  `6F329CFCD4E9422C9863EDC1912D2A1298B69ACE599977B050FB659025595002`.
- Audit1823 bytes,
  `D82F6E45C0E986F7A67A7CF12C48F9D057DBE895161B35B3490BBD919A714D72`.
- Canonical aggregate703 bytes,
  `85C695B794134FEEC1971AB7DC95A868926E34D049E76333BA7EA547AA06BD68`.
- Complete checkpoint36334 bytes,
  `29C1D272C7C24328265434EFC5F5D36C8C42C1C9895AB7A4F8C99B8333B6E062`.
- Native capture84264 bytes,
  `9D4D4954F0494CABB049AFE984632BC6DCABC07D53AD6A13938AB04075DDFE13`.

Original temporary output, raw evidence, source, preflight, logs and process
receipts remain preserved. The archive audit independently recomputed the
material result from the saved capture and checkpoint without native solving.

## Next gate and full remaining scope

Freeze the one- and two-macro active-plastic state lifecycle: compare actual
uninterrupted and paused/resumed same-programme solves byte-for-byte, inject
cancellation at step2 before assembly/trial/commit AFTER step1's verified
plastic history, require the exact preceding checkpoint and identical resumed
completion, and reject resealed origins/histories/predictors/programme/work.
Rehearse the complete lifecycle before two fresh deterministic formal cycles.
Do not rerun the completed fine-onset campaign. No explicit mid-history load
reversal policy exists in the current arc programme; add one only through a
separately frozen successor, not by changing stored predictors.

The full production goal remains active: true spatial postbuckled branches;
full material/fibre/load/mass/recovery/state/solver/restart/linear-transient
parity; current retained curved public18DOF integration; complete environment
attestation; independent review; installed explicit selection; and objective
eccentric/curved beam-shell connections. The earlier straight public facade
is not the current retained curved/generalized candidate.

Independent review PENDING; production_qualified=false;
restart_cancellation_qualified=false. NO_GO_PRODUCTION_RESTRICTION_UNCHANGED.
Existing B2/B3/S3/Q4/defaults and main remain unchanged. No push, merge, version
change, tag or release was performed or authorized by this private result.
