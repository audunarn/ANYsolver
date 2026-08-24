# E4-PL-Q1H: Executable Domain-Coercivity Completion

Q1H starts from merged Q1G commit
`bcd9243e120391765be86e242467c0b4cf6c6a3f`. It closes only the three
requirements left unresolved by Q1G: executable continuous-domain K/H
coverage, the exact H quotient kernel, and a mesh-independent coercivity
constant over the registered Q1F geometry domain. The accepted Q1G
translation/rotation/scale rigid-range theorem is inherited by hash and is not
recomputed or modified.

The gauge uses `a=u-(p/q)v` and `b=v/q`. The Q1F variation condition becomes
`a^2+b^2 <= 1/8`; `u=a+p*b` and `v=q*b` are reconstructed exactly. An
adaptive outward enclosure covers the rational root box in `p,q,a,b`.
Necessary-condition failures are excluded exactly. Every other terminal leaf
must certify the actual Q1Y3 Schur mechanics on the whole box.

The 18 control rows are the 14 mixed-core rows, three centre-Taylor rows, and
one retained hourglass row. An independent algebraic-field transcription must
prove

`det(L_anchor) = 32*q^12/729`.

For H, an invertible Gauss coefficient transform separates two anchored
9-dimensional blocks. Their frozen exact minors are

- bending/shear: `-128*q^5`;
- membrane/drill:
  `(64/9)*q^6*((a+b)^2-3)*((a-b)^2-3)`.

Since `q >= 1/4` and `(a±b)^2 <= 1/4`, both are nonzero. Exact factor-row
annihilation of the inherited analytical rigid fields and the accepted Q1G
rigid-range theorem then establish `kernel(H)=range(R)` without revisiting the
rigid-range proof.

For coercivity, write the core metric as `S=B^T P_A B <= B^T B`. In the exact
control coordinates the candidate lower energy is
`diag(||B^T B||^-1 I14, 6*Gram, c_hourglass)`. Each positive leaf proves by
outward interval congruence that this lower form minus `10^-6 H` is positive
definite. Prefix-free binary leaf paths with Kraft sum one prove complete root
coverage. Two fresh parallel cycles must emit byte-identical canonical
records.

The inherited Q1F local-to-global sum theorem supplies the mesh-independent
constant: no trace, inverse, or mesh-size constant is introduced. A successful
Q1H result authorizes the next assembled non-intrusion/locking/stability stage
only. It does not authorize production selection, Q1B execution, API/default
changes, or replacement of legacy `ShellElement`.

All work is research-only under `docs/` and `tests/`. Every process is
single-threaded at the numerical-library level; bounded coverage may use up to
16 independent worker processes and has a 600-second wall ceiling.
