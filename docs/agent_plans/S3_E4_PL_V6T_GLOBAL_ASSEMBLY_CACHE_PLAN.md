# S3 E4-PL V6T global assembly-cache repair

## Diagnosis

V6S closed modal and buckling but produced a deterministic mixed-performance
NO-GO.  Both solve and RSS routes passed.  Assembly failed at 25 percent in
both cycles and at 10 percent in cycle one.

The frozen source comparison identifies one orchestration difference relevant
to that result.  V2C retains and replays a revision-bound assembled CSR matrix;
V2D retains only per-element 18x18 matrices and reconstructs COO/CSR storage on
every warm assembly.  A bounded N20 observation confirmed that all V2D element
matrices were reused while the mixed global matrix was still reconstructed.

## Authorized repair

Add a V2D global assembled-stiffness plan equivalent in safety scope to the
accepted V2C plan.  It may operate only when every element is an exact qualified
Q4 or exact V2D element, activity is absent, and model/mesh/registry/token/
revision/material identities remain unchanged.  A cache hit must still pass
the qualified runtime guard before returning.

The retained matrix uses owned CSR data, indices, indptr, shape, and canonical
diagnostic bytes.  Mutation, activity, noneligible elements, material changes,
topology changes, or geometry changes must invalidate or bypass it.  Cold,
scalar, per-element-plan, and global-plan matrices must be byte-identical.

No element mechanics, coefficient, tolerance, load, mass, eigen procedure,
scientific threshold, formulation ID, public selector, serialization, recovery,
Q4 behavior, or default may change.  ANYmesh remains untouched.

After implementation, run targeted identity/invalidation tests and two bounded
N20 performance observations.  A pass authorizes a separately frozen V6U
performance-only Stage 4B successor; it does not reclassify V6S or activate S3.
