# Multisegment stationary-front history — development, 2 October 2026

**Three-segment scalar-history integration passes. Native coupled second loading/split
restart remain unpassed; this does not establish engineering acceptance.**

The explicit mixed helper admits exactly one stationary H branch over all saved segments.
Every other complete cover must have no stationary root and strictly nonzero B. Strict
openness at every captured pose over the whole stationary envelope then proves those
segments remain open there by monotonicity of H. Only the branch-owning segment contributes
strip work; all material outside the strip still receives the full replay path. Earlier
segments remain fixed when taking the endpoint force tangent.

The work bound now accepts an explicit owning segment index and reconstructs its start
through the full prefix, including native motion and shell displacement. Unspecified
multisegment calls still reject, preserving the historical helper contract. Resource,
uncertainty, ownership, orientation and captured-pose guards remain unchanged.

## Review and correction

Owned OpenAI independent source scrutiny supports the restricted geometric argument.
Review caught incorrect routing of an earlier pulse's uncertainty into final-increment
dissipation/release. The initial integrated run reproduced that defect: final increment
contained5.184509431771925e-16J despite its suffix being open. The bound now populates only
cumulative dissipation when its owner precedes the final segment. Earlier pulse release
is not reported as final-segment release. Initial source and failed outputs are retained.
This source review is not different-model-family or engineering acceptance.

## Checks actually run

- Initial controls:2passed/1failed. Actual prefix bound matches the bound from its
  reconstructed starting configuration; independent scalar32-step Coulomb work and
  released-storage bounds pass. Unspecified multisegment/index guards pass.
- The failed negative fixture started in penetration and was correctly rejected by
  the existing history constructor. Corrected it to start open, enter contact at an
  intermediate captured pose, then reopen before the stationary pulse. That case is
  explicitly rejected by the full-envelope captured-pose guard:1passed.
- Initial integrated candidate:66.80s test,72.1575s runner,218202112B sampled peak.
  Cumulative reference and zero force/tangent passed, but final-increment zero failed.
- Corrected translated-prefix/middle-pulse/open-suffix candidate:1passed,69.81s test,
  73.56s pytest. Cumulative work2.282983631740072e-6J versus independent scalar reference
  2.2829836420253866e-6J (~4.5e-9relative). Force and complete endpoint tangent are zero;
  storage, final-increment dissipation and final-increment release are exactly zero.
  Queries976,pointpaths3904,panels11,accepted6. Global scaled error estimate0.27732982.
  Only cumulative strip uncertainty5.184509431771925e-16J remains. Same original settings
  and180s/953MiB resource limits; no native owner or installed run.

Raw logs, runtime/selection/resource files and outputs:multisegment_front_results_raw.zip.
Exact source hashes/resources:multisegment_front_source.json.
Failed source:multisegment_initial_candidate_source.zip. No consumed run renewed.

## Next discriminator

One local replay from the saved second-load path, without resolving the structure:
retain actual initial pose, both increments, physical map/laws and settings, but explicitly
select xi[.72,.80],angle[3.19,3.20]. This local window contains the known pulse witness and
closed material and is not full-patch or coupled evidence. Apply the restricted helper;
report complete failure/resource/component diagnostics or resolved integration. The
question is whether actual moving-geometry proofs or material integration now control
failure. No caps/tolerance changes, no saved fullpatch retry and no coupled-owner retry.
If the local window resolves, choose the next owner-adapter/proof slice from its evidence;
do not infer global admission from this local check.
