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
nor the local return map owns a deforming element frame. At fixed committed
points, `objective_relative_tangent_variation` includes the candidate
point-position variations, material-frame rotation of the old separation and
the variation of the current tangent projector. The S3 point adapter below
supplies these local chain-rule inputs. Pressure, projection coordinates,
overlap boundaries and contact-point history still need coupled derivatives.

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

`trial_coulomb_point_directional` includes changes in the material frame as
well as slip and pressure. With `w = R z_old + delta_u`, its internal trial
variation is `delta_z = delta_P w + P (delta_R z_old + delta_delta_u)`.
The traction variation is `-k_t delta_z` in stick and
`-mu delta_p d - (cap / |z_trial|)(I - d d^T) delta_z` in smooth slip.
It rejects activation and yield equality when a smooth derivative does not
exist; the later coupled solver must handle these transitions by active-set
or one-sided logic.

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

`S3FrictionPointPair` is an internal fixed-material-pair force map. It takes
two S3 points in one structural coordinate space, an explicit reference-area
weight and a **prescribed** normal pressure. It builds the derivative `J_slip`
of the elastic predictor, including transported retained elastic history, on relevant structural columns and
returns the physical nodal force `A_ref J_slip^T t`. This includes frame terms
that a direct `J_source^T t - J_target^T t` scatter would miss. It reports a
disposable friction trial and does not mutate physical history. At zero
pressure, it releases traction and avoids building a slip work map. The
required active-column budget is explicit. A caller must still establish
that both adapters belong to the same model; this internal map does not own a
model-bound topology contract.

The pair map is checked against finite-difference virtual work, equal and
opposite translation forces, common rigid translation/rotation null work,
offset rotational work, deterministic trial reevaluation, opening after
stored traction and resource rejection. It does not represent mortar pressure
integration or changing contact partners. Its optional
`numerical_tangent` is a **development fixed-pressure tangent**: the caller
supplies a positive step for every FE coordinate and an evaluation budget.
Each central difference uses the same committed structural/friction origin,
and a stick/slip branch change fails explicitly. Directional error is checked
with force and moment DOFs normalized separately. The tangent does not include
normal-pressure variation, changing contact projection, mortar integration
boundaries or history transfer; those derivatives remain required before
Newton admission.

Focused checks in `tests/test_general_contact_friction_point.py` cover an
independent scalar stick/slip slider, reversal, material spin and normal
rotation with zero relative work, pressure reduction, opening/recontact,
invalid state rejection, objective paired motion under common rigid rotation
with a finite gap, and directional tangents on smooth branches. The S3 point
checks in `tests/test_general_contact_s3_skin_work.py` cover physical offsets,
barycentric position and work, drill invariance, paired motion and geometric
rejection. `tests/test_general_contact_s3_friction_pair.py` covers the local
paired force map. These checks do not qualify coupled equilibrium, general
frictional moment maps, finite sliding,
restart, or energy accounting for a full structural step.

## Pressure-coupled static development path

`S3MaterialFrictionSettings` in `anysolver.general_contact.s3_friction_static`
declares fixed S3 material quadrature pairs, reference area weights, Coulomb
properties and dimensioned FE derivative steps. Pass it as `contact_friction`
to `solve_static_nonlinear` with an explicit `contact_path_program`, or as
`friction` to the shared `solve_static_contact_path`. No additional solver stack
is introduced. This is an explicit development profile, not an accepted general
shell-friction capability or application admission.

The contributor interpolates the existing shared mortar nodal pressure at each
source material quadrature point. Physical opening releases traction. The whole
source facet must remain within its single selected target facet, and the declared
quadrature weights must cover its reference area. A cut face fails even when all
quadrature points remain inside. Both-body physical slip work is
assembled with the opposite sign in the structural residual. Retained elastic
history contributes to the work map; omitting it produces a spurious common-spin
moment under nonproportional slip. The retained counterexample and its correction
are checked separately from collinear sliding.

Traction derivatives use the material-frame Coulomb chain rule, including pressure
variation. Numerical differences of mortar pressure and geometric work maps remain
bounded development derivatives. The explicit equality selection uses the stick
member of the generalized derivative; activation uses the open member. Only FE
columns reached by the actual constraint transformation are differentiated in the
solve; force and reaction rows on both bodies are retained. Standalone work/tangent
checks use all physical columns.

Every candidate starts from the same accepted structural/friction origin. All
friction states are prepared and validated before structural commit, then published
without evaluation before reaction recovery. Restart binds quadrature identities,
properties, numerical settings, committed pose, partner and material frame.
Per-increment records distinguish traction, dissipation, storage and released
regularization storage.

This slice does not implement changing material partners, facet transfer, mortar
friction integration over moving overlap, curved/warped geometry, nonlinear
materials, beam friction, arc length or impact friction. Those remain required C5
work. Its fixed quadrature weights and derivative steps are explicit controls;
neither is an application default. Engineering acceptance remains open.
