# G0 F03 bounded E4 multi-element trial seam — 24 September 2026

Status: **bounded elastic material-trial seam verified; G0B remains open.**
This is a G0 diagnostic fixture, not a production mixed owner, scientific
qualification, accepted-state implementation, or weak-line coupling.

`FlatE4TrialPanel` constructs actual Q4 or S3-V2D E4 elements in a real
`FEModel`, with four/eight elements for the tested `n_s=1/2` flat panels. It
evaluates each element through `corotational_element_response` using one
unchanged virgin elastic predecessor and one complete total-coordinate
vector. Local force and consistent tangent are gathered in a bounded dense
global oracle. Candidate material states are returned as immutable bytes;
none is committed. The four-sample shell pose is evaluated from that same
total vector, so the pose and material trial share the physical configuration.

The fixture records the panel counts, model nodes, complete public element
configuration, material definition, and predecessor bytes. It rejects
observed mutation of fields consumed by the trial, including connectivity,
material selection, yield stress, hardening/Hill route, and panel array sizing.
This is a sequential bounded fixture, not a concurrent production owner.

Executed from the isolated checkout with `C:\Python\Python314\python.exe`:

- Focused trial suite: **22 passed**. It checks virgin response, repeated
  discarded trials, deformed pose parity, global tangent directional
  difference, definition-mutation rejection, and both panel sizes for both
  formulations.
- Combined trial, point-work, finite-pose, native beam-port, and shell-port
  diagnostics: **64 passed**.

The independent reviewer reproduced three guard gaps in the initial draft:
mutable panel node count, element material selection, and material yield
stress. A second review found that a dynamic `hill_yield` attribute could
change the Q4 material branch; the material's full attribute set and values
are now guarded, with a negative test. The final independent read-only review
found no remaining actionable issue within the declared elastic virgin-trial
scope and independently confirmed 22/22 focused tests.

The evidence establishes only an elastic trial from a virgin predecessor on
small flat panels. Plastic updates, non-virgin accepted predecessors,
material/state ownership in a production owner, layer-specific eccentric
sampling, curved and mixed panels, segmented weak-line integration, full
coupled KKT, and norm-scaled multiplier stability remain open. No one-use
scientific registration was consumed. G1 remains barred.
