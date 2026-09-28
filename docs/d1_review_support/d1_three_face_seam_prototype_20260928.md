# D1 three-positive-face artificial seam — stopped development prototype

At source `4860aaca`, a bounded prototype tried to extend the opt-in
projected Q4/S3 artificial-seam limit from two to three positively
overlapped target faces. The proposed check selected a unique incident
two-face edge owner and compared that pair's local force and tangent at
the existing one-sided sample poses. The [prototype patch](d1_three_face_seam_prototype_20260928.patch)
is retained (SHA-256
`3a727e601163342547114a12c14d57bae5240aaae3687348ac3eb79f233a972a`).
It was **not** promoted; production source and focused tests were restored.

The discriminating Q4 has projected vertices
`(-.6,.25),(.25,.25),(-.1,.75),(-.6,.75)` against the existing three-face
planar S3 target. It overlaps all three target faces and touches the
internal 0/1 diagonal at one vertex. The prototype selected unique owner
`(source face 0, target faces (0,1), shared nodes (1,3))` and entered the
seam fallback. The new case did **not** pass the unchanged derivative
checks:

| Development attempt | Outcome |
|---|---|
| Step `3e−8 m` | Full-patch centered quotient error `1.5635e−4` |
| Step `3e−6 m`, tolerance `2e−5` | Rejected: reduced tangent columns disagree; 19.24 s |
| Step `3e−6 m`, tolerance `1e−5` | Rejected: tangent limit relative error `1.05073596397e−5`; 20.00 s |

Two existing three-face ownership/rejection tests passed (5.35 s;
15 unrelated tests deselected). Each reported attempt remained within the
180 s development time cap; peak memory was not measured. The monolithic
raw-force path was not extended or tested for three-face admission.

**Decision.** Keep the production `<=2` positive-face guard and explicit
rejection for three-face transitions. The current prototype does not close
the D1 monolithic clipping gap. Any future extension needs a local
incident-pair certificate in both projected and raw-force work and a
fixture passing the existing one-sided derivative gates without tolerance
tuning. Preserve this failure and avoid another sweep without a new
discriminating hypothesis.
