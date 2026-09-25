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

Run `python examples/general_contact_q4_s3_augmented_path.py --projected`
for this profile. It reports phase gaps, integrated normal forces, pressure
multipliers and augmentation counts. The route uses physical Q4 bottom and
S3 top skins, including the S3 reference offset. These are development
settings, not application defaults.

The first source example run imported from this checkout and completed with
active pressure counts `4, 4, 0, 4`, a worst certified gap of about
`-0.05 mm` and a version-2 checkpoint
(`q4-s3-projected-example-source.txt`, SHA-256
`40bfb10bf19351e158a5617b2639a5a0a3300bd901fc8eafbe3799c03f428e06`).

This is one small nonmatching pair, not pressure-space or mesh/enforcement
convergence. The matching-projection certificate excludes unrepresented edge
features and is not interval arithmetic. Pressure-space stability, physical
edge/rim contact, independent review, broader Q4/S3 meshes, application
adapters, and engineering acceptance remain open. Earlier failed Q4/S3
tight-gap cases remain failed evidence.
