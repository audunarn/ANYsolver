# G0 F03 flat E4 additive-coordinate pose adapter — 24 September 2026

Status: **bounded coordinate-adapter evidence; G0B remains open.** This
extends the previously committed finite shell pose candidate; it does not
authenticate a material trial, accepted state, or coupled line solve.

The diagnostic now accepts a complete flat-panel E4 total displacement and
rotation vector. It forms current nodal positions from translations and
current physical directors from `Exp(total rotation) * +Z`, then evaluates
the director-constrained four-sample pose. A second-order Jet path evaluates
first and mixed second variations with respect to the *additive total
rotation coordinates*, including the chart curvature. This is distinct from
the spatial-left director variation already checked in the earlier result.

The selected Q4 and S3-V2D routes both use this additive total-rotation
representation in the existing generic corotational pullback. The qualified
native S3 formulation has a different committed rotation-state model and is
not used here. A physical spin about a tilted director is a combination of
additive coordinate increments; treating the raw `rz` column as that spin
would be wrong. A focused test applies the inverse left-Exp differential and
checks the distinction.

Executed with `C:\Python\Python314\python.exe` from the isolated checkout:

- Finite-pose candidate and additive adapter: **18 passed**.
- Adapter with native/shell spatial ports and existing F03 moment/nonaffine
  diagnostics: **92 passed**.

Independent read-only review inspected the exact Q4 and S3-V2D source paths
and found no actionable defect. The reviewer retracted an initial concern
that belonged to a separate native S3 class. The retained claim is only for
the flat +Z additive total-coordinate map and its derivatives.

The next boundary is to bind the map to a validated multi-element E4 trial
from one accepted predecessor, including material and owner identity, then
compose its second variation with the objective relative-pose Log work.
Layer-specific eccentric samples, chart transport, segmented weak-line
assembly and coupled stability remain unresolved. No one-use scientific
registration was consumed; G1 remains barred.
