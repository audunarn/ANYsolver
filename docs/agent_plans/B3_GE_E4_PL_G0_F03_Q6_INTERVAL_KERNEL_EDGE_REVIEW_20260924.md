# Q6 compiled interval-kernel edge review

**24 September 2026. Preparatory arithmetic work; no formal numerical
certificate acceptance.** Independent read-only audit found that existing
scalar/compiled bitwise parity and one crafted exact-Fraction case did not
exercise a subnormal input multiplied into a normal output. Such a case is
important because a DAZ arithmetic mode could silently shrink the enclosure.

An adversarial test first exposed a separate correctness defect: the compiled
CSR product used the input block's row count as the output row count. A valid
one-row, multiple-column CSR input caused a Windows access violation. Both
compiled and scalar products now use the matrix row count. The compiled entry
point also checks CSR pointer/index bounds before invoking Numba, so malformed
inputs fail with `ValueError` rather than reaching unchecked compiled indexing.
The production certificate path already validated its square CSR input; this
fix closes the helper's broader accepted-input contract.

The compiled arithmetic signature now uses runtime-supplied subnormal,
smallest-normal and large-normal operands. It checks subnormal addition,
normal-to-subnormal multiplication, and signed subnormal-to-normal products,
alongside `nextafter`. Exact-Fraction tests verify outward enclosure and
bitwise scalar parity for amplified subnormals, signed underflow to zero,
mixed cancellation, near-overflow finite sums and a 128-term alternating row.
Overflow and malformed sparse inputs are explicitly rejected. The affected
sparse-certificate and compiled-kernel suites passed **28/28** after the fix.

This is stronger edge-case evidence, not a universal proof of the installed
compiler and CPU arithmetic. The exact Numba/LLVM/platform environment must
be pinned, compiled operations independently reviewed or otherwise justified,
and all saved inverse columns replayed with independent arithmetic before a
formal scientific registration. The earlier X2 source rehearsals retain their
original source identities and remain unregistered. F03/G0B remain open;
G1 remains barred.

Independent read-only review found no further arithmetic counterexample in
the patched path and confirmed the row/column and CSR guards. It still requires
installed compiler/environment identity, independent compiled-operation
review and complete saved-only inverse replay before a formal soundness claim.
The added CSR scans run for every inverse block. A small synthetic scan timing
does not replace a full patched X2 measurement; remeasure the complete route
before freezing its resource budget.
