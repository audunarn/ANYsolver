# F03 finite-pad endpoint/line-space comparison protocol

22 September 2026. **Bounded classical diagnostic; no G0B qualification.**
This follows the independently accepted axis analysis, whose physical
response and fixed-band reactions remain unconverged. The programme still
requires native full-vector, curved/pre-rotated, off-grid and shear/drilling
checks before selecting a production attachment or multiplier space.

## Frozen physical law and discrete comparators

Keep the existing one-metre classical beam, Q4/CST-CB in-plane shell,
four `.10 x .10 m` material pads, `.05 m` halfwidth, smooth beam load,
reference axes, section laws and homogeneous supports. The root fixes
beam translation and section angle; it does not fix the Hermite slope.
The gap is `g=(bx-Tx, by-Ty, .46*(theta-Theta))` in metres.

At fixed positive pad area, the shell trace and beam trace are continuous
in station. Thus an exact continuous zero gap also has zero endpoint
values. This observation does not make finite P1 moment constraints
equivalent to endpoint evaluation.

Compare three exact-multiplier discretizations on each registered mesh:

1. **P1:** every continuous linear line-hat moment, unchanged baseline.
2. **Hybrid:** interior P1 moments, then exact root and tip gaps. It has
   the same number of rows as P1, with different row units and feasible set.
3. **Enriched:** all P1 moments plus both endpoint gaps. This is a separate
   stronger-constraint comparator, not the presumed remedy.

P1 and hybrid feasible sets are generally incomparable. The enriched set
is a subset of both. With these homogeneous constraints and unchanged
dead loading, its stored elastic energy cannot exceed either comparator's.
This ordering is a useful independent check, not physical qualification.

For hybrid, an optional local lift subtracts `phi0*g0+phiN*g1` from the
gap under the interior integrals. The resulting row change is invertible.
Its physical endpoint atoms are `alpha0=eta0-(h/6)*lambda1` and
`alpha1=eta1-(h/6)*lambda_(N-1)`. For N=2 the same interior hat contributes
to both. This lift is an algebraic comparison *within hybrid*; it cannot
transform the original P1 space into hybrid. Compare the physical density
and atoms, rather than interpreting raw lifted eta as physical forces.

## Work, scaling and stability diagnostic

Use `C=[-Cs,Cb]` and recover the full `C.T*mu` before restricting support
reactions. Line rows have units m² and density coefficients N/m; endpoint
rows have units m and atoms N. The physical moment from the third atom
component is `.46*alpha_theta`. Endpoint forces contribute their lever-arm
moment about the same origin as all other wrenches. Root reaction includes
elastic, line-port and endpoint-port contributions minus root loading.

Keep the previous physical scales: L0=1 m, F0=1 MN, M0=F0*L0,
U0=F0/(E*thickness), E0=F0*U0. Translational coordinates scale by U0;
angles and Hermite slopes by U0/L0. Line-moment rows scale by U0 times their
line measure (h for interior hats, h/2 for boundary P1 hats); endpoint
rows scale by U0. In dimensionless coordinates use
`Kbar=D.T*K*D/E0` and `Cbar=diag(1/(U0*measure))*C*D`.

Define an independent trace norm on the full H1 interval with free
endpoints: `integral_0^1 (v*w/L0 + L0*v'*w') ds`. Endpoint evaluation is
included; zero-endpoint trace spaces are inadmissible for this diagnostic.
Assemble its Riesz matrix on independent continuous P1 meshes with exactly
**32 and 64 subdivisions per mortar cell**. Cross-integrate the physical
line tests exactly, and evaluate endpoint functionals directly. Normalize
the functional rows by the same measures as Cbar. The three-channel dual
Gram is the scalar Gram tensor the 3x3 identity.

Require `max(abs(eig(G64,G32)-1)) <= 1e-3`, explicitly a squared-dual-norm
resolution check. Check positive definiteness and relative symmetry
within `1e-9`, without symmetrizing or regularizing. Failure is
`UNRESOLVED_AUXILIARY_NORM`; do not automatically add a finer level.
The approximate Riesz norms converge from below and are not certified
continuum norms. Independent unit tests use the endpoint Green matrix
with diagonal coth(1), off-diagonal csch(1), and the constant-density norm.

Form the small structural Schur matrix `S=Cbar*Kbar^-1*Cbar.T` through
sparse structural solves. Report the complete generalized spectrum of
`(S,G64)` and its positive minimum square root as a **finite-model
diagnostic**. No universal beta threshold or continuum stability claim is
assigned. A nonpositive quotient or failed factorization is preserved.
Never use S as its own norm. A normalized local-lift row change uses 1/6,
not h/6; apply the same congruence to S and the Gram.

## Inventory and acceptance of the diagnostic execution

Use shell `(Ns,Ny)=(8,16)` and these five `(Nb,Nm)` pairs:
`(16,4), (16,8), (16,16), (8,8), (32,8)`. Cross with Q4 and CST-CB.
Each of the ten supervised cases evaluates all three families: 30
equilibria. No changed shell axis, load, pad size or support is introduced.
The source-bound registration records all sources/dependencies and parent
snapshot hashes. P1 displacement/state arrays must match the frozen axis
snapshots with relative tolerance `1e-10`, absolute coordinate floor
`1e-15`, and multiplier floor `1e-5 N/m`. The historical files are read-only.

Frozen numerical checks are free equilibrium and global balance `1e-8`,
normalized compatibility `1e-9`, energy identity and enriched energy
ordering `1e-8`, structural inverse-action residual `1e-8`, and the
auxiliary-norm criterion above. Physical comparisons retain signed root
partitions, both endpoint atoms/gaps, line and total quarter wrenches,
tip pose, gap norm, stored energy and combined dual action. Report changed
responses; do not use this diagnostic to waive the physical 1% target.

Each child runs serially with the existing supervisor, one thread in every
numerical pool, 900 seconds and 8 GiB sampled RSS. Freeze a 20-minute
orchestration launch budget. No competing benchmark, automatic case retry
or overwritten output is allowed. Preserve failures and partial snapshots.
Changing source, auxiliary resolution or a case requires new versioned
evidence and review. Register only from a clean committed candidate after
focused tests and independent mechanics/code review.

The terminal decision is diagnostic completeness, source/parent parity,
algebraic consistency and numerical norm resolution. Even a complete pass
does not select hybrid, establish joint mesh convergence, qualify native
coupling, close F03, or authorize G1. Review the observed response and
stability patterns before deciding whether to refine, revise, or reject
the comparator.
