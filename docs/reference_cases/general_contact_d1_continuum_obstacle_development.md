# Independent scalar obstacle reference for the guided D1 strip

**Status:** development comparison, 28 September 2026. It does not qualify
the shell formulation, pressure space or C1 handoff.

## Question and independent method

The guided Q4 source in the saved D1 partial-contact fixture fixes all shell
rotations. Its transverse continuum limit has shear energy

\[
\frac{D}{2}\int_\Omega |\nabla w|^2\,dA,
\qquad D=\frac{5}{6}\frac{Et}{2(1+\nu)}=1602.5641\ \mathrm{N/m}.
\]

Use \(\Omega=[0,1]^2\) m, \(w=0\) at the left edge, free other edges,
downward load \(q=0.3\) N/m² and the obstacle \(w\geq-40\) µm over only
\(0\leq y\leq0.9\) m. Pressure is a nonnegative reaction to that bound.

`scripts/general_contact_d1_continuum_obstacle_reference.py` independently
discretizes this scalar variational inequality with cell-centred conservative
finite volumes and a primal active set. It imports NumPy/SciPy only: no
ANYsolver element stiffness, contact kernel or pressure optimizer. Each solve
checks nonnegative pressure, cell gap, free-cell residual and global force
balance. This provides a different mechanics/discretization reference for
the restricted fixture; it is not a general shell oracle.

For a full-width obstacle the exact one-dimensional contact front is
\(a=\sqrt{2Dg/q}=0.65372045\) m. The exact integrated contact reaction is
\(q(1-a)=0.103883865\) N. At 64×80 cells the independent solve gives
0.103891528 N and a maximum cell-displacement error of 5.68 nm. At 256×320
cells the reaction error is 7.98×10⁻⁷ N and displacement error is 0.356 nm.

## Partial-width observations

| Grid | Contact reaction (N) | Equilibrium defect (N) |
|---|---:|---:|
| 32×40 | 0.103801048 | 2.61×10⁻¹⁴ |
| 64×80 | 0.103801953 | 1.06×10⁻¹³ |
| 128×160 | 0.103803231 | 4.23×10⁻¹³ |
| 128×320 | 0.103806928 | 3.65×10⁻¹³ |
| 256×160 | 0.103800693 | 1.08×10⁻¹² |
| 256×320 | 0.103804402 | 1.65×10⁻¹² |

At common 128 x bins, changing 128×320 to 256×320 changes the
x-integrated pressure force by 0.0203% in L2 and its cumulative reaction by
at most 0.00270% of total reaction. Changing 128×160 to 128×320 changes
those by 0.0677% and 0.0179%, respectively. Raw cell pressure differences
are grid sensitive near the contact front; common-bin weak reactions are the
comparison quantity.

The active-set-stationary saved 128-Q4/fine-Q1 linearized field integrates to 0.103883728 N,
0.000079325 N (0.0764%) above the 256×320 continuum value. Their
x-integrated pressure differs by 1.39% relative L1 and 3.04% relative L2;
the largest cumulative difference is 0.639% of continuum total reaction.
The structural-node-aligned selected-knot field reproduced that same
fine-Q1 **discrete** field to about 10⁻¹¹ relative L2 in the earlier screen,
so it inherits the continuum discrepancy. That screen does not show a
whole-route cost reduction.

An independent local scalar-Q4 work matrix was compared with the guided
production Q4 vertical-displacement block at five x/y aspect ratios, from
16×1 to 128×4. Relative Frobenius errors were at most 6.42×10⁻¹⁶. This
confirms the scalar shear coefficient and local work reduction for these
flat, rotation-fixed elements. The saved Q4 strip still has only one element
across y. The continuum comparison flags transverse structural resolution
or pressure representation as possible causes of the weak field discrepancy;
it does not identify one. The next bounded action is a source-only Q4/y-row
refinement against the continuum before another coupled contact solve. Do
not adjust the original
contact gap, pressure, equilibrium or response acceptance gates.

A separate read-only reviewer checked the finite-volume signs, units,
obstacle support, exact full-width control, KKT/balance and Q1 common-bin
integration without finding a concrete defect. The reviewer identified that
an earlier pressure report preceded active-set stationarity refinement. The
comparison above uses the later stationary report; the change affected the
rounded force/weak-field metrics negligibly. This remains development
review, not independent acceptance.

Raw outputs:

- `reports/general_contact_d1_continuum_obstacle_dev_20260928.json`
- `reports/general_contact_d1_continuum_refinement_dev_20260928.json`
- `reports/general_contact_d1_linearized_front_stationary_dev_20260928.json`
- `reports/general_contact_d1_guided_scalar_work_dev_20260928.json`

All runs used Python 3.14, one BLAS/OpenMP thread and the isolated general
contact worktree. The new continuum scripts have no production dependency.
