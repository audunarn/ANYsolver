# Multiple actual-cap deformable S3/rigid contact — development

`MULTIPLE_EXPLICIT_B2_B3_HEMISPHERE_DEFORMABLE_S3_FIXED_RIGID_STATIC_DEV_V1`
is implemented and installed-tested. Independent engineering acceptance,
application admission and release remain open.

Run `examples/general_contact_multiple_beam_s3_caps.py`. Declare explicit pairs
from one-cell B2/B3 round selections with hemisphere caps to individual physical
S3 skins. Multiple independent pairs may share a beam or target. Optional fixed
plane/sphere pairs may be included. Select actual cap work and
`beam_shell_geometry="jet2_deformable_s3_dev"`; declare line N/m² and endpoint N/m
stiffness, dimensional gap tolerance, rim clearance and finite swept budgets.
The example presses one beam against two genuinely deforming orthogonal S3 skins.

Each child preserves its admitted equations/work map. S3 translations and moving
normals participate in complete work/Hessian blocks; fixed director offsets retain
structural couples. All contributions use the same authoritative candidate and
sparse assembly before ordinary structural constraint reduction. This profile
uses fixed target rotational coordinates and isotropic elastic von Karman
classical beams. Existing native analysis ownership is not changed.

Pairwise minimum gaps and tolerances remain independent acceptance gates.
Every child certifies the common path/prefix. No contact is discarded under the
aggregate pair cap. Duplicate physical beam/target-side features, conflicting
shared beam envelopes, unreferenced participants, unsupported controls and
invalid geometry fail explicitly. Genuine ends use all material-node incidence.

Results expose per-pair fields and wrenches grouped by physical beam/shell element
and named rigid body, about zero. Endpoint counts are endpoint/target counts.
Restart binds global and effective per-child settings plus every child contract;
rigid children explicitly use their existing `translated_planar` setting. Single
S3 and pure-rigid profiles, historical defaults and no-contact behavior remain.

## Verification and limitations

Installed50checks pass34.436s, peak357175296B;225loaded modules and507package
files match source. JIT disabled, NumPy/SciPy pools and Numba1;180s/953MiB bounds.
Independent combined work/1e-5H/couples, actual two-deforming-target force and
displacement control, active restart, actual later-child failure/cancellation,
shared target and true endpoint/midnode junction, optional plane/sphere driver
and checkpoint, duplicate/resource/rim rejection, legacy and no-contact pass.

Independent four-coordinate contact-gradient error8.358e-12 against1e-6; response
error8.798e-6 against1e-3 for an explicitly linearized structural reference.
Both target movements are about-2.92mm. Minimum gap-3.820e-7m meets1e-5m.
The reference includes cross motion through both moving normals and is checked
only within its open-root/active spherical-tip branch domain. It is not an
independent nonlinear structural qualification or unrestricted contact oracle.
A focused installed replay retained its unique response file after identifying
an output-name collision in the combined suite; unaffected checks were not rerun.

[Evidence](d1_review_support/contact_multiple_beam_s3_caps_20261004/summary.json)
contains seven runs and46raw records. Source01's four fixture/API failures remain,
alongside corrections and the supporting review. The reviewer found initial plane
endpoint-count serialization and effective rigid restart-setting omissions; both
were corrected before the first run. Supporting same-family review is not
independent engineering acceptance. No speed improvement is claimed.

These are independent whole-beam/interior-face pairs, not a clipped patch union.
Each child retains radius-covering rim clearance. Physical rims, native multiple
patches, finite target rotations, friction, moving rigid tools, cylinder support
transitions, impact, mesh/enforcement qualification and C0–C9 completion remain.
