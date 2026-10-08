# V5 saved-state postprocessing review

Independent read-only review checked the two new postprocessors against the
saved V5 arrays, the physical-fibre retained operator, and its source layout.
No solver or external reference was executed in this review.

The 30 nodal coordinates and retained-cell spin offsets 30/33/54/57 are
correct. The adjacent end-moment rows are 9/12, 15/6, and 9/12 in the two
element records. The section is 0.04 m wide in y and 0.06 m high in z, with
identity reference triads. At the virgin reference, the left right-end log
contributes `-p_left . delta(phi_left)` and the following right left-end log
contributes `+p_right . delta(phi_right)`. The averaged moment times the
spin jump is justified by the saved tiny moment imbalance.

The reviewer identified a wording limit: this is **reference-linearized**
virtual work, using the saved linear solution as a virtual direction. Exact
finite-state first variation would require SO(3) log derivatives and frame
transport. The active note and source comment were qualified accordingly.
The corner displacement mismatch is conditional on a rigid-section lift;
neither it nor the virtual-work scale allocates the V5 body-work difference.

This review is development evidence only. It does not accept BL5, F03, a
multiplier space, physical accuracy, or any programme gate.
