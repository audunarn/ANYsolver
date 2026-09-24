# General contact C1 development slice: guided planar Q4/S3 pair

This is an exploratory end-to-end pair force map, **implemented and locally
tested**, without independent engineering acceptance. It does not complete C1
or admit finite sliding. The public validator reports the exact profile
`PLANAR_Q4_PAIR_NORMAL_TRANSLATION_PENALTY_MORTAR_V0` for Q4/Q4 and
`PLANAR_Q4_S3_PAIR_NORMAL_TRANSLATION_PENALTY_MORTAR_V0` when S3 is present.

## Admitted model

- Two explicitly named, disjoint qualified planar E4-PL Q4 or S3 V2D shell
  surfaces; one integration side and one target side. Q4/Q4, Q4/S3 and S3/S3
  pairs, nonmatching meshes and partial projected overlap are supported at
  the reference pose. Each named surface must occupy one physical plane.
- Each face may move only by a uniform translation along the common fixed
  normal, plus a common tangential translation of both bodies. Relative
  lateral movement and shell rotations are rejected at candidate evaluation.
  Boundary conditions must enforce these restrictions.
- Physical top/bottom sides must face the opposing surface. An outward-facing
  side selection fails validation; a midsurface has no outward-side test.
- Physical top, bottom and midsurface selections use each formulation's
  reference director and fixed thickness. S3 V2D also uses its declared
  reference-surface offset. Offset force couples are assembled on the actual
  shell rotational coordinates, although finite rotations are outside this
  profile.
- One frictionless penalty interaction under `von_karman` nonlinear static
  force or displacement control. `normal_stiffness` is pressure per gap
  (Pa/m); `gap_tolerance` is a positive length in metres. Initial physical
  penetration is rejected.
- Version-2 static checkpoints bind the pair definition, law, settings and
  structural model. They carry an empty physical contact state for this
  frictionless penalty profile. Q4/Q4 and S3/Q4 continuations have local
  restart checks.
- Augmented enforcement, self-contact, warped Q4, finite sliding and shell
  rims are still unavailable.

The present all-pairs overlap search has an explicit candidate limit and
raises a resource error rather than dropping contact. It is a development
kernel, not the deterministic hierarchy required for production C1.

An internal trial-pose adapter can now recompute planar Q4/S3 physical faces
and projected overlap under relative sliding. The coupled pair law in this
profile still uses its fixed reference overlap and rejects relative lateral
motion. Candidate-pose overlap alone does not establish the moving-domain
residual or tangent. The internal geometry kernel also computes the
smooth-branch overlap-area derivative from clipped face edges. Shared-edge
and topology transitions need one-sided treatment in the later coupled law.
An internal rigid-translation control differentiates the corresponding
constant-gap penalty potential through its complete moving overlap, including
the overlap-area Hessian. It provides an analytical reference for the later
deformable-shell residual and tangent; it is not routed through the public
pair solver.
An internal moving Q1/P1 pressure state now computes positive support,
weighted gaps and both-body normal work on one current common-refinement
polygon. Its normal tangent is complete at fixed tangential translations.
Its reported vertex gap is a sample, not a certified physical minimum for a
nonuniform bilinear gap; the full geometric gap check remains a C1 gate.

## Discrete pair law

The common-refinement polygon of each projected pair is integrated on the
original Q4 bilinear or S3 linear faces. Nonnegative Q1 or P1 functions on
the integration surface carry the pressure coefficients. With positive reference
support `m_a`, weighted gap `gbar_a` and normal stiffness `k`, the discrete
potential is

```text
m_a      = integral_overlap N_a dA0
gbar_a   = (integral_overlap N_a g_n dA0) / m_a
Pi_c     = (k/2) sum_a m_a min(gbar_a, 0)^2
```

The residual and tangent differentiate that same potential with respect to
both shell bodies. The integration and target forces are equal and opposite.
For the admitted fixed overlap, the gap is affine in the permitted normal
translations. A common lateral translation leaves the pair contact work
unchanged. Independent polygon-vertex gap checks and analytic trial-step
limiting enforce the requested gap budget. The pressure-space constraint is
weak; a later C1 profile must qualify partial contact and resolution under
finite sliding.

## Example and evidence

Run the [guided nonmatching pair](../examples/general_contact_guided_pair.py)
from an environment containing this checkout. The two lower Q4 elements and
one upper Q4 element initially touch at their physical skins. The prescribed
0.4 N force gives a 0.4 N pair reaction and a -0.4 micrometre penalty gap.

Focused geometry and pair checks are in `tests/test_general_contact_overlap.py`
and `tests/test_general_contact_pair.py`. The coupled static check currently
uses S3 on the integration side against Q4; the other mixed combinations have
local force-map checks. Independent review, registered mesh/enforcement
qualification and the C1 finite-sliding handoff remain open.
