# Native retained-port and termination decision — 30 September 2026

**Decision:** match the reference termination/support before attributing this
fixed torque discrepancy to a native section-port defect. Retain the existing
BL5 law and native retained coordinates. No multiplier policy or gate is accepted.

This Level-A development slice uses one unchanged16-interval Q4/native B3
fixture, eight generalized beam elements,80 integrated P0 BL5 rows, the
previous shell-root supports and +10Nm beam-tip Mx. Reference geometry,
section data, normal arms(+.0175m shell/-.05m beam), loads and operators are
bound in the parent reports/source archive. No mesh, material, tolerance,
product API/default, wheel, main or external model changed. FormalF03 authority
remains unconsumed. The reference-linear native mixed system is indefinite.

## Independent stationary elimination

Partition nodal and retained coordinates as n/r. With locally bounded
24-coordinate retained blocks:

    L=-Krr^-1 Krn; R=Krr^-1 Cr.T
    Kbar=Knn+Knr L; Cbar=Cn+Cr L
    Bbar=Cn.T-Knr R; W=Cr R
    [Kbar Bbar; Cbar -W] [qn;lambda]=[fn;0]
    qr=L qn-R lambda

These equations use local solves and sparse scatter; there is no global dense
Schur complement/inverse, symmetry repair or SPD interpretation. The frozen
lift counterfactual replaces -W by zero and reconstructs qr=Lqn. It is not a
product law or physical oracle. Bbar/Cbar.T dual work is checked on the actual
multiplier action, not claimed for every untested direction.

The initial metadata run failed because of Git safe-directory ownership.
The next arithmetic run failed retained-resultant parity1.0949363427e-10
against the unchanged1e-10 limit; nodal/rotation parity passed. Both are retained.
One independently reviewed compensated correction then used the original
factor for the original route and reduced/local factors for elimination:

    z=Krr^-1 rr
    reduced correction RHS=[rn-Knr z; rc-Cr z]
    dqr=z+L dqn-R dlambda

Signed products use fsum/FMA tails. No original full factor is applied to the
eliminated answer. Raw states, corrections, corrected states, free maps and
original sparse matrices are retained. Corrected nodal/rotation parity is zero;
resultant parity2.9033e-28, multiplier parity zero. Original/reconstructed
scaled equilibrium<=2.17e-13 and constraints<=4.24e-22.

| Fixed native case | Applied work J |
|---|---:|
| Original weak BL5 | 7.263253861884568e-5 |
| Frozen uncoupled-retained lift | 7.169062397284818e-5 |
| Strong nodal comparator | 6.341756473066285e-5 |
| BL5 plus comparator nodal root rows | 6.341545000042213e-5 |

Full→frozen is9.4191e-7J,10.22% of the original weak/strong difference.
The retained correction work is-5.2241904516e-7J, independently equal to
-lambda.T W lambda. Its sign does not imply positivity of the native system.
Reciprocal weak/strong work closes to5.59e-20J; the strong-root term is
9.1502660887e-6J,99.30% of the9.2149738882e-6J difference. These are different
decompositions and must not be added or equated with raw retained work.

## Root counterfactual and physical semantics

One further fixed-case solve adds exactly the comparator's five root rows to
the80 weak rows. The sparse supported-row check initially hit PROPACK's default
ten-iteration limit. That failure is retained. Setting its iteration bound to
the same85-row space resolves the algorithmic issue; no model/criterion changed.
Smallest/largest scaled singular values=.0300306881/.7095595281 versus binary64
rank floor7.6571e-14. This bounded rank check is not uniform interface stability.

The augmentation removes the response difference to-0.0033346% of strong work.
The remaining signed difference is-2.1147e-9J, -0.02295% of the original gap.
Scaled equilibrium1.49e-13; weak/root scaled gaps<=4.24e-22; total/shell work
errors<=1.90e-19J; scaled global wrench imbalance3.21e-15. Concentrated root
Mx7.92949Nm and integrated-line Mx2.07051Nm sum to10Nm. Partial records report
interface actions/work only, never separate equilibrium or support reactions.
The root rows have no beam normal-spin column; the computed root spin remains
about-4.078e-7rad. This is not a general release qualification.

**The added rows use the beam nodal triad, while BL5 uses the retained section
director.** With the shell root fixed, they imply beam-root translations and
nodal x/y rotations zero, normal spin free: algebraically equivalent here to
public FixedCoordinate components0..4. They are not physical half-cell endpoint
enforcement, a bonded-line completion or an automatic production correction.
Replacing ties by direct beam supports changes reaction provenance: ground
reaction and transfer into a fixed shell must remain separately labelled.

The nonroot action difference decreases from4.0985 to.1440 in this slice's
work-scaled nodal-action norm. That remaining shape difference must not be
called convergence, matched engineering accuracy or the earlier compliance
norm. Prior same-action shell, uncoupled-lift and interface-action evidence keeps
its original domain. Saved external root tie actions and complete beam traces
remain unavailable; no independent continuous-trace bridge is established.

## Resulting action and remaining programme

Use existing public supports to declare and match the next reference's
termination before further physical comparisons. Remove redundant root tie rows
if direct beam supports replace them. Keep integrated-line and concentrated
termination recovery distinct. Do not rewrite section ports or select P0/P1
from the earlier14.6% torque observation. Complete remaining trace/action,
torque/shear and growing-space stability requirements afterward under their
registered contracts. No further diagnostic batch follows this decision slice.

G0B/F03/M2/G2 and aggregate acceptance remain open. Materials, footprints,
topology, loads, spectra, capacity, practical scale, installed platforms,
consumers, external references and authorized release remain mandatory.

Five terminal run folders preserve commands, exact source snapshots, logs,
statuses, resource guards and failures. Successful allocation:4.211s/160915456B;
root control:2.591s/157151232B. These are diagnostic costs, not speedup claims.
Both ran Windows Python3.14.2, JIT off and effective one-thread BLAS.
[Manifest](manifest.json), [independent review](review.md), source-fixtures.zip,
and the immutable seal bind the source, dependencies and exact consumed arrays.
