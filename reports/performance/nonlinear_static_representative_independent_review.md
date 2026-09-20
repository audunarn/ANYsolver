# Representative nonlinear evidence: independent review

## Outcome

**ACCEPT.** No remaining correctness or evidence-integrity findings.

The independent mechanics review checked the immutable formal result, bounded
offline adjudication, installed-wheel identity, diagnostic profiles, acceptance
math, and selected successor. It confirmed the performance **GO** and Armijo
**NO-GO** decisions.

## Finding and closure

The first review found that the adjudicator and profiler loaded a mutable
campaign helper without binding its exact identity. The final versions fail
closed before import unless the campaign runner SHA-256 is
`44d83a6d0889dee3364cfb6ade50c73add8a4ec0d8375349d7ac48ee12b5424b`.
The profiler additionally requires `_build_case` SHA-256
`f1cf32fb23e544b2d83672ec7c790d07ae944ede6ea9de857f7fd06fffae2933`,
which the reviewer independently matched to frozen campaign revision
`909929ee`.

The three diagnostic profiles were regenerated with those checks and still
support every timing, call-count, hotspot, and successor-guard claim. The
formal performance campaign was not rerun.

## Evidence checked

- Compressed raw evidence SHA-256:
  `22a9edd80f3f6ff91a3498f445172032a535f5806ad4a77d2d40931f6baa957f`
- Decompressed raw evidence SHA-256:
  `48691e0557d9b57bcab378c20a87a84d8c9ebd8ab1693683c278030b15bc2d8c`
- Terminal adjudication JSON SHA-256:
  `4fab02974d4c815759a85920fc8a16a9c92149d2bc3643e08a6f76fd8d303593`
- Profile synthesis SHA-256:
  `d29d0b497f796bee43be472abeb165f4f58a867699b0f8df72bc649721c26e60`
- Focused harness and identity tests: **18 passed**
- Staged diff check: **passed**
