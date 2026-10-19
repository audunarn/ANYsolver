# Independent candidate delta review — 2026-10-18

Read-only non-author review. No imports, solves, pytest, workers, or product/test writes were performed. This supplements `supervisor_integrated_candidate_review.md` and `supervisor_globalization_review.md`; unchanged mechanics derivations are not repeated. Source identity below was captured after the zero-span assertion repair and before the owner's next product repair.

## Result

The tightened intrinsic-mean helper closes the earlier uniqueness/chart findings on its expressly supported domain. The current continuation tests close the inverse-identity oracle, shallow preimage, nested-sequence comparator and split-tail mistakes. No new error was found in the admitted mean differential or connected map algebra. Final continuation acceptance remains unmet. The current source has a concrete missing trial-domain recovery boundary, and the history tests retain the coverage limitations below.

## Concrete current source issue: inadmissible trial aborts continuation

`src/anysolver/nonlinear_static.py:4220` calls `full_u(q_trial)` outside a recoverable-trial exception boundary. A chart/convexity refusal from the intrinsic mean therefore exits the solve rather than rejecting the trial. The corresponding force line-search boundary is `:7287`, before its constitutive-only try block. This is distinct from refusing an invalid initial/restart state. The parent reports that the current interpolated full-target attempt reached the DC path and raised the principal-chart refusal here; this reviewer did not execute it.

Recommended bounded repair: introduce a specific internal state-dependent rotation-domain exception, optionally a `ValueError` subclass to preserve public admission behavior. Use it for the mean's state-dependent chart/relative-angle/convex-domain refusals. Keep malformed weights, invalid descriptors and unrelated `ValueError`s outside this recovery category. Validate initial/restart states normally. Catch the specific exception only at candidate evaluation boundaries, discard pending candidate state, retain the starting q/lambda/committed histories, and reduce the line-search factor. Do not retain the existing full-step fallback when that step is inadmissible. If no admissible improving trial exists, emit a classified failure and use the existing rollback path. The subdivision predicate at `:4339` currently permits only `maximum_iterations_reached`; explicitly decide whether the new classified trial failure permits bounded subdivision. Preserve both positive-span and cutback-count bounds.

A discriminating regression should make the full trial leave the admitted domain while a smaller trial remains admissible; assert backtracking and unchanged committed/input/snapshot histories. A second case with every trial refused should return bounded failure after rollback. Inject an unrelated `ValueError` and ensure it still propagates. These checks should inspect actual q/lambda/state, rather than exception text alone. Apply the same exception semantics to force-control candidate mapping if that path is repaired in this slice.

## Mean-domain and differential closure

`corotational.py:1245–1296` normalizes admitted near-unit weights, checks every multi-master input chart before the identical shortcut, and checks the returned principal chart. The direct one-master branch retains its existing coordinates. Two masters use `R0 Exp(w1 Log(R0.T R1))` with relative angle strictly below pi minus the chart margin. Its stated relative logs `-w1 psi` and `(1-w1) psi` are exact. Larger means require every master and the returned mean in an open pi/4 ball about the first master. This is a conservative convex domain; it excludes the earlier antipodal/ambiguous construction and gives a nonsingular local mean differential. The anchor seed transforms objectively. The existing implicit derivative `Gi = Jl(theta_m)^-1 Rm B^-1 wi Ai Rm.T Jl(theta_i)` remains correct on the smooth admitted branch.

The independent SciPy shortest-geodesic reference and central-difference test at `tests/test_nonlinear_beam_shell_slice3.py:808` checks the two-master value, normalized weights and all derivative blocks. The domain cases at `:827` distinguish antipodal relative rotations, nonprincipal identical inputs, the larger-mean convex restriction and negative weights. Successful nonidentical three/four-master mean covariance/differentiation remains unmeasured by these new focused tests; do not extend measured claims from the two-master case. The zero-span test now uses `not result.steps` at `:867`; its earlier list/tuple mismatch is closed in the captured identity.

## Continuation/history oracle closure and remaining coverage

`test_nonlinear_beam_shell_slice3_continuation.py:503–526` now retains independent deep preimages, evaluates every accepted snapshot at its achieved lambda, and invokes the actual affine constraint summary after inverse mapping. It is no longer the tautological apply/inverse identity. Per-snapshot physical wrench balance covers both routes. Tail material comparisons at `:691` exclude the resume input split state, while the half-prefix comparisons include it.

The recursive comparator at `:315–356` covers all physical fields currently emitted by the fixture's shell and beam implementations (`elements.py:3127–3143`, `:4394–4400`), including complete plastic-strain/alpha and layer/fiber strain/stress arrays, at the existing rtol 1e-6 and atol 1e-9. It handles nested lists/tuples. However, equal key sets do not require the expected physical element IDs or required fields: identical omissions in full and resumed results still pass, and a scalar alpha maximum proves history exists somewhere only. Add a fixture schema assertion for expected shell/beam IDs, required nonempty physical fields and expected array shapes before comparison. This is a test-observability gap, not a demonstrated product history loss.

The equilibrium helper makes a second private state copy at `:421` before assembly `:424`. Outer comparisons prove stored snapshots and supplied objects were preserved; they do not prove the private mapping actually passed to assembly remained unchanged. If reconstruction immutability is part of the gate, retain/check that mapping's own deep preimage inside the helper, as assessment_support already does. Cancellation currently checks exact caller-history preservation and reuse after two accepted events (`:736–789`), but does not capture accepted snapshots before cancellation and compare their later histories. This remains a cancellation-specific snapshot coverage gap, not a confirmed mutation.

## Analytical and mesh tools

Rechecked A1–A4 closure: physical root-row reaction reconstruction, achieved-lambda terminal moment, duplicate input refusal, exact refinement prefix and prospective extension eligibility remain present. Summaries now additionally require matching relevant product/oracle hashes through `assessment_support.identities_match`. No new analytical formula or gate-summary error was found by this static delta review. Numerical tip/rotation/refinement gates remain unmeasured here; old or mixed-identity results cannot establish current acceptance.

## Captured SHA256 identities

| File | SHA256 |
|---|---|
| src/anysolver/corotational.py | 74CAE9C362EC73A021FA4AE316031D73655AA666027739B7A1D1488A692CC0B5 |
| src/anysolver/nonlinear_static.py | D9968DBCD7CB2812AA684EDC0D730E957823150AFB6AF94CB8E18BA5330710C8 |
| src/anysolver/nonlinear_performance.py | D22FD0F3C29E2E25AC22F306F2F70ACB64A30D0ADB856B30667B6BACD1F7624A |
| src/anysolver/elements.py | B3AC0D22E053AA670277C173AA3417F576D161AD132F1CA44C0ADDAA3BE28A08 |
| src/anysolver/mesh_gen.py | 2D023D1758A4785A3F812A051BD74B942432919F9273AD8C966B7A3D3A2A0485 |
| tests/test_nonlinear_beam_shell_coupling.py | ACD63DFF89934D01E0DD7DF66A89FF01468E94D14C5699D0725CC3BCAF27CB66 |
| tests/test_nonlinear_beam_shell_slice3.py | B3AEB2EF80B74C2239B97D8722D91168E0BAF57F92A71250C472E96875DF1399 |
| tests/test_nonlinear_beam_shell_slice3_continuation.py | 36FB305AED378EE69088B61B6E40F4C558B5C8999D0E5582F14703B30535C3D9 |
| diagnostics/assessment_support.py | B19C50B1C624AB86EF3E2DD3CA4BB96AEAD3171BBC38CC714E2F305DB96AF6ED |
| diagnostics/arc_reference.py | B9D241FD547DCC9F53ED1D1911C22A81F4AFC62F10B1442820E83A55329059DE |
| diagnostics/mesh_study.py | 62D0F167081BB21C5592AC6B95FA72A29C27798E7976A9A6BAA02469959E0BF9 |

Parent-supplied evidence, not reviewer execution: `evidence/supervisor-domain-dc-full-1` reportedly recorded five passing mean tests, the now-fixed zero-span assertion failure, direct full-target stopped_at_limit and interpolated full-target chart exception; 154.327 seconds process wall reported by parent. The subsequent repair and all final scientific gates require their own source identities and measured evidence. This review establishes neither full-target success nor final acceptance.
