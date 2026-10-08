# Installed D1 example — source impact screen

**29 September 2026. Development evidence.** The isolated wheel used by the
[eight-step installed run](d1_current_installed_interior_gap_20260929.json)
was built from `c0dfc7a194418ec2f8cc348b00bcde366101cb92` and imported
outside the checkout. The run completed press, slide, opening, recontact and
split restart, with independent accepted-pose gaps under the −50 µm limit.

For current local checkpoint `f145487a8e75d3d201e5dd1e11dcc3130e3be997`,
`git diff --name-only c0dfc7a1..f145487a -- src/anysolver pyproject.toml`
is empty. The exact current standalone example has SHA-256
`4FC744756387B64B777D9DDF1A3D4EFAA539CF64138EBE881A636801B66DA885`,
matching the copied example recorded for the installed run. The new
development scripts, tests and documents after `c0dfc7a1` do not change that
installed solver/example pair. The existing installed run may therefore be
reused as **local installed-behaviour evidence** for this mechanics content.

This is not an independent acceptance or released-package claim. A final
claim-bearing installed check needs the frozen source/environment identity,
the then-current capability wording and any affected changed implementation.
The experimental `overlap_local_dev` eight-S3 route was not part of this wheel
example and remains unverified as an installed workflow.
