Review complete. Findings below are from the current main tree and the gate-closure evidence only.

## Findings

**Current state is usable for elastic and default-route plastic work, but the public guide understates it.**
- `docs/BEAM_SHELL_CONNECTION.md:97-100` says plastic coupled displacement-control continuation/restart "remains incomplete" and "completed target cases have not been established". The terminal assessment contradicts this for the default route: `retained-coordinate-terminal-root-assessment.json:24` records the revised -11/60 m target passed including restart and state integrity, and the 17-test continuation partition passed in `retained-coordinate-final-regression-summary.json:79-93`. What remains open is the original -0.20 m target, the analytical accuracy gate, and the director route. The guide should say exactly that, neither more nor less.
- `CHANGELOG.md:3-34` has no Unreleased entry for `rotating_eccentricity`, the `MeshConfig` forwarding, `connection_trace="director_integrated"`, or the retained-coordinate restart repair. These are on main already. Users reading the changelog cannot find the feature.

**Result completion contract is sound in code but only discoverable by reading the solver.**
- Under displacement control, status starts as "completed" at `nonlinear_static.py:3882` and only drops to "stopped_at_limit"/"diverged" on a failure branch at lines 4734-4738 and 4761. Line 4997 sets stop_reason to "target_displacement_reached" exactly when no failure occurred. So status "completed" does mean the target was reached.
- `converged` at `nonlinear_static.py:772-774` includes "stopped_at_limit". The guide warns about this at lines 105-109. That warning is correct and must stay.
- The achieved controlled value is only on `steps[-1].control_value` (line 4861) and in `info["force_displacement_history"]` (line 4870-4871). There is no result-level field for it. The guide tells users to compare it against the target without saying where to read it.
- Checkpoint restart refuses any checkpoint whose terminal status is not "completed" at `nonlinear_static.py:6116-6119`. A stopped-at-limit beam-shell run therefore cannot be continued by checkpoint. The working continuation route is the manual one the slice3 tests use: `initial_displacements`, `initial_element_states`, `equilibrate_initial_state=False` (see `tests/test_nonlinear_beam_shell_slice3_director_continuation.py:106-111`). That is undocumented for users.

**Three tests on main fail by design of the evidence, not by accident.**
- `test_nonlinear_beam_shell_slice3_director_continuation.py` tests 3, 4 and 5 fail because the director route stops at -1/6 m. Their completion oracle at `tests/test_nonlinear_beam_shell_slice3_continuation.py:591-597` requires status "completed" and the probe within 1e-8 of target, so the failures are genuine open-gate signals.
- This means a clean checkout does not have a green test suite. Any "installable bundle" statement must say so.

**No concretely repairable accuracy defect is evidenced. Further solver work is not supported by the record.**
- The assessment at `retained-coordinate-terminal-root-assessment.json:26-27` states the TRF probe exhausted 40 evaluations and both derivative audits crossed material branches, so no tangent defect or nonexistence was established, and "no evidenced compatible repair or new bounded discriminant" exists.
- The director nx16 arc passed independent equilibrium, constraint and wrench checks yet missed the analytical response by about 5.3% (guide lines 166-169). A solution that satisfies its own equilibrium and constraints but misses an oracle points to discretization or modelling bias, not a solver bug. Recommending "fix the solver" from this evidence would be an error.
- Counterexample to any claim that main is still the tested candidate: three contact commits landed after the handover (888d854, 10d5e19, 9694d54). The recorded source hash at `HANDOVER.md:22` is for the candidate, not HEAD. Every slice below must re-run its own focused checks on HEAD.

**API compatibility facts that constrain every slice.**
- `connection_trace` is set as an instance attribute only when non-default (`mesh_gen.py:155-177`), to keep legacy pickles and V1 checkpoint namespaces unchanged. Do not change that.
- `rotating_eccentricity` rejects numpy bools by strict type (`mesh_gen.py:58-60`, `elements.py:5367-5368`), tested in `test_beam_shell_connection_options.py:68-86`. Keep it.
- `InterpolatedBeamShellMPCElement` lives in `mesh_gen.py:146`, not `elements.py`. The public import path via `anysolver` is what matters; do not move it.
- The checkpoint refusal at line 6116 is asserted in `tests/test_nonlinear_restart_checkpoint.py:646` and `tests/test_standard_edge_beam_shell_nonlinear_contact.py:1072`. Relaxing it would touch contact and is out of scope.

## Recommended slices, in order

**Slice 1. Truthful guide and changelog. No source change.**
- Rewrite `docs/BEAM_SHELL_CONNECTION.md:95-109` to state: default route demonstrated completion to -11/60 m with restart in the registered S355 case; the original -0.20 m target and the analytical accuracy gate remain open; the director route stops at -1/6 m; the three failing tests are the record of that.
- Add the Unreleased changelog entries listed above, one line each, with "no default, tolerance or material change".
- Add a short "Reading a displacement-control result" section: status, stop_reason, `steps[-1].control_value`, the manual continuation route, and that checkpoint restart requires a completed terminal state.
- Minimal test: one cheap elastic contract test in `tests/test_beam_shell_connection_options.py` asserting that a completed displacement-control solve has stop_reason "target_displacement_reached" and `steps[-1].control_value` within tolerance of the target. The existing `test_documented_complete_example_executes` already guards the first code block.
- Done when the test passes on HEAD and the guide contains no claim that the evidence files contradict.

**Slice 2. Stopped-run continuation recipe, documented and tested publicly.**
- No new helper. Document the manual continuation route and its refusal behaviour.
- Minimal test: a public-API test that a stopped-at-limit result can be resumed to a nearer target through the manual route, and that `restart_checkpoint` from the same result raises the documented error. Use a forced stop via a small `max_iterations` on a cheap model, as `test_nonlinear_beam_shell_slice3.py:854` already does with monkeypatching.
- Done when both assertions pass and the existing restart checkpoint tests are untouched.
- Optional, owner decision: add one property `NonlinearStaticResult.final_control_value` returning `steps[-1].control_value` or None. I lean against it. The recipe is two lines and a property is a permanent surface.

**Slice 3. Experimental director trace: status freeze, not expansion.**
- Keep it keyword-only on the constructor. Do not expose it through `MeshConfig`. The guide line 117-118 already says so. Stop further numerical variants, matching the assessment's own stop decision.
- Conditional mechanics work only under this one bounded discriminator: on the existing nx8 30-degree arc, run the same case at a load small enough that rotations are in the linear regime, with `kinematics="linear"` or a single small corotational step, and compare to the same analytical oracle. If the error is already near 5%, the bias is discretization or modelling and mechanics work stops. If it is far smaller, the trace is implicated and a separate, newly authorized task may follow. One run, one case, one comparison, with a fresh explicit time cap. The remaining 2138 s in the old ledger is not authority for this.
- Done when the single number is recorded next to the existing nx8 evidence and the guide gains one sentence stating which branch it fell on.

**Slice 4. One installable bundle.**
- Build wheel and sdist from HEAD after slices 1-2 (and 3 if run). Install in a clean venv, import, run the documented example, run `tests/test_beam_shell_connection_options.py` and `tests/test_director_integrated_trace.py` against the installed package.
- Version is an owner decision. The additions are keyword-only with unchanged defaults, so a patch bump from 0.4.7 is consistent with the changelog style.
- The bundle README or changelog must state that three director continuation tests fail on main as an open gate. Do not exclude or relabel them to make the build look green.
- Done when install, import, example and the two fast modules pass in the clean venv.

## Verification and repair policy

- Per slice: run only the named modules on HEAD, once. `test_beam_shell_connection_options.py` and `test_director_integrated_trace.py` are the fast set. The slice3 continuation and director modules take roughly 8 minutes each per the regression rows and should only be run if a slice touches `nonlinear_static.py` or `mesh_gen.py`; slices 1, 2 and 4 do not.
- The three director failures are expected and do not block any slice.
- Repair is allowed only for a genuine error in new test or doc code. No tolerance edits, no load or mesh sweeps, no retries for luck. A failure in an unchanged module stops the slice and is reported.
- One scoped main commit per slice. No push or release in scope.

## Open decisions for the owner

1. How CI should surface the three known-failing director tests: leave failing and documented (my recommendation), or something else. I do not recommend xfail or deselection.
2. Package version for the bundle.
3. Doc-only recipe versus the single `final_control_value` property.
4. Whether to authorize the slice 3 discriminator run and its time cap, or stop director mechanics outright.
5. Whether the public guide should name -11/60 m as the demonstrated endpoint or only describe it as a revised, case-specific continuation result. It must not be presented as the original -0.20 m target.