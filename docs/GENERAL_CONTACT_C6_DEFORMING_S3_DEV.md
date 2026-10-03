# Deforming S3 source and target impact — development profile

**Implemented, source-tested and installed-tested. Not independently accepted or
released.** This extends the normal-motion development route; it does not complete
C6 or admit general shell impact.

## Use

Run `examples/general_contact_deforming_s3_impact_dev.py --output result.json` from
the repository with ANYsolver installed. It uses the ordinary `TransientConfig`
and `solve_transient_contact` with
`ContactTransientSolverControls(allow_normal_s3_skin_hermite_dev=True)`.

The profile is `NORMAL_NODAL_S3_SKIN_HERMITE_NEWMARK_DEV_V1`. Two elastic S3 V2D
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
- A hidden-approach guard watches each original corner pair certified open at
  both endpoints. It is **not** an event exclusion certificate for all material
  points or weak pressure modes. Exact non-affine pressure-event localization is
  not supplied. The event-time result field is empty for this profile.
- Bounds cover complete represented faces/corners, including portions outside
  projected overlap. A tilted source and larger target can therefore cause a
  conservative cutback even when the physical overlap is open. Finite budgets
  end unresolved paths explicitly; contacts are not discarded.
- V13 restart binds the profile, definitions, ordered pressure feature identity,
  physical sweep budgets and hidden-approach tolerance. It stores committed
  coordinates/rates, not an invented affine pressure-event state. Rejected proof,
  cancellation and exception paths use shared cleanup/cutback infrastructure.
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
displacement error on the 200 µm scale from 0.04845% to 0.01212%, velocity error on
the 0.1 m/s scale from 0.4702% to 0.1183%, and reachable-coordinate energy defect
from 0.07343% to 0.04507%. Conservative penetration is below 12.23 µm against the
20 µm development budget. Storage accounting is labelled separately from the
projected contributor's `penalty_energy_j` field.

Active/open restart, incompatible identity/settings, exact motion rejection, actual
mapped hidden approach, second-face proof failure, cutback and in-proof
cancellation have focused checks. The named installed example matches every
result field and all 232 imported source hashes. These establish the stated
development observations, not full-contact scientific acceptance or a speedup.

[Evidence and retained failures](d1_review_support/C6_DEFORMING_S3_DRIVER_SLICE_20261003.md)
