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

Focused checks in `tests/test_general_contact_friction_point.py` cover an
independent scalar stick/slip slider, reversal, material spin and normal
rotation with zero relative work, pressure reduction, opening/recontact,
invalid state rejection and directional tangents on smooth branches. They do
not qualify coupled equilibrium, frictional moment maps, finite sliding,
restart, or energy accounting for a full structural step.
