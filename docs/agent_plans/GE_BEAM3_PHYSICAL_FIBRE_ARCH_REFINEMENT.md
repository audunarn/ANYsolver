# GE-B3 physical-fibre arch: comparison and bounded refinement

Parent: `9eb82909713dad97556c833e19d78b4a8ff0e2c9`, tree
`f26a048e32368f223365a8c1ef0e6a9865bbd127`.
This is a private development diagnostic, not standalone qualification.

## Preserved evidence and finding

Both original arch checkpoints remain byte-identical: 94,037 bytes,
SHA-256 `b334e0e10c14f733e9f88231fe94c8525276056862b5a47849969b3ff48a1b55`.
The new reader verifies their bytes and record seals without replaying or
advancing the archived mechanics. It does not replace the native replay.

All eight archived states retain zero plastic history, planar positions and
the physical second director. Reflection errors in positions, nodal triads
and cell rotations are below 4e-16. Thus observed symmetry breaking does not
explain these states' discrepancies with the symmetric continuum reference.
This is not a proof of branch uniqueness or of full spatial stability.

The separate continuum equations are the preserved Simo-Reissner arch BVP,
not a production-element import. Normalize EA, GA and EI by their largest
value, solve the same equations and scale force, moment, energy and load
slope back. Keep residual diagnostics explicitly in normalized units.
An equation/Jacobian unit test verifies the force-unit transformation using
an exactly represented power-of-two scale. No reference tolerance, callback
limit, collocation-node limit or branch boundary condition changes.

The prior unnormalized EA=1e6 BVP9 sensitivity attempt exceeded its mesh
bound; it was not retried with relaxed limits. The normalized formulation
avoids mixing large force units with geometric residual units. This remains
binary64 collocation, not multiprecision or interval certification.

For the nominal elastic family EA=1e6, GA=4e5 and planar EI=100, the archived
two-macro load error is 5.79% at crown drop .01, 12.39% at .025, 19.50% at .04,
27.09% at .055 and 46.16% at .1. These are not acceptable fine-mesh engineering
qualification results. The comparison uses nominal continuum coefficients;
it is not an exact certificate for the physical section's dyadic inputs.

## Next executable probe

Use four macros (nine nodes), the exact same parabola y=.1(1-x*x), unchanged
physical-fibre section/quadrature, clamped ends and crown dead force. Prescribe
only the first four existing drops: .01, .025, .04, .055. This isolates early
mesh convergence before expanding late post-buckling and branch-stability
studies. The original two-macro fixture is not modified or rerun.

The new fixture's two-macro case has identical reference fingerprints and
cell identities to the preserved original. Four and six macros are admitted
within the existing 256-variable native driver bound; eight are rejected.
Only the four-macro case is executable by the prepared probe command.

Freeze this clean development commit before registering the command:

`C:/Python/Python314/python.exe -B -m docs.reference_cases.ge_beam3_fibre_arch_probe --revision FROZEN_COMMIT --output FRESH_EXTERNAL_DIRECTORY`

The resource administrator must approve the exact request and its owner must
acquire/release the global slot. The runner does not grant resource authority.
The Python executable hash and installed runtime versions are checked; this
is not a complete frozen installed-wheel dependency graph or release gate.

One Windows Job holds the complete child tree, starts it suspended and sets
24-GiB memory and kill-on-close limits. One numerical-library thread, a
600-second wall and 120-second CPU/output inactivity limit are enforced.
The existing native controller's shorter cooperative limit remains unchanged.
Cleanup may use the inherited bounded 15-second tree-termination proof.
No automatic retry, extra child or queued second wave is permitted.

Keep stdout/stderr, failed checkpoints and pending files outside canonical
evidence. After a completed solve, native replay must reproduce the checkpoint;
all histories must still be elastic before comparison with the elastic BVP.
Only after the whole child tree exits successfully, final source checks and
complete comparison validation may the parent exclusively hard-link the
pending comparison to `comparison.json`. Any failure preserves diagnostics
and produces no canonical comparison.

The output deliberately has no qualification PASS threshold. Inspect load,
nodal shape/frame, symmetry and reference residuals against the preserved
two-macro result. Continued error or lost convergence demands diagnosis;
it does not authorize coefficient tuning, relaxed tolerances or activation.

## Preparation evidence and remaining scope

The canonical development record binds the actual comparison, source hashes
and unit report. Tests exercise the normalization, exact paired-coordinate
reflection, strict archived encoding/seals, reference sampling, fixture
identity, schema/mutation rejection and mocked process failures/publication.
Mocks do not establish a newly run real OS containment qualification.

No production source, B2/B3, Q4/S3, public selector, default, version, workflow
or historical evidence changes. Independent review remains PENDING. Actual
refined engineering convergence, recovery/energy convergence, branch/stability
tracking, nonlinear-section/load/dynamic/restart parity, packaging and the
objective eccentric/curved beam-shell connection remain required by the full
goal. A successful four-macro diagnostic cannot replace any of those gates.
