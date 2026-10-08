# Curved native static contact — supporting scrutiny, 4 October

Source candidate: `14fedcbe`, following `83b40d0c`. Reviewer: `/root/curved_initial_review`, Read only,
same OpenAI model family. This is development scrutiny, **not independent
engineering acceptance**. No reviewer numerical executions or source edits.

## Findings and disposition

- Whole-patch affine translation/left spatial Exp path controls retain chord,
  frame, internal rotation, orientation and gap bounds. Endpoint-only admission
  is insufficient; independent hidden inversion and gap-pulse witnesses reject.
- Norm-only frame bounds were excessively conservative for planar zero-roll
  geometry. Projected first/second derivatives retain exact binary plane and
  stored-tangent misalignment. Use requires an unclipped interval; general
  rotation/roll cases retain full-frame bounds. Taylor exclusion now also
  requires an unclipped interval.
- A tiny endpoint arc could be lost by rounded angular roots. Endpoint/extremum
  resolution checks retain full uncertain measure; the counterexample is tested.
- True active angular measure did not necessarily cover an unsplit fallback
  Gauss weight in a tiny grazing pocket. The corrected budget covers the true
  union **and** both actual approximate active-weight masses. Fallback energy
  and force use direct full-work bounds; tangent retains twice the complete
  integrand bound. The pocket centred on a 16-point Gauss node is tested.
- Complete scaled gradient and gradient-derivative norms, rotational Hessian,
  once-only spatial correction and nine-coordinate matrix-infinity conversion
  supply the root-band tangent bound. Translation/rotation cross blocks remain.
- InstalledV6 exposed a reference-case regression from overly broad direct
  fallback charges. V7 selects a resolved interior station when possible,
  caches it for both rules, encloses the whole band relative to that station,
  and uses the safe width²/2 axial Lipschitz variation bound. A bracket without
  an interior float explicitly reports parameter-resolution non-success.
- Owner assembly converts the spatial tangent once. Distinct profile, numerical
  revision, trial policy and tolerances bind restart. Accepted state changes
  only after staged record validation and precommit cancellation.

No further consequential defect was identified in the final reviewed deltas.
Gauss8/16 differences remain estimates, not rigorous quadrature certificates.
Adaptive station switches remain approximation choices, not exact smooth
derivatives across those switches.
The retained test corpus is one elastic beam/fixed-plane workflow plus local
geometry/work controls. Plastic curved contact, multiple bodies, finite obstacles,
friction and dynamics are not admitted by these results.

Failed runs remain in
`C:/ANYworkspaceWork/contact_native_material_s3_20261004/candidate10` with their
inputs, resource records and logs. This includes the initial budget/gap failures,
the mistaken lateral-skin experiment, conservative full-fallback-measure failure
and the inappropriate exact-byte unloading/reloading assertion. A corrected test
does not retroactively pass its failed predecessor.
