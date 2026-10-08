# D1 saved-pose active response across x refinement — development discriminator

**Question.** Could the 7.8166% physical-support pressure-field change between
the saved 16×8 and 32×8 coupled near-rim solves be explained by an exact local
null mode in the active pressure-to-gap work map? The competing explanations
are a local rank defect versus spatial/front resolution and deteriorating
conditioning. This check reuses accepted poses; it does not spend another
coupled solve or alter the production pressure basis.

The [parameterized saved-pose script](d1_saved_active_compliance.py) rebuilds
each structural/contact tangent, removes fixed and controlled structural
coordinates, differentiates the active normalized gaps, and computes
`G K⁻¹ Gᵀ`. It uses the actual saved pressure, displacement and support,
checks the saved gap/support and linear-solve residual, then compares the
unit-diagonal active response spectrum. The historical [16×8 record](d1_saved_active_compliance_9231bfbf_20260928.json)
is from source `9231bfbf`, with saved coupled-field SHA-256
`8293e528837cc2a8a25444aa079944c9f8371f5a5b50280bb6dc91816d19b852`.
The new [32×8 record](d1_saved_active_compliance_32x8_20260928.json) uses
source HEAD `eaefa889` and saved coupled-field SHA-256
`fda79a813d4235594af6cd0e7d367e62e98d57210d67e1152d435f00a845a72a`.
The script source itself is retained with this record. The first local attempt
loaded a different installed `anysolver` and failed at import; the completed
attempts set `PYTHONPATH` to this checkout's `src` and root.

| Saved pose | 16×8 | 32×8 |
|---|---:|---:|
| Active/supported pressure modes | 48/153 | 96/297 |
| Physical free structural coordinates | 295 | 583 |
| Minimum symmetric active response, m/N | 2.193×10⁻⁶ | 1.058×10⁻⁶ |
| Maximum symmetric active response, m/N | 2.418×10⁻² | 4.748×10⁻² |
| Unit-diagonal minimum/maximum eigenvalue | 9.768×10⁻⁵ | 2.341×10⁻⁵ |
| Relative linear solve residual | 9.40×10⁻¹⁵ | 2.12×10⁻¹⁴ |

The 32×8 saved-pose analysis took 26.46 s and reached 312.29 MB peak process
working set, below the existing 180 s/1 GB development limits. Its response
symmetry defect is 7.71×10⁻¹⁶. Both active maps have positive eigenvalues at
their saved poses. Thus an **exact local active null mode at either saved pose**
is not the observed explanation. The fourfold drop in the normalized
eigenvalue ratio and the 7.8166% field change leave pressure-space stability
open. These are one-pose, different-size spectra; they cannot establish a
mesh-uniform inf-sup bound, front convergence or nonlinear D1 acceptance.

**Decision.** Keep fine nodal Q1 as the sole D1 production candidate. Do not
promote pressure-knot reduction or rerun a larger coupled mesh from this
evidence. The next pressure investigation must hold structural resolution
fixed while changing an admissible, work-rank-controlled pressure space, and
must compare pressure on the physical support as well as common bin forces.
The fixed-32×8/coarse-16×8 x-pressure result is already available; one
bounded y/rim pressure comparison is the remaining axis discriminator before
deciding whether another coupled solve is justified. This is a development
decision, not a new acceptance criterion.

Independent read-only review confirmed the constrained response construction,
saved-field identities and local no-exact-active-null interpretation. It did
not assess a mesh-uniform bound or final D1 acceptance.
