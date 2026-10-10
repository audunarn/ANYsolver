# B3-GE / E4-PL and B2 — active development state

**B2 reduced-work decision (9 October):** `ef461081` shows the failed work
identity in the saved reduced KKT states as well as the physical form.
Product-float physical/reduced defects differ by at most `5.75e-18` against
`5.02e-11`–`7.93e-11` defects; two registered Decimal80 comparisons agree
between forms and still fail the unchanged tolerance. Absolute-action sums
near `2.4e6` show severe cancellation, but are not a condition-number
estimate. Independent review supports this narrow finding and does not
infer that the reduced operator is physically wrong. A v1 hash-preflight
failure and the one completed bounded v2 child are preserved. B2 G5/B16/B17
remain **OPEN**. Stop the same-factor/backend/evaluation-order sequence;
the next B2 investigation, if prioritized, must address reduced-KKT
sensitivity or conditioning. [Evidence]
(development/r8-b2-superlu-factor-20261009/reduced-work-README-v2.md).

**B2 correction path closed for the saved case (9 October):** commit
`0071b203` records two Decimal80 sparse-residual corrections using one
reused SuperLU factorization. Initial full state matched the prior SuperLU
case bitwise. Scaled componentwise residual fell to about `1e-16`, but
physical work worsened from `5.024e-11` to `7.888e-11` and `7.929e-11`,
all above the unchanged `~7.499e-12` allowance. Independent review found
the bounded negative result sound. Stop same-factor correction and backend
switch trials on this saved state; assess conditioning/work cancellation or
advance independent gates. No large current-wheel run, product repair or
G5/B16/B17 acceptance follows. [Evidence]
(development/r8-b2-compensated-refinement-20261009/README.md).

**B2 backend-switch decision (9 October):** `75e76d6d` records a forced
SuperLU solve on the same saved failed case. It missed the unchanged work
limit by 6.70× initially and 8.74× after one correction, even though its
scaled KKT residual fell. Independent review found no input, scaling or
backend-selection flaw. Together with the negative symmetric and GENERAL
PyPardiso checks, no tested backend switch repairs this saved case. A
conditioning and work-cancellation assessment is the next technical
question; there is no product repair or G5/B16/B17 acceptance.
[Evidence](development/r8-b2-superlu-factor-20261009/README.md).

**B2 general-factor decision (9 October):** `dbbb2833` preserves an exact
saved-KKT comparison using PyPardiso GENERAL mtype 11. It failed the unchanged
work criterion by 193× initially and 2,223× after one correction; projected
equilibrium residuals also grew. Independent review found no replay sign,
scaling or backend-selection error, but did not identify the numerical cause.
One child completed in 3.379 s, sampled peak RSS 463 MB; native PARDISO
thread count was not independently measured. A post-run hash inventory binds
the saved states. This rejects that candidate for the saved case; it does not
repair or accept the 10k Project. A saved-state backward check at `ce886d04`
confirms the GENERAL residual is already in the scaled KKT equations:
direct and mapped physical residuals agree within about `2.5e-16` normalized
mismatch, while the symmetric state maps consistently with a much smaller
residual. This locates the discrepancy without assigning its backend cause.
G5/B16/B17 remain **OPEN**. [Factor evidence]
(development/r8-b2-general-factor-20261009/README.md);
[backward check]
(development/r8-b2-general-factor-20261009/backward-README-v1.md).

**B2 saved-work precision (9 October):** commit `53c98106` records
80-digit evaluation of the same stored binary64 `K`, corrected displacement
and load from the failed old-wheel case 1. The stage-2 defect remains
`6.4074e-11`, 8.54 times the unchanged `7.4988e-12` work allowance;
product-style float evaluation differs by `9.63e-13`. Ordinary work
evaluation rounding alone does not explain the saved-state plateau, but
the factorization cause is unproven. Initial vectors matched bitwise;
later parity is scalar work only. The child wrote metrics but its supervisor
failed on a process-exit race, so exact child wall, exit and peak RSS are
unrecorded. A measured `6.177107 s` outer wall was conservatively charged;
resource-cap compliance is not certified. Independent read review found
the narrow numerical conclusion supported. The old Project failure and
G5/B16/B17 status are unchanged. [Evidence and limitations]
(development/r8-b2-work-precision-20261009/README.md).

**B2 saved-factor decision (9 October):** commit `82292011` preserves a
bounded replay of the exact failed old-wheel case-1 KKT. Initial `q`,
multiplier and displacement arrays matched the saved state bitwise. One
same-factorization correction reduced the signed work defect from
`-1.074e-8` to `+6.548e-11`; a second and third remained near `6.3–6.6e-11`,
above the unchanged `~7.50e-12` allowance. Projected residual work still
accounts for the defect; this does not identify factorization versus matvec
roundoff. Independent review found no false pass and noted that the replay's
gap-row ratio is not the product gap check and its charged phase ledger
excludes successful outer-launcher overhead. The existing product guard
should refuse such a result; the current wheel has not been run on the
large Project. The earlier 100-case failure remains **FAILED**, with
G5/B16/B17 **OPEN**. [Replay and receipts]
(development/r8-b2-saved-factor-correction-20261009/README.md).

**B2 old-wheel large work allocation (9 October):** solver commit `a40f1d07`
preserves one separately bound, full-state case-1 run from the old installed
wheel. It exactly reproduces the failed Project case-1 displacement, energy
and work defect. Of `2E-f·u = -1.07398906386e-8`, projected equilibrium work
is `-1.07398890868e-8` (99.9999856% of the two term magnitudes) and
multiplier-gap work is `+1.54179e-15`; saved-state identity closes to
about `1e-17`. One solve, 91.407865 s process wall and 1.566 GB sampled
peak RSS were recorded. A versioned read-only verifier uses explicit checks;
preflight wall was not measured and is reported as unknown. Independent
review found the narrow allocation supported. Factorization versus other
residual contributors remains unresolved. The prior 100-case Project attempt
stays **FAILED**; the later work guard has not been run at this size.
[Full-state evidence](development/r8-b2-large-work-allocation-20261009/README.md).

**B2 work-consistency guard (9 October):** solver commit `842c89bc`
adds a fail-closed aggregate work check on the eligible zero-offset physical
footprint static route. It uses the frozen `1e-12 + 1e-8|f·u|` allowance,
at most one same-factorization correction, and typed failure if work remains
outside the limit. Full-state 400-Q4/40-B2 evidence shows an admitted
per-row residual can accumulate into larger work error; multiplier-gap work
was negligible in that fixture. Thirty-nine focused source checks passed,
including correction, cancellation, near-zero work and historical routes;
independent read review found no concrete false pass. The final verification
used 10.414 s of its reserved allowance. Affected installed-wheel checks
followed, but the failed 10k Project case was not repeated with this guard,
so its large-scale outcome and G5/B16/B17 remain open. [Scoped source and receipts]
(development/r8-b2-work-consistency-20261009/README.md).

The exact committed source then passed 95/95 affected tests from an isolated
wheel with 627 source/wheel/site package files byte-bound and all 249 loaded
ANYsolver modules imported from the installed site. The first checker failed
on unrelated checkout CRLF differences and remains preserved; the corrected
binding passed. [Installed receipts](development/r8-b2-work-guard-installed-20261009/README.md).

**B2 installed Project solve work finding (9 October):** ANYfem consumer
commit `658723b` preserves a registered failed run of the exact reopened
10,000-Q4/1,000-B2/100-pad, 100-case Project. The public route completed all
100 ordered cases with one factorization and 118 solves, matching direct
selected displacements bit for bit; maximum selected gap was 5.97e-16. Its
frozen `2E = f·u` work check failed at 1.65338e-5 relative against 1e-8.
Process wall was 118.9247 s, sampled peak tree RSS 1.847 GB. Independent
review confirmed that exact-equilibrium work identity applies to the
zero-prescribed model, but saved outputs cannot split residual from
multiplier-gap work. No consumer mapping defect or criterion change is
established. The subsequent small full-state B2 fixture and fail-closed
guard are recorded above. The earlier direct solve remains development
feasibility evidence; G5/B16/B17 remain open. [Failed raw evidence and
diagnosis](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-b2-large-project-solve-20261009/README.md).

**B2 large input persistence (9 October):** ANYfem consumer commit `914b2df`
adds an explicit sparse-v2 physical-footprint case format while retaining v1
as the default. A byte-bound installed no-solve screen saved and reopened the
exact prior solved 10,000-Q4/1,000-B2/100-pad, 100-case load and selection
history through standalone and native Project inputs. The corrected v3 attempt
passed in 14.3178329 s process wall with 459,251,712 B sampled peak tree RSS;
16 focused codec tests passed independently. V1's failed supervisor exit and
v2's assertion-based assurance gap remain preserved. An independent read
review found no remaining false pass for v3. This closes a development
persistence gap, not assembly/solve, physical accuracy, G5/B17 acceptance or
release. [Consumer evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-b2-large-persistence-20261009/README.md).

**B2 full-size installed development result (9 October):** candidate `bfb2cc36`
completed a byte-bound installed 10,000-Q4/1,000-B2/100-pad model with
2,000 exact footprint rows and all 100 ordered loads. One factorization,
100 primary and 18 corrective solves were counted; selected recovery and
physical acceptance completed. Process wall was 97.041326 s, sampled peak
tree RSS 1.561 GB, and the first six outputs exactly matched the prior
failed-wheel attempt. The earlier case-7 failure remains preserved. This is
one feasibility screen, not repeated performance, persistence, beam-rich,
scaling, external or G5/B16 acceptance. [Exact evidence and limits](development/r8-b2-refinement-large-20261009/results.md).

**B2 beam-rich installed control (9 October):** the same installed candidate
completed one connected 400-Q4/1,000-B2/100-pad, 100-case control with 2,000
footprint rows. It used one factorization, 100 primary solves and no corrections;
selected displacement, pad wrench and member-station recovery was complete.
Process wall was 6.7790743 s and sampled peak tree RSS 263 MB. Independent
read review found no current false pass or overspend, but a prospective source-
commit guard omission in the versioned runner. This is development evidence,
not repeated performance, external, persistence or G5/B16 acceptance.
[Raw evidence and review](development/r8-b2-beam-rich-20261009/results.md).

**E01 CalculiX point-reference admission (9 October):** a source-bound audit
checks both eccentricity signs, three detached C3D20R port stations, all six
constraint rows, rigid/affine fields, signed side work, roots, loads and eight
oriented cuts. The source contract passes, but physical comparison is refused:
the square solid's Saint-Venant torsion constant is 0.843462 of the native
section's polar `J`; effective shear, finite-patch versus point work and
independent sided actions are also unmatched, and the native `Fx` case is not
in the deck. Ten new refusal tests and 27 affected focused tests pass;
independent Read review found no false admission. No external solve ran.
The smallest next repair is an independently matched six-resultant section
and exact sided-action/output map before another loaded E01 comparison.
[Audit and failures](development/r8-e01-resolved-port-admission-20261009/results.md).

**Latest BL5 transfer decision (9 October):** a detached, source-bound 16x4
five-channel Mz/Fy comparator verifies rigid fields, signed virtual work and
the common per-interval shell-wrench measure. All 40 signed basis actions agree
on 510 shell coordinates. Mz support profiles differ by 0.1131% of external L1
action despite about 10.1x local cancellation. A failed preflight-serialization
attempt and the distinct passing saved-data child are retained; independent
Read review found no evidence issue. This excludes a gross P0 support-order,
sign or lever-arm mismatch at that grid. BL5 remains a working candidate;
continuous-law accuracy, subinterval slip, body effects, convergence and F03
remain open. [Report and receipts](development/r8-bl5-five-channel-mz-reference-20261009/report.md).

**9 October 2026.** Work in `C:/Github/ANYsolver/.perf2-worktrees/stiffened-rev8-20261008` on `codex/stiffened-rev8-resume`; inspect Git for the current head. The former long living note is preserved byte-for-byte in [history V13](B3_GE_E4_PL_ACTIVE_STATE_HISTORY_20261008_V13.md), SHA-256 `6efbbd94947086bc7831e37d912ac23e6b8e87e27eaf3b79570364ee549c5984`. Earlier history remains linked there. The [Revision 8 plan](B3_GE_E4_PL_REVISION_8_PLAN.md), [goal](B3_GE_E4_PL_REVISION_8_GOAL.md) and [acceptance matrix](B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md) retain the full G0–G6, F01–F13, V01–V28 and B01–B18 scope, failures, criteria and release boundary.

**G4C reference provenance repair:** Commit `c0e8942c` keeps the curved material transport policy on a no-change stress-free reference. Three source controls and three controls from an isolated installed wheel passed; all 627 package Python modules matched committed source/wheel/site bytes. The first in-place build stalled and a full-repository archive was abandoned; both remain recorded. [Exact artifact and failures](development/r8-g4c-material-policy-20261009/results.md). This is a narrow point-reference correction, not G4C or G6A acceptance. Direct Astra repair was used because the previously attempted Mistral worker remained unavailable for this task.

**Curved S3 discriminator:** the elastic S3 local operator through the actual GE variational pullback passed two tilted-reference finite rigid-motion screens (normalized residuals `1.91e-16` and `5.51e-16`). Two preceding probes failed because they bypassed or miscalled that path; preserve them as probe-design failures. This permits designing a separate curved-S3 point policy, not admitting one: the current curved compiler is Q4-only and uses a four-vertex normal. [Decision and receipts](development/r8-curved-s3-local-20261009/results.md).

**Experimental curved Q4/S3 point owner:** candidate `731d9415` now selects a distinct curved Q4/S3 elastic point policy, fixes the S3 normal and orientation audit, uses the existing stable-translation pullback, and preserves that arithmetic through restart. Final focused source controls passed 6/6; final isolated wheel passed 22/22 affected installed controls with 627 source/wheel/site Python modules identical. Test-only follow-ups `080b1261` and `dbb8f2a7` independently reconstruct accepted point gaps and check recovered force/moment balance and multiplier work in all 12 port directions under vertical and mixed `Fx/Fy/Fz` loads on both panel types; final source and unchanged-wheel checks passed 8/8 each. The initially rejected finite steps and all superseded attempts remain recorded. [Implementation, artifact and limits](development/r8-curved-s3-point-20261009/results.md). This is an M4/G4C development increment only; physically matched six-channel transfer, full curved topology, external agreement, independent-family mechanics review and aggregate gates remain open.

**Changed curved Q4/S3 stress-free reference:** test-only `4b0ee5a7` extends both all-S3 and mixed panels through mixed-translation reference-linear response, accepted finite loading, independent point work, checkpoint restore and byte-identical continuation. Source and unchanged installed-wheel checks passed 9/9 each under the recorded CPU0/one-thread/JIT-off/2 GiB bounds. [Receipt and applicability](development/r8-curved-s3-point-20261009/results.md). This is scoped G4C development evidence; broader imperfection mechanics and qualification remain open.

**Curved Q4/S3 common-reference rotation:** test-only `d7d556c4` checks stress-free rigid reference transport, beam poses, loaded shell translations, objective point gaps and spatial point actions for all-S3 and mixed panels. Final source and unchanged-wheel checks passed 11/11 each; a preceding test-oracle read-only-array failure remains preserved. [Scoped evidence](development/r8-curved-s3-point-20261009/results.md). Local frame changes, finite loaded covariance, matched external transfer and G4C/F01 acceptance remain open.

**Pressure assessment slice:** the user approved the prospective pressure-only vector-equilibrium option with its stated shared-node masking tradeoff. The candidate binds selection to the pressure request/checkpoint, applies it to linear/finite acceptance, frozen-parent trial comparisons, restore and rebase, and leaves default component assessment unchanged. New focused source controls passed 8/8 plus a Q4 follow-up 1/1, selected legacy controls 13/13, and the same isolated wheel passed 22/22 selected tests under recorded CPU0/one-thread/JIT-off/2 GiB bounds (25.874 s; 178 MB sampled peak). The supporting read review's trial-merit finding was repaired. [Receipt and limits](development/r8-ge-pressure-vector-20261009/results.md). This is implemented but not qualified; G4A, independent mechanics review and the complete programme remain open. Earlier failed pressure runs remain failed.

**Consumer continuation:** ANYfem experimental consumer commit `806cd22` exercises the opt-in mixed Q4/S3 pressure route through Project save/reopen, reference-linear solve, accepted-prefix cancellation, checkpoint restore, identical continuation and policy-refusal checks. Isolated installed ANYsolver/ANYfem wheels passed 3/3 focused workflows; an initial test-assertion failure is retained. [Consumer evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-ge-pressure-vector-consumer-20261009/results.md). This adds installed consumer behavior only; G4A/G6 remain open.

**B2 consumer continuation:** ANYfem isolated commit `5c5eaa5` persists the distinct experimental physical B2 POINT reference-buckling request in standalone and Project records, including typed preload and section-traction data. Reopened mixed Q4/S3 and Q4 routes dispatch through the public operation; malformed input, cancellation, unsupported controls and ineligible-owner cleanup are covered. Installed ANYfem/ANYsolver checks passed 97/97 selected controls, with a 3/3 test-only refusal-path follow-up; source/wheel/site module bytes matched. [Evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-b2-point-buckling-persist-20261009/results.md). This is experimental B17/G6 consumer behavior, not F12/B14/G4B or independent mechanics acceptance. The latest user reply reconfirms the previously adopted prospective pressure-only opt-in amendment; it does not retroactively change historical failed runs.

**Physical B2 footprint consumer continuation:** ANYfem isolated commit `3dd750f` persists the separately typed five-row physical rigid-footprint reference-buckling request in standalone and Project records. The installed example's explicit `--buckling` route reopens and solves the request, checks the original typed preload/section-traction data, and preserves the historical static default. A supporting read review's CLI and original-input comparison gaps were repaired. Final isolated ANYfem/ANYsolver wheels passed 8/8 affected controls with all 100 ANYfem modules byte-identical across source/wheel/site. [Evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-b2-physical-footprint-buckling-persist-20261009/results.md). This advances experimental B10/B14/B17/G6 consumer behavior only; F12/G4B, external/scale/platform and independent mechanics acceptance remain open.

**GE accepted-state buckling consumer:** ANYfem isolated commit `137a225` adds a self-contained mixed Q4/S3, two-member native Project example that accepts a loaded prefix, stores a separate solver checkpoint, reopens Project input, restores the accepted state and obtains identical direct/restored conservative buckling results. A stale-generation request is refused without state mutation. The final installed ANYfem/ANYsolver run completed within 4.3256739 s under CPU0/one thread/JIT-off/2 GiB; the self-contained v3 defect and prior v1/v2 runs are preserved. [Evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-ge-accepted-buckling-consumer-20261009/results.md). This is G4B/G6 consumer development, not physical accuracy, convergence, F03 or aggregate acceptance.

**Native BL5 spectral consumer:** ANYfem isolated commit `fcf6d59` extends the existing physical-fibre line consumer with an explicit `--buckling` route. Its Q4 static default and mixed Q4/S3 native-line CLI both completed against installed wheels. The line route checks Project save/reopen, accepted-prefix restoration/continuation, stale-generation refusal, direct/restored factor parity and unchanged checkpoints. The bounded final installed run took 12.1701289 s under CPU0/one thread/JIT-off/2 GiB. [Evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-ge-native-line-buckling-consumer-20261009/results.md). This does not select the BL5 law/space, close F03 or qualify physical buckling.

**E02 next external discriminator prepared:** the rigid-tip CalculiX generator admits separate 20x8/nz=4,8 source-only thickness variants; its historical 20x8/nz=2 deck remains byte-identical. The bounded V2 self-check completed 20 exact geometry/metadata cases, parsed synthetic complete records at both new thicknesses and rejected unregistered/tampered variants. [Decision and receipt](development/r8-e02-rigid-thickness-prep-20261009/results.md). No external process was launched. If separately authorized, fixed-20x8 Mx work/transfer at nz=2/4/8 will distinguish solid thickness sensitivity from the unresolved native torque convergence; it cannot by itself qualify E02 or revise F04 criteria.

**E02 fixed-in-plane thickness result:** the archived nz2 and new nz4/nz8 CalculiX 20x8 +Mx work are 1.742097e-5, 1.745454e-5 and 1.746433e-5 J, changing +0.193% then +0.056%. The saved native 20x8 work differs -1.807%, -1.996% and -2.051% from those external values, so thickness refinement does not repair that fixed-grid gap. Both new complete single-thread runs passed development physical sanity checks under the 180 s bounded allowance. Two earlier sandbox CreateProcess failures remain preserved; the approved unsandboxed route succeeded. Seven-digit DAT output cannot certify 1e-8 balance. Native in-plane torque convergence, connection idealization and E02/F04 acceptance remain open. [Raw evidence and limits](development/r8-e02-rigid-thickness-run-20261009/results.md).

**F03 actual-owner reference progress:** the timed-out 16×4 Q4/P0 bound remains failed V10 execution; a fresh one-use V11 completed the same exact 40-column source check with relative Loewner bound `2.2123959869e-4` against unchanged `1e-3`. The subsequent seven-ratio, one-shell-resolution screen passed complete row work, supported shell/beam norm parity and independent continuous-dual bounds at half-cell counts `2–128`. At 128/32 the unscaled inverse failed `1e-10`; diagonal equilibration did not help, while a separate high/low diagnostic exposed a single-array rounding floor. A frozen 128/16 auxiliary reference passed the same inverse and Loewner criteria; the final seven-entry V6 passed in 13.894 s with largest bound `3.3535701819e-4`. All attempts and limits are preserved in [family evidence](development/r8-f03-actual-family-20261009/results.md). This is development evidence at one 16×4 shell grid, not the historical `0.43` floor, multiplier selection or F03 acceptance. The old graph allowance is closed to further checks; formal F03 remains unconsumed. The earlier c2 native family already covered the same seven half-cell ratios and support rule at three shell levels under its frozen installed artifact. The separate projected whole-member family has different support spans, row counts and ratio conventions; its spectra cannot be transferred by matching half-cell count. Reconcile current-source/reference identities and reuse eligible c2 evidence instead of repeating that positive campaign. Signed KKT, physical transfer/locking and different-family mechanics review remain open before any formal quotient.

**F03 c2 reuse decision:** all 21 historical positive quotients and 14 adjacent finite-family ceilings remain valid for their frozen installed fixture; 101 archived hashes matched their manifest. Current-source V6 checks seven ratios at 16×4. A fresh, bounded current-owner check at 32×8 and 64×16 now matches the supported signed-basis embedding, full sparse `H`, all `C E` row work and independent reference actions; the two children used 19.997064 s process wall and independent Read review found no evidence issue. The original first-child checker failure is preserved. This supports reuse of the construction for those checked objects, not bytewise identity of unarchived historical matrices, the old `0.43` floor, signed-family stability, physical transfer, multiplier selection or F03 acceptance. [Scoped reuse audit](development/r8-f03-actual-family-20261009/reuse-audit-20261009.md) and [current-owner parity evidence](development/r8-f03-current-owner-parity-20261009/report.md). Formal F03 authority remains unconsumed.

**F03 c2 current-owner bridge:** bounded 32×8 and 64×16 checks now match the expected supported `E`/`H` inventories and independently integrated physical density RHS/scatter on the same discrete `H`; Gram relative differences are `4.270e-15` and `1.676e-14`. This narrows the prior current-owner mapping uncertainty, but `C E` is a construction identity and the same-`H` comparison does not establish the continuous reference, current beta, signed family, transfer, locking or F03 acceptance. Final source checks passed 8/8; the exact numerical source, failed attempts and `84.705290/180 s` ledger are preserved. [Scoped report and raw archive](development/r8-f03-actual-family-20261009/current-owner-bridge-20261009/results.md). The `0.43` historical floor remains inapplicable without its own contract; formal F03 authority is unconsumed.

**F03 c2 signed-system discriminator:** one current-source 16×4 Q4/32-halfcell c2 P0 owner passed a bounded signed-KKT development check: constrained kernel minimum `1.738e-5` above `3.106e-11` uncertainty, reduced saddle inertia `769+/40-/0`, and maximum role parity `3.12e-12` after the owner's compensated full-system corrections. The initial raw-LU parity HOLD and all source/runner failures remain preserved. The final runner refuses another 60-second attempt because combined `42.577/150 s` usage leaves less than its 60-second final reserve; formal F03 authority is unconsumed. [Exact scope and raw receipts](development/r8-f03-c2-signed-kkt-20261009/results.md). Full and owner solves share the assembled operator; this checks one signed algebraic case, not independent mechanics, physical transfer or F03 acceptance. The supporting same-family read review found no sign/scaling defect.

**Next-grid signed and transfer decision:** the corrected 32×8 Q4/64-halfcell c2/P0 owner passed one bounded signed development case: projected binary64 Cholesky estimate `2.804e-6` versus heuristic uncertainty `8.421e-9`, with reduced inertia inferred as `2305+/80-/0`, role parity ≤`1.325e-12`, and physical equilibrium/work checks passed. A first numerical PASS imported main and is excluded; the final attempt is hash-bound to this isolated owner. Same-family review found no sign/congruence error but the estimate lacks a complete forward/interval error bound, so no certified exact inertia or family stability is claimed. Separately, 18 saved common-density probes across the three matched grids verified full native/external port work to roundoff, including fixed root and native retained rotations; a review-identified station-coverage guard was added and the affected source/final run passed. The exact external stiffness/DOF map is absent in all nine cases, so fixed-density response allocation was not attempted. [Combined decision and immutable raw evidence](development/r8-f03-signed-transfer-20261009/results.md). Physical transfer, growing-family signed mechanics, different-family review and F03 remain open; formal F03 authority is unconsumed.

**External-operator feasibility:** source-bound preflight of the saved 16×4 Fy/Mx/Mz OpenSees cases confirmed 708 physical coordinates, 35 fixed coordinates and 40 weak rows, but no saved stiffness or equation map. Three responses cannot uniquely determine fixed/free coupling; the bounded source-only capture validator now refuses missing provenance, altered load/RHS, small-response mutations and incorrect KKT blocks (7/7 focused controls). A fresh numerical capture was deliberately not launched because an unreduced physical tangent and unambiguous DOF map have not been demonstrated. [Decision, controls and retained failure](development/r8-bl5-external-operator-20261009/report.md). This parks fixed-density causal allocation; F03 and its formal one-use authority remain open/unconsumed.

**External matrix API discriminator:** one disposable three-node OpenSees 3.8 model returned a complete `FullGeneral` 5x5 KKT through `printA`, with `nodeDOFs` identifying physical rows and the correct analytic two-spring stiffness including fixed/free coupling. RCM placed MP and SP rows before interleaved physical rows, invalidating the previous physical-first/SP-first capture validator. The run completed in `0.453 s`, sampled `50 MB` peak on CPU0; eight OS threads were observed, so internal one-thread execution is not independently proven. [Hash-bound toy evidence](development/r8-bl5-matrix-api-20261009/results.md). Prepare one distinct 16x4 Fy capture with explicit row mapping and saved BandGeneral response comparison; stop on mapping or parity failure. No frozen external case or formal F03 authority was consumed.

**16x4 external Fy operator capture:** one distinct OpenSees `FullGeneral` child completed in `0.782 s` on CPU0, peak `108 MB`, with all 708 physical DOFs, 35 SP and 40 MP rows identified in its 783x783 KKT; 230 fixed/free couplings are nonzero. OpenSees normalizes MP rows by the source dependent coefficient, so the first postprocess refusal was repaired against the saved matrix without rerunning the child. All saved BandGeneral Fy poses, element forces and recovered actions match exactly; 11/11 source controls pass. Nine OS threads were observed, so lifetime one-numerical-thread execution remains unproven. [Source, raw, repair and limits](development/r8-bl5-external-operator-20261009/report.md). The operator is development evidence for a future common-density response comparison, not physical accuracy, multiplier selection or F03 acceptance; formal F03 authority remains unconsumed.

**Saved-state cross-load check:** the same captured Fy physical K reproduces independent archived Fy/Mx/Mz element-force covectors on all 708 rows, including fixed roots, to at most `1.17e-11 N` and `1.71e-13 Nm`. Source-only inferred multipliers give rank 75, complete KKT residuals ≤`6.26e-11 N`/`4.76e-11 Nm`, and the source density map agrees with archived recovery. External and native full beam-yaw fields (including 32 native retained rotation slots) annihilate their support-only K and have compatible fixed-density loads to ≤`1.76e-12` normalized work. One offline CPU0 child completed in `1.819 s`, peak `122 MB`, with one effective thread in each observed OpenBLAS pool; 14/14 source controls pass after a source-only native-load provenance repair. [Cross-case evidence](development/r8-bl5-external-operator-20261009/report.md). These are three saved states and one known null mode, not arbitrary-density response, complete support-only nullspace, physical equivalence or F03 acceptance. Next distinguish whether a single declared yaw gauge permits a well-posed common-density response; stop if additional unsupported modes appear.

**BL5 support-only gauge decision:** saved 16×4 external/native operators have exactly one numerical yaw null mode across three declared physical scales and rank screens; native retained-coordinate inertia is `768+/288-/1 zero`. The first bounded child failed an invalid coupled-state comparison and remains failed. A distinct repaired child, with exact 35-support and imported-helper hash binding, passed Fy/Mx/Mz fixed-density original-free equilibrium, gauge reaction and yaw-shift checks in both models (largest work-scaled residual `2.68e-12`); six source controls and focused independent Read review found no concrete false pass in this saved-data scope. [Run receipts and limitations](development/r8-bl5-support-only-gauge-20261009/report.md). This establishes neither arbitrary-density response nor physical agreement/F03 acceptance. The next useful comparison is matched physical work and transfer on the same fixed density, retaining the native indefinite/retained formulation and the external gauge.

**BL5 common-density response decision:** the same Fy/Mx/Mz source-row densities and physical loads on the saved 16×4 native/external operators yield gauge-fixed solutions with exact original-unit balance and retained-coordinate work. The first child failed because its diagnostic wrongly set native retained dual loads to zero; the distinct repaired child passed. In the chosen external-resolvent identity, native-minus-external effective-work differences are Fy `-2.5341e-6 J`, Mx `9.1289e-9 J`, Mz `-4.7883e-8 J`; the shell-body terms dominate these three fixed-density identities, beam-body terms are negligible, and action-map terms are smaller signed corrections. Independent Read review found three reporting/check gaps; source-only hash-bound adjudication corrected the free beam-root yaw reaction label, tightened unit-separated response/work closure and narrowed the causal language. Ten focused source controls and follow-up Read review pass; numerical run-v2 and failed run-v1 remain immutable. [Exact receipts, adjudication and limits](development/r8-bl5-common-density-response-20261009/report.md). This does **not** allocate the original coupled discrepancy, prove drilling causation, converged physical accuracy or F03 acceptance. Reuse the existing nx64 same-action evidence before choosing a new physical-shell or interface experiment; do not repeat n16 refinement automatically.

Local main `da1ba2e9` was merged into this isolated branch at `d47a6034` without conflicts. Three affected modal source files passed 42/42 focused cases; this does not refresh the installed-artifact evidence or accept F07/G4B. [Merge check](../../.development/main-modal-merge-20261008-v1/results.md).

The saved positive-offset E01 B31/S4 six-row point canary now executes with pinned CalculiX 2.23: one accepted increment, 11 printed translations, no warnings. A sandboxed launch failed before execution; the same pinned binary ran through the bounded unsandboxed supervisor. Section/shear/torsion equivalence, physical rotations, reactions/work, both offset signs and three-level convergence remain open, so E01 is still in progress. [Raw execution and limits](../../.development/e01-point-canary-20261008-v1/results.md).

The registered output-only variant also completed, preserving all original-node translations and exposing 32 expanded-node displacements. A synthetic rigid-motion reconstruction passed, but the expanded physical beam/shell traces show an apparent root position and rotation gap. CalculiX output averaging and knot/MPC expansion have not been reconciled with the six algebraic equations; the run is **physically unmatched reference evidence**, not an accuracy oracle or a native-law failure. [Output evidence](../../.development/e01-point-output-20261008-v1/results.md). A separate registered C3D8 two-port canary passed six explicit eccentric rows, full force/moment balance, rigid face/body kinematics and virtual work under the same +0.1 m/+1000 N action. This isolates the B31/S4 representation problem from the algebraic six-row work map; it does not qualify a beam/shell response. [Explicit-port evidence](../../.development/e01-explicit-port-20261008-v1/results.md).

A new one-use shared-node B31/S4 `+0.1 m` offset canary at prepared source `e34f47ad` generated explicit knots at all three beam/shell nodes and completed one accepted step in `0.0712516 s` under CPU0/one thread/2 GiB/30 s. Expanded section geometry and fitted beam/director pitch are recoverable, and the tip X offset translation agrees with the knot translation plus rotation arm to `3e-13 m`; the expanded Z discrepancy is `7.669e-9 m`. The saved nodal reactions lack the root moment, so support wrench and six-channel work remain unobservable. The shared-knot **kinematic route is promising, but its current output is not an E01 accuracy oracle**. [Registered run and interpretation](../../.development/e01-shared-knot-20261008-v2/results.md). The negative-offset deck was not run; formal F03 and historical one-use runs remain untouched.

The separate shared-knot section-output probe first failed at input parsing because `SECTION FORCES` and default 3D output conflict; its one-use failure is retained. A registered 2D-output correction completed with printed nodal results and accepted-step inventory byte-identical to the original run. It produced six-component nodal stress/section fields, but shared beam/shell nodes are not separated and the root moment remains absent from `RF`. **Stop this nodal-output route as a complete E01 work oracle**; identify independently balanced beam and shell cut actions or an explicit resolved physical port before the next external solve. [Failure and corrected evidence](../../.development/e01-shared-knot-section-output-20261008-v2/results.md). E01 remains open.

The [CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf) confirms that `*SECTION PRINT` can return force and moment on a named solid/shell face, but original B31 `*SURFACE` faces are the four lateral section faces, not an axial end cut (sections 7.115 and 7.129). Its face-stress integration can also be inaccurate at material interfaces. Therefore another B31/S4 formatting variant cannot by itself provide the missing separated beam-root work. **Choose an explicit resolved 3D physical-port/cut reference for E01** and validate its two sided wrench, orientation, support balance and virtual work before comparing response. Reuse the successful six-row C3D8 port canary only for algebraic work signs; its short cubes are not a plate/stiffener accuracy model. Match actual plate thickness, beam section and centroid offset, loading and supports to a native case before any new external execution. No historical run is renewed by this source decision.

The chosen E01 resolved-port deck has the point-canary's nominal plate/beam dimensions (`2 × 1 × 0.07 m` plate, `0.1 m` square beam, `±0.1 m` centroid offset), separate C3D20R solids, three six-row eccentric reference-port pairs, and independently named solid cuts. Two load controls isolate `Fy` shear-arm work and `Mx` torque. Independent review found a rigid-slave/direct-support overlap, inconsistent shell-port footprint and missing interior cuts; stronger tests then exposed a millimetre/metre deck error. All four are corrected in the [V6 source preflight](../../.development/e01-resolved-port-source-20261008-v6/results.md), which passes 5/5 for physical dimensions, port geometry, root support, cut-face coverage, Q20 topology, rigid motion, signs, work and refusal. [V1–V5](../../.development/e01-resolved-port-source-20261008-v2/results.md) preserve the earlier failure/narrower-check history. V6 was an inert source check; the later one-use execution is recorded below. Neither is a point-law accuracy oracle.

An independent source review identified that per-patch work alone misses connection work. The [V3 element-side recovery](../../.development/e01-resolved-port-weak-20261008-v3/results.md) now reports each constituent's weak port wrench, actual fitted six-row gap, signed two-sided work, free-port action residual and total grounded-root balance; 17/17 source controls pass, including nonzero manufactured ±offset `Fy`/`Mx` signs and an incompatible rigid-patch counterexample. It binds a saved deck to its manifest hash. The V3 receipt is source-only; physical E01 reference use needs the external evidence and independent comparisons described below.

The [one-use resolved-port output smoke](../../.development/e01-resolved-port-smoke-20261008-v1/results.md) subsequently completed one pinned positive-offset `Fy` CalculiX increment without warnings, and the saved FRD/DAT observer parsed eight cuts, separate root reactions and constituent weak port actions. Weak global balance is within roughly `0.01 N`/`0.0023 N·m`; printed support balance is tighter. The largest individual free-node reconstructed residual is `10.49 N`, so an FRD precision floor and independent sided-work check are still needed. Interior `SOF` left/right pairs are equal and opposite at print precision and do **not** independently resolve port transfer. This is an output-route feasibility result, not a native/solid accuracy comparison, E01 acceptance or a reason to repeat the run. Next E01 action is to establish an independent sided-action/work oracle and match finite footprint plus native shear/torsion section idealizations before opposite-offset/torque/refinement comparisons.

**Physical-comparator decision:** the currently executed resolved solid must not be scored against the historical native point fixture. The [native definition](../../scripts/b3_e4_e01_native_point_refinement_screen.py) assigns the `0.1 m` square an effective torsional factor `1.6666667e-5 m^4`, its polar second moment; a warping square has a distinct Saint-Venant torsion constant (about `1.406e-5 m^4`), so the native nominal torsional stiffness is about `18.6%` higher. This is a section-level prediction, not a measured coupled error. Its transverse shear factor is `0.008 m² = 0.8A`; equivalence to the resolved continuum has not been established. The native law attaches one shell node at each station, whereas the solid uses a one-sided `25 mm` shell-edge rigid patch and a full beam cross-section port; root restraint also differs. The historical native comparison applies `+Fx=1000 N`, with `+My=100 N·m` eccentric pullback, while the saved solid applies `+Fy=1000 N`, with `-Mx=100 N·m`; these are different physical actions. Treat the saved solid as a finite-port/work diagnostic only. A finite-footprint comparison is a separate capability; adding native `Fy` alone cannot make the saved patch a point-law oracle. The torsion interpretation follows [rectangular-section warping theory](https://stuff.mit.edu/afs/athena/course/other/emech/dontindex-build/full-text/emechbk_6.pdf) and an [independent square-section reference](https://citeseerx.ist.psu.edu/document?doi=382d08f8c31de4f046423ec099d1550a70ba6533&repid=rep1&type=pdf). E01 thresholds remain unchanged.

The existing [OpenSees point fixture](../../scripts/b3_e4_e01_opensees_point_canary.py) already matches the native beam section, point-arm law and `+Fx` action and recovers an independent root beam force and six-coordinate work. Its three-grid signed screens are supplementary external evidence, not accepted physical equivalence: the torsional disagreement grows with two-direction shell refinement, and the [saved reciprocal-work decision](../../../../.qualification/b3-ge-e4-pl/r8-e01-cross-work-dev-20260930-v1/results.md) allocates `102.2491%` signed cross-work to membrane/drill coordinates and `-2.2491%` to plate coordinates without identifying a defective element. The next point-law reference decision is to match the shell's material-spin/membrane connection interpretation and physical idealization before scoring the registered accuracy threshold. The B31/S4 shared-knot route remains a separate point-semantic feasibility route; its prior output lacked an independently recovered root moment. The finite-solid smoke alone did not justify a new external solve.

**One bounded B31/S4 output discriminator:** the saved shared-knot geometry, load and one-step solution lack a printed root moment, so their six-channel work cannot yet be checked. The [CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf) says `*NODE FILE,OUTPUT=3D` stores expanded beam/shell nodes and accepts `RF`, while `NSET` is deactivated in this mode; `RF` is the external-force inventory including applied loads. Prepare one output-only variant of the saved positive-offset deck (`U` to `U,RF`) with identical mechanics and a new input hash, then execute it once under CPU0/one thread/2 GiB/30 s. If expanded RF exposes the complete root wrench, use it to validate support force/moment and work on the existing nodal connection before a matched response claim. If not, record the missing observable and stop this output route. Do not recycle earlier one-use runs, modify the point law or treat the variant as E01 acceptance.

**Result and decision:** the [one-use output variant](../../.development/e01-shared-knot-rf-20261008-v1/results.md) completed one accepted step with the same original-node DAT bytes as the preceding run. Twenty-four expanded force/displacement records recover root `Fx=-999.9995 N`, `My=-99.9998885 N·m`, `Mz=-499.99975 N·m`, consistent with the nominal support wrench at FRD print precision. Expanded `FORC·DISP=0.00068948603 J` nearly equals printed knot `Fx ux=0.0001498027 J` plus `My theta_y≈0.000539708 J` from a fitted beam-section rotation, differing by `2.46703e-8 J`. The combined-action work appears in the eccentric expanded field; an earlier saved-file interpretation that it omitted moment work was corrected and preserved. Independent review found that the near-zero tip moment about the beam centroid is an **aggregate** of opposing beam/shell contributions, not a separated side wrench. This removes the root-wrench output obstacle but does **not** establish an exact printed rotational DOF, separated shell/beam side work, all six port channels, matched section/support idealization or E01 accuracy. Do not launch another output-format probe. Derive and independently check the exact work map before a physically matched E01 comparison; retain the registered opposite-offset and three-level requirements.

**Bounded saved-field discriminator:** the existing [source-only port map](../../scripts/r8_e01_material_frame_work.py) now reports both incident one-sided material spins from the two unchanged hash-bound 8×4 torque fields. [V2 evidence](../../.development/e01-spin-sides-20261008-v1/results.md) passes 16/16 focused controls; an [affected test-only delta](../../.development/e01-spin-sides-20261008-v2/results.md) passes 1/1 and the earlier selected-host spin is exactly unchanged. At x=1.75 m, native and OpenSees incident jumps are `8.728590078236072e-8` and `8.500972271783122e-8 rad`; the largest cross-model same-side differences over all **interior** stations are `1.5331654353297095e-8 rad` (left) and `1.3055476288767587e-8 rad` (right). The tip's selected-host difference is about `2.94448e-8 rad`. [Supporting read review](../../.development/e01-spin-sides-20261008-v1/review.md) confirmed indexing, signs and this scope. Thus a new point material-frame comparison needs an explicit host, averaging or footprint sampling law before scoring; the saved nodal fields do not select one. This is a sampling ambiguity, not evidence that either shell, point law or BL5 fails. No new equilibrium solve or E01 accuracy claim follows.

The saved pure-x-torque question is narrower: the linear material map samples director x-rotation at the shared vertex, independent of the one-sided polar-yaw host. A synthetic direct-work control with opposite incident yaws has identical `100 N m` x-torque work, and all 17 source controls pass. The saved native/OpenSees tip director x-rotations differ by `18.9985%` relative to OpenSees; sampled transverse shear-y differs by `26.5960%`. Their distinct coupled shell actions have nonzero original nodal `Mz`/`theta_z` coordinate work (`0.000157794` versus `0.000020527 J`); this is not work under the unadopted polar-spin map. [Bounded source result and hash-bound work split](development/r8-e01-torque-host-20261009/results.md). Host choice cannot change director extraction from the fixed saved fields, but a changed yaw connection could affect a re-solved response. The separate finite projected-polar candidate already has its own work transpose; the missing decision is its physical yaw sampling and matched connection/section/support comparison, not another derivative helper. Full six-channel E01 still needs independent acceptance.

## Decision sought

The saved external strong-to-P0 comparison already isolated enforcement-space sensitivity for the matched Mz case: native/P0-external work differed by `-0.271358%`, whereas native/strong-external differed by `+12.747623%`. Later matched growing-grid and reciprocal studies retained the candidate, and a fixed-body five-channel S4→S2 density control changed native work by `+13.119675%` and independently matched reference work by `+13.336932%`. These are evidence that the declared line resolution materially changes lateral transfer, not evidence that S2 or S4 is qualified. The fixed-body and external controls are complete; do not repeat them. The actionable F03 question is now whether the registered actual-owner norm extends with valid family bounds and physically acceptable transfer across the remaining envelope, followed by signed-KKT and different-family review. [Controlled enforcement](development/r8-bl5-matched-comparison-20261001/p0-v2-raw/independent-review.md) and [density decision](development/r8-bl5-projected-assessment-20261003/results.md).

The flat actual-owner BL5 primal/work bridge now passes Q4, mixed Q4/S3 and
all-S3 supported fixtures, preserving bulk off-line fields and native
half-cell directors. The compiled shell ordering and full native half-cell
coverage are checked; an input-order test was corrected to compare equivalent
DOFs by permutation. [Current bounded check](../../.development/f03-actual-primal-work-20261008-v3/results.md)
and [preserved failed test premise](../../.development/f03-actual-primal-work-20261008-v2/results.md).
This verifies one necessary kinematic mapping; family-wide independent `M_ref`
bounds, different-family review and signed-KKT/physical-transfer checks
still block F03. The already-consumed V6 sided-face run was not repeated.

The flat P0 root-supported owner now has an independently integrated
force-equivalent multiplier action and refined positive M2 dual, checked for
all row-density columns on Q4, mixed Q4/S3 and all-S3 fixtures. Extra trace
restraints and P1 are explicitly refused. [Bounded source evidence](../../.development/f03-actual-mref-20261008-v2/results.md).
The existing modal-shell and equilibrated-beam majorants now bound this flat
P0 continuous reference dual within the registered `1e-3` Loewner budget.
[Bounded check](../../.development/f03-actual-mref-20261008-v3/results.md).
An applicable candidate floor, non-P0 spaces, different-family review,
seven-ratio envelope, signed KKT and physical transfer remain open. The former
`0.43` floor is unchanged and inapplicable to the mixed fixture.
The exact 4×1 mixed-fixture relative reference bound is
`6.050952616809546e-05`; [V4 JUnit](../../.development/f03-actual-mref-20261008-v4/results.md)
records its components. One entry of the saved registered Q4 family,
16×4 shells/16 half-cells/eight P0 supports, now passes all actual-owner
physical density-action columns. [V6 evidence](../../.development/f03-actual-mref-20261008-v6/results.md)
preserves V5's failed test-key premise. [V7 evidence](../../.development/f03-actual-mref-20261008-v7/results.md)
also checks the complete supported Q4 shell norm against the saved scalar
tensor norm by exact field/node permutation. A same-family read-only review
found no sign, moment-density or scaling error in this bounded slice, but
identified missing complete-norm and partition checks. [V9](../../.development/f03-actual-mref-20261008-v9/results.md)
passes 7/7 with complete shell/beam Gram parity and negative missing-cell and
overlap admission checks. [V8](../../.development/f03-actual-mref-20261008-v8/results.md)
preserves the corrected syntax failure. The subsequent seven-ratio check at
one 16×4 Q4 grid extends this mapping and continuous-dual bracket, but does
not transfer the historical scalar floor or justify formal F03. Stop isolated
small-fixture scalar refinement; next resolve physical transfer and the
remaining refinement/signed-system contract. Different-family mechanics
review remains required.

BL5 remains the intended five-channel director/position bond, with released relative spin about the physical director. Its continuous law, multiplier resolution and final engineering fidelity are **not accepted**. The next F03 decision is whether the existing independent M2 trace norm `h_B+h_S` and dual `M_ref` can be restricted to the *actual supported BL5 trace kinematics*, with physical work and units preserved, before any growing-space quotient. The signed native KKT, locking, shear/drilling freedom and physical transfer remain separate mandatory checks.

One pending method counterexample is now explicit: a nonzero alternating P0 density on a fixed-end scalar `H^1_0` trace has zero P1 work but positive independently integrated dual `a²/12`, while a constant density approaches unit quotient as `sqrt(1-a²)`. Six source checks passed on three refinements with bounded process receipts. [Derivation and evidence](development/r8-f03-scalar-checkerboard-20261009/results.md). This does not select a BL5 space or physical norm; actual-owner dual, independent mechanics review and signed KKT remain open.

The provisional full-native positive graph is withdrawn from the prospective F03 norm: a director jump penalty conflicts with the M2 cell-constant L2 director space, and a three-level alternating-director check found graph/reference ratios `3.878/6.832/18.647` while its no-jump trace/reference ratio stayed `1.000`. This is adverse finite evidence, not a proof of asymptotic failure or a BL5 formulation failure. The [draft contract](B3_GE_E4_PL_BL5_F03_CONTRACT_DRAFT.md) identifies the proposed restricted spaces, five-channel work, released-motion witness, independent dual, units, nullspaces and required counterexamples. The prior `0.43` floor belongs only to its frozen M2 family and cannot be transferred by assertion.

At the current isolated Q4/BL5 owner, source inspection and a focused **2/2** P0/discontinuous-P1 regression confirm that assembled line rows have zero columns for inactive native beam variables after coordinate-selection supports. Reference and finite-chart line assembly both use 12 shell plus nine beam local slots. This supports the trace-active mapping only for the checked owner; mixed attachments, affine support maps, the positive norm, uniform inf-sup and signed KKT remain open. [Evidence](../../.development/bl5-active-slots-20261008-v1/results.md). An independent flat-reference derivation checks all current five-channel work columns, including shell-top director and eccentric beam-arm terms, against P0/discontinuous-P1 assembly: Q4 **2/2** and new mixed Q4/S3 plus all-S3 **4/4** passed. It reuses product quadrature and density basis, so those choices, finite-chart mapping and broader topology remain open. [Q4 work evidence](../../.development/bl5-physical-work-20261008-v1/results.md); [S3 work evidence](../../.development/bl5-physical-work-s3-20261008-v1/results.md). The earlier [no-jump rank](../../.development/bl5-centerline-no-jump-20261008-v1/results.md) and [weak-director norm](../../.development/bl5-cell-director-norm-20261008-v1/results.md) checks retain their separate limits.

The flat Q4/S3 five-field H1 shell restriction now passes **5/5** focused source controls, including existing-Q4 norm parity, mixed affine fields, units and actual-owner BL5 projection. Zero direct line work on off-line shell nodes coexists with nonzero H1 coupling, so those nodes remain in the primal norm. This is a necessary shell-side construction, not a complete F03 quotient or accepted metric. [Evidence](../../.development/f03-mixed-shell-h1-20261008-v3/results.md).

The physically matched native/resolved evidence remains mixed. The executed C3D20 weak-P0 Fy and Mx comparisons give native/resolved work-conjugate ratios `0.95955` and `1.22489` on their declared actions; these do not allocate body, root, warping and bond effects. V5's `7.24284` beam-work ratio cannot be decomposed from its saved solid fields because sided half-cell work is unavailable. The saved 2:1 x8/B3-14 mode and a supported 1:1 alternating-translation witness show that a nonzero continuous gap can be invisible to P0 rows; they do not select P1 or prove a zero-energy mechanism. Use [history V13](B3_GE_E4_PL_ACTIVE_STATE_HISTORY_20261008_V13.md) and the matrix for exact source identities and limitations. Do not restart classical axial or broad refinement campaigns without a new discriminating question.

## Delivered behavior and acceptance boundary

- Experimental sparse GE multi-element Q4, mixed Q4/S3 and all-S3 point workflows, finite stepping, physical recovery, cancellation and checkpoint/restore exist. A separate B2 physical batch route supports 1/10/100 compatible cases, selected recovery and factorization reuse. ANYfem has an experimental consumer. These are implemented/tested subsets, not aggregate G0/G1/G6 acceptance.
- ANYfem `ffa89b0` adds a distinct experimental B2 POINT reference-buckling operation on reopened Q4/S3 Project inputs. The final isolated consumer wheel and installed solver passed 93/93 affected mixed static/modal/buckling tests; a subsequent example-only direct-definition parity addition passed 2/2 against those same wheels. Typed refusal, ineligible capability, cancellation and owner closure are exercised. The spectral request remains explicit at execution rather than stored in the Project, and F12/B14/G4B/G6 acceptance is open. [Consumer evidence](C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/docs/development/r8-b2-point-buckling-consumer-20261009/results.md). Mistral was cached unavailable from the prior worker attempts; Astra directly owned this bounded consumer integration without a new worker probe.
- F05 fixed-predecessor material pullback, F08 native local extraction and F09 physical B2 section/trace foundations are marked passed in the matrix. F06 chart transport has focused Q4 and all-S3 J2/fibre installed evidence, but finite-angle histories and broader acceptance remain open. B2 member-resultant envelopes have focused installed evidence.
- A scoped F06 repair now refuses force-control shell chart rebases if any reevaluated native beam history component changes, including a compensated physical-fibre low half. Q4 and all-S3 mixed-section refusal plus ordinary S3 rebase passed 3/3 focused source and 3/3 isolated installed-wheel checks; broader F06 acceptance remains open. [Source](../../.development/f06-native-rebase-guard-20261008-v4/results.md); [installed](../../.development/f06-native-rebase-installed-20261008-v2/results.md).
- G0B and F03 remain open, G1 remains experimental/unqualified, and G2–G6 retain all unclosed materials, attachments, topology, loads, spectra, imperfections, continuation, practical scale, executed external references, consumers, independent reviews and one coordinated release. No intermediate subset is the programme completion.

## Next actions and execution boundaries

**B2 practical-scale development screen (9 October):** the source-package runner built connected 24/8/2, 400/40/4, and 2,500/250/25 Q4/B2/rigid-pad models and completed 1/10/100 compatible physical-section load cases respectively, with one factorization per eligible batch and selected recovery. The largest completed 100-case route took 22.468 s process wall and sampled 468 MiB peak; seven attempts, including one preserved low-stiffness failure, consumed 60.242 s of the 240 s development allowance. Runner-only later-case diagnostics and post-spawn budget accounting were repaired and independently checked without repeating numerical runs; seven focused source-only tests pass. The 10,000/1,000 workload was not attempted under the 90 s/2 GiB child cap. This is not installed, G5 or B16 acceptance. [Evidence and precise limits](development/r8-b2-large-scale-20261009/report.md). The next useful B2 scale decision needs separated compilation/assembly/factorization costs or a separately adopted resource contract, not extrapolated qualification.

The subsequent bounded phase discriminator completed the 2,500/250 case with one RHS: 18.097 s owner construction included only 0.226 s sparse factorization. A separate 400/40 construction profile attributed 4.503/5.997 s to guarded E4 operations and 1.043 s to physical-footprint compilation. Both completed with CPU0 and one thread; the ledger is now 88.673/240 s with 60 s reserved. This directs development toward validated preparation and attachment compilation; it does not justify a factorization/backend change or qualify the 10,000/1,000 route. The profile's wall times are not speed-comparable to unprofiled runs.

The physical B2 footprint compiler now uses indexed shell incidence and sparse-in-block Hessian construction, preserving the exact five-row law. Twenty-four focused/existing source checks passed, including dense-Hessian, derivative, admission and public-owner coverage; scoped independent read review found no concrete defect. One matched 2,500/250/25, 100-case development screen took 19.422 s versus 22.468 s saved before the change (13.56% single-pair reduction), with all common recorded batch outputs and work counts identical; sampled memory rose 2.67%. This is a promising single source-pair screen, not a repeatable performance claim or installed G5/B16 acceptance. The ledger is 108.095/240 s with 60 s reserved. [Evidence](development/r8-b2-large-scale-20261009/report.md).

The exact optimized source at `7f877a52` also passed 46/46 affected tests from an isolated wheel, with three selected source/wheel/site byte bindings and all 249 imported solver modules under the installed site. A corrected second attempt explicitly verified Python assertions enabled, CPU0, one-thread pools and JIT off in a 15.206 s bounded run. The initial sandbox-temp build failure and a first installed run with an unverified assertion setting remain preserved. This closes affected-route installed integration for this slice only; the 10,000/1,000 B2 route, repeated installed timing and full G5/B16 remain open. [Installed evidence](development/r8-b2-footprint-installed-20261009/results.md).

**Earlier B2 full-size case-7 decision (9 October):** the installed 10,000-Q4/1,000-B2/100-pad route compiled correctly with 2,000 constraint rows and one factorization, but two registered attempts failed at case 7 after six accepted load cases. The second measured an accurate unscaled KKT row defect `3.862166973416920e-5`, above the unchanged `3.341500508002232e-5` physical equilibrium tolerance; reaction-evaluation rounding is not the cause. Both failures and `197.6114507/300 s` cumulative work are preserved. The remaining allowance cannot fit another full-size construction while retaining its 60-second reserve. The subsequent work guard and case-1 investigations above supersede this paragraph's former next-action suggestion; neither repairs the historical case-7 failure. [Attempts and decision](development/r8-b2-installed-large-20261009/results.md).

**Bounded BL5 coupled-material tangent coverage (development, not formal F03):** existing checks sampled nodal directions at a yielded Q4-J2/generalized-beam state but left retained and multiplier row families untested together. Reuse that reachable accepted predecessor at load position 1.0; check actual finite-rotation update derivatives by shell, beam, retained and constraint row groups over a three-step finite-difference plateau, with constitutive active masks held fixed. A failed group identifies a derivative/branch to investigate; a pass strengthens this combination's smooth-branch tangent evidence without claiming all directions or other material families. Use one bounded focused source run on CPU0, one thread, JIT off, 2 GiB, one job, and retain its complete receipt. The separate failed **physical-fibre** continuation is not the subject of this check. Do not consume formal F03 or repeat that historical continuation run.

**Result:** the [focused yielded tangent](../../.development/bl5-yielded-global-tangent-20261008-v1/results.md) passed 1/1 in 33.259343 s process-wall with 16 active generalized stations and two active shell layer positions. One seeded direction exercises shell, beam, retained and multiplier coordinates and checks each residual row family separately. Two adjacent steps meet `1e-5` with accumulation/alpha activity signs unchanged and accepted checkpoint bytes intact. A supporting read review found no concrete false pass, but material segment identity and individual-row accuracy are not proven by these masks/group norms. This adds evidence for that Q4-J2/generalized combination only; the separate failed physical-fibre continuation and broader G3/F03 obligations remain open. Next choose a distinct physical-fibre discriminator only if saved branch/controller evidence identifies a tractable uncertainty; continue other ready mandatory implementation meanwhile.

1. Reconcile the checked 16×4 Q4 norm/work entry with the full saved scalar-family support/ratio policy and physical-transfer evidence; do not infer the `0.43` floor for mixed or unverified entries. Obtain a complete different-family mechanics review before any formal F03 quotient. Resolve any identified equation/counterexample first; otherwise execute only the registered eligible assessment under its exact authority.
2. For E01, retain the resolved-port smoke as a finite-port diagnostic and the OpenSees point fixture as supplementary matched-section evidence. Separate host-independent direct director work from saved nodal `Mz`/drilling-coordinate work. The distinct, unadopted projected-polar candidate already supplies an explicit material-spin transpose, multiplier curvature and bounded virtual-work controls in `scripts/r8_e01_objective_polar_trace.py` and `tests/test_r8_e01_objective_polar_trace.py`; do not derive a duplicate map. Its Q4 host and material-frame law are not equivalent to the native point law. The next decision is whether a matched physical connection, shell, beam-section and support idealization justifies comparing that candidate, with independent sided work and a declared yaw-sampling rule. A finite-footprint comparator has its own identity and cannot close point-law E01. Do not launch another axial refinement, finite-solid solve or B31 output formatting without a discriminating observable. Continue independent implementation slices in parallel.
3. Only then assess a candidate over the registered seven ratios, growing spaces and three refinement levels with physical transfer, locking and full signed-KKT checks. Do not choose a multiplier from rank, residual, one quotient or one loaded comparison.

No owned numerical job is live. The graph-development allowance used `44.6444159/105 s`; only `0.3555841 s` remains above its mandatory `60 s` reserve, so it cannot fund another numerical check. A single registered-Q4 bound attempt wrote passing assertions but timed out during supervised exit; preserve its failed-execution status and use only separately granted fresh authority for a completed check. Use CPU0, one numerical thread, JIT disabled, 2 GiB process-tree memory and one job. Formal F03 remains **unconsumed**; the historical body retry and closed one-use campaigns are not renewed. V6 saved-sided-face authority was consumed earlier and its raw cut-face actions were not balanced; do not repeat or use them as accepted sided work. Protect `us3-modal-canary`; do not inspect or copy it. Do not communicate with the separate contact worker.

A Mistral read-only mechanics review was attempted twice on 8 October. The four-turn attempt exited after reading contracts; the targeted twelve-turn attempt reached source reads but produced no final findings, and its launcher process was gone when checked. This is an **incomplete worker review**, not a no-finding review or F03 acceptance. Full logs remain outside the repository under `C:/Users/AudunArnesenNyhus/.vibe/logs/session/unified/` (session IDs `85324b9c-f5a6-032d-f909-000b167548a3` and `37915fb8-c573-66d5-e039-20a1fd87f371`), with the second captured stream at `C:/Users/AudunArnesenNyhus/.vibe/logs/task-evidence/anysolver-bl5-f03-20261008/stream.jsonl`. Do not repeatedly retry the same service behavior. Mistral/local implementation workers were otherwise unavailable; Astra owned the coupled contract work and Git integration directly. The user's prospective approval covers work inside existing scientific, resource and release contracts; it does not renew spent authority or qualify a partial release.
