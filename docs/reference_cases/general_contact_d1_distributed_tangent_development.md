# Distributed 24-Q4 contact tangent: bounded development audit

The accepted distributed full-cycle report supplies the final 324-DOF pose
and 50 committed multiplier estimates. The probe rebuilds the same planar
Q4/S3 model and holds those multipliers fixed while differentiating the
contact-law residual along source nodes 20 and 45 (ux and uz at each).
The saved pressure replays exactly; 18 pressure modes are active. The local
source residual is −0.103878837255226 N, opposite the reported integrated
physical reaction, with a 1.39e−17 N balance defect.

The first [raw diagnostic](../../reports/general_contact_d1_distributed_24q4_selected_tangent_dev_20260927.json)
(SHA256 `80ea8b969ac924058b093e60f8bf0d22eb05233a31dd7fb157b351cb3d745aa7`)
was stopped by the probe's incorrect residual/reaction sign comparison.
It did not reveal a mechanics mismatch and remains preserved. The corrected
[four-axis report](../../reports/general_contact_d1_distributed_24q4_selected_tangent_signfix_dev_20260927.json)
(SHA256 `1fcf23e59987fb7e8ec05028d701b20ce3410f1626a78c6c0ff85cc6a9758475`)
has relative errors 3.281e−10 and 8.239e−11 at h=1e−6 and 5e−7 m.
Independent read-only review confirmed the sign convention, fixed
multipliers, selected-row comparison and unchanged active/support/overlap
branches. This is valid local **development** evidence, not an independently
accepted complete tangent.

The later [98-row free-source report](../../reports/general_contact_d1_distributed_24q4_wide_source_tangent_dev_20260927.json)
(SHA256 `0fa050da62f25ab881b4e6a98a32773b90453d1d1d8fc2522bc0cb0386cc008f`)
uses all free source ux/uz rows and the same four-coordinate perturbation.
It replays pressure exactly, checks four touched Q4/S3 branch signatures,
and gives relative errors 2.888e−10 and 7.247e−11 at the same two steps;
the action scale is 78.86 N/m. This broadens the contact-law cross-row
check but does not include target reaction rows or the structural shell
tangent, contact-to-structure mapping and constraint reduction.

The [coupled assembled report](../../reports/general_contact_d1_distributed_24q4_coupled_tangent_importfix_dev_20260927.json)
(SHA256 `4c1ccb1549cb4b6d88efb84a23c0aca1318c1686dfa99a747f33c162a4383490`)
adds the structural Q4/S3 work, contact pullback and 98-DOF constraint
reduction. Its directional errors are 6.929e−11 and 1.746e−11. The first
probe attempt stopped before mechanics evaluation because it imported
`assemble_stiffness_matrix` from the wrong module; the corrected run used
`anysolver.matrix_assembly`. Structural stiffness dominates this coupled
action, so the total relative error alone could mask a contact error.

The [mapped-contact report](../../reports/general_contact_d1_distributed_24q4_mapped_contact_tangent_dev_20260927.json)
(SHA256 `94495b587daeef1bf640e18589e75ae05b1d4bcf557a07d3cceddfbc3e04ac03`)
subtracts structural-only force and tangent assembled at each identical pose.
At fixed saved multipliers, the reduced contact action is 78.8628 N/m;
its errors are 2.892e−10 and 7.278e−11 at h=1e−6 and 5e−7 m.
The active, support, overlap and four touched-pair projection branches stay
unchanged. Every structural material trial is discarded. Independent read-only
review found the subtraction and state handling sound for this elastic pose.
These are meaningful **development** checks of the implemented mapped residual,
not an independent physics oracle or claim-bearing complete C1 tangent result.

The next decision is whether to register a distinct claim-bearing tangent
case with frozen source, direction, steps and reference, then obtain independent
assessment. Pressure-space stability and installed 24-Q4 verification also
remain open. None of these development probes changes a frozen criterion or
establishes general C1.

## Fixed-target coordinates and a pressure kink

The accepted 24-Q4 case constrains all four S3 target nodes. Its 98 reduced
coordinates therefore test mapped source work but cannot vary target motion.
A separate unconstrained **contact-law** probe used the same saved geometry and
pressure estimates. A two-node target tilt gave central-difference errors
3.21% and 0.946% and failed its smooth-branch condition
([raw tilt](../../reports/general_contact_d1_distributed_24q4_target_tangent_dev_20260927.json),
SHA256 `0e1eb8aab24fdb6841fe257a4d1118796570fcb0ea1163894200325ba8e38fb9`).
A rigid target z motion also failed its central-difference branch condition,
despite unchanged overlap and pair derivative signatures
([raw rigid shift](../../reports/general_contact_d1_distributed_24q4_target_rigid_tangent_dev_20260927.json),
SHA256 `41c29d6d99c7e1d6ad54848ce3f13727b03b778af5bc3f5b59e87494f93b4f1b`).

The [pressure-margin diagnostic](../../reports/general_contact_d1_distributed_24q4_target_pressure_margin_dev_20260927.json)
(SHA256 `2abb69b8d2f9664cdb04e4aac8f9da4763829f5bc33e28720a26d3c8f785edb9`)
identified the cause: modes 15 and 40 activate under both positive target
motions at h=1e−6 and 5e−7 m, while negative motions retain the original
18-mode set. A central difference crosses a contact-law kink.

The [negative one-sided target check](../../reports/general_contact_d1_distributed_24q4_target_rigid_one_sided_dev_20260927.json)
(SHA256 `1f993b60cf50e631f79ad0789ccc4d9ece312b02b578a4fba6022f5a269082c4`)
kept the 18-mode branch, all 50 support nodes and every checked overlap and
projection signature. Its 162-row contact-law action has source and target
components of 376.22 and 933.08 N/m; one-sided relative errors are
5.128e−12 and 2.725e−12. This checks the selected generalized derivative
from the inactive side at a pressure kink. It does not qualify the active
side, a deformable target's structural pullback or general target motion.
Independent read-only review checked target-coordinate indexing, the
one-sided quotient sign, all 48 pair signatures and the pressure-mode changes;
it found no narrow code or sign issue in this development result.

## Direction selection at the accepted fixed-target pose

The coupled development probe now permits separate `ux` and `uz` source
directions without changing the historical registered probe result. At the
saved full-load pose, a combined direction at source nodes 7/32 remained
smooth but had zero mapped contact action and was inconclusive for contact
([raw](../../reports/general_contact_d1_distributed_tangent_nodes7_32_dev_20260928.json)).
A combined direction at active nodes 23/48 passed the selected smooth
derivative check with mapped contact action 78.8628 N/m and relative errors
2.88e−10 and 7.29e−11
([raw](../../reports/general_contact_d1_distributed_tangent_nodes23_48_dev_20260928.json)).

At the originally registered active nodes 18/43, `uz` alone reproduced a
78.8628 N/m mapped action and errors 2.88e−10 and 7.20e−11
([raw](../../reports/general_contact_d1_distributed_tangent_uz_nodes18_43_dev_20260928.json)).
`ux` alone remained smooth but its mapped contact action was only about
2–4e−11 N/m, below the 1e−6 N/m meaningful-action floor
([raw](../../reports/general_contact_d1_distributed_tangent_ux_nodes18_43_dev_20260928.json)).
An `ux` direction at the active edge nodes 17/42 was similarly action-free
([raw](../../reports/general_contact_d1_distributed_tangent_ux_nodes17_42_dev_20260928.json)).
Those relative contact errors are cancellation dominated and are not tangent
failures. The planar near-uniform gap and fixed target make this pose a poor
discriminator for tangential geometry derivatives. A future complete-tangent
gate needs a separate admitted pose with finite overlap-gradient/contact
action or a declared one-sided geometry feature. No additional direction on
this pose is automatically warranted.

## Subsequent local tilted-target discriminator

The later [finite-area tilted-target local screen](general_contact_d1_tilted_target_local_tangent_development.md)
found a smooth target-x direction with measurable mapped force and moment
action. Its physical target tilt was disposable and not an equilibrated solver
state, so the complete coupled tangent and C1 disposition remain open.
