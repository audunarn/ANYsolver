# C2 B2 chain-to-chain distributed contact development profile

`CLASSICAL_B2_CHAIN_ROUND_TUBE_NEAREST_DISTRIBUTED_PAIR_STATIC_DEV_V0`
connects two disjoint open chains of classical B2 cells through
`solve_static_nonlinear`. This is a locally tested development profile,
not accepted C2 beam contact.

Each side declares a round radius and has 1–16 connected, nonbranching B2
cells with two real physical ends. The surfaces share no material node IDs.
Elements use concentric isotropic elastic scalar sections and the von Karman
route. End caps, junction contact beyond the distributed centreline law,
friction, plasticity, B3 curves, closed loops and native beams are outside this
profile. The interaction has directed `normal_law="penalty"` and an explicit
`line_stiffness` in N/m²; `gap_tolerance` and the separate
`sliding_difference_step` are lengths in metres. Set
`pair_motion="general"`, `line_integration_relative_tolerance` and bounded
line/swept subdivision settings. At most 16 cells on either side and the
declared `maximum_candidate_pairs` are admitted; excess fails explicitly.

For each source cell, projection changes, nearest-target-cell changes and
contact activation divide its reference line. Its target is the closest point
on the entire opposite chain, with stable element-ID ownership at exact ties.
The symmetric potential is half the source-to-target line integral plus half
the reverse integral. Each quadrature force acts on both selected cells;
shared material nodes receive the assembled sum. This prevents an internal
target junction from receiving duplicate independent cell-pair penalties.
The tangent is a central difference of the fully repartitioned force at the
explicit dimensional step, which includes motion of nearest-cell boundaries
on smooth branches. A nonsmooth tie may require path subdivision. Adaptive
8/16-point quadrature reports its discrepancy and fails at the subdivision
budget. The current minimum gap checks every represented cell pair; swept
checks use a conservative nodal relative-motion bound and bounded subdivision.

The local controls in `tests/test_general_contact_beam_chain_pair.py` include
an analytic 2 m parallel-chain potential, a separate closest-polyline SciPy
integral for a kinked target, balanced wrench, role exchange, tangent,
through-crossing rejection, topology/resource failures, coupled displacement
control and restart. The initial exploratory coupled run exhausted an 8-level
integration budget at 10⁻⁸ tolerance; 12 levels with 10⁻⁷ also exhausted on a
small trial interval. The declared 10⁻⁶ setting passed the independent work
oracle and coupled route. These failures remain in the task evidence. They do
not establish a universal recommended tolerance or engineering acceptance.

Run [the chain-pair example](../examples/general_contact_round_beam_chain_pair.py)
with an installed package. C2 still needs B3 and general multi-cell beam pairs,
near-junction refinement, true endpoint contributions, mesh/enforcement and
resource qualification, and independent review.
