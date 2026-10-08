# Independent mechanics review

Reviewer: `/root/bl5_finite_contract`, independently assigned read-only mechanics
review; not sole implementer, no numerical jobs, edits or commits performed.
Review covers the equations, arithmetic implementation, complete new
counterfactual, observed outputs and resulting decision. This is development
review, not formalF03 or aggregate acceptance.

The reviewer derived the local elimination and reciprocal root/nonroot work
contract. Pre-run findings required original scaled equilibrium/compatibility,
dual coupling work and independently refined full/reduced routes. These were
implemented without changed thresholds. The arithmetic review found correction
signs, independent factors, strong no-retained-action map and FMA product tails
correct. It required corrected snapshots and free maps before guards; fixed.

The boundary review required total physical work/global wrench checks; partial
interface records must not masquerade as complete support/equilibrium records;
hash consumed parent arrays; require finite singular values; preserve normal
spin. All were fixed before the executed source snapshot. The rank-solver
default-limit failure remains preserved, corrected by a bounded85-row iteration
allowance without criterion/model change.

Final interpretation, quoted from the independent reviewer:

> The result decisively supports a boundary-enforcement explanation for this
> fixed native Mx fixture. Adding five nodal root restraints nearly removes the
> weak-versus-strong response difference, while retaining valid equilibrium,
> work, and row-admissibility checks. It does not establish BL5 fidelity or
> explain the external comparator completely.

> With the shell root fixed, those five rows imply u_b=0 and
> theta_bx=theta_by=0, while leaving theta_bz free. They are therefore
> algebraically equivalent, in this reference-linear fixture, to existing public
> beam-root FixedCoordinate components0..4. They constrain the beam nodal triad,
> not the retained half-cell endpoint director.

> The next reference definition should explicitly match this support/termination
> choice using public controls. If direct beam supports replace the strong
> comparator's root ties, remove the five now-redundant root rows. Preserve
> reaction provenance: a direct beam support reports ground reactions, whereas
> the root tie reports transfer into the fixed shell. Equivalent displacements
> do not make those reaction labels interchangeable.

> The augmented nonroot action difference remains0.1440 in its stated
> work-scaled nodal-action norm. It must not be equated with the earlier compliance
> norm. Remaining trace/action and stability questions stay open.

> No section-port rewrite or P0/P1 selection is justified by the earlier14.6%
> observation. Preserve the PROPACK failure and corrected run, record this
> fixture-specific decision, and launch no further diagnostic batch now.

No unresolved implementation finding remains in this bounded slice. Broader
physical-law and qualification obligations stay open as described in results.md.
