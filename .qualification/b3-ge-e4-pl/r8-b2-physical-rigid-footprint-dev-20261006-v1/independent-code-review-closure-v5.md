# Independent code-review closure V5

2026-10-06. Focused non-author supporting OpenAI Read closure of the frozen V5 candidate. No reviewer numerical imports/jobs/polling, product edits, Git actions or workers. The V1 review and failed evidence remain intact. Scientific acceptance, different-family assessment, installed qualification and complete F12/B14 remain open.

## Result

The V5 source resolves the Q4 physical-resultant frame defect identified in V1. The earlier nonexistent owner attribute, public keyword/fixture defects and mixed POINT/new-pad provenance admission are repaired. No additional blocking code error was discovered within this focused closure. This is a conclusion about the inspected bounded implementation and development evidence, not a blanket physical-accuracy or qualification claim.

## Frame and second-variation closure

`_stiffened_shell_b2_physical_rigid_footprint.py:q4_kernel_frame_resultants:200–214` obtains the native physical frame through `_physical_director_context(native["frame"])[0]`. This is the actual resultants frame: the native Equation-7 tangent frame with declared director parity, rather than the inherited Gauss-point xi frame. At each point it forms `R=kernel_tangents.T @ physical_tangents` and checks parallel/antiparallel normals. Packed membrane tensor N maps as `R N R.T`; bending tensor M maps as `(n_kernel·n_physical) R M R.T`. The shear component is packed as the off-diagonal physical tensor component. The homogeneous second moment is formed from mapped N times `h^2/12`, so it is director-even. These transformations are correct under proper global rotation and either physical director polarity.

The shared experimental B2 assembly invokes this conversion for both Q4 POINT and new-footprint paths (`reference_buckling:298–305`), without changing the element kernel. Its explicit identity is `Q4_QUALIFIED_REFERENCE_RECOVERED_N_M_HOMOGENEOUS_SECOND_MOMENT_PHYSICAL_TO_GP_FRAME_V2_DEV`. Historical request/profile/selection meaning is retained; the correction's scope was expressly adopted by Root. The square default has the same frame and remains unchanged numerically.

The new-family Exp-director first-work correction remains separate (`306–309`) and is added once. Native stationary first-work extraction excludes numerical PL/drilling contributions. The numbered-normal beta Hessian is director-even, and the covector is rotated to global, so native/physical normal reversal does not require a second sign on that correction. Five-row pad multiplier curvature is added once from the actual full static multiplier slices (`316–322`). Old POINT continuation does not receive this new shell chart term. Production assembly remains sparse and preserves all physical/algebraic KKT coordinates.

## Meaning of the independent controls

The distorted/skew scalar test (`tests:239–281`) uses a non-affine flat quadrilateral, a proper global rotation and both director polarities. It computes physical-coordinate shape gradients, N/M stress tensors and thickness Green work directly, rotating each nodal director before interpolation. It therefore discriminates the previous wrong-frame prestress and M-parity defect. Its chart covector is independently integrated from physical M. The two-point thickness rule integrates the prescribed quadratic thickness contribution.

The actual native square test now asserts recovered Q equals zero before comparing complete stress work. The nonzero director-multiplier test (`199–226`) uses native physical moments and solves their local interface virtual-work balance, then checks that shell chart and pad mixed spin/tilt work cancel. It explicitly shows finite work if the chart is omitted or doubled. This is a meaningful local balance construction; it is not a full public bending-preload equilibrium solve.

The public full-pencil case retains multiplier coordinates and compares the sparse spectral result with dense QZ, while original physical residual bounds remain `1e-8/1e-9`. It establishes solver integration for that specimen; its pencil is assembled from production G and does not independently establish continuum mechanics. The original square POINT workflow is also executed and checked against `24.60872920125391` with `rtol=1e-10`.

## Actual evidence inspected

`junit-v5.xml`: **8 cases, 0 failures, 0 errors, 0 skips, 11.648 s**. Cases are the new full dense pencil and public workflow, complete square shell Green scalar, nonzero director-multiplier cancellation, rotated/distorted scalar for both polarities, square POINT factor preservation and original POINT public workflow.

`resource-receipt-v5.json`: child PID 121388, exit 0, supervised 15.28301619994454 s, sampled peak RSS 221806592 bytes, one numerical job, limits 600 s / 2 GiB. Pre/post runtime confirms Python `C:/Python/Python314/python.exe`, affinity `[0]`, pinned CI dependencies, JIT disabled, NumPy/SciPy/Numba/llvmlite recorded versions, Numba threads one and all observed BLAS/OpenMP pools one. This is author-run evidence inspected by the reviewer; sampled RSS is not peak-memory qualification.

`example-workflow-v5.json` records static `completed`, spectral `ok`, factor `0.16324601652203263`, no failure and production_qualified false. V1 (13 cases/7 failures), V2 (13/3 failures), V3 (three repaired passes) and V4 (four passes) remain preserved. V4 includes actual old six-row static full-KKT controls with both affine variants.

Impact reuse is bounded to unchanged dependencies: normalized source-block hashes for `PhysicalFootprintNode`, `_node`, `compile_physical_footprints` and `selected_wrenches` are identical in V2 and V5 snapshots. Their C/H/topology/wrench controls therefore retain applicability. V5 re-exercises changed shell frame/chart assembly and public spectral workflows. This is not a fresh aggregate twenty-case campaign or twenty scientific acceptances.

## Frozen source binding

All nine listed files in `source-snapshot-v5` and the worktree matched `effective-runtime-v5.json` SHA256 at inspection. Principal bindings:

- physical footprint module: `873f5281b1c87d3a8e8e6b2309db85d2c031c06d9e1cfe42c4795cc7fcccc02c`
- buckling service: `133b7b2ddb23a720a39ef496cce7a1527f5523786d852a2289439af559c98094`
- panel: `137bcc6e8989dd333168b2fda3d63037021e0ec9662271d5e3a244ff69364186`
- facade: `d34b1ae2ba017c9293b47a1916c887b26fd3ea6919b2541ca58967feda803433`
- new tests: `837f1be4af9983bdb0c5c4691973e4a29460d4b33609378ab58678c3105bed18`
- new example: `084dec8511dde840c0cdae3efda20cc27682565b9458785e5dd9d1aaf61d809f`

The original POINT example/test and old footprint test hashes are preserved in the V5 runtime record. The new reference-case document now states the nodal-Exp interpolation, physical first-work correction, V2 frame identity, serial failure history and development-only scope.

## Remaining controls and boundaries

Severe representable wrench/constraint cancellation and reference-datum controls were not executed for this new family. Full public rotated/unit/member-reversal covariance remains beyond the local operator tests, as do full public nonzero-director bending preload, post-assembly cancellation/closed-owner/failure-path breadth, installed artifact verification, external transfer/reference comparison, refinement/thickness/spectral completeness and drilling sensitivity. Broader S3/shear/line/interior/distributing/mixed attachment, prescribed/dead-couple, nonlinear and physical-footprint mass/modes contracts remain unavailable or open. Existing owned compensated arithmetic is retained; no accuracy outside measured controls is inferred from its presence. Supporting independent OpenAI review does not satisfy the mandatory different-family requirement.
