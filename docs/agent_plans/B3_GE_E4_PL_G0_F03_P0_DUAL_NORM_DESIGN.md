# F03 classical P0 multiplier norm: bounded construction

22 September 2026. This is an independent **norm-only research candidate**.
It does not select a mortar space, qualify G0B/F03, replace a signed native
KKT, or authorize a loaded run. The closed local-dual/P0 and coarse-P1
physical screens had large sampled gaps and adverse mesh sensitivity. The
trace-image dual was model-wide, while the ambient local broken-trace dual
lost physical-image equivalence on joint refinement. Their results remain
unaltered; no case in those screens is repeated here.

Use the existing classical piecewise-constant multiplier over a line of
physical length `L` and `N_m` equal cells. In the dimensionless coordinate
`x=s/L`, define `e_0=1`, `e_n=sqrt(2) cos(n pi x)` for `n>=1`, and
`w_n=(1+(n pi)^2)^(-1/2)`. The P0 cell moments are exactly
`v_in=∫_{i/N_m}^{(i+1)/N_m} e_n(x) dx`; the implementation evaluates them
with `sinc`, including the constant mode. The coefficient Gram is

```text
H = L² Σ_{n=0}^∞ w_n v_n v_nᵀ.
```

Thus physical multiplier density `λ_i` in N/m has `λᵀHλ` in N². For
three metre-valued planar gap channels, apply the same scalar Gram by
channel (a block diagonal or equivalent Kronecker product in the actual
row ordering). The yaw gap is first scaled by the physical eccentric
length, here `.46 m`, so its conjugate multiplier is also a force density;
the equivalent yaw couple density is `.46 λ_yaw` in N. The pairing with a
metre-valued gap is `Σ_i λ_i∫cell gap(s) ds` in N m. For a different
numerical length unit, rescale both `L` and the numerical density; the
force norm and physical work are invariant. This is a reference-length
inhomogeneous spectral H^-1/2 norm; its chosen low-frequency normalization
is explicit and must be part of any later mechanical equivalence argument.

`p0_dual_gram(N_m,L,N)` returns a computable lower `H_N` and upper matrix
`H_N + L² w_(N+1) (M - Σ_{n=0}^N v_n v_nᵀ)`, where `M=I/N_m`.
Parseval gives the positive residual and the decreasing weights give
an analytic Loewner enclosure of the infinite sum. The implementation
uses binary64, clips only small negative roundoff in the residual, and
checks a bounded high-mode reference; it is **not a certified interval
arithmetic enclosure** at machine precision. The first `N_m` cosine moment
columns form a nonsingular DCT-type matrix (their sinc factors do not
vanish), so `N>=N_m-1` ensures strict positive definiteness. No small
eigenvalues are clipped; only roundoff in the Parseval residual is cleaned
after a tight negative-eigenvalue check. A bounded high-mode dense matrix
is a reference oracle, not a claim that its uncomputed tail is zero.

This norm is nonlocal and currently dense. More importantly, the native
beam yaw is discontinuous, with jumps outside a continuous H^(1/2) trace
space, and the shell offset pose fit needs uniform control. Hence this
classical continuous-trace dual does not itself bound the reachable broken
native gap or supply a mesh-uniform inf-sup constant. The signed retained
Schur cancellation, independent physical response, all six eccentric
channels, and joint/shell/beam refinement remain separate open G0B work.
