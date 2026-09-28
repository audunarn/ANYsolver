# Saved shell-pose pressure work — development discriminator

This check uses the accepted 16×8 near-rim Q4/S3 pose saved in
`d1_saved_16x8_near_rim_field_20260928.json`. It asks whether the full
pressure-space null seen in the scalar fixture is also present in the
*actual shell* contact work at this pose. It is a single-pose discrete
check, not D1 pressure-space acceptance or a mesh-uniform inf-sup proof.

For each supported physical pressure coefficient `λ_i`, the structural
force map is the transpose of `B_i = S_i D(gbar_i)` after eliminating
prescribed structural coordinates. The metric is the contact-free linear
shell stiffness assembled from this model and reduced by the same
structural constraints. This deliberately excludes contact tangent and
multiplier-update response. The metric is symmetric to machine precision;
its unit-diagonal-scaled smallest eigenvalue is `0.0016688`, so the
discrete energy norm is positive for the tested free coordinates.
In the active-set production path, `nodal_force_linearization` returns
`D(gbar_i) = (D(weighted_gap_i) − gbar_i D(S_i))/S_i`; the probe multiplies
that returned gradient by `S_i` exactly once to obtain pressure work.

| Pressure rows | Modes | Work rank at `1e-10` relative threshold | Smallest unit-diagonal compliance eigenvalue |
|---|---:|---:|---:|
| All physically supported | 153 | 144 | numerical zero (`−4.34e−16`) |
| Excluding only prescribed source `x=0` column | 144 | 144 | `5.461e−6` |
| Settled active set, with all physical modes retained | 48 | 48 | `0.003156` |

The nine full-space null combinations disappear when the nine source
`x=0` pressure rows are excluded. This associates the discrete defect
with that boundary column; it does not mean each edge basis function is
individually null or that the continuum trace annihilates it. Those Q1
hats have positive area support, and tangential structural coordinates
remain free. The weakest full-space mode includes node 137 at `(i=0,
j=8)` and other `i=0` modes. Once that column is excluded *for diagnosis
only*, the weakest unit-diagonal-scaled modes lie in the narrow last
source row near the obstacle rim. The weakest active mode also lies
there. Its positive eigenvalue establishes local independence only; the
last-row support is very small and no reference-mesh ratio was calculated.

The full work solve residual is `5.38e−15` relative and the active solve
residual is `7.06e−15`. The final bounded run completed in `12.37 s` and
`195.28 MB` peak process-tree RSS under the `180 s`/`1 GB` development cap.
The probe reports `10.93 s` internal elapsed time and `210.13 MB` peak
working set; these use different accounting boundaries. The exact source
was `5682a3c5a45065540adf05d5f24868387d690afc` plus the probe change.
The local ANYsolver module, saved-pose hash and probe hash are in the
[final raw result](d1_shell_energy_final_20260928.json), SHA-256
`de023fa19920a6051faf43d301fa16b361d174cab4a3c0f86545967b61bfcf31`.
The [resource record](d1_shell_energy_resource_20260928.json) and initial
and clamp-follow-up outputs remain available. The first command failed
before mechanics evaluation because the local `src` path was absent from
`PYTHONPATH`; the corrected bounded run imported that source explicitly.

**Decision:** The full-space defect at this pose is associated with the
prescribed-edge pressure column; there is no demonstrated active rank loss
at this pose. A richer structural test space might detect these discrete
null combinations, as in the scalar fixture. Do not remove production
pressure modes or declare a physical quotient from this result. For D1,
derive the admissible shell trace norm and any true annihilator, then test
the active partial-front modes and pressure response under bounded
structural, pressure and integration refinement. The present result does
not close that acceptance row or warrant a larger coupled solve.

An independent read-only mechanics review traced the active-set
`nodal_force_linearization` path and confirmed the single support factor
in the pressure work map, the saved/probe hashes, and the rank arithmetic.
It found no further numerical or code defect in this bounded check. It
also confirmed that no settled active mode lies at `i=0`, while six lie in
the final `j=8` row. Its proposed next discriminator uses the same physical
pressure basis/work on an independently enriched shell structural test
space, with reference convergence and explicit treatment of any true
continuous trace annihilator. A coarse null with positive refined dual
norm is a discrete detection gap, not a mode to drop by declaration.
