# G3b reference-interface transport development

Parent: `7c4c980a8c5b4ccadb6721be177746af58c341ae`.
Scope: the frozen M_B2, M_B3, M_Q4, M_S3 (V2D), and M_Q4_WEIGHTED
reference interfaces, each with reference, node-ID renumbering, native
end/mid/end reversal, common global rotation/translation, and reverse
node/element insertion. No nonnative connectivity reversal is added.

This is test-only development coverage. Fresh transformed native and exact
nonnative family operators are compared with the existing baseline operators.
An affine-eliminated Schur solve is checked against separately assembled full
stationary KKT equations from fresh element instances. The assembly oracle
does not call the condensed assembly or reuse its element instances/matrices;
both intentionally use the unchanged family operators allowed by G3.
This is not an independently reviewed implementation or formal confirmation.

Checks retain all 24 native internal coordinates and cover operator covariance,
displacements, support reactions, translation-only tie forces, force/moment
balance, energy, virtual work, native station fields including directed-cut
reversal, physical shell tensor/vector recovery, exact class construction,
authority corruption and result/map mutations. Global surface stress component
arrays are reconstructed as symmetric tensors before transport. S3's three
sampled shear vectors are not a single tensor. All invariant comparisons retain
the frozen normalized 1e-11 threshold.

Legacy beam orientation must be supplied to a fresh constructor because that
constructor captures it. S3 normal authority is read from frame[:,2], while Q4
retains its physical_director field. No recovery schemas are changed.

## Boundaries

No src/ changes, public admission, shared state owner, restart, finite mixed
rotations, positive rotational adapters, defaults, versions or publication.
G3a/G1/G2 accepted evidence is not rerun or altered. Existing baseline test
bodies are unchanged; only successor-extent allowlists are extended.

Each invocation uses the existing Windows process-tree bounds: one numerical
thread, 24 GiB, 600 seconds, 120-second CPU/output inactivity. Diagnostics and
failed harness attempts remain external; no automatic retries. The two fresh
transport invocations compare canonical packets byte-for-byte. Each preceding
baseline lane runs separately and its packet is compared to the parent archive.

## Status and next step

Execution details, incident records and archive hashes are in
`reference_cases/ge_beam3_g3b_transport_development_v1.json`.
This checkpoint cannot qualify G3b or authorize public mixed models.

Next: implement the reference-only mixed graph transaction owner and S18
atomic publication, cache/epoch isolation and authenticated restart/replay;
then request independent implementation review and freeze formal G3b confirmation.
