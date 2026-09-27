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

The governing next check is an assembled structural-plus-contact free-DOF
directional tangent audit at this saved smooth pose, with the same ≤1e−5
target and explicit branch control. Pressure-space stability and installed
24-Q4 verification also remain open. None of these development probes
changes a frozen acceptance criterion or establishes general C1.
