# Supporting staged caller review

Non-implementing OpenAI kernel_numerical_contract: ready for Nx16 stage.
Same helper/error/target/floor and producer checkpoints.17-case whitelist excludes
four completed kernels; reused-owner paths correct.5/5/7 sequential stages,
fresh outputs, pinned600s/2GiB/1thread supervisor; stops on first non-PASS,
unexpected error or STOP. Current failed case stays in ledger; no retry.

One metadata correction completed before launch: new batch binding now records
actual stage-controller SHA, rather than original single-case wrapper.
- driver a4fb7ea500fb8fd8025497915847969a657cf2944748aa76ecc60efc52eb6d25
- controller f7f460b0fcdd1d347958b31784b5a82d663bdc28c9273cc3abd4533c0da8af34
- campaign79beec6c7b07afdf47d8c538825e4d7b78b6a566ea860bf02e7533d84380cafb

Read-only review: no tests/jobs/edits/Git; no scientific/different-family
acceptance. Root must inspect each terminal stage before advancing.
