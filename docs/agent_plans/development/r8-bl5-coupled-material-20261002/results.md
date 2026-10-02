# Coupled Q4 J2 / generalized BL5 material candidate — 2 October 2026

Status: IN_PROGRESS, uncommitted candidate; not installed-qualified or accepted.
Base solver c32782ed, ANYfem eaed5ec. Distinct coupled material policy/schema reuse
the existing objective Q4 J2 adapter and preserve previous policy meanings.

Independent source review found a missing outer checkpoint dispatch; corrected.
Review otherwise found no consequential admission/lifecycle defect. Q4 local J2
needs predecessor plastic strain/alpha, not predecessor coordinates. Both domains'
accepted/predecessor arrays are stored and replayed before atomic publication.
Rebase checks both histories. This is source review, not mechanical acceptance.

Initial100N solve was shell-elastic (maximum Mises254135.818Pa versus1MPa limit).
The500N discriminator was chosen above its estimated394N yield onset, without
changing material laws. P0 monotonic500N source smoke passed simultaneous yield,
exact checkpoint/rebase and1.1 continuation (32.81s). Shell alpha1.62815e-6 and
beam alpha1.18574e-5. A test error restoring twice into the same owner was fixed.

Full two-basis signed-history test FAILED (236.63s). P0 passed actual yield,
cancellation, tangent, rejected-trial isolation, rebase/recovery and charted
restore, then exhausted four cutbacks approaching the negative endpoint. Coarse
P1 remained shell-elastic at500N; this is not proof its material path is defective
or qualified. No load adjustment/refinement sweep followed that finding.

The bounded P0 repeat saved durable prefixes and actual attempts. Accepted programme
positions:0.5,1,1.25,1.75,1.875,1.9375,1.96875,1.984375. Last load is-484.375N.
Target2 (-500N) fails with relative equilibrium0.0255676 and gap1.17835e-13.
This is NOT the zero-load boundary. Do not claim equilibrium or formulation failure.
Positive yielded tangent errors were1.35e-8,1.35e-10,5.94e-12 over decreasing steps.

Replaying just the final failed increment takes about14.7s. Its Newton-direction
finite differences were step-sensitive. Normalizing physical direction gives Q4
error1.42e-9 at the smallest tested step, but beam relative errors do not establish
a plateau (predicted weighted beam response0.118 versus shell1981); constraint
relative errors divide by a near-zero7.72e-14 prediction. These diagnostics do not
identify a tangent defect or qualify that failed state. Next discriminate the
local beam derivative/cancellation contribution at this saved state from a valid
mixed Newton direction that the current search fails to globalize. No tolerances,
search policy or scientific criterion have changed. Do not rerun the full history.

ANYfem strict coupled-v4 source tests passed3/3 in22.78s (supervised23.633s,
peak188690432bytes). They cover exact J2 persistence, prior-format isolation and
P0 monotonic dual-domain yield/rebase/checkpoint continuation. No signed-reversal,
coarse-P1 yielding or installed-consumer claim. Worker diff independently inspected.

`diagnostics-v1.zip` SHA256:
`3462c0ed07e253071d0d2f97ea2fdfca44a78df0278d64311d5be3b14ac261a0`.
Includes failed/successful raw logs, safe metadata, diagnostic runners, candidate
source hashes and binary accepted prefixes; full environments excluded. Direction
run-v1 failed from using a compiled rather than public programme and is retained.
Prepared installed runner has NOT run. Public candidate remains uncommitted while
the failing requested history is investigated. No F03 authority consumed.


## Native-scale correction and bounded decision (supersedes next-action text above)

Native virtual work establishes two retained force triples followed by four
moment triples. Only the new, unaccepted coupled policy now uses that role map;
legacy policies remain unchanged. Its model identity includes
`native_force_moment_roles_v1`, invalidating older candidate checkpoints. This
prospective correction invalidates reuse of earlier candidate pass claims, not
historical evidence. Tolerances and physical material laws are unchanged.

The corrected-scale source run passed admission/legacy-isolation but still failed
the same signed reversal (1 passed, 1 failed; 234.24 s). It accepted -484.375 N;
the failed -500 N trial had equilibrium ratio 0.02556734374 and gap 1.17826e-13.
Smaller fractions expose only a tiny decrease near 2^-20. No search budget change
was made. A congruence-scaled diagnostic solve reduced weighted linear residual
from 3.82e-4 to 1.19e-9 (one refinement 1.16e-10), but the same corrector still
failed. No product factorization change follows from that experiment.

The 134-row bounded fresh-chart tangent was symmetric to about 1e-16. Its smallest
positive scaled eigenvalue was 3.65e-5 at reference, 1.14e-5 at accepted state and
1.27e-8 at the failed trial. Inertia remained 56 negative / 78 positive. The
sensitive vector includes nodal and retained components. This is KKT sensitivity,
not evidence of a physical limit point: the failed state is off equilibrium and
compared constitutive predecessors differ. No matrix symmetrization was used.
Independent OpenAI read-only review confirmed this interpretation and transform;
it is not cross-family or scientific acceptance.

Decision: stop this reversal diagnostic batch. Before introducing a separately
admitted continuation controller, inspect the existing sensitive direction's
coupling to the actual programme load derivative and a physical displacement
control, and the corresponding bordered operator. That bounded design check may
select a control; it cannot establish stability or change plastic path semantics.
Keep the original force-controlled signed-history failure open.

A distinct P0 monotonic lifecycle check on corrected scales passed in 41.13 s
(41.92 s supervised, peak 177307648 bytes): simultaneous yield, cancellation,
actual-update tangent, rejected-trial isolation, chart rebase, exact checkpoint
and continued-state parity. The original two-basis signed-history test is retained
without xfail/skip or relaxed assertions. Diagnostic prefixes now use pytest's
unique temporary directory rather than overwriting a shared evidence path.

`diagnostics-v2.zip` SHA256:
`6ffe725a6c170ae01be35a566e33997c17cb6187f406142fb182c9666e11bf57`.
This supplement preserves corrected source, raw bounded diagnostics and prefixes;
v1 remains unchanged. No full environment mappings are archived.


## Installed bounded verification

Five selected checks passed in 129.60 s (131.67 s supervised; peak183013376 bytes).
Wheel SHA256 `87146a8c0946ade59a2abba3f4c71478250d337f672ad4a8d04aed126bec6410`;
398 source/wheel/site modules matched, all219 imports came from the isolated site,
JIT disabled and both numerical pools used one thread. Checks comprise the new
monotonic lifecycle and native-scale/admission check, existing generalized BL5
pre-yield isolation and P0 reversal, and existing coupled point-material lifecycle.
The failed new coupled signed-history tests were not rerun or counted as passes.

`installed-v1.zip` SHA256:
`87524069926b0da9a2d2d724bf228d153c6cebb94b89bdc09c2b39346513ec6c`.
No full coupled-envelope, installed ANYfem or scientific acceptance follows.

ANYfem coupled-v4 affected source checks rerun against corrected solver: 3 passed
in33.41s (34.26s supervised;188780544-byte peak). Logs in consumer-source-v2.
No installed consumer claim. All owned jobs completed; no run remains active.


## Displacement-control foundation

The bounded loaded-tip control design check took2.70s. At the failed state the
normalized load and control projections on the sensitive direction are0.30687;
bordering the actual nonsymmetric Newton operator increases its smallest scaled
singular value from1.2664e-8 to3.6326e-5 (condition1.741e8 to6.069e4). This selects
loaded beam105 global-z displacement as a useful bounded control candidate; no
physical stability or capacity acceptance is inferred.

A new private sparse displacement corrector solves [K,-p;e,0], retaining all native
coordinates and multipliers. It returns only uncommitted trials. Its independent
amplitude is not a staged-programme cursor. The first trial implementation failed
backtracking: an equilibrium start with unmet control is unsuitable for the old
combined initial merit. Independent review recommended a full displacement
predictor, followed by fixed-displacement corrections with fixed dual-work residual
merit. Domain-invalid predictors fail without silently shortening the target.
Equilibrium1e-8 and compatibility/control1e-9 remain mandatory for return.

The revised corrector reached the saved target -6.609120036e-5m at -487.8411433N,
equilibrium8.05384e-10, gap1.37550e-17, zero displacement error,6 iterations and16
evaluations (8 rejected trials,6.15s). The accepted checkpoint was byte-identical.
This does not complete the -500N force-controlled endpoint. No state was committed.
Subsequent review added exact accepted-endpoint affine-load binding; all predecessor
identities are captured/rechecked and input loads copied read-only. Trial outputs
remain mutable internal data. Public publication must rebuild recovery, revalidate
and atomically commit with a distinct controller/checkpoint identity.

The initial algebraic checks pass singular/nonsymmetric borders and fixed-control
rejection. The first lifecycle test failed attempting to mutate an already-read-only
fixture load; the fixture now copies that input. Failure evidence is retained.
No installed verification is claimed for this newly added private corrector.

Initial design/failed predictor archive control-design-v1.zip SHA256:
92dd99bc0f6b2a84ae5c632f5212979e9f6a0b39be9cf91796163e173a458ca2.

Final private-corrector source suite:4passed,27.41s supervised,176041984-byte peak.
Covers actual yielded trial, no publication, cancellation, stale histories, owned
loads and mismatched affine endpoint rejection. Archive displacement-corrector-v2.zip
SHA256 `faad931e6af2057aecfa5fd486dd95bc636566c6f668a133de59e6efc122f273`. All owned runs terminal.


## Shared publication preparation

Extracted the existing force/staged accepted block into `_publish_equilibrium`.
A direct comparison against retained diagnostics-v2 source confirms the moved
body is identical after indentation and hook-parameter rename. Five source
lifecycle checks pass in71.46s (72.38s supervised;177639424-byte peak), including
coupled monotonic cancellation/rebase/restart and private displacement trials.
No public displacement commit or checkpoint is implemented by this refactor.
The requested independent extraction review failed at model capacity and remains
outstanding; direct source comparison and test evidence do not replace it.

Checkpoint design review before that failure confirms a distinct controller
envelope AND mechanical kind are needed. Store actual applied load, accepted and
predecessor histories, anchors/witness and physical state. Keep accepted generation,
material-step count and control progress distinct. Preserve an authentic seed
checkpoint/hash; do not invent positive force factors. Restore through an isolated
owner, validate affine-load/target/pose and endpoint material replay, then publish
once. Endpoint replay does not authenticate the full earlier history.

Archive publication-extract-v1.zip SHA256 `c6ae3a65ea89ab9d6bbbf90520e2c415bbd73e92e0ce04392a02b4273e4c21ab`.
All owned runs terminal. The installed wheel above predates this extraction and
the private corrector; these latest changes have source verification only.


## Separate displacement snapshot framing

Added a private controller envelope and separate binary mechanical schema. It
stores actual affine applied load, seed endpoint/digest, signed amplitude and
actual displacement-step records, physical arrays, anchors/pose witness and both
accepted/predecessor material histories. Generation may include chart events and
is not required to equal displacement-step count. No synthetic force factors.
Seven framing tests pass (latest4.03s supervised,176357376-byte peak), including
signed amplitudes, read-only owned decode, corrupt bytes, mismatched history/load/
target/shape/control/digest, and refusal by ordinary force restoration without
publication. Test states are framing fixtures, NOT mechanically validated states.

Decoding validates representation/controller consistency only. Mechanical replay,
pose/material admissibility, recovery and atomic publication remain unimplemented
for this controller, so no public restore or persistence capability is claimed.
Independent review remains outstanding following the earlier reviewer capacity
failure. Latest additions have source checks only, no installed claim.
Archive displacement-checkpoint-v1.zip SHA256 `80d8947f4f1aa053735d6e13c328e8451354cb2d851aefda8237b5f070569238`.


## Isolated mechanical endpoint validation

Private validate_endpoint now checks coordinate/support/load layout, physical
frames and shell pose witness, nonnegative/admissible material state, and replays
from saved shell and beam predecessors in a copied owner with its own driver/lock.
It requires unchanged equilibrium1e-8, compatibility1e-9 and existing64-epsilon
material replay agreement. No generation or state is published to the live owner.

Eleven focused source checks pass in29.90s (30.66s supervised;177680384-byte peak).
A real yielded displacement trial round-trips physical coordinates and endpoint
equilibrium. Rechecksummed altered shell history, invalid beam frame and matching
but mechanically changed affine load are rejected, preserving live checkpoint.
Cancellation/stale-predecessor/ownership and framing negatives remain covered.
Independent review, installed checks, atomic controller publication and public
restart are still outstanding. Endpoint replay is not full-history authentication.
Archive displacement-endpoint-v1.zip SHA256 `0d73bd1aa7228bfce5819d8f410c249e43f8dd21058600dbfc71c49c50ff5528`.


## Public seeded displacement workflow

Added typed DisplacementControl/DisplacementResult through the existing solve
facade. An accepted force endpoint supplies the affine base; solve actions are
the fixed load direction and targets are absolute global translations. Amplitude
is independent of staged position. Each accepted trial is mechanically replayed
in an isolated driver, fully prepared, then published with controller bytes and
material histories under one owner lock. Recovery/checkpoint/restore dispatch is
explicit, and returning to force mode is rejected.

The first public test rejected NumPy scalar targets; admission was corrected to
match existing numeric conventions. Source-v2 passed8checks. Independent review
then identified unexplained generation gaps/zero history and chart coordinates
reported as physical rotations. Current V1 requires at least one actual step,
exact seed-generation+step accounting and changing adjacent targets; post-seed
rebase remains unsupported. Physical rotation vectors and separate chart arrays
now follow the ordinary result convention. Source-v3 passed9checks in34.78s
(35.59s supervised;180817920-byte peak), starting from a rebased force seed.

The public integration check covers accepted-prefix cancellation, binary restore,
continued exact state/bytes, injected prepublication failure, changed-direction
rejection and rejection of force-mode continuation. Independent review confirmed
both fixes; prior extraction review also completed without findings. This does
not confer independent scientific acceptance of the BL5/material envelope.

Adaptive displacement increments, external loads, selected recovery and post-seed
rebase are explicit current limitations and remain future programme obligations.
No arc-length, demonstrated first limit point or -500N force endpoint claim.
An isolated installed-wheel campaign is being recorded separately; source checks
alone do not qualify the final artifact or complete G4.


Installed displacement candidate:15checks passed,113.38s supervised,
187342848-byte peak. Wheel SHA256:
`f8d64a0b1fee068b534f7da668f7f23f91d889a959e63708066118fff311acb9`.
All401 source/wheel/site modules matched; all221 imports are onsite,
JIT disabled and numerical pools verified at one thread. This campaign includes
public displacement, framing, private corrector, coupled force-monotonic lifecycle
and generalized BL5 pre-yield legacy isolation. It does not include or pass the
failed full coupled signed-force reversal or qualify the complete material envelope.
Archive displacement-public-installed-v1.zip SHA256 `3e23fbefc34d39b91c9fdbeaecda96810f770d70022f1a2199d2ae8e87c32d8c`.
All owned runs completed. Source and installed bounded workflows now delivered;
scientific, consumer and full G4 acceptance remain open.


## Bounded installed continuation: failed at second target

Preregistered in the runner before execution: targets -66,-68,-70,-72 micrometres
from saved -484.375N prefix, fixed -15.625N affine direction,20 Newton/12 backtracks,
restart after the second target. Installed wheel f8d64a0b...311acb9 accepted -66um
at -487.858966N (equilibrium2.60e-10, gap9.17e-18, shell alpha1.01469e-5,
beam alpha2.50083e-5), then failed backtracking at -68um. Later targets and planned
midpoint restart were NOT reached. Accepted prefix retained. No automatic interval
extension, smaller steps, additional budget or physical limit-point claim follows.

Added immutable structured displacement failure detail (generation, target,
amplitude, iteration/evaluation/linear-solve/rejected counts and equilibrium/gap/
control errors), exported with its typed exception. Predictors now retain the last
coherent evaluated state when reporting domain failure. A patch-script assertion
stopped the first edit attempt; its subsequent test was an unchanged earlier test,
not evidence of the new fields. Corrected source integration test passed in36.07s,
including deterministic zero-correction failure counts and unchanged checkpoint.
These post-wheel diagnostics changes have source verification only.

One targeted source replay of only the failed increment (17.97s) reproduced:
5 iterations,61 evaluations,7 linear solves,54 rejected trials; equilibrium1.6250,
gap3.49e-13,zero scaled control error. This is not a small acceptance-tolerance
miss. Prefix unchanged. The failed amplitude1.02028 is not an accepted load point.
Stop the branch diagnostic batch; do not infer physical instability or promise
that smaller increments/globalization will repair it.
Archive displacement-branch-v1.zip SHA256 `6afabfd0344d874ca5ad0c2af8881285e2a260c9ca560926928a95bd641e6fff`.


## Signed displacement cutback accounting (private)

Added immutable displacement-specific attempts/progress, reusing existing bounded
AdaptiveIncrementControl limits and halving rule. Unlike force-position validation,
negative positions and reversals are valid. Controller metadata replay verifies the
attempted path and keeps spent budgets across serialization. It does not replay
mechanics. Six focused checks pass (2.18s supervised,161406976-byte peak), including
restart, signed reversal and corrupted attempt rejection.
Source/test: _stiffened_shell_displacement_increment.py and matching test module.
Raw checks: TEMP/r8-ge-pressure-source-v1/displacement-increment-state-v1.
This private state is NOT yet wired into public solve/checkpoint publication.
No retry of the failed -68um branch was made. All owned runs terminal.


## Adaptive displacement integration — 2 October

The public coupled-Q4 BL5 route now supports signed displacement cutback using
existing AdaptiveIncrementControl limits. A bounded controller envelope retains
failed work and spent budgets across checkpoint/restore, including failure before
the first displacement acceptance. Publication of state and controller is atomic.
Observer exceptions after publication propagate without manufacturing rejection.
Trial-domain rejection counts may legitimately exceed residual evaluations.

Source adaptive/increment checks: 8 passed in38.15s, supervised38.93s,
peak179863552bytes. Independent delta review found no remaining defects.
Installed complete affected slice:23passed in141.52s, supervised143.73s,
peak191438848bytes. Wheel9d133a513ca0e75c4edb5a2f99196d3f96a1c21c1ce9326c757a5634ef3e9237;
403source/wheel/site Python modules match;223imports onsite; both numerical pools
one thread; JIT disabled. Includes fixed-step/checkpoint/corrector and monotonic
coupled material/legacy isolation. No failed branch campaign was repeated.

Archive: displacement-adaptive-installed-v1.zip,
SHA256 facd9ec3d66f046c6b86221c6904c65c95a019a941f7f559f0538d0e833f9d99.
Includes prior active note byte-for-byte, fixtures, runner, identity and logs.
Execution metadata is explicitly whitelisted; no inherited environment dump.
These checks do not close the material envelope, G0/G4, capacity or release gates.


## Installed ANYfem coupled/adaptive consumption — 2 October

4 checks pass, supervised40.28s, peak190648320bytes. ANYfem wheel
cf8a36dbf65781a5461c6acb8c07c7039ed4c41dfa884c55b4ff50744da9ade3
uses solver9d133a51...f3e9237 above. All98ANYfem/403solver modules match
source, wheel and site. Imported modules are onsite; JIT disabled and numerical
pools use one thread. Tests cover strict V4/legacy schema isolation, distributed
envelope serialization, project save/reopen, simultaneous yielding, force-prefix
rebase/restart and public adaptive displacement cancellation/restart across two
nearby targets. No displacement reversal or capacity claim. Independent consumer
review found no blocking defect. No full consumer/platform acceptance implied.
Archive:anyfem-coupled-adaptive-installed-v1.zip, SHA256 6a383435d0ada66bdf8cd49b2af98b1c33fc6c40a994465eb4248ffc382f0737.
