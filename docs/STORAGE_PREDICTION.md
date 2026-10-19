# Storage-only predictors

`storage_prediction/1` is an optional compression role in capsule2. It grants no engineering response, field availability, case certification or new-case evaluation. Mixed native-affinity exports may retain qualified primitive columns with literal zeros at native rows solely to predict stored words. VM/EQ predictors derive from primitive predictions using existing runtime rules; principal predictors are omitted. Dynamic/selected layouts remain on the explicit route.

ANYpost stores `xor_storage_prediction_sha256/1`: every original float64 word is XOR-corrected and SHA256-protected per persisted case/spatial chunk, at most256KiB. A partial read validates the complete integrity tile before returning selected values. Verified tiles consume the configured cache budget; dependencies, conversion, output and tile scratch consume the configured working budget, capped at128MiB. Missing stored rows never use the predictor as a scientific fallback.

Finite-input prediction overflow may write a durable zero-prediction tile. Readers follow the recorded branch and verify decoded SHA256; a changed platform/runtime prediction or corruption is a typed refusal. This is integrity detection, not a universal cross-platform binary64 portability guarantee. A supplied predictor has no physical meaning at padded native rows.

New decoding requires `ANYpost[results]` with anysolver-results2.1 capability `STORAGE_PREDICTION_API=1`. Metadata discovery and old plain/numeric-XOR reads remain runtime-free. Capsule/runtime2 and ordered_float64/1 scientific semantics are unchanged. The lightweight validator imports only NumPy and validates structure; it does not certify arbitrary metadata or element physics.

An unused staged storage role can be withdrawn only with zero target rows and zero new-codec datasets. Existing failed input handling remains fail-fast, preserves the previous destination and publishes terminal diagnostic evidence. No empty successful recovery records or fabricated field descriptors are introduced.
