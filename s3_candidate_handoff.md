# S3 R1 candidate handoff

Status: verified against focused assigned checks; broader scientific acceptance and non-VK baseline comparison remain with parent. Experimental candidate only. No B0–B9 acceptance, adoption, qualification or release claim.

## Result and formulation

Current default NativeParityE4PLS3V2DShellElement now has explicit `von_karman=True` evaluation. Default local response retains its prior arithmetic, used by LINEAR and corotational constitutive evaluation. Q4 and old native S3 are untouched.

For constant reference triangle transverse gradient g=G*u_local=(wx,wy), epsilon=Bm*u_local+[wx^2/2,wy^2/2,wx*wy]. The differentiated membrane operator adds [wx*Gx; wy*Gy; wy*Gx+wx*Gy]. Existing curvature, shear, signed offset/polarity operators, generalized-section coupling, layered return map and PL stabilization remain. Force is the quadrature-weighted differentiated strain operator transpose times physical resultants, plus PL*u. Tangent is its constitutive derivative plus sum(area/3 * G.T*[[Nxx,Nxy],[Nxy,Nyy]]*G). N includes initial resultants and returned material stress. This is the fixed-reference moderate-rotation VK hypothesis, not a finite-rotation replacement.

## Integration and changed files

- src/anysolver/e4_pl_s3_v2d_element.py: explicit candidate law; force/tangent; marked trial states; virgin accepted-state recovery; incompatible mode refusal.
- src/anysolver/nonlinear_element_evaluation.py: exact V2D explicit-kinematics dispatch; existing other-family call remains.
- src/anysolver/nonlinear_static.py: reference scalar explicit mode, state-absent final recovery.
- src/anysolver/nonlinear_performance.py: explicit VK scalar lane in existing VK-only plan.
- src/anysolver/nonlinear_performance_batch_b.py, nonlinear_performance_batch_c.py, nonlinear_reduced_assembly.py: one explicit VK argument per scalar evaluation call. Parent approved narrow scope delta. Existing plan wrappers admit VK only; corotational uses reference fallback. Impact reduced controller also excludes non-VK.
- src/anysolver/e4_pl_s3_v2d_state.py: parent-approved optional integrity-sealed experimental_von_karman_law=S3_V2D_VK_R1. Existing non-VK payloads unchanged. Historical unmarked/unknown VK rejected, and marked VK cannot be interpreted in another mode. No automatic history migration.
- src/anysolver/recovery.py: parent-approved changes only in _recover_v2d_committed_state. Existing stored station/layer quantities are consumed without constitutive replay; candidate VK tensors use reference frame and report that provenance. LINEAR/corotational frame branch unchanged.
- src/anysolver/current_state_tangent.py: parent-approved explicit ElementCapabilityError for candidate VK spectral decomposition. No silent corotational Hessian. Loading tangent remains available with fixed predecessor.
- tests/test_e4_pl_s3_v2d_von_karman.py: nine focused regressions. Existing tests unchanged.
- s3_candidate_handoff.md: this checkpoint/handoff.

s3_v2d_fast_assembly.py inspected and unchanged: reference stiffness-only caching; legacy nonlinear batching excludes exact V2D. All product changes within original ownership plus explicitly approved deltas. No Git mutation or sibling source/worktree read. Canonical philosophy read under parent exception. Prior Sonnet unavailable (credit); OpenAI fallback authorised prospectively.

## Checks actually run

Exact command: `py -3.14 -m pytest tests/test_e4_pl_s3_v2d_von_karman.py -q --basetemp=C:/ANYworkspaceWork/codex-s3/.pytest-s3`.
Runtime verified from saved metadata: Python3.14.2; import C:/ANYworkspaceWork/codex-s3/src/anysolver/__init__.py; PYTHONPATH own src; OMP_NUM_THREADS=1. One process at a time, hard process-tree bound <=900s. No plate above n4. Runtime constraints are evidence metadata, not checked-in machine-specific assertions.

Evidence folder: C:/ANYworkspaceWork/codex-s3-notes/evidence/openai-r1/.
- check01: sandbox launcher failure112, 0.088835s, no Python found; retained stdout/stderr and hashes.
- check02: 6 passed/2 failed, 7.579225s. One test incorrectly used FEModel weak-key cache before installer; corrected test to direct plan build. Public production route exposed additional acceleration call sites missing mode, rejected by marker check; fixed approved call sites.
- check03: 8 passed, 9.3175598s. Early green candidate.
- check04: 8 passed/1 failed, 9.4613842s. Strengthened free-residual regression misread load-vector API tuple; corrected tuple unpack, no tolerance weakening.
- check05: 9 passed, 9.140509s. Final relevant verification. Full stdout/stderr, exact command, hashes, timing and runtime in check05.{json,stdout,stderr}; measurements in check05.measurements.json.
- git diff --check passed on final product/test inputs; status confirms only owned/approved files changed.
Cumulative process wall across attempts35.587513s; remaining of conservative900s aggregate bound864.412487s. No process remains running. Check supervisor retains failures and hashes of all affected product files and new test; includes unique outputs and process-tree kill on timeout.

Measured results in final check:
- Affine w=.02*x recovers exx=.0002, demonstrates nonlinearity; legacy default local response has zero membrane strain.
- Full18x18 force-difference relative tangent errors: elastic5.55436e-12; yielded5.452998e-10; generalized5.91601e-12 (criterion<=1e-6). Cases include initial stress, offset and director reversal, and fixed predecessor/nonmutation/roundtrip.
- Public clamped n4, t=.003m,E210GPa,nu.3,p50kPa,4steps: deflection12.498442490358884mm, free force residual1.2152401646252717e-9; displacement hash5d9e9e85cde7d7fd1f18aa6ac43f293379793fff9e19c798bbeeb07f735318f1. Prior supplied baseline missing membrane law115.43mm. Coarse regression band10–16mm around supplied independent11.79mm reference; not a scientific tolerance/acceptance decision.
- Reference/plan scalar dispatch agrees, accepted recovery uses reference frame, candidate provenance/tampering and spectral refusal are tested.
- Virgin accepted-state recovery produces exact candidate state; performing VK evaluations does not alter default local/corotational force/tangent/state bytes or linear stiffness bytes.
- Actual solver state transaction candidate discard preserves virgin history without mutation. This covers rollback primitive; full cancellation/restart campaign not run.

## Remaining acceptance work and limitations

Parent owns broader B4 baseline LINEAR/corotational byte comparisons, B5 loading checks and any resource-authorised campaign. The focused isolation test is not evidence of complete baseline mesh bit equivalence. No reference convergence/plastic-collapse acceptance or independent review has been run by this author. Historical VK states cannot migrate automatically; candidate VK current-state eigen decomposition remains explicitly unsupported by parent decision. No further product edits/checks pending for this focused slice. Parent may return specific review findings to same owner.

## R1 integration repair early checkpoint
Freeze released by parent; only owned/approved files are being edited. Deleted-history defect confirmed by source and parent retained reproduction: deleted hook discarded explicit solver mode. Implemented explicit von_karman keyword forwarding and exact-V2D caller mode; accelerated deletion dispatch now routes exact V2D to frozen-history reference assembly. Non-VK hook default remains False; no state-selected active mode.
Remaining: regressions for two production assemblies after deletion and frozen-history immutability, public cancellation after accepted step with input-state preservation, and yielded uniform stretch+bending PSD with rigid modes removed. Then same focused test command under remaining864.412487s aggregate check budget. No checks run since freeze release; no additional physics/tolerances/adoption.

## R1 integration repair final handoff (supersedes focused-check count above)

State: verified against the expanded focused criteria, experimental only. No scientific adoption/acceptance claim. Parent froze numerical inputs during its checks, then explicitly released the freeze and authorised this connected repair.

Changes since check05:
- e4_pl_s3_v2d_element.py: deleted frozen-history operator accepts explicit von_karman=False keyword and forwards it. VK direct callers must supply True; no inference from predecessor metadata. Default local/non-VK arithmetic unchanged.
- nonlinear_static.py: deleted operator receives explicit VK context only for exact V2D, from current solver kinematics. Other element signatures unchanged.
- nonlinear_performance.py: exact V2D deleted elements use validated frozen-history reference assembly rather than the ordinary active-history plan.
- tests/test_e4_pl_s3_v2d_von_karman.py: added both-mode frozen-hook byte comparisons, two successive production optimized-wrapper assemblies after deletion at changing displacement with0.1 residual scaling and frozen-state integrity, real public cancellation after first accepted increment followed by successful reuse of unchanged supplied initial state, and physical yielded stretch+bending PSD test.
- This handoff note. Other original R1 product files unchanged during this repair. Original/snapshot/sibling files were not edited. Concurrent parent-owned changes to two historical tests and .s3-baseline/.pytest-s3 scratch were observed in status and left untouched.

PSD test uses uniform tensile membrane stretch with compatible bending/linear triangle transverse field; every material layer yields (minimum alpha0.007352588829163642). It subtracts numerical PL stiffness so stabilization cannot conceal physical indefiniteness, projects out six reference rigid-motion directions, and checks both full physical and projected symmetric eigenvalues against floating-point roundoff256*eps*||Kphysical||2. Minimum projected eigenvalue-3.0178217299022615e-8, full-1.240933569517172e-8, roundoff bound7.536285344248547e-6. Thus no resolved negative physical stiffness in this prescribed tensile yielded fixture; this does not claim PSD under compression/all plastic paths or replace B6 adjudication.

Same exact authorised pytest command and basetemp as above:
- check06:14passed,9DeprecationWarnings,12.7454095s precise process wall. Warning came solely from test reference rigid-axis cross product with2D coordinates; changed to explicit3D coordinate, no physics/tolerance change.
- check07:14passed, no warnings,10.6297043s precise process wall, exit0, no timeout. Full evidence check07.json/.stdout/.stderr/.measurements.json in openai-r1. Final hashes include all original and scope-delta product files and test. Runtime Python3.14.2, own source path and OMP1 recorded.
Total focused-check aggregate process wall58.9626268s; remaining841.0373732s of conservative900s budget. Final numerical process finished; parent notified before its B9 timings. No process running, no further product writes or numerical work planned.

Final n4 unchanged12.498442490358884mm; free residual1.2152401646252717e-9; yielded full FD5.452998348323247e-10. Historical candidate current-eigen decomposition remains deliberately unsupported. Broader B7 failures, B2/C4 acceptance shortfall, matched-cost/B9, final non-VK baseline comparison and independent acceptance belong to parent and are not waived by these14 tests.
