# Native curved-beam reconstruction and installed transaction parity

Frozen implementation `6b9c31c3157c7f42ea4da530e07e93911b5ebff2`, tree
`05f9a3067bdb286c83ac23a49a319f5f5880f723`.
Private outcome: `PRIVATE_NATIVE_DEFINITION_TRANSACTION_PARITY_ONLY`.
Independent review remains PENDING; production qualification remains false.

## Implemented integration

The new definition codec reconstructs the actual native resultant-ellipsoid
and physical-fibre elements, including curved stress-free reference geometry,
physical material triads, tolerances, quadrature, complete section data and
explicit physical inertia. It recomputes element/operator/section identities
instead of substituting hashes for missing constitutive data. Reconstructed
elements have fresh mesh/store ownership. The codec neither captures nor
restores committed histories; existing externally authenticated state owners
remain mandatory. Earlier straight GE-B3, B2/B3/S3/Q4 and defaults are unchanged.

Physical fibre flow curves/background factors are retained as authored native
material data. The generalized ellipsoid remains a resultant-level law; neither
family is mislabelled as the other or as an automatic 3D J2 conversion.
Supplying an inertia tensor does not turn the static18-DOF Schur response into a
dynamic reduction. Physical internal cell inertia must still use its distinct
descriptor assembly; the static element mass method remains fail-closed.

## Separate verification inventories

| Phase | Definition/schema tests | Native transaction tests |
| --- | ---: | ---: |
| Frozen rehearsal | 48 | 4 |
| Formal-A repeat | 48 | 4 |
| Formal-B repeat | 48 | 4 |

Eight reconstruction artifacts per phase cover both section families,
straight/curved geometry and quadrature4/8. Four real native transaction
artifacts cover both families and both geometries at order4: actively plastic
trial, exact residual/tangent/state parity against original construction,
one commit, original-origin replay and a subsequent trial/discard without
history advance. This is actual NonlinearStateStore/assembly dispatch, not
mocked method calls. It is not a complete global equilibrium/load programme.

All three aggregates and every corresponding artifact were directly compared
byte-for-byte after the runs. Shared aggregate:2172bytes, SHA-256
`221BF0BDB6935F0C0504A1FB106DB119D9D26B23CE5F90B330464FBC7D01FECA`.
Definition children took4.33--4.83seconds; native children41.79--41.80seconds.
Maximum frozen-repeat tree allocation240246784bytes. All children exited0
with empty Job trees. Bounds:600seconds/child,24GiB,one numerical thread,
1800seconds/wave,120seconds inactivity. No automatic retries occurred.

Earlier development inventories are preserved separately:47definition tests,
four native transaction tests, a later single oversized-input regression and
13existing source-boundary regressions. Counts are not combined with the frozen
inventories. No earlier onset or plastic lifecycle campaign was rerun.

## Installed-wheel evidence and preserved isolation incident

An offline no-build-isolation build used exact committed package files in a
fresh external source directory; no build products entered the research
worktree. Private artifact `anysolver-0.4.2-py3-none-any.whl`:1707819bytes,
SHA-256 `D326B9EF50C3B9590F3B2E991011D2174E124946F58DDC08A45B30E7AA82F735`.
This is an unpublished development wheel, NOT a replacement PyPI release.
No version, tag, release or default changed.

The first package probe failed before importing mechanics because Python's
global `.pth` files introduced `C:/Github/ANYsolver/src` even under `-I`.
The failure was genuine isolation rejection; build/install had succeeded.
Its output contains no installed-parity result and is not reclassified as pass.
Failed receipt SHA-256:
`681CE7DE38DB23B4AA6B13A6B52811A54152B36D602F2AD8077F5770992E4234`.

A separate successor bootstrap removed that process-local source path, checked
that ANYsolver was not preloaded, and executed the unchanged hash-bound probe
in a fresh process. The wheel and installed files were reused unchanged, not
rebuilt. Every installed package member was compared against the frozen wheel
before and after the probe. No global configuration or dependency was changed.

The successor reconstructed all eight definitions and reproduced all four
native transaction artifacts byte-identically. Every loaded ANYsolver module
was checked to originate inside the isolated wheel target. Runtime21.40seconds,
peak185290752bytes, successful exit and empty process tree. Result11721bytes,
SHA-256 `0ECAA93F51233FFFAC7A9107C255878ADED3BF466545C601712AE810B2E31FD6`.

Sibling dependencies remain global editable installations. Their complete
source/wheel graph is NOT qualified by this ANYsolver package-isolation probe.
It does not authorize public curved selection or whole-environment deployment.

## Preservation and next work

Verified external archive:
`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-native-definition-6b9c31c-20260909`.
106manifest entries preserve source snapshots, helper versions, all repeat and
preflight artifacts, exact wheel/source archive, failed isolation receipt/logs
and successor installed evidence. Every entry was byte-verified after copy.
Manifest16661bytes, SHA-256
`3EC0E61C43867D64BE69111B04C335DFB1BEC9A9F561207A107602CDC3A56BF9`.
Original temporary outputs and prior evidence remain untouched.

This closes reconstructible definition/installed transaction parity, not the
whole production adapter. Next connect the current core's definition/state and
retained dynamic-coordinate contracts to explicit production dispatch without
relabeling the earlier straight facade. Actual spatial postbuckled branches,
remaining section/load/solver/mass/state and installed-dependency coverage,
independent review and objective eccentric/curved shell connections remain
required. Full goal ACTIVE. `NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`.
