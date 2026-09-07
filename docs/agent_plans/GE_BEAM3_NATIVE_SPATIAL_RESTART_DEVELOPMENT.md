# Native spatial nodal-couple restart development gate

Base: 1e53dae1afe478fcca822b1e7989b41ed2ead2bb. This successor extends only
the private native line/couple driver and typed checkpoint boundary. It does
not change physical beam/shell operators, material laws, tolerances, historical
qualification evidence, public selectors, defaults or versions.

The complete accepted chain binds the unchanged native element state and its
epoch, predecessor, material origin, seeds, multiplicative rotations and shared
node poses; it additionally binds the line-force and spatial nodal-couple
constant/proportional patterns and segment parameter. Applied nodal couples are
counted once globally, including junction nodes, when checking accepted free
equilibrium. They are external spatial work, never section resultants or a
conservative potential. The original line-only checkpoint cannot authenticate
a moment-bearing chain and is not silently upgraded.

An external SHA-256 is mandatory, in addition to strict canonical JSON,
duplicate/nonfinite rejection, exact schemas/model/support identity, bounded
input size/count and validation time. Rehashing a different complete valid
history does not prove it was authorized; the caller owns the external hash.
Finite norm checks must reject overflow rather than using infinite load scale
to hide a nonzero free residual.

Resume into the actual force-control solver only after chain validation. The
initial constant line and moment loads must match the accepted endpoint. A
frozen live programme binds that checkpoint hash through solver entry; no raw
state bypass is added. Existing line-only calls retain their schema and path.
General nonsymmetric factorization and the spatial couple chart derivative
remain unchanged. Failed/rejected increments preserve the accepted state.

Development cases: straight elastic, curved coupled plastic, and connected
curved plastic with a moment at the shared junction. Check canonical typed
round-trip, split-run versus uninterrupted accepted state, unloading, physical
recovery, shared-node counting, failed continuation and strict mutations of
moments/path/policy/schema/hash/state/model. Preserve separate scientific output
and stdout/stderr. Smoke before full rehearsal; then clean implementation freeze
and two fresh-directory runs with byte-identical scientific outputs. Compare
the prior finite-load coupled and line-only outputs to preserved evidence.

Each child: one numerical thread, 24-GiB process-tree memory, 600-second wall
cap, 120-second CPU inactivity cap; no automatic retry. At most three children
and 1,800 seconds per wave. All failures remain evidence. The gate is private
development only, with independent review pending and production qualification
false. Distributed couples/internal nonsymmetric reduction, full nonlinear
path/section parity, mass/spectra/engineering qualification, packaging and the
objective beam-shell connection remain separate outstanding requirements.
