# G0 candidate: physical ribbon pose for a nonmatching B3-GE/shell line

Status: **derivation and experiment contract, not accepted mechanics**. This
candidate is tested under F02/F03/F04; it does not select a production
multiplier space or change an existing qualified element.

Independent mechanics review caught an earlier, incorrect global-Q2 current
beam position in this draft. The equation below now follows the native
retained half-cell lift and is subject to the executed F03-B station-work
comparison. The reviewer also clarified that four moving samples sweep two
traction rails under line integration; they do not produce finite-area
traction. The midpoint jump and shell shear/stability questions remain open.

## Reference geometry and fixed correspondence

Let `s` be the material beam coordinate. Split every integration interval at
beam half-cell, shell-face, and attachment boundaries. For each quadrature
station select a declared shell face and four material sampling points at
`(s-a,-b)`, `(s+a,-b)`, `(s+a,b)`, `(s-a,b)` in an oriented local surface chart.
The positive physical half-widths `a,b` belong to the attachment definition;
they do not shrink automatically as the mesh is refined. Shell point
interpolation uses the actual Q4 or S3-V2D nodal translations and each host
element's material shape functions. Search and host selection occur in the
reference configuration. Each station consequently touches at most four
small shell elements even when the physical ribbon spans many elements.
When integrated along `s`, the four moving samples describe two longitudinal
rails. Their traction support is line-like, **not** uniformly distributed
over the area between rails. This may be appropriate for a bonded line with
a finite physical torque arm; it is not the separate finite-area footprint
law. Convergence and shell shear/locking tests decide its admissibility.

Take the weighted centroid of the four reference/current sample positions,
`r_s0/r_s`, and their proper least-squares rigid rotation `R_s0/R_s`. The
reference sample covariance must have two resolved singular directions;
ambiguous orientation, a folded/degenerate patch, an opening, or an undeclared
seam crossing fails preflight. No normal-coordinate or director equality is
imposed. The pose fit must remain differentiable within a declared chart and
must have a unique proper branch at every accepted and trial state. An
objective proper fit obeys `r_s(Wx+t)=W r_s(x)+t` and
`R_s(Wx+t)=W R_s(x)` for a common spatial rigid motion.

The native three-node beam uses its **half-cell physical lift**, retaining
high/low compensated coordinates. On half-cell `c`, let `I_c` linearly
interpolate its two endpoint positions and let
`L_c(s)=X_b0(s)-I_c X` be the centered reference lift. Then

`r_b(s)=I_c(x+x_low)+U_c L_c(s)`.

The native line-load evaluator computes the same displacement as
`I_c[(x+x_low)-X]+(U_c-I)L_c`. Differentiating `r_b` therefore includes the
`U_c`-dependent lift force and moment. A global Q2 nodal-displacement trace
is **not** the native retained beam trace, even for a deformed straight beam,
and must not be used for this attachment.

Within retained half-cell `c`, the section frame is
`R_b(s)=U_c R_b0(s)`, where `U_c` is the **actual retained cell rotation** and
`R_b0(s)` is the native centered reference frame. The native local evaluator
uses this `U_c` against reference nodal triads. Its two half-cell variables
are not silently replaced by interpolated nodal rotations. At the shared
half-cell boundary, use one-sided traces and examine whether separate exact
line constraints cause locking or an unsupported interface mode. A jump
cannot be erased by a reference remap during Newton iterations.

The declared reference beam-axis offset must agree with the selected face,
orientation and projected ribbon geometry. Compute `e0(s)` and `A0(s)` from
the validated supplied reference poses; do not infer an arbitrary offset to
make an unrelated geometry stress-free. In particular, positive/negative
eccentricity and an axis lying on either side of the shell need distinct
reference records. Reconstructed constraints at **every** assembled station
must vanish at reference within the registered tolerance.

## Work and derivatives

At each station use the objective relative-pose law

`c_t=R_s^T(r_b-r_s)-e0`, `c_R=Log(A0^T R_s^T R_b)`.

For exact multiplier fields, the connection work is

`Pi_c=int [lambda_t^T c_t+lambda_R^T c_R] dL0`.

`dL0` is the fixed reference beam arclength, with the native curved
reference Jacobian. Physical beam variations include physical nodal
translations and retained cell rotations through both the section frame and
the lifted centerline; shell variations include sampled translations through
actual host shape functions. The shell's independent
director rotations remain available to its own shear/bending operator; they
are not equated to the surface normal or artificially assigned beam torque.
This is an intentional **distributing** ribbon model. A rigid ribbon is a
separate law that constrains a physical shell region; one must not masquerade
as the other.

Differentiate the full sampled-position and proper-fit composition twice.
The fit's first/second variations, the `SO(3)` logarithm, the eccentric
translation lever arm, native beam chart and multiplier curvature all enter
the coordinate tangent. Shell residual rows may be spatial while columns
are additive rotation coordinates; beam retained rows have their existing
spatial/chart contract. Transform at each port before scatter. A symmetric
Hessian in one coordinate representation does not justify symmetrizing a
spatial-row tangent. Recover physical wrenches by virtual work, not by
displaying raw material multipliers as spatial moments.

## Required bounded experiments before selecting this law

1. On one curved and one flat reference, check all station gaps, common rigid
   motion, origin translation, reversed beam parameter direction, and both
   eccentricity signs. Compare first and second derivatives against
   independent directional perturbations through actual shell and retained
   beam updates, including nonzero multiplier forces and moments. First verify
   the lifted `r_b` numerically against native line-load station work for an
   arbitrary deformed curved state with nonzero `U_c`; this is a prerequisite
   to any vector constraint result.
2. Assemble actual physical Q4 and S3-V2D stiffness, plus native retained B3
   operators, with independent dense and sparse small-model oracles. Examine
   drill-only and director/shear perturbations. A pure single-node `rz`
   cannot be the only source of beam-normal torque. Confirm total force,
   moment about a common origin, and virtual-work balance.
3. For ratios 1:1, 1:2, 1:4, 1:8 and reciprocals at three registered
   refinements, compare exact P0, continuous P1 and derivable dual multiplier
   spaces. Segment quadrature on the union of shell, beam half-cell and
   multiplier intervals. Examine scaled row rank, mechanically active
   constraint modes, energy-norm inf-sup, patch response, locking,
   pointwise/weak gaps, and convergence. A nonzero scalar singular floor from
   F03-S does not select a space.
4. Sweep fixed physical ribbon width, shell thickness, shell refinement,
   Q4/S3 transitions and support overlap. Report physical/numerical shell
   stiffness channels separately. Require preserved transverse shear and
   stable physical torque transfer. This may reveal that the candidate is
   inadmissible; no drilling-penalty tuning or penalty-line substitute is an
   accepted repair.
5. Freeze the selected multiplier space, ribbon-resolution policy, admissible
   mapping ratios, quadrature, constraint scaling and resource envelope only
   after the foregoing checks and independent mechanics review. If none
   passes, revise the formulation within G0 instead of advancing G1.

This is a concrete candidate, not a production decision. Most importantly,
the four sampled shell positions create a finite physical moment arm while
leaving the shell director independent, and the beam side retains the actual
cell rotational variables. Whether that candidate is stable and convergent
is an executable question, not an assumption.
