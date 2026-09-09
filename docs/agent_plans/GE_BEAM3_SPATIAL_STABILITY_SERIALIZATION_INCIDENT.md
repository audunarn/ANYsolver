# Spatial factor packet serialization incident

Frozen run 90bf036b84ed679722bc7e6ab8fcd877fd1b648c is consumed and failed.
The positive N24 endpoint was replayed and its full 438-coordinate physical
factors captured. Final writing called the plain JSON encoder on the dataclass
ElasticSeedPencil, raising TypeError before packet bytes were created.
The process exited 1 after 72.6331481 seconds, peak 464273408 bytes, with an empty
Windows Job tree. No negative capture or inertia worker launched. No stability
classification or canonical aggregate exists. The source endpoint is unchanged.

Preserve the original command, stdout/stderr, receipt and frozen source snapshots
in the distinct spatial-stability-90bf036 archive. Do not rerun that helper or
reuse its output. The successor changes only research packet serialization:
use the existing native canonical dataclass/array encoder, then strict-parse
the bytes to the plain wrapper representation. An actual captured small packet
regression asserts byte identity with the native encoding and seed identity.
No mechanics, factor equations, pivot logic, thresholds or source data change.
Freeze the correction before a separate successor smoke/wave in a fresh root.

This is a runner serialization defect, not a scientific beam NO-GO.
Production qualification and independent review remain incomplete.
