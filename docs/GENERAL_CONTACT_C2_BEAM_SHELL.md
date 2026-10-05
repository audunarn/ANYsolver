# C2 interior round-beam contact on a physical S3/Q4 shell skin

This is a locally tested **development profile**, not accepted C2 contact. It
connects one classical B2 or B3 beam cell to one S3 V2D or planar qualified Q4 shell face through
`solve_static_nonlinear`. The beam has an explicitly declared round radius;
the shell uses its physical top or bottom skin, structural thickness and
reference-surface offset.

## Admitted model

- One explicit beam-to-shell interaction, with the beam as `surface` and shell
  as `target`. Use `ContactSurface(..., beam_radius=...)` and
  `ContactSurface(..., side="top" | "bottom")`.
- Isotropic elastic materials, concentric scalar B2/B3 section and von Karman
  structural route. The planar S3/Q4 face may undergo common translation; its
  rotations must remain fixed. Beam displacement uses its actual linear or
  quadratic curve. These are enforced model limits. Warped Q4s are rejected.
- Frictionless `normal_law="penalty"`, explicit `line_stiffness` in N/m²,
  dimensional `gap_tolerance` in m, and `beam_end_caps="none"`.
- `ContactSolverSettings(pair_motion="general",
  beam_shell_rim_clearance=..., beam_shell_difference_step=...,
  line_integration_relative_tolerance=...)`. Both clearances and the difference
  step are lengths in m. The rim clearance must cover at least the beam radius.
  `maximum_line_subdivisions` bounds integration work.

For an interior beam coordinate \(\xi\), the normal gap is the oriented
distance from the current centreline to the current physical shell plane minus
the beam radius. The active part of the beam is integrated over its **reference
length** using a line penalty potential. Each quadrature force goes to both
the beam and the original S3/P1 or Q4/bilinear physical face; the shell reference node also receives the
moment from its skin offset. An adaptive 8/16-point comparison controls the
reported line integration error. The exact quadratic beam-plane gap gives the
independent minimum-gap check.

The projected entire B2/B3 curve must remain inside the declared clearance
from each physical shell rim. A Bézier control-hull check makes this a
conservative whole-curve test for this planar convex face. Crossing the rim is
an explicit unsupported-geometry failure or trial cutback. There is no rim,
corner, end-cap or neighbouring-face force. A common shell translation fixes
the plane normal, so the endpoint gap and hull checks certify the linear trial
path used by this profile. The Q4 tangent is defined only on the admitted
common-translation manifold; independent nodal perturbations can warp a Q4
and have no admitted tangent. No claim is made for general shell deformation
or rotation.

The normal line force and shell force sum to zero; reported body moments are
about the global origin. The `general_contact` result includes `minimum_gap`,
`active_line_length`, `minimum_rim_clearance`, integration error, forces,
moments and `gap_tolerance_met`. A version-2 static checkpoint binds the
definition and numerical settings. Unresolved initial penetration is rejected.

## Example and evidence

Run [the beam-on-shell example](../examples/general_contact_round_beam_shell.py)
with an installed ANYsolver package; pass `--q4` to select the planar Q4.
Focused checks are in
`tests/test_general_contact_beam_shell.py`: analytic uniform closure, coupled
virtual work, smooth tangents including the shell offset rotation column,
curved B3 active interval, finite interior sliding, rim rejection, S3/Q4
static solves and checkpoint continuation, Q4 common-translation tangent,
and warped-Q4 rejection. These are local development checks.

Full C2 still requires general beam–shell segmentation and physical boundaries,
multi-cell beam topology, B3/beam pairs, moving rigid tools, refinement,
resource measurements and independent review. C1 paired-shell pressure-space
acceptance also remains open.

## Planar shell patch seam slice

The separate `CLASSICAL_B2_B3_ROUND_TUBE_PLANAR_SHELL_PATCH_LINE_PENALTY_STATIC_DEV_V0`
profile admits one B2 or B3 cell over 2–64 conforming, coplanar S3 V2D or qualified
Q4 faces. The faces must share material node IDs at every internal seam, have
one connected convex exterior, a continuous physical skin and one common skin
lever. The shell nodes undergo only common translation, with fixed rotations.
All other material, normal-law, stiffness, gap, radius and no-cap restrictions
above apply.

The actual B2 line is clipped against each current convex face. For B3, exact
roots of the quadratic signed distance to each face edge cut the deformed
curve into owned intervals; this admits repeated crossings of one seam. The
quadratic Bézier control hull provides conservative exterior-rim clearance.
The resulting disjoint reference-line intervals integrate through the original
S3/Q4 face interpolation. An exactly seam-aligned line has one deterministic
owner, selected by stable face ID. The exterior edges alone receive the
radius-covering clearance test. B2 endpoints or B3 Bézier controls certify
that clearance along the current centreline and admitted linear trial path.
An uncovered interval, nonconforming topology, overlap, nonconvex
exterior, incompatible orientation or discontinuous skin fails explicitly.
The tangent acts on B2/B3 translations and common shell translation, the admitted
motion manifold; it does not admit individual shell rotations or warping.

Run [the patch seam example](../examples/general_contact_round_beam_shell_patch.py),
using `--b3` for the quadratic beam route.
`tests/test_general_contact_beam_shell_patch.py` checks the independent
constant-gap line potential, paired global wrench, B2/B3 seam partition,
re-entrant B3 curve, slide, exterior-rim rejection, tangent, static route and restart. This is local
development evidence. General curved line–surface contact, nonconvex patches,
physical rims, beam caps, multi-cell beams and qualification remain open.
