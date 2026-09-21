# F03 after K3: channel-adapted native-trace candidate

21 September 2026. **Unregistered mechanics design, not a production
space or G0B result.** K2P, K2L and K3 rule out choosing one common
scalar P1 or P0 grid merely by row rank, local KKT parity, or the
coarser side. The next falsifiable hypothesis changes the *span* of
the multiplier tests to match the actual native trace roles, rather
than renaming a P0/P1 basis or inserting a penalty.

Let `N_h` denote the actual count of native half-cells (twice the
beam-element count in this fixture). For the current supported planar
native half-cell fixture, the beam
translational trace uses continuous nodal P1 functions. Its root is
fixed in the small diagnostic, so candidate translational tests span
the free nodal hats `N_j`, `j=1,...,N_h`. Native yaw uses independent
cellwise retained rotations, so its tests span each native half-cell
indicator `chi_k`, `k=1,...,N_h`. Construct exact L2 Riesz duals of
these test functions and integrate each physical channel on the
unchanged beam/shell overlay, with the existing yaw length scale and
signed retained KKT. There are `3 N_h` rows in this fixture. The
dual-basis transformation itself leaves a row span unchanged; the
channel-specific translation/yaw span and explicit fixed-boundary
treatment are the actual hypothesis. An inverse global Gram matrix
may define a bounded proof basis but would make globally supported
dual functions; any production dual must have a derived local-support
construction or an equivalent sparse action.

Before one registered comparison, independently derive and verify:

1. The complete supported native trace block image, nullspace and
   rank after physical and retained support elimination, including
   one-sided yaw traces at half-cell boundaries. A full native row
   image might remove the K2L shell-only restrictions, but that alone
   does not establish physical transfer.
2. Reference consistency, constant/linear translation and rotation
   patches, rigid-motion virtual work, force/moment balance and
   endpoint response. Omitting the root translational hat can create
   uncontrolled endpoint slip; a general support-aware boundary rule
   is needed before product selection.
3. A fixed physical beam/shell trace graph norm that includes native
   cell-yaw jumps. Do not infer a standard continuous H^(1/2) trace
   bound for a discontinuous yaw field. Establish stable primal/dual
   scaling, an exact signed-retained inf-sup or Fortin argument, and
   mesh-ratio behavior for the registered family without an artificial
   penalty or global dense production inverse.
4. Independent analytical or high-resolution physical response
   targets for the Q4/S3 `N_b=8,N_s=1` and `N_b=8,N_s=64` smooth and
   sine loads. Compare shell energy, resolved displacement stations,
   pointwise and weak gaps, traction jumps, moment transfer and
   support reactions. Preserve three joint-refinement levels and both
   reciprocal reaches; do not choose a candidate by a favorable
   single mesh.

If the supported planar screen is promising, extend the actual span
and trace proof to all six pose channels, eccentric work and torque,
director/transverse shear, Q4/S3 transitions, curved/pre-rotated
reference geometry and free or multiply attached boundaries. No
generic line-coupling selection follows from the planar screen.

This recommendation received an independent read-only mechanics
review after K3. It has not passed the stated derivation, reference,
stability or physical-response obligations. F03/G0B remain open and
G1 production integration remains barred.

An unregistered six-mesh rank/physical screen subsequently found full
native row rank but near-zero coarse-Q4 sine shell work and persistent
sampled smooth gap under shell-only refinement. See
`B3_GE_E4_PL_G0_F03_K4_EXPLORATORY_SCREEN.md`. The simple span is no
longer a recommended registered candidate without a new mechanics
argument; this design record is retained to explain the tested hypothesis.
