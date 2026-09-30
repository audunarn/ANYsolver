# Independent ANYfem staged consumer review

Read-only source and retained installed-evidence review, 2026-10-01. No product imports, solves, numerical jobs, source edits or Git mutations. I did not implement the four consumer files. Disposition: no consequential consumer ownership, persistence, dispatch, binding or lifecycle defect found within this slice. This is bounded development evidence, not F06 or broader staged mechanics acceptance.

## Exact source/artifact scope

ANYfem worktree parent: `6226230d0395bb917f88ca2271157d528bf05e20`. Reviewed current file SHA256:

- `src/anyfem/solve/stiffened_shell.py`: `4bc18d19b0e764514963a9d0c7445184c80055d1596882fd29a849462f709e2a`.
- `src/anyfem/solve/stiffened_shell_project.py`: `99c360a76ddf19a9b63e096f650353f80cb62567e3a27679f2984ea1c6804bf4`.
- `tests/test_stiffened_shell_staged_load_consumer.py`: `adf89954a0843771722b572bfbcd682c34c782f23b4bca53a6babe9857eb97b4`.
- `docs/EXPERIMENTAL_STIFFENED_SHELL_CONSUMER.md`: `3c81e118933f9d40f9d8b32f0fa16e05890debcac8f0158188fda5701753c44c`.

Installed ANYfem wheel: `92daa6370ca019a10de07779ac37238cf34be2bb4180752617d722344859dd75`; unchanged solver wheel: `0c45666609355e654cb726a0e4e0780d386bccfaafef1209ffd994bdd3b9d09c`. V2/V3 runners assert the complete 98 ANYfem + 388 solver Python-module inventories and source/wheel/site byte equality, then constrain all final product imports to the installed site. Both record effective BLAS=1, Numba=1 and JIT disabled. V2/V3 module hash inventories and wheel identities are unchanged.

## Contract review

`ExperimentalGEPointPanel.__post_init__` admits exactly the public staged descriptor type and requires empty legacy actions. It reconstructs the descriptor through public serialize/deserialize, owning its normalized actions and all future endpoint identity. `to_dict` uses an explicit staged-v4 envelope around the complete existing v1/v2/v3 panel record, plus descriptor. `from_dict` requires exact fields/status/profile, restricts the inner schema to those legacy point schemas, delegates descriptor policy/bounds/moment/identity validation to the solver and applies exclusivity again. Nested staged envelopes and implicit downgrades fail; no endpoints or unsupported moments are silently dropped.

Standalone save/reopen and native Project encoding/validation remain input-only. They detach nested JSON and revalidate the route-bound parser without creating a mechanical owner. The new no-assembly test explicitly replaces public owner construction with a failing stub during construction, standalone persistence and `.anyfem` Project save/reopen. Native mutable analysis payloads are revalidated on save, including future endpoint tampering. Legacy schema/default selection, Project format, ordinary analysis records and B2 dispatch remain distinct. The staged descriptor's model identity is not treated as proof of physical admission during persistence.

`create_analysis` builds the actual public owner from the complete stored panel, checks its public preflight physical identity against the descriptor and closes it on admission failure. The solver still checks every endpoint's node/scope before trials. `load_input` explicitly selects the programme or original action tuple. `solve_point_panel` requires explicit staged targets, rejects finite options on legacy routes and GE `on_case`, and forwards target positions, finite budgets, cancellation, adaptive controls and accepted observer unchanged to the public finite solve. It does not multiply forces by positions, infer targets or implement mechanics. The temporary owner closes in `finally`; the existing GE owner close clears references and marks closed. The stub failure test checks the identical original MemoryError object is rethrown while closure occurs. Returned results are detached solver results, not durable state: a caller uses `create_analysis` and a separately retained opaque checkpoint for restart.

The documentation accurately distinguishes input persistence from solver checkpoints and actual model admission, keeps explicit unsupported routes, and does not extend staged scope to BL5/B2, moments, follower forces or complete unloading. Save/reopen never interprets accepted-state bytes. Callback/cancellation option forwarding is tested with a stub; this campaign does not independently establish every callback/cancellation mechanical path through a Project, which remains the solver owner's contract.

## Installed inventory and reuse

`TEMP/r8-anyfem-staged-installed-v1/build.log` preserves the pre-wheel pip cache permission failure (`WinError 5`); it is not an installed product test or a successful wheel build.

V2 runs 51 cases: 13 staged metadata/dispatch tests, 36 existing Project/GE/B2 tests, and two installed Q4/S3 Project-to-solve-to-checkpoint/restore/continue workflows. The actual inventory is **50 passed, one failed, zero skipped/errors**, with 275 onsite imports. The failure is `test_installed_staged_project_owner_restart_and_continue[True]`: the S3 small-load path (beam Fz=100 N, then Fy=30 N added; four requested positions; fixed stepping) reports `FiniteIncrementFailure: finite mixed backtrack budget exhausted`. Retain this unresolved numerical failure; V2 is not all green.

V3 selects only that S3 workflow and changes only its mechanical path/options to the previously successful frozen staged F06 fixture: same shell/beam geometry and S3 triangulation, first beam105 Fz=1 MN, then the same beam force plus shell3/6 Fz=-/+375 kN, positions (.125,.5,.75,1.,1.125,1.5,1.75,2.), default adaptive control, 20 Newton iterations/12 backtracks. It retains Project save/reopen, helper finite dispatch, direct control, accepted position-1 checkpoint, fresh restore and continuation. It passes one case, 274 onsite imports; process observation is 76.4388 s and 217,997,312 B peak RSS. This demonstrates the consumer route on that admitted path, not successful execution of the failed small-load path.

The V3 manifest byte-binds V2 verification (checked against actual V2 `verification.json`). The staged metadata test, existing Project test and common fixture hashes are identical; only the installed workflow fixture differs, with the S3 conditional adding the strong path and adaptive options. The Q4 branch retains its V2 small-load inputs/options; its retained V2 pass is applicable. Thus reuse of 13+36+1=50 V2 passes plus one V3 S3 pass is justified as a **combined scoped inventory**, not a fresh 51-case green rerun or 51 passes on the original inputs. The Q4 mechanical workflow uses its existing historical pullback selection; this does not newly certify every nested policy/material combination.

## Limits and disposition

The installed workflow checks result fields, accepted positions, programme identity, applied force, equilibrium/gaps and restart parity. It does not independently compare complete nonlinear material-history trees or prove noncommutation/chart transport; those belong to the separately retained solver F06 evidence. The successful S3 specimen is elastic and does not establish arbitrary yielding, unloading, material laws or load amplitudes. The failed S3 small-load workflow is preserved and unresolved. Strict zero-load equilibrium behavior is unchanged. No criteria, floors, versions or loads were relaxed in the consumer code.

Accept the bounded implementation/evidence handoff as input persistence and explicit finite delegation on the two demonstrated Q4/S3 routes, subject to the parent's acceptance authority. No source correction is required from this review. Do not elevate it to all-path convergence, broad material/staged programme closure, F06/F03 qualification or a resource-performance gate.
