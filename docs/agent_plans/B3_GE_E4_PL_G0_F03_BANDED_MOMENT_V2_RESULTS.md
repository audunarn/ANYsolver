# F03 banded moment v2: adverse diagnostic result

22 September 2026. Frozen source `98341168793525eeb6572c64b88d41a9650a26eb` ran once under exclusive root `C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-banded-moment-v2`. Supervisor exit **1**. Manifest SHA-256 `5c0e7ab6152cf3ef673fbc24f1c47b4edf503f3e7945bc4e76f0efbb35114f0b`; records SHA-256 `4b94cb3118adc7eb4c0a64e5c6c46914060ea72e7692feb4e4219df281796383`. Retain all raw stdout/stderr and records. Do not rerun this identity.

All ten native Q4/S3 mesh cases failed at the separately reported structural check with `cross=1.0, root_native=0.0`. The five pure algebraic synthetic sizes completed. The native application did not reach parity evaluation; there is **no native pass**.

Source examination resolves the `cross` criterion as a diagnostic coding mistake: after zeroing diagonal channel blocks, it evaluates `relative(offblock,t)`, which is `||offblock-t||/||t||` and therefore measures the removed diagonal portion, not the remaining off-block portion. A perfectly block-diagonal nonzero `t` scores 1.0. The v2 data establish root-native zero on these cases; they do not by themselves establish actual off-block zero because that value was not reported. V3 must measure `||offblock||/||t||`, retain every other criterion, and use a new frozen source/evidence identity and independent review. F03/G0B stay open.
