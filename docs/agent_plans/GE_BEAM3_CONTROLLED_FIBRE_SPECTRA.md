# GE-B3 native control-history current-state spectra

Parent development checkpoint: `18d6860fb3bc92e35da54ae51bba2181cbf467c5`,
tree `270ec62d80a00aebac50de49be15d30b5e846780`.

This private adapter closes a history-interface gap, not a new beam formulation.
It restores the complete native kinematic-seeded translation-control chain,
including the accepted load parameter, actual material origins and histories.
It never manufactures a force-program history or advances the nonlinear path.

## Perturbation boundary conditions

Translation control is a numerical continuation equation used to find an
equilibrium with load parameter lambda. It is not a physical support. For the
current-state perturbation, hold the accepted spatial dead-load parameter
fixed and remove the continuation border. Keep every original physical free
DOF, including the controlled nodal translation. The retained-resultant and
massless nodal-rotation eliminations are the existing native modal operations;
cell rotation inertia remains physical and retained.

The conservative energy Hessian, not the nonsymmetric off-equilibrium Newton
Jacobian, defines the second variation here. The original complete-chain
replay verifies physical equilibrium and compatibility before spectrum
construction. Spatial dead nodal forces have zero load tangent. General
follower loads and beam-shell constraints are outside this adapter's scope.

Two explicit material interpretations remain separate:

- Frozen accepted plastic coordinates: elastic perturbations at rest about
  the committed state, including the plastic-strain affine offset.
- Accepted-increment algorithmic operator: a diagnostic of the last smooth
  material increment, not physical plastic vibration authority.

The implementation reuses native station compliance factors, compensated
factor-chain eigensolving and current lifted kinetic factors. It does not
change the element potential, section laws, mass policy or numerical gates.
This is reuse of the same implementation, not an independently authored
checker. The adapter binds its own schema, actual checkpoint hash, load
parameter, material policy, operators, inertias and physical free/algebraic
spaces. The complete model/program capture is checked again after solving.

## Bounded checks

Small two-macro models cover both constitutive contrasts, both material
policies, current physical mass, native replay without initialization or
advance, foreign-controller/hash rejection, cancellation and final mutation
guards. A coarse arch probe inspects an early loading state and a later
descending-branch state with the continuation constraint removed. Signed
negative eigenvalues must remain negative; they are not clipped, squared into
positive frequencies or called buckling load factors. Moderate-contrast
spectra are compared with a separately assembled ordinary generalized pencil
from the same operator factors, not an independent mechanics implementation.

All these are development checks. Mesh-converged critical loads, branch
selection and stability, general material/dynamic parity, exact independent
engineering references, qualified eccentric/curved beam-shell connections and
independent scientific review remain required. Existing public beam/shell
mechanics, aliases, defaults and publication are unchanged.

## Shifted-sign arithmetic incident and successor

The initial adapter suite recorded 16 passes and one failure in 64.45 seconds.
The arch spectrum failed closed when the binary64 shifted-sign margin could
not decide signs near roots in the 22,000--48,000 range. The initial adapter
source and raw failure are preserved. No bracket width, modal residual,
material law or physical matrix was changed to clear that failure.

The successor reuses the original factor-chain reduction and all its modal
audits. Only an ambiguous shifted inertia count receives an exact rational
congruence of the represented binary64 pencil H - shift M. Deterministic
nonzero diagonal pivots contribute their exact signs. If every diagonal is
zero, a nonzero off-diagonal gives a 2-by-2 hyperbolic pivot with one positive
and one negative sign; a remaining zero block contributes exact nullity.
An exactly singular trial shift remains unresolved and uses the original
two-sided root-bracketing treatment, never an invented sign.

Exact arithmetic is limited to 64 coordinates and 30 seconds per count with
cooperative cancellation. The existing 96-step search, 600-second spectral
deadline, original Ritz identity and 1e-11 modal residual checks remain. This
establishes signs of the supplied rounded pencil only. It does not certify
intervals for the unrounded operator, continuum problem or physical critical
load. No scientific qualification follows merely from a resolved sign.

## Verified development checkpoint

The final suites passed 24 tests in 61.689 seconds and 24 tests in 64.058
seconds, with nine byte-identical JSON output pairs. They preserve the actual
two-target material histories and recover both explicitly selected material
operators without nonlinear advancement. The coarse arch's first state has
no negative root among the first six; its sixth state has two negative roots.
These signs remain visible with the continuation constraint removed. They
are not a mesh-converged critical-load claim.

The archive contains 35 content files (1,832,335 bytes) and a 5,430-byte
manifest, SHA-256
`3824ba8ea1edc27b8b8a54025407f7d9d4dc340d96cd86faad45761b1250453b`.
It includes the initial failed suite and its adapter source, exact-sign unit
checks, both final cycles and all five final source/test files. The canonical
repository record binds these inventories separately. Independent review
remains PENDING and no production routing is enabled by this checkpoint.
