# Native adaptive force stepping development

Base: d7c3b64177dc014b34b0584a455e1fa35933e121.
Expose the existing native Newton cutback/growth through an optional typed
AdaptiveForcePolicy, without changing any element, section law, residual,
tangent, acceptance tolerance, public route or default. Fixed-step calls with
policy=None must retain their exact historical scientific outputs.

Bind policy and nominal/Newton controls in the private programme identity.
Reject wrong types, booleans-as-counts, mutated controls and exhausted history
capacity before mechanics or before accepting a trial. Use power-of-two
nominal steps, binary half-cutbacks and double-growth; at most 64 total accepted
increments including authenticated restart history. Existing 2-MiB checkpoint
and 65-snapshot bounds remain explicit; this is not a scalable restart design.

Verify actual adaptive behavior, not just parameter forwarding:
- A prescribed factorization fault rejects the first full increment. Its
  discarded state must be identical to the accepted pre-attempt state.
  Two subsequent half increments must reproduce a separate fixed two-step
  solve byte-for-byte in straight, curved plastic and connected plastic cases.
- Encode/decode the resulting complete accepted chain and recover fields.
- A diagonal elastic torsion fixture uses four initial steps with growth;
  verify accepted load factors .25,.75,1. and analytical rotations/reactions.
- A real max_iterations=1 nonconvergence exhausts bounded cutbacks without
  committing any state or spinning.
- Mutating policy during a live trial must reject and discard before commit.
- Invalid controls and insufficient complete-chain capacity fail closed.

The factorization fault is an explicit test injection, not a material defect
or an automatic process retry. Adaptive Newton cutbacks are part of the
requested algorithm, distinct from forbidden automatic worker retries.
Retain all deterministic adaptation events and load factors; omit timing from
scientific packets. Keep the existing 1e-12 Newton convergence and 1e-11
work/equilibrium checks. No reference field, material or load tuning.

Run the inexpensive growth/nonconvergence smoke first, then complete local
and geometry rehearsals. Each geometry has one complete cutback/history test:
its selected case-level smoke is also its complete pre-freeze rehearsal and
is not executed redundantly under another label. Clean freeze before two
fresh deterministic cycles. Separate unit/local/geometry and regression
inventories; count each actual invocation once. Each child:
one numerical thread, 24 GiB tree memory, 600-second wall, 120-second CPU
inactivity; at most three concurrent, 1,800-second waves, no worker retry.
Preserve failures before correction. Independent review remains PENDING.
Broader arc-length, prescribed fields, partial rotational supports, arbitrary
history/scalability, mass/spectra and production integration remain required.
