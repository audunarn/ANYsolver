# Standalone D1 example with independent physical gap and split restart

The standalone four-Q4/two-S3 deformable-target example now saves accepted
poses and reconstructs both physical shell skins without calling the contact
geometry or work kernel. On its planar XY-overlap footprint it bounds the
target-normal gap by subdividing Q4 parameter boxes at triangle-footprint
boundaries. Invalid conditioning, orientation, box-budget exhaustion and
unresolved overlap fail explicitly. The check does not claim closest-point or
edge-only contact.

# Gap-only development check

The first gap-only example SHA-256 was
`d228ec40ac0480f65cb21877664c0c0b82a4bec2436107713ddd30b269b45d70`.
It ran from the source checkout at `4abcc181` and as an unchanged standalone
copy outside the checkout against the isolated `df37e784` wheel (SHA-256
`658920683c674b0f117127e1210be7612b7142ab5b1f0ed708655f`). The
installed process reported `anysolver.__file__` inside its isolated target.
All eight local and installed result fields match after excluding that module
path. The minimum independent bound was −2.3330296 µm under the declared
50 µm gap budget. An independently introduced 1 mm downward displacement at
source node 2 caused the bound to reject the pose.

The [local result](d1_example_independent_gap_local_result_4abcc181_20260928.json)
and [installed result](d1_example_independent_gap_installed_result_4abcc181_20260928.json)
retain each step's solver and independent gaps. The bounded local run took
22.08 s/332.30 MB and the installed run 21.62 s/317.02 MB; these are not
paired performance comparisons. [Local resources](d1_example_independent_gap_local_resource_4abcc181_20260928.json)
and [installed resources](d1_example_independent_gap_installed_resource_4abcc181_20260928.json)
are retained.

# Split restart development check

The example then gained an open-state checkpoint after step six and a fresh
model continuation through recontact. This final example has SHA-256
`1c74ff3065c9719542303743167491e660e23f16a2ea6486495129f455dd68ce`.
The [local result](d1_example_gap_restart_local_result_4abcc181_20260928.json)
and [installed result](d1_example_gap_restart_installed_result_4abcc181_20260928.json)
both complete eight steps. Split and uninterrupted final displacement and
integrated contact force differ by zero in each process. After excluding the
loaded module path, the complete local and installed result fields match. The
installed path points inside the isolated `df37e784` wheel target. Both
processes report the same worst independent gap lower bound,
−2.3330296 µm, within the declared 50 µm budget.

The bounded [local resources](d1_example_gap_restart_local_resource_4abcc181_20260928.json)
were 38.52 s/404.64 MB; [installed resources](d1_example_gap_restart_installed_resource_4abcc181_20260928.json)
were 41.08 s/397.75 MB. These runs include the uninterrupted and split paths
and are not paired performance comparisons. An initial example assertion
mistakenly expected only two steps in a resumed result; the restart API includes
the six checkpointed steps and two new ones. The failed
[assertion log](d1_example_gap_restart_assertion_failure_4abcc181_20260928.txt)
and [resource record](d1_example_gap_restart_assertion_failure_resource_4abcc181_20260928.json)
are retained; the assertion was corrected without changing solver mechanics.

This closes an independent gap check over the represented planar overlap and
an open-to-recontact split restart in the development example. Gap checks use
accepted endpoint poses, not a conservative swept path certificate. The check
does not establish general rims, creases, edge-only collision or complete D1
acceptance.
