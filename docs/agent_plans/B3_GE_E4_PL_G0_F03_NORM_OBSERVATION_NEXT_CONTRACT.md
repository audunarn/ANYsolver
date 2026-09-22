# Required signed norm observation seam

22 September 2026. Read-only design guidance by independent reviewer
`/root/finite_pad_axis_review`; implementation and qualification remain open.
This contract completes the raw-norm requirement in
`B3_GE_E4_PL_G0_F03_RECOVERY_ADMISSION_NEXT_CONTRACT.md`. It changes no
scientific tolerance or registered execution authority.

Extract the existing local-functional quadrature arithmetic into a raw
`norm_observation_at_order` operation. Preserve each successful channel's
operation and summation order, physical moment/ell scaling once per operand,
and all existing diagonal/off-diagonal/atom/cancellation fields. Keep
`norm_at_order` as a strict compatibility wrapper: identical successful
dictionary values, and rejection for every previously rejected observation.

Separate finite measurement validity from admissibility. A finite negative
channel or total remains a measured signed value but fails nonnegativity.
A nonzero exact channel with a computed zero also fails. Preserve fixed three
channel positions, signed total, per-channel finite/nonnegative/nonzero-valid
flags, and typed failure stage/reason. If one channel is unavailable, retain
every independently completed finite peer. An overflowing total must not
erase finite channels. Never clip, take absolute values, replace a rejected
value with zero, or evaluate again with another quadrature rule.

Do not broadly catch ValueError. Keep invalid functional/order, representation,
geometry and active weighted-Jacobian guards distinct from numerical
observation failures and unexpected programming errors. Catch only identified
numeric operations: for example, fsum can raise OverflowError or its specific
mixed-infinities error before producing a number. Mark that channel/total
unavailable with its reason; use NaN only in explicitly permitted diagnostic
array storage and null in JSON. Do not manufacture a numeric result.

At orders48/64 retain each complete raw record and compare signed channels
and total with denominator `max(abs(q48),abs(q64),1000**2)`. Compute resolution
only where finite. The maximum discrepancy must satisfy 1e-10, and every
finite/nonnegative/nonzero requirement remains independently mandatory.
This measures quadrature resolution, not a rigorous Green-norm error bound.

Required focused checks before acceptance:

- Bitwise parity of successful historical strict-wrapper dictionaries.
- A negative channel with a positive total remains visible and rejected.
- An invalid channel with surviving finite peers preserves their values.
- Finite channels whose sum overflows remain retained.
- Exact zero is accepted; nonzero exact channel computed as zero is rejected.
- Historical strict-wrapper failures remain failures.
- Saved validity flags, raw channels and totals bind to the recomputation;
  altered flags, missing fields and masked negative values cannot pass.

Use bounded manufactured data only until independent review and the full
scientific protocol are complete. Old evidence stays immutable and retains
its original source identity. A revised helper requires new affected-scope
evidence, not relabeling earlier passes.
