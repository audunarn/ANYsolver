# Native generalized combined spatial-couple closeout

Implementation: `deb0d97fa93bbf1edcc6e432c2232fac6deeba97`.
Tree: `8ca22ff0e8ff3dc4027628beb27ac9d1cd2c24e5`.
Base: `f785a4db4cea86d60739acc1b80274c87d39d3f7`.

The private combined-load development gate passes. The generalized-section
beam supports reference-line forces, distributed spatial couples and nodal
spatial couples together through actual native Newton assembly, complete-chain
restart and accepted generalized-resultant recovery.

This is not independent review, complete production qualification, public
integration, finite-rotation dynamics, conservative spectral authority or
default activation. The overall beam and beam-shell goal remains active.

## Separate inventories

| Lane | Passed | Deselected | Supervisor seconds |
| --- | ---: | ---: | ---: |
| smoke-local | 1 | 11 | 5.619 |
| smoke-straight-elastic | 1 | 96 | 8.424 |
| smoke-curved-plastic | 1 | 96 | 54.337 |
| rehearsal-local | 13 | 0 | 67.565 |
| smoke-connected-plastic | 1 | 96 | 145.547 |
| rehearsal-curved-plastic | 32 | 65 | 98.426 |
| rehearsal-straight-elastic | 32 | 65 | 19.653 |
| rehearsal-connected-plastic | 32 | 65 | 242.771 |
| q4-regression | 12 | 0 | 7.426 |
| legacy-regression | 5 | 0 | 4.617 |
| prior-generalized-straight-elastic | 32 | 64 | 22.260 |
| prior-generalized-curved-plastic | 32 | 64 | 141.937 |
| prior-physical-combined | 13 | 0 | 49.522 |
| prior-generalized-connected-plastic | 32 | 64 | 282.051 |
| cycle-a-connected-plastic | 32 | 65 | 248.564 |
| cycle-a-local | 13 | 0 | 68.157 |
| cycle-a-curved-plastic | 32 | 65 | 105.452 |
| cycle-a-straight-elastic | 32 | 65 | 19.453 |
| cycle-b-straight-elastic | 32 | 65 | 19.450 |
| cycle-b-curved-plastic | 32 | 65 | 97.421 |
| cycle-b-local | 13 | 0 | 66.950 |
| cycle-b-connected-plastic | 32 | 65 | 237.156 |

All 22 inventories passed. Each frozen local lane has 13 tests and 13 canonical
scientific files. Each frozen geometry lane has 32 tests and 44 canonical
scientific files. Both replicas and the corresponding rehearsal are byte-for-byte
identical. No automatic retry, failed scientific attempt or post-smoke correction
was required. Helpers were checked and corrected during authoring before execution.

The three distributed-only generalized regressions have 32 tests and 44 files
each, exactly matching the f200b90 archive. The preserved physical-fibre
combined-load local lane has 13 tests/files, also archive-byte-identical.
Q4 current-state ownership has 12 tests and legacy B3 nonlinear has five.
These targeted regressions do not constitute full old-element requalification.

The explicit enormous-load rejection test emits a preserved NumPy overflow
warning while confirming typed range rejection. No ordinary load is accepted
with nonfinite data. The warning was neither suppressed nor represented as
a mechanics failure.

## Work, state and recovery

The spatial nodal virtual work is m dot delta-theta. Its additive increment
chart force and tangent are A.T m and (dA).T m. Distributed couples retain the
previously frozen internal virtual-work map and general stationary Schur
tangent. The combined global Jacobian subtracts the nodal external chart
tangent; it is not artificially symmetrized. Actual factorization is GENERAL.
The analytical torsion fixture measures nonsymmetry up to 0.44654095353639034
and reproduces the independently specified torsion/rotation and reaction fields.

The connected fixture applies its nodal moment at shared node 3. The load is
counted once globally, not once per adjacent element. Accepted free-equilibrium
errors are at most 1.8929055794019249e-13; recovery work discrepancies are at
most 4.2934406030425976e-17. The curved and connected cases have eight and
sixteen evolving plastic stations respectively; straight-elastic has none.

The new combined checkpoint has a separate load policy and schema. It binds
the distributed pattern, nodal moments, supports/model, complete stress-free
genesis and accepted history, shared rotation operators, epochs, predecessor
hashes and internal seeds. Mandatory external SHA-256 prevents treating a
resealed self hash as provenance for a replaced history. The generalized
history codec is reused explicitly; old fibre schemas are not inferred.

Prefix restart followed by the remaining increment is byte-identical to the
uninterrupted final accepted state. Unloading continues the accepted history.
Failed Newton continuation leaves that state intact. Malformed, resealed,
foreign or incomplete inputs fail before solver entry or during strict replay.
Accepted recovery does not advance history and does not add external couples
to material resultants. No fibre stresses are supplied by this resultant law.

The frozen four-step directional protocol records all coarse and fine values.
Plastic raw errors are approximately 6.13249e-7, 1.53319e-7, 3.82691e-8 and
9.58172e-9, with the required second-order reduction. Both fine raw errors and
all Richardson errors satisfy the unchanged 1e-7 gate; the largest Richardson
error is 1.2069783978188554e-9. Local nodal work error is below 7.7e-17.
No coefficient, material law, load fixture or tolerance was tuned.

## Scope and process audit

Both new module algorithms are AST-identical to their preserved physical-fibre
counterparts after the explicit type/import, policy and schema substitutions.
The only existing functions changed are the generalized force programme's
checkpoint dispatch and the shared solver's private load dispatch. Exactly
seven paths constitute the implementation freeze.

Element residuals/tangents, station laws, state transactions, reference fields
and recovery operators remain unchanged. All other existing repository paths,
including B2/B3, Q4/S3 mechanics, public aliases/defaults, package metadata and
historical evidence, are unchanged from the base. No other repository is edited.

Every child uses one numerical-library thread, a 24-GiB Windows Job process-tree
limit, a 600-second wall limit and 120-second CPU-inactivity cutoff. At most
three run concurrently. Replica pairs may overlap across lanes, but a second
replica starts only after its first replica passes. All jobs terminated with
zero descendants and complete supervisor records. Longest recorded child:
282.0509651999964 seconds (prior generalized connected regression); longest
frozen child: 248.5635026000018 seconds. Largest recorded peak: 309260288 bytes.
No Python worker remains after the final run.

The runtime guard checks a clean frozen commit, Python executable hash and
configured package versions, not a complete dependency-file graph.
Git global-ignore permission warnings remain recorded without changing
the user's configuration. Independent scientific review remains PENDING.

## Preservation and next step

Archive:
`C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-native-generalized-combined-deb0d97-20260908`.

741 data files plus the manifest preserve all commands, available tool records,
complete supervisor data, XML/logs, deterministic outputs, frozen source and
unchanged-authority snapshots, administrative audit and intermediate checkpoint.
All copied byte counts and SHA-256 hashes were verified. The intermediate note
is historical; the completed audit and status supersede its running-state report.

Manifest: 128,359 bytes, SHA-256
`FBA78A1916A3E83C998570CAC7C0DA29AFAE6401E9ECDC9AF7B1DA8609EC71CB`.

Original run directories and historical archives remain intact. Only the
fully verified transfer duplicate may be removed. Main is unchanged at
`09351645ba17a0a5b130a1c7a48007d36dd08ada`; the user-owned untracked
ANYMESHER_05_COMPATIBILITY_CANDIDATE_PLAN.md is preserved. No push, merge,
release, package publication or default activation occurs at this gate.

Next: broaden native nonlinear path-control, cutback and initial/support-state
parity, then establish the conservative mass/spectral boundary. The private
16-element/512-DOF and supported force-programme limits are development bounds,
not the intended final product scope.

Consistent physical mass, modal/prestress/buckling, broader material/measure
adapters, slenderness and curved engineering, practical scale, independent
review, installed-package/public integration and objective beam-shell joints
remain required. Static condensation does not by itself authorize a dynamic
reduction. Keep the full goal active until these requirements are verified.
