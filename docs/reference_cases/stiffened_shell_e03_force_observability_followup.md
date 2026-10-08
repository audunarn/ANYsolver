# E03 force observability follow-up packet

This is prepared reference tooling, not an accepted E03 result. The prior root-only RF balance failure and consumed physical primaries remain preserved. A new human “Proceed” applies only to proposal-v3's fresh150-second scope; source preparation itself launches nothing. Root must inspect the frozen packet before launching its supervisor and separately adopt the observed analytic semantics before the external phase becomes eligible.

Owned additive source is `scripts/r8_e03_force_observability_followup.py`, its focused test file, and this document. The execution packet is `.qualification/b3-ge-e4-pl/r8-e03-coarse-dev-20261007-v1/next-force-output-v1/`. Older builders, parsers, audit code, decks/proposals and evidence are unchanged.

The scalar control uses two SPRING2 elements with k12=10 and k34=20, equation u1-u3=0, prescribed u2=0/u3=.1, load p1=2 and free u4. Nonzero SPCs are inside the static step; all four nodes' unused y/z translations are fixed zero. Independently derived u=[.1,0,.1,.1], g=[1,-1,0,0], physical lambda=(g1-p1)=-1 and physical reactions r2=r3=-1. Coincident equation-node coordinates make its action objective under rigid work. The source's internal fmpc=fn_dep/coefficient=+1 differs from physical lambda for this loaded pivot.

The DAT parser follows exact release2.23 `printout.f` labels and `printoutnode.f` global i10/three e13.6 rows. It requires exactly one U and RF frame, set ALL, final time1, all four distinct nodes and three finite components each. It rejects malformed, truncated, duplicate, extra, nonfinite or repeated frames. The separately scoped printed instrumentation absolute limit1e-6 checks all twelve U and RF components. This does not replace E03's frozen DOUBLE balance limit1e-8. STA requires its two exact header rows and one completed unit-time static increment; actual stdout must declare version2.23, job completion and numerical CPU declarations all1, with no warnings/errors.

Exact release source inspected from the officially acquired archive: `printout.f` declares labels, `printoutnode.f` prints RF from fn, `resultsforc.c` subtracts/stores/restores equation action and `frd.c` exports fn. `mastruct.c` activates three translations for the spring branch. These source observations do not independently establish the pinned Windows binary's correspondence. Root must inspect the actual analytic result/receipts/runtime and create `semantics-confirmation-v1.json` after the analytic finalization succeeds. The program creates only a review candidate and never creates/adopts this confirmation.

The root-authored confirmation must satisfy the existing audit provenance schema, use `independent_analytic_spc_mpc_observable_control`, bind exact source archive/binary/source-file hashes and include an independent reviewer/reference. Its `control_bindings` must equal the actual `analytic-bindings.json`, including candidate, original DAT/STA/stdout/stderr, deck, outer process receipt and input-manifest hashes. `control_evidence_sha256` equals the actual candidate file hash. This is admissible observed-control correspondence evidence; byte-for-byte source build identity is not required. Validation of this record remains a caller-evidence trust boundary, not proof of the review's truth.

E03 changes exactly one output card: RF NSET ROOT to PHYSICAL. Reversing that replacement reproduces the frozen original bytes. Geometry, materials, elements, equations, supports and loads are unchanged. All333 physical U/FORC nodes are required; recovery retains the true49 supports. The existing strict DOUBLE reader and bounded coupled-pivot equation-force audit are reused. Actual fitted-port gaps, positive finite load work and full6 fitted tip poses retain the original guards. Recovered free residual, equation rigid work and common-origin support-plus-load balance are reported as diagnostic observables without deficit fitting, accuracy scoring or qualification. A reported recovered balance does not waive the frozen1e-8 acceptance criterion.

The supervisor reuses the prior process-start/timeout/stream/accounting implementation with fresh files and tokens. It holds an exclusive one-job lock, sets CPU0/thread1/JIT-off, records exact argv, hashes and process-wall duration, monitors treeRSS2GiB and kills the owned tree on timeout/resource failure. Independent review identified override precedence and parent-only fatal cleanup gaps, repaired here: NUMBER_OF_CPUS/CCX_NPROC_CFD/CCX_NPROC_RESULTS are explicitly1, and unrecorded CCX_NPROC overrides are removed. Fatal monitor paths terminate identity-checked recorded descendants before the owner. The outer supervisor checks recorded descendants even after the parent exits, using PID plus creation timestamp at Windows millisecond resolution; mismatch/missing physical registry or termination uncertainty blocks further accounting/launches rather than killing an unproven PID. CCX affinity inheritance is observed; numerical thread verification requires frozen inherited environment plus all actual stdout CPU declarations1. OS-thread counts are diagnostic. Sampling does not establish an absolute instantaneous memory bound.

Fresh accounting is total150, reserve60, cumulative controls20, one analytic20, one external30, and combined finalization20 split10/10. The physical tokens are persisted consumed before launch. Unknown remainder, failed attempts, mismatched inputs or attempted retries refuse. Finalization is a separate process after `execution.json` exists; actual prior resource/runtime/input/output/origin bindings are checked before any successful outcome is written. Every prior raw/partial attempt remains preserved on refusal. No previous authority is reused.

The same RLock covers CCX Popen, creation-identity capture and registry persistence, and stays held through fatal snapshot/termination. Launch cannot interleave with fatal cleanup. If identity capture or registration fails, the retained owned Popen process handle is terminated and waited directly; no guessed PID is opened. A failed termination is preserved as cleanup uncertainty. This launch/registration repair was source-inspected only, with no new execution or acceptance claim.

Deferred root commands, in order, from the worktree root:

```powershell
$packet='./.qualification/b3-ge-e4-pl/r8-e03-coarse-dev-20261007-v1/next-force-output-v1/supervise-followup-v1.ps1'
& $packet -Mode controls -Attempt controls-followup-v1 -Cap 20 -Reserve 60
& $packet -Mode analytic -Attempt analytic-v1 -Cap 20 -Reserve 60
& $packet -Mode finalize-analytic -Attempt analytic-finalize-v1 -PhaseAttempt analytic-v1 -Cap 10 -Reserve 60
# Root inspects actual evidence and independently adopts a bound confirmation here.
& $packet -Mode external -Attempt external-followup-v1 -Cap 30 -Reserve 60
& $packet -Mode finalize-external -Attempt external-finalize-followup-v1 -PhaseAttempt external-followup-v1 -Cap 10 -Reserve 60
```

Both phases/finalizations must complete before moving onward. Stop at the first failure; no physical retry, native rerun, refinement, sign/load sweep, qualification, merge or publication is granted. The unchanged431-module wheel/site payload is hash-validated; no new wheel/install is needed. `sys.orig_argv` is preserved and must exactly match the outer command; path-spelling differences refuse rather than discarding actual argv.

Prepared tests:46 by static parametrization, including fake-process fatal cleanup and thread-override refusal. All checks are **UNRUN by the author**: no imports, collection, tests or numerical processes were launched. Root's bounded checks, actual binary semantics adoption, external observations and numerical adjudication remain outstanding.

## Preserved executed failure and prospective repair

Root executed candidate25ba6f4c:46 controls passed; analytic CCX exited0; finalization failed because no periodic CCX observations were recorded. CCX stdout reports Total CalculiX Time0.0075; that printed value is not outer process-wall accounting. Direct launch CPU0/creation identity and inherited thread environment were recorded. The repaired observation gate requires that direct observation and validates every periodic row when present, reporting sample count0 honestly. This does not claim a periodic sample or weaken numerical-thread/stdout requirements.

The actual DAT has a single `S T E P 1`/`INCREMENT 1` preamble. The repaired reader admits exactly that bounded framing; unknown/repeated preambles still refuse. More consequentially, saved u4=0 and g=[1,-1,2,-2] fail the unchanged executed v3 oracle. The regression reads the preserved original DAT/STA/stdout/stderr and actual process receipt, binds their hashes, accepts framing, then requires oracle refusal. No semantics confirmation can be adopted from that response.

Observed obstruction: the saved stdout declares one reduced equation and zero lower-triangular off-diagonal entries, while the declared free node4 x equilibrium has g4-p4=-2N. Its ten declared SPCs and prescribed u1/u3=.1 are reflected in the outputs. The evidence does not allocate this mismatch to assembly, the nonzero-SPC route, the scalar solve, or recovery; no backend defect is asserted. Further investigation of that route was explicitly stopped because E03 uses zero supports.

Root adopted preparation of a separate unexecuted v4 discriminator, `mpc-support-v4.inp`. It retains the four nodes/two springs/equation and zero transverse supports, fixes only u3x=0 and applies p1=2,p2=1. Nodes2/4 x are free: from 10(u2-u1)=1 and20(u4-u3)=0, u=[0,.1,0,0]; g=[-1,1,0,0]. Physical lambda=g1-p1=-3, r3=g3+lambda=-3; both free residuals vanish and total applied3N balances support−3N. The separate fixed-oracle function `zero_support_analytic_candidate` cannot parameterize or fit the failed v3 response.

`entry-followup-v2.py` is a source-only candidate for v4, referencing future versioned manifest/snapshots and proposal-v4. Its snapshot is prepared separately. The executed v1 entry/wrapper,25 frozen snapshots, authority, ledger and old decks/proposals remain unchanged. The previous46PASS applies only to executed source. Revised source has62 tests expected by static parametrization; all added/changed controls are UNRUN. Fresh one-use execution authority and root freezing/binding are required for any v4 run; the recorded131.4847609s remainder grants no rerun or external launch after stop-first-failure.

## Pending amendment within the existing remainder

Root prospectively chose an explicit amendment rather than new time. Proposal-v4 and the PENDING v2 authority/ledger carry forward used18.5152391/remaining131.4847609 of the original150. They bind the exact prior ledger hash, preserve all three prior attempts including failed finalization in `prior_history`, retain v3's consumed token, and grant nothing until human amendment evidence is recorded by root. The original records remain unchanged. This prospective amendment supersedes the earlier fresh-authority proposal only after explicit approval; remainder alone is not authority.

The new v2 attempts stop at their first failure. Their caps are controls10, one v4 analytic15, external30 from the original unconsumed allowance only after oracle PASS/root semantics adoption, and each finalization6.5. The original7.5138045s controls and5.3276499s finalization remain charged against their cumulative20s category limits. Reserve60 and total150 are unchanged; all new caps sum68s, within71.4847609s available above reserve. Prior v3 physics is not retried. Versioned snapshots include the actual saved v3 outputs consumed by the refusal regression. Pending wrappers refuse before any interpreter/CCX launch.

Deferred amendment commands (root only, after activation and frozen-source review):

```powershell
$packet='./.qualification/b3-ge-e4-pl/r8-e03-coarse-dev-20261007-v1/next-force-output-v1/supervise-followup-v2.ps1'
& $packet -Mode controls -Attempt controls-followup-v2 -Cap 10 -Reserve 60
& $packet -Mode analytic -Attempt analytic-v4 -Cap 15 -Reserve 60
& $packet -Mode finalize-analytic -Attempt analytic-finalize-v4 -PhaseAttempt analytic-v4 -Cap 6.5 -Reserve 60
# Root adopts actual bound v4 semantics in semantics-confirmation-v2.json here.
& $packet -Mode external -Attempt external-followup-v2 -Cap 30 -Reserve 60
& $packet -Mode finalize-external -Attempt external-finalize-followup-v2 -PhaseAttempt external-followup-v2 -Cap 6.5 -Reserve 60
```

No worker check was run. Root still owns approval/adoption, checks, integration and numerical adjudication.
