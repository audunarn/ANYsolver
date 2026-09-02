# S3 V5B Relaxed MIN3 Repair Funnel

## Scope

Apply only the accepted V5B relaxation authority to the frozen V5A MIN3
operator.  The candidate is
`CANDIDATE_E4_PL_S3_V5B_MIN3_RELAXED_FLAT_LINEAR_SCREEN_V1`.

For every element, form the unrelaxed V5A bending block `K_b` and shear block
`K_s*`.  Over the six rotational coordinates, compute

- `BENSUM = sum(diag(K_b)[rotational])`;
- `SHRSUM = sum(diag(K_s*)[rotational])`;
- `PSI_HAT = BENSUM/SHRSUM`; and
- `PHI_SQUARED = 2*PSI_HAT/(1+2*PSI_HAT)`.

Then use `K = K_m + K_b + PHI_SQUARED*K_s* + K_PL`.  This is exactly the
official MYSTRAN rule with `CBMIN3=2`, equivalently UHM `C_s=1/2`.  Both sums
must be positive.  Coefficient fitting is forbidden.

## Ordered gates

1. Recheck local interpolation, source-relaxed patch energy, six rigid modes,
   ranks 9/3/12, D3 covariance, director reversal, load work, symmetry, and
   virtual work.
2. Recheck 21 macrocells: sizes 1, 2, and 4; slash, backslash, and alternating;
   all-S3, isolated, and strip variants.  Membrane/bending patch energy remains
   continuum exact.  Shear energy is compared with the source-relaxed
   per-element energy.  Q4 D-to-N differences and interior patch actions remain
   diagnostics; interface action-reaction and load work remain hard gates.
3. Run the four preregistered development records first: N20/N40, dispersed
   slash, 5% and 10%.
4. Only after development passes, complete exactly 42 unique campaign records:
   36 dispersed combinations over N20/N40/N80, all three diagonals, and
   1/5/10/25%; three N20/N40/N80 chain/slash/10% holdouts; and three
   N20/N40/N80 all-S3/alternating research controls.  Compute three all-Q4
   baseline records separately.
5. Only after the campaign passes, run 12 all-S3/slash thin-regime records:
   N20/N40 for `t/L = 1e-1 ... 1e-6`.

The exact frozen connectivity hashes must be used.  No Stage 4A record is part
of this funnel.

## Thresholds

- local construction comparison: `3e-13`;
- local source identity: `3e-12`;
- macro source-patch/interface gate: `1e-10`;
- solve residual: `1e-8`;
- successive response error: `E_fine <= 1.02 E_coarse`;
- finest response error: `<= 2%`;
- N80 mixed error relative to all-Q4: `<=1.25` through 10% S3 and `<=1.50`
  at 25% S3; and
- normalized N40 response spread over `t/L=1e-3...1e-6`: `<=0.5%`.

All-S3 is a research control and is excluded from the mixed/all-Q4 ratio gate.
The relaxation factor must remain in `(0,1]` and decrease strictly as thickness
decreases at a fixed mesh level.

Diagonally equilibrate the assembled sparse system, reuse one deterministic LU
factorization, and apply two residual-correction solves.  This changes no
matrix, load, support, or scientific result; it reduces redundant
factorizations and keeps the reported N80 backward residual below the frozen
`1e-8` gate instead of weakening that gate for sparse-factorization roundoff.

## Process and decisions

Run two fresh cycles.  Each child uses one numerical-library thread, at most
24 GiB, and at most 600 seconds.  At most three processes overlap, the complete
wave is capped at 1,800 seconds, and automatic retry is forbidden.  Checker
replicas run concurrently and must be byte-identical; the two cycle proofs and
checks must also be byte-identical.

Terminal precedence:

1. `BLOCKED_E4_PL_S3_V5B_PROCESS_OR_EVIDENCE`
2. `NO_GO_E4_PL_S3_V5B_RELAXATION_SOURCE_OR_LOCAL_OPERATOR`
3. `NO_GO_E4_PL_S3_V5B_MIXED_INTERFACE`
4. `NO_GO_E4_PL_S3_V5B_THIN_REGIME`
5. `PROVISIONAL_GO_E4_PL_S3_V5B_STAGE4A_RERUN`

A pass authorizes preparation of a separately frozen Stage 4A reauthorization;
it does not execute or directly authorize Stage 4A.  S3 activation remains
unauthorized, ANYmesh remains untouched, qualified Q4 remains unchanged, and
the S3 default remains `legacy-s3`.
