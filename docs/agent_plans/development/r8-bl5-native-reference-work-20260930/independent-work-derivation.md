# BL5 native/reference work map — independent mathematical check

Scope: straight flat reference, zero native lift, fixed spatial normal n=e_z, shell physical rotation coordinates eta=(r_x,r_y), continuous beam translation U, and independent spatial cell rotation Theta. This source-based derivation uses BL5LineWork.at_reference/_evaluate in src/anysolver/_stiffened_shell_bl5_local_experimental.py and NativeHalfCellPort.pose_pair/active_beam_slots in src/anysolver/_stiffened_shell_l1_local_experimental.py, at the supplied source baseline 7987074b in the coupling worktree. It concerns the declared positive auxiliary norm; no spectrum, thresholds, numerical execution or qualification is included.

## Exact physical density and sign

At a reference station let R be the beam station frame, E the stored 2-by-3 director_basis, n the spatial shell director, and a_s the shell midsurface-to-top arm. Let a_b be the interpolated beam-axis-to-coupling-point arm. With zero lift, a_b=R reference_arm. In a future nonzero-lift case it would include the extra native-cell lift: a_b=R reference_arm+R_cell lift.

For the five multiplier densities lambda=(lambda_t,lambda_d), define
\[
 p=R\lambda_t,\qquad q=R E^T\lambda_d,\qquad c=n\times q.
\]
Here lambda_t and p have units N/m; lambda_d, q and c have units N (moment per line length). The stored basis makes q tangential to n at the reference. It must be used as stored; the two director channels are not generally spatial rx/ry moment components.

The local first variation of the implemented **constraint work** is
\[
 \delta W=p\cdot[v-U+\theta_s\times a_s-\Theta\times a_b]
           +c\cdot(\theta_s-\Theta),
 \qquad \theta_s=(\eta_x,\eta_y,0).
\]
Thus the resisting covector C^T lambda, per unit length, is
\[
 \begin{array}{c|cc}
 &\text{translation}&\text{spatial moment}\\ \hline
 \text{shell}&+p&a_s\times p+c\\
 \text{beam}&-p&-a_b\times p-c .
 \end{array}
\]
The loads exerted on the domains are MINUS these covectors. Either convention can define a norm functional if used consistently on both domains, but an action recorder must state which it uses. Ground reactions are a separate equilibrium quantity. With the reference coupling point written equally as shell_origin+a_s and beam_axis+a_b, the two spatial forces and total moments about any common origin cancel stationwise; checking this is independent of a Riesz solve.

For n=e_z and q=(q_x,q_y,0), c=(-q_y,q_x,0). The shell eta load is the x/y projection of the shell spatial moment, not lambda_d itself. Pure spatial-normal direct couple is zero, while eccentric force-arm normal moment need not be zero for a general arm.

For a cell-constant Theta_j, the resisting beam reference functional is
\[
 F_B=\int_0^L(-p)\cdot U\,ds+\sum_jm_j\cdot\Theta_j,\qquad
 m_j=\int_{I_j}[-a_b(s)\times p(s)-c(s)]\,ds.
\]
Each m_j is an integrated N m vector, without division by cell length. Preserve the actual multiplier basis, split integration at its boundaries and all native halfcells/shell segments, and use physical line measure ds. Coherent multiplier aggregation changes its support/basis; it does not change this work formula.

For the shell resisting functional,
\[
 F_S=\int_{\Gamma}\{p\cdot v+
             [(a_s\times p+c)_{x,y}]\cdot\eta\}\,ds .
\]
This is a line functional on the enriched five-field shell, not a volume load uniformly spread over its width. The total functional is F_S+F_B; the independent dual squared norm is the sum of the two domain dual squares.

## Density scaling and native primal pullback

Set mu=(lambda_t,lambda_d/ell), Q=diag(1,1,1,ell,ell), lambda=Q mu. All mu channels have units N/m, and the correct pairing is mu^T Q^T C delta_q. Q scales director gaps by a fixed physical length; it does not rotate the director basis. Derive reference loads from lambda=Q mu, including c, before a Riesz solve. Reciprocal basis and physical unit conversions must transform both work and M by congruence.

At each native station, pull reference U back as (1-w)u_left+w u_right and reference Theta as the left spatial increment of that native retained cell. NativeHalfCellPort uses only these six endpoint translation slots and three retained rotation slots. Consequently an integrated beam covector scatters its force with weights (1-w),w and puts the complete integrated spatial cell moment into the retained cell's three rotation slots. With a lift, its force moment additionally includes the lift cross force; zero lift is the present scope.

On the shell, use the same physical station interpolation as the native edge map for v and eta. The flat reference director variation is theta_s cross n. Scatter the spatial force and x/y moment by those shape weights. The reference map is an independently expressed physical pullback; its work must agree with the native reference Jacobian on arbitrary admissible native perturbations, not only on a compatible solution. The identities to check are F_ref(P delta_q)=lambda^T C delta_q and, after scaling, F_ref(Q mu; P delta_q)=mu^T Q^T C delta_q. A minus convention changes both sides together.

## Omitted slots, positive normal spin and gauges

NativeHalfCellPort.active_beam_slots selects translations 6*node+[0,1,2] and retained rotations nodal_count+24*element_index+3*cell+[0,1,2]. In this native layout the first six retained entries are the two cell rotations; the remaining 18 entries are retained force/resultant coordinates. The auxiliary physical norm omits:

- All native beam nodal rotations (slots 6*node+[3,4,5]).
- The 18 retained force/resultant slots per native element (offsets 6..23).
- Shell reference normal-spin/drilling rotations (flat-reference nodal rz).

For each of these omitted basis directions Z, verify the actual assembled supported C Z=0, including all constraint rows and interpolation/assembly. This is required to descend the coupling to the physical-norm quotient. The selected port formula explains the beam zeros structurally. The shell zeros follow because rotating about n changes neither its director nor its normal top arm at this flat reference. These directions are not thereby removable from the actual mechanical KKT: native nodal rotations/resultants and drilling stiffness still have their mechanical roles.

In contrast, retain all three components of cell Theta in the positive beam norm. For the present centerline a_b parallel to n, a retained Theta_z gives Theta_z cross n=0 and Theta_z cross a_b=0, hence C annihilates it. It is a positive-norm direction in the kernel of this coupling, not a zero-norm direction or a proven mechanical gauge. Do not quotient it out merely because C sees no work. Nonzero transverse arms/lifts can activate it through translation, so the five-channel director law alone does not guarantee this annihilation.

Bulk shell fields away from the coupling line also remain in its positive norm, even when their line trace vanishes. Distinguish this ordinary trace kernel from omitted-coordinate norm nullspace and from a mechanical rigid-body gauge. A mechanical gauge requires its own supported KKT/kernel reasoning.

## Width and normal-spin convention

No different normal-spin release is needed for this initial reference: shell eta has two tangential components, beam Theta has three, and the five-channel law supplies two director constraints while its translation constraints retain all physical force-arm work. Adding a sixth director channel or deleting beam Theta_z would change that declaration.

The auxiliary beam norm may average its actual bottom-surface trace across a declared finite physical width. Then A(s,y)=skew(a(s,y)) enters C_j through the average A^T A, and D_j through average A^T. The BL5 work above is still evaluated on its physical coupling line, with a_b(s) at that line. Off-line surface points can respond to Theta_z even when the centerline law annihilates it; their positive norm is consistent with a zero centerline functional.

Using a single centerline arm in the norm instead of a finite-width surface average defines a different reference M. It must be declared beforehand with its width/weights and physical rationale, not silently substituted or adjusted using candidate beta. The single-arm analytic manufactured control verifies coupling algebra, but does not verify the finite-width average. A separate analytic average/moment control is needed for that implementation choice.

There is no intrinsic function-space obstruction for the stated flat, zero-lift scope, provided actual C annihilates the omitted slots and the shell line functional is assembled as a line source. Current-chart/nonflat extensions require spatial/director chart pullback and a fresh annihilator check; the flat rz statements cannot be carried over unchanged. Actual mechanical KKT stability, line-reference enrichment, controls/floors and qualification remain separate open obligations.
