# S4 Stage-M Candidate-A constrained derivation status

Status: `BLOCKED_PRIMARY_SOURCE_UNAVAILABLE`; no Candidate-A equation has
been implemented or numerically classified.

## 1. Content-addressed boundary

This status is governed by
`docs/S4_STAGE_M_MECHANICS_SELECTION_PLAN.md`, raw SHA-256
`4AE07F5954C9A2E6E6B002BEA24A9FC274B528D405EE6E5FCACE630893021E5B`,
and the independently accepted source manifest
`docs/reference_cases/s4_stage_m_source_manifest.json`, raw SHA-256
`22B7B9D56DCC180CEE29F43AD4F31C69547A7C74CB212FD5B7D301909A8C0BE6`.

The required primary source is D. D. Fox and J. C. Simo, *A drill rotation
formulation for geometrically exact shells*, CMAME 98 (1992) 329-343, DOI
`10.1016/0045-7825(92)90002-2`. The accepted manifest records lawful local,
metadata, publisher, and full-text acquisition attempts. No renderable PDF was
obtained; direct access stopped at publisher 403/CAPTCHA/authentication
boundaries. No access control was bypassed.

Consequently Candidate A has no frozen continuous constraint equation,
multiplier functional, finite-rotation branch, configuration derivative,
discrete multiplier space, quadrature, or inf-sup pair. Secondary descriptions
and recollection cannot fill those gaps. `equation_implementation_authorized`
remains false, `candidate_a_classification` remains null, and no Candidate-A
mechanics run is authorized.

## 2. Source-independent necessary theorem

The following basis-invariant theorem is an input gate, not a Candidate-A
classification. For the flat four-node reference element, let `q in R^24`,
let the literal published operator satisfy `rank(B)=16`, let `R` be a six-column
rigid basis with `rank(R)=6` and `B R=0`, let a future source-derived
constraint Jacobian satisfy `rank(C)=p` and `C R=0`, and let `T` have full
column rank with `range(T)=ker(C)`.

An admissible constraint must preserve every published energetic direction and
leave exactly the physical rigid nullspace:

```text
rank(B T)=16,
T ker(B T)=range(R).
```

Rank-nullity then requires

```text
dim(T)-rank(BT)=6,
(24-p)-16=6,
p=2,
rank([B;C])=18.
```

Therefore a rank-four Q1 multiplier constraint cannot satisfy both conditions:
its admissible space has dimension 20, so retaining six null directions forces
`rank(BT)=14` and removes two positive-energy directions of the published
operator. No post-result SVD row selection, `{1,rs}` subset, tuned quadrature,
or topology-specific target may repair this failure. A rank-two or
topology-adaptive multiplier space must be derived independently from the
primary variational source and a preregistered stability argument.

## 3. Resume condition and terminal effect

Candidate A may resume only after a lawful, renderable copy of the primary
source is recorded in a new content-addressed source-manifest amendment with
raw PDF hash, size, page count, provenance, cited page/equation locations, and
the source-derived interpolation and quadrature. That amendment requires
independent acceptance before any Candidate-A equation edit or mechanics run.

Candidate B may be derived and evaluated independently as comparison evidence.
Its result cannot select Candidate B or turn this Stage-M state into `GO` while
Candidate A remains blocked. The overall status remains
`BLOCKED_PRIMARY_SOURCE_UNAVAILABLE`.

No production path, selector, assembly, constraint adapter, activation,
integration, push, publication, or cleanup is authorized by this document.
