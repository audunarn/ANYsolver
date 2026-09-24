# General contact restart checkpoint — 24 September 2026

## Objective and ownership

Continue implementing the user's C0–C9 ANYsolver general-contact plan. The isolated worktree is `C:\ANYworkspaceWork\ANYsolver-general-contact`, branch `codex/general-contact-core`; the original `C:\Github\ANYsolver` checkout was not edited. C0 is committed as `31e60277` (`Add opt-in planar shell contact prototype`). No PR, merge or publication occurred. Keep concurrent repository work untouched.

## Completed C0 slice and evidence

- Opt-in planar qualified Q4 against a fixed plane, frictionless penalty mortar, physical sides, force/displacement static routes, coupled residual/tangent, gap diagnostics and step limiting, small-rotation contact restart schema v2, example and capability ledger.
- Status is **implemented and locally tested**, not independently accepted. C1–C9 remain open.
- `62 passed` in `C:\ANYworkspaceWork\general-contact-evidence\regression5.txt`; after a stricter checkpoint version check, `29 passed` in `C:\ANYworkspaceWork\general-contact-evidence\restart6.txt`.
- A disposable wheel built from committed C0 code has SHA-256 `1d192e7b13171465928eac9156ece96bbedb4bcc1a0c895611594543c1980f66`. The isolated installed copy ran the guided plate example; output is `C:\ANYworkspaceWork\general-contact-evidence\installed-example-current.txt`.
- Known limit: corotational contact restart remains rejected because its Q4 committed-state binding failed validation in an exploratory run; no-contact schema v1 is preserved. Free shell normal translation after opening lacks a dedicated rigid-mechanism diagnostic.

## C1 guided-pair development state

- Internal planar Q4/S3 projected-overlap kernel: `src/anysolver/general_contact/overlap.py`; Q4/S3 and S3/S3 geometry checks passed (8 tests after face-scale fix). These geometry checks do not admit S3 coupled contact.
- Exploratory guided planar Q4/Q4 pair kernel in `src/anysolver/general_contact/pair.py` and static integration hooks in `core.py` and `nonlinear_static.py`. Fixed reference overlap; only uniform facewise normal translation; penalty law; both-body residual/tangent and physical offset couples. No finite sliding, augmentation or pair restart. The 6 focused pair tests passed, including the tilted-director couple check.
- Runnable nonmatching Q4/Q4 pair example and limits are `examples/general_contact_guided_pair.py` and `docs/GENERAL_CONTACT_C1_GUIDED_PAIR.md`. The example completed with 0.4 N opposing forces and -0.4 micrometre gap from the checkout source. This is a local development check, not installed-package or engineering qualification.
- The Q4/Q4 slice was committed as `ecd93305`; affected C0/C1 checks passed: 30 tests in `C:\ANYworkspaceWork\general-contact-evidence\c1-guided-pair-check1.txt`.
- Current post-commit edits admit guided S3 V2D pairs using its physical director and reference-surface offset. First-touch reference gaps are snapped only within the geometric roundoff tolerance to keep the closed-side tangent active. An exploratory run failed with two wrong-signed micrometre gaps and one singular S3 trial before the orientation and roundoff corrections; the corrected affected run passed 35 tests in `C:\ANYworkspaceWork\general-contact-evidence\c1-guided-s3-check1.txt`. The final S3 directional-tangent addition passed all 11 pair tests. Source review and a local commit are next. Do not claim C1 accepted or complete.

## Prospective policy transition

`ANY_ECOSYSTEM_RISK_PROPORTIONATE_ENGINEERING_V1`, revision `2026-09-24.1`, is adopted locally at `C:\Github\ANYopenSoft\governance\ECOSYSTEM_PHILOSOPHY.md` (SHA-256 `92e458e1c3d1c252fdc22c2f1d90c2ffb976601e67a59545d162ec3d6110468d`). Use this single living note and the existing tests/evidence instead of a new dossier or review ceremony for each C1 helper. The contact plan's mechanics, geometry, restart, resource and numerical criteria, independent milestone acceptance, installed-package and application gates, and separate publication/merge decisions remain in force. C0 is still locally tested, not accepted. The current guided-pair slice is only an exploratory subset of C1. No amendment or extra approval is needed for authorized local development; any change to a frozen acceptance criterion or execution authority requires the contract's explicit amendment, and acceptance/release retains its existing review and approval boundary.
