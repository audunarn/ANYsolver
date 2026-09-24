# General contact C1 development slice: guided planar Q4 pair

This is an exploratory end-to-end pair force map, **implemented and locally
tested**, without independent engineering acceptance. It does not complete C1
or admit finite sliding. The public validator reports the exact profile
`PLANAR_Q4_PAIR_NORMAL_TRANSLATION_PENALTY_MORTAR_V0`.

## Admitted model

- Two explicitly named, disjoint qualified planar E4-PL Q4 shell surfaces;
  one integration side and one target side. Matching and nonmatching meshes
  and partial projected overlap are supported at the reference pose.
- Each face may move only by a uniform translation along the common fixed
  normal. Shell rotations and lateral movement are rejected at candidate
  evaluation. Boundary conditions must enforce these restrictions.
- Physical top, bottom and midsurface selections use the formulation's
  reference director and fixed thickness. Offset force couples are assembled
  on the actual shell rotational coordinates, although finite rotations are
  outside this profile.
- One frictionless penalty interaction under `von_karman` nonlinear static
  analysis. `normal_stiffness` is pressure per gap (Pa/m); `gap_tolerance` is
  a positive length in metres. Initial physical penetration is rejected.
- Pair contact restart, augmented enforcement, self-contact, warped Q4,
  finite sliding, shell rims and S3 force mapping are still unavailable.

The present all-pairs overlap search has an explicit candidate limit and
raises a resource error rather than dropping contact. It is a development
kernel, not the deterministic hierarchy required for production C1.

## Discrete pair law

The common-refinement polygon of each projected Q4/Q4 pair is integrated on
the original bilinear faces. First-order, nonnegative Q1 functions on the
integration surface carry the pressure coefficients. With positive reference
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
translations. Independent polygon-vertex gap checks and analytic trial-step
limiting enforce the requested gap budget. The pressure-space constraint is
weak; a later C1 profile must qualify partial contact and resolution under
finite sliding.

## Example and evidence

Run the [guided nonmatching pair](../examples/general_contact_guided_pair.py)
from an environment containing this checkout. The two lower Q4 elements and
one upper Q4 element initially touch at their physical skins. The prescribed
0.4 N force gives a 0.4 N pair reaction and a -0.4 micrometre penalty gap.

Focused geometry and pair checks are in `tests/test_general_contact_overlap.py`
and `tests/test_general_contact_pair.py`. They include Q4/S3 and S3/S3
*overlap geometry* checks, but those combinations have no coupled contact
admission yet. Independent review, registered mesh/enforcement qualification,
restart, and the C1 finite-sliding handoff remain open.
