# F03 finite-pad axis and endpoint diagnostics

22 September 2026. **18/18 bounded algebraic screens passed. Physical
convergence, multiplier stability and G0B remain open.** These classical
Q4/CST-CB and beam experiments do not qualify native B3-GE/E4-PL or B2.
The illustrative finite-pad physical model remains distinct from the earlier
four-point comparator and its preserved failed comparisons.

## Identities, inventory and checks

The axis execution used source `584835f1fcd51f72ba5bbd56e0d7bce68ec9fc50`,
fixed `.05 m` pad halfwidth, P1 exact multipliers and smooth loading. For
each of Q4 and CST-CB, baseline `(Ns,Ny,Nb,Nm)=(8,16,16,8)` and low/high
values along each separate axis give nine cases. The low/high pairs are
shell x `4/16`, shell y `8/32`, beam `8/32`, and mortar `4/16`.

Raw evidence is preserved in the integration worktree at
`.qualification/b3-ge-e4-pl/f03-area-axis-v1/`. Its registration SHA-256 is
`39937c33ea2efa9e58516f09e6f9cdeb852e0be4c01337511b3d8baa451f84f7`;
adjudication SHA-256 is
`272e25c97b97d2fe7b33ecb2401733c10a13588ac01d87d27d2f7dc7c84bd22c`.
The serial orchestration completed in 292.898 s against the registered
20-minute launch budget. All 18 cases completed within 900 s and 8 GiB
sampled child RSS each; the maximum observed case time was 17.374 s and
maximum sampled RSS 87.7 MiB. Both baseline observable files matched the
frozen v2 baseline hashes exactly. The independent raw-evidence audit
accepted this algebraic/resource evidence with no findings.

All states were saved as owned physical arrays, bound to the child events
and receipts. Source `bfff7f0d66da8487fc1613643d1fd77950137b4c` subsequently
analyzed those snapshots without rerunning equilibrium. The new root is
`.qualification/b3-ge-e4-pl/f03-area-axis-analysis-v1/`. Analysis registration
SHA-256 is `806e74698dfa1929d2fe63815ddecf81fad0b4601b6db25eb0309bbe315ed98a`;
results SHA-256 is
`eed96ace1cab076e3128ff0624faa18d069a3b7edef273f9c37f0801d2acac4e`.
All 18 descriptions completed in 25.222 s.

An independent read-only audit accepted this descriptive analysis: all 18
case files match the aggregate, all 72 input-file hashes and seven analysis
source hashes match, and the identities and reconstruction checks pass.
That disposition does not accept physical convergence or close F03.

The endpoint and reporting code passed 43 focused checks after independent
review. Initial pytest attempts had temporary-directory setup errors;
the successful invocation used a fresh worktree scratch directory. Those
setup failures did not consume scientific cases or generate acceptance.

Postprocessing independently integrates P1 tractions over fixed physical
bands and the root Hermite test support. It checks quarter wrenches and
root port force against the original recovery. The shell-trace derivative
uses independent edge interpolation and boundary flux, with the original
area-average translation used only in the yaw correction. Orders 10 and
12 agree to at most `1.63e-19` across the reported derivative quantities.
The maximum first-hat identity residual norm is `5.20e-20 m`.

## Physical findings

Mortar refinement at fixed shell and beam resolution drives the largest
response change. Signed results below preserve the original support and
interface channels. The yaw gap is multiplied by the fixed `.46 m` length.

| Shell | Nm | Tip uy, micrometres | Root Fy, kN | Endpoint y gap, micrometres | Scaled endpoint yaw gap, micrometres | Fy on [0,1/32] m, kN |
|---|---:|---:|---:|---:|---:|---:|
| Q4 | 4 | 44.485 | -445.301 | -28.086 | -20.504 | -91.803 |
| Q4 | 8 | 39.517 | -601.243 | -17.734 | -17.459 | -310.918 |
| Q4 | 16 | 35.458 | -721.644 | -10.126 | -15.205 | -680.674 |
| CST-CB | 4 | 44.009 | -443.861 | -27.915 | -20.281 | -91.609 |
| CST-CB | 8 | 39.089 | -601.276 | -17.667 | -17.301 | -311.843 |
| CST-CB | 16 | 35.085 | -721.807 | -10.130 | -15.063 | -680.910 |

For Q4, the first vertical multiplier coefficient changes from -3.24 to
-11.92 to -31.97 MN/m, followed by a positive coefficient at every level.
Its L2 norm grows from 1.219 to 2.428 to 4.391 MN/sqrt(m). First-quarter
force also changes substantially: -200.917, -271.542 and -416.925 kN.
Neither a shrinking support integral nor a fixed physical band has yet
settled to a mesh-independent value.

The first-cell gap derivative norm decreases, from `3.557e-4` through
`2.545e-4` to `2.033e-4 m/sqrt(m)` for Q4. This is compatible with the
observed decreasing endpoint gap. The earlier statement that a *persistent*
gap would require derivative growth is conditional; these finite results
do not demonstrate such growth or a persistent nonzero limit.

For a first P1 hat of width h, the exact identity is

`r = g(0) + integral_0^h (1-s/h)^2 g'(s) ds`.

The reported floating bound includes the measured residual:

`norm(g(0)) <= sqrt(h/5)*norm(g')_L2 + norm(r)`.

It is a numerical consistency diagnostic, not a certified enclosure.
Small assembled weak gaps do not imply small endpoint gaps at finite h.

Beam-only refinement changes the direct root port-force partition because
the root Hermite weight shrinks with its element support. The total root
force moves much less: Q4 -606.139, -601.243, -600.605 kN for Nb=8,16,32.
This does not permit omitting the direct port force from reaction recovery.
Shell x refinement gives -607.360, -601.243, -596.329 kN; shell y refinement
gives -600.756, -601.243, -601.148 kN. These are axis diagnostics at fixed
other resolutions, not a joint refinement proof.

## Decision and next mechanics question

Retain all evidence. Do not advance G1, select a production multiplier
space, or claim physical convergence from this screen. Endpoint traction
growth can be compatible with an endpoint reaction in the dual of an H1
trace; it can also coexist with a poor discrete multiplier space. The
current fixed-band and primal responses do not resolve that distinction.

The next bounded formulation study must explicitly distinguish the
continuous exact-bond law from its discrete weak approximation, derive
endpoint work and physical reaction recovery, and use a declared
trace-dual norm for the multiplier stability comparison. Adding endpoint
rows changes the discrete feasible set and requires its own registration;
it must not be described as an algebraic rewrite of these P1 runs. Root
slope restraint must not be added. No tolerance or historical result is
changed by this diagnostic.
