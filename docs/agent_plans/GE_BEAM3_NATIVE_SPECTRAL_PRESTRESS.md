# Native generalized current-state boundaries and critical-load development

Base 31d1ca5019ba99aeb123e5f3619ec28ceaea4a12. Freeze this plan and
tests/test_ge_beam3_native_spectral_prestress.py. No production module,
mechanical coefficient, tolerance, mass rule, solver kernel or default changes.

## Local hardening: three tests

- Construct real committed uniform axial states at the one-dimensional
  yield boundary and after plastic flow. Require the current-rest modal path
  to reject them without changing accepted history or material-store state.
- Solve the same registered curved conservative load case. While a subsequent
  native trial is pending, inspect its committed current-rest pencil; require
  unchanged issued validator, pending trial, accepted history and generation.
  Independently integrate finite-deformed lifted velocity work at 64 points
  and compare with the fixed 24-point mass to normalized 1e-11.

## Prestress/buckling: four separate one-test inventories

Use straight, clamped-free, uncoupled chains with 1, 2, 4 and 8 macrocells,
length 2, axial rigidity 1000 and weaker bending rigidity 1, exactly as in
the preceding native-modal fixture. No adjustment after seeing results.

For each compression P, prescribe the analytically known uniform axial
strain -P/EA at the nodes, solve the actual internal stationary equations
through assemble_distributed_trial, and commit through the real native store.
Verify the end actions against the independent one-dimensional constitutive
formula and require zero free equilibrium residual with the actual tip force.
This is a manufactured exact axial equilibrium, not a claim that a global
Newton loading programme was executed. Do not forge/reseal an accepted state.

Require tensile stiffening and compressive softening using P=-0.5PE,0,0.5PE.
Bracket the first signed modal eigenvalue's zero crossing in [0,2PE], then
perform exactly 18 bisections, creating fresh state/model instances per point.
Require positive lower and nonpositive upper roots, normalized bracket width
below 1e-5, and eight-macrocell critical-load error below 2% against
PE=pi^2 EI/(4 L^2). Coarser cases report discretization error diagnostically.

The independent Euler expression is the classical clamped-free reference,
also given in MIT's Unified Engineering problem-set solution, equation (2):
https://live.ocw.mit.edu/courses/16-001-unified-engineering-materials-and-structures-fall-2021/mit16_001_f21_pset12_sol.pdf
This bibliographic background is not independent authorship of the discrete
checker. The finite-shear/extensional candidate is compared to this slender
reference; no coefficients are fit to it.

Save each actual parameter, equilibrium/state identity, full current-rest
pencil and signed eigenpair externally. The load bracket is the critical-load
estimate; an individual squared frequency is never reported as a load factor.
Do not clip negative roots or silently drop a failed algebraic block.

## Bounded execution and evidence

Each of the five inventories gets one clean frozen rehearsal and two
fresh-directory repeats only after all rehearsals pass. At most three
concurrent processes; one numerical thread, 24 GiB process-tree limit,
600-second child wall, 120-second CPU-inactivity bound, 1800-second wave.
Progress before each preload and after each spectrum. No automatic retry.
Require both child/supervisor success and byte-identical scientific files
within each inventory. Preserve failed/partial evidence, never create an
absent passing assessment. Keep all five inventory counts separate.

An accepted result is development evidence for these current-state safety
and straight axial-preload buckling cases only. Independent review remains
PENDING. Bending/curved continuum frequencies, broader buckling paths,
nonlinear spatial stability/postbuckling, extreme slenderness/contrast,
practical scale, general material/support/load/state parity, installed public
integration and objective beam-shell qualification remain part of the full
goal. Existing B2/B3/Q4/S3 mechanics and defaults remain unchanged.
