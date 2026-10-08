# Saved interface and fixed-band admission component

This bounded classical F03 component verifies one supplied saved interface
record against a newly recovered local Qp state. It performs no equilibrium
solve and does not establish support work, virtual work, functional norm,
rank, positivity, convergence, product behavior or full recovery acceptance.

`SavedInterface` accepts an exact `Fraction` station partition and exact-shape
finite binary64 arrays: piecewise density `(ni,3,6)`, cosine amplitudes `(3)`,
endpoint atoms `(2,3)`, and four `(8,3)` signed-wrench inventories named
`band_analytic`, `band48`, `band64` and `line_band_analytic`. It validates
all types and dimensions before copying. The stored arrays are independent,
readonly snapshots; later caller mutation cannot change the record.

`verify_interface` owns `q,eta`, requires the saved cuts to equal the compiled
grid's exact trace cuts, and calls the existing recovery factory exactly once.
It independently constructs a `Functional` by lifting every saved binary64
coefficient to its exact represented rational. For saved density, cosine and
atoms, absolute discrepancy divided by `F0` must be at most `1e-10`. In
addition, the saved root atom must equal `root_resultant-eta` and the tip atom
must equal `-tip_resultant`, with absolute discrepancy divided by `F0` at
most `1e-11`. These stricter
partition checks remain separate from the general atom check.

The fixed signed bands are

```
[0,1/4], [1/4,1/2], [1/2,3/4], [3/4,1],
[0,1/32], [1/32,1/16], [15/16,31/32], [31/32,1].
```

Each total wrench is `(Fx,Fy,M_origin)` with
`M_origin=integral(s*mu_y+mu_theta)` and endpoint atoms included exactly once:
the root atom only when `left=0`, and the tip atom only when `right=1`, where
its moment is `Fy+M`. The line-only Action is formed by subtracting that exact
endpoint contribution from the total Action. No fake Recovery mutation is
used. A pure Functional band evaluator repeats the construction for the owned
saved Functional.

The component makes 192 fixed certified comparisons using the independently
reviewed Action enclosure: recovered total Actions against all three saved
total inventories, recovered line Actions against the line inventory, and
the same four inventories against Actions from the saved Functional. For every
comparison, the certified absolute discrepancy divided by `F0` must be at
most `1e-10`. This binds numerical inventories both to the
recovered state and to the saved coefficient record. A certified definite
violation or a coefficient/partition violation produces `FAILED`; that takes
precedence over any unresolved enclosure. With no failure but at least one
threshold-straddling enclosure the status is `HOLD_UNRESOLVED`. `PASSED` requires all 192
enclosures and every coefficient/partition check to pass. No retry occurs.

Explicit resource admission precedes recovery: interval count, exact 192-item
inventory, worst-case aggregate Action operations and rational bits, and a
workspace estimate containing the saved arrays, full declared nested Recovery
workspace/retained state, maximum Action scratch, saved Functional fractions,
and all 192 retained nested comparison records at maximum fraction size plus
fixed object overhead. It also charges 128 simultaneous maximum-size Actions.
The four 24-Action recovered/saved total/line lists account for 96; total,
line and endpoint 3-tuples coexist during construction, and one unary
subtraction plus its result brings the evaluated peak above 102. The remaining
slots cover loop/local references and fixed-band temporaries. Every slot has a
rational and all interval endpoint/coefficient fields. The Recovery numerator
and denominator bit caps are explicitly converted to bytes and receive fixed
Python integer/Fraction object overhead. Nested recovery DOF and interval limits are
checked before copying `q,eta`. Actual comparison operations and integer bits are accumulated
and checked after every comparison. The result is factory-closed; its recovered
state and saved Functional are immutable, nested comparison dictionaries are
frozen, and hashes bind the raw owned saved arrays, exact cuts, exact `q,eta`,
grid partitions and grid gather identity. Independent review and a registered
supervised saved-state use remain required before this can contribute to a
scientific reference decision.
