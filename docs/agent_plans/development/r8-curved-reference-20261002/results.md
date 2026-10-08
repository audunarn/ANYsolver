# Curved reference point-owner development slice

2 October 2026; IMPLEMENTED_NOT_QUALIFIED. Base 369166cc plus this commit.

Explicit `CURVED_Q4_POINT_REFERENCE_V1` permits elastic planar Q4 facets on
a curved reference with generalized B3 beams and full-pose nodal points.
It requires the existing algorithmic Q4 pullback. Shell rotations remain global
incremental physical rotations; facet normals remain in reference geometry.
No new director interpolation or element equations were introduced. Flat
defaults and identity payloads remain unchanged.

The installed wheel SHA256 is
`163c3e717772e1ad5ac6f692b79d2be54d9485c0afd7d8edbd47ac9b9b38eda1`.
All 412 source modules matched wheel/site bytes; runtime imports, one numerical
thread and disabled JIT were verified. Installed checks: **44 passed**, 40.30 s
pytest / 42.51 s supervised, peak process tree 194084864 bytes. Limits were
600 s / 1 GiB. The runner, identities, logs and sanitized execution metadata
are in `checks-v1.zip`. No timing improvement is claimed.

Checks cover tilted-facet zero response and finite rigid motion, objective force
mapping and chart derivatives, eccentric point work, full-owner linear solve,
10–30 N finite stepping and exact checkpoint-restored continuation, plus flat,
physical-fibre and arc regressions. A physical-fibre admission negative uses the
existing real fibre fixture. Modal entry points and load restoration reject
unsupported curved combinations.

**Known failure:** the 0.1 N curved control stops at equilibrium ratio
1.914543159641637e-8 against the unchanged 1e-8 criterion, committing nothing.
Flat controls pass both load scales. The test preserves non-success and zero
accepted generation; its green result is not successful low-load equilibrium.
Root cause is unestablished. Initial fixture error (plastic-only state key on an
elastic response) and subsequent failed low-load runs are retained in the archive.

Independent read review found and then verified fixes for fibre-history admission,
external/staged checkpoint bypass and decoded-load restrictions. Final review
reported no remaining consequential source-level findings; it ran no numerical
checks and supplies no cross-family scientific acceptance.

Excluded: yielding, fibres, S3, lines, footprints, external loads, moments,
spectra and arc continuation on this curved route. ANYfem does not yet serialize
the new policy. This bounded two-Q4/two-beam control is not the E04 roof solve,
an external reference, limit-point evidence or aggregate gate acceptance.

Next: extend elastic point arc/checkpoint admission through the existing owner,
then establish the E04 nonlinear bracket and matched external connection.
Investigate low-load precision only with a targeted numerical discriminator;
do not relax equilibrium tolerances or infer a limit point from nonconvergence.
