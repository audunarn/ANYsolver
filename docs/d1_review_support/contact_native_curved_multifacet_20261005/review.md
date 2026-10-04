# Curved native / connected S3 facets — development review

5 October 2026. Same-family supporting Read review; no numerical jobs or edits
by the reviewer. This is not independent engineering acceptance.

The reviewer verified the native xi convention, facet normals and shared nodes,
42 retained native plus24shell coordinates and unchanged single-facet identities.
It requested explicit central/end source exclusions and per-pair shared-coordinate
checks: both now appear in the guide and tests. Independent analytic parabola
integration checks fixed material area, force, moment and energy. The reviewer
checked its pi/2 frame conversion, `r*(j-.4*r*sin(alpha)/j²)` reference measure,
harmonic angular root cuts and reaction signs. Smooth directional tangent and
independent nodal virtual-work checks pass at two perturbation sizes.

The actual coupled solve opens the left patch and activates the right. Correcting
the test's two-active expectation preserves this mechanics result. Both patches
are active only in the declared shallow manufactured work fixture; that fixture
is not equilibrium or application admission evidence. Fresh structural reaction
recovery can reuse the exact accepted contact candidate without repeating its
quadrature. The reviewer identified `.nnz` on a dense recovered tangent; it is
corrected with `np.count_nonzero`.

The failed source/installed test batches retain their NONPASS status. The real
installed completed checkpoint is now verified separately for reactions, shared
mapping and exact restart. No unchanged full-solve replay was needed. All523
production Python bytes match the previously installed wheel; imported hashes,
JIToff and single-thread runtime settings are verified. Two unique installed
checks pass; the added virtual-work gate repeats only its changed local case.

Full represented-patch containment remains required. No central seam crossing,
finite overlap/rim, simultaneous-contact coupled solve, complete multifacet
cycle, convergence, general native sections/materials or engineering acceptance
is established. The coupled solver cost102.331s remains a measured development
cost, not a speedup. See [summary](summary.json) for raw identities and nonpasses.
