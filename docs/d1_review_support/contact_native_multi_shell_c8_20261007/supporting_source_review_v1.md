# Multiple native/S3 supporting source review

Status: early coherent-source review; author still finishing candidate. Read only; no imports/numerical jobs/tests/builds/product edits/Git/workers/sibling access. Same-family support, not engineering acceptance.

## Early actionable findings sent to lead

1. Exterior physical boundary is misclassified as internal patch transition: `_geometry` catches every kernel rim refusal and emits UNADMITTED_PATCH_TRANSITION_BAND; accepted pair rows label every selected triangle boundary as transition. Topology records exterior and internal edges but these labels are not used in those caller paths. A beam approaching the actual exterior triangle edge gets an internal-transition report. Require explicit selected-face exterior/internal identities/semantics and accurate refusal classification (or honest combined patch-boundary label), plus separate exterior/internal discriminator. Neither boundary is currently admitted; this finding proposes no edge force or patch switching.
2. Pair geometry can run uncharged: `_geometry` computes affine skin and exact normal/orientation and can refuse before geometry_gap's leaf budget debit. An invalid-orientation attempt therefore exposes geometry used0 despite actual work. The declared every-pair prospective visit cap requires one debit at start of the full pair geometry unit, with no leaf double-charge; test failed orientation used1. Work adapter also maps skin before leaf debit, so debit-before-unit placement should be explicit. Integration recursion correctly debits before visiting each interval.

## Reviewed consistency

Structural shell elements scatter actual K/M exactly once, including unselected faces and shared nodes; body vectors are independent and global native maps are reused by contributors. Same beam/target selections share their state/mass. Selected native zero lift makes physical sample map constant and second-order geometric pullback zero; own native Hessian spatial conversion and both crossblocks are preserved. Global physical/algebraic shell charts, two-leg actual projected endpoint path, replay hooks and transaction services follow the single owner.

The dimensional error map has a conservative max row/column bound `B=max(4,1+2|offset|/length)` in global metre/length-times-rotation coordinates, hence operator norm <=B. Component gradient error eps gives sqrt27*B*eps; component Hessian error eps gives27*B²*eps. No curvature error term exists for the admitted zero lift/affine shell map. Factory reserves per-pair shares and owner aggregates mapped error witnesses; current tests inspect both row and column bounds/zero curvature. These fixtures remain unexecuted and are not independent quadrature qualification.

One active operation ledger is inherited through initialization/trial/restore callbacks; all pair integration visits and swept legs share it. Per-path saved counts are deltas, which avoids operation-total replay mismatch. Failures and cap exhaustion need actual runtime evidence. Default None leaf path retains previous call form and fingerprint fields; exact old owner/result/capsule parity is still prospective, not a source PASS.

## Current source identities (ongoing bytes)

- `src/anysolver/_ge_beam3_native_multi_shell_contact.py` — `789861580f1d3c227d293a31cd43a64d004c1afd926ed8d3d7a3cab04ca16f4f`

- `src/anysolver/general_contact/native_transient_multi_shell.py` — `857767c4d74a26c9cdf8a460945b8fca74f1b7ce704a6831ac13daf79855232d`

- `src/anysolver/general_contact/native_retained_line_s3.py` — `7f92beea2ac82dbc823a45014b5e3c690359e5c7ea512775cdb13bbc1480a750`

- `src/anysolver/general_contact/native_retained_line_s3_work.py` — `eb70cd26f3e9398f9b537d65e414e49c22cf45aa94419ce49a61f0d12766349c`

- `tests/test_general_contact_native_transient_multi_shell.py` — `e0e6c517c60908b4d6522ea2366de591da1877749bd4b665a48d36f5b4511973`