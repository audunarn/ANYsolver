# Current-source complete-route enforcement comparison

**29 September 2026. Development performance screen, not D1 acceptance.**

Six isolated processes ran the same fixed-target eight-Q4/two-S3, two-step
distributed 0.3 N force route with checkpoint emission. The order was
nested/monolithic, monolithic/nested, nested/monolithic. Only the explicitly
selected enforcement algorithm and its algorithmic settings changed; the
contact definition, fine nodal Q1 pressure, 10 kPa/m normal regularization,
50 µm gap limit, mesh, loads and structural solver route matched. All six
completed under the existing 180 s / 1 GB per-process cap. Source commit
was `773f0adef996e8c076c6af3b855cd1115cec71cb`; Python 3.14.2,
NumPy 2.4.6, SciPy 1.17.1 and one OpenBLAS/OMP thread were recorded by
each process. The standalone comparison runner was uncommitted when these
processes ran, but it only constructs the route and records results.

| Complete process | Nested augmentation | Monolithic active set |
|---|---:|---:|
| Run 1 | 22.889 s | 13.899 s |
| Run 2 | 22.792 s | 14.322 s |
| Run 3 | 30.069 s | 13.909 s |
| **Median** | **22.889 s** | **13.909 s** |
| Median peak process-tree RSS | 305.03 MB | 280.24 MB |

The ratio of medians is **1.646×**; paired ratios are 1.647×, 1.591× and
2.162×. The three-run range is too narrow for a broad performance claim,
and this route does **not** demonstrate the twofold median target. All
monolithic steps used five candidate evaluations and zero backtracks.
Nested rejected-work counts were not captured by this runner; elapsed
process time includes that work. The source of the slower third nested
run is not established. No optimization follows from this screen.

All pairs accepted two steps. Across them, maximum absolute differences
were 1.78e−13 in displacement, 2.87e−14 N in integrated contact force,
6.98e−12 Pa in numerical pressure and zero in reported minimum gap.
These are same-model algorithmic parity observations, not an independent
mechanics oracle. Checkpoints differ by algorithm identity as expected.

The [aggregation and parity record](d1_enforcement_current_compare_20260929.json),
[aggregation script](d1_enforcement_current_compare.py), [single-route runner](d1_enforcement_current_route.py)
and six `d1_enforcement_{nested,monolithic}_{1,2,3}_20260929.json` files
retain fields and settings. Each run has adjacent `*_resource_20260929.json`
and `*_log_20260929.txt` files. The per-process command and cap are
recorded in each resource file.

**Decision:** retain the current monolithic candidate for D1 mechanics
work, without a twofold complete-route claim or another open-ended
optimization campaign. The pressure-space and spatial acceptance gates
remain independent of this timing comparison.
