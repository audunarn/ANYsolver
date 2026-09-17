# Retained diagnostic evidence

Root: `C:\Github\ANYsolver\.tmp_spectral_medium_fine`.
These records bind diagnostic files, not a successful performance qualification.
Failed/incomplete attempts remain immutable and excluded from speed claims.

For each directory, recursively sort files by path, then construct a JSON list
of objects with `path` (relative POSIX path), `bytes`, and lowercase `sha256`.
Hash UTF-8 `json.dumps(rows, sort_keys=True, separators=(",", ":"))` with no
trailing newline. The table records that directory-manifest SHA-256.

| Directory | Status | Files | Total bytes | Manifest SHA-256 |
| --- | --- | ---: | ---: | --- |
| baseline-cylinder-fine-buckling-effective-05 | ok | 9 | 24566889 | 5f512d8c6797fbfd4a4e7a63e21d48824306bf3b104b65156de26871751729b4 |
| baseline-cylinder-medium-buckling-01 | failed | 2 | 1754 | 7c268d28dd53767e431977ae4aa881b7bd42a0cc82108b64ba45ff24dc234eaa |
| baseline-cylinder-medium-buckling-corrected-03 | failed | 4 | 4750390 | f0d7119f44784ea0d07af57818c2e7ddabef41cea386ce94185cd0be589f03db |
| baseline-cylinder-medium-buckling-effective-05 | ok | 9 | 13750822 | 855da9f893c42ac67a71264b23db4faa1ac5a8e2c19d3139950aea3775ff1862 |
| baseline-cylinder-medium-modal-04 | aborted/incomplete | 2 | 2232 | af4190fd85a20e0f2cfd7c5a65f210ec53ab13b79bbfbea3b5028846e3c84995 |
| baseline-panel-fine-buckling-01 | ok | 9 | 15567459 | 1f9fc9234bc1d6750445c5cbbd8432f9364c7aa8cb5bbb2941070d1df341a5da |
| baseline-panel-fine-modal-04 | ok | 9 | 802076 | 63c4752c0761b7d595c63490526f6c668858e999814603ab92f135f368886895 |
| baseline-panel-medium-buckling-01 | ok | 9 | 11028139 | cd66b33f46393deb3025051c823a6e9d0309400d5c0ba8269ab6198d3d0b640a |
| baseline-panel-medium-modal-04 | ok | 9 | 569484 | 484761d25dda61d88d86c03fd0e5963f6da3fcdb9e3ac991a7f8633adefc1af6 |
| diagnostic-cylinder-coarse-buckling-02 | failed | 2 | 7094 | 6b7c7e3b1628f1ba07ede533dc3793fc19a7d9738e8cd370b8c1d26774a430b2 |
| screen-panel-medium-buckling-05-0-baseline | ok | 5 | 4446110 | 32a6220d74db6b1bbe98517c9881f982b1090c659c2c3c3fd5e65e6cb208da02 |
| screen-panel-medium-buckling-05-1-candidate | ok | 5 | 4445428 | 486b33aad45fbd80333fdd972c22e57b367da161ebef2c19735310145cbb355c |
| screen-panel-medium-buckling-05-2-candidate | ok | 5 | 4445438 | 84856ade970766033131e6db8b85a51c3d973d41ad45204bc453c0f4f7bda7cf |
| screen-panel-medium-buckling-05-3-baseline | ok | 5 | 4446118 | 4370b0b5cefad7edf7e7f1e4ebce4f65e68f77ba6cfa2fe01603d8ccf59acb7d |
| screen-panel-medium-buckling-05-4-baseline | ok | 5 | 4446092 | 0f592e0f7f6d5c2a9e92bc3a2f00e65865d3f2d197c1a64f003c3e53bf3a05a9 |
| screen-panel-medium-buckling-05-5-candidate | ok | 5 | 4445436 | 16a1d241e0a3418a30d7f164ea2e9b4379525bbeb8561fea2122b7d17a325d3e |
| smoke-cylinder-coarse-corrected-03 | diagnostic zero-moment fixture | 5 | 3619814 | 11e2e9ed12c9ffd5a99db05c22410d1ac9aedf823ba4414bf9eaf8c21d173661 |
| smoke-panel-buckling-01 | ok | 5 | 1830249 | 5185965efa17a211c56a4559d1830d919bd659557cf12533891689d65463eadf |

Standalone diagnostic hashes (no accepted eigen results):

- `diagnose_modal_entry.py`: `081a9628f3aad6b2f4568589a955098026c0cad76a1c2ae6dc5182ecfcf0c95a`.
- `cylinder-modal-entry-probe-06.log`: `811a328aeaedfe850d49196cc275a5cf5b8f3be0b16021fc1a901f6e77286878` (numerical replacement correctly rejected).
- `cylinder-modal-entry-probe-07.log`: `bfe9860ca60ef943ddcc55ede39bac8278e480cbe3f363f3b11571ffd6e1cd9f` (observer reached sparse dispatch; intentional abort caught by solver, not a successful solve).

Verification inventories remain separate: 116 source/authority regression
tests; 10 harness tests; six alternating screen processes; baseline profiling
and failed diagnostic attempts as enumerated above. No final seven-pair,
installed-wheel or broader qualification inventory was executed.

Independent reviews: `spectral_gate_review` returned FIX-FIRST for omitted
effective cylinder moment; `spectral_fixture_rereview` returned SHIP after
correction, limited to diagnostic tooling and the unpromoted prototype.
