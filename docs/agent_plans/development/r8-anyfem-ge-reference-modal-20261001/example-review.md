# Independent modal consumer example supplement — 2026-10-01

No blocking finding. This closes only the optional example item in `r8-ge-modal-consumer-independent-review-v1.md` (SHA256 `4331dc578286f3326654d0c9614ded69b9dc7b810af57d34f81ec62a83487cd4`), whose bytes remain unchanged. Review used source, saved JSON/logs/identities and hashes only; no imports, assembly, numerical jobs, source edits or Git operations.

Reviewed `C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/examples/experimental_ge_reference_modes.py`, SHA256 `de55e13fdb1e7fb941a8fd786264ce9b136d346980e8353392d0f7b4d720c86e`. The three previously reviewed source/test hashes remain unchanged. The example uses public constructors, explicit native generalized section/inertia, Q4 shell density/thickness, two six-pose points, typed `GEReferenceModesRequest(count=2, shift_hz=1.)`, the strict modal consumer, ordinary Project save/reopen and `solve_point_panel`. Free-free is an explicit modal-only boundary policy with empty supports; `--supported` instead declares shell root supports. No finite state, staged action or inferred inertia is introduced.

The mass tensor independently prescribes `m=rho*area`, first moment through the skew centroid arm, and section-axis inertia `rho*diag(Iy+Iz,Iy,Iz)-m*skew(center)^2`; it is not inferred from the stiffness matrix. This is a prescribed example input, not an independent physical frequency reference or planar-section qualification. Output retains boundary/numerical policy, model identity, typed request, factor count and the solver's completeness disclaimer. Free-free rigid fields are counted separately from the requested flexible frequencies. Supported output rigid count0 reflects its result representation, not a general nullity proof.

Actual terminal evidence:

| Artifact | Result | Requested flexible Hz | Rigid count | Elapsed / sampled tree RSS |
| --- | --- | --- | --- | --- |
| `TEMP/r8-ge-modal-consumer-example-free-v2` | completed, factor1, exit0 | 55.03428970322184;159.8266970706792 | 6 | 2.085050499998033s /162213888B |
| `TEMP/r8-ge-modal-consumer-example-supported-v1` | completed, factor1, exit0 | 31.160280574040108;160.1090561857179 | 0 | 2.090730900003109s /162267136B |

Both use unchanged ANYfem wheel `57ee44eff01a3453082f1e1a9c528acf9aa2ac35eb2f0a1959d3428b764e4b2c` and ANYsolver `4ddde5790ce72697d20425186473d1d5066f84156287d9d9083ea1f059643ccd`, with391+98 modules. The wrapper verifies wheel/site hashes against the already independently checked manifest. Independently checked saved example hashes and all275 observed imports per route: none offsite. Effective loaded NumPy/SciPy OpenBLAS and OpenMP pools are1; Numba1 and JIT disabled are recorded and checked by the wrapper. Both runs stayed within600s/8GiB. Resource figures are bounded observations, not performance claims.

Preserved initial `TEMP/r8-ge-modal-consumer-example-free-v1` is **failed**, exit1, after the example had completed and returned JSON: root wrapper incorrectly asserted three frequencies although the public example declares two. Independently comparing retained old/current wrapper shows the sole changed line is `len(frequencies_hz)==3` to `len(frequencies_hz)==request['count']`; corrected wrapper SHA256 `d24371934c6aa24b1c2aef44fffdab912cbcd31f5191fa03c0e8450d7abb0d62`. All three saved example sources have the identical hash above. No product, example input, tolerance or physical criterion changed. The V1 runner/source/log and repair JSON remain evidence; it is not an all-green first run or a product solve failure.

The installed example now demonstrates both intended public Project routes. Existing solver/consumer review limits remain: no complete-spectrum/exactly-six-nullity/unexcited-mechanism absence claim, externally validated engineering frequencies, full F07 or aggregate qualification. No further change or execution is requested by this supplement.
