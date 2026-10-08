# D1 guided planar shell pressure reference — bounded development result

## Question and model reduction

The saved, accepted 16×8 and 32×8 near-rim Q4/S3 poses have a *fixed* S3 target. The Q4 source guide fixes all source director rotations and `uy`; the left source edge fixes `uz`. This check asks whether the active pressure work is detected by the actual shell's admissible transverse source motion, and whether an independently bounded continuum reference can replace the previously unsaturated structural-mesh reference. It does not address a deformable target or a changing contact front.

At each saved pose, the physical pressure work matrix is `B = diag(S) D(gbar)` on the constrained coordinates. An independent current-skin clipper integrates the Q1 pressure mass `G`. The actual E4-PL linear stiffness restricted to all free source `uz` coordinates equals an independently assembled rectangular Q1 gradient matrix times `κGt`, with `κ=5/6`, to about `3e−16` relative. The fitted factor, `1602.5641025641028 N/m`, agrees with `5/6·E t/[2(1+ν)]` from the fixture's material to `1.42e−16` relative. The all-source-`uz` response equals the full constrained shell pressure compliance to numerical precision. The earlier 48-column collocated witness had omitted 96 other admissible `uz` motions; its low `0.0002015` minimum squared ratio does not describe the full transverse space.

The independently clipped active-by-**all free source `uz`** pressure-to-displacement mass agrees with production work to `2.60e−13` relative at 16×8 and `6.13e−13` at 32×8. This completes the local scalar-work bridge that the first Fourier review found missing. The analytic tensor-product Q1 mass agrees with the independent clipped Gram to `1.49e−15` and `3.75e−15`, respectively.

## Independent continuum interval

For this constrained scalar fixture, the reference is `κGt ∫Ω |∇w|²`, with `w=0` on the left edge and natural conditions on the other three edges. The pressure field is Q1 on the source rectangle, clipped by the target at the horizontal `y=0.9 m` source-relative line. The independent helper integrates the piecewise-linear Q1 hats analytically against

`sin((m+1/2)πx/Lx) cos(nπy/Ly)`.

For 512 modes per axis, the finite spectral compliance `C_512` is a lower bound on the ideal scalar continuum compliance. Parseval bounds every omitted mode by

`0 ⪯ C_cont − C_512 ⪯ G/[κGt·λ_first omitted]`.

The coefficient multiplying `G` has units `m³/N`. These are exact-arithmetic bounds; the implemented eigensolves are double precision and do not outward-round interval endpoints.

The generalized eigenvalues of the discrete shell pressure compliance against this interval give the following **development** bounds over the settled active pressure subspace:

| Saved pose | Active modes | Largest omitted-mode bound relative to `C_512` | Interval for the *minimum* discrete/continuum squared dual ratio | Full source-`uz` / full-shell squared response |
|---|---:|---:|---:|---:|
| 16×8 | 48 | 1.284% | `[0.591616, 0.593137]` | 1 within `1.5e−13` |
| 32×8 | 96 | 2.446% | `[0.432783, 0.443156]` | 1 within `5.0e−13` |

The 64×64 initial reference had a 93.18% worst-case tail and was too loose; one targeted 512×512 refinement reduced it. The intervals do not overlap: the decline in the worst settled-active detection ratio across these two meshes exceeds Fourier truncation uncertainty. Two poses do **not** establish decay toward zero, a mesh-uniform lower bound, a stable partial-contact front under refinement, or the 2% physical response gate. In particular, the nine full-supported coarse pressure-work null combinations remain unresolved; only the settled active sets were evaluated. The scalar reduction also depends on the fixed-target, planar guide and the checked reference energy. Do not transfer this result to the deformable-target workflow.

The Fourier helper's independent analytical constant-load check initially failed a test-only requested interval width because 64 x-modes with only 16 y-modes leave a conservative `0.000395` absolute interval width. The bound still contained the exact result; using 64 modes on both axes met the stated interval-width assertion. The final two focused analytical tests pass. No mechanics tolerance or production contact law changed.

## Evidence and next decision

The final bounded replays used [16×8 raw output](d1_guided_fourier512_final_v2_16x8_20260929.json) and [resource record](d1_guided_fourier512_final_v2_16x8_resource_20260929.json) (11.74 s, 314.89 MB process-tree peak), and [32×8 raw output](d1_guided_fourier512_final_v2_32x8_20260929.json) and [resource record](d1_guided_fourier512_final_v2_32x8_resource_20260929.json) (22.21 s, 626.84 MB). Both were below the 180 s/1 GB development cap. A first run imported the other checkout and stopped before mechanics; its [log](d1_source_transverse_witness_log_20260929.txt) and [resource record](d1_source_transverse_witness_resource_20260929.json) are retained. Corrected runs record the isolated worktree module path. Intermediate records with the older unit labels and an upper value for the *maximum* ratio remain historical, not the final interval. The saved fields and earlier failed structural-reference results remain unchanged.

Production base: `f6f17b65` plus offline probe/oracle changes only. SHA-256: runner `06273AB41678A7FE5756702A2FAA77226F10C8EFE601248628DB35F9F7D68095`; Fourier helper `2A323715A85A15E5299F844343F9E6B67CA4583D0699EEA4FA079B6C37DCDC96`; independent clipper `299E2E6F6A7CD46DE667EDE590900A5F8426840AB131FCB0A29C6DB012F84A64`; final raw 16×8 `C1C5DDAB0429049682D9F493799201BEC185517EA3D5A13828ABDF8B94DB0A9A`, 32×8 `EAB855000434AB8890698DCC6F5666A2EEBDC702639DCC95974872A0D0A94304`.

**Decision:** The independently bounded scalar reference can now be used for this guided fixed-target active-space development comparison, subject to the independent final bridge review and floating-point limits. The decline in the two lower bounds makes mesh-family stability the next principal uncertainty. Do not spend a coupled refinement budget merely to get another number; design the next acceptance comparison around active and near-front modes, physical-bin response, and a reference error bound under the unchanged D1 gates. The fixed-target result is not an independently accepted D1 capability.
