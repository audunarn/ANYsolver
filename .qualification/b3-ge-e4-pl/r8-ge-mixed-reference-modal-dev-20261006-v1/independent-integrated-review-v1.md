# Independent integrated review, frozen source V1

Outcome: no blocking product-source correctness defect found in the narrow adopted experimental route. Verification remains incomplete: the actual V1 suite reports 73 passed and 3 failed out of 76. No numerical imports, tests or jobs were run by this reviewer. No product edits. F03 remains UNCONSUMED. This is development review, not scientific qualification, acceptance, installed verification or different-model-family independence.

Reviewed scope: new physical S3/native mass modules; scoped diff against supplied HEAD543ee80d for modal owner, facade and dispatch; actual new tests/example/document; V1 effective runtime, JUnit/output/resource receipt and source snapshot. Product/source judgments refer to preserved `source-snapshot-v1` bindings below. The author owns repairs. Earlier mass assessment and root's explicit adoption of the V2D LINEAR kinetic approximation remain governing.

## Actionable verification findings

1. `tests/test_stiffened_shell_ge_mixed_reference_modal.py:99`, `test_independent_curved_centered_lift_kinetic_work`: identity nodal triads cannot describe the chosen curved quadratic reference `(0,0,0),(.5,.2,.1),(1,0,0)`. `CenteredCurvedBeam3ReferenceGeometry._validate_frames` requires each first triad axis to equal the oriented curve tangent at xi=-1,0,1. V1 fails at construction, so it supplies no evidence for curved native lift work. Repair by constructing proper tangent-aligned SO(3) triads without changing geometry/physics. Preserve independently reconstructed quadratic shape/offset/Jacobian and cross-product velocity calculation. A common rigid-field curve-position control would strengthen the nonrigid kinetic-work check.

2. `tests/test_stiffened_shell_ge_mixed_reference_modal.py:59–63`, `test_independent_dense_qz_on_actual_full_mixed_pencil`: V1 calls dense QZ on dimensional unscaled A/B and compares eigenvalues at frozen rtol=1e-8. S3/POINT fails at maximum relative difference 2.59771267e-8; mixed/BL5 at 1.65351161e-5. The test does preserve the full singular pencil, but supplies no mapped QZ eigenvector residual or conditioning diagnosis. Thus it cannot discriminate sparse-solver error from dimensional-QZ conditioning. Required repair: finite nonsingular congruence of the FULL pencil, preserve all primal/resultant/trace/multiplier dimensions and singular mass, map QZ vectors back, and verify original physical/constraint residuals. Retain the original tolerance and failed V1 evidence. No condensed/SPD surrogate, pair filtering to force agreement or tolerance relaxation. Source inspection cannot decide numerical agreement; await actual repaired check output.

V1 failure evidence: `stdout-v1.log`, `junit-v1.xml`, `resource-receipt-v1.json`. These are real unresolved verification gates, not evidence that a physical family is unstable. Passing development tests do not establish external/refinement 2% acceptance.

## Product/source assessment

`_stiffened_shell_physical_s3_mass.physical_mass` implements the adopted global `[v,omega]` linear barycentric law exactly in source: positive geometric A, G=A/12*(ones+I), translation rho h I and rotation rho h³/12 times cross(n).T cross(n). It checks density/thickness, shape, finite coplanarity/unit normal, positive area and lost/overflowed inertia. Normal-spin zero, director reversal and node-block permutations follow that law. Owner admission remains globally XY-flat n=z; the helper's tilted covariance test does not widen owner admission. This is explicitly approximate V2D kinetic interpolation, not full MIN3 reconstructed-field mass or legacy S3 mass. The separate physical-bubble family is not admitted.

`_stiffened_shell_ge_mixed_modal_mass.native_physical_mass` is the exact kinetic half of the existing centered order24 evaluator: explicit inertia Cholesky; reference frame, Jacobian and half-cell lift; velocity nodal translations `(1-t),t`; cell rotational lift `-F.T skew(offset)` and angular velocity `F.T`. It needs no fabricated elastic section or constitutive tangent. `_assemble_mass` runs physical spatial realizability validation before calling it and scatters `slots[:24]`; resultants18 and nodal rotation traces remain zero. The original generalized evaluator remains on the legacy request path. Existing tests include exact equality with its factors and direct straight kinetic work; curved coverage is currently blocked by finding1.

`_stiffened_shell_ge_reference_modal._admit` uses exact typed mixed-request dispatch and refuses accepted/nonvirgin state, material BL5, shell J2, footprints and curved shell references. S3 direct18 formulation identity is checked. BL5 topology linking is explicitly separate from six-pose constraint regularity. The owner retains its actual compiled C and original `_unsupported_modes` check; `_assemble_mass` adds no inertia to constraints, retained resultants or traces. It publishes byte-backed immutable sparse arrays only after all assembly/representability checks and `mass_publish` cancellation safe point; mixed and legacy caches and mass policy digests are distinct.

The existing sparse full indefinite descriptor route is reused. It retains `[K C.T; C 0]` and singular `[M 0;0 0]`, general sparse factorization and original equation/constraint/physical residual checks; no new static/Guyan elimination, mass floor or tangent averaging appears. Native inertial packing is unchanged. The new free-boundary constructor calls mixed admission explicitly; a legacy request on this boundary fails with `mixed free-free boundary requires GEMixedReferenceModesRequest`. Old request/result/mass defaults, old Q4/generalized/POINT boundary and the legacy mass factor route are retained in the scoped diff.

## Controls actually present and remaining limitations

V1 tests contain actual public supported Q4/S3/mixed, generalized/fibre/mixed-beam and POINT/BL5 combinations; physical normalization, massless rows and immutable separate cache checks; new free-boundary six rigid fields, legacy request refusal and static-solve exclusion; cancellation at start, shell/beam mass, mass publication, iteration and final publication; malformed controls and nonvirgin refusal. The genuine single-p0 BL5 negative is `test_actual_single_p0_bl5_support_retains_existing_mechanism_refusal` at line161: an actual BL5 line is rebuilt with multiplier_span=4, compiled through the public factory, then admission/operation refuse the existing free native rigid mode. This is separate from the injected diagnostic-message control at line141. It preserves the real structural refusal rather than merely testing a patched string.

S3 tests independently integrate barycentric/thickness physical velocities, check constant-field totals, rank15/exact z-spin kernel, symmetry, node permutation/director reversal, tilted helper covariance and nonrepresentable input. They validate the declared interpolation; they do not establish enriched MIN3 kinetics, mesh convergence or final physical spectral truth. The planned external/refinement criterion and any required different-family independence remain open. Mixed BL5 connectivity does not certify complete kernel absence. Nearest-shift pairs do not prove complete lowest spectra. Source-level review plus same-family independent author is not a substitute for those gates.

Documentation names the linear nodal director approximation, midplane/homogeneous assumptions, excluded bubble family and open final 2% convergence gate. The example uses public factory/request/operation and returns explicit nonqualified policies. No new release/default claim was found.

## Runtime evidence and identity

`effective-runtime-v1.json` binds imports to exact Python3.14/NumPy2.5.3/SciPy1.18.1/Numba0.68.0/llvmlite0.50.0 isolated CI site and this repository source. It records affinity `[0]`, both discovered OpenBLAS pools at one thread, Numba threads1, JIT disabled and no forced backend. Entry code asserts those effective settings before pytest. Resource receipt records one child job, terminal failed status exit1, sampled tree RSS232493056 bytes, 13.0100066s supervision against 600s/2147483648-byte bounds. JUnit records 76 tests, failures3, errors0, 8.474s. Sampled RSS is not peak-memory qualification. This reviewer inspected evidence and started no job.

| Frozen V1 source | SHA256 |
|---|---|
| modal module | A4018AE50F07CCBC90283461B7C7659E0003ACA613D0255B4BCB642179FF90EC |
| owner module | C9477655CD4FB5A6339D8EA6BD2CC772DFC81A5DFE32B4E8FFF7E5258DF63D8B |
| facade | D2E402E0D34466EFEC5558690B62160AD1E8F34A37B3AA22932FBF058E88ADC1 |
| physical Q4 mass | 66B174BADE92F322DD87CB194292AAA3179A9A59D2E217C2D2A77DC04DF7B2F5 |
| physical S3 mass | 83635C33D1A43AE90425B24F825A610CA87F9CDD62B0D7516D02A1A3C921DF15 |
| native mixed kinetic-only mass | D57A1C599E55E0BD66E693386FCCD0EEE6A19DC3EA8EFE10CB2574CE7AC91F72 |
| new modal tests | 121280652CB998040809B6F14B58F69E707585EB8D957FA01FF82AD8D6EAE3E5 |
| new S3 mass tests | 0F44DA4384B430DB402CD496DCDDEB5906971E9CAD1E625031EC4F62FD78B9C0 |
| new example | 5EDBE27A249DFAB6C9E7643847271276A283E37177394A4FE5065C290D87E437 |

Handoff: source assessment complete for frozen V1; implemented candidate with unresolved verification. Same author repairs two test mechanisms; root independently judges repaired original-pencil residual evidence and convergence/independence boundaries. No product fix inferred or authorized by this Read assessment.
