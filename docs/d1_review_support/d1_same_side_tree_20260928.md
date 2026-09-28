# Same-side projected-overlap tree: bounded development result

Source before this change: `652a994b3c7308f852b4813e5fbddf9b071d52da`, branch `codex/general-contact-core`. Python 3.14.2, NumPy 2.4.6, SciPy 1.17.1; ANYgeometry imported from `C:\Github\ANYgeometry\src\anygeometry`. The new change is recorded by the commit containing this note. This is development evidence, not D1 acceptance.

**Question.** The previous projected-rectangle pruning preserved the mechanical result but still scanned every face pair. Can the existing AABB tree remove that scan without missing a same-side projected overlap or changing the coupled result?

**Change.** Validate every face as before. Build a 3D tree of its physical face boxes. For each first face, query a conservative world-space box around its projected rectangle extruded across the scene's full normal extent. Retain the prior projected-interval and exact planar-overlap checks for every returned candidate. Sort by stable original face ID. The query uses a roundoff margin; it does not rank or discard contact by depth.

**Controls.** Twenty-two focused exhaustive-versus-tree cases passed in 1.14 s, covering rotated Q4/S3 faces, distant normal separation, oblique crossings, late collisions after many separated faces, large coordinates, valid warped Q4 and invalid geometry. The related mortar/static subset passed four tests with one unrelated long four-phase test deselected in 31.94 s, bounded at 180 s and 1 GB (peak 223.15 MB). An earlier unbounded combined-module invocation was interrupted after exceeding the development time and provides no mechanics verdict. Independent read-only scrutiny found no concrete exact-arithmetic false-negative construction in the prism query; the focused checks supply finite-precision controls.

**Matched complete route.** One fine-Q1 16×8 near-rim, two-step monolithic route used the same mechanics, settings, 32-pivot block response, no-checkpoint scope and 180 s/1 GB cap as the previously saved projected-pruning run. Its status, accepted steps, final displacement array, complete contact result and step counters are exactly equal in the saved JSON. Timings are instrumented solver times; the measurements are one pair, not balanced repeated timing.

| Quantity | Projected pruning | Tree query |
|---|---:|---:|
| Instrumented solver elapsed | 82.06788 s | 79.45633 s |
| Whole process elapsed | 83.77318 s | 81.37501 s |
| Ordinary aggregate geometry | 25.0020 s | 22.2065 s |
| Batched Jet2 pair work | 40.1518 s | 40.8329 s |
| Peak process-tree memory | 493.6704 MB | 487.6247 MB |

The tree reduced geometry time by about 2.80 s on this route and complete measured process time by about 2.40 s. It does not establish a reliable complete-route speedup or support a larger coupled run by itself. The remaining dominant pair derivative work is unaffected. Search-only scaling and installed optional-extra compatibility are still open.

Raw records: [route](d1_same_side_tree_route_20260928.json), [resource](d1_same_side_tree_route_resource_20260928.json), [22 search cases](d1_same_side_tree_reviewed_focused_20260928.txt), [bounded related tests](d1_same_side_tree_patch_focused_20260928.txt), [test resource](d1_same_side_tree_patch_focused_resource_20260928.json). Previous route: [projected pruning](d1_same_side_profile_after_20260928.json) and [resource](d1_same_side_profile_after_resource_20260928.json).

**Decision.** Retain the conservative tree broad phase as a D1 preparation for larger deformable-target scenes, with the exact check and exhaustive small-scene oracle. Continue D1 mechanics and acceptance gaps. Do not spend another coupled run solely to claim performance.
