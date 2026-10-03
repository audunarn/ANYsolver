# Deforming S3 source and target impact — development profile

**Implemented, source-tested and installed-tested. Not independently accepted or
released.** This extends the normal-motion development route; it does not complete
C6 or admit general shell impact.

## Use

Run `examples/general_contact_deforming_s3_impact_dev.py --output result.json` from
the repository with ANYsolver installed. It uses the ordinary `TransientConfig`
and `solve_transient_contact` with
`ContactTransientSolverControls(allow_normal_s3_skin_hermite_dev=True)`.

The profile is `NORMAL_NODAL_S3_SKIN_HERMITE_NEWMARK_EVENT_DEV_V2`. Two elastic S3 V2D
surfaces interact through the existing full Jet2 projected-penalty contributor.
The source contains two triangles and the target one larger triangle in the
tested fixture. All seven physical normal nodal coordinates remain in the shared
Newmark system; source deformation changes the normal and normalized gaps.
Forces are not replaced by a reduced reference model or the affine pressure
sidecar used by the older uniform-source profile.

## Contracts and limits

- Explicit opt-in; separate from the existing guided/fixed-projection profiles.
  Exact admitted normal nodal translations, zero shell rotations and zero
  tangential motion. Reference skins occupy exactly parallel planes. Isotropic
  elastic S3 V2D, fine P1 pressure, projected penalty and positive physical reduced
  mass are required. Existing solver defaults and sphere APIs remain unchanged.
- Newton iterates on acceleration, with displacement linked by the same
  average-acceleration Newmark equation. This avoids subtracting nearby positions
  and dividing by the square of a short step.
- Actual mapped endpoint skins and rates supply a rational Bernstein enclosure
  of each represented cubic Hermite path. Original analysis reference normals
  retain polarity across successive steps. Every source face must resolve within
  finite panel/depth and penetration budgets before physical commit.
- A separate reference-P1 pressure-phase proof bounds weighted gap and support
  over moving projected overlap. Exact rational Bernstein and Cramer bounds keep
  original pressure functions and reference measure on subdivision children.
  Shared-node quantities accumulate across faces before testing joint
  `W+tau*S >= 0` for open modes or `W-tau*S <= 0` for closed modes. No division
  by vanishing support, deletion of small positive supports or added pressure
  unknowns is used. Cells outside different target edges remain unresolved;
  only one common outside edge excludes a cell.
- Opposite endpoint phases trigger the shared bounded endpoint localizer. Every
  proposed duration is reequilibrated from the same committed origin. Complete
  pressure-phase and physical-path proofs are required before commit, including
  paths whose endpoints alone conceal an interior excursion. The tested fixture
  now reports four localized pressure events. Endpoint, Newton-stage, cell,
  temporal-panel and depth budgets are finite and restart-bound.
- Bounds cover complete represented faces/corners, including portions outside
  projected overlap. A tilted source and larger target can therefore cause a
  conservative cutback even when the physical overlap is open. Finite budgets
  end unresolved paths explicitly; contacts are not discarded.
- V14 restart binds the profile, definitions, ordered pressure feature identity,
  physical/pressure sweep budgets and endpoint localization controls. It stores committed
  coordinates/rates, not an invented affine pressure-event state. Rejected proof,
  cancellation and exception paths use shared cleanup/cutback infrastructure.
  Historical developmental V13 checkpoints are incompatible with this new
  algorithm and rejected; existing V1–V12 profile selections remain unchanged.
- General rotations/sliding, warped Q4 dynamics, unrestricted algebraic shell
  rotations, nonlinear material contact, friction and engineering impact
  acceptance remain separate programme work.

## Named verification

The independent contact oracle solves covered-triangle projection equations,
integrates P1 gaps analytically and differentiates them by complex step. Both
source faces contribute before the common nodal pressure law. The accepted S3
structural stiffness is an input to the dynamics references; this does not
independently qualify S3 spatial mechanics.

Local full/partial active checks cover gap, both-body virtual work, wrench and
directional tangent. Independent nonlinear Newmark and continuous DOP853
references cover the seven-coordinate trajectory. One 25→12.5 µs halving reduces
displacement error on the 200 µm scale from 0.04874% to 0.01196% and velocity error on
the 0.1 m/s scale from 0.4702% to 0.1183%. Reachable-coordinate energy defects are
7.22e-9 and 7.59e-9; the failed strict per-halving improvement assertion is retained.
A separate prospective event-tolerance refinement at fixed 25 µs reduces that
defect from 7.22e-9 to 1.41e-10 (gap/time tolerances 1e-10→1e-12 in SI).
This separates trajectory and event error; it is not monotonic temporal energy
qualification. Conservative penetration is below 12.23 µm against the
20 µm development budget. Storage accounting is labelled separately from the
projected contributor's `penalty_energy_j` field.

Active/open restart, incompatible identity/settings, exact motion rejection, actual
mapped hidden approach, shared pressure-mode excursions, partial overlap, tiny
positive/absent support, second-face proof failure, cutback and in-proof
cancellation have focused checks. Actual stage-budget exhaustion restores model
and owner; rejected localized endpoints report their actual query/stage work.
The named installed example matches every result field and all 233 imported source
hashes: 123 states, four localized events, zero cutbacks, 60 endpoint queries and
297 Newmark stages. These establish the stated
development observations, not full-contact scientific acceptance or a speedup.

[Current event evidence and retained failures](d1_review_support/C6_S3_PRESSURE_EVENT_SLICE_20261003.md).
[Historical V1 evidence](d1_review_support/C6_DEFORMING_S3_DRIVER_SLICE_20261003.md)
remains unchanged. Substantial moving clipped-overlap dynamics still lacks an
independently checked trajectory and is the next development question.
