# D6 native dynamics interface assessment

2026-09-30; worktree HEAD `23e845e131a8ea0c3457d10d9355ecdd5d1dd28e`.
Read-only source assessment; no numerical execution or qualification claim.
D1-interior acceptance does not close D6 or the required C0–C9 evidence.

## Available authority

Paths below are relative to `src/anysolver/`.

| Owner / exact symbol | Available contract |
| --- | --- |
| `_native_exact_shift_inertia.py:11` `exact_inertia`, `:24` `integer_inertia`; `_native_dyadic_interval_inertia.py:23` `interval_inertia` | Counts positive/negative/zero eigenvalues of represented symmetric `H-shift*M`. This is spectral arithmetic authority, **not physical inertial work**, velocities or gyro. |
| `ge_beam3_native.py:56` `define_beam`, `:80` `create_analysis`; `_ge_beam3_native_analysis.py:63` `NativeBeamAnalysis` | Explicit native definitions include positive physical 6×6 section inertia, centered reference geometry and triads. The analysis already constructs its own model; retain that exact owner rather than inserting native elements into a generic FEModel/dynamics route. |
| `_ge_beam3_retained_generalized_state.py:52` `Mechanical`, `:62` `State`, `:152` `Context.assemble`, `:181` `advance` | Compensated positions, nodal frames, retained cell rotations/resultants and issued material histories; full mixed work residual/Jacobian, multiplicative rotation updates. No velocity/time/dynamic checkpoint contract. |
| `_ge_beam3_p5_centered/mass.py:67` `_CenteredRestInertia`, `:91` `current_rest_mass`; `_ge_beam3_lifted_kinetic_factor.py:14` `current_lifted_kinetic_factor` | Centered physical station cache, uncondensed current-rest mass/factor. `_CenteredRestInertia.evaluate` rejects nonzero velocity or acceleration. |
| `_ge_beam3_p5/inertia.py:19` `FiniteInertiaResponse`, `:48` `LiftedInertia.evaluate` | Internal development kernel already returns kinetic energy, configuration-dependent mass, momentum, full finite inertial force and velocity/configuration derivatives, including centrifugal and momentum cross terms. Its original position interface lacks compensated low coordinates. |

Per element, the kinetic ordering is external 18 plus retained cell-spin 6.
Nine nodal translations and six cell spins carry physical inertia; nine nodal
rotation traces have exactly zero inertia. Full retained generalized work adds
18 algebraic section-resultant coordinates: one element has 42 mixed unknowns.
`_ge_beam3_native_generalized_modal.py:243` marks the free nodal rotation traces
algebraic and checks exact zero trace mass. Cell spins must remain dynamical;
the static element response/condensation is insufficient for this step.

At a station, with cell rotation U, reference frame R0 and lift d0,
`v_station=(1-t)v_left+t*v_right+omega×(U d0)` and
`omega_station=omega_cell`. Thus
`T=½ sum measure * [Q.T v_station,Q.T omega].T Jsection [Q.T v_station,Q.T omega]`,
`Q=U R0`. Existing owners supply this map and its physical cross terms; no new
AD engine is needed. `chart.exp_chart_terms` supplies the left Exp Jacobian and
derivative. Its symmetric-potential `pullback` is not a general inertial-tangent
adapter; finite inertia derivatives need their own chain rule.

## Contract needed before authoring

1. Approve a separate **centered finite-velocity** owner consuming the existing
   centered station data, with the finite kernel's physical work mapped explicitly.
   Use `_ge_beam3_p5_centered/positions.py:14` `station_position(high,low,...)` for
   momentum lever arms. The rest wrapper discards low positions safely only at
   zero momentum. Calling its superclass to evade the rest guard is unacceptable.
2. Freeze spatial cell angular velocity/acceleration, multiplicative midpoint
   rotation convention and consistent initial algebraic constraints. Derive the
   complete midpoint Jacobian `I_q Dq + I_v Dv + M Da`, including Exp-map terms.
   Freeze atomic mechanical/history/time/velocity commit and rollback identity.
3. Preserve public `FINITE_VELOCITY_DYNAMICS` exclusion and modal
   `finite_velocity_dynamics_authorized=False`. The static adapter's
   `compute_mass_matrix` remains unsupported. A separate development entry needs
   explicit scope; reference-Newmark `dynamics.py` cannot grant this authority.

## Smallest integrated slice and ownership

After those decisions: one contact-free native three-node/two-cell generalized
beam, elastic response, fixed physical section inertia, no damping/follower loads,
bounded steps. Solve the complete mixed midpoint residual with physical inertia
on translations/cell spins and algebraic trace/resultant equations retained.
Exercise nonzero cell spin and a lifted/curved reference so gyro and configuration
dependence cannot disappear. Check derivative consistency, full force/moment work,
constraint consistency and failed-step rollback; report energy drift without
claiming exact conservation.

Proposed author owns only new `_ge_beam3_centered_finite_inertia.py`,
`_ge_beam3_native_midpoint.py` and `tests/test_ge_beam3_native_midpoint.py`.
Lead owns any later additive analysis dispatch. Existing inertia/modal/static
guards and accepted state codecs stay protected. This is an implementation
proposal, not execution authority or D6 acceptance.

Source SHA256: P5 inertia `4274095b7a010a707aff68ede94c342f3b4504395dc0b3c9fc5bad075e269dfa`;
centered mass `f1f0de6eb24d8759b0f4c6d4515d65c5c7bb7487354ed4637ba07ad9d5d403b5`;
native facade `45cf3507bfe1da798c206a05370365e02475a77c3925d7355a970a20154f80ea`.
