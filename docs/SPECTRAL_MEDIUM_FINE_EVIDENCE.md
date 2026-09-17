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

## Accepted successor evidence

The following fresh directories bind the successor screen, final seven-pair
gate, retained-route checks and installed-wheel smoke using the same manifest
algorithm defined above.

| Directory | Status | Files | Total bytes | Manifest SHA-256 |
| --- | --- | ---: | ---: | --- |
| screen-panel-medium-wrap-06-0-baseline | ok | 5 | 4446092 | 9ba4df6276eb43da145504ee11f5df7f06beac2aef4f32f47774da1eab51da9f |
| screen-panel-medium-wrap-06-1-candidate | ok | 5 | 4445410 | dfb2670a701e9f4e55f051eb00d2359ef61d203a819ab927c34d5115b1d3fbdf |
| screen-panel-medium-wrap-06-2-candidate | ok | 5 | 4445438 | 04b7bfc1e4e12eeb504291e3eb0dcf37c2a59e4a6b9ba077ffb25d89ed8915bd |
| screen-panel-medium-wrap-06-3-baseline | ok | 5 | 4446083 | 37740475ca0ccfea8fa199a46361a504a1a6993be4280bb015b7284c9f6d3b59 |
| screen-panel-medium-wrap-06-4-baseline | ok | 5 | 4446100 | e83b48513763e9d140561f920dcfeb0bba829ad7fad8fddc2dae71401807a8cb |
| screen-panel-medium-wrap-06-5-candidate | ok | 5 | 4445447 | c04b469ca8feb232037315dfff4d07daf3321c2b051358dfbf6ca37d51fd7e98 |
| final-panel-medium-wrap-07-00-baseline | ok | 5 | 4446124 | 64ae007d39a250dad4f978d0296f63dd3afb109b361a33d25b037f127784488f |
| final-panel-medium-wrap-07-01-candidate | ok | 5 | 4445427 | ba87c8ba2985f0c2ccc5bd5b00c0400fa47cfe1000b3f21bd4828d4b3156ee60 |
| final-panel-medium-wrap-07-02-candidate | ok | 5 | 4445432 | d9210f99e322fe93171c02c5270969c29f617b7aa89b5b3c0f1ce368ffae12eb |
| final-panel-medium-wrap-07-03-baseline | ok | 5 | 4446089 | 861c8044c8243a9f55e26a163aca26f45c6949079accb3df6494777fc77e7f2a |
| final-panel-medium-wrap-07-04-baseline | ok | 5 | 4446109 | b7e443f3451ba4de09bd1b596b1e7033af59bf4007b19eac3c98f39fd51aef0e |
| final-panel-medium-wrap-07-05-candidate | ok | 5 | 4445430 | a80d23c06fedccc7f4f314077f2d027720554c09feb40921169a94460b848ecd |
| final-panel-medium-wrap-07-06-candidate | ok | 5 | 4445430 | 0514f2815e320bd6ee056843f844015908d96d314bbbd0388ea383e87b041e22 |
| final-panel-medium-wrap-07-07-baseline | ok | 5 | 4446087 | 8288320e0e2737f51fac0bc3de3a82443f1097a478e8e5dafd4b0fe0e4855dce |
| final-panel-medium-wrap-07-08-baseline | ok | 5 | 4446087 | a5120dd00c3fb9de5956b89ecd4c400159b57071930bd7a44f8128377abd64fe |
| final-panel-medium-wrap-07-09-candidate | ok | 5 | 4445420 | c550985856289d5ead8ae71fab1115fb5b2d00a94355861263765e2514d9de9d |
| final-panel-medium-wrap-07-10-candidate | ok | 5 | 4445428 | c8561a133edcbf5062338ba7faf5af972efc3ff3a0a463d2b05ac20152f22dca |
| final-panel-medium-wrap-07-11-baseline | ok | 5 | 4446094 | 35616d29c94700310c4bd70bea6cad4343d4d9779ff05194146ef5e5a47764d0 |
| final-panel-medium-wrap-07-12-baseline | ok | 5 | 4446084 | 5ff1b5766b6cdcc8e79190a1be75f96a53bcab68b89fca40de8c088abbb99f31 |
| final-panel-medium-wrap-07-13-candidate | ok | 5 | 4445439 | 7bc0954c39626c8ee0586b59217c0919fb7440da4e047612190a27081d00a1f6 |
| regression-wrap-08-00-baseline-girder_panel-fine-buckling | ok | 5 | 7586024 | c278f867d1cf1929032508468642d97ae952fd623e86ac201f3c986c1912ec70 |
| regression-wrap-08-01-candidate-girder_panel-fine-buckling | ok | 5 | 7585331 | 6bc9f4589cad80604f46ff7d2c5484b9c033e0317bc3fdbd4c9a36549614b283 |
| regression-wrap-08-02-candidate-girder_panel-medium-modal | ok | 5 | 329676 | 4368b3033bbe2dd7abbe57c3391a4261e323df1cfd2bcf54ea6afdb35f845a45 |
| regression-wrap-08-03-baseline-girder_panel-medium-modal | ok | 5 | 330344 | e89097318cb88eb23b43c264d44975efc02df288b4d87c6268937b64e3f8379c |
| regression-wrap-08-04-baseline-cylinder-medium-buckling | ok | 5 | 8932327 | 9c745cb223eee2882c40b83b7cdbf48f203efd881367f247bd9df463b59cf7f9 |
| regression-wrap-08-05-candidate-cylinder-medium-buckling | ok | 5 | 8931641 | 4cb83ef22f3dbe238c5afde073c0e30dab0d3e6e67a9a0372f8634963cfdad6c |
| wheel-wrap-09 | ok | 754 | 21397361 | 761dfe4fd8e27ed4c8cd051fa67b5275afb236abb1e710a6a15c956853224158 |

Accepted successor review: `wrap_review` returned SHIP with no findings after
20 targeted tests. Parent verification: 164 focused tests. The successor
freeze is `114d2cd83b8a7e5c5eacc23bbe20b3f7f902afb2` and the wheel SHA-256 is
`6BC45678A501CCC38D04294EE13BAF91C2F2824963F67DF0CBF4B1BAD5A2CD57`.
