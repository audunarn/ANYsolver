# Q4/two-S3 projected-gap development profile

`Q4_S3_PATCH_GENERAL_NODAL_PRIMAL_MORTAR_AUGMENTED_STATIC_DEV_V1` is an
opt-in profile for one qualified Q4 pressure face and two qualified S3 V2D
target faces. Set `q4_source_gap_certificate="projected_matching"` with the
existing augmented, primal-mortar Q4/S3 controls. The multi-control path uses
`Q4_S3_PATCH_GENERAL_AUGMENTED_PATH_DEV_V1`. The default `whole_face` setting
retains the V0 identities and checkpoint format.

The static and swept matching-projection lower bounds are derived in the
[Q4 projected-gap note](GENERAL_CONTACT_C1_Q4_PROJECTED_GAP.md). Both accept
a P1 triangle target as well as a Q1 quadrilateral target. They bound the
represented overlap where source and target points share the same projection.
Each of the two S3 faces is checked; the weaker bound governs the pair.
Source pressure, normal work, tangent, augmentation and material mapping are
unchanged from the Q4/S3 V0 route. The V1 selector is bound in the version-2
restart contract. Reversed sides, penalty enforcement and other element mixes
are rejected for this selector.

## Development evidence

Exact admission, V0 contract preservation, a corner trial under a 0.1 mm
declared gap tolerance, static/swept checks and opposite-body wrench balance
passed (`q4-s3-projected-local-first.txt`). V0 rejected the same corner trial
under its full-face bound. A public single-press path completed with active
pressure, four pressure modes and a checkpoint
(`q4-s3-projected-path-first.txt`, 57.86 seconds). The four-phase press, 50 mm
slide, opening and recontact path completed under a 0.2 mm gap budget; opening
released all four multipliers, and resuming from the opening checkpoint
matched the uninterrupted final displacement and multipliers
(`q4-s3-projected-four-phase-first.txt`, 248.71 seconds).
The ordinary displacement-control route also completed a two-step 0.05 mm
corner closure with active pressure, opposite-body force balance, the same
0.2 mm gap budget and a version-2 multiplier checkpoint
(`q4-s3-projected-ordinary-displacement-first.txt`, 48.43 seconds). Ordinary
force control remains a separate untested route for this V1 profile.
With 10,000 Pa/m normal regularization and a 0.04 mm corner closure, a
single press and a four-phase lifecycle each met a declared 0.05 mm gap
budget (`q4-s3-projected-50um-first.txt`,
`q4-s3-projected-50um-four-phase-first.txt`). The latter activated pressure
in press, slide and recontact and released it on opening. This budget equals
`10^-3` of the 50 mm shell thickness for this benchmark; it is not a
universal tolerance or evidence of enforcement convergence.
The `--projected-tight` source example completed with one active Q1 pressure
mode in each contact phase, none on opening, and a worst certified gap of
about `-0.04 mm` (`q4-s3-projected-tight-source.txt`, output SHA-256
`986964199bdce57cd63967f6081e9df14c13992065a29023ad9418e8a65ab98e`).
One active mode here is an outcome of this loaded geometry and regularization;
the other pressure functions remain in the declared Q1 space.

Run `python examples/general_contact_q4_s3_augmented_path.py --projected`
for the 0.2 mm development lifecycle or `--projected-tight` for the
0.05 mm benchmark-scale lifecycle. It reports phase gaps, integrated normal forces, pressure
multipliers and augmentation counts. The route uses physical Q4 bottom and
S3 top skins, including the S3 reference offset. These are development
settings, not application defaults.

The first source example run imported from this checkout and completed with
active pressure counts `4, 4, 0, 4`, a worst certified gap of about
`-0.05 mm` and a version-2 checkpoint
(`q4-s3-projected-example-source.txt`, SHA-256
`40bfb10bf19351e158a5617b2639a5a0a3300bd901fc8eafbe3799c03f428e06`).

A wheel built from clean commit `223d1a9f` has SHA-256
`565cc98c2622dac3300116c0ea456b7973355a235a5f05721886dfb776acc43c`.
After offline installation into an isolated target, the import origin pointed
there and the installed `--projected` example completed. Its complete output
was byte-identical to the committed-source output, with SHA-256
`40bfb10bf19351e158a5617b2639a5a0a3300bd901fc8eafbe3799c03f428e06`
(`q4-s3-projected-example-installed-223d1a9f.txt`). The wheel was not
published; installed agreement is a delivery-route check only.

This is one small nonmatching pair, not pressure-space or mesh/enforcement
convergence. The matching-projection certificate excludes unrepresented edge
features and is not interval arithmetic. Pressure-space stability, physical
edge/rim contact, independent review, broader Q4/S3 meshes, application
adapters, and engineering acceptance remain open. Earlier failed Q4/S3
tight-gap cases remain failed evidence.
