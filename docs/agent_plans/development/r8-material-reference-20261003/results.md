# Virgin curved material references — 3 October 2026

**IMPLEMENTED_NOT_QUALIFIED.** Solver parent `0a88f292`, candidate captured in
`raw.zip`; consumer product `85ed953`, documentation `7a00a0b`. Formal F03 remains
unconsumed. No main merge, publication or aggregate G4C/G3 acceptance.

## Delivered behavior

The existing `create_stress_free_point_reference` now also accepts the explicit
curved Q4 material definition. Its result carries a separate material-reference
operation policy. It creates a new virgin model, preserving canonical material,
section, inertia, quadrature and frame/admission contracts. It accepts neither a
loaded owner nor a checkpoint. Source/target temporary owners are still closed
on success, failure and cancellation; the old elastic policy is preserved.

Bounded physical checks establish:

- Finite rigid transformation covariance of the yielded two-Q4/two-B3 reference
  model at the same load factors; displacement/beam position and material-history
  comparisons meet 1e-9 relative checks with specified absolute floors.
- The loaded source's checkpoint and native definition bytes remain unchanged.
- Actual 4x4 roof crown changes of both signs, ±0.1 mm, have zero initial shell
  stress/plasticity, beam plasticity and attachment gap through actual nonlinear
  assembly. The material laws are development fixtures, not a calibrated roof.
- A nonrigid shell-width reference change, keeping lower-edge hosts and beam axes
  fixed with explicit zero port rotations, completes simultaneous yielding,
  unload/reload and exact detailed restart through native ANYfem persistence.

This separates initial geometry from loaded material state. It does not qualify
arbitrary distortions, material capacity, connections or the entire G4C scope.
Q4 facets, beam regularity, multiple hosts and reference frames retain admission.

## Installed evidence

**18 solver checks passed:** the new material reference/history tests, thirteen
existing elastic reference/lifecycle cases, and strict material capability guards.
All 413 source/wheel/installed modules match. Wheel SHA256:
`ad859e94d18cf6e83d78ac63bf7f0ac9be16cecdaf525bb0421336e993e6ea30`.
Supervised route 106.488 s, 206815232 sampled peak process-tree bytes.

**Two paired consumer checks passed:** strict input rejection and the newly
constructed nonrigid material definition through standalone/native save/reopen,
simultaneous yielding, unloading/reloading, exact detailed recovery and checkpoint
continuation. All 98 unchanged consumer product modules match wheel
`6435122e6aded71bcaa3b16a535c23efc15889367f85aa4810c77256d07e2b10`.
Route 37.832 s, 192004096 bytes. Runtime records verify installed imports, one
numerical thread and JIT disabled; limits are 600 s/1 GiB, serial execution.

Native input persistence preserves the new geometry and mechanical definition.
The experimental schema does not save the construction recipe or original-source
identity; retain the operation result/perturbations separately as provenance.
Complete provenance/consumer qualification remains a programme obligation.

## Review, failure and boundary

Integration-owner review checked explicit policy admission, virgin-state semantics,
unchanged material/section reconstruction, owned inputs, loaded-state isolation,
existing chart/frame guards and cancellation cleanup. Cross-family scientific
acceptance remains pending. The first covariance test failed in SciPy because its
comparison received a read-only result view; explicit detached copies corrected
the test. The failure and all corrected source runs remain in the archive.

No element equation, material tolerance, convergence threshold, load definition,
default, checkpoint meaning or release version changes. Curved material arc,
displacement control, spectra, external loads, fibres, S3 and broader attachments
remain unadmitted. No first limit point, descending material branch or external
agreement is established here. These execution costs are not a speedup claim.

Archive SHA256:
`f86d8d1db2f67b91d34b307709f12771d28395afa4d4f360b191dbe563131fab`.
Captured fresh source/fixtures/runners, wheel, logs, results and whitelisted
metadata exclude full environments and installed-site copies.

Next: inspect existing mixed arc state/normalization contracts for the curved
material route, then decide whether their reuse supports a separate experimental
mechanical identity. Do not relabel material checkpoints as elastic arc states.
Preserve physical metrics, predecessor histories, acceptance tolerances and
remaining external/scale/foundation gates.
