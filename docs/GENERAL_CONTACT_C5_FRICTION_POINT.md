# C5 internal Coulomb traction-point component

`anysolver.general_contact.friction_point` is an internal, locally tested
component. Public `ContactInteraction` does not admit friction yet. A model that
needs shell or beam friction must still be rejected by general-contact
validation rather than routed through this component alone.

## Local contract

The geometry owner supplies a persistent material contact point, its partner
identity, an oriented orthonormal material frame with tangent axes in columns
1 and 2, the current compression-positive normal pressure, and the
source-relative displacement increment. The law projects that increment onto
the current tangent plane. Pressure and traction use Pa; displacement uses m;
`tangential_stiffness` uses Pa/m; stored energy and dissipation use J/m².

For a fixed pair of physical material points, the internal
`objective_relative_tangent_increment` helper can compute that increment from
committed/candidate positions and target material frames:

```text
R_t = F_target_candidate F_target_committed^T
delta_u_t = P_target_candidate [
    (x_source_candidate - x_target_candidate)
    - R_t (x_source_committed - x_target_committed)
]
```

Transporting the old separation before differencing removes apparent slip
when a finite normal opening rotates with both bodies. The caller must supply
the same source and target material points at both states. Neither this helper
nor the local return map differentiates a frame supplied by a deforming
element; the later coupled contact adapter must include those derivatives.

Given committed elastic slip vector `z_old` and frame rotation
`R = F_current F_old^T`, the trial elastic slip is

```text
z_trial = P_current (R z_old + delta_u_relative)
cap = mu * normal_pressure
```

For `k_t |z_trial| <= cap`, traction is `-k_t z_trial` and the point sticks.
Otherwise the local return is

```text
d = z_trial / |z_trial|
z_new = (cap / k_t) d
t = -cap d
delta_s_plastic = z_trial - z_new
delta_D = cap * |delta_s_plastic| >= 0
```

The returned displacement tangent is `-k_t P_current` in stick and
`-(cap / |z_trial|) (P_current - d d^T)` in smooth slip. The pressure derivative
is zero in stick and `-mu d` in smooth slip. These derivatives are not claimed
at activation or the stick/slip kink.

The candidate state is disposable. A Newton iteration or line-search trial
must always evaluate from the same physical committed state; only a fully
accepted structural increment may commit its candidate. Opening clears
elastic traction and reports released regularization storage. Recontact and a
changed partner start with zero elastic traction; accumulated physical slip
and frictional dissipation remain available for reporting.

Material-frame transport correctly rotates traction under a common rigid
spin, including spin about the normal, provided the supplied axes track the
same material chart. The component does not establish material-point
correspondence or transfer state across shell facets, clipped integration
cells, changing partners, or beam section coordinates. Those are required
before any frictional shell or beam profile can be admitted.

The internal `S3SkinMaterialPoint` composes the exact admitted S3 V2D
`S3SkinWorkAdapter` for one fixed barycentric point on a declared physical
skin. It evaluates position from the formulation's actual skin corners,
forms tangent axes from current material edges, and maps point force back to
authoritative translations and rotations through a sparse position map.
Numerical drill changes that leave the physical skin fixed leave its pose and
work unchanged. A collapsed or inverted skin fails explicitly. This map uses
the admitted small-rotation S3 skin kinematics; it does not extend the solver
to finite-rotation shell friction. Its `frame_directional_variation` returns
the exact smooth-pose derivative of both material tangents and the normal
through the S3 physical skin work map. Point migration between facets,
pressure-to-traction integration, a fully assembled contact tangent and the
committed history owner remain to be implemented.

Focused checks in `tests/test_general_contact_friction_point.py` cover an
independent scalar stick/slip slider, reversal, material spin and normal
rotation with zero relative work, pressure reduction, opening/recontact,
invalid state rejection, objective paired motion under common rigid rotation
with a finite gap, and directional tangents on smooth branches. The S3 point
checks in `tests/test_general_contact_s3_skin_work.py` cover physical offsets,
barycentric position and work, drill invariance, paired motion and geometric
rejection. These checks do not qualify coupled equilibrium, frictional moment
maps, finite sliding,
restart, or energy accounting for a full structural step.
