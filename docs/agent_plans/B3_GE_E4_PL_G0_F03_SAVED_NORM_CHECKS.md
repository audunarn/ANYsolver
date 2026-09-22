# Saved signed norm binding

The saved-norm component operates on one owned physical `Functional` and a
fixed ordered pair of observations at48/64. It performs no equilibrium solve
and does not establish complete recovery or physical qualification.

`SavedNorm` retains signed channels, signed totals, all six existing
contribution/cancellation arrays, per-channel finite/nonnegative/nonzero-valid
flags, total flags, exact-zero flags and ordered typed failure records.
Arrays own immutable bytes; caller mutation or restoring writeability cannot
alter them. Numeric NaN is permitted only as an unavailable stored observation;
infinity is rejected. The raw returned observation uses the underlying
observer's missing values, which are null-compatible, rather than fabricated
numeric replacements.

Channel-flag storage axes are `(order, flag, channel)`; flags are finite,
nonnegative, nonzero-valid in that order. Total flags are finite, nonnegative,
admissible. Component axes are `(order, channel, component)`, with diagonal,
offdiagonal, atom_cross, atom_gram, sum_abs_terms, cancellation_ratio in order.
Orders48/64 are implicit and fixed; no user-selected fallback exists.

Preflight bounds exact input intervals/bits, quadrature operations and peak
workspace before owned reconstruction or norm evaluation. Workspace includes
the input snapshots, maximum rational input storage, retained interval
contributions and fixed64-point scratch. These are conservative estimates,
not measured RSS. Geometry, representation and unexpected errors propagate;
the verifier does not broadly catch them or retry another order.

Every saved finite numeric observation must match the actual observation's
binary64 bytes, including signed zero. Missing-value locations must match;
NaN payload identity is not promised. Every boolean flag and every ordered
stage/channel/reason record must match exactly. Saved fields are never
regenerated or replaced by the verifier. `_pack` is an internal format adapter,
not a method that accepts its own generated observations as external evidence.

Acceptance independently requires finite and nonnegative signed channels and
totals, all validity flags, no reported failures, and consistency with the
exact functional's zero/nonzero channels. Every exact-zero channel must be
measured as zero and every exact-nonzero channel must be measured as nonzero
at both orders. An exact-zero functional must also have a zero total at both
orders. Even matching saved invalid values fail. A nonzero exact channel
reported as zero fails even if a flag is wrong. Finite negative channels
remain visible even when the total is positive.

For each order, a finite reported total must be bitwise identical to the
legacy `math.fsum` of its three finite signed channels. A known finite-input
sum overflow leaves the total unavailable and the observation rejected while
preserving the finite channel values. Unexpected summation errors propagate;
the consistency check does not convert programming failures into numerical
failure records.

For each signed channel and total, compare orders using
`abs(q48-q64)/max(abs(q48),abs(q64),1000**2)`. The four ratios use exact rational
representations of the measured finite binary64 values. Their maximum must
not exceed1e-10. Missing/invalid measurements fail before resolution is
considered; otherwise unresolved resolution remains HOLD_UNRESOLVED. No
absolute-value repair of observations, clipping, extra division by ell,
invented zero or automatic higher-order evaluation is permitted.

The source functional is revalidated into an owned snapshot, then the raw
observer is called exactly twice. Input hashes bind that exact physical
functional and the owned saved arrays/failure inventory. Results are immutable
observations, not cached acceptance authority. A composing verifier must still
bind the functional to the same q/eta and all other saved recovery fields.
This48/64 comparison measures quadrature resolution, not a rigorous bound on
the Green norm's analytic error.
