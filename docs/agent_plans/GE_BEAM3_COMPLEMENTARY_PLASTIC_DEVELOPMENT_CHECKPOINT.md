# GE-B3 complementary plasticity development checkpoint

Status: **section progress; nonlinear cell force precision unresolved**.
Independent review: **PENDING**. Nonlinear beam integration is not authorized
by these results. The full beam/joint qualification goal remains incomplete.

Base: `fba13e4e9165b0ce4f4acea0b61a0860bc00e85b`, tree
`e44ab0ac4a786bfcfbdc7e06e42b9562c81a61c7`.

## Full section conjugate

The new private section component is the algebraic Fenchel conjugate of the
existing directed-hardening incremental potential, not a changed plastic law.
For stress/resultant vector s, plastic direction a, elastic matrix C, yield
force Y, hardening H and fixed origin (z0,p0):

    W*(s) = 1/2 s^T C^-1 s + z0 (a^T s)
            + max(|a^T s|-Y-H p0,0)^2/(2H).
    dz = sign(a^T s) max(|a^T s|-Y-H p0,0)/H.
    z_new = z0 + dz; p_new = p0 + |dz|.
    dW*/ds = C^-1 s + a z_new.
    d2W*/ds2 = C^-1 + a a^T/H on a smooth plastic branch.

The denominator H is appropriate to prescribed resultants. It must not be
confused with the strain-controlled return-map denominator a^T C a + H.
The exact yield boundary is recorded as a semismooth elastic selection,
not a classically smooth Hessian. Histories and section coefficients are
owned and immutable; evaluating a trial never commits its origin.

The initial single-vector elastic strain failed the 1e-11 force check at
contrast 1e12 (observed error approximately 2.91e-11). That source draft and
JUnit failure are preserved. The corrected component stores normalized high
and low elastic-strain parts. A scaled binary64 solve is a preconditioner;
bounded refinement uses the exact supplied-binary64 C times both strain parts
to calculate its residual. No section coefficient or acceptance tolerance
changes. A separate exact Fraction computation in the test verifies the represented
elastic equation. Total strain also retains a low part instead of subtracting
plastic strain to recover the elastic part. Compliance factors remain available
so later operators need not prematurely form a rounded dense Gram matrix.

Section tests cover coupled elasticity, both plastic signs, prior history,
unloading/reversal, Fenchel energy, dissipation, tangent reciprocity, directional
first/second derivatives, explicit yield-boundary disposition, immutable
capture, invalid input and exact scalar minimization. These are same-author
checks, not an independent scientific review or general fibre-section parity.

## Integrated cell conjugate

A section conjugate cannot simply replace each station law independently:
the beam shares six cell-strain coordinates across its quadrature stations.
The research cell adapter therefore transforms the integrated functional.
With the preserved elastic matrices A, B, S, station plastic coordinates tau,
and quadrature-weighted coupling matrices Dz and Dm:

    Phi(z,m,tau) = 1/2 z^T A z + z^T B m - 1/2 m^T S m
                  - z^T Dz tau - m^T Dm tau + 1/2 tau^T F tau
                  + incremental hardening/dissipation.
    K = F - Dz^T A^-1 Dz.
    G = [Dz^T A^-1, Dm^T - Dz^T A^-1 B].
    Q = K + diag(w H); r = w (Y + H p0); d = G p - K z0.
    delta = argmin 1/2 delta^T Q delta - d^T delta + r^T |delta|.

Here p contains the six retained cell forces and twelve endpoint moments.
K is constructed as a projected-factor Gram matrix, avoiding subtraction of
two large PSD matrices. The complementary gradient is C0 p + G^T(z0+delta),
and its smooth active-branch Hessian adds G_A^T Q_AA^-1 G_A to C0. This is a
same-author discrete derivation requiring independent review. The shared
strain field, moment interpolation, quadrature and material law are unchanged.

The first active-set iteration cycled at contrast 1e4. Its captured sequence
stalled with optimality error about 0.04595, not merely a roundoff-level error.
The correction solves inside the current sign region, stops at the first zero
crossing, removes that bound, and releases one violated zero coordinate only
after the current region is stationary. The 32-iteration/30-second bounds
and 1e-11 optimality gate are unchanged. This resolves the 1e4 cycle.

**One genuine failure remains.** At contrast 1e12, the latest cell result has
optimality residual 1.1516e-12 after 16 iterations, but reconstructing the
prescribed force through the original partial station response gives error
**2.203355787243626e-11**, above the unchanged **1e-11** gate. Curvature,
history and Fenchel checks alone do not override this failure. The failed
test remains an ordinary failing assertion, not a skip or expected-failure
waiver. The nonlinear cell is not integrated into the retained beam controller.

## Separate test inventories

- Original section draft: 15 passed, 1 failed.
- Refined section: 16 passed.
- Final section A: 27 passed, 1.366 seconds.
- Final section B: 27 passed, 1.359 seconds.
- Original cell: 2 passed, 2 failed.
- Instrumented cell: 2 passed, 2 failed.
- Corrected sign-region algorithm: 3 passed, 1 failed.
- Latest cell including invalid-input checks: 6 passed, 1 failed, 1.649 seconds.

The two final section runs have four byte-identical JSON pairs. The failed
cell campaign is not presented as a passing deterministic cycle. All runs are
small correctness checks with one numerical thread; timings are diagnostics,
not performance claims. No resource request or ledger was consumed or altered.
These are local research revisions, not retries of a consumed formal request.

## Preservation and next action

Archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-complementary-plastic-development-20260907-9325e35bd701`.
Its 63 content files total **298,721 bytes**, including six failed-draft source
files, raw cell systems, optimality traces and all JUnit reports. The additional
manifest is **20,025 bytes**, SHA-256
`9f3aadacac90721ade58dfa96da9332995d0ca1d1ebc600c01d85be68311d569`.
Every external file was verified by byte count and SHA-256 from the ordinary
workspace context. Original temporary outputs remain; verified relay/draft
duplicates can be removed after preservation.

Next: audit the high-contrast force reconstruction with exact arithmetic on
the captured/source-bound cell inputs. Distinguish integrated coefficient,
gradient-representation and station-evaluation losses, then correct the
implicated numerical representation without relaxing the gate. Only after
the complete cell gate passes should nonlinear histories be integrated into
the retained beam state/controller. General fibre sections, larger finite
loading/continuation, mass/modal/buckling integration, broader curved/slender
qualification and objective eccentric/curved beam-shell connections remain
open.

One private section module and research/test/checkpoint files are added. No
existing tracked file, B2/B3, accepted straight beam, qualified Q4/S3, default,
alias, dependency, package version or workflow changes. No publication,
activation or public qualification is claimed.
