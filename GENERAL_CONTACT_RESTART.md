# General contact — living task note

Updated 26 September 2026. The complete earlier decision, failure, execution-authority and evidence log is preserved in [GENERAL_CONTACT_HISTORY.md](GENERAL_CONTACT_HISTORY.md). This note records the current decision and next bounded action; it does not supersede the historical evidence or the adopted 26 September implementation plan.

## Scope and authority

- Required programme: C0–C9 under `ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1` revision `2026-09-24.2`. Scientific scope, tolerances, frozen/consumed execution authorities and failures remain unchanged.
- Integrating worktree: `C:\ANYworkspaceWork\ANYsolver-general-contact`, branch `codex/general-contact-core`. Original `C:\Github\ANYsolver` checkout is concurrently owned and untouched.
- Current committed baseline: `d15be67b` (C6 Q4/plane transient **development** slice). Work after that commit is uncommitted D1 development. Nothing in this note claims independent acceptance, release, publication or merge.
- Up to two bounded workers were authorized. Geometry worker owns new S3 and Q4/S3 derivative primitives and tests. Independent mechanics reviewer performed read-only early scrutiny; lead owns shared drivers, settings, enforcement and integration.

## Current position

1. D0 C6 prototype final focused checks passed 19/19 in 24.36 s. Its 80-step source example completed; see history for outputs and limitations. C6 remains developmental.
2. The coupled 64-Q4 partial-contact active step remains **rejected**: 17 augmentations, 19 active modes, pressure change 1100.58 Pa versus 0.2 Pa target, 906.46 s. Gap passed its registered 50 µm budget, but no active response was accepted. Do not rerun or relax budgets without a specific response-operator diagnosis and full trace capture.
3. Corrected the pivot multiplier-to-force derivative from `-dW` to `-(dW-g dS)` and checked the moving-support Schur response against an independent small analytical system. A new bounded many-mode projected Schur proposal exists, but is not yet coupled to structural re-equilibration or the active static path.
4. Added a diagonal-normalized supported pressure Gram diagnostic. The static result now reports scaled rank/condition separately from legacy unscaled values. This corrects interpretation of tiny supports without rewriting historical evidence.
5. Added Jet2 S3/S3 projected overlap support and weighted-gap derivatives, including shared pressure-node assembly in the projected-normal work. A zero-area touching pair, including one sharing an active pressure node, raises an explicit branch error. `ContactSolverSettings.general_s3_differentiation="jet2_s3_dev"` opts into this route for eligible augmented general S3/S3 patches; default behavior is unchanged. A smooth shifted static path completes and restarts with matching displacement. Exact clipping ties remain unsupported in this development route.
6. A bounded affine Q4/S3 Jet2 overlap primitive and seven focused tests exist, including independent warped-direction finite differences against the production Q4 kernel. It rejects warped/non-affine base poses and unresolved integration branches and is not yet wired into the static manager.
7. The affected development regression batch passed 46/46 in 332.71 s; complete output is in `reports/general_contact_d1_focused_20260926.txt`. It covers the new derivative/static/restart path, the corrected pivot, pressure diagnostics and existing S3/Q4 partial-pressure routes. This is focused testing, not formal qualification or whole-route performance evidence.
8. After a local evaluation-counter adjustment, the three directly affected test files passed 13/13 in 150.92 s. The change only counts inactive Jet2 local pair evaluations consistently; it did not alter contact equations or the accepted scientific gates.

## Next decision-oriented slice

Principal uncertainty: can the corrected constrained gap response and many-mode Schur proposal reduce the 64-Q4 multiplier residual while preserving the existing physical gap, equilibrium and resource gates? Competing explanations are an incorrect pressure response operator, rank/conditioning from small supported modes, or an intrinsic projection/support topology change.

An analytical moving-support oracle now confirms (a) and (b), including an independently re-equilibrated multiplier perturbation. The next bounded check is one physical two-face shared-node patch with 2–4 pressure modes: compare the constrained gap-response columns and projected residual against independently re-equilibrated perturbed multipliers, and separate topology changes from a smooth response. If they agree, connect the bounded Schur proposal to the static augmentation loop with guarded re-equilibration and fallback; otherwise repair the discrepant block. Only then revisit the unchanged 64-Q4 mechanical case with complete pressure/active-set/cutback trace and an explicit resource cap.

The first independently accepted handoff remains planar nonmatching Q4/S3 static press, slide, open and recontact, with physical skins, integrated reactions, independent gap checks, restart and installed verification. Later D2–D8 and full C0–C9 obligations remain open.
