# Independent connected code review V1

2026-10-06; supporting non-author OpenAI review. No numerical imports, jobs, polling, product edits or Git actions. This is implementation/evidence review, not scientific qualification or different-family acceptance. The author began repair while this review was active; frozen V1 bindings and evolving source are distinguished below.

## Blocking production finding: Q4 stress-frame mismatch

`_stiffened_shell_b2_reference_buckling.py:298–303` supplies native physical-frame N/M/second moments directly to `element.compute_geometric_stiffness_matrix`. Native recovery uses the Equation-7 frame and declared director polarity (`e4_pl_element.py:3863–3905,6516–6545`). The inherited kernel interprets these components in each Gauss-point xi-tangent frame (`elements.py:2553–2561`). Qualified geometry explicitly returns that inherited frame unchanged (`e4_pl_element.py:3102–3104`), and the qualified geometric wrapper forwards without a stress-frame conversion (`5659–5668`).

The admitted general flat Q4 domain therefore contains wrong prestress directions. For the parallelogram `(0,0),(2,0),(3,1),(1,1)`, each kernel xi tangent is global x, but the Equation-7 first tangent is the normalized sum of normalized diagonals and is tilted. A native uniaxial N11 is interpreted along the wrong tangent. Reversed physical directors also require the corresponding bending sign conversion; the existing pad-only reversal test does not cover shell stress conversion.

Required new-policy repair: let F be the native physical tangent columns, Rt the kernel tangent columns and `s=n_kernel·n_physical=+/-1`. Re-express tensors per point: `Nk=Rt.T F Np F.T Rt`, `Hk=Rt.T F Hp F.T Rt`, `Mk=s*Rt.T F Mp F.T Rt`. Engineering shear/resultant packing must match the tensor convention. Add an independently evaluated physical scalar Green-work oracle on skew/distorted and globally rotated cells, with director/numbering reversal and coupled N/M. Preserve historical policy behavior through an explicit scope decision; this same unresolved frame issue is visible in the previous point route but was not repaired by this reviewer.

Subsequent reserved Root decision: apply this input stress-frame correctness repair to BOTH experimental B2 reference-POINT and new physical-footprint routes, without changing element equations or POINT request/selection meaning. Introduce an explicit frame-covariant Q4 kernel identity; preserve historical raw/source identities and the square default factor. Final transform implementation and skew/distorted/global/director-reversal oracle closure were pending when this report was saved and require a focused source-bound follow-up. This prospective decision resolves repair scope, not verification.

## Frozen V1 failures and returned repairs

- `physical_footprint_capabilities:245` accesses nonexistent `owner.points`; the owner stores `point_ids`. This prevents public new-family capability/buckling/cancellation paths. V1 JUnit confirms the AttributeError. Current service hash differs from V1 after repair; no repaired runtime claim is made here.
- Frozen V1 example/test calls `solve_linear(...,footprint_selection=...)`, while the supported keyword is `selected_footprints` (`panel:1583–1591`). V1 static/workflow failures confirm it; current example/test source has been repaired and no longer matches its V1 hash.
- Frozen `test_full_shell_frozen_green_scalar_second_variation:158` sets `w=-.5*x*y, rx=.5*x, ry=-.5*y`. The compatible shear law (`e4_pl_element.py:2078–2080`) is `w_x+ry, w_y-rx`, giving nonzero shear. The chart helper extracts full physical rotational first work, including this unsupported shear, whereas the scalar oracle includes only N/M. The recorded approximately 0.9795 relative error is not evidence that the admitted zero-Q chart completion is wrong. Use a genuine zero-Q fixture and assert the recovered forbidden resultants before comparing; keep the original tolerance and failed evidence.

An additional static-domain/provenance mismatch was returned: the constructor initially allowed POINT plus new pad, but `panel:1783–1785` publishes full multipliers/gaps and only pad row provenance. Root adopted an explicit NEW-family constructor coexistence refusal, preserving old POINT/old-pad behavior. Its implementation/refusal coverage was pending at this review binding.

## Connected implementation assessment

The new module's C and symmetric chart Hessians implement the reviewed five-row law correctly. Complete patch membership is now mandatory. Read-only byte-owned directors/bases/C/H prevent ordinary mutation; old topology/overlap audit is reused, while only its six-row kinematics are replaced. The selected wrench uses actual `-C.T lambda`, five-row slices, physical director couples, compensated arm differences and `fsum` moments. Static failure catches recovery representability exceptions.

Panel assembly carries `row_count` and both shell/beam incidence matrices, retaining six-row/I defaults for historical footprints (`971–982`). Compatibility uses three length rows and two director rows (`1220–1224`). New static result exposes all pad multipliers/gaps and row provenance; the separate facade definition passes no POINTs. Modes and batches refuse before legacy selection, and typed new buckling requests/results distinguish the new policy. Existing shell/member K and full sparse KKT/descriptor coordinates remain; production spectral assembly is sparse.

`q4_exp_director_chart_correction` uses `stationary_coupling @ stationary_parameters`, the native physical first-work covector, whose physical core excludes PL/drilling fields and sixth drilling slot. Its global m and beta Hessian contraction have the correct sign and director-reversal invariance. The service invokes the helper once, after exact zero-Q admission, and adds pad multiplier curvature once using the actual static full multiplier vector (`304–320`). The nodal-Exp-then-interpolation scalar oracle has the correct intended field. The frame defect above remains separate from this chart completion.

## Controls still required

Complete repaired public path and failed-preload/closed-owner/cancellation checks; actual old six-row static regression; nonzero pad-director reaction with physical shell-plus-pad chart cancellation; distorted/global/reversal shell scalar oracle; severe representable datum/wrench cancellation and true nonrepresentability refusal. The present finite-work tests exercise one combined direction rather than all mixed blocks, and the dense QZ check compares the public pair with a pencil built from the production G; it verifies solver integration, not independent mechanics. External/refinement/spectral completeness, broader footprint/line/S3 obligations, installed qualification and different-family acceptance remain open. No passing test by this reviewer is claimed.

## Evidence and source bindings

Actual saved V1 evidence: `junit-v1.xml` reports **13 tests, 7 failures, 0 errors, 6.175 s**, hence 6 passes. `resource-receipt-v1.json` records child PID 128152, exit 1, 10.2193329 s supervised, sampled peak RSS 233455616 bytes, one numerical job, 600 s / 2 GiB limit. Effective pre/post runtime records confirm source ANYsolver, pinned CI dependency paths, affinity `[0]`, JIT disabled, NumPy/SciPy/Numba versions recorded, BLAS/OpenMP pools and post Numba thread count one. These are inspected author-run artifacts, not reviewer execution or peak-memory qualification.

Frozen V1 SHA256 from effective-runtime records:

- physical module `9ad5d94170317ef31a0b7c77afe9dad33800d85ebaf42e030999126d6af206d6`
- buckling service `0814e238225ca3d75bf4fc70c264b107c9e33f20e7279ccac7544b8b1eccd8a3`
- panel `587dce7b688deb6dfb190d1e40c268e71cd83897638fc341de772c3b51198683`
- facade `d34b1ae2ba017c9293b47a1916c887b26fd3ea6919b2541ca58967feda803433`
- new tests `beef732833b3a483384b5b4c07aac3a0279004de681e651ad53148c059c1a2a9`
- new example `bbbf640fa902cc0e8de8180d9806cf6de45964f4d660b52ba554c85daf4c455e`

At source comparison the physical module/panel/facade matched V1; repaired service was `d3ab43784e594603dcf1cf6ffecf26f3f3d55befcf821ba30890eb72a39a99f7`, tests `6206508874d831261f18c385235bbcb6e4a58a756c9640722dbc13d7c7006cd0`, example `084dec8511dde840c0cdae3efda20cc27682565b9458785e5dd9d1aaf61d809f`. Later author changes/results are not covered by these bindings. E4-PL and inherited shell hashes are recorded in the companion contract review. No new-family documentation appeared in the scoped reference-case search at review time; final contract/example documentation remains a handoff obligation.
