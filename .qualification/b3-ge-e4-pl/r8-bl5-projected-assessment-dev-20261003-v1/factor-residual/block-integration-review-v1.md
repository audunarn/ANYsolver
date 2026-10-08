# Supporting fixed 18 integration review V1: preserved initial source

Read-only source/control review; no numerical job, test, source edit, Git operation or worker was run by this reviewer. This report preserves initial evidence; the corrected complete review is block-integration-review-v2.md. No scientific/F03 acceptance.

Initial source-only inspection read helper ef0c978db1fd0fc8349b4c776a74ecb232a0c78f24b535f9f94e33d140146b64. The actual first control run froze helper d57095c2699520c04425900bdfbf02c0d808beedee646e17d81bc713499bb437 and tests cdf325394d928e653c1dc5c31c4110f6b3c8b5d38241999362c3960080a902e8; those outcomes must not be attributed to the earlier ef0 read.

No mathematical theorem/rounding defect was identified: W is arbitrary exact stored, complete WF multiplication is enclosed, lower Ghat comparison is validated, b/c/eta and inverse square are directed, and the V3 driver preserves original FF.T rho. The source was not execution-ready while BLOCK_SOURCE_PIN remained a placeholder.

Read test-block-v1/stdout.log: 4 failed, 28 passed in 0.73s. Three failures were generated WF CSR index-order validation in signed factor sizes 18/21 and all-ones 36. Native multiplication may return unsorted CSR; sorting this trusted generated result's index/value pairs preserves the operator/error enclosure. Combining duplicates or dropping upper entries would require additional arithmetic/error treatment and was not authorized.

Fourth failure was the workspace-control KeyError: a 10000-byte limit triggered the earlier owned-input resource guard, so combined workspace_estimate_bytes was not present. This was a test-phase mismatch, not a resource-guard bypass. The repair should admit ownership but refuse combined workspace before any local solve.

I requested a just-below 1 Neumann control in addition to eta>=1 refusal. Existing exact Fraction controls comparing the returned 2-norm bound against actual inverse1*inf use a stronger condition than the general theorem; they validate selected fixtures, not a universal mathematical acceptance condition.

No case ran against this failed source. Failed snapshots/logs remain in sources-block-v1 and test-block-v1. The final correction/report must retain these identities and failures.