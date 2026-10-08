# C4 owner-backed search adapter: development disposition

The internal `ContactAABBIndex` accepts stable `(kind, integer ID)` feature
keys and conservative three-dimensional current boxes. It uses the public
ANYgeometry `AABBTree`, returns deterministic exact-box candidates and
refits existing features without changing their identities. ANYgeometry is
declared in the opt-in `general-contact` package extra. Search creation
imports it lazily. The adapter exposes owner query and index work counters.
This is infrastructure for later general search; it
does not implement automatic pairing, swept bounds or self-contact.

The existing restricted planar `PatchAABBTree` was temporarily replaced
with a two-dimensional wrapper over this adapter to answer one bounded
selection question. The [paired whole-route comparison](../reports/general_contact_c4_search_owner_patch_route_adapter_dev_20260928.json)
returned exactly the same Q4/Q4 sliding example output in old/owner/owner/old
order. Warmed route times were about 4.05 s for the old tree and
4.13–4.19 s for the owner tree; the first old run took 8.02 s. These
measurements are exploratory and do not establish a speed difference.

Search-only scenes with 1,024, 10,000 and 99,856 planar faces and 1,000
queries each returned byte-identical candidate signatures. At 99,856
faces, the old tree built in 0.94 s and used about 19 MB of incremental
process RSS; the owner tree built in 2.55 s and used about 180 MB. Its
query phase took 0.13 s versus 0.24 s for the old tree. The full
build-plus-query route was thus slower and used substantially more memory
in this scene. The raw [1k](../reports/general_contact_c4_search_scale_1024_dev_20260927.json),
[10k](../reports/general_contact_c4_search_scale_10000_dev_20260927.json)
and [near-100k](../reports/general_contact_c4_search_scale_99856_dev_20260927.json)
reports retain counts, timings and RSS snapshots. They are single-process
development observations, not balanced statistical performance claims.

**Decision:** keep the existing solver tree for its restricted planar
profile. The owner-backed adapter remains available for new general
contact search, where three-dimensional physical bounds, refitting and
stable keys matter. Before admitting that route, integrate it with a
real geometry/feature owner and prove conservative current/swept bounds,
exhaustive candidate completeness, resource admission and whole-route
cost. No existing accepted patch output or search semantics changed.

Six focused owner/patch search tests passed, including 3D exhaustive
comparison, refit and invalid-input rollback. Independent read-only
review found no concrete adapter correctness defect and agreed with
retaining the restricted tree on the measured build and memory evidence.
An isolated ANYsolver wheel
(SHA256 `5ddb8c58988f7996d485063f0e370cd3d8ea2752494be04ac9463687b34a38d7`)
contains the opt-in extra metadata and the current adapter. The wheel imported
from its install target and passed query, refit and diagnostic checks against
the locally available ANYgeometry 0.4.3 source. This verifies the installed
solver artifact's interface, but not an independently isolated ANYgeometry wheel. A
missing-ANYgeometry import simulation is not meaningful for the current
package because its existing ANYmesher dependency imports ANYgeometry
while importing ANYsolver; that is a pre-existing dependency path.
