# F03 finite-pad independent-axis diagnostic protocol

22 September 2026. **Experimental G0B diagnostic, not a physical-reference
acceptance gate.** The four-case feasibility result showed exact assembled
equilibrium but large changes in root and first-quarter reactions under
simultaneous refinement. This protocol isolates which discretization drives
those changes before selecting a continuum reference or production trace.

The physical model is unchanged from the registered v2 feasibility screen:
four distinct `.10 × .10 m` square material pads centered at
`(±.20, ±.23) m`, fixed `.05 m` halfwidth, separate classical beam and
Q4/CST-CB shell operators, P1 exact multipliers, the same smooth beam load
and supports, and single-thread solves. Nominal beam-section dimensions
motivate an *illustrative* pad size but do not establish a real connection.
The older four-point model and its failed physical-reference evidence remain
separate.

The source-frozen runner `b3_e4_f03_area_axis_refinement.py` registers a
baseline `(Ns,Ny,Nb,Nm)=(8,16,16,8)` and the following two variants for
each coordinate, for both Q4 and checkerboard CST-CB: shell x `4/16`, shell
y `8/32`, beam `8/32`, mortar `4/16`. With the baseline, each axis has three
levels and the unique inventory is 9 meshes × 2 topologies = 18 cases.
No axis is changed along with another in a variant. The baseline is a
fresh source-bound execution, not a relabeled prior sample.

The fresh Q4 and CST-CB baseline observable files must reproduce the v2
terminal payloads byte-for-byte under the same dependency/platform/thread
identity: respectively SHA-256
`a8e4496734b3225bd727b033bc623857543a90bebec4731b1181ec713fa22a9c`
and `9e492bd09e2abf1c7d604e1be2abb613a1e2f58ca2d0e18c209a6087498bba3a`.
The v2 registration SHA-256 is
`9bdf3d4f7c63f86e27d8fea63fc11f81631fe8358c3df9c11dc90b0a29d2560f`.
This parity rule covers unchanged physical computation and JSON output;
the runner binds the expected payload hashes and rejects a baseline mismatch.
Timing and process identity are outside the observable payload. A mismatch
requires investigation and remains visible even if algebraic checks pass.

Each new case additionally preserves `solved_state.npz` with independently
owned float64 `physical_q` and `physical_lambda` arrays. The first is shell
nodal displacements followed by the classical beam coordinates; the second
is the signed P1 multiplier coefficient vector used in the assembled
system. The child event binds the binary file hash; supervision and final
adjudication check array names, dimensions, finite values and hash before
accepting evidence. These diagnostic arrays are not native-owner
checkpoints. They permit independent recovery of root traction, fixed
physical subband resultants, endpoint gaps and interface mode diagnostics
without rerunning a consumed case. Saving them does not change the v2
observable payload or its baseline-parity requirement.

Each case retains the registered 900-second and 8-GiB 100-ms-sampled
child-RSS caps and numerical algebraic screens. Execute serially, with a
20-minute orchestration launch budget: stop starting new cases when that
elapsed campaign time is reached, preserve the accepted evidence prefix,
and report the unfinished inventory. This is a launch budget, not an
additional hard kill inside an already supervised case. Preserve
the source/environment registration, child phase logs, sampled resource
receipts, raw signed observables and final adjudication. Failure consumes
that case under its registration; do not retry or hide it. The feasibility
runner's independent raw energy, support-balance and root-partition checks
still apply. No physical match or convergence status is assigned by that
adjudicator.

Report all three support wrenches; beam-root elastic, port and applied-load
terms; all four port-quarter resultants about the same origin; three shell
stations; beam tip translations and yaw; energies; weak and integrated L²
gaps; KKT dimension and nonzeros; and failure/resource work. Compare signed
components first. For descriptive cross-mesh percent changes, divide the
absolute difference by the larger absolute endpoint value and list the
dimensional difference as well. Components near zero are reported in
physical units, without a relative percentage. The diagnostic cannot
declare saturation from any single small pair or replace the three-level
physical convergence studies in the main programme.

After its independent evidence review, decide which operator/axis needs a
larger or redesigned model. The separate nonaffine clipped-host oracle,
operator swap, certified pointwise/endpoint gap, P0 and sine histories,
matched external solver and native B3-GE/E4-PL mechanics remain open.
G0B is not passed and G1 remains barred.
