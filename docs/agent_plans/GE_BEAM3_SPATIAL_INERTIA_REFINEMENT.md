# Scalable spatial signed-inertia audit and saved-state refinement

Parentd403da7275dc196707b67905170db3887f8eea73. No beam/shell mechanics or
historical evidence changes. Existing small Decimal all-root audit remains
preserved; successor uses sparse ORIGINAL factor products and high-precision
signed-inertia queries instead of all-root Jacobi at larger sizes.

Independent arithmetic reference: stdlib Decimal80/100digits, explicit symmetric
1x1/2x2 Schur elimination with complete diagonal/off-diagonal search. Singular
or unresolved pivots fail closed, never clipped. The algebraic stiffness block
must be positive and physical mass positive. At each root-bracket endpoint,
count negative pivots of the full constrained K-lambda M; positive algebraic
inertia contributes no negative roots. Require both precisions to give identical
counts. Also count atzero to expose all unstable physical directions.

Background block-factorization principle (not copied LAPACK implementation):
https://www.netlib.org/lapack/explore-html/db/d8d/group__hetf2_ga91a9fdb3b98a38e1a91689b65c366569.html
The numerical count/precision agreement is not certified interval evidence or
independently reconstructed beam mechanics. Review remains pending.

Unit cases include non-diagonal congruences through210coordinates, block pivots,
signed physical roots, massless variables, singular and mutated inputs. Validate
the new audit against BOTH existing small arch packets and their independently
computed80/100-digit all-root references before larger work. This is a new
arithmetic cross-check, not rerunning the completed arch or small modal campaign.

Next refinement uses saved steps1/12 for meshes4/8/12 from the immutable arch
repeat archive. Authenticate and replay arc states in capture children, emit
hash-bound factor packets only after native guards pass. Audit factor packets
in separate children; never fabricate Context-issued states from packet JSON.
Each captured artifact binds source, original checkpoint, canonical packet,
exclusive ready marker and successful complete process-tree receipt. New inputs
are checked before numerical imports. No partial canonical science.

Retain exact original-factor planar/lateral zero-coupling proof and signed roots.
At most3workers;1numericalthread;24GiB/tree;600s/child;1800s/wave;120sCPU-idle.
Existing native Context120s unchanged. Arithmetic calls bounded120s. No automatic
retry. Smoke the smaller cases and measure before finer cases; freeze each runner
before execution. Require two fresh deterministic science cycles when rehearsal
is complete. Negative physical eigenvalues are branch properties, not automatic
element implementation NO-GOs. Full spatial/branch, material/state/solver parity,
production integration and objective shell joints remain open.
