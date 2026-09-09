# Native fibre restart and physical recovery development

Parent 2b9814481c521c4baf5b99abf5cc6a41a53b416a, tree
7792d5416005bec7a99a3388c4c77f98e62a2ef7. Preserve frozen native adapter f5bc443,
static boundary afa2c5a, all mechanical operators and historical evidence.

Add a strict typed canonical JSON checkpoint for the complete supported native
static model: model/DOF/support identity, fixed nodal force pattern, stress-free
genesis and every accepted snapshot. Verify each local static/material replay,
exact predecessor, internal-seed and origin/history links, native multiplicative
rotation updates, shared-node agreement and full supported equilibrium (1e-11).
Reject skipped/missing states, duplicate/nonfinite/noncanonical JSON, boolean
numeric substitution, changed supports/model/loads, invalid hashes and forged
qualified flags. Require the caller's external SHA-256. Self-hashes are integrity
checks, not cryptographic proof of who created an entirely replaced valid chain.

Bound the private format to 16 elements, 512 nodal coordinates, 65 snapshots,
2 MiB and 60-second validation. Homogeneous support, no MPC/activity/point mass,
no partial rotational support and nodal force loading only. No public restart
route is switched. Decoding must reconstruct typed arrays, paired histories and
the exact static response, and reproduce the canonical bytes.

Native recovery uses accepted internal coordinates and fixed origins, returns
paired physical fields/fibre stresses, frames, paired positions and global
resultants. Verify unchanged history and material/global work conjugacy; never
recover physical fields from numerical diagnostic coordinates or advance history.

Use new straight-elastic and curved-plastic two-increment actual Newton cases
with tip force (.34,-.014,.007). Encode the first accepted prefix, decode into a
fresh model, continue with the previous half-load as constant and remaining
half-load as incremental. Require byte-identical final state/displacements to
the uninterrupted path. The initial smoke's 1e-10 driver setting accepted the
curved half-load state at residual 6.420418655440868e-11, correctly rejected by
the stricter restart validator. Preserve that failed smoke and its separate
snapshot diagnostic; use 1e-12 for these new development solves without changing
the 1e-11 restart acceptance, mechanics, or historical test settings. Also exercise
connected-model genesis. Save the raw snapshot chain before attempting encoding.
The corrected smoke passed chain encoding but caught NumPy scalar terms at the
new recovery boundary: the frozen compensated-sum helper requires Python floats.
Convert only the new recovery wrapper's terms; preserve the failed smoke, helper,
and mechanical operators unchanged.

The first full rehearsal passed 17 nodes but both continuation cases hit the
generic solver input copier's rejection of typed CellHistory. Add only an
exact-private-class branch in nonlinear_static._owned_initial_element_states;
its helper serializes under the supplied observation guard, reconstructs owned
typed arrays/histories, and fully validates the local response. The generic
copier, frozen adapter and all mechanics remain unchanged. This single-state
capture is not a substitute for complete checkpoint chain/provenance validation.

The integration rehearsal completed both continuations but failed bit identity:
the established LSQR restart projection introduced offsets (maximum 5.421e-20
straight and 3.469e-18 curved), changing subsequent arithmetic. Preserve that
failure. For this exact private candidate only, validate the complete homogeneous
support selection map and extract free coordinates directly with exact full
reconstruction. All other formulations retain the existing projection path.

Twenty-three test nodes: four roundtrip/recovery/continuation cases, nine resealed
mutations, four strict-parser/hash negatives, changed support rejection and
connected genesis, plus exact coordinate-map/mutation checks, detached typed capture, guard-on-failure and unchanged
generic rejection. Smoke roundtrip/recovery first with fail-fast behavior; any
failure is preserved and diagnosed before correction. Freeze only after complete
rehearsal; run twice in fresh directories and require identical scientific
packets. Each child: one numerical thread, 24 GiB, 600-second wall, 120-second
inactivity, no retry. Independent review, full restart/workflow qualification,
general material/dynamic parity and beam-shell connection remain outstanding.
