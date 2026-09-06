# GE-B3 loaded-state conservative spectrum development

Private successor of `16d068d82b2f39d9bf579104f4e64191045b96d4`, tree
`b4ffdc7b90013f4c9a416f4e0705693da758aaf5`.

The new `_ge_beam3_loaded_modal` adapter consumes accepted native V4 states.
It changes no static element operator, material law, mass kernel, load work,
solver control, tolerance, public alias, default or prior qualification record.
No method on the frozen element is enabled by this adapter.

## Loaded operator and retained inertia

The complete accepted 36-coordinate stationary functional is replayed with
the saved previous algorithmic origins, committed nodal rotations, retained
cell rotations and endpoint moments. Its distributed spatial dead load is
`load_parameter * element.core.line_force`, integrated over reference arclength.
The load acts on the lifted curved centreline, including cell rotations: its
second variation must not be omitted from the net Hessian.

Only the twelve massless endpoint moments are locally eliminated. The resulting
24-coordinate pencil retains all six inertial cell rotations. A further
nodal Schur operation is performed only to validate agreement with the accepted
static tangent; it is not applied to the dynamic mass. Current rest mass uses
the existing lifted velocity field and explicit positive-definite generalized
section inertia, including translation/rotation coupling. No Guyan reduction
of cell inertia, numerical trace mass or stiffness regularization is introduced.

Assembly shares physical node DOFs and retains distinct cell DOFs per element.
Nodal rotation traces remain exactly massless. Their equations are eliminated
globally by the existing signed stationary-pencil solver, which requires a
positive trace block and positive physical mass. Negative and zero physical
eigenvalues are retained, not clipped or converted into positive frequencies.

## State, load and constraint authority

The adapter requires an explicit common load parameter, complete accepted
state and inertia maps, and the accepted global displacement. Each native state
is replay-validated and must carry that same parameter. A detached native
rotation store validates shared nodal rotation authority; no caller-owned trial
is opened, committed, discarded or re-originated. The inputs and result arrays
are copied into owned snapshots. Model and packet guards detect later mutation.

Modal interpretation additionally requires free equilibrium against explicit
**actual nodal spatial dead forces at this state**, not a unit force pattern.
Distributed work is already present in the net derivatives and is not
subtracted again. Nodal moments, followers, mixed formulations, point masses,
activity, general MPCs, nonhomogeneous supports and partial rotational support
blocks fail closed. Unconstrained stress-free bodies are admitted for the six
free-body-mode check. The private model remains bounded to 256 retained DOFs.

An accepted algorithmic plastic Hessian can be inspected, but is not silently
called a vibration modulus. Modes require every station to be on an elastic
interior branch, away from the nonsmooth yield boundary. Elastic unloading
after prior plastic history is supported when this criterion holds; the
history is preserved. General inelastic vibration branch policies remain open.

## Development evidence and scope

Checks cover actual loaded Newton states, moment/nodal Schur identities,
distributed-load second variations, rest kinetic energy, shared-node assembly,
large exact translations, proper coordinate re-expression, malformed states,
load disagreement, input mutation and cancellation.

The distributed-work comparison uses the independently reconstructed rational
Q2/closed-form load oracle. The separate elastic-potential comparison shares
the existing AD kernel and is **not** an independent mechanics oracle. The
separate velocity-field integration checks mass assembly; it does not establish
quadrature convergence or replace engineering modal references.

The small straight cantilever shows tension stiffening, compression softening
and negative eigenvalues on a strongly compressed straight equilibrium branch.
This is not an Euler factor, a buckling bracket, bifurcation classification or
post-buckling engineering qualification. The output explicitly withholds
buckling-factor authority.

The first 15 checks passed in 13.80 seconds; the expanded 22 checks passed in
48.69 seconds. A focused mutation test then found the new guard had captured
the initial DOF count without comparing the live count. It was corrected before
freeze; no physical operator changed. The canonical development record binds
the final suite, source identities, diagnostic hashes and preserved inputs:

`docs/reference_cases/ge_beam3_loaded_modal_development_evidence.json`

## Final verification and preservation

The final source regression passed **115 tests in 175.74 seconds**. Separate
inventories are 23 loaded-modal checks, 39 force-program checks, 28 native-load
state checks, eight existing signed-pencil checks, five adaptive checkpoint
checks, seven installed-control checkpoint checks and five arc checkpoint
checks. A fresh-process repetition of the two recorded diagnostics passed in
19.32 seconds. Five new static evidence-binding tests passed in 0.13 seconds.
Python 3.13.9, NumPy 2.4.3 and SciPy 1.16.3 used one numerical-library thread.
These timings are diagnostics, not performance qualification.

The two axial-spectrum records are 529 bytes each, SHA-256
`692870fe0e3ed2c333e0a74ca812c9467a233cac5348bf7c2100e244be959e7b`.
The two shared-node translated-pencil records are 37,397 bytes each, SHA-256
`6ac8c092e0f4ab7fdefe62004534523212c8016b25f3fa5637d68e679b84f8fb`.
Both pairs are byte-identical. The four files (75,852 bytes) are preserved at:

`C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-loaded-modal-development-20260906-858f6c1b7cf4`

Every external file was exclusively copied and byte/hash-verified from the
normal workspace context. Only verified relay duplicates and empty relay
directories were removed; original temporary outputs remain. No formal
resource request was created or consumed, and no earlier run was reclassified.

## Remaining programme

Independent review, installed-wheel validation of the adaptive/modal successors,
modal engineering accuracy, qualified conservative buckling factors and
nonlinear branch studies remain open. Generalized material/section and load
parity, straight/curved qualification, public integration and the objective
beam-shell connection are still required. Nonzero-velocity rotational dynamics
are not enabled. Formal studies require their own frozen inputs and bounded
process/resource supervision. No formal request, publication, version change
or default activation is authorized by these development checks.
