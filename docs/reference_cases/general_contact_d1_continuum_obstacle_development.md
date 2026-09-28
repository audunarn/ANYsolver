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

## Source-only transverse-resolution discriminator

`scripts/general_contact_d1_source_y_resolution.py` keeps the same guided
flat Q4 structural tangent and independently integrates the distributed
0.3 N load and clipped Q1 pressure work. Its one-row cases reproduce the
earlier 16/32-Q4 linearized reactions to roundoff. The pressure solve checks
stationarity, nonnegative pressure, weak gap and structural equilibrium.
When a y grid places pressure nodes entirely above the 0.9 m overlap, the
script removes their exactly zero-support modes before solving.

| Q4 x×y cells | Reaction (N) | Weak x-force L2 error vs continuum | Maximum cumulative-force error |
|---|---:|---:|---:|
| 16×1, 16×2, 16×4 | 0.103871560 | 3.656% | 1.144% |
| 16×8 | 0.103816377 | 3.156% | 0.978% |
| 16×16 | 0.103807014 | 3.105% | 0.963% |
| 32×1, 32×2, 32×4 | 0.103857267 | 6.065% | 1.192% |
| 32×8 | 0.103815599 | 5.342% | 0.866% |
| 32×16 | 0.103808466 | 5.272% | 0.827% |
| 64×16 | 0.103825688 | 2.611% | 0.385% |

All reported structural residuals were below 5×10⁻¹⁵ N and represented
physical gaps were at worst −0.0771 µm. Transverse resolution changes the
integrated reaction once the overlap rim is resolved locally. The weak
pressure field remains nonmonotone in x, though the 64×16 result improves
over 32×16. Neither integrated-force agreement nor the small gap establishes
pressure-field convergence. A further x/pressure-resolution choice should
be justified against this comparator before allocating a coupled nonlinear
run. The first 16-row attempt failed in the diagnostic because it required
positive support for modes entirely outside the overlap; the corrected
support admission and the failed attempt are retained in the living note.
An independent read-only review found no load, Q1 overlap, supported-mode,
indexing, sign or comparison-bin defect in these reports; the one-row results
match the previous linearized source cases to roundoff. It identified a
command-line range check that allowed x grids unable to partition the
256-cell continuum reference. That check and an explicit 50 µm represented
gap budget are now enforced. A focused 16×16 rerun reproduced its saved
reaction and weak-field error exactly; an invalid 24-column comparison
rejects before solve. The review does not establish pressure convergence.

## Fixed-structure x-pressure screen

The source-only 64×16 Q4 structure was held fixed while nonnegative P1
pressure used 16, 32 or 64 x cells. All pressure knots coincide with
structural x nodes. Exact two-point Q1 cross-work matches the earlier
independent overlap integrator within 1.8×10⁻¹⁷ m on these nested grids.
The matched source control reproduces its saved force, field metric and gap.

| Pressure x cells | Supported modes | Reaction (N) | Weak x-force L2 error vs continuum | Maximum cumulative-force error |
|---|---:|---:|---:|---:|
| 16 | 272 | 0.103852885 | 7.717% | 1.046% |
| 32 | 528 | 0.103828615 | 9.298% | 1.088% |
| 64 | 1040 | 0.103825688 | 2.611% | 0.385% |

Every P1 field is integrated onto the same 64 structural x bins before
comparison with the 256×320 finite-volume reference. The first saved
diagnostic instead compared each field on its own 16/32/64 bins, which
smoothed the coarse fields; that raw report is retained but its cross-policy
field ranking is invalid. The corrected result shows a large weak-field
effect masked by small reaction changes. The pressure sequence is still
nonmonotone. Supported-pressure stationarity, structural equilibrium and
the existing represented-gap budget pass, but no continuum pressure-space
convergence or whole-route speedup is established.

Independent read-only scrutiny found no defect in the corrected nested Q1
work, support indexing or common-bin comparator. It confirmed that the
16/32-cell fields are farther from the continuum than the 64-cell field on
the same weak measure. This remains a source-only x-integrated comparison;
it does not certify the local two-dimensional pressure field, selected-knot
performance, coupled S3 behavior, restart or cost.

The next decision is whether structural x refinement at *fixed* 64-cell
pressure changes this field. A 128×16 source-only structure is the maximum
next candidate under a separately checked 3-minute/1-GB diagnostic cap;
pressure x128 on that same structure would follow only if needed. A larger
nonlinear coupled solve is not yet justified.

That bounded discriminator completed. At common 128 x bins, structural
64×16/pressure x64 has 5.567% weak-field L2 error. Refining only structure
to 128×16 lowers it to 4.747%. Holding that structure and refining pressure
to x128 lowers it to 1.452%; total reaction changes by only 0.000000825 N.
The matched x128 case has 2064 supported and 677 active pressure modes,
1.54×10⁻¹⁴ N structural residual and −0.0771 µm represented gap.

The initial matched-pressure run stopped because its preliminary L-BFGS-B
search reached 10,000 iterations, even though the subsequent active-set
refinement had near-zero gap and complementarity. The failure is retained.
An opt-in source-only correction now accepts that specific optimizer limit
only after a complete discrete KKT certificate. The historical default
still rejects it. The repeated identical mechanics produced active
stationarity 4.24×10⁻²⁰ m, inactive minimum gap +3.05×10⁻⁹ m and maximum
complementarity 4.17×10⁻¹⁹ Pa·m. A small analytical QP test checks both
the opt-in certificate and the unchanged default rejection. Independent
read-only review found no concrete gate weakening and confirmed the
common-bin field improvement. The certificate does not establish a local
two-dimensional pressure error bound or good compliance conditioning.

The next bounded source-only candidate is the already implemented
structural-node-aligned front-knot selection at 128×16. Compare its
pressure and response with matched x128 on the same structure, under the
same resource and physical-gap limits. Do not infer nonlinear coupled
speed or C1 pressure acceptance from this linearized comparison.

The selected front knot set uses 45 x knots, 720 supported pressure modes
and 362 active modes, versus 129 knots, 2064 supported modes and 677 active
modes for matched p128. On the same 128×16 structure, their total reaction
differs by 3.49×10⁻¹² N. Their full two-dimensional P1 pressure fields
differ by 0.0258% in exact common-Q1 L2 over the physical overlap
\(x\in[0,1], y\in[0,0.9]\). The maximum common-grid nodal pressure
difference is 0.01965 Pa, or 0.1845% of the matched field maximum.
The common-grid x-line pressure differs by 0.00402% L2. The selected and
matched active scaled compliance minimum eigenvalues are 9.987×10⁻⁴ and
7.258×10⁻⁴; their condition estimates are 2.216×10⁵ and 5.560×10⁵.

The selected source-only route took 15.84 s and 418 MB peak process RSS;
matched p128 took 31.29 s and 599 MB in these diagnostic reruns. These
measurements motivate a **bounded coupled candidate** with the same
mechanical inputs and unchanged acceptance gates. They do not measure
whole-route savings, prove continuum pressure convergence or establish
C0/C1 acceptance. Full-field comparison consumes saved P1 grids through
an independent postprocessor; it does not call the contact kernel.
Independent read-only review verified the saved comparison and found a
generic nonnested-knot validation gap. The postprocessor now requires
selected knots on the fine grid; this correction does not change the
reported nested-grid result.

Raw outputs:

- `reports/general_contact_d1_continuum_obstacle_dev_20260928.json`
- `reports/general_contact_d1_continuum_refinement_dev_20260928.json`
- `reports/general_contact_d1_linearized_front_stationary_dev_20260928.json`
- `reports/general_contact_d1_guided_scalar_work_dev_20260928.json`
- `reports/general_contact_d1_source_y_resolution_dev_20260928.json`
- `reports/general_contact_d1_source_y16_dev_20260928.json`
- `reports/general_contact_d1_source_64x16_dev_20260928.json`
- `reports/general_contact_d1_source_y16_guard_recheck_dev_20260928.json`
- `reports/general_contact_d1_pressure_x_fixed_64x16_dev_20260928.json`
- `reports/general_contact_d1_pressure_x_fixed_64x16_common_bins_dev_20260928.json`
- `reports/general_contact_d1_pressure_x_fixed_64x16_common128_dev_20260928.json`
- `reports/general_contact_d1_structure128_pressure64_common128_dev_20260928.json`
- `reports/general_contact_d1_structure128_pressure128_common128_dev_20260928.err`
- `reports/general_contact_d1_structure128_pressure128_certified_dev_20260928.json`
- `reports/general_contact_d1_structure128_selected_front8_field_dev_20260928.json`
- `reports/general_contact_d1_structure128_pressure128_field_dev_20260928.json`
- `reports/general_contact_d1_selected_vs_fine_field_dev_20260928.json`

All runs used Python 3.14, one BLAS/OpenMP thread and the isolated general
contact worktree. The new continuum scripts have no production dependency.
