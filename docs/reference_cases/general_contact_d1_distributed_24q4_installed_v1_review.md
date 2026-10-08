# Installed 24-Q4 distributed shell cycle: narrow review

The [registration](general_contact_d1_distributed_24q4_installed_v1.json)
(SHA256 `bf4f7290a7aa9897c72aafaaf7a20fec6da5f4137e1e2c05756866d1fe0cccfb2`)
was committed as `ecd2fad3` before the one installed example run. The wheel
from `c55c3860` has SHA256
`dcade18155bd1e5f1e2b98b6869711c07f7ba06435877f75a13a05062f304c81`.
The runner and case-builder blobs match the registered versions, and the
solver/example paths did not change between that wheel source and this run.

The [raw installed report](../../reports/general_contact_d1_distributed_cycle_24q4_installed_v1_20260927.json)
(SHA256 `e16d53f6a34d9547b6dd38f89fa1eddca388bc758821578c2a99c8c9853e79dd`)
records twelve completed steps, a restart checkpoint and an `anysolver`
module under the isolated install target. The [adjudicator verdict](../../reports/general_contact_d1_distributed_cycle_24q4_installed_v1_verdict_20260927.json)
(SHA256 `3866451a637d60c1912f5eefdb1024e8ab0287de9fdd603e6513a056d10cd2c3`)
passes every implemented numerical predicate. Against the independently
accepted source reference, all twelve ordered normal forces, minimum gaps,
pressure changes and active-pressure counts match exactly. Full-load normal
force is 0.103878837255225 N; first unload is 0.0398439616559074 N; the
last minimum gap is −2.01624e−8 m, within the registered 50 µm budget.

Independent read-only review checked the wheel/reference/registration/raw
hashes, source blobs, installed import location and all twelve rows. It
supports the **narrow installed 24-Q4 cycle parity** claim. The verdict does
not itself check installed elapsed time. The registration commit timestamp is
20:09:02 UTC; the completed raw artifact's creation and last-write time is
20:24:44.3778806 UTC. Since launch followed the commit, the host timestamps
bound time to completed artifact creation by 942.38 s, below the registered
1200 s cap. This is an external upper bound conditional on stable host clocks
and unchanged file metadata, not a directly measured command duration or a
timestamp of process exit. The reviewer checked this provenance separately.

This verifies the bounded installed solver/example route. It does not accept
complete C1, application adapters, release, deformable target motion or the
remaining contact programme.
