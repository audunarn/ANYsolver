# GE-B3 shared-kinematic factor-chain successor

Status: **development correction; full qualification remains incomplete**.
Independent review: **PENDING**. No public routing or release is authorized.

Base: `9e2418020d09b43098da80c94b73b66a8029436d`, tree
`376f5c2a45c34ae94301d28c8bc34de70e1cf766`. The installed-wheel covariance
failure at that checkpoint is preserved unchanged. This successor changes
the private modal representation, not the accepted beam or shell mechanics.

## Diagnosis and algebra

The old private modal split expands the constitutive coefficients into the
global-coordinate strain rows before spectral reduction. Large axial/shear
and coupled-section coefficients multiply a shared cell kinematic map. Early
rounding of those expanded rows loses small compatible terms; the exact
eigensolver subsequently reproduces that perturbed operator accurately.

The diagnostic preserves two half-cell strain maps z and the twelve signed
endpoint virtual-rotation maps ell. Stack their first variations in J:

    J = [Dz; Dell]

At each station, gamma = v z_cell. For the partial Legendre section Hessian,
write its blocks Hgg, Hmg and Hmm; N interpolates endpoint moments. Let

    C = sum(weight N^T Hmg v)
    S = -sum(weight N^T Hmm N)

Then the moment-eliminated material factor is the unexpanded chain L J:

    L_top = [sqrt(weight) chol(Hgg)^T v, 0]   (one station block per row)
    L_bottom = chol(S)^(-1) [C, I]

Cell placements in these expressions are explicit in the source. This is the
same moment-Schur identity as the preserved split. The geometric Hessian G
still includes endpoint moment work, strain second derivatives and lifted
spatial-dead-load work. A loaded-state test requires G to be byte-identical to
the old split; it is not discarded or replaced with a positive reference
tangent. Section state, quadrature, SO(3) derivatives and recovery are reused.

The new modal solver retains L and J through complete-map congruence:

    H = V^T ((L J)^T (L J) + G) V
    M = V^T B^T B V

Integer-over-power-of-two arithmetic evaluates the supplied binary64 chain
without rounding intermediate products; each final matrix entry is rounded
once. A rounded expansion is used only to find a complete numerical coordinate
map V, never as final eigenvalue authority. Original-chain Ritz checks,
separate material/geometric action residuals, physical mass normalization and
full-coordinate backward checks remain. Numerical brackets are not certified
intervals. Negative eigenvalues, cell inertia and massless traces are retained.

## Scope and observed diagnosis

The separately coded Decimal chain audit reduced the failed per-node and
batched general-rotation covariance discrepancies to below 6e-16. The expanded
factor arrays differ from the old arrays by only about 3e-17 relatively, which
explains why a global norm comparison cannot establish weak-mode accuracy.
This locates a concrete expansion-rounding mechanism in the tested specimen;
it does not establish accuracy over every geometry, load state or section.

Native checks retain both coordinate-construction orders at L/h=1,000,000,
reference general rotations, finite-load covariance, compression/tension,
plastic-history elastic unloading, free rigid modes and large translations.
The native factor-chain spectrum and mode columns are also compared directly
with the 90-digit reference-chain audit. No covariance tolerance was changed.

An artificial matrix with entries of order 1e16 needed a physical mode-vector
component correction below binary64 spacing. A draft test incorrectly
expected the solver to return a positive root with an acceptable physical
vector. It instead failed its action-residual guard. The failed draft and
report remain; the revised test requires this fail-closed behavior. An exact
arithmetic test separately confirms the chain retains the missing unit work.
This is not a waiver of a beam case or permission to return an inaccurate mode.

The final two fresh-directory runs each passed **47 tests**, in 79.733 and
79.090 seconds. Their **28 JSON records are byte-identical**. Inventories are
separate: 8 exact chain arithmetic tests, 20 numerical-kernel tests, 17 native
state/mode tests, and 2 common-map/Decimal audit tests.

The archive contains **111 files, 4,875,331 bytes**, verified individually from
the ordinary workspace context:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-factor-chain-development-20260907-7b774419039a`.
Original temporary files are retained; only verified relay duplicates may be
removed. No raw evidence or earlier failed package result is overwritten.

Final run inventories, source hashes, timing diagnostics, deterministic JSON
pairs and external archive contents are bound by
`docs/reference_cases/ge_beam3_common_kinematic_chain_evidence.json`.
All original diagnostics and the failed installed wheel remain preserved.
These are ordinary one/two-macro correctness checks, not formal resource runs
or complete engineering qualification. Cooperative kernel limits do not
replace process-tree safeguards in future isolated qualification runners.

## Remaining work

Build a new private wheel from the clean frozen successor and repeat the
expanded installed-state/covariance gate; do not rerun or overwrite the failed
wheel. Broaden loaded and slender curved stability and convergence checks.
The nonlinear force/continuation operators still use their preserved numerical
assembly: their high-contrast variational accuracy must be checked separately,
not inferred from improved modal representation. Complete V5 continuation,
general nonlinear/fibre sections, loads and solver parity, supported runtimes,
objective eccentric/curved beam-shell connections and independent review.

Existing B2/B3, Q4/S3, public defaults, aliases, package versions, dependencies,
workflows, qualification records and all previously committed source remain
unchanged. This checkpoint is not production completion.
