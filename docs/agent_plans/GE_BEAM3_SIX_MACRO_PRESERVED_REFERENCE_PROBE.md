# Six-macro physical-fibre arch: new bounded refinement diagnostic

Parent `2b2afbe8fb004def013c8a1cc4e946c384bd17e8`, tree
`9aa99e3640c8022c017bc9a11e3abd46ef010cc0`. This extends the prepared family
to its already admitted six-macro case. It is not a retry of failed request
`b89e903dc17d44408ce0c42d11c6b61f`, whose checkpoint and failure remain intact.

## Why this calculation

The completed load-only audit is 2,409 bytes with SHA-256
`bf27fe91b0fad7dc6247a42536b14c40af280fd1dae789350e0f0fa9034a72bd`.
Two frozen standard-library reader invocations produced identical bytes.
The first four two-/four-macro load errors decrease from 5.79/12.39/19.50/27.09
percent to 2.09/4.96/7.22/8.75 percent. Neither mesh provides the required
finest-mesh engineering qualification. A six-macro case measures continued
refinement without repeating solved two-/four-macro targets.

This diagnostic does not guarantee that six macros are sufficient. It must
retain unsatisfactory errors and negative/changed branch behavior. No
coefficient, quadrature, tolerance, section, reference or load tuning is allowed.

## Frozen numerical scope

- Six native macros, 13 nodes, the same y=.1(1-x*x) reference parabola.
- The existing physical-fibre section: nominal EA=1e6, GA=4e5, bending EI=100;
  same exact stored fibre/material parameters and integration order four.
- Clamped end poses, crown dead force and the existing four translation
  targets .01, .025, .04, .055, in that order.
- Existing retained driver size: 222 variables, below its unchanged 256 bound.
- No shell coupling, additional mesh, later target, alternate seed or retry.

The model/section/solver implementations are unchanged. The family already
admits six macros; this runner selects that case explicitly. Reference loads
come exclusively from preserved BVP9 evidence at commit `3f05a4ee`, LF hash
`c2401dfc756cf7d95005ee6c92f43ae5960c82b361e7477a68cd2b676e025728`.
No continuum BVP, sensitivity calculation or new reference generation runs.
These are nominal reference coefficients, not an exact dyadic section proof.

## Execution and publication

Freeze the clean source first, then register the exact command:

`C:/Python/Python314/python.exe -B -m docs.reference_cases.ge_beam3_fibre_arch_six_probe --revision FROZEN_COMMIT --output FRESH_EXTERNAL_DIRECTORY`

Obtain the administrator's explicit ledger approval and grant, acquire only
the matching request, run once, and release after complete tree termination.
The earlier request is consumed and must never be reused. No resource request
or execution is authorized merely by this document.

The inherited guard checks the exact clean source commit, Python executable
SHA and existing installed runtime versions before importing mechanics. It is
version checking, not an installed-wheel artifact graph qualification. The
preserved reference bytes are checked before mechanics and before publication.

One suspended-launch Windows Job contains the worker and its whole tree:
24 GiB, one numerical-library thread, 600 seconds wall and 120 seconds of
CPU/output inactivity. The native controller's shorter existing cooperative
budget is unchanged. Cleanup must prove the tree terminal within the existing
15-second bound. No extra worker, retry or following wave is automatic.

The worker writes progress, retains a checkpoint even if the native controller
fails, and requires completed native replay before preparing the comparison.
The reader verifies checkpoint seals, all four targets, six-macro node/element
counts and zero physical histories before comparing with the elastic loads.
The complete pending packet must equal the parent's independently re-created
load packet byte-for-byte. Publication requires root exit, zero active Job
processes, successful final cleanup, final source/reference guards and
unchanged staged bytes. Failure leaves raw/partial diagnostics, not a
canonical comparison. Original reference/native evidence is never overwritten.

## Output and checks

Schema: `GE_BEAM3_SIX_MACRO_PRESERVED_REFERENCE_LOAD_DIAGNOSTIC_V1`.
Status: `DEVELOPMENT_LOAD_COMPARISON_ONLY`; no qualification PASS threshold.
It records exact source/checkpoint/reference identities, native and reference
loads, recomputed errors, record seals and zero-history counts. It records
native replay as performed only in the successful worker path; reference
recomputation, prior-four-macro success, same-branch proof and production
qualification remain false. Independent scientific review is pending.

Focused final suite: 79 passed, one BVP test deliberately deselected, 0.96 s.
No native/BVP solve occurred. Process tests use disposable Jobs and temporary
fixtures, including lingering descendants and cleanup-uncertain publication
refusal. An earlier default-pytest-temp cleanup produced a PermissionError
after 42 passing tests; the final suite uses a fresh explicit basetemp and had
no cleanup error. No historical pytest files were removed.

After the single authorized execution, compare the refinement trend and
review the next necessary accuracy/stability step. This is not full geometric
field/recovery/energy convergence, post-buckling branch tracking or independent
qualification. Existing B2/B3, qualified Q4/S3, aliases/defaults, recovery,
package metadata and historical scientific evidence remain unchanged. The
complete standalone beam and objective shell-connection goal remains open.
