# P5 continuum/discrete lateral shape comparison — research plan

Parent: `ecf755eff9c2065c0a42b56a454a17a647367a25`, tree
`c66fa209015a6833d3619fe48a8e645e2a6569d4`. Add a separate linear continuum
mode-recovery helper and a hash-guarded comparison reader, without editing any
existing mechanics, reference equations or accepted/failed external proofs.

Inputs are the two saved continuum root records, SHA-256
3CAB47BFB275DE3D9AF26609F9F1291717420285BE1EBB458815B5C7B4D08E20 and
FE310EC8836FDD0ADB58B8C910A47F111D32AD4097FE6BD9534279323FB6A1DA,
and the saved discrete spatial inspection, SHA-256
252ACE01CABF4B11818657436F7D49B669325B9B97B7BFE21FAF7C5679495E9F.
Validate their exact bytes/hashes before numerical imports. Reconstruct the
saved continuum base fields; never rerun its base/root solver or the discrete
nonlinear path. The independent equation implementation stays separate from
the module that reads and compares stored discrete modes.

Use the left endpoint of each saved root bracket. Obtain its isolated near-null
initial momentum from the transfer boundary block's smallest right singular
vector. Require a near-neutral isolated singular value before integration.
Integrate only the six-variable linear Jacobi state over the two fixed halves,
with a seventh state accumulating the quadratic Lagrangian. Compare this
integral with boundary u dot p. This checks integration/work consistency of
the already derived equations, not an independent proof of those equations.

Use DOP853 with rtol 1e-11, atol 1e-13, at most 10,000 RHS calls and thirty
cooperative seconds per shape. Sample exactly 33 registered reference nodes;
preserve crown continuity and actual end residuals. Do not zero, smooth or
project boundary errors to force a clamp. Require saved-transfer agreement
within 1e-8, normalized end error within 1e-7, and work consistency within
1e-9. No automatic retry or larger search is permitted.

Normalize the shape with reference-arclength trapezoid weights and rotational
coordinate scale equal to reference span 2. Map z,wx,wy into nodal DOFs uz,rx,ry.
Compute sign/amplitude-invariant squared cosines and sign-aligned distances
against all eight saved lowest odd modes. Report combined, translation-only
and rotation-only comparisons separately. Compare the two continuum sampling
resolutions as well. This is **not physical-mass MAC**, a frequency estimate,
or a new qualification threshold. The continuum and discrete states have
different crown drops; high shape similarity alone cannot qualify the earlier
discrete critical onset or prove mode-family identity/mesh convergence.

Small tests cover the exact straight-column shape, constant-coefficient
exponential, work consistency, clamps, bounds, endpoint identities, norm/
weight/shape mutations, sign/amplitude invariance, separate component mismatch,
input byte/hash guards and import boundaries. Initial suite: 17 passed in
0.47 seconds. The tests perform no nonlinear arch solve.

Run the bounded read-only comparison twice in fresh external directories and
require byte-identical outputs. Bind both new source-file hashes. These are
small reference integrations/postprocessing, not a resource-heavy campaign;
the consumed arch request remains untouched. Preserve all original evidence,
all comparison values and the absence of qualification claims. The result
remains production_qualified=false, qualification_gate=false, and
NO_GO_PRODUCTION_RESTRICTION_UNCHANGED. Broader material/state, curved/slender,
mass/modal/dynamic, production/restart and beam-shell-joint work remains open.
