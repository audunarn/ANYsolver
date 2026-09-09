# Native physical-fibre static token integration

Parent d0bd46ff4428563d3484dacec6a7de9cafe93723, tree
bcd533fd6394726eb15bbc9c9d6cd9670680a048. Use the frozen retained physical-fibre
static boundary afa2c5a, not an older P5 material kernel. Reuse only the existing
analytic Exp-chart pullback from the source P5 math module.

Add an unregistered private Element subclass with explicit native material
validation. The actual NonlinearStateStore supplies pose/token authority;
validate before and after mechanics and before commit. Bind internal seeds,
accepted origins, history, response, model identity, epoch and predecessor hash.
Replay the full local response and static Schur matrix without advancing history.
Preserve the low part of exact reference-coordinate plus supplied binary64
total-displacement addition; never silently discard a sub-ULP translation.
This does not yet qualify a globally compensated displacement accumulator.

The adapter handles static internal mechanics with nodal external loading only.
Mass, modal, prestress/buckling and dynamic routes remain explicitly unavailable;
no public selector or default changes. Serialization/restart-file authority
and full accepted-chain authenticity are separate work, not inferred from a
self-consistent restored state. Static local stationarity remains 1e-11.

Sixteen nodes: three actual state-store commit/discard fixed-origin cases, five
resealed corruption cases, live/stale/foreign-token rejection, identical-pose
foreign-model rejection, current-store-state binding, three small
actual Newton-driver elastic/plastic smoke cases, and actual failed-increment
rollback, and a real-store common translation below the coordinate ULP at a
large reference offset. Commit/staging failures must preserve
both material and rotation generations. Save failures before assertions.
Smoke the state-store cases first, then complete rehearsal; preserve and diagnose
any failure before correction. Freeze only on pass, run two fresh bounded
cycles, and require byte-identical canonical packets. Existing driver smoke
tolerance is 1e-10, not an engineering qualification tolerance claim.

Each child: one numerical thread, 24 GiB, 600-second wall, 120-second inactivity,
no automatic retry. The local boundary retains its 60-second/24-update limits.
Independent review and all remaining straight/curved/nonlinear/material/dynamic
and objective beam-shell qualification requirements remain open.

The initial eleven-node rehearsal passed. Before freeze, implementation review
identified that pose-only token checks do not bind a numerically identical
foreign model. Bind this element's stable validator identity in the actual
store, and require the supplied input to equal the store's current committed
state before replay/mechanics. Two additional tests reject these cases before
the element's validation/evaluation entry. Existing shared protocol code is
unchanged. This is same-author hardening, not independent review.

The thirteen-node hardened rehearsal also passed. Full current-state canonical
comparison belongs at evaluation entry and exit; inner callbacks retain live
token and exact validator binding checks but do not recopy/hash the complete
unchanged committed state each time. Commit still revalidates the complete
candidate. Add the curved plastic actual-driver and failed-increment cases
before final freeze. Preserve all separate rehearsal inventories and compare
their overlapping scientific packets without claiming a controlled speed ratio.
