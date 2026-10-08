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

## Planar material-anchor development route

`S3SlidingFrictionSettings` in `anysolver.general_contact.s3_sliding_friction`
uses the same `contact_friction` argument and ordinary static path. Its target is
a connected conforming convex planar S3 patch; the whole source face remains in
the target union. Three positive reference-area quadrature points per source face
have stable material identities. The target facet and barycentric material anchor
are history: changing facets does not release traction or reset cumulative slip.
The original fixed-pair profile remains selectable and unchanged.

With source point x, committed target material anchor alpha, and current target
interpolation X(u,alpha), the trial elastic gap is

    e_trial = P [x(u) - X(u,alpha)], P = I - n n^T.

Stick retains alpha. Slip returns to an elastic gap of length mu*p/kt in the trial
direction and locates the resulting interacting point on the current target patch.
Both target stretch/shear and rigid motion convect the anchor through the actual
interpolation. Initial activation/recontact initializes a stress-free anchor at the
current projection under the historical endpoint rule; physical opening releases
the anchor and stored traction. The explicit first-touch option below initializes
at the represented touch stage instead.
At zero pressure with negative gap, the return retains a zero-elastic-gap material
anchor. This finite-step initialization needs event/step refinement before general
friction admission.

The physical virtual work holds the trial returned anchor fixed as an internal
variable. For r=x-X, g=n.r, Js=dx/du and Jt=dX/du at fixed material coordinates:

    De = P (Js-Jt) - (n r^T + g I) Dn,
    R_friction = -sum(area_reference * De^T traction), traction = -kt*e.

The patch normal is the normalized sum of oriented triangle area vectors; Dn
differentiates that same sum. Internal diagonals cancel in both definitions.
An earlier candidate used a normal from the first facet but a derivative from the
anchor facet; the independent review identified this mismatch, and focused apex/
seam work checks cover its correction. Geometry and return derivatives are local
development work, with bounded full-return finite differences assembled sparsely;
candidate perturbations share one physical committed origin.

Roundoff-sized seam ties use stable element-ID ownership. The admission tolerance
does not snap a finite-width return band. Residuals and one-sided slopes have focused
checks. The internal-seam tangent now selects the stable-ID physical return facet
at the base candidate and differentiates that same facet's affine equations for
every FE column. Probe shape coordinates may be negative within the explicit
`maximum_probe_barycentric_change` bound, but they are disposable and return no
physical histories. Physical candidates/commits keep strict patch coverage and
nonnegative anchor coordinates. One-sided force and moment checks and an actually
solved normal-response path landing at the seam cover this construction. The
physical-rim generalized tangent remains rejected. Unresolved slip directions or
derivative resolution cause explicit non-success, with no law switch or budget growth.
The new tangent identity/probe controls bind restart; prior checkpoints with the
older derivative contract require a compatible migration rather than silent reuse.

Records identify force per source reference area and the shared mortar pressure
coefficient. Endpoint pressure times the current anchor-motion chord is the discrete
Coulomb dissipation measure. Storage, storage change, released storage, return
storage drop and the return's projection loss are separate fields. It is not a
continuous path-work certificate. Common affine stretch of a *nonzero* spatial
elastic gap can trigger a return; a retained discriminator shows this contribution
scales as 1/kt at equal traction. It is an exposed regularization consequence,
requiring enforcement/step sensitivity before engineering admission.

For the installed example, import `run_example` from
`examples/general_contact_s3_friction_static.py` and call
`run_example(material_anchor=True)`. The target's in-plane response is solved,
and source quadrature/anchors cross the artificial target diagonal before reversal,
opening and stress-free recontact. Default `run_example()` preserves the fixed-pair
example. Restart binds geometry, quadrature, properties, derivative controls,
initialization rule, committed pose and anchor/history; incompatible definitions
and inconsistent stored elastic energy are rejected before mutation.

Reference-cell friction integration is now explicitly selectable with
`source_quadrature_refinement`: level0 preserves the original three-point rule;
each level divides every reference triangle into four cells and applies the same
positive three-point rule. Level3 gives192 persistent material points per source
face. The material-anchor example explicitly selects level3. The default remains
level0 for compatibility, and is not an accuracy recommendation. A separate
`maximum_material_points` cap is checked before allocation. Point coordinates,
weights and refinement settings bind restart; changing them during continuation
is rejected. Refinement does not add normal pressure unknowns or repartition
history within an increment.

An independent constant-traction fixture integrates the target-node shape
`max(A-B*bary0,0)` exactly, using the triangle density `2*(1-bary0)` and a separate
scalar quadrature check. The original three-point rule has8.47446% error at the
selected target-node force despite correct total force. This failure is retained.
The refined candidate must meet the unchanged case-specific0.2% integration
budget, with positive first/second reference moments, complete target-force
distribution, directional derivatives, solved deformable-target history and
restart checks. This case alone is not a general integration-error estimator.
Cached physical maps use only participating FE columns; full reaction rows remain
and local tangent blocks scatter sparsely. Direct full-map comparisons and
constrained-reaction checks cover that optimization. See
[integration slice evidence](d1_review_support/contact_c5_s3_quadrature_20261002/results.md).

### Activation within an increment

`activation_history="endpoint"` preserves the historical development selection.
It misses post-touch sliding during simultaneous approach/sliding: the retained
one-step slider failed with essentially0N instead of the independent.12N.
`activation_history="linear_constant_normal_touch_dev"` is an explicit alternative;
the material-anchor example now selects it. Its physical increment path is
`u(alpha)=u_committed+alpha*(u_candidate-u_committed)` on the admitted affine skin
maps, with constant target normal. This interpolant defines the history update;
it is not the exact intervening equilibrium trajectory.

Quadratic whole-path extrema check target facet orientation, convexity and source
corner coverage. Normal-parallel coefficient bounds use the minimum represented
facet area, so a large step does not loosen the angular tolerance. A rotating
target normal, mid-path collapsed facet or unresolved path fails explicitly.
Under these conditions a point's signed gap is affine: its first closing fraction
is `g0/(g0-g1)`. A stress-free material anchor is located on that stage target and
convected through the actual target interpolation to the endpoint before return.
The residual holds the returned anchor fixed; disposable tangent probes recompute
the touch fraction and stage material coordinates on the same selected event
facet. `maximum_probe_touch_fraction_change` and the material-coordinate bound
limit those probes. Physical candidates retain nonnegative coordinates; probes
return no histories. Rim-reaching derivative probes explicitly reject.

The exact slider hasg=.015−.02*tau andx=.1*tau, hence touch at.75. Its normal
pressure is20*(tau−.75), elastic-gap slope.006 and plastic-slip slope.094.
Endpoint reaction is.12N and continuous dissipation.00141J. The new rule recovers
the reaction in one step. The existing endpoint-pressure/chord measure still gives
`D_N=D_exact*(1+4/N)` forN divisible by4; measured errors are100%,50%,25%,12.5%
and1.5625% atN4,8,16,32,256. It does not make coarse-step work exact. An independent
stick reaction derivative−.6N/m and1e-5 directional checks include moving-event
sensitivity. Recontact/path identity and controls bind restart; changing the rule
on continuation rejects. See [activation evidence](d1_review_support/contact_c5_s3_activation_20261002/results.md).

This bounded stage rule does not admit moving-normal/finite-rotation activation,
partial overlap, general swept collisions, adaptive history repartitioning or
continuous work without measured step refinement. Those programme rows remain.

The interacting-material-point idea is informed by
[Duong and Sauer (2019), contact kinematics](https://arxiv.org/html/1808.10420).
ANYsolver retains its own normal mortar law and derives the above work maps; this
is not adoption or qualification of that paper's full discretization. No external
contact code was copied. Partial overlap/history repartitioning, adaptive friction
integration, finite rotations/creases, nonlinear materials, swept beam/native
friction, arc length and impact friction remain required C5 work.

## Partial-overlap replay candidate — development only

`S3ReplayFrictionSettings` selects an internal experimental material-coordinate
history owner. It is not an accepted application capability. The existing
full-coverage owner and its evidence remain separate.

With `event_subdivisions=0`, replay uses the endpoint return and rejects hidden
contact intervals. Positive subdivisions select event-resolved returns using
actual stage mortar pressures, with bounded stage evaluations and temporal
refinement still required. Histories are reconstructed from accepted poses;
candidate quadrature indices never identify physical history. Reference-cell
partitioning, pressure integration and event-time refinement are distinct.

Independent pulse work, point-query independence, both-body work, resource
rejection and local pressure-specialization checks pass in development. The
complete coupled route exhausted routine resource limits. The named integrated development run accepted press and partial slide, then
exhausted its pressure-stage cap during reversal. No C5 acceptance, installed
handoff or speedup for the complete workflow is established. See the
[derivation, limits and evidence](d1_review_support/contact_c5_s3_partial_replay_20261002/event_integration_development.md).

Subsequent bounded development completed the original nonguided five-increment
press/slide/reverse/open/recontact route in513.90s (224055296B process peak), with
all five physical commits and a saved final checkpoint. Exact material-history
reuse and certified-separated candidate integration reduce repeated work;
canonical full-domain commit/restore retains complete history and partitions.
The same retained tangent fell from622.763s to55.503s, with force/tangent differences
within existing checks. This is local development performance, not whole-route
qualification. Split restart matches the saved full checkpoint exactly; temporal,
spatial/thin-transition refinement, independent acceptance and installed handoff
remain required. Historical failures remain failures. See
[current evidence](d1_review_support/contact_c5_s3_partial_replay_20261002/history_cache_development.md)
and [full workflow result](d1_review_support/contact_c5_s3_partial_replay_20261002/separation_full_v1_result.json).


Additional fixed-path development controls: an independent proportional-pressure
slider converges in work (8/32/128events:11.72/3.08/.78% error). Replaying saved
five-increment FE paths changes total dissipation0.83% from4 to32events; spatial
control changes~0.00007%. Halving the same affine segments changes refined work
0.016%. These do not establish re-equilibrated trajectory convergence or arbitrary
cut accuracy. Thin mixed-stick/slip tangent bias now triggers one resource-bounded
canonical-partition retry with unchanged integration/tangent gates; cancellation
restores an unvalidated retry policy. Refer to the linked current evidence.

The step-partition comparison now binds identical physical-path/pressure/settings
and quadrature coordinates/weights explicitly. Its assertion concerns total
dissipation only; released storage changes7.9% from4 to32events. No claim that all
work quantities meet the same relative accuracy follows. Original unbound records
and the review finding remain in the evidence directory.


A standalone [partial-replay example](../examples/general_contact_s3_partial_friction.py)
now exposes the nonguided five-phase path and checkpoint continuation. Its first
press/checkpoint plus12focused mechanics/state checks pass against the installed
459-module ec5bc0ad artifact. See [installed results](d1_review_support/contact_c5_s3_partial_replay_20261002/installed_results.md).
The complete installed five-phase execution is not claimed from that smoke check.
