# Sparse envelope kernel review V3: admission repair and arithmetic discriminator

Read-only supporting review in C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001. No numerical job, test, worker or Git operation was run by this reviewer. Prior preparation-review-v2.md and failed/HOLD evidence remain unchanged. This review supplies no different-family scientific acceptance, qualification or formal F03 authority.

## Admission blocker resolved

Current caller SHA256 is 72dd59cf4b222c8b22fb3cc5f4a6b04172e81b87dea4beeb338e14905b055f1d. bind:159–166 now calls previous_hash. That helper at204–210 explicitly validates the historical v7 schema BL5_DEVELOPMENT_RAW_EXTENSION_V7 and predecessor filename raw-manifest-v6.json before using previous_sha256; v8/v6 use their actual previous_manifest_sha256 schema. The returned digest is compared against the predecessor file hash. This resolves the previously identified KeyError without rewriting historical manifests.

Evidence actually read:

- test-v3/stdout.log: 33 passed in 0.74s; execution.json:terminal exit 0, elapsed 1.325s, sampled peak 86,872,064 bytes, numeric-or-unresolved maximum 1. Added tests validate v7 schema/name and refusal of an unsupported version.
- bind-smoke-v3.py calls actual bind for ns16_b1_8, ns16_b8, ns32_b1_8 and all three canonical reused owners ns16_b1_2, ns16_b2, ns32_b1. stdout.log reports all six BOUND with caller SHA 72dd59cf...; supervised terminal exit 0, elapsed 0.834s, sampled peak 67,244,032 bytes. The saved script contains no solver/certificate job; it exercises admission and actual frozen files.

The raw v1 numerical screens remain evidence of predecessor caller 8021f614..., not of current 72dd59cf.... The guard-only change does not alter their mechanical body or the fixed saved operators. The separately inspected immutable file hashes and successful current bind smoke establish applicability without pretending the old solver outputs ran current source. The ns16_b8 mechanical HOLD and zero-shift representative HOLD are unresolved.

Current test source SHA256:56dc2e4307e5251ff7c77170d3879fe9aa7cc76eea02aefb36d221ab7b653d0e. Interval primitive is unchanged 47adfa44533b08c33aac8879d231b63d1b900ac2b50cf7d9e3427b52428d0199; saved primitive unchanged 064a0d8d36dca6db916d9a8eb2563620cf8c72cb82920bd4dc0c7182b6d1c138.

## Explicit Decimal100 discriminator

A separately selected Decimal100 mode is mathematically legitimate. Current certify_decimal_lower:231–304 converts every binary64 input and fixed shift with Decimal.from_float, then applies FLOOR/CEILING elementary operations with positive denominator checks. Replacing only the two context precisions 50 by 100 preserves outward enclosures of the same exact-real elimination. No tolerance, matrix entry, shift, graph, pattern or permutation changes. Higher precision may reduce rounding-width amplification but need not resolve interval dependency; failure to resolve remains HOLD.

Implementation conditions: leave50 as the default; validate an explicitly bounded precision selection (plain integer 50 or 100, rejecting booleans/coercions); use the selected precision consistently in both contexts; preserve Underflow/Subnormal and existing invalid-operation/division/overflow traps; retain complete structural pattern checks. Record precision, source hash, exact predecessor array/JSON hashes, permutation, pattern and fixed shift. Save fresh output rather than overwriting50 evidence. Add exact Fraction enclosure controls at both precisions and controls for rejected precision values. Respect unchanged global elapsed/memory supervision and proof/update caps; larger precision can cost more time and storage, so the old elapsed or workspace estimate is not a measured100-digit resource result.

At zero shift, a complete positive100-digit proof would establish SPD of the exact stored representative alone. It would not prove the actual constrained mechanical kernel, because the representative-to-target epsilon obligations have not been subtracted. At the original fixed 2epsilon shift, a complete positive proof can enter the existing unchanged mechanical transfer contract. Neither outcome authorizes reducing epsilon, changing scientific criteria, consuming formal authority or declaring actual-law failure on HOLD.

Verdict: previous admission blocker resolved. Explicit bounded Decimal100 is a valid arithmetic discriminator under these conditions; its implementation and runtime are not yet reviewed or measured here.