# Independent B2 nodal-footprint source and installed review

2026-10-01. Bounded read-only review of all five source/test/example paths, relevant physical B2 and historical point contracts, installed manifests/runners, XML, logs, raw legacy arrays/observables and example records. No product imports, numerical jobs, source edits or Git mutation. No blocking finding for the declared experimental reference-linear selected-node six-pose law. New F10/F11/F04/M4 acceptance and qualification remain open.

## Frozen source and repaired fixture

I independently verified these initial five bindings:

| File | SHA256 |
| --- | --- |
| `src/anysolver/_stiffened_shell_b2_nodal_footprint.py` | `e3a9fd01574ded5371a201e1394cb5c497d2d7ee365e1f7c22ba9bed7a224ff0` |
| `src/anysolver/_stiffened_shell_b2_q4_panel_experimental.py` | `ba8c68cefbe89ff6fbd8971162b11cd2bad7686002be757f8fb4ef9685b59177` |
| `src/anysolver/stiffened_shell.py` | `ba303e0487741985a45559df0bc608f26876bfa2ecb312358d4f7101690467e8` |
| Initial `tests/test_stiffened_shell_b2_nodal_rigid_footprint.py` | `d50f884bf86968079b70fdc2ea32dc4a9f470d3974c2ea90f6c17a3c5bcb2fdb` |
| `examples/stiffened_shell_b2_nodal_rigid_footprint.py` | `166c59afed0ac09911dae2112d9cb66ffced44f1997c8ca40a4becbb9daef152` |

The only repair changes the last test's intended successful disjoint groups from (1,2,4)/(3,5,6) to (1,2,3)/(4,5,6). On the unchanged six-node geometry, old B nodes (1,1),(2,0),(0,2) lie on x+y=2 and correctly fail the noncollinearity policy; both repaired groups are noncollinear. I inspected the exact diff: no helper, negative edge case, geometry, product, load or criterion changed. Current source test and separately named installed `_v2.py` both hash `c22faf56f3262d088dd3c9cc00be4a3b71410b5e20146517c15c75f7a3f339f2`. The original filename/source and failed evidence remain intact.

## Mechanical representation and dual recovery

The panel has global [u3,theta3] nodal coordinates, and physical B2 endpoint trace Jacobians reduce to the corresponding six-coordinate selector. The new endpoint-node incidences therefore do not need a fitted shell port or an interpolated/off-node beam station. For d=Xb-Xs the compiler implements g=(ub-us+[d]x theta_s,theta_b-theta_s), exactly the agreed virgin linearization. Shell rows are [-I,[d]x;0,-I], beam rows I6; multiplier work is lambda dot g. Reported domain loads are minus the transpose actions. All nodal actions and the common-origin group wrench preserve global spatial coordinates, explicit forceN/coupleNm fields, reference positions and row provenance. Direct shell couples, including normal-spin components, remain visible.

The B2-specific `B2_NODAL_RIGID_FOOTPRINT_REFERENCE_LINEAR_V1_EXPERIMENTAL` is distinct from both GE's footprint identity and historical B2 finite-vertex least-squares points. Historical point rows remain first and unchanged; footprint rows follow in declared group/node order. New result/case/batch/capability subclasses appear only for nonempty footprints. Legacy result schemas remain the old classes. Group descriptors are normalized immutable tuples and geometry is copied before assembly; selected recovery is typed, ordered, compiled-membership checked, detached and omitted when unrequested.

Independent tests scatter the actual shell/member tangents separately, build C explicitly, and solve a small independently assembled affine KKT. They compare displacement, affine reaction, gap, actual transpose loads and full work 2E=u dot L+u0 dot reaction, including nonzero prescribed work. Common rigid fields and zero element deformation cover all six rigid modes. Other controls cover nonaxis spatial-frame/contragredient unit maps, objective-joint virgin derivatives with nonzero multipliers, both member endpoint orders, reversed members and a shared physical endpoint. These are reference/algebraic controls; they do not establish finite mechanics or a full converted-unit engineering campaign.

## Admission, sparse solve and lifecycle

Connectivity is extended using actual shell-node incidence and existing physical B2 endpoint hosts. Unknown/collinear groups, duplicate or point-colliding IDs, shell-node overlaps, incomplete patches and unsupported constrained rows reject. Complete patches select exactly the vertex union and use canonical actual shell cycles for edge connectivity; caller permutations cannot invent a shared edge. Disjoint groups may share a beam endpoint, with complete supported C@T row independence checked subsequently. Noncollinearity is a declared footprint geometry policy, not a substitute for that supported numerical rank check or physical qualification.

The existing sparse affine KKT, congruence scaling, bounded accurate affine projection, row-wise force/moment/gap guards and tolerances are reused. No penalties, invented shell stiffness, load scaling or default criterion changes occur. Batch cases reuse one factor; requested group recovery is attached only to completed cases. Cancellation, backend failure and callback-close preserve the complete prefix and counts. Closing clears the owner factor handle; batch result records retain scalar counts/tuples rather than that handle. Modes/prestress explicitly reject nonempty footprints even when mass exists. No finite, rebase or checkpoint capability is added.

The synthetic sub-ulp recovery control intentionally yields shell common-origin moment -1Nm and beam moment0 for a highly cancelled action through rounded stored C coefficients. It proves retention/reporting of the low lever-arm contribution, not exact physical rigid-work balance at arbitrary extreme scales. Ordinary specimen transpose/work/balance checks are separately exercised; the synthetic result must not be represented as an arbitrary-scale balance theorem.

## Installed results and exact legacy control

Wheel `ee6f70a28a19a245251e452602ff68fde5a72bdcebb831c6f7dd82742caf2973` binds390 source/wheel/site modules. Initial XML has35 passed/1 fixture failure, zero errors/skips. The corrected affected predicate alone then passes1/1 on the same wheel/site, with both fixture hashes inventoried. Reuse of the35 unchanged cases is justified by the two-line test-only diff; this is36 distinct covered predicates across preserved V1+V2, not an all-green V1 or a fresh36-case V2 campaign. Legacy panel XML confirms38/38, zero errors/skips. All three runs inventory209 installed imports; reported pools1, Numba1 and JIT disabled are asserted in the target process.

Supervisor elapsed/observed tree RSS: initial5.2123615s/170360832B, repaired predicate2.0837624s/160632832B, legacy6.9781779s/169492480B under600s/8GiB bounds. Cache-denied first wheel build is preserved; the successful frozen-source build reports the same final wheel hash after cache-independent retry. The first old-oracle preparation fails before execution because a fixture's relative probe dependency is absent; the repaired old-v2 tree retains the declared dependency rather than changing the oracle/model.

I independently compared all13 `.npy` entry bytes in old-v2/new-v1 `operators.npz`: identical. Observable JSON bytes also match SHA256 `2e2c0796a0ceb481f4c25176812b7957ad8b94e6aa730fe81fb93c612bb219a9`. These are the fixed empty-footprint K/C/T/u0 and default-result/batch/capability oracle, not universal legacy equivalence.

The headless example completes one-factor selected static recovery on the same artifact. Its recorded209 installed imports and actual module hashes match the facade, panel and footprint bindings above; its wrapper verifies pools1, Numba1/JIT disabled and unqualified status. Elapsed1.5709048s, observed peak132354048B. The example deliberately reports direct couples and a selected reference group; it does not suppress drilling dependence.

## Bounded conclusion

The implementation and development evidence support this separately identified elastic reference-linear capability and preserve the measured empty legacy branch. Full nodal six-pose locking includes shell normal spin; it is not BL5, a drill-free joint, a distributing/continuous area weld, finite attachment or qualified physical torque-transfer model. No new scientific threshold, space selection, F10/F11/F04/M4 closure, aggregate acceptance or release is established by this review.
