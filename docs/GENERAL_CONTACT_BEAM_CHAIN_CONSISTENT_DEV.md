# Opt-in consistent B2-chain contact tangent

3 October 2026. Implemented/tested development; engineering acceptance,
normal application admission and release remain open.

## Use and scope

Set `ContactSolverSettings(beam_chain_tangent="consistent_dev", ...)` for one
explicit pair of connected, unbranched classical B2 chains. At least one side
has multiple cells. The existing limits of 16 cells per side and the candidate
pair cap remain. Declare both round radii, no endpoint caps, explicit line
stiffness, gap tolerance and line integration controls, with `pair_motion="general"`.
Existing elastic isotropic scalar/von-Karman structural restrictions apply.
This does not admit B3, native, friction, finite-rotation structural response,
self-contact, physical endpoint forces or beam junctions.

Run `python examples/general_contact_round_beam_chain_pair.py --consistent`.
Without this option the example and solver retain the existing finite-difference
selection. No automatic algorithm switch occurs on failure. The new profile is
`CLASSICAL_B2_CHAIN_ROUND_TUBE_NEAREST_CONSISTENT_STATIC_DEV_V1`.
Restart binds the selection and moving-interface geometry revision; incompatible
continuation fails. Existing default checkpoints retain their former identity.

## Discrete work and tangent

The mechanics remain the symmetric half-weighted sum of directional nearest-cell
distributed potentials. With fixed reference source length L, tube-radius sum R
and line stiffness k, each direction contributes

`E = (L/2) integral [k/2 min(d_nearest-R, 0)^2] ds`.

Bulk work uses the converged closest-point projection and its reduced Hessian.
At a transverse active switch b between left and right owners, define
`D=d_left-d_right`, `v=grad D` and positive `D_s`. The moving interface contributes

`K_interface = -(L/2) k g/D_s (v outer v)`.

Because g is negative this term is positive semidefinite. Gradients are mapped
to common authoritative coordinates before subtraction. The local union includes
the source and both targets, including shared-node accumulation and cross-target
blocks; global assembly is sparse. Activation adds no boundary term because
the traction vanishes there. One feature assembly replaces the old global
perturbation loop; residual-only evaluations retain the same derivative-sensitive
quadrature decisions as tangent evaluations.

## Geometry and explicit failure boundaries

Exact rational polynomials built from the prepared binary coordinates partition
projection, nearest ownership and activation. Positive panels are retained even
below floating parameter spacing. Quadrature coordinates and measures use
rational panel endpoints; unresolved floating physical work explicitly fails.
Quadratic roots use an 80-digit radical with exact-square-verified rational
enclosures. Stable q and c/q arithmetic remains rational, preventing tiny roots
from collapsing before domain filtering. Enclosure overlap or unresolved nonroot
domain-end overlap fails within a finite precision budget. Irrational cuts are
enclosure midpoints, not exact algebraic roots.

Nearest-feature classification uses exact squared distances. A length tolerance
previously mistook distinct nearby projections on a gently bent chain for an
unequal-work tie. At irrational cuts, canonical rational polynomial normalization
makes verified root midpoint identity invariant under scaling; the containing
all-feature projection interval retains branch-boundary rejection. Genuine
irrational triple ties are checked under all target permutations.

Active unequal-work domain-end ties, repeated nontransverse ties, distinct triple
ownership and projection-clamp plateaus reject. Strict shared-material-vertex
cones with identical mapped work are distinguished from these ambiguities;
all tied nearest competitors are checked, independent of element numbering.
The 8/16-point adaptive energy/force/tangent estimate is not a rigorous integration
certificate for arbitrary geometry. Broader refinement and admission remain open.

## Evidence and limitations

Independent scalar closest-point energy, virtual work, source/target directional
tangents, positive interface blocks and both-body cross blocks are checked.
Actual force/displacement control, fresh active split restart, incompatible
selection, small panels, ambiguous ties, public example and legacy compatibility
are covered. The V-switch local work fixture is not a qualification of its
through-crossing loading path or large-motion structural response.

Balanced guided four-step displacement timings compare identical mechanics,
integration controls and equilibrium tolerance with fresh models and one warm-up
per selection. See the [summary](d1_review_support/contact_chain_consistent_20261003/summary.json)
for final installed measurements and identities. No universal speed or programme
forecast follows from this case. Failed legacy force/integration comparisons stay
failed; the displacement comparison is a different development case. All earlier
root/panel/fixture failures are retained in the raw archive. Supporting Read
scrutiny by a different author using the same model family is not independent
engineering acceptance. Scientific tolerances and resource limits are unchanged.

The [partial-contact reference evidence](d1_review_support/contact_chain_refinement_20261003/summary.json)
compares guided small-motion cantilever chains against an independently assembled
Timoshenko/P1 unilateral line-foundation reference. Mesh and penalty sensitivity
are separate axes. The reference excludes finite-sliding geometry nonlinearities;
very small loads/gaps explicitly bound that comparison. It verifies distributed
work and measured sensitivity, not arbitrary-motion or continuum acceptance.
