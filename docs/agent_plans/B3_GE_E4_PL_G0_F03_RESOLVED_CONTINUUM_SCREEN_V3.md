# F03 independent continuum comparator: exact-static beam-field screen

21 September 2026. **Exploratory, not registered qualification. F03/G0B
remain open.** Commit `df3aa99` replaces the v1/v2 affine interior beam
load/trace with a homogeneous exact-static Timoshenko field derived from
`EI θ''=-V`, `V=GA_s(v'-θ)`. Endpoint interpolation and integrated
bending/shear energy match its nodal stiffness. Equivalent nodal force
*and moment* loads come from the same field's virtual work. The four-sample
shell pose is assembled from an independent classical Q4/CST membrane.
Constraints are still imposed at beam stations, rather than with the
required continuous weak multiplier law. The distributed-load particular
solution between stations is absent; refinement must establish adequacy.

The exclusive evidence root is
`C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/f03-resolved-continuum-v3/`.
The manifest binds commit, source and runner hashes, dependencies and 44
Q4/S3 smooth/sine cases, including joint x/y refinements and fixed-side
`N_b=8,N_s=1,64` reaches. The raw JSONL SHA-256 is
`0ae9357528bca8bdfa0faf0d5e81404557d4011020c8e7daa88b8705cd09a9c0`.
The largest relative physical equilibrium and work residuals were
`8.39e-14` and `1.02e-13`; the largest imposed constraint gap was
`2.84e-20`, and the two physical sides' interface-work discrepancy was
`1.07e-14 J`. Support moment includes the rotational equivalent loads.
These figures establish algebraic balance for this exploratory discrete
problem, not continuum accuracy or multiplier stability.

Within each shell/beam knot interval the declared beam field is at most
cubic and the shell trace is affine. The probe evaluates polynomial
stationary points and endpoints and separately checks a dense sample grid;
largest midpoint polynomial-fit discrepancy was `2.48e-20`. Its extrema
are floating-point estimates, **not** rigorous numerical upper enclosures
or certified continuum gaps. In the Q4 joint-width smooth series
`N_s=2,4,8,16` with `N_b=2N_s`, tip `u_y` is respectively
`1.58977e-5`, `2.41641e-5`, `2.62223e-5`, `2.90708e-5 m`.
Corresponding estimated interior yaw-gap maxima are `1.95623e-5`,
`1.83521e-5`, `9.50328e-6`, `3.86810e-6 rad`. The latter is
substantially larger than the zero imposed station gap. No converged
physical target follows. At fixed `N_b=8`, Q4 `N_s=1` still locks to
effectively zero tip motion, whereas `N_s=64` gives `2.25305e-5 m`;
the S3 counterparts are `8.32148e-7` and `2.13643e-5 m`.

Independent read-only review checked the exact-static beam equations,
endpoint and energy identities, load virtual work, Q4/CST assembly,
four-sample rigid pose, and small-case support balances. It identified
the physical interface-work sign and rotational load moment inventory;
both were corrected before this versioned execution. The row-normalized
constraint Gram diagnostic cannot establish the required signed native
retained inf-sup bound. A converged, physically matched reference and a
new admissible multiplier span remain prerequisites to F03 registration.
