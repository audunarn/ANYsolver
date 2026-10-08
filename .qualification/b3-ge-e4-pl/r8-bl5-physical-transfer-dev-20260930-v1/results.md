# BL5 physical transfer and matched-support screen — development only

Source parent `8b8bf6bb4726f1550d987e844e7ea0ea43813e5b`. No product
mechanics changed. Native operator runs use installed wheel
`615596739690168a5ecc7f02ac3a20a078cda5490e79604a50440a61a7d2f597`;
all387 installed module hashes are checked by the frozen native runners.
The external recorder forwards the unchanged direct16-interval reference in
fresh Python3.12 processes to verified OpenSees3.8.0/DLL25ba42e1....
Full source, binary, environment, command and output identities are retained.

## Decision and matched idealization

Can the released-normal-spin BL5 line transmit a physical normal couple, and
does matching ground supports resolve the previously large torque discrepancy?
Keep L1m,W.2m,h.035m, beam square.1m/A.01m2, E210GPa/nu.3,
As.008m2, Iy=Iz8.333333333333333e-6m4, J1.6666666666666667e-5m4.
Shell midplanez0, beam axisz.0675, common connectionz.0175.
Shell root fixed6; native beam root0..4 fixed, normal spin free.
External root five equations into fixed shell have the same nodal kinematics
but classify root load as shell transfer rather than direct beam ground load.
Native8 B3 members/16 retained halfcells/80 P0 rows and external16 Timoshenko
members/85 strong nodal rows are different discrete operators.

## Executed observations

The native +10Nm Mz case transfers10Nm through distributed force arms;
direct normal couples and shell-drilling constraint columns are zero.
Independent station-wrench recovery includes the native retained-cell reference
lift moment. Local/global pullback errors are at most8.9e-16 in the Mz case,
with valid virtual work, equilibrium and weak constraints. This demonstrates
the load path, not whole-response independence from numerical drilling.

| Fixed case | Native applied work J | External applied work J | Relative difference |
|---|---:|---:|---:|
| Mx10Nm | 6.341545000042213e-5 | 6.336019181751633e-5 | +0.08721% |
| Fy100N | 4.170920424889757e-4 | 4.190405315823900e-4 | −0.46499% |

Native Mx work exactly reproduces the saved root-restraint counterfactual.
At characteristic length1m, beam full-pose L2 differences are0.0570%/0.4989%
for Mx/Fy; shell differences0.3690%/1.9279%. Separate translation/rotation
measures and all poses appear in external-actions/comparison.json.

The root/line partition is still different: about the beam root, Mx line
contribution is−2.04647Nm native versus−2.10111Nm external; Fy root Mx is
14.07137Nm native versus12.14927Nm external. Other transfer components also
differ. These are resolution-dependent actions, not interchangeable nodal or
pointwise tractions. Changing moment origin from globalz0 to beamrootz.0675
includes the force lever arm; older origin values remain valid.

External recovery retains51 primary poses,32 global element covectors and85
equation rows. Actual transpose work maps give Cb.Tλ=L−G, exerted loads−C.Tλ,
and fixed-shell ground loads G+C.Tλ−L. Raw nodeReaction is explicitly unverified.
Worst external normalized ground/equilibrium error3.37e-13, work error2.68e-14,
gap3.39e-21; noncompatible virtual fields verify the sign of the dual work.
Both fresh external processes passed; no external model refinement or new load.

Installed impact checks on the unchanged61559673 wheel passed9/9 BL5 finite
predicates, including actual-update tangent, finite recovery/rebase/restart,
rejection, cancellation and typed/programming failure separation;210 onsite
imports. This fills the BL5-path impact coverage after point-recovery additions.

## Execution and limits

All owned numerical runs were serial, ceiling600s/8GiB. Native three-case route
5.69s, sampled process-tree peak160133120B; earlier supervisedMz2.59s/153759744B.
Installed impact39.40s/215138304B. External processes about0.274s each; their
coarse RSS samples miss short-lived peaks and are not a peak-memory claim.
Native effective BLAS1thread/JIT off verified; external environment requests1
thread only, no effective OpenSees thread assertion. No performance gain claim.
Initial unmonitoredMz output remains retained and is not resource evidence.

Retain BL5 ports and declared supports: this screen finds no defect requiring
a port rewrite and resolves the missing root-action observable. Next investigate
growing-space compatibility and integrated/fixed-distance transfer convergence,
with supported native work norms and actual indefinite KKT checks. Do not use
tip agreement to select a multiplier space or restart isolated axial refinement.
No1% converged acceptance, drilling-response independence, F03 execution,
M2/F02/F03/G0B/G2 qualification or release follows. Mandatory external CalculiX
comparisons, physical envelope and complete gates remain open.

[Independent review](independent-review.md) is clear for this bounded development
disposition; it confirms the substantial Fy transfer-partition differences and
does not accept a physical accuracy, multiplier or aggregate gate claim.
