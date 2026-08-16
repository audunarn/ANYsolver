# Candidate-A1 exact rank certificate

Status: `PROVEN_FAIL_CANDIDATE_A1_FLAT_RANK`, with pair-gate result
`PROVEN_FAIL`, for the isolated Candidate-A1 rank and energetic-preservation
gate. This certificate does not classify Candidate A2 or the aggregate
Candidate-A route.

## Frozen inputs

The certificate is derived only from the accepted flat-square identities at commit `148ccb45ba79266d48dae1a84c4c500bdc1b4d85`:

- the published operator has `rank(B)=16` and `nullity(B)=8`;
- its kernel consists of six independent rigid vectors `R`, the constant-drill gauge `G`, and the positive-mass alternating-drill mode `Z`;
- Candidate A1 is the registered D4-invariant multiplier space `span{r,s}` with M-orthonormal basis `(sqrt(3)/2) [r,s]`;
- the registered exact raw moment rows are `C_r` and `C_s`.

The machine certificate binds the accepted derivation, cases, and nullspace
proof by canonical Git-style LF byte size and SHA-256, independent of checkout
EOL conversion. Bare CR or mixed CRLF/LF input fails closed. The certificate
also records every vector and exact identity used below.
Its canonical UTF-8/LF bytes have SHA-256
`2198458DCDC7EFB4684B5CC59ADAF6E9A0EECF381951CBDD21B286D6DB11097C`.

## Exact kernel action

Use node order `(-1,-1),(1,-1),(1,1),(-1,1)` and per-node coordinates `[u,v,w,theta_x,theta_y,psi]`. Exact `Fraction` arithmetic gives

```text
C_A1 R = 0,
C_A1 G = 0,
C_A1 Z = 0.
```

The eight recorded vectors are independent: their selected 8-by-8 coordinate minor at zero-based rows `[0,1,2,3,4,5,7,11]` has determinant `4`. Since the accepted nullity of `B` is eight, these witnesses span `ker(B)`. Consequently

```text
ker(B) subset ker(C_A1).
```

The raw constraint rows have a 2-by-2 minor on columns `[0,1]` with determinant `-1/9`. Multiplying both rows by the registered radical normalization `sqrt(3)/2` changes that determinant by exactly `3/4`, giving `-1/12`. Thus `rank(C_A1)=2` in both raw and registered normalization.

## Rank consequence

Because `ker(B) subset ker(C_A1)`, the stacked operator has

```text
nullity([B;C_A1]) = 8,
rank([B;C_A1]) = 24 - 8 = 16.
```

For any full-column basis `T` of `ker(C_A1)`, `dim(range(T))=24-2=22`, and the restricted kernel still has dimension eight. Rank-nullity therefore gives

```text
rank(B T) = 22 - 8 = 14.
```

Candidate A1 fails both mandatory targets `rank([B;C])=18` and `rank(BT)=16`. It leaves `G` and `Z` unconstrained while removing two energetic directions from the published strain image.

## Boundary

This is an exact necessary-condition failure. It uses no NumPy, SVD, floating rank tolerance, Candidate-B output, penalty, stabilization, production source, or selector. Candidate A2, finite rotations, global inf-sup stability, enforcement architecture, and production activation remain untouched.

Machine-readable certificate: `docs/reference_cases/s4_candidate_a_open_a1_certificate.json`.
