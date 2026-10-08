# Deforming elastic Q4 / opposing planes — development example

Run `examples/general_contact_deforming_q4_planes_dev.py --output <result.json>`.
The example uses the existing multiple-plane Newmark development profile with
`batch_plane_event_fronts_dev=True`. This selection requires the explicit
multiple-shell Q4 event profile and is bound into restart identity. The default
per-row event proposal remains unchanged. No automatic algorithm switch occurs
inside a failed increment.

Four actual Q4 strips retain two manufactured affine modes, (w=a+bx). Other
coordinates are constrained. Physical bottom/top skins approach opposing fixed
planes; in-plane motion and section rotations are zero. The shell has genuine
transverse shear and von Karman membrane work. These constant MPCs are mathematical
fixtures, not permanent beam/shell attachment capabilities.

For unit square, thickness 0.05 m, density 1 kg/m³, E=100 kPa and nu=0.3:

\[
M=\operatorname{diag}(0.05,0.05/12),\qquad
U=801.282051282b^2+686.813186813b^4.
\]

Independent local checks resolve both terms at structural-only slopes 0.08 and
−0.13. The impact uses velocities (0.002 m/s, 0.05 s⁻¹), gap 10 µm, pressure
penalty 10⁹ N/m³, physical gap tolerance 5 µm, dt=10 µs, end=1.8 ms. Its membrane
energy is tiny; whole-route energy agreement does not qualify nonlinear membrane
accuracy. The asymmetric initial motion makes the two wall contacts sequential.
Separate simultaneous-contact evidence remains in the preceding example.

The pressure basis is the structural mesh's Q1 nodal basis. A boundary hat has
weighted x coordinate (0.5-\Delta x/3). One Q4 would permit 20 µm physical
penetration before pressure activation and is unsuitable for this fixture's
5 µm budget. Four strips give 2 µm activation penetration. This calculation is
a resolution preflight, not a bound on the full trajectory; independent physical
corner path checks still gate every accepted step.

The opt-in event front uses the minimum oriented gap among every required,
properly bracketed pressure row. It shares vector endpoint equilibrations across
rows. Both time and gap tolerances, initial-phase checks, omitted/hidden-row
rejection, cancellation and resource limits remain. A nonlinear endpoint family
with hidden reentry is not certified by this proposal; the solver still
reequilibrates and checks the entire represented Hermite path and physical gaps.

Source/installed example and active split restart pass, including rejection of a
changed front selection. This is discrete development verification, not independent
engineering acceptance, release, continuous dynamics, spatial/temporal convergence,
free/deformable-target contact, finite-rotation/descriptor behavior or plasticity.
The full programme remains active.

[Evidence and retained failures](d1_review_support/C6_DEFORMING_SHELL_PLANES_SLICE_20261003.md).
