# S4 nullspace-semantics proof plan

## Authority and proof-only boundary

The ANY ecosystem boss accepted the quarantined literal-formulation commit
`f5cf8d925f47c816f5fe4857a83c5e38fd599570` and authorized this new
proof-only stage under standing user delegation. This stage must determine
what the corrected published element's nullspace means; it must not repair,
constrain, stabilize, activate, integrate, or relax anything.

The proof must partition each investigated nullspace in the registered
dimensionless metric as

```text
N_B = ker(B_w),
G = N_B intersect ker(H_w),
Pi_P = Pi_N_B - Pi_G.
```

`Pi_P` is the registered-metric orthogonal representative of the invariant
positive-mass quotient `N_B/G`; it is not an undefined set difference and is
not, by itself, a non-rigid-mechanism projector. `B_w` and
`H_w` are defined exactly below from the corrected strain and displacement /
inertia interpolations on the same positive quadrature domain. A constant
drill vector may be gauge-like only if the deterministic algebra proves it is
in both kernels. A checkerboard or other positive-mass zero-stiffness vector
must never be called or constrained as gauge without a separate physical
derivation and later authority.

Options 1, 2A, 2B, and 3 remain reserved until the proof packet receives
independent acceptance. No penalty, hourglass term, stabilization, tuned or
invented stiffness, magic rank correction, rank-gate relaxation, constraint,
gauge application, shared-path edit, production selection, integration,
handoff/native-hybrid consumption, or sibling-repository write is authorized.

## Repository, branch, and immutable baseline

- Repository: `C:\Github\ANYsolver`
- Worktree: `C:\Github\ANYsolver\.perf2-worktrees\s4-nullspace-semantics`
- Branch: `codex/s4-nullspace-semantics`
- Base/HEAD before proof edits:
  `f5cf8d925f47c816f5fe4857a83c5e38fd599570`
- Base parent: `cd4831c6352844be7853f2764ada4f72662ab15f`
- Literal correction completion packet SHA-256:
  `F6715265F9B82756A883AF120083AEA70DF4D00F6957F044F6F3E33EAB059521`
- Post-correction JSON/output SHA-256:
  `09DC95B663F83457C83457973E8276C8C2462068CA90275C1E8907CE7972AAF6`
  and `3C131E9E08ABCF256C54AD0908E432E2380632BB461D144C32246746FA2CD9CA`
- Frozen 113-claim contract SHA-256:
  `1591906DB90B83A7018E51D1C6CF35A545BCE28787ED3108713CDEECC51103F1`
- Unchanged rank gate SHA-256:
  `D77AEC9AB491D86D1EDAF747ABADD8ADA84B8A469EA7A2186C27AA92A2284E2A`

Canonical future file-I/O repository spelling is `C:\Github\ANYfileIO`.
Historical evidence that captured the earlier void-ANYio path remains
unchanged and is not rewritten by this stage.

## Exact ownership

Vidar, the sole proof editor, owns only these new files:

- `docs/S4_NULLSPACE_SEMANTICS_PROOF.md`
- `docs/reference_cases/s4_nullspace_semantics_oracle.py`
- `docs/reference_cases/s4_nullspace_semantics_cases.json`
- `tests/test_s4_nullspace_semantics_proof.py`

The coordinator owns only the final new completion files after proof freeze:

- `docs/S4_NULLSPACE_SEMANTICS_COMPLETION_PACKET.md`
- `docs/reference_cases/s4_nullspace_semantics_output.txt`

Heimdall is read-only and owns no path. Every existing source, test, contract,
plan, evidence, package, assembly, activity, handoff, and sibling file is
read-only. Any ownership change requires a registered plan amendment before
the first overlapping edit.

## Frozen dimensionless metric and row scaling

All proof algebra uses IEEE-754 binary64. No scale may be selected from an
observed singular spectrum.

For one element, let `ell` be the maximum Euclidean distance between any two
of its four nodes. For an assembled retained topology, let `ell` be the
maximum of that same element-local diameter over retained elements; separation
between disconnected components does not change it. Zero or nonfinite `ell`
is invalid. Define physical and dimensionless DOFs by

```text
q_phys = S_q q_hat,
S_q = blockdiag(ell,ell,ell,1,1,1) per global node.
```

The registered DOF metric is ordinary Euclidean inner product in `q_hat`.
Equivalently, its physical-coordinate metric is
`S_q^(-T) S_q^(-1)`. This freezes the relative translation/rotation units.

At each retained volume quadrature station `a`, use the corrected local
engineering strain operator `B_a` in order
`[eps11,eps22,gamma12,gamma13,gamma23]`, positive signed volume weight `w_a`,
strictly positive proof density `rho_a`, stiffness activity `alpha_a`, and mass
activity `beta_a`. Cases freeze `rho_a=1` unless explicitly stated. Retained
rows require `0 < alpha_a <= 1` and `0 < beta_a <= 1`; deletion removes the
element and all its rows/connectivity. `alpha=0` or `beta=0` is not silently
coerced to deletion. Softening fixtures use the exact JSON value of `alpha`
and keep `beta=1` unless the JSON explicitly declares another abstract mass
rule.

Define

```text
W_B = sum_a alpha_a w_a,
W_H = sum_a rho_a beta_a w_a,
B_w = vertical_stack_a sqrt(alpha_a w_a/W_B) B_a S_q,
H_w = vertical_stack_a sqrt(rho_a beta_a w_a/W_H) H_a S_q / ell.
```

All weights and both totals must be finite and strictly positive. These row
weights are dimensionless and positive, so they do not invent a kernel.
Moreover,

```text
||H_w q_hat||^2
 = q_phys^T M q_phys / (ell^2 W_H),
M = sum_a rho_a beta_a w_a H_a^T H_a,
```

which makes `ker(H_w)=ker(M)` explicit for the frozen positive weights. Mass
energy remains corroborating evidence; this equality is the gauge definition.

Constraint/coupling rows supplied as `C_phys q_phys=d_phys` are transformed as
`C_raw=C_phys S_q`, `d_raw=d_phys`. For each nonzero row, divide both the row
and its matching RHS by `||C_raw[row]||_2` to obtain `C_hat,d_hat`; this is the
only constraint-row scaling. A zero tangent row with zero RHS is recorded
redundant and omitted, while a zero tangent row with nonzero RHS is infeasible
and fails closed. Affine feasibility is the minimum 2-norm residual from the
same registered SVD pseudoinverse, reported dimensionlessly as
`||C_hat q_hat-d_hat||_2/max(1,||d_hat||_2)` at all three fixed sensitivity
multipliers. No other B/H/C row equilibration, column normalization, unit
choice, or data-dependent scaling is permitted.

## Deterministic rank-revealing algebra

The oracle must use deterministic dense linear algebra appropriate to the
small proof fixtures, with all scales and tolerances published:

### Frozen residual calculus

Residual acceptance is fixed here before any proof result. Let
`eps64=2^-52`. For each individual check, let `d` be the maximum of one and
every row, inner, and column dimension of the matrices participating in that
check, and define

```text
r_tol(d) = 4096 * d * eps64.
```

The factor, dimension rule, and norms are not case inputs and may not be
changed after observing results. For an annihilation/orthogonality check use

```text
r_zero(A,X) = ||A X||_F / (||A||_2 ||X||_F).
```

For an equality check use

```text
r_eq(L,R) = ||L-R||_F / max(||L||_F,||R||_F).
```

If a displayed denominator is exactly zero, its residual is defined as zero
only when the numerator is exactly zero, and positive infinity otherwise.
All operands, products, norms, residuals, and tolerances use finite binary64;
a nonfinite value fails closed. A check passes only when its reported residual
is at most its `r_tol(d)`. Use `r_zero` for `A N`, `Pi_G Pi_P`, and
other zero products; use `r_eq` for symmetry, idempotence, containment,
projector invariance/equality, `Q^T Q=I`, and the stated
`H_w^T H_w`/mass equivalence. For a rank-`k` projector also require
`abs(trace(P)-k)/max(1,k) <= r_tol(d)`; `k` comes from the frozen SVD decision,
never from rounding the trace. Affine feasibility uses the already frozen
dimensionless minimum residual. It is classified feasible when that residual
is at most `r_tol(d)` and infeasible otherwise; expected-infeasible hostile
fixtures report rather than suppress the residual. Every subspace produced at
the three SVD sensitivity multipliers must pass the same residual checks; a
failed check or dimension change blocks a categorical semantic claim. These
residual tolerances verify computed algebra and never modify the rank threshold.

1. Apply only the frozen `S_q`, positive quadrature weights, and constraint-row
   normalization above; record every resulting scale.
2. For a finite binary64 matrix `A` of shape `(m,n)`, compute singular values
   in descending order. If `m=0` or `A` is exactly zero, define `rank(A)=0`,
   `ker(A)=I_n`, largest singular value and threshold zero. If `n=0`, the
   nullspace/projector are empty. Otherwise freeze

   ```text
   tau(A) = 64 * max(m,n) * eps64 * sigma_max(A),
   rank(A) = count(sigma_i > tau(A)).
   ```

   Always report decisions again at the fixed sensitivity multipliers
   `(0.25, 1.0, 4.0)*tau`; any dimension change across that band is reported
   as threshold-sensitive evidence and blocks a categorical semantic claim.
   These constants may not be changed after results.
   For a derived restriction `T=A Q`, where `Q` is an orthonormal
   projector-derived basis, do not rescale roundoff by `sigma_max(T)`. Freeze
   and record the inherited parent scale `s_A=sigma_max(A)` from the parent's
   multiplier-one decomposition before forming `T`, and use

   ```text
   tau_parent(T | A) = 64 * max(rows(T),columns(T)) * eps64 * s_A.
   ```

   Apply the same sensitivity multipliers only to `tau_parent`. If `A` is
   exactly zero, require `T` to be exactly zero and use the registered
   zero-matrix convention; otherwise a zero parent with a nonzero restriction
   fails closed. This inherited scale is fixed by the parent operator or
   projector, never selected from a restricted spectrum or a case result.
   In particular, use parent `H_w` for `H_w Q_N`, and parent `Pi_P` or
   `Pi_P_C` for the quotient-image maps defined below. A nonzero verified
   orthogonal projector has inherited scale exactly one. The residual
   tolerance remains `4096*d*eps64` and is never multiplied by an SVD
   sensitivity multiplier.
3. Form each null projector `Pi=N N^T` from the SVD nullspace, symmetrize it as
   `(Pi+Pi^T)/2`, and use the projector—not raw SVD vectors—as the invariant
   evidence for repeated/degenerate singular spaces. Derive an optional basis
   only from projector columns: at each step project all `Pi e_j` against the
   accepted basis with two modified-Gram-Schmidt passes; choose the largest
   residual 2-norm (ties within `256*eps64*max(1,max_norm)` choose the smallest
   column index). Before normalization require
   `max_norm > r_tol(max(1,n))`; otherwise canonical basis extraction fails
   closed instead of normalizing a numerical zero. Normalize, then choose sign
   so the largest-absolute component is positive. For that sign choice,
   components tie when
   `max_abs-abs(value) <= 256*eps64*max(1,max_abs)`; choose the smallest tied
   index. Stop after the registered projector rank.
4. Serialize each unquantized projector and projector-derived basis for JSON as
   C-order rows of finite binary64 JSON number tokens. Map either signed zero to
   token `0`; otherwise start with binary64 `format(value,'.17g')`, lowercase
   `E` to `e`, and, when an exponent exists, serialize it as `e`, an optional
   minus sign, and the base-10 exponent magnitude with no plus sign or leading
   zeroes. Preserve the formatter's mantissa verbatim. JSON uses
   lexicographically sorted keys, separators exactly `(',',':')`, UTF-8 without
   BOM, and one terminal LF.

   Projector/basis digests are explicitly environment-scoped exact snapshots,
   not cross-runtime scientific identities. Before hashing a projector,
   symmetrize it. For either projector or basis, make a C-contiguous binary64
   copy, replace every value numerically equal to zero (including negative zero)
   with positive zero, require every value finite, convert to little-endian
   IEEE-754 binary64 dtype `<f8`, and take its exact C-order bytes. Hash SHA-256
   over the UTF-8/ASCII header
   `s4-nullspace-snapshot-v2|env=<64 lowercase hex>|<kind>|<rows>x<cols>|<f8|C|`,
   where `<kind>` is exactly `projector` or `basis`, followed immediately by
   those bytes. No quantization, rounding, half-grid guard, or numerical use of
   this digest is permitted.

   The `env` value is the SHA-256 of the exact environment manifest defined
   below. Exact snapshot-digest equality is required only for repeated runs
   whose complete environment-manifest digests are identical. When manifest
   digests differ, never compare snapshot digests as scientific evidence;
   cross-runtime equivalence is decided only by the frozen rank, dimension,
   projector, and residual calculus above. Store unquantized residuals
   separately. A digest difference within one environment is a reproducibility
   failure, not a tolerance decision.

### Exact environment manifest and hash domain

At process start, before importing NumPy, set and require these exact thread
controls in `os.environ`: `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`,
`MKL_NUM_THREADS=1`, `BLIS_NUM_THREADS=1`, `VECLIB_MAXIMUM_THREADS=1`, and
`NUMEXPR_NUM_THREADS=1`. Before that assignment, collect every environment
entry whose name, compared case-insensitively, starts with `OPENBLAS_`, `MKL_`,
`BLIS_`, `VECLIB_`, `ACCELERATE_`, `OMP_`, `GOTO_`, or `NUMEXPR_`; reject
case-insensitive duplicate names and require each name/value free of CR/LF.
Reject if any collected case-folded name is one of
`openblas_coretype`, `openblas_verbose`, `openblas_default_num_threads`,
`mkl_cbwr`, `mkl_debug_cpu_type`, `mkl_enable_instructions`,
`mkl_verbose`, `mkl_dynamic`, `blis_arch_type`, `blis_model_type`,
`goto_num_threads`, `omp_dynamic`, `omp_proc_bind`, `omp_places`, or
`omp_schedule`. For each of the six controlled thread names, reject a
case-insensitive spelling that is not the exact uppercase spelling; accept
absence or exact value `1`, then assign exact uppercase value `1`. Other
recognized-prefix entries, including `OMP_STACKSIZE`, remain unchanged and are
bound into the manifest's `numeric_environment`; none is silently deleted.
Backend runtime architecture/thread/library binding below is still mandatory,
so an unlisted override that changes the loaded numerical backend also changes
the manifest or fails its one-thread/backend checks. If NumPy is already in
`sys.modules`, fail closed.
The exact snapshot-manifest implementation in this stage supports only CPython
on Windows with `sys.byteorder == 'little'`; another runtime may reproduce the
scientific matrices and residuals but must report `snapshot_digest_available`
false and must not emit or compare an environment/snapshot digest. On the
supported runtime, after importing NumPy, create one manifest containing exactly
these fields and expressions:

- `schema`: literal `s4-nullspace-environment-v1`;
- `python_implementation=platform.python_implementation()`,
  `python_version=platform.python_version()`,
  `python_cache_tag=sys.implementation.cache_tag`,
  `python_compiler=platform.python_compiler()`, and
  `python_build=list(platform.python_build())`; require nonempty strings and an
  exact two-string build array;
- `numpy_version=np.__version__` and `numpy_record`, an object produced by the
  frozen installed-distribution verification below;
- `os_system=platform.system()`, `os_release=platform.release()`,
  `os_version=platform.version()`, `machine=platform.machine()`,
  `processor=platform.processor()`, and `byteorder=sys.byteorder`; require
  `os_system == 'Windows'`, nonempty values, and `byteorder == 'little'`;
- `float_info`: an object containing exact integer `radix`, `mant_dig`,
  `max_exp`, `min_exp`, `rounds`, and `epsilon_hex=float.hex(epsilon)`;
- `numpy_float64`: an object containing `dtype` (must be `float64`),
  `itemsize` (must be 8), `byteorder` after normalization to literal `little`,
  and `eps_hex=float.hex(np.finfo(np.float64).eps)`;
- `numpy_config`: `np.__config__.show(mode='dicts')` after recursively deleting
  every mapping entry whose case-folded key is exactly `path`, `commands`,
  `include directory`, `lib directory`, or `pc file directory`; retain all
  remaining build-dependency, compiler name/version, machine, OpenBLAS, and
  SIMD values; recursively require JSON primitives/string-keyed mappings/lists,
  sort mapping keys, and preserve list order;
- `numpy_cpu`: import exactly `numpy._core._multiarray_umath` and copy exactly
  the keys `features`, `baseline`, and `dispatch` from its attributes
  `__cpu_features__`, `__cpu_baseline__`, and `__cpu_dispatch__`, respectively;
  absence of an attribute fails closed;
- `blas_runtime`: the string-key-sorted output of
  `threadpoolctl.threadpool_info()` after one fixed `np.linalg.svd` warm-up on
  the C-order binary64 identity matrix of shape `(2,2)`. The list must contain
  exactly one entry whose `user_api` is `blas`; for this registered Windows
  stage require exact `internal_api == 'openblas'`, `num_threads == 1`, and
  nonempty `version`, `threading_layer`, `architecture`, and `prefix` strings.
  Accept exactly the source entry keys `user_api`, `internal_api`, `num_threads`,
  `version`, `threading_layer`, `architecture`, `prefix`, and `filepath`; an
  extra/missing key fails. Replace `filepath` with key `binary` whose value is
  exactly `{role,name,sha256}` matched from `numeric_binary_artifacts`, then
  store the manifest value exactly as
  `{library:<normalized entry>,distribution:<installed verification object>}`,
  where `distribution` is the `threadpoolctl` installed-distribution algorithm
  below. Missing/ambiguous BLAS, unmatched binary, or unsupported backend fails;
- `numeric_binary_artifacts`: an ordinally sorted JSON array covering the
  resolved `sys.executable`; every regular file in its parent whose filename
  case-fold matches `python*.dll`, `vcruntime*.dll`, or `msvcp*.dll`; and every
  regular file with a case-folded `.pyd` or `.dll` suffix recursively under the
  installed NumPy package directory and its sibling `numpy.libs` directory.
  Require at least one `python<major><minor>*.dll`, at least one NumPy `.pyd`,
  and a nonempty `numpy.libs`. Each entry is exactly
  `{role,name,size,sha256}`: `role` is `python_executable`, `python_runtime`,
  `numpy`, or `numpy.libs`; `name` is only the executable filename for the first
  two roles and otherwise the forward-slash relative path under that role's
  root; `size` is the exact byte count and `sha256` hashes raw file bytes.
  Resolve every root/file, reject symlinks or Windows reparse points, duplicate
  case-folded `(role,name)` pairs, files escaping their declared root, missing
  roots, or empty required sets. Select suffixes case-insensitively, retain the
  actual serialized case, then sort entries by Python ordinal string tuple
  `(entry['role'],entry['name'])`—never by absolute path. Absolute paths are
  deliberately not serialized;
- `thread_controls`: an object with exactly the six names and literal string
  value `1` listed above;
- `numeric_environment`: an ordinal-key-sorted object containing every
  recognized-prefix environment entry collected after the six assignments,
  preserving exact key spelling and string value. This includes the six thread
  controls and benign settings such as `OMP_STACKSIZE`; it must contain no
  rejected-name entry.

Transient executable/install paths, user names, PIDs, timestamps, and working
directories are deliberately excluded. Serialize the manifest with sorted
keys, separators `(',',':')`, `ensure_ascii=True`, UTF-8 without BOM, and one
terminal LF; require every string free of CR/LF; SHA-256 those exact bytes.
Record both manifest and digest in every output. Heimdall must independently
reconstruct them. This manifest scopes byte repeatability; it does not replace
the formulation/source hashes or the scientific residual checks.

The installed-distribution verification algorithm used for both `numpy_record`
and `blas_runtime.distribution` is exact. Call
`importlib.metadata.distribution(<literal name>)`; require non-None `.files`;
among those `PackagePath` values select exactly one whose `.name == 'RECORD'`
and whose parent name ends with `.dist-info`; resolve
`distribution_base=Path(distribution.locate_file('')).resolve()` and require a
directory; resolve `distribution.locate_file(record_path)` and require a regular
non-reparse file.
Hash its raw bytes. Decode those same bytes as strict UTF-8 without BOM and parse
with `csv.reader(io.StringIO(decoded_text,newline=''),strict=True)` through full
iterator exhaustion; require exactly three columns and unique forward-slash
relative path strings with no empty/dot/backslash/drive component. A path with
no `..` component must resolve through `distribution.locate_file(path)` beneath
the resolved distribution base. For the literal `numpy` distribution only,
permit exactly `../../Scripts/f2py.exe` and
`../../Scripts/numpy-config.exe`: each must resolve beneath the exact resolved
`sys.executable` parent's `Scripts` child; no other row may contain `..`.
Record `external_verified_count` separately and require it equals two for NumPy
and zero for threadpoolctl. `verified_count` counts every successfully verified
hashed/sized row, including external rows; thus the two external NumPy rows are
included in both `verified_count` and `external_verified_count`. Every
row with both hash and size must name a regular non-reparse file, have a decimal
nonnegative size equal to `stat().st_size`, use algorithm literal `sha256`, and
match the URL-safe-base64 no-padding SHA-256 of its raw bytes. The only rows
allowed to omit both hash and size are RECORD itself and `.pyc` files under a
`__pycache__` component; a row omitting only one fails. Return exactly
`{name,version,record_name,record_sha256,verified_count,external_verified_count,unhashed_pyc_count}`,
where `record_name=record_path.as_posix()` exactly.
Require `name` and `version` from distribution metadata to equal the requested
canonical project name case-insensitively and the imported module version
exactly, respectively. This binds the installed Python sources as well as the
RECORD metadata.

For `numpy_config`, `numpy_cpu`, and `blas_runtime`, the recursive canonicalizer
accepts only `None`, exact Python `bool`, exact Python `int`, finite exact Python
`float`, `str`, mappings with exact-string keys, and list/tuple containers;
tuples become lists, mapping keys are ordinally sorted, list/tuple order is
preserved, signed float zero becomes positive zero, and any other scalar or
container type fails. Every string/key must be free of CR/LF. Filtering occurs
before canonicalization and uses the exact case-folded keys already listed.
5. Compute `N_B=ker(B_w)` first. Restrict `H_w` to a projector-derived basis of
   `N_B` using the inherited parent scale of `H_w`; the image in full
   dimensionless DOF space of `ker(H_w Q_N_B)` defines `G`. Verify
   `Pi_G Pi_N_B=Pi_G` with the registered
   `r_eq` check and define the positive-mass quotient representative only as
   `Pi_P=Pi_N_B-Pi_G`; symmetrize and verify its idempotence, orthogonality to
   `Pi_G`, and dimension by trace/rank. Never label individual degenerate SVD
   vectors by inspection.
6. Independently verify every projector/basis with residuals for `B_w`, `H_w`,
   stiffness, and consistent mass.
7. Construct the analytic rigid candidate space `R` from dimensionless forms
   of the documented component-wise translation/rotation fields and its own
   deterministic projector. Every intersection of represented subspaces uses
   the following symmetric augmented-basis primitive, never a restriction whose
   threshold is derived from its own near-zero spectrum. For projector-derived
   orthonormal bases `Q_U,Q_V`, form `A_UV=[Q_U,-Q_V]`, apply the ordinary
   frozen SVD rule and sensitivity multipliers to this O(1)-scaled matrix, and
   map the coefficient kernel back through both bases. The two mapped range
   projectors must agree under the frozen residual calculus, and dimension,
   symmetry, idempotence, trace, containment, and orthogonality must pass at all
   multipliers. Empty subspaces use the exact registered conventions.

   First establish `R_N=R intersect N_B` with that primitive and obtain its
   projector-derived basis `Q_R_N`. The rigid image in the registered quotient
   `N_B/G`, represented by `P`, is

   ```text
   Y_R = Pi_P Q_R_N,
   Pi_RQ = projector(range(Y_R)),
   Pi_Z = Pi_P - Pi_RQ.
   ```

   Rank-reveal `Y_R` with the inherited parent scale of `Pi_P`. Independently
   compute `R_G=R_N intersect G` and require
   `rank(Y_R)=dim(R_N)-dim(R_G)` at all three multipliers. If that expected
   dimension is zero, return the exact zero `Pi_RQ`; a roundoff-only range must
   not create a direction. Never substitute raw `R intersect P` or
   `Pi_P Pi_R Pi_P`: a rigid vector may have a gauge component, so its quotient
   representative need not remain in `R`. Symmetrize and residual-check
   containment, idempotence, orthogonality, annihilation, trace, and dimensions
   for `Pi_RQ` and `Pi_Z` at every multiplier. This keeps gauge, rigid quotient
   class, and non-rigid positive-mass mechanism distinct without relabelling
   mixed numerical basis vectors by inspection.

The proof must distinguish local element operators from assembled topology.
It must never claim that a constrained or reduced rank is the local rank.

## Required semantic domains and fixtures

### Local element

At minimum: square, affine/skew, tapered, distorted, and valid warped Q4s;
uniform and varied directors; uniform and nonuniform thickness; cyclic and
anchored-reversal numbering. Report `rank(B)`, `null(B)`, `rank(H N_B)`,
`dim(G)`, `rank(Pi_P)`, `rank(Pi_RQ)`, `rank(Pi_Z)`, rigid-quotient separation,
consistent-mass participation,
and invariance of subspace projectors.

The flat unit-square expectation is frozen as
`dim(N,G,P,R_N,RQ,Z)=(8,1,7,6,6,1)`. Its constant-drill gauge overlaps the
physical rigid z-rotation without being a rigid vector; the projected rigid
coset remains one of six rigid quotient directions. The checkerboard candidate
is the single non-rigid positive-mass quotient direction. Also include a
two-dimensional algebraic counterexample frozen exactly as

```text
N = R^2,
G = span([0,1]^T),
P = span([1,0]^T),
R_N = span([1,1]^T).
```

Here `R_N intersect P={0}` and `R_N intersect G={0}`, but
`range(Pi_P Q_R_N)=P` has rank one. This proves independently of the S4 result
that raw intersection cannot represent the quotient image.

The inherited-scale regression family is also frozen before execution. For
`delta in {0,2^-60,2^-40,1}`, use

```text
A_delta = diag(1,delta),
Q = [0,1]^T,
T_delta = A_delta Q,
s_A = sigma_max(A_delta) = 1.
```

With `tau_parent` and multipliers `(0.25,1,4)`, expected ranks are respectively
`(0,0,1,1)` at every multiplier. A threshold derived only from
`sigma_max(T_delta)` would incorrectly assign rank one to `delta=2^-60`; this
test permanently detects that relative-only failure without selecting a scale
from any proof outcome.

### Assembled topology

Use independent, numeric-only fixture assembly in the proof oracle, not
ANYsolver shared assembly. Cover:

- one element;
- two elements sharing an edge;
- regular 2x2 and non-bipartite/odd-cycle-compatible Q4 connectivity;
- distorted and curved/warped patches;
- disconnected components and deletion-created splits;
- activity states that are active, softened by explicit nonzero scaling, and
  deleted, while treating zero scaling/deletion as topology changes rather
  than magic constraints.

Derive the global drill-difference/strain operator from exact element maps and
actual connectivity/orientation. Prove or refute constant-per-component and
alternating-pattern claims for each topology; do not hard-code “two modes.”

For this proof, deletion preserves the declared global node/DOF universe and
original indices; it removes the selected element, its quadrature rows, and its
connectivity contribution before any support/MPC/coupling rows are applied.
There is no implicit pruning, compaction, reindexing, or reference remap.
Validate every C/coupling index against the original declared node universe
before deletion, assemble retained B/H rows next, identify nodes with zero
retained-element incidence as orphans, then apply the validated C rows in the
unchanged global columns. Report the orphan coordinate projector and its
intersections with `G`, `G_C`, and the constraint row space separately, because
unconstrained orphan DOFs create explicit zero-B/zero-H gauge dimensions. A
fixture whose deletion leaves no positive B/H quadrature total is invalid under
the frozen weight rules. This is a proof convention for observable algebra,
not a production deletion or node-compaction policy.

### Supports, MPCs, and coupling semantics

Represent supports and MPCs as explicit affine rows `C_phys q_phys=d` in the
proof only. Store and report the RHS separately. Null/tangent semantics use
only the homogenous dimensionless matrix `C_hat` produced by the frozen row
scaling above; the RHS affects feasibility/offset, never tangent rank. Cover
fixed drill DOFs, tied drill DOFs, weighted affine MPCs, and redundant /
dependent constraints. Report `rank(C_hat)`, RHS feasibility residual,
`N_C=ker(vertical_stack(B_w,C_hat))`, and

```text
G_C = N_C intersect ker(H_w),
Pi_P_C = Pi_N_C - Pi_G_C
```

For constrained rigid quotient semantics, first form the represented sum
`S_RG=R_N+G` from projector-derived bases and define

```text
L_C = N_C intersect S_RG,
L_G_C = L_C intersect G_C,
Y_R_C = Pi_P_C Q_L_C,
Pi_RQ_C = projector(range(Y_R_C)),
Pi_Z_C = Pi_P_C - Pi_RQ_C.
```

Use the symmetric augmented-basis primitive for the intersections and the
inherited parent scale of `Pi_P_C` for `Y_R_C`. Require
`rank(Y_R_C)=dim(L_C)-dim(L_G_C)` at every multiplier. This captures a rigid
quotient class whose constraint-compatible representative may differ from a
raw rigid vector by gauge; raw `R intersect N_C`, raw `R intersect P_C`, and
direct projection of rigid vectors excluded from `L_C` are invalid
substitutes. Repeat every projector and annihilation check. Never
conflate local element rank, free assembled rank, homogeneous constrained
rank, affine feasibility, or a later reduced solve.

Represent shell/shell and beam/shell drill-transfer semantics only through
explicit abstract coupling matrices with documented intended physical work
conjugacy. The proof may state what rank a declared coupling removes, but may
not claim a production coupling is physically valid or edit its policy.

Activity/deletion semantics must consume the already authoritative conceptual
boundary—canonical activity and element-local pre-scatter scaling—without
copying policy into production code. The proof must document how topology and
null components change; it must not integrate native-hybrid or touch its maps.

## Reproducibility and proof claims

The JSON cases file must freeze coordinates, connectivity, directors,
thickness, supports, MPC/coupling matrices, activity/deletion states,
the governing tolerance constants as read-only metadata, expected dimensions
where analytically derived, and source hashes. It may not override a tolerance.
The standalone oracle may use the Python standard library and must import no
third-party package except NumPy and the installed-distribution-verified
`threadpoolctl`; its only ANY code is the accepted quarantined
numeric reference modules. No geometry package, live document, solver shared
assembly, or sibling package. Ordinary `import anysolver...` is forbidden
because it executes the root initializer. The exact synthetic import procedure
is frozen:

1. resolve `src/anysolver/shell_formulations` relative to the oracle's own
   repository root and verify these accepted canonical SHA-256 values before
   loading:

   ```text
   protocol.py                    32BF05E0BD0B282C49C47392CAF9400D2C8C136B9B6D1D398B3B54451EACB089
   q4_common.py                   DE2DCDCD3BC04A90A4DB2C074EC15D4E4B097123010F146A0C718506443C3D19
   mitc4_plus_d_reference.py      AAF44046EEE607541F2A84EA16CBA948CB98130A568BBF8B5B03B243928E9536
   mitc4_plus_d_scalar.py         9E3F1827F813546FF9C183C77E654F268C8A67F976B63FF010749EFDEAB3118B
   ```

   The canonical hash input is exact and platform-independent: read raw bytes;
   reject an initial UTF-8 BOM; decode with strict UTF-8; replace every CRLF
   pair with one LF; reject any CR that remains; encode the resulting text as
   UTF-8 without BOM; then SHA-256 those normalized bytes. Never hash the raw
   Windows checkout bytes as the accepted identity. For audit only, the
   observed CRLF-checkout raw-byte SHAs at registration were respectively
   `A90D6461B55256A56895B43EB9EB647336A247AF9B449ED677E242EC67318280`,
   `B645C772191AF8F10A1D1074FB2A748C32D22D2F1E1D01B94D6462E81EA3B19C`,
   `D736BAAED3D32D5929664D406B91DD92E7AD91791750B863F1DC4D5ADE49862F`,
   and `7F18C6EEEB0C6B5B2B66FDA8C63A724687BC9DEBCE2BE217F9055CBC95EEE2B5`;
   those raw hashes are observations, not portable acceptance identities.

2. snapshot `sys.modules` as an insertion-order-preserving mapping
   `modules_before={name:object}`. Fail before mutation if any existing key
   case-folds to `anysolver` or starts with `anysolver.`; also precompute the six
   exact canonical loader names below and fail if any of them exists under any
   casing. Never overwrite or reuse a pre-existing module object;
3. create synthetic `types.ModuleType` packages named exactly `anysolver` and
   `anysolver.shell_formulations`, assign only their local `__path__`,
   `__package__`, and package `ModuleSpec`, then register them in `sys.modules`;
4. load the four files in the dependency order above with
   `importlib.util.spec_from_file_location` under their canonical submodule
   names; never execute either real package initializer;
5. verify each loaded module `__file__`
   remains under the quarantined worktree, then case-fold all newly added
   module names and reject any name whose top-level component case-folds to an
   `any*` name unless the full case-folded name is one of exactly these six:
   `anysolver`, `anysolver.shell_formulations`, and the four registered
   `anysolver.shell_formulations.<module>` names. On any loader failure, remove
   from `sys.modules` every key absent from `modules_before`, restore every
   original key to its exact `modules_before[name]` object in original insertion
   order, then verify both exact key order and `sys.modules[name] is
   modules_before[name]` for every key before raising. If rollback verification
   fails, raise that transactional-integrity failure chained from the loader
   failure. The loader must never leave, overwrite, or substitute a module;

Tests must load the oracle itself by file location before any ANYsolver import
and exercise the same fail-closed procedure. `--list` must be light and
deterministic.

The proof document and stored output must clearly classify each statement as:

- exact algebraic theorem/derivation;
- deterministic numerical evidence;
- physical interpretation requiring later authority;
- unresolved ambiguity/blocker.

No evidence in this stage authorizes applying a gauge or constraint. In
particular, a positive-mass checkerboard mechanism remains a mechanism unless
a later physical derivation and boss authorization establish otherwise.

## Lightweight gates and definition of done

Without a PERF lease, run only the focused oracle and focused proof test. No
broad/full suite, build, profiler, benchmark, scaling sweep, stress run, or
qualification.

Definition of done:

1. all edits are within Vidar's four new paths plus the two coordinator packet
   paths after freeze;
2. source and contract hashes remain unchanged;
3. local and topology-level gauge/quotient-projector partitions are deterministic and residual-
   verified, including `R_N`, free/constrained rigid quotient images, and
   non-rigid complements at every sensitivity multiplier;
4. supports/MPC/coupling/activity/deletion semantics are explicit matrices,
   with local versus constrained rank kept separate;
5. repeated runs under an identical complete environment-manifest digest
   produce byte-identical normalized output and snapshot hashes; runs with
   different or unavailable manifest digests are compared only through the
   frozen numerical rank/projector/residual equivalence rules;
6. focused tests pass and `git diff --check` is clean;
7. Heimdall independently accepts equations, algorithms, cases, semantics,
   claims, hashes, and reproducibility;
8. an atomic quarantined proof commit and completion packet are reported to the
   boss, without merge/integration or option selection.
