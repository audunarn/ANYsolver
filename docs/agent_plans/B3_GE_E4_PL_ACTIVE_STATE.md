# B3-GE / E4-PL / B2 active state

Updated 28 September 2026. Living note for Revision 7. The historical checkpoint
`B3_GE_E4_PL_CURRENT_CHECKPOINT.md`, complete programme, protected evidence,
scientific limits and one-use F03 authority retain their original meaning.
`ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1` governs prospective process.

Revision 7 resumes experimental integration while G0/F03 remain open. The user
approved a prospective, independently reviewed replacement F03 assessment and
repeatable versioned execution; historical failed runs and consumed authorities
are not re-scored or replayed. New development diagnostics may use up to 100,000
rows, 600 seconds, 8 numerical threads and 8 GiB per process tree, with one
heavy numerical job at a time. Existing protected evidence and other limits
retain their original contracts. The immediate delivery is the consolidated
installed GE/ANYfem and B2 workflows; the separate mechanics question is
whether a six-channel drill-free line trace and compatible multiplier pairing
passes objective work, shear, transfer and growing-space stability. No F03
candidate or assessment metric has been selected. G1 acceptance remains open.

## Revision 7 integration evidence

Source is `7061c555` plus the targeted Revision 7 GE factorization, B2 topology,
local L1 probe, tests and this note. A development wheel built from a copy of
those `src/anysolver` files has SHA-256
`68D142DE2CAF86239E5BE64A235AD7447B7492F8827F0F2BFF19C36C51DDA02B`.
Its bytes and full build/install/test logs are preserved under
`.qualification/b3-ge-e4-pl/r7-integration-dev-20260928-v2/`; the wheel is
stored as `anysolver-0.4.7-wheel.bin` with the same hash. The installed import
was `C:/Users/AudunArnesenNyhus/AppData/Local/Temp/anysolver-r7-installed-integration-dev-20260928-v2/venv/Lib/site-packages/anysolver/__init__.py`.
With `NUMBA_DISABLE_JIT=1`, a temporary pytest configuration outside both
repositories and the installed wheel, 33/33 focused solver/L1 checks and 3/3
ANYfem consumer checks passed. The consumer imported from the separate
`C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/src/anyfem/solve/stiffened_shell.py`.
The installed environment was Windows 11, Python 3.14.2, NumPy 2.4.6,
SciPy 1.17.1, ANYmaterial 0.2.0, ANYmesher 0.5.0, ANYfileio 0.3.2 and
threadpoolctl 3.6.0; effective OpenBLAS threads were 1 (`OMP_NUM_THREADS=1`).
The consumer test now compares restored factor-2 state and reactions with an
uninterrupted run. The earlier ordinary JIT-enabled source test was interrupted
during import and is not a passing check. The snapshot wheel omits optional
repository documentation and is a development artifact, not a G6 wheel/sdist.
Independent read-only review found no consequential defect in the targeted
factorization, topology and local-chart guards; F03 formulation and the other
scientific foundations remain unaccepted.

## Decision sought

Deliver an experimental multi-element point-connected owner while deciding the
native six-channel line law and multiplier resolution. Experimental G1 coding is
permitted during open G0B; **G0B/F03 and G1 acceptance remain open/barred**. No
production qualification or release is implied.

## Established behavior and evidence

- Branch `codex/b3-ge-e4-pl-integration`, original head `f50583da`; main untouched.
- Sparse experimental GE owner solves two Q4/two native generalized B3 members,
  or mixed Q4/S3 and all-S3 reference-linear variants, with three eccentric
  point ties and 48 retained beam coordinates. It exposes the explicit facade,
  preflight, reactions, immutable recovery, checkpoint, restore and close.
  Disconnected shell cells are rejected. The Q4 reference-linear panel has a
  120-row, 4,428-nonzero KKT; 100 N tip load gives free equilibrium `7.94e-14`,
  constraint max `3.34e-19`, support Fz `-100 N`.
- The same point-connected GE owner now has an **experimental elastic finite**
  route: 1000 N Fz, factors 0.5 and 1.0, accepted predecessor and native retained
  variables, then checkpoint/restore and continuation to factor 2. Rejection,
  cancellation, first-attempt retry with a different load pattern, rotational
  cutback and partial-prefix publication are tested. Mixed Q4/S3 and all-S3
  finite panels now pass the same two-increment and restart/continue checks
  (`7/7` finite tests); plasticity, physical scaling and G1 qualification
  remain open.
- Separate physical B2 connected beam graph runs 1/10/100 compatible loads,
  selected recovery and one factorization through the public facade. It has
  no shell attachment. Bounded public routes join one Q4/one B2, and now two
  Q4/two physical B2 members, through existing F10 point laws. The two-member
  panel matches an independently assembled dense reduced oracle for two loads,
  reactions, multipliers and work. Its bounded dense rank audit is not a
  production-scale constraint audit. Typed numerical failure gives non-success;
  programming errors propagate. These routes remain experimental.
- Previous focused new/legacy regression: 71 passed after Q4/S3, B2 graph, and
  bounded B2/Q4 point integration; the three B2/Q4 point tests passed after
  review fixes. New finite/panel-focused source checks: 18 passed; nearby
  B2 attachment/batch/descriptor checks: 41 passed. Current disposable wheel
  SHA256 `D7EE9D6AEBFAE4DBD53E5816B576AF95A7CD1BD31343AF63C783D84503F7AD95`;
  its actual installed import passed the same 18 focused checks. Earlier wheel SHA256
  `26DDDEA1F7DDC6D7FC08F3D60CDEC592F45347C17D26CDAE56ED3D1D2F08E055`
  was the actual imported package for the Q4 example, mixed/all-S3 runs,
  B2 1/10/100, and B2/Q4 point solve. Independent
  finite-driver review found two atomicity/cutback defects; both were repaired
  and focused regression passed. B2/Q4 rejects overflow and names general
  affine-plan reactions accurately.
- F01-F13 have useful bounded evidence but none is fully accepted. The
  independent foundation inventory remains in the prior handoff; do not
  infer G0 closure from local implementation tests.

## Connection decision

The bounded x8/B3-14 2:1 Fy/rotation diagnostic reproduced beta `0.364430`,
normalized least-dual work `0.13280935`, auxiliary shell Riesz work
`0.10129863` and beam work `0.03151072`. Strong alternating Fy/Mx cancellation
was found; no row/norm arithmetic defect. The 1,286-row, 54.01 s,
one-thread source-bound result is
`B3_E4_F03_C1_X8_B14_FY_ROTATION_AUDIT_DEV_V1.json` (SHA256
`40aeaf34a38ffcf6cba5fcd7675597b1a18b86f48cf0fc9b62b11c53b3f4d19d`).
Two earlier computations completed but could not write evidence. Riesz work is
not a physically loaded equilibrium. Existing Mx/Fz reference actions cannot
qualify independent Fy/shear transfer. No multiplier candidate was selected.

No saved independent supported Fy/shear case matches the 0.1 m bond, 35 mm
plate/Q4, square bar and supports. Existing F5 C3D20R +100 Nm Mx/-1000 N Fz
common work induces Fy but is not a prescribed Fy test; the same-action Q4
comparison separates action representation only for Mx/Fz. The next
discriminator is a supported, physically matched Fy/shear action with the same
geometry, supports and force/couple work, recording both support and sided work.
A mismatch in continuous prohibited motion revises the law; an all-channel
discrete compatibility failure motivates one derived resolution candidate;
a physically admissible compliant mode goes to transfer/convergence checks.
One targeted candidate batch at most before focused mechanics review. Formal
F03 authority remains unconsumed; 1,900 diagnostic rows, 120 s/run and one
numerical thread remain binding.

The first supported Fy solid attempt used the saved F5 side-cut geometry and
changed only the quadratic tip-face work to +100 N Fy. Preflight verified
the `(0,100,0; -6.75,0,100) N/Nm` origin wrench. The pinned one-thread
CalculiX execution reached the 120 s cap before producing `.dat` or a
completed step; its immutable failed raw root is
`.qualification/b3-ge-e4-pl/f03-c1-supported-fy-factor5-dev-20260928-v1`.
It supplies **no** physical-response comparison. Do not infer a formulation
failure or increase the cap. A lower-cost factor-4 instance is under focused
review as the sole possible fallback in this diagnostic batch; if it cannot
distinguish the hypotheses, stop external execution and identify the missing
observable.

The matched native x8/y4 +100 N Fy solves for B3-18 (1:1) and B3-14 (2:1)
passed 44/44 supported rows and global wrench/work checks. Tip Uy is
`0.452009` versus `0.440575 µm`, and shell-support Fy is `−93.989` versus
`−93.613 N`; maximum continuous Fy gap is `6.14e−10 m` versus numerical zero.
The earlier weak Fy/rotation least mode is not by itself a loaded failure under
this uniform action. Full source-bound evidence is
`B3_E4_F03_C1_FY_SUPPORTED_NATIVE_DEV_V1.json` (SHA256
`A50837D8043356219275EE7B24F63EDBCF0023A0A874DA3C711358561073082B`).
This does not select the law or multiplier. A factor-4 solid Fy comparison can
check physical transfer but cannot alone allocate law versus discrete-space
error; interpret it with the native continuous gap and all-channel row work.

## Next integration action

Commit and review the consolidated solver and consumer slices, then resolve the
unit-scaled stress-free check and checkpoint scale contract without changing
historical checkpoint decoding. Keep line/footprint mechanics behind replaceable
interfaces. Complete F01-F13 and G0-G6 without weaker physical criteria or an
interim release.

**Earlier pause snapshot, 28 September 2026 (historical).** Solver HEAD was
`7061c555`; the only uncommitted solver source then was
`scripts/b3_e4_f03_c1_fy_supported_reference.py`, alongside this living note.
Its factor-4 pure-Fy fallback is prepared in source but has not been preflighted
or executed. The factor-5 Fy run timed out and remains failed evidence. The
native Fy pair is saved and independently read-only reviewed; its smooth load
does not demonstrate excitation of the alternating least mode or select a law.
At that pause no numerical process was running. ANYfem's separate experimental
consumer worktree had three untracked files and 2 focused/38 nearby checks
passed; its note then named the prior solver commit. Revision 7 work has since
resumed and the updated installed checks are recorded above.
