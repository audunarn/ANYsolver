# P5 analytical prestress and discrete buckling diagnostic — 2026-09-06

Research successor to `cc0ca003bf9d3d780c9f498d621a26a11b6199a8`, tree
`dc3f89845c32cda0c9b816e8aede567b3b6fe42d`. The preceding one- and two-element
postcritical seed failures remain preserved. Neither failed solve is repeated
or reclassified here. This separate diagnostic evaluates a known straight
equilibrium and its second variation, not the failed deformed seed path.

## Analytical state and unchanged mechanics

The reference is a straight length-2 cantilever with material axis 2=global z
and C=diag(EA,GA,GA,2*EI,EI,2*EI). The default values remain EA=1000, GA=400,
EI=1. Positive P denotes compressive spatial dead force at the free end;
negative P denotes tension. At reference coordinate X in [-1,1], supply

    x=-1+(1-P/EA)*(X+1), y=z=0,
    shared nodal U=I, cell rotations=I, endpoint moments=0.

This homogeneous state has axial force -P and no shear or bending. The probe
evaluates the existing 36-coordinate mixed potential directly, without invoking
the local Newton solver. It checks local stationarity and the negative moment
block, then the cell-rotation Schur block. Only after local definiteness checks
does it condense the internal variables and scatter the 18-coordinate element
operators. Global force balance and tangent symmetry must pass at the unchanged
1e-11 normalized scale. Positive axial stretch is mandatory.

Local loss of stationary-block definiteness raises a distinct diagnostic; it
is not silently treated as global buckling. Negative free global eigenvalues
are retained and are not removed by a stiffness shift, damping or stabilization.
The constrained first node removes the six rigid motions for the critical-load
comparison. No mass or dynamic modal interpretation is introduced.

## Critical-load calculation and numerical limits

The source-bound finite-compliance continuum critical load from the preceding
reference is 0.6162805724521121. A zero-to-twice-continuum-load interval brackets
the first observed free-stiffness sign change for this case. For each mesh,
congruence scaling uses the positive zero-load stiffness diagonal and remains
fixed throughout the calculation. Thirty-two bisections locate the change;
the helper allows at most forty and rejects an unresolved width above 1e-8
times the continuum load. Each evaluation is a direct stationary-state Hessian
evaluation, not a seeded nonlinear iteration.

These are binary64 sign brackets and eigenvalue diagnostics, not rigorously
rounded intervals, exact rank/PSD certificates or a proof excluding all possible
earlier modes in other parameter families. No broad section/slenderness claim
follows from this one diagonal-section case.

| Elements | Lower load | Upper load | Relative critical-load error (%) |
|---:|---:|---:|---:|
| 1 | 0.6485342301382502 | 0.6485342304252282 | 5.233600 |
| 2 | 0.6242330406030694 | 0.6242330408900474 | 1.290397 |
| 4 | 0.6182612343752452 | 0.6182612346622232 | 0.321390 |
| 8 | 0.6167752645626765 | 0.6167752648496545 | 0.080271 |

Errors decrease monotonically in this sequence; the eight-element estimate is
well within the development 2% engineering comparison criterion. This does not
authorize a production formulation or replace independent qualification review.

## What this says about the seed failures

The previous comparison force was 0.6449785996190569. Direct free-stiffness
minimum eigenvalues at that force were approximately:

| Elements | Minimum global eigenvalue | Minimum local rotation-Schur eigenvalue |
|---:|---:|---:|
| 1 | 0.0010386833833526555 | 24 |
| 2 | -0.004196664258558435 | 48 |
| 4 | -0.003211819412508259 | 96 |
| 8 | -0.0018548026676011963 | 146.0160932651857 |

The one-element comparison is below that mesh's discrete critical load, despite
being above the continuum critical load. This establishes an onset mismatch,
not a proof that no remote/subcritical coarse buckled equilibrium exists and
not a reconstruction of every cause of the earlier solver failure.

The two-element comparison is above its discrete critical load. Its local
blocks are admissible at the straight state, but this says nothing definitive
about their condition along the failed deformed seed iterations. That seed
failure remains unresolved and must be diagnosed separately. The four/eight
postcritical comparisons already recorded remain unchanged.

## Tests and preservation

- New suite: **10 passed in 11.07 seconds**, with one numerical-library thread.
  The earlier coarse-only version passed nine tests in 3.62 seconds; extending
  the same diagnostic to four/eight elements and adding local-failure mutation
  produced ten passing tests. No failed seed was retried by these tests.
- Existing postcritical-reference and continuation suites: **37 passed in
  12.96 seconds** (22 reference and 15 continuation tests).
- Checks distinguish local/global signs, independently re-evaluate the reported
  sign-bracket endpoints with the same registered congruence, forbid local
  Newton calls, and verify global equilibrium and tangent symmetry. A selected
  transverse mode stiffens under tension and softens under compression.
- Injecting a bad local moment block yields a local stationary-block error, not
  a global critical-load result. Invalid counts, nonpositive compressed stretch
  and exhausted bisection bounds fail closed.

These are small bounded correctness tests, not performance measurements or a
formal resource qualification wave. No consumed resource request or historical
scientific certificate was rerun, modified or promoted.

Inspected implementation SHA-256:
`CDC0315E3A8817A2ED1AD6BF161092E24A163D103E71A61C7534D9D525AF876F`.
Inspected test SHA-256:
`CBE28CE693C3E031DDC1385BF5B6B09EC0376ED637BFF1FFC98C988BD260C59E`.

## Next work and full-goal status

Use a separately declared diagnostic to locate the two-element deformed-seed
failure: distinguish local stationarity, block conditioning, branch selection
and global correction before changing a solver. Preserve the exact old case,
residual scales, tolerances and outcome. Source-based improved initial guesses
may be studied as solver changes, not empirical stiffness changes.

Critical-load accuracy still needs wider section/slenderness coverage and
independent review. Curved reference postcritical cases, general nonlinear
section adapters, controller persistence/cutback, prestressed modes, dynamics,
installed-wheel integration and objective eccentric/curved beam-shell joints
remain open. The overall goal is not complete or blocked.

Only this record, the new research diagnostic and its test are added. No src,
existing B2/B3/Q4/S3 mechanics, defaults, production recovery/state, package,
dependency, workflow or accepted qualification evidence changes. No push,
merge, release or activation. `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
