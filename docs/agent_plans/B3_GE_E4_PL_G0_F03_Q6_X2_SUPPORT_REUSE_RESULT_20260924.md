# X2 Q6 support-row reuse diagnostic

**24 September 2026. Unregistered source-process comparison. F03/G0B open;
G1 barred.** The new candidate reuses the already assembled free shell matrix
for free-row forces and evaluates only first/last-cell support rows for
reactions. The old full-shell nodal recovery remains the default and bounded
oracle. The candidate was committed at `7dd70e72c4d1803f7b43434616de0f8a3f56aa20`
before this single supervised X2 run; main was not changed. The preserved
[V1 comparison](B3_GE_E4_PL_G0_F03_Q6_X2_SHARED_ASSEMBLY_RESULT_20260924.md)
uses a different runner revision and is a diagnostic baseline, not a paired
installed-artifact performance gate.

The [new receipt](B3_GE_E4_PL_G0_F03_Q6_X2_SUPPORT_REUSE_REHEARSAL_20260924/receipt.json)
reports `completed`, exit 0, **2,082.77 s** and 691,175,424 B sampled peak
tree RSS. The child [measurement](B3_GE_E4_PL_G0_F03_Q6_X2_SUPPORT_REUSE_REHEARSAL_20260924/measurement.json)
records **2,082.00 s** across its phases:

| Phase, seconds | Preserved V1 | Support reuse | Difference |
|---|---:|---:|---:|
| Assembly | 340.63 | 372.82 | +32.20 |
| KKT certificate | 970.11 | 819.11 | −151.00 |
| Shell positivity | 542.56 | 557.01 | +14.44 |
| Physical recovery | 94.55 | 86.55 | −8.00 |
| Spatial audit | 309.68 | 246.48 | **−63.20** |
| Complete child | 2,257.53 | 2,082.00 | −175.53 |

Spatial recovery was **20.4% faster in this one comparison**. Its nodal
recovery subphase fell from 279.65 to 227.20 s; the remaining spatial
subphases also varied. The complete-route reduction is 7.8%, but the much
larger variation in the unaffected certificate phase prevents attributing it
to this optimization. This is one source-process pair, without an installed
wheel, alternating repetitions or a frozen performance registration. The
new child duration still exceeds the draft **1,800 s** envelope by **282.00 s**.
Neither the time envelope nor F03 is passed.

The new certificate reports `CERTIFIED_WITHIN_LIMIT` and positivity reports
`POSITIVE_QUADRATIC_FORM`; each complete proof dictionary matches V1 exactly.
The canonical KKT/RHS, scaled-system archive and original shell-matrix hashes
repeat V1. The new attempt/start runner hashes match. Start/measurement record
matching spatial and nodal source hashes, and the runner rechecked those files
after spatial recovery. The operator fingerprint was unchanged at each phase.
Both runs used one-thread numerical settings. These are source-level
experimental proof results, not installed scientific qualification.

The [physical output](B3_GE_E4_PL_G0_F03_Q6_X2_SUPPORT_REUSE_REHEARSAL_20260924/physical.json)
has the same structure and all non-timing observables as V1, except the
iterative shell eigenvalue estimate changed by `1.42e-16`. The
[spatial output](B3_GE_E4_PL_G0_F03_Q6_X2_SUPPORT_REUSE_REHEARSAL_20260924/spatial.json)
has the same structure except its input hash follows the new physical JSON.
Its six support-wrench components differ from V1 by at most
`5.24e-10` in their respective force/moment units; all other physical
wrenches and work values are identical. Three scaled spatial-balance metrics
change by at most `2.14e-13`; all remain under their unchanged checks.
These tiny differences are consistent with the changed shell force summation
order, but this comparison does not prove equivalence beyond the checked
case and bounded parity tests.

The candidate passed 4/4 original bounded nodal tests after adding the
optional reuse comparison, a separate degree-6 deterministic full-matrix
force-action comparison, 13/13 combined-runner/integrated tests, and three
focused review-closure tests. The independent read-only code/mechanics review
found no algebraic defect. It required degree-6 parity and recovery-helper
source hashes; both findings were closed before this run. The independent
read-only postrun review found no integrity or numerical blocker: it checked
both receipt chains, candidate/KKT/shell hashes, recomputed physical-state
identity, proof equality, all physical/spatial values and the attribution
limits above. It did not independently rerun the full model. The raw matrix and inverse
archives remain local and Git-ignored, with hashes in tracked measurements.

The new measurement SHA-256 is
`bec325e07c4dae90b6272cdb51acbb45897393e113f4f5595a32aeac43253e26`;
receipt SHA-256 is
`51b6e7b72ccc4f39b25763b603483204a1dc33b4708f6fbb3792347e06fb1f10`.
No speedup, mechanics, installed-package, or release acceptance is claimed.
The next performance decision needs paired installed measurements and a
reviewed, prospective resource envelope. The native interface mechanics and
complete physical-observable error propagation remain separate G0 blockers.
