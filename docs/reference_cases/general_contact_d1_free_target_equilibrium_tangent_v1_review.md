# Actual-equilibrium free-target tangent v1: independent disposition

**Disposition:** Independently accepted for one selected smooth,
fixed-multiplier mixed source/target directional tangent at the recorded
eight-Q4/two-S3 elastic static equilibrium. This is a bounded tangent
capability, not complete C1 acceptance.

The [original registration](general_contact_d1_free_target_equilibrium_tangent_v1.json)
was committed before the single formal run. The [formal raw report](../../reports/general_contact_d1_free_target_8q4_equilibrium_tangent_v1_formal_20260927.json)
(SHA256 `bec5aa71f3811b336230eae9f0e1c7700753ef9ac7a59f83c446a3f63b9db0a1`)
ran for 25.79 s and the [numerical verdict](../../reports/general_contact_d1_free_target_8q4_equilibrium_tangent_v1_verdict_20260927.json)
(SHA256 `df6461b273fbdcf23959079a7a0cfa433bd95c02c8bb5fbcdf68ff814b2c578b`)
passed the frozen gates. Both 3e-7 and 1.5e-7 m backward second-order
stencils kept pressure activity, reference support, overlap and all 16
checked pair derivative branches fixed. Among 40 reduced force and six
moment rows, the largest relative coupled force/moment errors were
3.765e-13/1.117e-13; isolated mapped-contact errors were
1.088e-11/6.498e-11. Each is below 1e-5 and each action exceeds its
separately dimensioned nontriviality floor. The saved press pose was an
actual completed equilibrium with 1.67e-14 N final residual and
5.24e-11 Pa multiplier change; constraint and pressure replay errors
were zero to reported precision.

Independent review found that the original registration had one malformed
46-character Git blob value for `s3_patch_static.py`, and the numerical
adjudicator did not check source blobs. The original registration and
verdict remain unchanged. The [v1a metadata amendment](general_contact_d1_free_target_equilibrium_tangent_v1a_metadata.json)
(SHA256 `027d6ae7cf3b8c96feb6343b58fce185291c17e543c995893b2510bc32a0d4c1`)
corrects only that field to the actual 40-character blob at the frozen
source commit. The [separate identity verdict](../../reports/general_contact_d1_free_target_8q4_equilibrium_tangent_v1a_identity_verdict_20260927.json)
(SHA256 `aa72533dace7e4bf44098c4702afb07bd3d5347781f373612ee3ee643f5cf0cb`)
passes original registration/raw/verdict hashes, the one-field correction,
all six source blobs and unchanged mechanics criteria. The independent
reviewer accepted the narrow claim from the combined v1/v1a evidence.

The earlier 8e-7 m development stencil crossed pressure activation and
remains inconclusive. The accepted result holds multipliers fixed and
uses fresh elastic element state. It does not establish multiplier-update
derivatives, arbitrary directions, branch crossings, a complete tangent,
history-dependent material state or general C1. The raw report stores
scalar derivative error and action summaries rather than full derivative
vectors; the reviewer independently recalculated gate extrema and source
binding but did not reconstruct the underlying derivatives without a new
solve. Run-once provenance rests on the committed registration timing,
write-once execution path and owner record, not a cryptographic counter.
